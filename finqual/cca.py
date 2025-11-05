from .core import Finqual
import polars as pl
from concurrent.futures import ThreadPoolExecutor, as_completed
import functools
import weakref
import gc

def weak_lru(maxsize=128, typed=False):
    """LRU Cache decorator that keeps a weak reference to 'self'"""
    def wrapper(func):

        @functools.lru_cache(maxsize, typed)
        def _func(_self, *args, **kwargs):
            return func(_self(), *args, **kwargs)

        @functools.wraps(func)
        def inner(self, *args, **kwargs):
            return _func(weakref.ref(self), *args, **kwargs)

        return inner

    return wrapper
class CCA:

    def __init__(self, ticker: str):
        self.ticker = ticker
        self.fq_ticker = Finqual(ticker)
        self.sector = self.fq_ticker.sector
        self.sectors = self.fq_ticker.load_label("sector_mapping.parquet")

    @weak_lru(maxsize=10)
    def get_c(self, n: int | None = None):

        df_c = self.sectors.filter(pl.col('sector') == self.sector)
        match_indices = df_c.select((pl.col('ticker') == self.ticker).arg_true()).to_series().to_list()

        if n is None:
            no_comparables = 3
        else:
            no_comparables = n

        if match_indices:
            i = match_indices[0]
            total_rows = len(df_c)
            half_window = 2

            start = max(0, i - half_window)
            end = start + no_comparables

            if end > total_rows:
                end = total_rows
                start = max(0, end - no_comparables)

            return tuple(df_c.slice(start, end - start)['ticker'])

        print("No comparable companies found.")

    def _get_ratios(self, year: int | None, method_name: str, quarter: int | None = None, n: int | None = None):

        def fetch_ratios(ticker: str):
            fq_instance = Finqual(ticker)
            func = getattr(fq_instance, method_name)
            df_ratio = func(year, quarter)
            if df_ratio is not None and len(df_ratio) > 0:
                df_ratio = df_ratio.with_columns(pl.lit(ticker).alias("Ticker"))
            del fq_instance
            gc.collect()
            return df_ratio

        tickers = self.get_c(n)
        lazy_frames = []

        # --- Collecting tickers

        with ThreadPoolExecutor(max_workers=1) as executor:
            futures = {executor.submit(fetch_ratios, ticker): ticker for ticker
                       in tickers}
            for future in as_completed(futures):
                df = future.result()
                if df is not None and len(df) > 0:
                    lazy_frames.append(df.lazy())
                del df
                gc.collect()

        if not lazy_frames:
            return pl.DataFrame()

        df = pl.concat([lf.collect(streaming=True) for lf in lazy_frames], rechunk=True)

        # --- Sorting

        ticker_df = pl.DataFrame({"Ticker": tickers, "Ticker_order": list(range(len(tickers)))})
        df = df.join(ticker_df, on="Ticker", how="left")
        df = df.sort(["Period", "Ticker_order"], descending=[True, False])

        return df.drop("Ticker_order")

    def _get_ratios_period(self, start_year: int, end_year: int, method_name: str, quarter: bool = False, n: int | None = None):

        def fetch_ratios(ticker: str):
            fq_instance = Finqual(ticker)
            func = getattr(fq_instance, method_name)
            df_ratio = func(start_year, end_year, quarter)
            df_ratio = df_ratio.with_columns(pl.lit(ticker).alias("Ticker"))
            del fq_instance
            gc.collect()
            return df_ratio

        tickers = self.get_c(n)
        lazy_frames = []

        # --- Collecting tickers

        with ThreadPoolExecutor(max_workers=1) as executor:
            futures = {executor.submit(fetch_ratios, ticker): ticker for ticker in tickers}
            for future in as_completed(futures):
                df = future.result()
                if df is not None and len(df) > 0:
                    lazy_frames.append(df.lazy())
                del df
                gc.collect()

        if not lazy_frames:
            return pl.DataFrame()

        df = pl.concat([lf.collect(streaming=True) for lf in lazy_frames], rechunk=True)

        # --- Sorting

        ticker_df = pl.DataFrame({"Ticker": tickers, "Ticker_order": list(range(len(tickers)))})
        df = df.join(ticker_df, on="Ticker", how="left")
        df = df.sort(["Period", "Ticker_order"], descending=[True, False])

        return df.drop("Ticker_order")

    @weak_lru(maxsize=10)
    def profitability_ratios(self, year: int | None = None, quarter: int | None = None, n: int | None = None):
        return self._get_ratios(year, 'profitability_ratios', quarter, n)

    @weak_lru(maxsize=10)
    def liquidity_ratios(self, year: int | None = None, quarter: int | None = None, n: int | None = None):
        return self._get_ratios(year, 'liquidity_ratios', quarter, n)

    @weak_lru(maxsize=10)
    def valuation_ratios(self, year: int | None = None, quarter: int | None = None, n: int | None = None):
        return self._get_ratios(year, 'valuation_ratios', quarter, n)

    @weak_lru(maxsize=10)
    def profitability_ratios_period(self, start_year: int, end_year: int, quarter: bool = False, n: int | None = None):
        return self._get_ratios_period(start_year, end_year, 'profitability_ratios_period', quarter, n)

    @weak_lru(maxsize=10)
    def liquidity_ratios_period(self, start_year: int, end_year: int, quarter: bool = False, n: int | None = None):
        return self._get_ratios_period(start_year, end_year, 'liquidity_ratios_period', quarter, n)

    @weak_lru(maxsize=10)
    def valuation_ratios_period(self, start_year: int, end_year: int, quarter: bool = False, n: int | None = None):
        return self._get_ratios_period(start_year, end_year, 'valuation_ratios_period', quarter, n)
