"""
High-level interface around SEC EDGAR submissions for a single company.

Resolves ticker/CIK, downloads the submissions index, filters Form 4 and 13F
filings, fetches the underlying XML via :mod:`form_4` / :mod:`form_13`, and
returns aggregated insider-transaction / 13F holdings DataFrames.
"""

from __future__ import annotations

import gzip
import io
from datetime import datetime, timedelta, timezone

import ijson
import polars as pl
import requests
from dateutil.relativedelta import relativedelta
from ratelimit import limits

from finqual._cache import weak_lru
from finqual.config.headers import sec_headers
from finqual.sec_edgar.entities.exceptions import CompanyIdCodeNotFoundError
from finqual.sec_edgar.entities.models import CompanyIdCode

from .form_4 import retrieve_form_4
from .form_13 import retrieve_form_13f_aggregated

# HTTP request defaults for SEC endpoints.
_REQUEST_TIMEOUT_SECS = 30


def _parse_period_to_start_date(period: str) -> datetime:
    """
    Convert a period string like ``'1y'``, ``'6m'``, ``'30d'`` into a UTC start datetime.

    Parameters
    ----------
    period : str
        Period suffixed with ``y`` (years), ``m`` (months) or ``d`` (days).

    Returns
    -------
    datetime
        UTC datetime ``period`` ago.

    Raises
    ------
    ValueError
        If ``period`` is empty or has an unsupported suffix.
    """
    if not period or len(period) < 2:
        raise ValueError("Invalid period format. Use '1y', '6m', '30d', etc.")

    now = datetime.now(timezone.utc)
    unit = period[-1].lower()
    value = int(period[:-1])

    if unit == "y":
        return now - relativedelta(years=value)
    if unit == "m":
        return now - relativedelta(months=value)
    if unit == "d":
        return now - timedelta(days=value)

    raise ValueError("Invalid period format. Use '1y', '6m', '30d', etc.")


