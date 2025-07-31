import matplotlib.pyplot as plt
from finqual.core import Finqual
import pandas as pd


def plot_profitability_ratios(
    ticker: str,
    start_year: int,
    end_year: int,
    quarterly: bool = False,
):
    print(f"[INFO] Fetching profitability ratios for {ticker}")
    try:
        fq = Finqual(ticker)
        df = fq.profitability_ratios_period(start_year, end_year, quarter=quarterly)
    except Exception as e:
        print(f"[ERROR] Failed to fetch data: {e}")
        return

    if df is None or df.empty or df.shape[1] <= 2:
        print("[WARN] Data is empty or malformed.")
        return

    # Drop non-numeric and identifier columns
    df_plot = df.drop(columns=["Ticker", "Period"], errors="ignore")
    df_plot = df_plot.apply(pd.to_numeric, errors="coerce").dropna(axis=1, how="all")

    if df_plot.empty:
        print("[SKIP] No numeric data to plot.")
        return

    # Determine and sort x-axis
    # "Period" exists for quarterly or multi-year queries; fall back to range if missing
    if "Period" in df.columns:
        df_plot.index = df["Period"]
    else:
        df_plot.index = range(start_year, end_year + 1)

    df_plot = df_plot.sort_index()

    # Plot
    df_plot.plot(
        title=f"{ticker} Profitability Ratios ({start_year}–{end_year})", marker="o"
    )
    plt.ylabel("Ratio (%)")
    plt.xlabel("Period")
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()
    plt.show()
    print(f"[INFO] Plotting profitability ratios for {ticker} completed.")


# Example usage
# plot_profitability_ratios(ticker="AAPL", start_year=2018, end_year=2022, quarterly=True)
