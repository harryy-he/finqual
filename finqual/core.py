from .node_classes.node_tree import NodeTree
from .node_classes.node import Node
from .sec_edgar.sec_api import SecApi
from .stocktwit import StockTwit

import copy
from datetime import datetime
import functools
from importlib.resources import files
import json
import numpy as np
import pandas as pd
import polars as pl
import re
import weakref

from concurrent.futures import ThreadPoolExecutor, as_completed

def weak_lru(maxsize=128, typed=False):
    """LRU Cache decorator that keeps a weak reference to 'self'"""
    def wrapper(func):

        @functools.lru_cache(maxsize, typed)
        def _func(_self, *args, **kwargs):
            return func(_self(), *args, **kwargs)

        @functools.wraps(func)
        def inner(self, *args, **kwargs):
            return _func(weakref.ref(self), *args, **kwargs)

        return inner

    return wrapper

def build_rule(equation_str: str, prefer_balance: list[str] = None) -> dict:
    """
    Convert a rule string into a rule dictionary, with a preferred balancing item if specified.
    """
    lhs, rhs = equation_str.split("=")
    lhs = lhs.strip()
    rhs = rhs.strip()

    # Extract variable names
    variables = list(set(re.findall(r"[A-Za-z ]+", equation_str)))
    variables = [v.strip() for v in variables if v.strip() not in {'+', '-', '*', '/', '='}]

    if prefer_balance is None:
        prefer_balance = []

    def calc(**kwargs):
        missing = [k for k, v in kwargs.items() if v is None]
        if len(missing) != 1:
            return None
        missing_key = missing[0]

        # Prepare dict of known vars
        known_vars = {k: v for k, v in kwargs.items() if v is not None}

        # Parse rhs into tokens (var names with signs)
        import re
        tokens = re.findall(r"([+-]?)\s*([A-Za-z ]+)", rhs)

        # Build dictionary of var -> sign (+1 or -1)
        var_signs = {}
        for sign, var in tokens:
            var = var.strip()
            sign_val = 1 if sign != '-' else -1
            var_signs[var.replace(" ", "_").lower()] = sign_val

        # If missing var is LHS, just evaluate rhs with known vars
        lhs_key = lhs.replace(" ", "_").lower()
        if missing_key == lhs_key:
            # sum all known vars with signs
            total = 0
            for var, sign_val in var_signs.items():
                if var not in known_vars:
                    return None
                total += sign_val * known_vars[var]
            return total

        # Otherwise solve for missing var:
        # missing_var * sign = lhs - sum(other vars * their signs)
        if missing_key not in var_signs:
            return None  # can't solve if missing var not in equation

        missing_sign = var_signs[missing_key]
        lhs_val = known_vars.get(lhs_key)
        if lhs_val is None:
            return None

        other_sum = 0
        for var, sign_val in var_signs.items():
            if var != missing_key:
                if var not in known_vars:
                    return None
                other_sum += sign_val * known_vars[var]

        # missing_var = (lhs_val - other_sum) / missing_sign
        return (lhs_val - other_sum) / missing_sign

    return {
        "name": equation_str,
        "vars": variables,
        "calc": calc,
        "prefer_balance": [v.replace(" ", "_").lower() for v in prefer_balance]
    }

def triangulate_smart(df: pd.DataFrame, rules) -> (pl.DataFrame, list):
    df = df.set_index("line_item")
    notes = []
    updated = set()  # Keep track of recalculated items

    for rule in rules:
        vars_ = rule["vars"]
        calc_fn = rule["calc"]
        prefer = rule.get("prefer_balance", [])

        try:
            probs = [df.at[var, "total_prob"] for var in vars_]
            values = [df.at[var, "value"] for var in vars_]
            var_keys = [v.replace(" ", "_").lower() for v in vars_]

            # Force preferred balancing items to lowest prob
            for i, key in enumerate(var_keys):
                if key in prefer and vars_[i] not in updated:
                    probs[i] = 0.0  # Ensure this becomes the target

            low_conf_indices = [i for i, p in enumerate(probs) if p < 3.0 and vars_[i] not in updated]

            if len(low_conf_indices) == 1:
                i = low_conf_indices[0]
            elif len(low_conf_indices) > 1:
                preferred_found = [i for i in low_conf_indices if var_keys[i] in prefer]
                if preferred_found:
                    i = preferred_found[0]
                else:
                    i = sorted(low_conf_indices, key=lambda x: probs[x])[0]
            else:
                continue  # All high-confidence or already updated

            if all(pd.notnull(values[j]) for j in range(len(vars_)) if j != i):
                kwargs = {var_keys[j]: None if j == i else values[j] for j in range(len(vars_))}
                result = calc_fn(**kwargs)
                if result is not None:
                    missing_var = vars_[i]
                    df.at[missing_var, "value"] = result
                    df.at[missing_var, "total_prob"] = 1.0
                    updated.add(missing_var)  # Lock this variable
                    notes.append(f"Recalculated '{missing_var}' using rule '{rule['name']}'")
        except KeyError:
            continue

    df.reset_index(inplace=True)
    return df, notes