class FinqualForms:
    """
    Interface for interacting with SEC EDGAR endpoints and standardised forms.
    """

    def __init__(self, ticker_or_cik: str | int):
        """
        Initialise the SEC client and retrieve company-level metadata.

        Parameters
        ----------
        ticker_or_cik : str or int
            Stock ticker (e.g., ``"AAPL"``) or raw CIK (e.g., ``"0000320193"``).
        """
        self.headers = sec_headers
        self.id_data = self.get_id_code(ticker_or_cik)
        self.submissions_data = self.process_company_submissions()

    # ------------------------------------------------------------------ #
    # CIK / ticker resolution
    # ------------------------------------------------------------------ #

    @weak_lru(maxsize=4)
    def get_id_code(self, ticker_or_cik: str | int) -> CompanyIdCode:
        """
        Resolve a ticker or CIK to a :class:`CompanyIdCode`.

        Raises
        ------
        CompanyIdCodeNotFoundError
            If the ticker or CIK is not found in the SEC index.
        """
        value = str(ticker_or_cik).strip()

        # --- Numeric → treat as CIK
        if value.isdigit():
            cik_padded = value.zfill(10)
            url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"

            response = requests.get(url, headers=self.headers, timeout=_REQUEST_TIMEOUT_SECS)
            if response.status_code == 200:
                data = response.json()
                return CompanyIdCode(
                    cik=cik_padded,
                    name=data.get("name"),
                    ticker=(data.get("tickers") or ["None"])[0],
                    exchange=(data.get("exchanges") or ["None"])[0],
                )

            raise CompanyIdCodeNotFoundError(value)

        # --- Otherwise → look up by ticker in SEC's combined index
        url = "https://www.sec.gov/files/company_tickers_exchange.json"

        with requests.get(url, headers=self.headers, stream=True, timeout=_REQUEST_TIMEOUT_SECS) as response:
            gz = gzip.GzipFile(fileobj=response.raw)
            text_stream = io.TextIOWrapper(gz, encoding="utf-8", errors="replace")

            # Each item: [cik, title, ticker, exchange]
            for item in ijson.items(text_stream, "data.item"):
                cik, name, ticker, exchange = item
                if ticker.lower() == value.lower() or str(cik) == value:
                    return CompanyIdCode(
                        cik=str(cik).zfill(10),
                        name=name,
                        ticker=ticker,
                        exchange=exchange,
                    )

        raise CompanyIdCodeNotFoundError(value)

    # ------------------------------------------------------------------ #
    # Form-4 (insider) and Form-13F (institutional holdings) metadata
    # ------------------------------------------------------------------ #

    @weak_lru(maxsize=4)
    def get_form4(self) -> pl.DataFrame:
        """Return the metadata DataFrame of Form 4 (insider transaction) filings."""
        df = self.submissions_data.filter(pl.col("form").is_in(["4"]))

        df = df.with_columns(
            (
                pl.lit("https://www.sec.gov/Archives/edgar/data/")
                + pl.lit(str(int(self.id_data.cik)))
                + "/"
                + pl.col("accessionNumber").str.replace_all("-", "")
                + "/"
                + pl.col("primaryDocument").str.split("/").list.last()
            ).alias("URL")
        )

        return df

    @weak_lru(maxsize=4)
    def get_form13(self) -> pl.DataFrame:
        """Return the metadata DataFrame of Form 13F (institutional holdings) filings."""
        df = self.submissions_data.filter(
            pl.col("form").is_in(["13-F", "13F-HR", "13F", "13F-HR/A"])
        )

        df = df.with_columns(
            (
                pl.lit("https://www.sec.gov/Archives/edgar/data/")
                + pl.lit(str(int(self.id_data.cik)))
                + "/"
                + pl.col("accessionNumber").str.replace_all("-", "")
            ).alias("URL")
        )

        return df

    @limits(calls=10, period=1)
    def process_company_submissions(self) -> pl.DataFrame:
        """
        Download and parse the SEC ``submissions`` JSON file for the company.

        Returns
        -------
        polars.DataFrame
            The recent-filings table from the SEC submissions endpoint.
        """
        url = f"https://data.sec.gov/submissions/CIK{self.id_data.cik}.json"
        response = requests.get(url, headers=self.headers, timeout=_REQUEST_TIMEOUT_SECS)
        response.raise_for_status()

        json_request = response.json()
        return pl.DataFrame(json_request["filings"]["recent"])

    # ------------------------------------------------------------------ #
    # Form-4 detail fetch + period aggregation
    # ------------------------------------------------------------------ #

    def _process_form4_by_accession(
        self, df_filings: pl.DataFrame, accession_number: str
    ) -> pl.DataFrame:
        """Retrieve and normalise a single Form 4 filing by accession number."""
        row = df_filings.filter(pl.col("accessionNumber") == accession_number)
        if row.is_empty():
            raise ValueError(f"Accession {accession_number} not found.")

        url = row["URL"][0]
        filing_date = row["filingDate"][0]
        report_date = row["reportDate"][0]

        df_form4 = retrieve_form_4(url, self.headers)
        df_form4 = df_form4.with_columns(
            [
                pl.lit(filing_date, dtype=pl.Utf8).alias("filingDate"),
                pl.lit(report_date, dtype=pl.Utf8).alias("reportDate"),
                pl.lit(accession_number, dtype=pl.Utf8).alias("accessionNumber"),
            ]
        )
        return df_form4

    def get_insider_transactions_period(self, period: str) -> pl.DataFrame:
        """
        Retrieve insider transactions filed within ``period`` (e.g. ``'1y'``, ``'6m'``).
        """
        df = self.get_form4()

        if df is None or df.is_empty():
            print("No Form 4 filings found.")
            return pl.DataFrame()

        start_date = _parse_period_to_start_date(period)

        df = df.with_columns(pl.col("filingDate").str.strptime(pl.Date, strict=False))
        df_filtered = df.filter(pl.col("filingDate") >= start_date.date())

        if df_filtered.is_empty():
            return pl.DataFrame()

        dfs: list[pl.DataFrame] = []
        for accession_number in df_filtered["accessionNumber"]:
            try:
                dfs.append(self._process_form4_by_accession(df_filtered, accession_number))
            except Exception as e:
                print(f"[FinqualForms] Skipping Form 4 accession {accession_number}: {type(e).__name__}: {e}")
                continue

        if not dfs:
            return pl.DataFrame()

        return pl.concat(dfs, how="vertical_relaxed")

    # ------------------------------------------------------------------ #
    # Form-13F detail fetch + period aggregation
    # ------------------------------------------------------------------ #

    def _process_form13_by_accession(
        self, df_filings: pl.DataFrame, accession_number: str
    ) -> pl.DataFrame:
        """Retrieve and normalise a single Form 13F filing by accession number."""
        row = df_filings.filter(pl.col("accessionNumber") == accession_number)
        if row.is_empty():
            raise ValueError(f"Accession {accession_number} not found.")

        url = row["URL"][0] + "/index.json"
        filing_date = row["filingDate"][0]
        report_date = row["reportDate"][0]

        resp = requests.get(url, headers=self.headers, timeout=_REQUEST_TIMEOUT_SECS)
        resp.raise_for_status()

        files = resp.json()["directory"]["item"]

        # Pick the holdings XML (anything except primary_doc.xml)
        xml_files = [
            f["name"]
            for f in files
            if f["name"].lower().endswith(".xml") and f["name"].lower() != "primary_doc.xml"
        ]

        if not xml_files:
            raise ValueError(f"No holdings XML found for accession {accession_number}")

        info_xml_url = row["URL"][0] + f"/{xml_files[0]}"
        df_form13 = retrieve_form_13f_aggregated(info_xml_url, self.headers)
        df_form13 = df_form13.with_columns(
            [
                pl.lit(filing_date, dtype=pl.Utf8).alias("filingDate"),
                pl.lit(report_date, dtype=pl.Utf8).alias("reportDate"),
                pl.lit(accession_number, dtype=pl.Utf8).alias("accessionNumber"),
            ]
        )
        return df_form13

    def get_form_13_period(self, n: int) -> pl.DataFrame:
        """
        Retrieve the aggregated holdings of the latest ``n`` Form 13F filings.

        Parameters
        ----------
        n : int
            Number of most-recent filings to include.
        """
        df = self.get_form13()

        if df is None or df.is_empty():
            print("No Form 13 filings found.")
            return pl.DataFrame()

        df = df.with_columns(pl.col("filingDate").str.strptime(pl.Date, strict=False))
        df_latest = df.sort("filingDate", descending=True).head(n)

        if df_latest.is_empty():
            return pl.DataFrame()

        dfs: list[pl.DataFrame] = []
        for accession_number in df_latest["accessionNumber"]:
            try:
                dfs.append(self._process_form13_by_accession(df_latest, accession_number))
            except Exception as e:
                print(f"[FinqualForms] Skipping Form 13 accession {accession_number}: {type(e).__name__}: {e}")
                continue

        if not dfs:
            return pl.DataFrame()

        df_agg = pl.concat(dfs, how="vertical_relaxed")
        df_agg = df_agg.with_columns(pl.lit(self.id_data.cik).alias("CIK"))
        df_agg = df_agg.select(["CIK"] + [c for c in df_agg.columns if c != "CIK"])

        return df_agg
