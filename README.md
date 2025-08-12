[![Star History Chart](https://api.star-history.com/svg?repos=harryy-he/finqual&type=Date)](https://www.star-history.com/#harryy-he/finqual&Date)

# finqual

This is a work in progress package that enables users to conduct fundamental financial research, utilising the SEC's data and REST API.

## Installation
```
pip install finqual
```

## Features

finqual has the following features:
 
- Ability to call the income statement, balance sheet or cash flow statement for any company on SEC's EDGAR system
- Breakdown of chosen financial ratios for a chosen ticker
- Conduct comparable company analysis by comparing valuation, liquidity and profitability metrics

This has four key features that enable better programmatic access compared to other providers:
- Ability to call up to 10 requests per second, with built-in rate limiter
- No restriction on the number of calls within a certain timeframe
- Standardised labels for easy analysis between companies
- Probability and tree-based value gathering system to maximise the accuracy and calculation of financial statement values

## Quick-start guide

This provides section provides a quick overview on the functions available within the finqual package.

The core functionalities to retrieve financial statement information:
```
import finqual as fq

fq.Finqual("NVDA").income_stmt(2023) # Get annual income statements for FY2023
fq.Finqual("NVDA").balance_sheet(2023, 3) # Get quarterly balance sheet for FY2023 Q3
fq.Finqual("NVDA").cash_flow(2020) # Get annual cash flow statements for FY2020

# ---

fq.Finqual("NVDA").income_stmt_period(2020, 2022) # Add '_period' to the end of the function and define the start and end to retrieve the income statement over the period
fq.Finqual("NVDA").cash_flow_period(2020, 2022, quarter = True) # Add 'quarter = True' to retrieve the quarterly information over that time period
```

![nvda_2024_income_period.png](images%2Fnvda_2024_income_period.png)

We can also retrieve selected financial ratios (sorted by type) for the chosen company:

```
fq.Finqual("NVDA").profitability_ratios(2020) # Get selected profitability ratios for FY2020 (e.g. Operating Margin, Gross Margin, ROE, ROA, ROIC etc)
fq.Finqual("NVDA").liquidity_ratios(2020) # Get selected liquidity ratios for FY2020 (e.g. D/E, Current, Quick Ratio) 
fq.Finqual("NVDA").valuation_ratios(2020) # Get selected valuation ratios for FY2020 (e.g. P/E, EV/EBITDA, EPS etc)

# ---

fq.Finqual("NVDA").profitability_ratios_period(2020, 2024) # Similar to before, add "_period" to the end of the function and define a period to retrieve the ratio over that period
fq.Finqual("NVDA").profitability_ratios_period(2020, 2024, quarter = True) # Add 'quarter = True' to retrieve the quarterly information over that time period
```

![nvda_valuation_2024.png](images%2Fnvda_valuation_2024.png)

We can also conduct comparable company analysis by using the CCA method, as shown below:

```
import finqual as fq
fq.CCA("NVDA").get_c() # Get comparable companies that are in the same sector and most similar in market capitalisation to NVIDIA
fq.CCA("NVDA").liquidity_ratios(2020) # Similar to before, but retrieve the liquidity ratios for NVIDIA and its competitors for FY2020
fq.CCA("NVDA").valuation_ratios_period(2020, 2022) # Similar to before, but retrieve the valuation ratios for NVIDIA and its competitors for FY2020 to FY2022
```

![nvda_cca_2024.png](images%2Fnvda_cca_2024.png)

## Dependencies

Only four external packages are required, with the following versions confirmed to be working:

| Package      | Version   |
|--------------|-----------|
| pandas       | >= 2.2.3  |
| polars       | >= 1.21.0 |
| cloudscraper | >= 1.2.71 |
| requests     | >= 2.32.3 |
| ratelimit    | >= 2.2.1  |

The rest are in-built Python packages such as json, functools and concurrent.futures.

## Limitations
Currently, there are several known limitations that I am aware of from my own testing. These are still to be looked at:

- Some missing data values for companies, this is mostly due to companies using custom tags that are not accessible via the SEC database (e.g. Broadcom uses their own tag for depreciation and amortisation)
- Banks, insurers and other financial institutions have a different financial statement profile that has not been mapped yet

## Contact

If you would like to help me out, collaborate or for any other enquiries, please feel free to [email me](mailto:harryhe99@outlook.com).
