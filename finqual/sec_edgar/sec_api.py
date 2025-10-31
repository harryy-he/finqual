import requests
import polars as pl
from datetime import datetime
import functools
import weakref
from ratelimit import limits
import gzip
import ijson
import io

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

        facts_data = self.process_company_facts()

        self.sec_data = facts_data[0]
        self.taxonomy = facts_data[1]
        self.currency = facts_data[2]
        self.dei = facts_data[3]

        del facts_data

        submissions_data = self.process_company_submissions()

        self.latest_10k = submissions_data[0]
        self.sector = submissions_data[1]

        del submissions_data

    # --- Company Facts

    @limits(calls=10, period=1)
    def process_company_facts(self):
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{self.cik}.json"

        rows = []
        currency_counts = {}

        dei = None
        taxonomy = None

        with requests.get(url, headers=self.headers, stream=True) as r:
            gz = gzip.GzipFile(fileobj=r.raw)
            text_stream = io.TextIOWrapper(gz, encoding="utf‑8", errors="replace")

            parser = ijson.kvitems(text_stream, "facts")

            for tx, fact_dict in parser:
                # Getting DEI
                if tx == 'dei':
                    dei = fact_dict
                    continue

                # Getting taxonomy - enforces order
                elif tx in ("us-gaap", "ifrs-full"):
                    taxonomy = tx

                    # Getting facts
                    for key, value in fact_dict.items():
                        units = value.get("units", {})
                        desc = value.get("description", "")
                        for unit_type, entries in units.items():
                            currency_counts[unit_type] = currency_counts.get(unit_type, 0) + 1  # Counting currencies

                            for entry in entries:
                                if entry.get("form") not in ['10-K', '10-Q', '8-K', '20-F', '40-F', '6-F', '6-K']:
                                    continue

                                rows.append({
                                    "key": key,
                                    "start": entry.get("start", "None"),
                                    "end": entry.get("end", "None"),
                                    "description": desc,
                                    "val": entry.get("val"),
                                    "unit": unit_type,
                                    "frame": entry.get("frame"),
                                    "form": entry.get("form"),
                                    "fp": entry.get("fp"),
                                })
                    # if you only want first taxonomy, break now
                    break

        preferred_currency = max(currency_counts, key=currency_counts.get)

        df = pl.DataFrame(rows)
        df = df.filter(pl.col("unit").is_in(["shares", preferred_currency]))

        df = map_missing_frames(df)
        df = convert_to_quarters(df)

        # Lazy casting and deduplication
        df = (
            df.lazy()
            .with_columns([
                pl.col("quarter_val").cast(pl.Float64),
                pl.col("val").cast(pl.Float64),
                pl.col("key").cast(pl.Categorical),
                pl.col("unit").cast(pl.Categorical),
                pl.col("frame").cast(pl.Categorical),
                pl.col("frame_map").cast(pl.Categorical),
                pl.col("form").cast(pl.Categorical),
                pl.col("fp").cast(pl.Categorical),
            ])
            .collect()
        )

        return df, taxonomy, preferred_currency, dei

    # --- CIK code

    @weak_lru(maxsize=10)
    def get_cik_code(self):

        url = "https://www.sec.gov/files/company_tickers_exchange.json"

        with requests.get(url, headers=self.headers, stream=True) as r:
            gz = gzip.GzipFile(fileobj=r.raw)
            text_stream = io.TextIOWrapper(gz, encoding="utf‑8", errors="replace")

            # Each item in the JSON array is like: [cik, title, ticker, exchange]
            for item in ijson.items(text_stream, "data.item"):
                cik, title, ticker, exchange = item
                if ticker.lower() == self.ticker.lower():
                    return str(cik).zfill(10)

    # --- Company submissions

    @weak_lru(maxsize=10)
    @limits(calls=10, period=1)
    def process_company_submissions(self):

        url = 'https://data.sec.gov/submissions/CIK' + self.cik + '.json'
        response = requests.get(url, headers=self.headers)
        json_request = response.json()

        # --- Latest 10K

        df = pl.DataFrame(json_request['filings']['recent'])
        df = df.filter(pl.col("primaryDocDescription").is_in(["10-K", "20-F"])).head(1)

        if len(df) > 0:
            report_date = df['reportDate'][0]
            year = int(report_date[:4])
            latest_10k = year

        else:
            latest_10k = None

        # --- Sector

        sector = json_request['sicDescription']

        return latest_10k, sector

    # TODO: Remove/deprecate
    # @weak_lru(maxsize=10)
    # @limits(calls=10, period=1)
    # def get_company_submissions(self):
    #     url = 'https://data.sec.gov/submissions/CIK' + self.cik + '.json'
    #     response = requests.get(url, headers=self.headers)
    #     json_request = response.json()
    #
    #     return json_request
    #
    # @weak_lru(maxsize=10)
    # def get_latest_10k(self):
    #
    #     df = pl.DataFrame(self.get_company_submissions()['filings']['recent'])
    #     df = df.filter(pl.col("primaryDocDescription").is_in(["10-K", "20-F"])).head(1)
    #
    #     if len(df) > 0:
    #         report_date = df['reportDate'][0]
    #         year = int(report_date[:4])
    #         return year
    #
    #     else:
    #         return None
    #
    # @weak_lru(maxsize=10)
    # def get_sector(self):
    #     json_request = self.get_company_submissions()
    #
    #     sector = json_request['sicDescription']
    #
    #     return sector
    #
    # @weak_lru(maxsize=10)
    # def get_year_end(self):
    #     json_request = self.get_company_submissions()
    #
    #     year_end = json_request['fiscalYearEnd']
    #     year_end = datetime.strptime(year_end, "%m%d")
    #     year_end_formatted = year_end.strftime("%B %d")  # "June 30"
    #
    #     return year_end_formatted
    #
    # @weak_lru(maxsize=10)
    # def get_filings(self):
    #     json_request = self.get_company_submissions()
    #
    #     df_filings = pl.DataFrame(json_request['filings']['recent'])
    #
    #     return df_filings

    # ---

    @weak_lru(maxsize=10)
    def get_annual_quarter(self):

        df_filter = self.sec_data.filter(pl.col("form").cast(pl.Utf8).is_in(["10-K", "8-K", "6-K", "20-F", "40-F", "6-F"]))
        frame_str = pl.col("frame").cast(pl.Utf8)

        df_filter = (df_filter
            .filter(frame_str.str.contains("I"))  # filter frame containing "I"
            .filter(pl.col("fp").cast(pl.Utf8).str.contains("FY"))  # fp contains "FY"
            .with_columns(frame_str.str.extract(r"Q(\d)").alias("quarter")  # extract quarter
            )
        )

        # Cast 'quarter' back to categorical to save memory
        df_filter = df_filter.with_columns(pl.col("quarter").cast(pl.Categorical))

        return int(df_filter.select(pl.col("quarter").mode())[0, 0])

    @weak_lru(maxsize=10)
    def get_shares(self, year: int, quarter: int|None = None) -> int|None:

        annual_quarter = self.get_annual_quarter()

        # --- Compute lookup values

        inst_lookup_val = f"CY{year}Q{annual_quarter}I" if quarter is None else f"CY{year}Q{quarter}I"

        if annual_quarter == 1:
            inst_lookup_val_prev = f"CY{year-1}Q4I" if quarter is None else f"CY{year-1}Q4I"
        else:
            inst_lookup_val_prev = f"CY{year}Q{annual_quarter-1}I" if quarter is None else f"CY{year}Q{quarter-1}I"

        # Using DEI dataframe...
        try:
            # Filtering
            shares = self.dei['EntityCommonStockSharesOutstanding']['units']['shares']
            df_shares = pl.DataFrame(shares)

            try:
                df_shares_i = df_shares.filter(pl.col("frame").cast(pl.Utf8).is_in([inst_lookup_val]))
                shares = df_shares_i.item(0,'val')

            except (IndexError, KeyError):
                df_shares_i = df_shares.filter(pl.col("frame").cast(pl.Utf8).is_in([inst_lookup_val_prev]))
                shares = df_shares_i.item(0,'val')

            return shares

        # ...else use the SEC data
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
    def align_fy_year(self, instant: bool):

        last_year = self.latest_10k

        if last_year is None:
            return 0

        else:
            # ---
            df = self.sec_data.select(["form", "frame", "fp"])

            df_filter = df.filter(pl.col("form").cast(pl.Utf8).is_in(["10-K", "8-K", "6-K", "20-F", "40-F", "6-F"]))

            frame_str = pl.col("frame").cast(pl.Utf8)
            fp_str = pl.col("fp").cast(pl.Utf8)

            if instant:
                df_filter = df_filter.filter(frame_str.str.contains("I"))
            else:
                df = df.filter(~frame_str.str.contains("I") & ~frame_str.str.contains("Q"))

            df_filter = df_filter.filter(fp_str.str.contains("FY"))
            df_filter = df_filter.with_columns([frame_str.str.extract(r"(\d+)", 1).cast(pl.Int32).alias("FY")])
            last_fy = df_filter["FY"].max()

            # ---

            diff = last_year - last_fy

            return diff

    @weak_lru(maxsize=10)
    def financial_data_period(self, year: int, quarter: int|None = None) -> pl.DataFrame:

        annual_quarter = self.get_annual_quarter()

        # Filtering

        dur_lookup_val = f"CY{year}" if quarter is None else f"CY{year}Q{quarter}"
        inst_lookup_val = f"CY{year}Q{annual_quarter}I" if quarter is None else f"CY{year}Q{quarter}I"

        data = self.sec_data.filter(pl.col("frame_map").cast(pl.Utf8).is_in([dur_lookup_val, inst_lookup_val]))

        data = data.unique()

        return data
