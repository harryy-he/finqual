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

def triangulate_smart(df: pl.DataFrame, rules: list[dict[str]]) -> tuple[pl.DataFrame, list[str]]:
    """
    Triangulate financials using rule-based recalculation in Polars.

    Parameters
    ----------
    df : pl.DataFrame
        Must have columns ["line_item", "value", "total_prob"]
    rules : list of dicts
        Each dict contains:
        - "vars": list[str]  # variables in the rule
        - "calc": callable   # function accepting keyword args
        - "prefer_balance": optional list[str]  # tie-breaker

    Returns
    -------
    pl.DataFrame, list[str]
    """
    notes: list[str] = []
    updated: set[str] = set()

    # Convert to dict-of-rows keyed by line_item for fast updates
    data = {
        row["line_item"]: {
            "value": float(row["value"]) if row["value"] is not None else None,
            "total_prob": float(row["total_prob"]) if row["total_prob"] is not None else None
        }
        for row in df.iter_rows(named=True)
    }

    for rule in rules:
        vars_ = rule["vars"]
        calc_fn = rule["calc"]
        prefer = rule.get("prefer_balance", [])

        try:
            probs = [data[v]["total_prob"] for v in vars_]
            values = [data[v]["value"] for v in vars_]
            var_keys = [v.replace(" ", "_").lower() for v in vars_]

            # Candidates: low confidence and not yet updated
            low_conf_indices = [
                i for i, p in enumerate(probs)
                if (p is not None and p < 3.0 and vars_[i] not in updated)
            ]
            if not low_conf_indices:
                continue

            min_prob = min(probs[i] for i in low_conf_indices)
            candidates = [i for i in low_conf_indices if probs[i] == min_prob]

            # Select candidate
            if len(candidates) == 1:
                i = candidates[0]
            else:
                preferred_found = [j for j in candidates if vars_[j] in prefer or var_keys[j] in prefer]
                i = preferred_found[0] if preferred_found else candidates[0]

            # Only calculate if all other vars are known
            if all(values[j] is not None for j in range(len(vars_)) if j != i):
                kwargs = {var_keys[j]: None if j == i else values[j] for j in range(len(vars_))}
                result = calc_fn(**kwargs)
                if result is not None:
                    missing_var = vars_[i]
                    data[missing_var]["value"] = float(result)
                    data[missing_var]["total_prob"] = 1.0
                    updated.add(missing_var)
                    notes.append(f"Recalculated '{missing_var}' using rule '{rule['name']}'")
        except KeyError:
            continue

    # Rebuild Polars DataFrame, ensuring numeric columns are floats
    df_out = pl.DataFrame(
        {
            "line_item": list(data.keys()),
            "value": [data[k]["value"] for k in data],
            "total_prob": [data[k]["total_prob"] for k in data],
        }
    )

    # Force float dtype explicitly to avoid mixed-type errors
    df_out = df_out.with_columns([
        pl.col("value").cast(pl.Float64),
        pl.col("total_prob").cast(pl.Float64)
    ])

    return df_out, notes

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
    def _process_annual_quarter(self, year: int, quarter: int, label_type: tuple):

        quarter_list = self._previous_quarters(year, quarter)

        if quarter_list[0][1] != 3:
            fy_diff = self.sec_edgar.align_fy_year(False)
        else:
            fy_diff = 0

        # --- Select FY result
        fy_result = []

        if "".join(label_type) == "income_statement":
            fy_result = self.income_stmt(year - fy_diff, None)
        elif "".join(label_type) == "cash_flow":
            fy_result = self.cash_flow(year - fy_diff, None)

        # --- Collect quarterly results
        quarterly_results = []
        data = 0

        for curr_year, curr_quarter in quarter_list:
            if "".join(label_type) == "income_statement":
                data = self.income_stmt(curr_year, curr_quarter)[:,1]

            elif "".join(label_type) == "cash_flow":
                data = self.cash_flow(curr_year, curr_quarter)[:,1]

            if (data == 0).all():   # Checking that it is not all 0's
                print(f"No data for ASML {curr_year}Q{curr_quarter}.")

                df_annual_quarter = pl.DataFrame({
                    "line_item": fy_result[:, 0],
                    "value": 0,
                    "total_prob": 1
                })

                return df_annual_quarter

            quarterly_results.append(data)

        quarterly_sum = sum(quarterly_results)

        # --- Adjust cash flow specifics
        df_annual_quarter = []

        if "".join(label_type) == "income_statement":

            fy_series = fy_result[:, 1]
            annual_quarter = fy_series - quarterly_sum

            # Put it back into a dataframe with line items
            df_annual_quarter = pl.DataFrame({
                "line_item": fy_result[:, 0],
                "value": annual_quarter,
                "total_prob": 1
            })

        elif "".join(label_type) == "cash_flow":
            beginning_cash = self.cash_flow(quarter_list[0][0], quarter_list[0][1])[4,1]
            end_cash = fy_result[5,1]

            fy_series = fy_result[:, 1]
            annual_quarter = fy_series - quarterly_sum

            annual_quarter[4] = beginning_cash
            annual_quarter[5] = end_cash

            # Put it back into a dataframe with line items
            df_annual_quarter = pl.DataFrame({
                "line_item": fy_result[:, 0],
                "value": annual_quarter,
                "total_prob": 1
            })

        return df_annual_quarter

    @weak_lru(maxsize=10)
    def _process_financials(self, year: int, quarter: int | None, label_type: tuple,
                            period_type: tuple, target_yf_list: tuple, tolerance: float = 0.4):

        if self.taxonomy == 'ifrs-full':
            tolerance = 0.0

        sec_data = self.sec_edgar.financial_data_period(year, quarter)
        sec_data_dict = dict(zip(sec_data['key'], sec_data['val']))

        if len(sec_data_dict) > 1:
            if quarter == self.sec_edgar.get_annual_quarter():
                if "".join(label_type) in ['income_statement', 'cash_flow']:
                    df = self._process_annual_quarter(year, quarter, label_type)
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

            return df_total

        else:
            #print(f"*** Finqual: There is no data available for ticker {self.ticker} for year {year} and/or quarter {quarter} - it may be too newly listed or in the future. \n")
            df_target = pl.DataFrame({"line_item": target_yf_list})
            df_target = df_target.with_columns(pl.lit(0).alias("value"))
            df_target = df_target.with_columns(pl.lit(0).alias("total_prob"))

            return df_target

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

        df_income = df_income.with_columns(pl.col("total_prob").cast(pl.Float64))

        increments = {
            "Total Revenue": 0.5,
            "Gross Profit": 0.5,
            "Operating Income": 0.5,
            "Pretax Income": 0.5,
            "Net Income": 0.5
        }

        # ---

        for item, inc in increments.items():
            df_income = df_income.with_columns(
                pl.when((pl.col("line_item") == item) & (pl.col("total_prob") != 0))
                .then(pl.col("total_prob") + inc)
                .otherwise(pl.col("total_prob"))
                .alias("total_prob")
            )

        df_income, log = triangulate_smart(df_income, rules)

        label = str(year) if quarter is None else f"{year}Q{quarter}"
        df_income = df_income.rename({"value": label, "line_item": self.ticker})

        if "total_prob" in df_income.columns:
            df_income = df_income.drop("total_prob")

        df_income = df_income.with_columns(
            pl.when(pl.col(label) == -0.0)
            .then(0.0)
            .otherwise(pl.col(label).round(0))
            .alias(label)
        )

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
            period_type=tuple(["instant"]),
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

        label = str(year) if quarter is None else f"{year}Q{quarter}"
        df_bs = df_bs.rename({"value": label, "line_item": self.ticker})

        try:
            shares = float(self.sec_edgar.get_shares(year, quarter))

        except (ValueError, TypeError):
            shares = 0.0

        df_bs = pl.concat([df_bs, pl.DataFrame({self.ticker: ["Shares Outstanding"], label: [shares], "total_prob": [1.0]})])

        if "total_prob" in df_bs.columns:
            df_bs = df_bs.drop("total_prob")

        df_bs = df_bs.with_columns(
            pl.when(pl.col(label) == -0.0)
            .then(0.0)
            .otherwise(pl.col(label).round(0))
            .alias(label)
        )

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

        label = str(year) if quarter is None else f"{year}Q{quarter}"
        df_cf = df_cf.rename({"value": label,"line_item": self.ticker})

        if "total_prob" in df_cf.columns:
            df_cf = df_cf.drop("total_prob")

        df_cf = df_cf.with_columns(
            pl.when(pl.col(label) == -0.0)
            .then(0.0)
            .otherwise(pl.col(label).round(0))
            .alias(label)
        )

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

            # Collect and concat Polars DataFrames horizontally
            df_results = [results[label] for label in ordered_labels if label in results]
            if not df_results:
                return pl.DataFrame()

            df_results = [df.select([df.columns[0], df[df.columns[1]].alias(label)]) for df, label in zip(df_results, ordered_labels)]

            df_total = df_results[0]
            for df in df_results[1:]:
                df_total = df_total.join(df, on=df.columns[0])

            non_zero_cols = [col for col in df_total.columns if not (df_total[col] == 0).all()]
            df_total = df_total.select(non_zero_cols)

            ordered_labels_in_df = [lbl for lbl in ordered_labels if lbl in df_total.columns]
            df_total = df_total.select([self.ticker] + ordered_labels_in_df)

            return df_total

        elif append_type == 'ratios':

            dfs = []

            for df in results.values():
                dfs.append(df)

            df_total = pl.concat(dfs, how="vertical")

            metric_cols = [c for c in df_total.columns if c not in ("Ticker", "Period")]

            df_mask = df_total.select([pl.when(pl.col(c).is_nan()).then(0).otherwise(pl.col(c)).alias(c) for c in metric_cols])
            non_zero_mask = df_mask.select(pl.any_horizontal([pl.col(c) != 0 for c in metric_cols])).to_series()
            df_total = df_total.filter(non_zero_mask)

            df_total = df_total.sort("Period", descending=True)

            return df_total

    def income_stmt_period(self, start_year: int, end_year: int, quarter: bool = False):
        return self._financials_period('income_stmt', start_year, end_year, 'statement', quarter)

    def balance_sheet_period(self, start_year: int, end_year: int, quarter: bool = False):

        df_bs = self._financials_period('balance_sheet', start_year, end_year, 'statement', quarter)
        df_filtered = df_bs.filter(pl.col(self.ticker) != "Shares Outstanding")
        cols_to_drop = [col for col in df_filtered.columns if (df_filtered[col] == 0).all()]
        df_bs = df_bs.drop(cols_to_drop)

        return df_bs

    def cash_flow_period(self, start_year: int, end_year: int, quarter: bool = False):
        return self._financials_period('cash_flow', start_year, end_year, 'statement', quarter)

    def income_stmt_ttm(self):
        current_year = int(datetime.now().year)

        # TODO: find latest, change previous_quarter method
        # df_sec = self.sec_edgar.sec_data
        # df_sec = df_sec.with_columns([pl.col("frame_map").str.extract(r"CY(\d{4})Q\d").cast(pl.Int32).alias("Year"), pl.col("frame_map").str.extract(r"Q(\d)").cast(pl.Int32).alias("Quarter")])
        #
        # latest_year = df_sec["Year"].max()
        # latest_quarter = df_sec.filter(pl.col("Year") == latest_year)["Quarter"].max()

        df_inc = self.income_stmt_period(current_year - 2, current_year + 1, True)

        line_items = df_inc.select(pl.col(df_inc.columns[0]))

        if df_inc.width < 4:
            print(f"Not enough data to calculate income TTM for {self.ticker}")

            df_inc = self.income_stmt_period(current_year - 2, current_year + 2)
            line_items = df_inc.select(pl.col(df_inc.columns[0]))

            df_ttm = pl.DataFrame({
                self.ticker: line_items,
                "TTM": df_inc.select(pl.col(df_inc.columns[1])),
            })

            return df_ttm

        df_ttm = df_inc.select(pl.col(df_inc.columns[1:5]))
        ttm = sum(df_ttm)

        df_ttm = pl.DataFrame({
            self.ticker: line_items,
            "TTM": ttm,
        })

        return df_ttm

    def balance_sheet_ttm(self):
        current_year = int(datetime.now().year)
        df_bs = self.balance_sheet_period(current_year - 1, current_year + 1, True)

        line_items = df_bs.select(pl.col(df_bs.columns[0]))

        if df_bs.width < 1:
            print(f"No balance sheet data for {self.ticker}")

            df_ttm = pl.DataFrame({
                self.ticker: line_items,
                "TTM": np.nan,
            })

            return df_ttm

        df_ttm = df_bs.select(pl.col(df_bs.columns[1:2]))
        ttm = sum(df_ttm)

        df_ttm = pl.DataFrame({
            self.ticker: line_items,
            "TTM": ttm,
        })

        return df_ttm

    def cash_flow_ttm(self):
        current_year = int(datetime.now().year)
        df_cf = self.cash_flow_period(current_year - 2, current_year + 1, True)

        line_items = df_cf.select(pl.col(df_cf.columns[0]))

        if df_cf.width <= 4:
            print(f"Not enough data to calculate cashflow TTM for {self.ticker}")

            df_cf = self.cash_flow_period(current_year - 2, current_year + 2)
            line_items = df_cf.select(pl.col(df_cf.columns[0]))

            df_ttm = pl.DataFrame({
                self.ticker: line_items,
                "TTM": df_cf.select(pl.col(df_cf.columns[1])),
            })

            return df_ttm

        df_ttm = df_cf.select(pl.col(df_cf.columns[1:5]))
        ttm = sum(df_ttm)

        beginning_cash = df_ttm[4,3]
        end_cash = df_ttm[5,0]
        chg_cash = end_cash - beginning_cash

        df_ttm = pl.DataFrame({
            self.ticker: line_items,
            "TTM": ttm,
        })

        # --- Adjust specific line items

        df_ttm[4,1] = beginning_cash
        df_ttm[5,1] = end_cash
        df_ttm[6,1] = chg_cash

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
                    statement_data[name] = dict(zip(stmt[self.ticker], stmt[label]))
                else:
                    stmt = fetcher(year, quarter)
                    statement_data[name] = dict(zip(stmt[self.ticker], stmt[label]))

            result = {'Ticker': self.ticker, 'Period': label}
            for ratio, func in ratio_definitions.items():
                try:
                    result[ratio] = func(statement_data) * ratio_multiplier
                except (ZeroDivisionError, TypeError):
                    result[ratio] = np.nan
            return result

        except KeyError:
            print(f"No data for {self.ticker} found.")
            result = {'Ticker': self.ticker, 'Period': label}
            for ratio, func in ratio_definitions.items():
                result[ratio] = np.nan
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

        df_ratio = pl.DataFrame([ratios])
        df_ratio = df_ratio.fill_null(np.nan)

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

        df_ratio = pl.DataFrame([ratios])
        df_ratio = df_ratio.fill_null(np.nan)

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

        df_ratio = pl.DataFrame([ratios])
        df_ratio = df_ratio.fill_null(np.nan)

        return df_ratio

    def profitability_ratios_period(self, start_year: int, end_year: int, quarter: bool = False):
        return self._financials_period("profitability_ratios", start_year, end_year, 'ratios', quarter)

    def liquidity_ratios_period(self, start_year: int, end_year: int, quarter: bool = False):
        return self._financials_period("liquidity_ratios", start_year, end_year, 'ratios', quarter)

    def valuation_ratios_period(self, start_year: int, end_year: int, quarter: bool = False):
        return self._financials_period("valuation_ratios", start_year, end_year, 'ratios', quarter)
