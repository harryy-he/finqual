import finqual as fq

tickers = ["NVDA"]  # You can add more tickers if needed
start = 2024
end = 2025
quarter = 4  # For quarterly data

for ticker in tickers:

    # Financial Statements
    df_inc = fq.Finqual(ticker).income_stmt(year=start, quarter=quarter).to_pandas()  # Get annual income statements for end
    df_bs = fq.Finqual(ticker).balance_sheet(year=start, quarter=quarter).to_pandas()  # Get quarterly balance sheet for end and quarter
    df_cf = fq.Finqual(ticker).cash_flow(year=start, quarter=quarter).to_pandas()  # Get annual cash flow statements for start

    # TTM
    df_inc_ttm = fq.Finqual(ticker).income_stmt_ttm().to_pandas()
    df_bs_ttm = fq.Finqual(ticker).income_stmt_ttm().to_pandas()
    df_cf_ttm = fq.Finqual(ticker).cash_flow_ttm().to_pandas()  # Get annual income statements for end

    # Period Data
    df_incp = fq.Finqual(ticker).income_stmt_period(start_year=start, end_year=end, quarter=True).to_pandas()  # Add '_period' to the end of the function and define the start and end to retrieve the income statement over the period
    df_cfp = fq.Finqual(ticker).cash_flow_period(start_year=start, end_year=end, quarter=True).to_pandas()  # Add 'quarter=True' to retrieve the quarterly information over that time period

    # Ratios
    df_p = fq.Finqual(ticker).profitability_ratios(year=start) # Get selected profitability ratios for START_YEAR (e.g. Operating Margin, Gross Margin, ROE, ROA, ROIC etc)
    df_l = fq.Finqual(ticker).liquidity_ratios(year=start) # Get selected liquidity ratios for START_YEAR (e.g. D/E, Current, Quick Ratio)
    df_v = fq.Finqual(ticker).valuation_ratios().to_pandas() # Get selected valuation ratios for START_YEAR (e.g. P/E, EV/EBITDA, EPS etc)

    # -----------------------------------------------------------------------

    # Comparable Company Data
    df_cca = fq.CCA(ticker).get_c()  # Get comparable companies that are in the same sector and most similar in market capitalisation to ticker
    df_cc_l = fq.CCA(ticker).liquidity_ratios(year=start).to_pandas()  # Similar to before, but retrieve the liquidity ratios for ticker and its competitors for start
    df_cc_v = fq.CCA(ticker).valuation_ratios().to_pandas()  # Retrieve the latest valuation ratios for ticker and its competitors
