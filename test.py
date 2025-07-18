import finqual as fq

TICKER = (
    "NVDA"  # Change this to any ticker you want to analyze, e.g., "AAPL" for Apple Inc.
)

fin = fq.Finqual(TICKER)  # Initialize Finqual with NVIDIA ticker
cca = fq.CCA(TICKER)  # Initialize CCA for comparable companies

df_inc = fin.income_stmt(2023)  # Get annual income statements for FY2023
df_bs = fin.balance_sheet(2023, 3)  # Get quarterly balance sheet for FY2023 Q3
df_cf = fin.cash_flow(2020)  # Get annual cash flow statements for FY2020

df_incp = fin.income_stmt_period(
    2020, 2022
)  # Add '_period' to the end of the function and define the start and end to retrieve the income statement over the period
df_cfp = fin.cash_flow_period(
    2020, 2022, quarter=True
)  # Add 'quarter = True' to retrieve the quarterly information over that time period

df_p = fin.profitability_ratios(
    2020
)  # Get selected profitability ratios for FY2020 (e.g. Operating Margin, Gross Margin, ROE, ROA, ROIC etc)
df_l = fin.liquidity_ratios(
    2020
)  # Get selected liquidity ratios for FY2020 (e.g. D/E, Current, Quick Ratio)
df_v = fin.valuation_ratios(
    2020
)  # Get selected valuation ratios for FY2020 (e.g. P/E, EV/EBITDA, EPS etc)

df_cca = fq.CCA(
    "NVDA"
).get_c()  # Get comparable companies that are in the same sector and most similar in market capitalisation to NVIDIA
df_cc_l = fq.CCA("NVDA").liquidity_ratios(
    2020
)  # Similar to before, but retrieve the liquidity ratios for NVIDIA and its competitors for FY2020
df_cc_v = fq.CCA("NVDA").valuation_ratios_period(
    2020, 2022
)  # Similar to before, but retrieve the valuation ratios for NVIDIA and its competitors for FY2020 to FY2022


print("Income Statement FY2023:")
print(df_inc)
print("\nBalance Sheet FY2023 Q3:")
print(df_bs)
print("\nCash Flow FY2020:")
print(df_cf)
print("\nIncome Statement Period 2020-2022:")
print(df_incp)
print("\nCash Flow Period 2020-2022 (Quarterly):")
print(df_cfp)
print("\nProfitability Ratios FY2020:")
print(df_p)
print("\nLiquidity Ratios FY2020:")
print(df_l)
print("\nValuation Ratios FY2020:")
print(df_v)
print("\nComparable Companies for NVIDIA:")
print(df_cca)
print("\nLiquidity Ratios for NVIDIA and Competitors FY2020:")
print(df_cc_l)
print("\nValuation Ratios for NVIDIA and Competitors 2020-2022:")
print(df_cc_v)
