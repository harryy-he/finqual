import json
import glob
import os
from typing import Tuple
import pandas as pd
import pytest
import finqual as fq


def load_snapshot(path: str, endpoint: str, ticker: str) -> pd.DataFrame:
    """
    Load a snapshot JSON file and return a DataFrame for a specific ticker and endpoint.

    Args:
        path (str): Path to the JSON snapshot file.
        endpoint (str): Endpoint to extract ('income_statement', 'balance_sheet', 'cashflow').
        ticker (str): Stock ticker to extract data for.

    Returns:
        pd.DataFrame: DataFrame containing the snapshot data for the specified ticker and endpoint.
    """
    with open(path, "r") as f:
        data = json.load(f)
        if ticker not in data:
            raise ValueError(f"Ticker {ticker} not found in snapshot")
        if endpoint not in data[ticker]:
            raise ValueError(f"Endpoint {endpoint} not found for ticker {ticker}")
        return pd.DataFrame(data[ticker][endpoint])


def parse_filename(path: str) -> Tuple[str, int, int]:
    """
    Extracts ticker, start year, and end year from snapshot filename.

    Expected filename format: ticker_startyear_endyear.json
    Example: amazon_2020_2024.json

    Args:
        path (str): Path to the snapshot file.

    Returns:
        Tuple[str, int, int]: (ticker, start_year, end_year)
    """
    name = os.path.basename(path).replace(".json", "")
    parts = name.split("_")
    ticker = parts[0].upper()  # Convert to uppercase for API usage
    start_year = int(parts[1])
    end_year = int(parts[2])
    return ticker, start_year, end_year


def call_finqual_api(ticker: str, endpoint: str, start_year: int, end_year: int) -> pd.DataFrame:
    """
    Calls the Finqual API for a given ticker, endpoint, and period.

    Args:
        ticker (str): Stock ticker symbol.
        endpoint (str): Financial statement endpoint ('income_statement', 'balance_sheet', 'cashflow').
        start_year (int): Starting year for the period.
        end_year (int): Ending year for the period.

    Returns:
        pd.DataFrame: DataFrame returned by Finqual API for the requested period.
    """
    fq_ticker = fq.Finqual(ticker)

    if endpoint == "income_statement":
        return fq_ticker.income_stmt_period(start_year=start_year, end_year=end_year).to_pandas()
    elif endpoint == "balance_sheet":
        return fq_ticker.balance_sheet_period(start_year=start_year, end_year=end_year).to_pandas()
    elif endpoint == "cashflow":
        return fq_ticker.cash_flow_period(start_year=start_year, end_year=end_year).to_pandas()
    else:
        raise ValueError(f"Unsupported endpoint: {endpoint}")


# AUTO-DISCOVER SNAPSHOT FILES
SNAPSHOT_DIR = os.path.join(os.path.dirname(__file__), "snapshots")
print("Looking in:", SNAPSHOT_DIR)
snapshot_files = glob.glob(os.path.join(SNAPSHOT_DIR, "*.json"))
print("Found snapshot files:", snapshot_files)


@pytest.mark.parametrize("snapshot_path", snapshot_files)
def test_finqual_snapshot(snapshot_path: str) -> None:
    """
    Test Finqual API against stored snapshot data for multiple endpoints.

    Args:
        snapshot_path (str): Path to the snapshot JSON file.

    Raises:
        AssertionError: If the API data does not match the snapshot.
    """
    ticker, start_year, end_year = parse_filename(snapshot_path)

    # Assume the snapshot contains all endpoints; test each one
    endpoints = ["income_statement", "balance_sheet", "cashflow"]

    for endpoint in endpoints:
        df_expected = load_snapshot(snapshot_path, endpoint, ticker)

        df_actual = call_finqual_api(
            ticker=ticker,
            endpoint=endpoint,
            start_year=start_year,
            end_year=end_year
        )

        # Normalize df_actual to match snapshot format
        ticker_col = [col for col in df_actual.columns if col.lower() == ticker.lower()]
        if ticker_col:
            df_actual = df_actual.rename(columns={ticker_col[0]: "metric"})

        # Reorder columns to match snapshot
        df_actual = df_actual[df_expected.columns]

        # Ensure all expected columns are present
        missing_cols = set(df_expected.columns) - set(df_actual.columns)
        assert not missing_cols, f"{endpoint} missing columns in API result: {missing_cols}"

        # Reorder columns to match snapshot
        df_actual = df_actual[df_expected.columns]

        pd.testing.assert_frame_equal(
            df_actual,
            df_expected,
            check_dtype=False,
            check_exact=False,
        )


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
