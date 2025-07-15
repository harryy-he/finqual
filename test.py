import finqual as fq

df_inc = fq.Finqual("NVDA").income_stmt(2023) # Get annual income statements for FY2023
df_bs = fq.Finqual("NVDA").balance_sheet(2023, 3) # Get quarterly balance sheet for FY2023 Q3
df_cf = fq.Finqual("NVDA").cash_flow(2020) # Get annual cash flow statements for FY2020

df_incp = fq.Finqual("NVDA").income_stmt_period(2020, 2022) # Add '_period' to the end of the function and define the start and end to retrieve the income statement over the period
df_cfp = fq.Finqual("NVDA").cash_flow_period(2020, 2022, quarter = True) # Add 'quarter = True' to retrieve the quarterly information over that time period

df_p = fq.Finqual("NVDA").profitability_ratios(2020) # Get selected profitability ratios for FY2020 (e.g. Operating Margin, Gross Margin, ROE, ROA, ROIC etc)
df_l = fq.Finqual("NVDA").liquidity_ratios(2020) # Get selected liquidity ratios for FY2020 (e.g. D/E, Current, Quick Ratio)
df_v = fq.Finqual("NVDA").valuation_ratios(2020) # Get selected valuation ratios for FY2020 (e.g. P/E, EV/EBITDA, EPS etc)

df_cca = fq.CCA("NVDA").get_c() # Get comparable companies that are in the same sector and most similar in market capitalisation to NVIDIA
df_cc_l = fq.CCA("NVDA").liquidity_ratios(2020) # Similar to before, but retrieve the liquidity ratios for NVIDIA and its competitors for FY2020
df_cc_v = fq.CCA("NVDA").valuation_ratios_period(2020, 2022) # Similar to before, but retrieve the valuation ratios for NVIDIA and its competitors for FY2020 to FY2022
