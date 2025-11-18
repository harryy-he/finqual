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
    """
    Comparable Company Analysis (CCA) for a given ticker or CIK.

    This class provides methods to retrieve financial ratios for a company
    and its sector peers over a given period or specific year/quarter.
    Ratios include profitability, liquidity, and valuation metrics.

    Attributes
    ----------
    fq_ticker : Finqual
        Instance of Finqual for the specified ticker/CIK.
    ticker : str
        Company ticker.
    cik : str
        Company CIK code.
    sector : str
        Company sector.
    sectors : pl.LazyFrame
        DataFrame of sector mappings.
    """
    def __init__(self, ticker_or_cik: str | int):
        """
        Initialize the CCA instance.

        Parameters
        ----------
        ticker_or_cik : str | int
            The company identifier (ticker symbol or CIK).
        """
        self.fq_ticker = Finqual(ticker_or_cik)
        self.ticker = self.fq_ticker.ticker
        self.cik = self.fq_ticker.cik
        self.sector = self.fq_ticker.sector
        self.sectors = self.fq_ticker.load_label("sector_mapping.parquet")

    @weak_lru(maxsize=4)
    def get_c(self, n: int | None = None) -> tuple[str] | None:
        """
        Get a list of comparable companies in the same sector.

        Parameters
        ----------
        n : int | None, default=None
            Number of comparable companies to retrieve. Defaults to 6.

        Returns
        -------
        tuple[str] | None
            Tickers of comparable companies. Returns None if no comparables found.
        """
        df_c = self.sectors.filter(pl.col('sector') == self.sector).collect()
        match_indices = df_c.select((pl.col('ticker') == self.ticker).arg_true()).to_series().to_list()

        if n is None:
            no_comparables = 6
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

    def _get_ratios(self, year: int | None, method_name: str, quarter: int | None = None, n: int | None = None) -> pl.DataFrame:
        """
        Retrieve ratios for the company and its comparables for a given year/quarter.

        Parameters
        ----------
        year : int | None
            Year to retrieve ratios for. If None, retrieves TTM.
        method_name : str
            Name of the Finqual method to call (e.g., 'profitability_ratios').
        quarter : int | None, default=None
            Specific quarter to retrieve. If None, annual ratios are returned.
        n : int | None, default=None
            Number of comparable companies to include.

        Returns
        -------
        pl.DataFrame
            DataFrame containing the ratios for the company and comparables.
        """

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
            futures = {executor.submit(fetch_ratios, ticker): ticker for ticker in tickers}
            for future in as_completed(futures):
                df = future.result()
                if df is not None and len(df) > 0:
                    lazy_frames.append(df.lazy())
                del df
                gc.collect()

        if not lazy_frames:
            return pl.DataFrame()

        df = pl.concat(lazy_frames, how="vertical").collect(engine="streaming")

        # --- Sorting

        ticker_df = pl.DataFrame({"Ticker": tickers, "Ticker_order": list(range(len(tickers)))})

        df = (
            df.lazy()
            .join(ticker_df.lazy(), on="Ticker", how="left")
            .sort(["Period", "Ticker_order"], descending=[True, False])
            .drop("Ticker_order")
            .collect(engine="streaming")
        )

        return df

    def _get_ratios_period(self, start_year: int, end_year: int, method_name: str,
                           quarter: bool = False, n: int | None = None) -> pl.DataFrame:
        """
        Retrieve ratios for the company and its comparables over a range of years.

        Parameters
        ----------
        start_year : int
            Start year of the period.
        end_year : int
            End year of the period.
        method_name : str
            Name of the Finqual period method to call (e.g., 'profitability_ratios_period').
        quarter : bool, default=False
            If True, retrieves quarterly data; otherwise annual.
        n : int | None, default=None
            Number of comparable companies to include.

        Returns
        -------
        pl.DataFrame
            DataFrame containing the ratios over the specified period.
        """
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

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(fetch_ratios, ticker): ticker for ticker in tickers}
            for future in as_completed(futures):
                df = future.result()
                if df is not None and len(df) > 0:
                    lazy_frames.append(df.lazy())
                del df
                gc.collect()

        if not lazy_frames:
            return pl.DataFrame()

        df = pl.concat(lazy_frames, how="vertical").collect(engine="streaming")

        # --- Sorting

        ticker_df = pl.DataFrame({"Ticker": tickers, "Ticker_order": list(range(len(tickers)))})

        df = (
            df.lazy()
            .join(ticker_df.lazy(), on="Ticker", how="left")
            .sort(["Period", "Ticker_order"], descending=[True, False])
            .drop("Ticker_order")
            .collect(engine="streaming")
        )

        return df

    @weak_lru(maxsize=4)
    def profitability_ratios(self, year: int | None = None, quarter: int | None = None, n: int | None = None) -> pl.DataFrame:
        """Retrieve profitability ratios for the company and comparables for a given year/quarter."""
        return self._get_ratios(year, 'profitability_ratios', quarter, n)

    @weak_lru(maxsize=4)
    def liquidity_ratios(self, year: int | None = None, quarter: int | None = None, n: int | None = None) -> pl.DataFrame:
        """Retrieve liquidity ratios for the company and comparables for a given year/quarter."""
        return self._get_ratios(year, 'liquidity_ratios', quarter, n)

    @weak_lru(maxsize=4)
    def valuation_ratios(self, year: int | None = None, quarter: int | None = None, n: int | None = None) -> pl.DataFrame:
        """Retrieve valuation ratios for the company and comparables for a given year/quarter."""
        return self._get_ratios(year, 'valuation_ratios', quarter, n)

    @weak_lru(maxsize=4)
    def profitability_ratios_period(self, start_year: int, end_year: int, quarter: bool = False, n: int | None = None) -> pl.DataFrame:
        """Retrieve profitability ratios over a range of years or quarters for the company and comparables."""
        return self._get_ratios_period(start_year, end_year, 'profitability_ratios_period', quarter, n)

    @weak_lru(maxsize=4)
    def liquidity_ratios_period(self, start_year: int, end_year: int, quarter: bool = False, n: int | None = None) -> pl.DataFrame:
        """Retrieve liquidity ratios over a range of years or quarters for the company and comparables."""
        return self._get_ratios_period(start_year, end_year, 'liquidity_ratios_period', quarter, n)

    @weak_lru(maxsize=4)
    def valuation_ratios_period(self, start_year: int, end_year: int, quarter: bool = False, n: int | None = None) -> pl.DataFrame:
        """Retrieve valuation ratios over a range of years or quarters for the company and comparables."""
        return self._get_ratios_period(start_year, end_year, 'valuation_ratios_period', quarter, n)
