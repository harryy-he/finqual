"""
Smoke / exploration script for the :class:`Finqual` and :class:`CCA` public surface.

This file is **not** a test (no assertions). It is intended as a runnable example
to manually verify end-to-end behaviour. Previously this script lived at the
project root as ``test.py`` and was being auto-collected by pytest, masking the
absence of real tests.

Run with:

    python examples/smoke_finqual.py
"""

import finqual as fq

tickers = ["JPM", 1018724, "NVDA", "ASML"]
start = 2020
end = 2024
quarter = 3

for ticker in tickers:
    fq_ticker = fq.Finqual(ticker)
    fq_cca = fq.CCA(ticker)

    # --- Financial statements
    fq_ticker.income_stmt(year=start, quarter=quarter).to_pandas()
    fq_ticker.balance_sheet(year=start).to_pandas()
    fq_ticker.cash_flow(year=start, quarter=quarter).to_pandas()

    # --- TTM
    fq_ticker.income_stmt_ttm().to_pandas()
    fq_ticker.balance_sheet_ttm().to_pandas()
    fq_ticker.cash_flow_ttm().to_pandas()

    # --- Period data
    fq_ticker.income_stmt_period(start_year=start, end_year=end).to_pandas()
    fq_ticker.balance_sheet_period(start_year=start, end_year=end, quarter=False).to_pandas()
    fq_ticker.cash_flow_period(start_year=start, end_year=end).to_pandas()

    fq_ticker.income_stmt_period(start_year=start, end_year=end, quarter=True).to_pandas()
    fq_ticker.balance_sheet_period(start_year=start, end_year=end, quarter=True).to_pandas()
    fq_ticker.cash_flow_period(start_year=start, end_year=end, quarter=True).to_pandas()

    # --- Ratios
    fq_ticker.profitability_ratios(year=start).to_pandas()
    fq_ticker.liquidity_ratios(year=start).to_pandas()
    fq_ticker.valuation_ratios().to_pandas()

    fq_ticker.profitability_ratios().to_pandas()
    fq_ticker.liquidity_ratios().to_pandas()

    fq_ticker.profitability_ratios_period(start_year=start, end_year=end).to_pandas()

    # --- Comparable company analysis
    fq_cca.get_c()
    fq_cca.liquidity_ratios().to_pandas()
    fq_cca.profitability_ratios_period(start_year=start, end_year=end).to_pandas()
    fq_cca.valuation_ratios().to_pandas()
