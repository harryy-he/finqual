import finqual as fq

tickers = ["NVDA"]  # You can add more tickers if needed
start = 2020
end = 2023
quarter = 3  # For quarterly data

for ticker in tickers:

    # Financial Statements
    df_inc = fq.Finqual(ticker).income_stmt(year=end) # Get annual income statements for end
    df_bs = fq.Finqual(ticker).balance_sheet(year=end, quarter=quarter) # Get quarterly balance sheet for end and quarter
    df_cf = fq.Finqual(ticker).cash_flow(year=start) # Get annual cash flow statements for start

    # Period Data
    df_incp = fq.Finqual(ticker).income_stmt_period(start_year=start, end_year=end) # Add '_period' to the end of the function and define the start and end to retrieve the income statement over the period
    df_cfp = fq.Finqual(ticker).cash_flow_period(start_year=start, end_year=end, quarter=True) # Add 'quarter=True' to retrieve the quarterly information over that time period

    # Ratios
    df_p = fq.Finqual(ticker).profitability_ratios(year=start) # Get selected profitability ratios for START_YEAR (e.g. Operating Margin, Gross Margin, ROE, ROA, ROIC etc)
    df_l = fq.Finqual(ticker).liquidity_ratios(year=start) # Get selected liquidity ratios for START_YEAR (e.g. D/E, Current, Quick Ratio)
    df_v = fq.Finqual(ticker).valuation_ratios(year=start) # Get selected valuation ratios for START_YEAR (e.g. P/E, EV/EBITDA, EPS etc)

    # -----------------------------------------------------------------------

    # Comparable Company Data
    df_cca = fq.CCA(ticker).get_c() # Get comparable companies that are in the same sector and most similar in market capitalisation to ticker
    df_cc_l = fq.CCA(ticker).liquidity_ratios(year=start) # Similar to before, but retrieve the liquidity ratios for ticker and its competitors for start
    df_cc_v = fq.CCA(ticker).valuation_ratios_period(start_year=start, end_year=end) # Similar to before, but retrieve the valuation ratios for ticker and its competitors for start to end


    # Output
    print(f"=== {ticker} ===")
    print(f"Income Statement:\n{df_inc}\n")
    print(f"Balance Sheet:\n{df_bs}\n")
    print(f"Cash Flow:\n{df_cf}\n")
    print(f"Income Statement {start}-{end}:\n{df_incp}\n")
    print(f"Cash Flow {start}-{end} (Quarterly):\n{df_cfp}\n")
    print(f"Profitability Ratios:\n{df_p}\n")
    print(f"Liquidity Ratios:\n{df_l}\n")
    print(f"Valuation Ratios:\n{df_v}\n")

    print(f"Comparable Companies:\n{df_cca}\n")
    print(f"Competitors Liquidity Ratios:\n{df_cc_l}\n")
    print(f"Competitors Valuation Ratios {start}-{end}:\n{df_cc_v}\n")