# ----------------------------------------------------------------------------------

class Finqual:

    def __init__(self, ticker: str):
        self.ticker = ticker
        self.sec_edgar = SecApi(ticker)
        self.taxonomy = self.sec_edgar.taxonomy

        self.trees = self.select_tree()
        self.labels = self.select_label()

        self.sector = self.sec_edgar.get_sector()

    @staticmethod
    def load_trees(file_name: str) -> dict:
        path = files("finqual.data") / file_name
        with open(path, "r") as f:
            trees_dict = json.load(f)
        return {k: [Node.from_dict(n) for n in v] for k, v in trees_dict.items()}

    @staticmethod
    def load_label(file_name: str) -> pl.DataFrame:
        path = files("finqual.data") / file_name
        df_label = pl.read_parquet(path)
        return df_label

    def select_tree(self):
        if self.taxonomy == "us-gaap":
            return self.load_trees("gaap_trees.json")

        elif self.taxonomy == "ifrs-full":
            return self.load_trees("ifrs_trees.json")

        else:
            return self.load_trees("gaap_trees.json")

    def select_label(self):
        if self.taxonomy == "us-gaap":
            df_label = self.load_label("gaap_labels_v2.parquet")
            df_label = df_label.filter(pl.col("count") > 1)
            # df_probs = df_label.with_columns([(pl.col("count") / pl.sum("count").over(["yf", "type"])).alias("prob")])
            return df_label

        elif self.taxonomy == "ifrs-full":
            df_label = self.load_label("ifrs_labels.parquet")
            df_label = df_label.filter(pl.col("count") > 1)
            return df_label
        else:
            df_label = self.load_label("gaap_labels.parquet")
            df_label = df_label.filter(pl.col("count") > 1)
            return df_label

    @staticmethod
    def _previous_quarters(year: int, annual_quarter: int):

        results = []
        for i in range(1, 4):
            q = annual_quarter - i
            fy = year
            if q <= 0:
                q += 4
                fy -= 1
            results.append([fy, q])
        return results

    @weak_lru(maxsize=10)
    def _process_annual_quarter(self, year: int, quarter: int, label_type: tuple,
                                period_type: tuple, target_yf_list: tuple, tolerance: float = 0.4):

        if self.taxonomy == 'ifrs-full':
            tolerance = 0.0

        quarter_list = self._previous_quarters(year, quarter)

        quarterly_results = []
        fy_diff = self.sec_edgar.align_fy_year(False)
        fy_result = self._process_financials(year - fy_diff, None, label_type, period_type, target_yf_list, tolerance)

        for period in quarter_list:

            curr_year = period[0]
            curr_quarter = period[1]

            quarterly_results.append(self._process_financials(curr_year, curr_quarter, label_type, period_type, target_yf_list, tolerance))

        df_quarterly = pd.concat(quarterly_results, axis=1)
        df_quarterly = df_quarterly.T.groupby(level=0).sum().T

        df_annual_quarter = fy_result.copy()
        df_annual_quarter['value'] = fy_result['value'] - df_quarterly['value']

        if "".join(label_type) in ['cash_flow']:

            df_annual_quarter.loc[4, "value"] = quarterly_results[0].loc[5, "value"]  # Set Beginning Cash to last quarter End Cash
            df_annual_quarter.loc[5, "value"] = fy_result.loc[5, "value"].round(0)  # Set End Cash to FY End Cash

        df_annual_quarter['value'] = df_annual_quarter['value'].apply(lambda x: int(x))

        return df_annual_quarter

    @weak_lru(maxsize=10)
    def _process_financials(self, year: int, quarter: int | None, label_type: tuple,
                            period_type: tuple, target_yf_list: tuple, tolerance: float = 0.4):

        if self.taxonomy == 'ifrs-full':
            tolerance = 0.0

        sec_data = self.sec_edgar.financial_data_period(year, quarter)
        sec_data_dict = dict(zip(sec_data['key'], sec_data['value']))

        if len(sec_data_dict) > 0:
            if quarter == self.sec_edgar.get_annual_quarter():
                if "".join(label_type) in ['income_statement', 'cash_flow']:
                    df = self._process_annual_quarter(year, quarter, label_type, period_type, target_yf_list, tolerance)
                    return df

            all_dfs = []
            for nodes in self.trees.values():
                nodes_copy = copy.deepcopy(nodes)  # make a thread-safe copy
                tree = NodeTree(nodes_copy)

                tree.load_sec_data(sec_data_dict)
                tree.get_all_values()
                df_tree = tree.to_df()

                if df_tree is not None:
                    df_tree = df_tree.with_columns(pl.col("balance").cast(pl.Utf8))
                    all_dfs.append(df_tree)

            df_total = pl.concat(all_dfs, how="vertical") if all_dfs else pl.DataFrame()
            df_total = df_total.filter(pl.col('period_type').is_in(period_type))

            df_label = (self.labels.filter(pl.col('type').is_in(label_type)).select(['code', 'yf', 'prob']))
            df_total = df_total.join(df_label, on='code', how='inner').unique()

            # ---

            df_total = df_total.filter(pl.col('yf').is_in(target_yf_list))

            df_total = df_total.select(['yf', 'prob', 'value'])
            df_total = (df_total.group_by(['yf', 'value']).agg(pl.col('prob').sum().alias('total_prob')).sort('total_prob', descending=True))
            df_total = (df_total.sort(['yf', 'total_prob', 'value'], descending=[False, True, False]).unique(subset='yf', keep='first'))
            df_total = df_total.filter(pl.col('total_prob') >= tolerance)

            # ---

            df_target = pl.DataFrame({'yf': target_yf_list})
            df_total = df_target.join(df_total, on='yf', how='left')

            order_map = {name: i for i, name in enumerate(target_yf_list)}
            df_total = (df_total.with_columns(pl.col('yf').cast(str).replace(order_map).cast(pl.Int32).alias('sort_order')).sort('sort_order').drop('sort_order'))

            df_total = df_total.rename({"yf": "line_item"})
            df_total = df_total.fill_nan(0)

            df_total = df_total.with_columns(df_total["value"].fill_null(0), df_total["total_prob"].fill_null(0))

            return df_total.to_pandas()

        else:
            #print(f"*** Finqual: There is no data available for ticker {self.ticker} for year {year} and/or quarter {quarter} - it may be too newly listed or in the future. \n")
            df_target = pl.DataFrame({"line_item": target_yf_list})
            df_target = df_target.with_columns(pl.lit(0).alias("value"))
            df_target = df_target.with_columns(pl.lit(0).alias("total_prob"))

            return df_target.to_pandas()

    @weak_lru(maxsize=10)
    def income_stmt(self, year: int, quarter: int | None = None):

        income_list = [
            'Total Revenue', 'Cost Of Revenue', 'Gross Profit',
            'Selling General And Administration', 'Research And Development',
            'Other Operating Income Expense', 'Operating Income',
            "Interest Expense", 'Other Non Operating Income Expense', 'Pretax Income',  # 'Total Expenses'
            'Tax Provision', 'Net Income',
        ]

        rules = [
            build_rule("Gross Profit = Total Revenue - Cost Of Revenue", prefer_balance=["Gross Profit"]),
            build_rule("Operating Income = Gross Profit - Selling General And Administration - Research And Development - Other Operating Income Expense", prefer_balance=["Other Operating Income Expense"]),
            build_rule("Pretax Income = Operating Income - Interest Expense + Other Non Operating Income Expense", prefer_balance=["Other Non Operating Income Expense"]),
            build_rule("Net Income = Pretax Income - Tax Provision"),
            build_rule("Total Expenses = Total Revenue - Net Income"),
        ]

        df_income = self._process_financials(
            year, quarter,
            label_type=tuple(["income_statement"]),
            period_type=tuple(["duration"]),
            target_yf_list=tuple(income_list),
        )

        # ---

        df_income["total_prob"] = df_income["total_prob"].astype(float)

        increments = {
            "Total Revenue": 0.5,
            "Gross Profit": 0.5,
            "Operating Income": 0.5,
            "Pretax Income": 0.5,
            "Net Income": 0.5
        }

        for item, inc in increments.items():
            df_income.loc[(df_income["line_item"] == item) & (df_income["total_prob"] != 0), "total_prob"] += inc

        # ---

        df_income, log = triangulate_smart(df_income, rules)

        label = str(year) if quarter is None else str(year) + "Q" + str(quarter)
        df_income = df_income.rename(columns={'value': label, 'line_item': self.ticker})
        df_income = df_income.set_index(self.ticker)
        df_income = df_income.drop(columns=['total_prob'])

        return df_income

    @weak_lru(maxsize=10)
    def balance_sheet(self, year: int, quarter: int | None = None):
        balance_list = [
            "Total Assets",
            "Current Assets", "Other Short Term Investments", "Receivables", "Inventory", "Other Current Assets",
            "Total Non Current Assets", "Net PPE", "Goodwill", "Investments And Advances", "Other Non-Current Assets",

            "Total Liabilities Net Minority Interest",
            "Current Liabilities", "Accounts Payable", "Current Debt", "Current Capital Lease Obligation", "Other Current Liabilities",
            "Total Non Current Liabilities Net Minority Interest", "Long Term Debt", "Long Term Capital Lease Obligation", "Other Non-Current Liabilities",

            "Stockholders Equity", "Capital Stock", "Retained Earnings",
        ]

        df_bs = self._process_financials(
            year, quarter,
            label_type=tuple(["balance_sheet"]),
            period_type=tuple(["instant", "duration"]),
            target_yf_list=tuple(balance_list),
        )

        rules = [
            build_rule("Total Assets = Current Assets + Total Non Current Assets"),
            build_rule("Current Assets = Receivables + Inventory + Other Short Term Investments + Other Current Assets", prefer_balance=['Other Current Assets']),
            build_rule("Total Non Current Assets = Net PPE + Goodwill + Investments And Advances + Other Non-Current Assets", prefer_balance=['Other Non-Current Assets']),
            build_rule("Total Liabilities Net Minority Interest = Current Liabilities + Total Non Current Liabilities Net Minority Interest"),
            build_rule("Liabilities = Accounts Payable + Current Debt + Current Capital Lease Obligation + Other Current Liabilities", prefer_balance=["Other Current Liabilities"]),
            build_rule("Total Non Current Liabilities Net Minority Interest = Long Term Debt + Long Term Capital Lease Obligation + Other Non-Current Liabilities", prefer_balance=['Other Non-Current Liabilities']),
            build_rule("Total Assets = Total Liabilities Net Minority Interest + Stockholders Equity"),
            build_rule("Stockholders Equity = Common Stock + Preferred Stock + Retained Earnings"),
        ]

        df_bs, log = triangulate_smart(df_bs, rules)

        label = str(year) if quarter is None else str(year) + "Q" + str(quarter)
        df_bs = df_bs.rename(columns={'value': label, 'line_item': self.ticker})
        df_bs = df_bs.set_index(self.ticker)

        try:
            df_bs.loc['Shares Outstanding'] = [self.sec_edgar.get_shares(year, quarter), 1]

        except ValueError:
            pass

        df_bs = df_bs.drop(columns=['total_prob'])

        return df_bs

    @weak_lru(maxsize=10)
    def cash_flow(self, year: int, quarter: int | None = None):

        cashflow_list = [

            "Operating Cash Flow",
            "Depreciation And Amortization",
            
            "Investing Cash Flow",
            
            "Financing Cash Flow",
            "Beginning Cash Position", "End Cash Position",
            "Changes In Cash",
        ]

        df_cf = self._process_financials(
            year, quarter,
            label_type=tuple(["cash_flow"]),
            period_type=tuple(["duration", "instant"]),
            target_yf_list=tuple(cashflow_list),
        )

        rules = [
            build_rule("End Cash Position = Beginning Cash Position + Changes In Cash"),
        ]

        df_cf, log = triangulate_smart(df_cf, rules)
        label = str(year) if quarter is None else str(year) + "Q" + str(quarter)
        df_cf = df_cf.rename(columns={'value': label, 'line_item': self.ticker})
        df_cf = df_cf.set_index(self.ticker)
        df_cf = df_cf.drop(columns=['total_prob'])

        return df_cf

    def _financials_period(self, method_name: str, start_year: int, end_year: int, append_type: str, quarter: bool = False):
        """
        General method to retrieve financial statements or ratios over a given period

        :param method_name: Method name within Finqual to call
        :param start_year: Start of period
        :param end_year: End of period
        :param append_type: Tells the method whether it is a 'statement' or 'ratios' to look for
        :param quarter: Returns quarterly info
        :return:
        """
        func = getattr(self, method_name)

        years_period = [i for i in range(end_year, start_year - 1, -1)]

        results = {}
        with ThreadPoolExecutor() as executor:
            futures = {}
            for y in years_period:
                if not quarter:
                    futures[executor.submit(func, y)] = f"{y}"
                else:
                    for q in [4, 3, 2, 1]:
                        futures[executor.submit(func, y, q)] = f"{y}Q{q}"

            for future in as_completed(futures):
                label = futures[future]
                df = future.result()
                results[label] = df

        # # - This is sequential and confirmed to work
        # for y in years_period:
        #     if not quarter:
        #         results[f"{y}"] = func(y)
        #     else:
        #         for q in [4, 3, 2, 1]:
        #             results[f"{y}Q{q}"] = func(y, q)

        if append_type == 'statement':

            if quarter:
                ordered_labels = [f"{y}Q{q}" for y in years_period for q in [4, 3, 2, 1]]
            else:
                ordered_labels = [f"{y}" for y in years_period]

            # Ordering and formatting the result
            ordered_results = [results[label] for label in ordered_labels]
            df_total = pd.concat(ordered_results, axis=1)

            df_total = df_total.loc[:, (df_total != 0).any(axis=0)]
            df_total = df_total[[label for label in ordered_labels if label in df_total.columns]]

            return df_total

        elif append_type == 'ratios':

            # Ordering and formatting the result
            df_total = pd.concat(results, axis=0)

            df_total = df_total.loc[(df_total != 0).any(axis=1), :]
            df_total = df_total.sort_values(by='Period', ascending=False)

            df_total = df_total.reset_index(drop=True)

            return df_total

    def income_stmt_period(self, start_year: int, end_year: int, quarter: bool = False):
        return self._financials_period('income_stmt', start_year, end_year, 'statement', quarter)

    def balance_sheet_period(self, start_year: int, end_year: int, quarter: bool = False):

        df_bs = self._financials_period('balance_sheet', start_year, end_year, 'statement', quarter)
        cols_to_drop = [col for col in df_bs.columns if (df_bs.drop(index="Shares Outstanding")[col] == 0).all()]
        df_bs = df_bs.drop(columns=cols_to_drop)

        return df_bs

    def cash_flow_period(self, start_year: int, end_year: int, quarter: bool = False):
        return self._financials_period('cash_flow', start_year, end_year, 'statement', quarter)

    def income_stmt_ttm(self):
        current_year = int(datetime.now().year)
        df_inc = self.income_stmt_period(current_year - 2, current_year + 1, True)

        if len(df_inc.columns) < 4:
            print("Not enough data to calculate TTM")
            df_ttm = pd.DataFrame(df_inc[df_inc.columns[:4]].sum(axis=1), columns = ["TTM"])
            df_ttm["TTM"] = "Not Found"
            return df_ttm

        df_ttm = pd.DataFrame(df_inc[df_inc.columns[:4]].sum(axis=1), columns = ["TTM"])
        return df_ttm

    def balance_sheet_ttm(self):
        current_year = int(datetime.now().year)
        df_bs = self.balance_sheet_period(current_year - 1, current_year + 1, True)

        if len(df_bs.columns) < 1:
            print("Not enough data to calculate latest balance sheet.")
            df_ttm = pd.DataFrame(df_bs[df_bs.columns[:1]].sum(axis=1), columns = ["TTM"])
            df_ttm["TTM"] = "Not Found"
            return df_ttm

        df_ttm = pd.DataFrame(df_bs[df_bs.columns[:1]].sum(axis=1), columns = ["TTM"])

        return df_ttm

    def cash_flow_ttm(self):
        current_year = int(datetime.now().year)
        df_cf = self.cash_flow_period(current_year - 2, current_year + 1, True)

        if len(df_cf.columns) <= 4:
            print("Not enough data to calculate latest TTM for cashflow.")
            df_ttm = pd.DataFrame(df_cf[df_cf.columns[:4]].sum(axis=1), columns = ["TTM"])
            df_ttm["TTM"] = "Not Found"
            return df_ttm

        df_ttm = df_cf[df_cf.columns[:4]].copy()

        # ---

        df_ttm["TTM"] = df_ttm.iloc[:4,:].sum(axis=1)

        df_ttm.loc["Beginning Cash Position", "TTM"] = df_cf.iloc[4, 3]
        df_ttm.loc["End Cash Position", "TTM"] = df_cf.iloc[5, 0]
        df_ttm.loc["Changes In Cash", "TTM"] = df_cf.iloc[5, 0] - df_cf.iloc[4, 3]

        df_ttm = pd.DataFrame(df_ttm["TTM"], columns=["TTM"])


        return df_ttm

    # ----

    def _get_ratios(self, year: int|None, ratio_definitions: dict, statement_fetchers: dict, quarter: int | None = None, pct_flag: bool = False):
        """
        Method that takes in a dictionary with definitions of ratios and a dictionary of statements to retrieve (i.e. income, balance or cashflow)

        :param year: The year of info to retrieve from
        :param ratio_definitions: Dictionary of ratio definitions/formula
        :param statement_fetchers: Dictionary of statements to retrieve (i.e. income, balance, cashflow)
        :param quarter: The specific quarter to look at
        :param pct_flag: True/False for whether the ratio is expressed in terms of percentages
        :return:
        """
        if pct_flag:
            ratio_multiplier = 100
        else:
            ratio_multiplier = 1

        if year is None and quarter is None:
            label = "TTM"

        else:
            label = str(year) + "Q" + str(quarter) if quarter is not None else str(year)

        try:
            statement_data = {}
            for name, fetcher in statement_fetchers.items():
                if quarter is None:
                    stmt = fetcher(year)
                    statement_data[name] = dict(zip(stmt.index, stmt[label]))
                else:
                    stmt = fetcher(year, quarter)
                    statement_data[name] = dict(zip(stmt.index, stmt[label]))

            result = {'Ticker': self.ticker, 'Period': label}
            for ratio, func in ratio_definitions.items():
                try:
                    result[ratio] = func(statement_data) * ratio_multiplier
                except (ZeroDivisionError, TypeError):
                    result[ratio] = "Not Found"
            return result

        except KeyError:
            print(f"No data for {self.ticker} found.")
            result = {'Ticker': self.ticker, 'Period': label}
            for ratio, func in ratio_definitions.items():
                result[ratio] = "Not Found"
            return result

    def profitability_ratios(self, year: int, quarter: int | None = None):
        ratio_definitions = {
            'SG&A Ratio': lambda data: data['income'].get('Selling General And Administration') / data['income'].get('Total Revenue'),
            'R&D Ratio': lambda data: data['income'].get('Research And Development') / data['income'].get('Total Revenue'),
            'Operating Margin': lambda data: data['income'].get('Operating Income') / data['income'].get('Total Revenue'),
            'Gross Margin': lambda data: data['income'].get('Gross Profit') / data['income'].get('Total Revenue'),
            'ROA': lambda data: data['income'].get('Net Income') / data['balance'].get('Total Assets'),
            'ROE': lambda data: data['income'].get('Net Income') / data['balance'].get('Stockholders Equity'),
            'ROIC': lambda data: data['income'].get('Operating Income') * (1 - (data['income'].get('Tax Provision', 0) / data['income'].get('Pretax Income'))) / (data['balance'].get('Current Assets') - data['balance'].get('Current Liabilities') + data['balance'].get('Net PPE') + data['balance'].get('Goodwill')),
        }

        statement_fetchers = {
            'income': lambda y, q=None: self.income_stmt(y, q) if q else self.income_stmt(y),
            'balance': lambda y, q=None: self.balance_sheet(y, q) if q else self.balance_sheet(y),
        }

        ratios = self._get_ratios(year, ratio_definitions, statement_fetchers, quarter, True)
        df_ratio = pd.DataFrame([ratios])
        df_ratio = df_ratio.fillna("Not Found")

        return df_ratio

    def liquidity_ratios(self, year: int, quarter: int | None = None):
        ratio_definitions = {
            'Current Ratio': lambda data: data['balance'].get('Current Assets') / data['balance'].get('Current Liabilities'),
            'Quick Ratio': lambda data: (data['balance'].get('Current Assets') - data['balance'].get('Inventory')) / data['balance'].get('Current Liabilities'),
            'Debt-to-Equity Ratio': lambda data: data['balance'].get('Total Liabilities Net Minority Interest') / data['balance'].get('Stockholders Equity'),
        }

        statement_fetchers = {
            'balance': lambda y, q=None: self.balance_sheet(y, q) if q else self.balance_sheet(y),
        }

        ratios = self._get_ratios(year, ratio_definitions, statement_fetchers, quarter, False)
        df_ratio = pd.DataFrame([ratios])
        df_ratio = df_ratio.fillna("Not Found")

        return df_ratio

    def valuation_ratios(self, year: int|None = None, quarter: int | None = None):
        """
        Retrieve valuation for a given time period - only works for latest time.

        :param year: Year of interest
        :param quarter: Quarter of interest
        :return:
        """
        if year is None and quarter is None:

            share_price = StockTwit(self.ticker).retrieve_data()[self.ticker]  # This would have to be the share price at the given year and quarter time

            statement_fetchers = {
                'income': lambda y, q=None: self.income_stmt_ttm(),
                'balance': lambda y, q=None: self.balance_sheet_ttm(),
                'cashflow': lambda y, q=None: self.cash_flow_ttm(),
            }

        else:

            print("*** Finqual: Note that functionality for historical valuation ratios not implemented.")

            share_price = np.nan  # Placeholder code - need to add the share price at the requested year and quarter

            statement_fetchers = {
            'income': lambda y, q=None: self.income_stmt(y, q) if q else self.income_stmt(y),
            'balance': lambda y, q=None: self.balance_sheet(y, q) if q else self.balance_sheet(y),
            'cashflow': lambda y, q=None: self.cash_flow(y, q) if q else self.cash_flow(y),
            }

        ratio_definitions = {
            'EPS': lambda data: data['income'].get('Net Income') / data['balance'].get('Shares Outstanding'),
            'P/E': lambda data: share_price / (data['income'].get('Net Income') / data['balance'].get('Shares Outstanding')),
            'P/B': lambda data: (share_price * data['balance'].get('Shares Outstanding')) / (data['balance'].get('Total Assets') - data['balance'].get('Total Liabilities Net Minority Interest')),
            'EV/EBITDA': lambda data: (data['balance'].get('Shares Outstanding') * share_price + data['cashflow'].get('End Cash Position')) / (data['income'].get('Operating Income') + data['cashflow'].get('Depreciation And Amortization')),
        }

        ratios = self._get_ratios(year, ratio_definitions, statement_fetchers, quarter, False)
        df_ratio = pd.DataFrame([ratios])
        df_ratio = df_ratio.fillna("Not Found")

        return df_ratio

    def profitability_ratios_period(self, start_year: int, end_year: int, quarter: bool = False):
        return self._financials_period("profitability_ratios", start_year, end_year, 'ratios', quarter)

    def liquidity_ratios_period(self, start_year: int, end_year: int, quarter: bool = False):
        return self._financials_period("liquidity_ratios", start_year, end_year, 'ratios', quarter)

    def valuation_ratios_period(self, start_year: int, end_year: int, quarter: bool = False):
        return self._financials_period("valuation_ratios", start_year, end_year, 'ratios', quarter)
