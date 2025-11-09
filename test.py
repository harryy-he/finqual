import finqual as fq

tickers = [1018724, "NVDA", "ASML"]  # You can add more tickers if needed
start = 2020
end = 2025
quarter = 3  # For quarterly data

for ticker in tickers:

    fq_ticker = fq.Finqual(ticker)
    fq_cca = fq.CCA(ticker)

    # Financial Statements
    df_inc = fq_ticker.income_stmt(year=start, quarter=quarter).to_pandas()  # Get annual income statements for end
    df_bs = fq_ticker.balance_sheet(year=start).to_pandas()  # Get quarterly balance sheet for end and quarter
    df_cf = fq_ticker.cash_flow(year=start, quarter=quarter).to_pandas()  # Get annual cash flow statements for start

    # TTM
    df_inc_ttm = fq_ticker.income_stmt_ttm().to_pandas()
    df_bs_ttm = fq_ticker.income_stmt_ttm().to_pandas()
    df_cf_ttm = fq_ticker.cash_flow_ttm().to_pandas()  # Get annual income statements for end

    # Period Data
    df_inc_p = fq_ticker.income_stmt_period(start_year=start, end_year=end).to_pandas()  # Add '_period' to the end of the function and define the start and end to retrieve the income statement over the period
    df_bs_p = fq_ticker.balance_sheet_period(start_year=start, end_year=end, quarter=False).to_pandas()
    df_cf_p = fq_ticker.cash_flow_period(start_year=start, end_year=end).to_pandas()  # Add 'quarter=True' to retrieve the quarterly information over that time period

    df_inc_pq = fq_ticker.income_stmt_period(start_year=start, end_year=end, quarter=True).to_pandas()  # Add '_period' to the end of the function and define the start and end to retrieve the income statement over the period
    df_bs_pq = fq_ticker.balance_sheet_period(start_year=start, end_year=end, quarter=True).to_pandas()
    df_cf_pq = fq_ticker.cash_flow_period(start_year=start, end_year=end, quarter=True).to_pandas()

    # Ratios
    df_p = fq_ticker.profitability_ratios(year=start).to_pandas()  # Get selected profitability ratios for START_YEAR (e.g. Operating Margin, Gross Margin, ROE, ROA, ROIC etc)
    df_l = fq_ticker.liquidity_ratios(year=start).to_pandas()  # Get selected liquidity ratios for START_YEAR (e.g. D/E, Current, Quick Ratio)
    df_v = fq_ticker.valuation_ratios().to_pandas()   # Get selected valuation ratios for START_YEAR (e.g. P/E, EV/EBITDA, EPS etc)

    df_p_ttm = fq_ticker.profitability_ratios().to_pandas()  # Get selected profitability ratios for START_YEAR (e.g. Operating Margin, Gross Margin, ROE, ROA, ROIC etc)
    df_l_ttm = fq_ticker.liquidity_ratios().to_pandas()  # Get selected liquidity ratios for START_YEAR (e.g. D/E, Current, Quick Ratio)

    df_pp = fq_ticker.profitability_ratios_period(start_year=start, end_year=end).to_pandas()

    # -----------------------------------------------------------------------

    # Comparable Company Data

    df_cca = fq_cca.get_c()  # Get comparable companies that are in the same sector and most similar in market capitalisation to ticker
    df_cc_l = fq_cca.liquidity_ratios().to_pandas()  # Similar to before, but retrieve the liquidity ratios for ticker and its competitors for start
    df_cc_pp = fq_cca.profitability_ratios_period(start_year=start, end_year=end).to_pandas()
    df_cc_v = fq_cca.valuation_ratios().to_pandas()  # Retrieve the latest valuation ratios for ticker and its competitors
