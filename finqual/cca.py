from .core import Finqual
import polars as pl
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import functools
import weakref

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
    def get_c(self, n: int|None = None):

        df_c = self.sectors.filter(pl.col('sector') == self.sector)
        match_indices = df_c.select((pl.col('ticker') == self.ticker).arg_true()).to_series().to_list()

        if n is None:
            no_comparables = 5
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

    def _get_ratios(self, year: int | None, method_name: str, quarter: int | None = None, n: int|None = None):

        def fetch_ratios(ticker: str, year_f: int | None, method_name_f: str, quarter_f: int | None):
            fq_instance = Finqual(ticker)
            func = getattr(fq_instance, method_name_f)
            return func(year_f, quarter_f)

        tickers = self.get_c(n)
        results = []

        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(fetch_ratios, ticker, year, method_name, quarter): ticker for ticker in tickers}
            for future in as_completed(futures):
                result = future.result()
                results.append(result)

        df = pd.concat(results)
        df['Ticker'] = pd.Categorical(df['Ticker'], ordered=True, categories=tickers)
        df = df.sort_values('Ticker')

        return df

    def _get_ratios_period(self, start_year: int, end_year: int, method_name: str, quarter: bool = False, n: int|None = None):

        def fetch_ratios(ticker: str, start_year_f: int, end_year_f: int, method_name_f: str, quarter_f: bool):
            fq_instance = Finqual(ticker)
            func = getattr(fq_instance, method_name_f)
            return func(start_year_f, end_year_f, quarter_f)

        tickers = self.get_c(n)
        results = []

        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(fetch_ratios, ticker, start_year, end_year, method_name, quarter): ticker for ticker in tickers}
            for future in as_completed(futures):
                result = future.result()
                results.append(result)

        df = pd.concat(results)
        df['Ticker'] = pd.Categorical(df['Ticker'], ordered=True, categories=tickers)
        df = df.sort_values(['Period', 'Ticker'], ascending=False)

        return df

    @weak_lru(maxsize=10)
    def profitability_ratios(self, year: int, quarter: int | None = None, n: int|None = None):
        return self._get_ratios(year, 'profitability_ratios', quarter, n)

    @weak_lru(maxsize=10)
    def liquidity_ratios(self, year: int, quarter: int | None = None, n: int|None = None):
        return self._get_ratios(year, 'liquidity_ratios', quarter, n)

    @weak_lru(maxsize=10)
    def valuation_ratios(self, year: int | None = None, quarter: int | None = None, n: int|None = None):
        return self._get_ratios(year, 'valuation_ratios', quarter, n)

    @weak_lru(maxsize=10)
    def profitability_ratios_period(self, start_year: int, end_year: int, quarter: bool = False, n: int|None = None):
        return self._get_ratios_period(start_year, end_year, 'profitability_ratios_period', quarter, n)

    @weak_lru(maxsize=10)
    def liquidity_ratios_period(self, start_year: int, end_year: int, quarter: bool = False, n: int|None = None):
        return self._get_ratios_period(start_year, end_year, 'liquidity_ratios_period', quarter, n)

    @weak_lru(maxsize=10)
    def valuation_ratios_period(self, start_year: int, end_year: int, quarter: bool = False, n: int|None = None):
        return self._get_ratios_period(start_year, end_year, 'valuation_ratios_period', quarter, n)
