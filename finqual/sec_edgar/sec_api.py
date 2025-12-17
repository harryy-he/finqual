import requests
import polars as pl
import functools
import weakref
from ratelimit import limits
import gzip
import ijson
import io

from finqual.config.headers import sec_headers
from finqual.sec_edgar.entities.exceptions import CompanyIdCodeNotFoundError
from finqual.sec_edgar.entities.models import CompanyFacts, CompanySubmission, CompanyIdCode

def weak_lru(maxsize: int = 128, typed: bool = False):
    """
    LRU cache decorator that stores a **weak reference to `self`**.

    This pattern allows caching of instance methods while preventing memory leaks
    by avoiding strong references to the class instance.

    Parameters
    ----------
    maxsize : int, default 128
        Maximum size of the LRU cache.
    typed : bool, default False
        Whether to consider function argument types as part of the cache key.

    Returns
    -------
    callable
        Decorated method with LRU caching applied.
    """
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
    """
    Fill missing SEC XBRL `frame` values using surrounding context.

    SEC data often contains missing or inconsistent `frame` entries.
    This function builds fallback mappings based on start/end dates and
    applies several cleaning and consistency rules.

    Parameters
    ----------
    df : pl.DataFrame
        SEC Company Facts dataframe containing ``key``, ``start``, ``end``,
        ``frame`` and associated metadata.

    Returns
    -------
    pl.DataFrame
        Frame-consistent and cleaned dataframe.
    """
    # Creating mapping based on "key", "end" and "frame" columns
    frame_map_se = (
        df.filter(pl.col("frame").is_not_null())
        .select(["key", "start", "end", "frame"])
        .unique()
        .rename({"frame": "frame_se"})
    )

    frame_map_e = (
        df.filter(pl.col("frame").is_not_null())
        .select(["end", "frame"])
        .unique()
        .rename({"frame": "frame_e"})
    )

    df_se = df.join(frame_map_se, on=["start", "end"], how="left")
    df_see = df_se.join(frame_map_e, on=["end"], how="left")

    df_filled = df_see.with_columns(pl.coalesce(["frame", "frame_se", "frame_e"]).alias("frame_map")).drop(["frame_se", "frame_e"])

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
    ]).unique(subset=["key", "frame_map", "fp"], keep='last').drop("key_right")

    # ---

    # # The rule remove incorrect attribution of annual data to a quarter (e.g. Amazon CASHFLOW 2025Q3 results is incorrectly attributed as CY2025)
    df_filled = df_filled.filter(
        ~((pl.col("frame") == "None") & (pl.col("frame_map").str.contains(r"^CY\d{4}$")))
    )

    # ---

    df_filled = df_filled.sort(["key", "end", "frame_map"])

    return df_filled


