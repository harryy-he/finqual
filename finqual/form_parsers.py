from .form_4 import retrieve_form_4
from .form_13 import retrieve_form_13f_aggregated
from finqual.config.headers import sec_headers

import functools
import gzip
import ijson
import io
import polars as pl
from ratelimit import limits
import requests
import weakref

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from finqual.sec_edgar.entities.exceptions import CompanyIdCodeNotFoundError
from finqual.sec_edgar.entities.models import CompanySubmission, CompanyIdCode


def weak_lru(maxsize: int = 128, typed: bool = False):
    """
    LRU cache decorator that stores a weak reference to 'self'.

    This decorator is used to cache instance method results while avoiding
    memory leaks by keeping only a weak reference to the object.

    Parameters
    ----------
    maxsize : int, optional
        Maximum size of the LRU cache (default is 128).
    typed : bool, optional
        If True, arguments of different types will be cached separately.

    Returns
    -------
    callable
        Decorator function to wrap methods with a weak LRU cache.
    """
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

def _parse_period_to_start_date(period: str) -> datetime:
    """
    Convert period string like '1y', '6m', '30d' into a start datetime.
    """
    now = datetime.utcnow()

    unit = period[-1].lower()
    value = int(period[:-1])

    if unit == "y":
        return now - relativedelta(years=value)
    elif unit == "m":
        return now - relativedelta(months=value)
    elif unit == "d":
        return now - timedelta(days=value)
    else:
        raise ValueError("Invalid period format. Use '1y', '6m', '30d', etc.")

