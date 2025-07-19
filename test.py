import finqual as fq

TICKERS = ["NVDA"]  # You can add more tickers if needed
START_YEAR = 2020
END_YEAR = 2023
QUARTER = 3  # For quarterly data

for ticker in TICKERS:
    fin = fq.Finqual(ticker)  # Initialize Finqual
    cca = fq.CCA(ticker)      # Initialize Comparable Company Analysis

    # Financial Statements
    df_inc = fin.income_stmt(year=END_YEAR) # Get annual income statements for END_YEAR
    df_bs = fin.balance_sheet(year=END_YEAR, quarter=QUARTER) # Get quarterly balance sheet for END_YEAR QUARTER
    df_cf = fin.cash_flow(year=START_YEAR) # Get annual cash flow statements for START_YEAR


    # Period Data
    df_incp = fin.income_stmt_period(start_year=START_YEAR, end_year=END_YEAR) # Add '_period' to the end of the function and define the start and end to retrieve the income statement over the period
    df_cfp = fin.cash_flow_period(start_year=START_YEAR, end_year=END_YEAR, quarter=True) # Add 'quarter=True' to retrieve the quarterly information over that time period

    # Ratios
    df_p = fin.profitability_ratios(year=START_YEAR) # Get selected profitability ratios for START_YEAR (e.g. Operating Margin, Gross Margin, ROE, ROA, ROIC etc)
    df_l = fin.liquidity_ratios(year=START_YEAR) # Get selected liquidity ratios for START_YEAR (e.g. D/E, Current, Quick Ratio)
    df_v = fin.valuation_ratios(year=START_YEAR) # Get selected valuation ratios for START_YEAR (e.g. P/E, EV/EBITDA, EPS etc)

    # Comparable Company Data
    df_cca = cca.get_c() # Get comparable companies that are in the same sector and most similar in market capitalisation to TICKER
    df_cc_l = cca.liquidity_ratios(year=START_YEAR) # Similar to before, but retrieve the liquidity ratios for TICKER and its competitors for START_YEAR
    df_cc_v = cca.valuation_ratios_period(start_year=START_YEAR, end_year=END_YEAR) # Similar to before, but retrieve the valuation ratios for TICKER and its competitors for START_YEAR to END_YEAR


    # Output
    print(f"=== {ticker} ===")
    print(f"Income Statement:\n{df_inc}\n")
    print(f"Balance Sheet:\n{df_bs}\n")
    print(f"Cash Flow:\n{df_cf}\n")
    print(f"Income Statement {START_YEAR}-{END_YEAR}:\n{df_incp}\n")
    print(f"Cash Flow {START_YEAR}-{END_YEAR} (Quarterly):\n{df_cfp}\n")
    print(f"Profitability Ratios:\n{df_p}\n")
    print(f"Liquidity Ratios:\n{df_l}\n")
    print(f"Valuation Ratios:\n{df_v}\n")
    print(f"Comparable Companies:\n{df_cca}\n")
    print(f"Competitors Liquidity Ratios:\n{df_cc_l}\n")
    print(f"Competitors Valuation Ratios {START_YEAR}-{END_YEAR}:\n{df_cc_v}\n")
