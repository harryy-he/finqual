import requests
import polars as pl
from datetime import datetime
import functools
import weakref
from ratelimit import limits

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

class SecApi:

    def __init__(self, ticker):
        self.ticker = ticker

        self.headers = {"Accept": "application/json, text/plain, */*",
                        "Accept-Language": "en-US,en;q=0.9",
                        "Origin": "https://www.nasdaq.com",
                        "Referer": "https://www.nasdaq.com",
                        "User-Agent": 'YourName (your@email.com)',
                        'Accept-Encoding': 'gzip, deflate',
                        }

        self.cik = self.get_cik_code()
        self.sec_submissions = self.get_company_submissions()
        self.sec_company_facts = self.get_company_facts()
        self.sec_data = self.get_sec_data()
        self.taxonomy = self.get_taxonomy()

    @weak_lru(maxsize=10)
    @limits(calls=10, period=1)
    def get_company_facts(self):
        url = 'https://data.sec.gov/api/xbrl/companyfacts/CIK' + self.cik + '.json'
        response = requests.get(url, headers=self.headers)
        json_request = response.json()

        return json_request

    @weak_lru(maxsize=10)
    @limits(calls=10, period=1)
    def get_company_submissions(self):
        url = 'https://data.sec.gov/submissions/CIK' + self.cik + '.json'
        response = requests.get(url, headers=self.headers)
        json_request = response.json()

        return json_request

    @weak_lru(maxsize=10)
    def get_latest_10k(self):
        df = pl.DataFrame(self.sec_submissions['filings']['recent'])
        df = df.filter(pl.col("primaryDocDescription") == "10-K").head(1)

        if len(df) > 0:
            report_date = df['reportDate'][0]
            year = int(report_date[:4])
            return year

        else:
            return None


    @weak_lru(maxsize=10)
    def align_fy_year(self, instant: bool):

        last_year = self.get_latest_10k()

        if last_year is None:
            return 0

        else:
            # ---

            df_filter = self.sec_data.filter(pl.col("form").is_in(["10-K", "8-K", "6-K", "20-F", "40-F", "6-F"]))

            if instant:
                df_filter = df_filter.filter(pl.col("frame").str.contains("I"))
            else:
                df_filter = df_filter.filter(~pl.col("frame").str.contains("I"))

            df_filter = df_filter.filter(pl.col("fp").str.contains("FY"))
            df_filter = df_filter.with_columns([pl.col("frame").str.extract(r"(\d+)", 1).cast(pl.Int32).alias("FY")])
            last_fy = df_filter["FY"].max()

            # ---

            diff = last_year - last_fy

            return diff

    @weak_lru(maxsize=10)
    def get_cik_code(self):

        url = "https://www.sec.gov/files/company_tickers_exchange.json"
        response = requests.get(url, headers=self.headers)
        response = response.json()["data"]

        dict_data = {i[2]: str(i[0]).zfill(10) for i in response}

        cik_code = dict_data[self.ticker]

        return cik_code

    @weak_lru(maxsize=10)
    def get_taxonomy(self):
        json_request = self.sec_company_facts

        facts = json_request.get('facts', {})

        if 'us-gaap' in facts:
            taxonomy = 'us-gaap'
        elif 'ifrs-full' in facts:
            taxonomy = 'ifrs-full'
        else:
            taxonomy = "None"

        return taxonomy

    @weak_lru(maxsize=10)
    def get_currency(self):
        json_request = self.sec_company_facts

        facts = json_request.get('facts', {})

        if 'us-gaap' in facts:
            data = facts['us-gaap']
            self.taxonomy = 'us-gaap'
        elif 'ifrs-full' in facts:
            data = facts['ifrs-full']
            self.taxonomy = 'ifrs-full'
        else:
            raise KeyError("Neither 'us-gaap' nor 'ifrs-full' found in facts")

        # ---

        currency_counts = {}

        for value in data.values():
            units = value.get('units', {})
            for currency in units:
                currency_counts[currency] = currency_counts.get(currency, 0) + 1

        preferred_currency = None
        max_count = 0

        for currency, count in currency_counts.items():
            if count > max_count:
                preferred_currency = currency
                max_count = count

        return preferred_currency

    @weak_lru(maxsize=10)
    def get_sec_data(self):
        json_request = self.sec_company_facts

        facts = json_request.get('facts', {})

        if 'us-gaap' in facts:
            data = facts['us-gaap']
            self.taxonomy = 'us-gaap'
        elif 'ifrs-full' in facts:
            data = facts['ifrs-full']
            self.taxonomy = 'ifrs-full'
        else:
            raise KeyError("Neither 'us-gaap' nor 'ifrs-full' found in facts")

        # ---

        records = []

        for key, value in data.items():
            units = value.get('units', {})

            # Iterate over all unit types
            for unit_type, entries in units.items():
                for entry in entries:
                    if 'frame' in entry and entry.get('form') in ['10-K', '10-Q', '8-K', '20-F', '40-F', '6-F', '6-K']:
                        records.append({
                            "key": key,
                            "description": value.get('description', ''),
                            "value": entry.get('val'),
                            "unit": unit_type,  # keep track of what unit it is (shares, USD, etc.)
                            "frame": entry.get('frame'),
                            "form": entry.get('form'),
                            "fp": entry.get('fp'),
                        })

        main_currency = self.get_currency()
        df = pl.DataFrame(records)
        df = df.filter(pl.col("unit").is_in(["shares", main_currency]))

        return df

    @weak_lru(maxsize=10)
    def get_sector(self):
        json_request = self.sec_submissions

        sector = json_request['sicDescription']

        return sector

    @weak_lru(maxsize=10)
    def get_year_end(self):
        json_request = self.sec_submissions

        year_end = json_request['fiscalYearEnd']
        year_end = datetime.strptime(year_end, "%m%d")
        year_end_formatted = year_end.strftime("%B %d")  # "June 30"

        return year_end_formatted

    @weak_lru(maxsize=10)
    def get_filings(self):
        json_request = self.sec_submissions

        df_filings = pl.DataFrame(json_request['filings']['recent'])

        return df_filings

    @weak_lru(maxsize=10)
    def get_dei(self):
        json_request = self.sec_company_facts

        facts = json_request.get('facts', {})
        dei = facts.get('dei', {})

        return dei

    @weak_lru(maxsize=10)
    def get_shares(self, year: int, quarter: int|None = None) -> int|None:

        annual_quarter = self.get_annual_quarter()

        inst_lookup_val = f"CY{year}Q{annual_quarter}I" if quarter is None else f"CY{year}Q{quarter}I"

        if annual_quarter == 1:
            inst_lookup_val_prev = f"CY{year-1}Q{4}I" if quarter is None else f"CY{year-1}Q{4}I"
        else:
            inst_lookup_val_prev = f"CY{year}Q{annual_quarter-1}I" if quarter is None else f"CY{year}Q{quarter-1}I"

        try:
            # Filtering
            shares = self.get_dei()['EntityCommonStockSharesOutstanding']['units']['shares']
            df_shares = pl.DataFrame(shares)

            try:
                df_shares_i = df_shares.filter(pl.col("frame").is_in([inst_lookup_val]))
                shares = df_shares_i.item(0,'val')

            except (IndexError, KeyError):
                df_shares_i = df_shares.filter(pl.col("frame").is_in([inst_lookup_val_prev]))
                shares = df_shares_i.item(0,'val')

            return shares

        except (IndexError, KeyError):
            try:
                df_shares = self.sec_data.filter(pl.col("key").is_in(["CommonStockSharesOutstanding", 'WeightedAverageNumberOfSharesOutstandingBasic']))
                df_shares_i = df_shares.filter(pl.col("frame").is_in([inst_lookup_val_prev]))
                shares = df_shares_i.item(0, 'value')

                return shares

            except (IndexError, KeyError):
                # print(f"*** SecApi: No outstanding share data found for {self.ticker}, returning None.")
                return None

    @weak_lru(maxsize=10)
    def get_annual_quarter(self):

        df_filter = self.sec_data.filter(pl.col("form").is_in(["10-K", "8-K", "6-K", "20-F", "40-F", "6-F"]))
        df_filter = df_filter.filter(pl.col("frame").str.contains("I"))
        df_filter = df_filter.filter(pl.col("fp").str.contains("FY"))
        df_filter = df_filter.with_columns(pl.col("frame").str.extract(r"Q(\d)").alias("quarter"))

        return df_filter.select(pl.col("quarter").cast(pl.Int64).mode())[0, 0]

    @weak_lru(maxsize=10)
    def financial_data_period(self, year: int, quarter: int|None = None) -> pl.DataFrame:

        annual_quarter = self.get_annual_quarter()

        # Filtering

        dur_lookup_val = f"CY{year}" if quarter is None else f"CY{year}Q{quarter}"
        inst_lookup_val = f"CY{year}Q{annual_quarter}I" if quarter is None else f"CY{year}Q{quarter}I"

        data = self.sec_data.filter(pl.col("frame").is_in([dur_lookup_val, inst_lookup_val]))
        data = data.unique()

        return data