class FinqualForms:
    """
    Interface for interacting with SEC EDGAR endpoints and standardized forms.
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
        self.submissions_data = self.process_company_submissions()

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
        ticker_or_cik = str(ticker_or_cik)
        value = str(ticker_or_cik).strip()

        # --- It is CIK code

        if value.isdigit():
            cik_padded = value.zfill(10)
            url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"

            r = requests.get(url, headers=self.headers)
            if r.status_code == 200:
                data = r.json()

                payload = {
                    "cik": cik_padded,
                    "name": data.get("name"),
                    "ticker": (data.get("tickers") or ["None"])[0],
                    "exchange": (data.get("exchanges") or ["None"])[0]
                }
                return CompanyIdCode(**payload)

            raise CompanyIdCodeNotFoundError(ticker_or_cik)

        # --- Ticker

        url = "https://www.sec.gov/files/company_tickers_exchange.json"

        with requests.get(url, headers=self.headers, stream=True) as r:
            gz = gzip.GzipFile(fileobj=r.raw)
            text_stream = io.TextIOWrapper(gz, encoding="utf‑8",
                                           errors="replace")

            # Each item in the JSON array is like: [cik, title, ticker, exchange]
            for item in ijson.items(text_stream, "data.item"):
                cik, name, ticker, exchange = item
                if ticker.lower() == ticker_or_cik.lower() or str(
                        cik) == ticker_or_cik:
                    payload = {
                        "cik": str(cik).zfill(10),
                        "name": name,
                        "ticker": ticker,
                        "exchange": exchange
                    }
                    return CompanyIdCode(**payload)

        raise CompanyIdCodeNotFoundError(ticker_or_cik)

    @weak_lru(maxsize=4)
    def get_form4(self) -> pl.DataFrame:
        """
        Returns the metadata dataframe of Form 4 filings
        """

        # --- Filter relevant filings
        df = self.submissions_data.filter(pl.col("form").is_in(["4"]))

        # --- Build document URLs
        df = df.with_columns(
            (
                pl.lit("https://www.sec.gov/Archives/edgar/data/")
                + pl.lit(str(int(self.id_data.cik)))
                + "/"
                + pl.col("accessionNumber").str.replace_all("-", "")
                + "/"
                + pl.col("primaryDocument")
                .str.split("/")
                .list.last()
            ).alias("URL")
        )

        # ---

        if len(df) < 0:
            return None

        else:
            return df

    @weak_lru(maxsize=4)
    def get_form13(self) -> pl.DataFrame:
        """
        Returns the metadata dataframe of Form 4 filings
        """

        # --- Filter relevant filings
        df = self.submissions_data.filter(pl.col("form").is_in(["13-F", "13F-HR", "13F", "13F-HR/A"]))

        # --- Build document URLs
        df = df.with_columns(
            (
                pl.lit("https://www.sec.gov/Archives/edgar/data/")
                + pl.lit(str(int(self.id_data.cik)))
                + "/"
                + pl.col("accessionNumber").str.replace_all("-", "")
            ).alias("URL")
        )

        # ---

        if len(df) < 0:
            return None

        else:
            return df

    @limits(calls=10, period=1)
    def process_company_submissions(self) -> pl.DataFrame:
        """
        Download and parse the SEC `submissions` file for the company.

        Returns
        -------
        CompanySubmission
            - latest_10k : int or None
                Most recent fiscal year filed as a 10-K or 20-F.
            - report_date : str or None
                Report date of the latest 10-K or 20-F.
            - sector : str
                SIC industry description.
            - reports : polars.DataFrame
                Filtered filings with URLs.
        """

        url = f"https://data.sec.gov/submissions/CIK{self.id_data.cik}.json"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()

        json_request = response.json()

        df = pl.DataFrame(json_request["filings"]["recent"])

        return df

    def _process_form4_by_accession(self, df_filings: pl.DataFrame, accession_number: str) -> pl.DataFrame:
        """
        Retrieve and normalize a single Form 4 filing by accession number.
        """

        row = df_filings.filter(pl.col("accessionNumber") == accession_number)

        if row.is_empty():
            raise ValueError(f"Accession {accession_number} not found.")

        url = row["URL"][0]
        filing_date = row["filingDate"][0]
        report_date = row["reportDate"][0]

        df_form4 = retrieve_form_4(url, self.headers)

        df_form4 = df_form4.with_columns([
            pl.lit(filing_date, dtype=pl.Utf8).alias("filingDate"),
            pl.lit(report_date, dtype=pl.Utf8).alias("reportDate"),
            pl.lit(accession_number, dtype=pl.Utf8).alias("accessionNumber"),
        ])

        return df_form4

    def get_insider_transactions_period(self, period: str) -> pl.DataFrame:
        """
        Retrieve insider transactions within a given period.
        Example: '1y', '6m', '30d'
        """

        df = self.get_form4()

        if df is None or df.is_empty():
            print("No Form 4 filings found.")

        start_date = _parse_period_to_start_date(period)

        # Ensure filingDate is datetime
        df = df.with_columns(pl.col("filingDate").str.strptime(pl.Date, strict=False))

        # Filter filings within period
        df_filtered = df.filter(pl.col("filingDate") >= start_date.date())

        if df_filtered.is_empty():
            return pl.DataFrame()

        dfs = []

        for i in df_filtered["accessionNumber"]:
            try:
                dfs.append(self._process_form4_by_accession(df_filtered, i))
            except Exception:
                continue

        if not dfs:
            return pl.DataFrame()

        return pl.concat(dfs, how="vertical_relaxed")

    def _process_form13_by_accession(self, df_filings: pl.DataFrame, accession_number: str) -> pl.DataFrame:
        """
        Retrieve and normalize a single Form 13 filing by accession number.
        """

        row = df_filings.filter(pl.col("accessionNumber") == accession_number)

        if row.is_empty():
            raise ValueError(f"Accession {accession_number} not found.")

        url = row["URL"][0] + '/index.json'
        filing_date = row["filingDate"][0]
        report_date = row["reportDate"][0]

        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()

        files = resp.json()["directory"]["item"]

        # -------------------------------
        # Find holdings XML
        # -------------------------------
        xml_files = [
            f["name"]
            for f in files
            if f["name"].lower().endswith(".xml")
               and f["name"].lower() != "primary_doc.xml"
        ]

        if not xml_files:
            raise ValueError(
                f"No holdings XML found for accession {accession_number}"
            )

        # In this case it will be 50240.xml
        info_xml_url = row["URL"][0] + f'/{xml_files[0]}'

        df_form13 = retrieve_form_13f_aggregated(info_xml_url, self.headers)

        df_form13 = df_form13.with_columns([
            pl.lit(filing_date, dtype=pl.Utf8).alias("filingDate"),
            pl.lit(report_date, dtype=pl.Utf8).alias("reportDate"),
            pl.lit(accession_number, dtype=pl.Utf8).alias("accessionNumber"),
        ])

        return df_form13

    def get_form_13_period(self, n: int) -> pl.DataFrame:
        """
        Retrieve insider transactions within a given period.
        Example: '1y', '6m', '30d'
        """

        df = self.get_form13()

        if df is None or df.is_empty():
            print("No Form 13 filings found.")

        # Ensure filingDate is datetime
        df = df.with_columns(pl.col("filingDate").str.strptime(pl.Date, strict=False))

        # Sort descending by filingDate (or reportDate if preferred)
        df_sorted = df.sort("filingDate", descending=True)

        # Take latest N filings
        df_latest = df_sorted.head(n)

        if df_latest.is_empty():
            return pl.DataFrame()

        dfs = []

        for i in df_latest["accessionNumber"]:
            try:
                dfs.append(self._process_form13_by_accession(df_latest, i))
            except Exception:
                continue

        if not dfs:
            return pl.DataFrame()

        df_agg = pl.concat(dfs, how="vertical_relaxed")

        df_agg = df_agg.with_columns(
            pl.lit(self.id_data.cik).alias("CIK")
        )

        df_agg = df_agg.select(["CIK"] + [c for c in df_agg.columns if c != "CIK"])

        return df_agg
