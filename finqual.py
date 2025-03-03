# Import packages
import json
import pandas as pd
import numpy as np
import requests
import ratelimit
import datetime
import os

from balance_sheet import *
from cashflow_statement import *
from income_statement import *

# API connection class

class Ticker():

    def __init__(self, ticker):
        self.ticker = ticker
        self.cik = self.CIK()
        self.data = self.SEC()
        self.SIC = self.SIC()

    def CIK(self):

        url = "https://www.sec.gov/files/company_tickers_exchange.json"

        headers = {"User-Agent": "YourName (your@email.com)", "Accept-Encoding": "gzip, deflate"}

        response = requests.get(url, headers=headers)

        response = response.json()["data"]
        dict_data = {i[2]: str(i[0]).zfill(10) for i in response}

        cik_code = dict_data[self.ticker]

        return cik_code

    def is_date_between(self, date, q):

        start_date = q[0]
        end_date = q[1]

        date_month = date.month
        date_day = date.day

        start_month = start_date.month
        start_day = start_date.day

        end_month = end_date.month
        end_day = end_date.day

        if start_month < end_month:
            return (start_month, start_day) <= (date_month, date_day) <= (end_month, end_day)
        elif start_month > end_month:
            return (start_month, start_day) <= (date_month, date_day) or (date_month, date_day) <= (end_month, end_day)
        else:  # start_month == end_month
            if start_day <= end_day:
                return (start_month, start_day) <= (date_month, date_day) <= (end_month, end_day)
            else:  # Handle wraparound from end of year to start of year
                return (start_month, start_day) <= (date_month, date_day) or (date_month, date_day) <= (
                    end_month, end_day)

    def SIC(self):
        this_dir, this_filename = os.path.split(__file__)
        sic_path = os.path.join(this_dir, "data", "sec_sic.csv")

        sic = pd.read_csv(sic_path, index_col=0)
        sic = sic.dropna()

        sic_code = sic[sic["ticker"] == self.ticker]["SIC"].values[0]

        return sic_code

    def date_quarter(self, date, q1, q2, q3, q4):
        quarter_list = [(q1, 1), (q2, 2), (q3, 3), (q4, 4)]
        for quarter, quarter_num in quarter_list:
            if self.is_date_between(date, quarter):
                return quarter_num
        return None

    def fiscal_year(self):

        headers = {"Accept": "application/json, text/plain, */*",
                   "Accept-Language": "en-US,en;q=0.9",
                   "Origin": "https://www.nasdaq.com",
                   "Referer": "https://www.nasdaq.com",
                   "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"}

        source = requests.get(url="https://data.sec.gov/submissions/CIK" + self.cik + ".json", headers=headers, verify=True)
        data = source.json()
        end = data["fiscalYearEnd"]
        fiscal_end = datetime.datetime.strptime(end, "%m%d")

        q4 = [fiscal_end + datetime.timedelta(days=-14), fiscal_end + datetime.timedelta(days=14)]
        q1 = [q4[0] + datetime.timedelta(days=76), q4[1] + datetime.timedelta(days=104)]
        q2 = [q1[0] + datetime.timedelta(days=76), q1[1] + datetime.timedelta(days=104)]
        q3 = [q2[0] + datetime.timedelta(days=76), q2[1] + datetime.timedelta(days=104)]

        return q1, q2, q3, q4

    @ratelimit.sleep_and_retry
    @ratelimit.limits(calls = 10, period = 1)
    def SEC(self):
        """
        Function to get a Pandas dataframe from the SEC API of a chosen ticker
        """
        # Defining the headers for access
        headers = {"Accept": "application/json, text/plain, */*",
                   "Accept-Language": "en-US,en;q=0.9",
                   "Origin": "https://www.nasdaq.com",
                   "Referer": "https://www.nasdaq.com",
                   "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"}

        try:
            source = requests.get(url="https://www.sec.gov/files/company_tickers.json", headers=headers, verify=True)
            cik = source.json()

        except:
            this_dir, this_filename = os.path.split(__file__)
            source = os.path.join(this_dir, "data", "company_tickers.json")

            with open(source) as f:
                cik = json.load(f)

        cik = pd.DataFrame(cik)
        cik = cik.transpose()

        value = str(cik.loc[cik["ticker"] == self.ticker]["cik_str"].iloc[0])

        # Making sure the CIK is of right length
        value = value.zfill(10)

        url = 'https://data.sec.gov/api/xbrl/companyfacts/CIK' + value + '.json'

        # Getting the Pandas dataframe of chosen ticker
        source = requests.get(url=url, headers=headers, verify=True)
        data = source.json()
        data = pd.DataFrame(data)
        return data

    def lookup(self, node, year, category, quarter = None):
        """
        Looks up items that are under the "us-gaap" taxonomy and are in USD units, this has to be done year by year or quarter
        by quarter as companies may change what they file certain items under
        """
        item = node.name

        data = self.data

        try:
            data = data["facts"]["ifrs-full"]

        except:
            data = data["facts"]["us-gaap"]

        if (category == "EPS"):
            """
            Creating search term
            """
            try:
                df = pd.DataFrame(pd.DataFrame(data[item])["units"].iloc[0])
                df.dropna(inplace = True)

                df["frame"] = df["frame"].str.replace('CY', '')

                if (quarter != None):
                    # If looking at quarter then:

                    df = df[df["frame"].str.contains(str(year))]

                    unique_quarters = set(df["frame"])
                    all_quarters = [str(year) + "Q" + str(i) for i in range(1, 5)]
                    missing_quarter = list(set(all_quarters) - unique_quarters)

                    if (len(missing_quarter) == 1):
                        df["frame"] = df["frame"].replace(str(year), missing_quarter[0])

                    search = str(year) + "Q" + str(quarter)

                else:
                    search = str(year)

                return df["val"].to_numpy()[df["frame"].to_numpy() == search][0]

            except:
                return False

        if (category == "income"):
            """
            Creating search term
            """
            try:
                df = pd.DataFrame(pd.DataFrame(data[item])["units"].iloc[0])
                df.dropna(inplace = True)
                df["frame"] = df["frame"].str.replace('I', '')

                if (quarter != None):
                    # If looking at quarter then:
                    search = "CY" + str(year) + "Q" + str(quarter)
                else:
                    search = "CY" + str(year)

                return df["val"].to_numpy()[df["frame"].to_numpy() == search][0]

            except:
                return False


        if (category == "balance"):

            """
            Getting the desired item value
            """
            try:

                df = pd.DataFrame((pd.DataFrame(data[item])["units"]).iloc[0])
                df.dropna(inplace = True)
                df["frame"] = df["frame"].str.replace('I', '')
                fy = df[df["fp"] == "FY"].iloc[-1].iloc[7][-2:]

                if (quarter == None):
                    search = "CY" + str(year) + fy
                else:
                    search = "CY" + str(year) + "Q" + str(quarter)

                return df["val"].to_numpy()[df["frame"].to_numpy() == search][0]

            except:

                return False

        if (category == "cashflow"):
            try:
                df = pd.DataFrame((pd.DataFrame(data[item])["units"]).iloc[0])
            except:
                return False

            if (df.shape[1] == 8):
                try:
                    df.drop_duplicates(subset=["end", "val"], inplace=True, keep="last")
                    df['end'] = pd.to_datetime(df["end"], format='%Y-%m-%d')

                    df["year"] = df['end'].dt.year
                    df["quarter"] = df["end"].dt.quarter
                    df["quarter_frame"] = df["year"].astype(str) + "Q" + df["quarter"].astype(str)

                    if (quarter == None):
                        search = str(year) + "Q" + str(4)
                        try:
                            return df["val"].to_numpy()[df["quarter_frame"].to_numpy() == search][0]
                        except:
                            return False
                    else:
                        search = str(year) + "Q" + str(quarter)
                        try:
                            return df["val"].to_numpy()[df["quarter_frame"].to_numpy() == search][0]
                        except:
                            return False
                except:
                    pass

            else:
                df['end'] = pd.to_datetime(df["end"], format='%Y-%m-%d')
                df['start'] = pd.to_datetime(df["start"], format='%Y-%m-%d')
                df.drop_duplicates(subset=['start', "end"], inplace=True, keep="last")

                df["difference_days"] = (df["end"] - df["start"]).dt.days
                df["flag"] = df["difference_days"].between(76, 104)

                df["year"] = df['end'].dt.year
                df["quarter"] = df['end'].dt.quarter
                df["quarter_frame"] = df["year"].astype(str) + "Q" + df["quarter"].astype(str)

                df['frame'] = np.where(df['difference_days'].between(350, 380), df['year'].astype(str), np.nan)
                df.sort_values(['year', 'quarter', "end", "difference_days"], inplace=True)
                df.drop_duplicates(subset=['year', "quarter"], inplace=True, keep="last")

                """
                #Calculating the quarter_vals
                """
                df.loc[~df['flag'], 'quarter_val'] = df.groupby('start')['val'].diff(periods=1)
                df.loc[df['quarter_val'].isnull(), 'quarter_val'] = df['val']
                df["quarter_val"] = df["quarter_val"].astype(np.int64)
                df.reset_index(drop=True, inplace=True)

                if (quarter == None):
                    search = str(year)
                    try:
                        return df["val"].to_numpy()[df["frame"].to_numpy() == search][0]
                    except:
                        return False
                else:
                    search = str(year) + "Q" + str(quarter)
                    try:
                        return df["quarter_val"].to_numpy()[df["quarter_frame"].to_numpy() == search][0]
                    except:
                        return False

    def tree_item(self, node, year, values, attributes, category, quarter = None):
        """
        Returns the value of a chosen node at a certain point in time, using a tree-based node system and summing where needed
        """
        check = self.lookup(node, year, category, quarter)

        if (check != False):
            values.append(check)
            attributes.append(node.attribute)

        else:
            [self.tree_item(i, year, values, attributes, category, quarter) for i in node.getChildrenNodes()]

        # This is done after checking all the nodes
        df = pd.DataFrame(zip(values, attributes), columns=["USD", "Attribute"])

        # Sum credits and subtract credits
        parent_attribute = node.attribute

        if parent_attribute == "debit":
            value = df.loc[df["Attribute"] == "debit"]["USD"].sum() - df.loc[df["Attribute"] == "credit"]["USD"].sum()

        else:
            value = df.loc[df["Attribute"] == "credit"]["USD"].sum() - df.loc[df["Attribute"] == "debit"]["USD"].sum()

        return value

    def year_tree_item(self, node, start, end, category, quarter = None):
        """
        Returns a given tree_item over a timeframe
        """
        year_list = [i for i in np.arange(end, start - 1, -1)]
        values = []

        if quarter != None:
            values = [self.tree_item(node, i, [], [], category, j) for i in year_list for j in np.arange(4, 0, -1)]

        else:
            values = [self.tree_item(node, i, [], [], category) for i in year_list]

        return values

    def income(self, start, end, category = "income", quarter = None, readable = None):

        df = self.income_helper(start, end, category, quarter, readable)
        df = df.drop(["Cost and Expenses", "Interest Expense", "Depreciation and Amortization"])

        no_columns = -1*len(df.columns)

        nodes = [s_b,s_d]

        data = [self.year_tree_item(i, start, end, category = "EPS", quarter = True) for i in nodes]

        for i in range(len(data)):
            if no_columns == -1:
                data[i] = data[i][-1]

            else:
                data[i] = data[i][no_columns:]

        df.loc["Number of Basic Shares"] = data[0]
        df.loc["Number of Diluted Shares"] = data[1]
        df.loc["Basic EPS"] = df.loc["Net Profit"]/df.loc["Number of Basic Shares"]
        df.loc["Diluted EPS"] = df.loc["Net Profit"]/df.loc["Number of Diluted Shares"]
        df = df.round(1).map('{:.1f}'.format).replace('\.0$', '', regex=True) # Changed
        df.replace("inf", np.nan, inplace=True)
        return df

    def income_helper(self, start, end, category, quarter = None, readable = None):
        """
        Creating list of years and quarters for columns
        """
        year_list = [i for i in np.arange(end, start - 2, -1)]
        quarter_list = [str(i) + "Q" + str(j) for i in year_list for j in np.arange(4, 0, -1)]

        """
        Creating list of income statement items and their names
        """
        nodes = [rev, cor, gp, opex, ce,
                 oi1,
                 noi, pti1, tax1, ni,
                 cce5_2,
                 ide1_1]
        node_names = ["Revenues", "Cost of Revenue", "Gross Profit", "Operating Expenses", "Cost and Expenses",
                      "Operating Profit"
            ,"Non-Operating Income/Expense", "Pretax Profit", "Tax", "Net Profit", "Depreciation and Amortization"
            ,"Interest Expense"]
        """
        Appending each node values for each year to a data
        """
        if quarter == True:
            data = [self.year_tree_item(i, start - 1, end, category, quarter) for i in nodes]
            df = pd.DataFrame(data, index = [node_names], columns = [quarter_list])

            """
            Get the missing quarter stuff, some zeros will be replaced at sense-checking stage, the zeros will signify the quarter that the company reports in
            """
            for i in np.arange(start, end + 1):
                df1 = df.filter(regex=str(i))  # Filtering for only a year i's items
                try:
                    position = [True if self.MissingQuarter(df1, i) > 3 else False for i in df1.columns].index(True)
                    label = df1.columns[position]  # Getting the column name of the label
                    idx = df.columns.get_loc(label)
                    idx_list = [x for x in np.arange(idx, idx + 4)]   # Getting the last four quarters from label backwards by index
                    df1 = df.iloc[:, idx_list]  # Getting the dataframe for the chosen four quarters

                    totals = df1.sum(axis = 1).values  # Summing across income statement items for a given year's quarters
                    """
                    Getting the annual figures for comparison into an "actual" list
                    """
                    if readable:
                        annual = [int(x.replace(',', '')) for x in self.income_helper(i, i, category = "income", quarter = False, readable = True)[i]]
                    else:
                        annual = list(self.income_helper(i, i, category = "income", quarter = False, readable = False)[i])

                    changed = list(df.loc[:, label])  # The list of values that are to be changed, i.e. the incorrect column

                    diff = [a - b + c for a, b, c in zip(annual, totals, changed)]  # Reconcile discrepancies and the actual figures
                    df.loc[:, label] = diff

                except:

                    continue

        else:

            data = [self.year_tree_item(i, start - 1, end, category = "income") for i in nodes]
            df = pd.DataFrame(data, index=[node_names], columns=[year_list])

        df.columns = df.columns.get_level_values(0)
        df.index = df.index.get_level_values(0)

        """
        Sense-checking
        """

        df.loc["Cost of Revenue"] = df.loc["Revenues"] - df.loc["Gross Profit"]

        mask = (df.loc["Cost of Revenue"] == 0) & (df.loc["Cost and Expenses"] != 0) & (df.loc["Operating Expenses"] != 0)
        df.loc["Cost of Revenue", mask] = df.loc["Cost and Expenses", mask] - df.loc["Operating Expenses", mask]

        df.loc["Gross Profit"] = df.loc["Revenues"] - df.loc["Cost of Revenue"]

        mask = (df.loc["Operating Profit"] == 0) & (df.loc["Operating Expenses"] != 0) & (df.loc["Gross Profit"] != 0)
        df.loc["Operating Profit", mask] = df.loc["Gross Profit", mask] - df.loc["Operating Expenses", mask]

        df.loc["Operating Expenses"] = df.loc["Gross Profit"] - df.loc["Operating Profit"]
        df.loc["Non-Operating Income/Expense"] = df.loc["Pretax Profit"] - df.loc["Operating Profit"]
        df.loc["EBIT"] = df.loc["Net Profit"] + df.loc["Tax"] + df.loc["Interest Expense"]
        df.loc["EBITDA"] = df.loc["EBIT"] + df.loc["Depreciation and Amortization"]

        if readable:
            df = df.applymap(lambda x: '{:,}'.format(x))
            df = df.loc[:, (df != 0).any(axis=0)]
            df.drop(df.filter(regex=str(start - 1)).columns, axis=1, inplace=True)
            return df

        else:
            df = df.loc[:, (df != 0).any(axis=0)] #Remove columns that have all zeros
            df.drop(df.filter(regex=str(start - 1)).columns, axis=1, inplace=True)
            return df

    def MissingQuarter(self, df, column):
        """
        Returns the number of times 0 appears in a column
        """
        try:
            return (df[column].value_counts()[0])
        except:
            return 0

    def cashflow(self, start, end, quarter=None, readable=None, category="cashflow"):
        """
        Creating list of years and quarters for columns
        """
        year_list = [i for i in np.arange(end, start - 1, -1)]
        quarter_list = [str(i) + "Q" + str(j) for i in year_list for j in np.arange(4, 0, -1)]
        """
        Creating list of income statement items and their names
        """
        nodes = [cce2_3, cce2_4, cce2_5, cce1_1, cce1, cce4_8]

        node_names = ["Operating Cash Flow", "Investing Cash Flow", "Financing Cash Flow",
                      "Effect of Exchange Rate on Cash", "End Cash Position", "Capital Expenditures"]
        """
        Appending each node values for each year to a data
        """
        if quarter:
            data = [self.year_tree_item(i, start, end, quarter = True, category = "cashflow") for i in nodes]
            df = pd.DataFrame(data, index = [node_names], columns = [quarter_list])

        else:
            data = [self.year_tree_item(i, start, end, category = "cashflow") for i in nodes]
            df = pd.DataFrame(data, index = [node_names], columns = [year_list])

        df.columns = df.columns.get_level_values(0)
        df.index = df.index.get_level_values(0)

        df.loc["Free Cash Flow"] = df.loc["Operating Cash Flow"] - df.loc["Capital Expenditures"]
        df.drop(["Capital Expenditures"], inplace=True)
        df = df.loc[:, (df != 0).any(axis=0)]

        if readable:
            df = df.applymap(lambda x: '{:,}'.format(x))
            return df
        else:
            return df

    def balance(self, start, end, quarter = None, readable = None):
        """
        Creating list of years and quarters for columns
        """
        year_list = [i for i in np.arange(end, start - 1, -1)]
        quarter_list = [str(i) + "Q" + str(j) for i in year_list for j in np.arange(4, 0, -1)]

        """
        Getting SIC code
        """

        sic_code = self.SIC

        bank_codes = [6022, 6021, 6211, 6029, 6035, 6199]

        if sic_code in bank_codes:
            nodes = [ca1_1, ba1_1, ba1_4,
                     ba1_6, ba1_7, ba1_9, ba1_15, ba1_3, ba1_18,
                     ba1_10, nca1_19, ba1_16, ba1_11, a,
                     bl1_1, bl1_3, bl1_9,
                     cl1_3, bl1_6,
                     bl1_8, bl1_10, l,
                     se2_3, se2_8, se2_12, se2_11,
                     se1_1, se1_2, se]

            node_names = ["Cash and Cash Equivalents", "Securities Purchased Under Agreements to Resell", "Net Loans",
                          "Trading Securities", "Available-For-Sale Securities","Held-To-Maturity Securities", "Derivative Securities", "Securities Borrowed", "Financial Instruments Owned",
                          "Property, Plant and Equipment", "Intangibles", "Accounts Receivables", "Other Assets", "Total Assets",
                          "Securities Sold Under Agreements to Repurchase","Deposits", "Short Sales Obligations",
                          "Short-Term Debt", "Long-Term Debt",
                          "Accrued Expenses and Accounts Payable", "Other Liabilities", "Total Liabilities",
                          "Common Stock", "Additional Paid In Capital", "Retained Earnings", "Accumulated Other Income",
                          "Stockholder's Equity", "Minority Interest", "Total Equity"]


        else:
            nodes = [ca1_1, ca1_4, ca2_12,
                     ca1_34, ca1,
                     nca1_13, nca1_19, nca1_36,
                     nca,
                     cl2_1, cl2_2, cl1_2, cl1_3,
                     cl1_27, cl1,
                     ncl1_1, ncl1_2, ncl,
                     se2_3, se2_8, se2_12, se2_14,
                     se1_1, se1_2,
                     a, l, se]

            node_names = ["Cash and Cash Equivalents", "Accounts Receivable, Net", "Inventories",
                          "Other Current Assets", "Total Current Assets",
                          "Property Plant and Equipment", "Intangibles", "Other Non-Current Assets",
                          "Total Non-Current Assets",
                          "Accounts Payable", "Accrued Liabilities", "Deferred Revenue", "Short-term Borrowings",
                          "Other Current Liabilities", "Total Current Liabilities",
                          "Long-Term Debt", "Non-Debt Long Term Liabilities", "Total Non-Current Liabilities",
                          "Capital Stock", "Additional Paid In Capital", "Retained Earnings", "Accumulated Other Change",
                          "Stockholder's Equity", "Minority Interest",
                          "Total Assets", "Total Liabilities", "Total Equity"]

        """
        Appending each node values for each year to a data
        """
        if quarter == True:
            data = [self.year_tree_item(i, start, end, category = "balance", quarter=True) for i in nodes]  # Fetching the data
            df = pd.DataFrame(data, index=[node_names], columns=[quarter_list])  # Creating the dataframe with columns and index according to the list

        else:
            data = [self.year_tree_item(i, start, end, category = "balance") for i in nodes]
            df = pd.DataFrame(data, index=[node_names], columns=[year_list])

        df.columns = df.columns.get_level_values(0)
        df.index = df.index.get_level_values(0)

        """
        Sense-checking
        """
        if sic_code not in bank_codes:
            df.loc["Total Non-Current Assets"] = df.loc["Total Assets"] - df.loc["Total Current Assets"]
            df.loc["Other Current Assets"] = df.loc["Total Current Assets"] - df.iloc[0:3].sum()
            df.loc["Other Non-Current Assets"] = df.loc["Total Non-Current Assets"] - df.iloc[5:7].sum()

            df.loc["Other Current Liabilities"] = df.loc["Total Current Liabilities"] - df.iloc[9:13].sum()
            df.loc["Total Non-Current Liabilities"] = df.loc["Total Liabilities"] - df.loc["Total Current Liabilities"]
            df.loc["Non-Debt Long Term Liabilities"] = df.loc["Total Non-Current Liabilities"] - df.loc["Long-Term Debt"]

            df.loc["Accumulated Other Change"] = df.loc["Stockholder's Equity"] - df.iloc[18:21].sum()
            df.loc["Minority Interest"] = df.loc["Total Equity"] - df.loc["Stockholder's Equity"]

        else:

            df.loc["Other Assets"] = df.loc["Total Assets"] - df.iloc[0:12].sum()
            df.loc["Other Liabilities"] = df.loc["Total Liabilities"] - df.iloc[14:20].sum()

        if readable == True:

            df = df.applymap(lambda x: '{:,}'.format(x))
            df = df.loc[:, (df != 0).any(axis=0)]
            return df

        else:

            df = df.loc[:, (df != 0).any(axis=0)]
            return df

    def comparables(self, n, level = None):
        this_dir, this_filename = os.path.split(__file__)
        sic_path = os.path.join(this_dir, "data", "sec_sic.csv")

        if level == None:
            level = 4

        sic = pd.read_csv(sic_path, index_col=0)
        sic = sic.dropna()

        sic["SIC"] = sic["SIC"].astype(int)
        sic["SIC"] = sic["SIC"].astype(str)
        sic['SIC'] = sic['SIC'].apply(lambda x: x[:level])
        sic["SIC"] = sic["SIC"].astype(int)

        sic_code = sic[sic["ticker"] == self.ticker]["SIC"].values[0]
        company_list = sic[sic["SIC"] == sic_code].copy()
        company_list.drop(["cik_str"], axis=1, inplace=True)
        company_list.reset_index(drop=True, inplace=True)

        sic_index = company_list[company_list['ticker'] == self.ticker].index[0]  # Getting index of desired row

        n_above = n // 2
        n_below = n - n_above

        start_row = max(0, sic_index - n_above)  # Getting the index
        end_row = min(sic_index + n_below, len(company_list) - 1)

        surronding_companies = company_list.iloc[start_row:end_row + 1]

        if len(surronding_companies) < (n + 1):
            n_below = n - len(surronding_companies) + 1
            end_row = min(end_row + n_below, len(company_list) - 1)
            surronding_companies = company_list.iloc[start_row:end_row + 1]

        if len(surronding_companies) < (n + 1):
            n_above = n - len(surronding_companies) + 1
            start_row = max(0, start_row - n_above)
            surronding_companies = company_list.iloc[start_row:end_row + 1]

        surronding_companies = surronding_companies.rename(columns={'ticker': 'Ticker', 'title': 'Name'})

        return surronding_companies

    def ratios(self, start, end):

        df = self.data
        df = df["facts"]
        sic_code = self.SIC
        bank_codes = [6022, 6021, 6211, 6029, 6035, 6199]

        balance_r = self.balance(start - 1, end)
        income_r = self.income(start, end).astype(float)
        cash_r = self.cashflow(start, end)

        year_list = [i for i in np.arange(end, start - 1, -1)]

        try:
            cap_df = pd.DataFrame(df["dei"]["EntityPublicFloat"]["units"]["USD"])
            cap_df["fy"] = cap_df["frame"].str[2:6]
        except:
            cap_df = None

        cap = []
        for i in year_list:
            try:
                cap.append(cap_df.loc[cap_df['fy'] == str(i), 'val'].iloc[0])
            except:
                cap.append(None)

        cap = pd.Series(cap, index=year_list)

        ebitda = income_r.loc["EBITDA"]
        ebit = income_r.loc["EBIT"]
        net_profit = income_r.loc["Net Profit"]
        operating_profit = income_r.loc["Operating Profit"]
        tax = income_r.loc["Tax"]

        if sic_code in bank_codes:
            total_assets = balance_r.loc["Total Assets"]
            total_liabilities = balance_r.loc["Total Liabilities"]
            total_se = balance_r.loc["Stockholder's Equity"]
            total_equity = balance_r.loc["Total Equity"]
            cash = balance_r.loc["Cash and Cash Equivalents"]

        else:
            current_assets = balance_r.loc["Total Current Assets"]
            total_assets = balance_r.loc["Total Assets"]
            current_liabilities = balance_r.loc["Total Current Liabilities"]
            total_liabilities = balance_r.loc["Total Liabilities"]
            total_se = balance_r.loc["Stockholder's Equity"]
            total_equity = balance_r.loc["Total Equity"]
            inventory = balance_r.loc["Inventories"]
            cash = balance_r.loc["Cash and Cash Equivalents"]
            nwc = (current_assets - current_liabilities).diff(-1)

        fcf = cash_r.loc["Free Cash Flow"]

        d_a = pd.Series(self.year_tree_item(cce5_2, start, end, "income"), index=year_list)
        capex = pd.Series(self.year_tree_item(cce4_8, start, end, "cashflow"), index=year_list)

        if sic_code in bank_codes:
            ufcf = operating_profit + tax - capex + d_a
        else:
            ufcf = operating_profit + tax - capex + d_a - nwc

        cap = cap + total_liabilities - cash

        ratio_df = pd.DataFrame(columns=year_list)

        if sic_code in bank_codes:
            ratio_df.loc["Debt-to-Equity Ratio"] = (total_liabilities / total_se)

            ratio_df.loc["Return on Equity"] = (net_profit / total_se)
            ratio_df.loc["Return on Assets"] = (net_profit / total_assets)
            ratio_df.loc["Return on Invested Capital"] = (operating_profit + tax) / (total_liabilities + total_equity)

            ratio_df.loc["FCFF Yield"] = ufcf / (cap)

            ratio_df.loc["EV/EBITDA"] = (cap / ebitda)

        else:
            ratio_df.loc["Current Ratio"] = (current_assets / current_liabilities)
            ratio_df.loc["Quick Ratio"] = ((current_assets - inventory) / current_liabilities)

            ratio_df.loc["Debt-to-Equity Ratio"] = (total_liabilities / total_se)

            ratio_df.loc["Return on Equity"] = (net_profit / total_se)
            ratio_df.loc["Return on Assets"] = (net_profit / total_assets)
            ratio_df.loc["Return on Capital Employed"] = ebit / (total_assets - current_liabilities)
            ratio_df.loc["Return on Invested Capital"] = (operating_profit + tax) / (total_liabilities + total_equity)

            ratio_df.loc["FCFF Yield"] = ufcf / (cap)

            ratio_df.loc["EV/EBITDA"] = (cap / ebitda)

        ratio_df.dropna(axis=1, how='all', inplace=True)

        ratio_df["Mean"] = ratio_df.mean(axis=1)

        return ratio_df
