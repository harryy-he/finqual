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

def map_missing_frames(df: pl.DataFrame) -> pl.DataFrame:

    # Creating mapping based on "key", "end" and "frame" columns
    frame_map = (
        df.filter(pl.col("frame").is_not_null())
        .select(["key", "end", "frame"])
        .unique()
    )

    # Mapping to dataframe
    df_filled = (
        df.join(frame_map, on=["end"], how="left", suffix="_mapped")
        .with_columns(
            pl.when(pl.col("frame").is_null())
            .then(pl.col("frame_mapped"))
            .otherwise(pl.col("frame"))
            .alias("frame_map")
        )
        .drop("frame_mapped")
    )

    # Remove any I's from "frame_map" col
    df_filled = df_filled.with_columns([
         pl.col("frame_map").str.replace("I", "")
        .alias("frame_map")
    ])

    # Add back any I's for when "start" col is "None"
    df_filled = df_filled.with_columns([
        pl.when(pl.col("start") == "None")
        .then(pl.col("frame_map") + "I")
        .otherwise(pl.col("frame_map"))
        .alias("frame_map")
    ]).unique(subset=["key", "frame_map"], keep='last')

    df_filled = df_filled.sort(["key", "end", "frame_map"])

    return df_filled


def convert_to_quarters(df: pl.DataFrame) -> pl.DataFrame:
    """
    Convert cumulative SEC values into true quarter-by-quarter values.
    Works on a Polars DataFrame with columns: key, start, end, value, ...
    Handles all keys automatically.
    """

    # Ensure dates are parsed
    df = df.with_columns([
        pl.col("start").str.strptime(pl.Date, strict=False),
        pl.col("end").str.strptime(pl.Date, strict=False),
    ])

    # Sort by key + end date
    df = df.sort(["key", "end"])

    # Compute quarter values within each key
    df_quarters = df.with_columns([
        (pl.col("val") - pl.col("val").shift(1)).over(["key", "start"]).alias("quarter_val"),
        pl.col("end").shift(1).over(["key", "start"]).alias("prev_end")
        ])

    # If quarter_val is empty, then fill with "val"
    df_quarters = df_quarters.with_columns([
        pl.when(pl.col("quarter_val").is_null())
        .then(pl.col("val"))
        .otherwise(pl.col("quarter_val"))
        .alias("quarter_val"),
        ])

    # If frame_map is "I" then set "quarter_val" to "val"
    df_quarters = df_quarters.with_columns([
        pl.when(pl.col("frame_map").str.contains("I"))
        .then(pl.col("val"))
        .otherwise(pl.col("quarter_val"))
        .alias("quarter_val")
    ])

    df_quarters = df_quarters.filter(pl.col("quarter_val") != 0)

    # Setting "val" to the correct value
    df_quarters = df_quarters.with_columns([
        pl.when(pl.col("frame_map").str.contains("Q"))
        .then(pl.col("quarter_val"))
        .otherwise(pl.col("val"))
        .alias("val")
    ])

    return df_quarters.select(["key", "start", "end", "quarter_val", "val", "unit", "frame", "frame_map", "form", "fp"])

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

        df = pl.DataFrame(self.get_company_submissions()['filings']['recent'])
        df = df.filter(pl.col("primaryDocDescription").is_in(["10-K", "20-F"])).head(1)

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

            df_filter = self.sec_data.filter(pl.col("form").cast(pl.Utf8).is_in(["10-K", "8-K", "6-K", "20-F", "40-F", "6-F"]))

            frame_str = pl.col("frame").cast(pl.Utf8)
            fp_str = pl.col("fp").cast(pl.Utf8)

            if instant:
                df_filter = df_filter.filter(frame_str.str.contains("I"))
            else:
                df_filter = df_filter.filter(~frame_str.str.contains("I"))
                df_filter = df_filter.filter(~frame_str.str.contains("Q"))

            df_filter = df_filter.filter(fp_str.str.contains("FY"))
            df_filter = df_filter.with_columns([frame_str.str.extract(r"(\d+)", 1).cast(pl.Int32).alias("FY")])
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
        json_request = self.get_company_facts()

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
        json_request = self.get_company_facts()

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
        json_request = self.get_company_facts()

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
                    if entry.get('form') in ['10-K', '10-Q', '8-K', '20-F', '40-F', '6-F', '6-K']:
                        records.append({
                            "key": key,
                            "start": entry.get('start', 'None'),
                            "end": entry.get('end', 'None'),
                            "description": value.get('description', ''),
                            "val": entry.get('val'),
                            "unit": unit_type,  # keep track of what unit it is (shares, USD, etc.)
                            "frame": entry.get('frame'),
                            "form": entry.get('form'),
                            "fp": entry.get('fp'),
                        })

        main_currency = self.get_currency()
        df = pl.DataFrame(records)
        df = df.filter(pl.col("unit").cast(pl.Utf8).is_in(["shares", main_currency]))

        df = map_missing_frames(df)
        df = convert_to_quarters(df)

        df = df.unique()

        df = df.with_columns([
            pl.col("quarter_val").cast(pl.Float64),
            pl.col("val").cast(pl.Float64),
            pl.col("key").cast(pl.Categorical),
            pl.col("unit").cast(pl.Categorical),
            pl.col("frame").cast(pl.Categorical),
            pl.col("frame_map").cast(pl.Categorical),
            pl.col("form").cast(pl.Categorical),
            pl.col("fp").cast(pl.Categorical)
        ])

        buf = df.write_ipc(None, compression="zstd")

        return df

    @weak_lru(maxsize=10)
    def get_sector(self):
        json_request = self.get_company_submissions()

        sector = json_request['sicDescription']

        return sector

    @weak_lru(maxsize=10)
    def get_year_end(self):
        json_request = self.get_company_submissions()

        year_end = json_request['fiscalYearEnd']
        year_end = datetime.strptime(year_end, "%m%d")
        year_end_formatted = year_end.strftime("%B %d")  # "June 30"

        return year_end_formatted

    @weak_lru(maxsize=10)
    def get_filings(self):
        json_request = self.get_company_submissions()

        df_filings = pl.DataFrame(json_request['filings']['recent'])

        return df_filings

    @weak_lru(maxsize=10)
    def get_dei(self):
        json_request = self.get_company_facts()

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
                df_shares_i = df_shares.filter(pl.col("frame").cast(pl.Utf8).is_in([inst_lookup_val]))
                shares = df_shares_i.item(0,'val')

            except (IndexError, KeyError):
                df_shares_i = df_shares.filter(pl.col("frame").cast(pl.Utf8).is_in([inst_lookup_val_prev]))
                shares = df_shares_i.item(0,'val')

            return shares

        except (IndexError, KeyError):
            try:
                df_shares = self.sec_data.filter(pl.col("key").cast(pl.Utf8).is_in(["CommonStockSharesOutstanding", 'WeightedAverageNumberOfSharesOutstandingBasic']))
                df_shares_i = df_shares.filter(pl.col("frame").cast(pl.Utf8).is_in([inst_lookup_val_prev]))
                shares = df_shares_i.item(0, 'val')

                return shares

            except (IndexError, KeyError):
                # print(f"*** SecApi: No outstanding share data found for {self.ticker}, returning None.")
                return None

    @weak_lru(maxsize=10)
    def get_annual_quarter(self):

        df_filter = self.sec_data.filter(pl.col("form").cast(pl.Utf8).is_in(["10-K", "8-K", "6-K", "20-F", "40-F", "6-F"]))

        frame_str = pl.col("frame").cast(pl.Utf8)

        df_filter = (
            df_filter
            .filter(frame_str.str.contains("I"))  # filter frame containing "I"
            .filter(pl.col("fp").cast(pl.Utf8).str.contains("FY"))  # fp contains "FY"
            .with_columns(
                frame_str.str.extract(r"Q(\d)").alias("quarter")  # extract quarter
            )
        )

        # Cast 'quarter' back to categorical to save memory
        df_filter = df_filter.with_columns(pl.col("quarter").cast(pl.Categorical))

        return df_filter.select(pl.col("quarter").cast(pl.Int64).mode())[0, 0]

    @weak_lru(maxsize=10)
    def financial_data_period(self, year: int, quarter: int|None = None) -> pl.DataFrame:

        annual_quarter = self.get_annual_quarter()

        # Filtering

        dur_lookup_val = f"CY{year}" if quarter is None else f"CY{year}Q{quarter}"
        inst_lookup_val = f"CY{year}Q{annual_quarter}I" if quarter is None else f"CY{year}Q{quarter}I"

        data = self.sec_data.filter(pl.col("frame_map").cast(pl.Utf8).is_in([dur_lookup_val, inst_lookup_val]))

        data = data.unique()

        return data