def convert_to_quarters(df: pl.DataFrame) -> pl.DataFrame:
    """
    Convert cumulative financial values into true quarterly values.

    SEC Company Facts reports some values cumulatively.
    This converts them into Q1 / Q2 / Q3 / Q4 values automatically.

    Parameters
    ----------
    df : pl.DataFrame
        Input dataframe containing period-based SEC data (start, end, value, frame).

    Returns
    -------
    pl.DataFrame
        Updated dataframe including ``quarter_val`` and corrected ``val`` fields.
    """

    # Ensure dates are parsed
    df = df.with_columns([
        pl.col("start").str.strptime(pl.Date, strict=False),
        pl.col("end").str.strptime(pl.Date, strict=False),
    ])

    # Sort by key + end date
    df = df.sort(["key", "end", "start", "frame_map", "form", "fp"])

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
    """
    Interface for interacting with SEC EDGAR endpoints and standardized financial data.

    This class wraps SEC Company Facts, Submissions, and mapping utilities.
    It automatically extracts:
    - CIK metadata (CIK, ticker, name, exchange)
    - CompanyFacts financials
    - Taxonomy type (US-GAAP or IFRS)
    - Currency
    - DEI values
    - Sector
    - Latest 10-K year

    """
    def __init__(self, ticker_or_cik: str | int):
        """
        Initialize SEC client and retrieve all company-level metadata and facts.

        Parameters
        ----------
        ticker_or_cik : str or int
            Stock ticker (e.g., "AAPL") or raw CIK (e.g., "0000320193").
        """
        self.headers = sec_headers
        self.id_data = self.get_id_code(ticker_or_cik)
        self.facts_data = self.process_company_facts()
        self.submissions_data = self.process_company_submissions()

    # --- Company Facts

    @limits(calls=10, period=1)
    def process_company_facts(self) -> tuple[pl.DataFrame, str, str, dict]:
        """
        Download and process ``companyfacts`` records from the SEC API.

        Returns
        -------
        tuple
            (df, taxonomy, currency, dei)

            - **df** : polars.DataFrame
              Cleaned and quarterly-normalized company facts.
            - **taxonomy** : str
              Reporting taxonomy.
            - **currency** : str
              Most frequent reporting currency.
            - **dei** : dict
              Raw DEI (entity information) block.
        """
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{self.id_data.cik}.json"

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
                                if entry.get("form") not in ['10-K', '10-Q', '8-K', '20-F', '40-F', '6-F', '6-K', '10-K/A']:
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

        df = (
            pl.LazyFrame(rows)
            .filter(pl.col("unit").is_in(["shares", preferred_currency]))
            .pipe(map_missing_frames)  # <-- must accept LazyFrame
            .pipe(convert_to_quarters)  # <-- must accept LazyFrame
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
        
        company_facts = CompanyFacts(
            sec_data=df,
            taxonomy=taxonomy,
            currency=preferred_currency,
            dei=dei
        )
        
        return company_facts

    # --- CIK code

    @weak_lru(maxsize=4)
    def get_id_code(self, ticker_or_cik: str | int) -> CompanyIdCode:
        """
        Resolve a ticker or raw CIK to a full CompanyIdCode object.

        Parameters
        ----------
        ticker_or_cik : str or int
            Ticker (e.g. ``'AAPL'``) or numeric CIK.

        Returns
        -------
        CompanyIdCode
            Normalized identifier record.

        Raises
        ------
        CompanyIdCodeNotFoundError
            If the ticker or CIK is not found in the SEC index.
        """
        url = "https://www.sec.gov/files/company_tickers_exchange.json"
        ticker_or_cik = str(ticker_or_cik)
        
        with requests.get(url, headers=self.headers, stream=True) as r:
            gz = gzip.GzipFile(fileobj=r.raw)
            text_stream = io.TextIOWrapper(gz, encoding="utf‑8", errors="replace")

            # Each item in the JSON array is like: [cik, title, ticker, exchange]
            for item in ijson.items(text_stream, "data.item"):
                cik, name, ticker, exchange = item
                if ticker.lower() == ticker_or_cik.lower() or str(cik) == ticker_or_cik:
                    payload = {
                        "cik": str(cik).zfill(10),
                        "name": name,
                        "ticker": ticker,
                        "exchange": exchange
                        } 
                    return CompanyIdCode(**payload)
                
            raise CompanyIdCodeNotFoundError(ticker_or_cik)

    # --- Company submissions

    @limits(calls=10, period=1)
    def process_company_submissions(self) -> CompanySubmission:
        """
        Download and parse the SEC ``submissions`` file for the company.

        Returns
        -------
        tuple
            (latest_10k, sector)

            - **latest_10k** : int or None
              Most recent fiscal year filed as a 10-K or 20-F.
            - **sector** : str
              SIC industry description.
        """
        url = 'https://data.sec.gov/submissions/CIK' + self.id_data.cik + '.json'
        response = requests.get(url, headers=self.headers)
        json_request = response.json()

        df = pl.DataFrame(json_request['filings']['recent'])

        # --- Getting URLs

        df = df.filter(pl.col("primaryDocDescription").is_in(["10-K", "10-Q", "20-F", "40-F"]))

        df = df.with_columns(
            (pl.lit("https://www.sec.gov/ix?doc=/Archives/edgar/data/")
                + pl.col("accessionNumber").str.slice(0, 10)
                + "/"
                + pl.col("accessionNumber").str.replace_all("-", "")
                + "/"
                + pl.col("primaryDocument")
                ).alias("URL")
        )

        df = df["reportDate", "primaryDocDescription", "URL"]

        # --- Latest 10K

        df_latest = df.filter(pl.col("primaryDocDescription").is_in(["10-K", "20-F"])).head(1)

        if len(df_latest) > 0:
            report_date = df_latest['reportDate'][0]
            year = int(report_date[:4])
            latest_10k = year

        else:
            report_date = None
            latest_10k = None

        # --- Sector

        sector = json_request['sicDescription']
        
        return CompanySubmission(latest_10k=latest_10k, report_date=report_date, sector=sector, reports=df)

    # --- In-class methods (no downloads)

    @weak_lru(maxsize=4)
    def get_annual_quarter(self) -> int:
        """
        Determine which quarter represents the company's fiscal year-end
        (e.g., many firms have FY ending in Q4, some in Q1, etc.).

        Returns
        -------
        int
            Fiscal year-end quarter number (1–4).
        """
        df_filter = self.facts_data.sec_data.filter(pl.col("form").cast(pl.Utf8).is_in(["10-K", "8-K", "6-K", "20-F", "40-F", "6-F"]))
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

    @weak_lru(maxsize=4)
    def get_shares(self, year: int, quarter: int | None = None) -> int | None:
        """
        Retrieve outstanding share count for a given year and quarter.

        Parameters
        ----------
        year : int
            Fiscal year (calendar CY).
        quarter : int, optional
            Quarter number (1–4). If omitted, uses fiscal year-end quarter.

        Returns
        -------
        int or None
            Share count, or None if unavailable.
        """
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
            shares = self.facts_data.dei['EntityCommonStockSharesOutstanding']['units']['shares']
            df_shares = pl.DataFrame(shares)

            try:
                df_shares_i = df_shares.filter(pl.col("frame").cast(pl.Utf8).is_in([inst_lookup_val]))
                shares = df_shares_i.item(0, 'val')

            except (IndexError, KeyError):
                df_shares_i = df_shares.filter(pl.col("frame").cast(pl.Utf8).is_in([inst_lookup_val_prev]))
                shares = df_shares_i.item(0, 'val')

            return shares

        # ...else use the SEC data
        except (IndexError, KeyError):
            try:
                df_shares = self.facts_data.sec_data.filter(pl.col("key").cast(pl.Utf8).is_in(["CommonStockSharesOutstanding", 'WeightedAverageNumberOfSharesOutstandingBasic']))
                df_shares_i = df_shares.filter(pl.col("frame").cast(pl.Utf8).is_in([inst_lookup_val_prev]))
                shares = df_shares_i.item(0, 'val')

                return shares

            except (IndexError, KeyError):
                # print(f"*** SecApi: No outstanding share data found for {self.ticker}, returning None.")
                return None

    @weak_lru(maxsize=4)
    def align_fy_year(self, instant: bool) -> int:
        """
        Compute fiscal-year alignment shift between SEC reporting and calendar
        year frames.

        Parameters
        ----------
        instant : bool
            Whether to use instant-type frames (frame contains ``"I"``).

        Returns
        -------
        int
            Shift in years required to align SEC fiscal years to calendar years.
        """
        last_year = self.submissions_data.latest_10k

        if last_year is None:
            return 0

        else:
            # ---
            df = self.facts_data.sec_data.select(["form", "frame", "fp"])

            df_filter = df.filter(pl.col("form").cast(pl.Utf8).is_in(["10-K", "8-K", "6-K", "20-F", "40-F", "6-F"]))

            frame_str = pl.col("frame").cast(pl.Utf8)
            fp_str = pl.col("fp").cast(pl.Utf8)

            if instant:
                df_filter = df_filter.filter(frame_str.str.contains("I"))
            else:
                df_filter = df.filter(~frame_str.str.contains("I") & ~frame_str.str.contains("Q"))

            df_filter = df_filter.filter(fp_str.str.contains("FY"))
            df_filter = df_filter.with_columns([frame_str.str.extract(r"(\d+)", 1).cast(pl.Int32).alias("FY")])
            last_fy = df_filter["FY"].max()

            # ---

            diff = last_year - last_fy

            return diff

    @weak_lru(maxsize=4)
    def financial_data_period(self, year: int, quarter: int | None = None) -> pl.DataFrame:
        """
        Return SEC financial data for a given year or year-quarter.

        Parameters
        ----------
        year : int
            Calendar year.
        quarter : int, optional
            Quarter (1–4). If omitted, returns full-year data.

        Returns
        -------
        polars.DataFrame
            Records matching the period's ``frame_map``.
        """
        annual_quarter = self.get_annual_quarter()

        # Filtering

        dur_lookup_val = f"CY{year}" if quarter is None else f"CY{year}Q{quarter}"
        inst_lookup_val = f"CY{year}Q{annual_quarter}I" if quarter is None else f"CY{year}Q{quarter}I"

        data = self.facts_data.sec_data.filter(pl.col("frame_map").cast(pl.Utf8).is_in([dur_lookup_val, inst_lookup_val]))
        data = data.unique()

        return data
