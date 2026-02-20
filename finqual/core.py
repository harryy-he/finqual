from .node_classes.node_tree import NodeTree
from .node_classes.node import Node
from .sec_edgar.sec_api import SecApi
from .stocktwit import StockTwit
from .form_4 import retrieve_form_4

import functools
from importlib.resources import files
import ijson
import numpy as np
import polars as pl
import re
import weakref

from concurrent.futures import ThreadPoolExecutor, as_completed

def weak_lru(maxsize: int = 128, typed: bool = False):
    """
    LRU cache decorator that stores a weak reference to 'self'.

    This decorator is used to cache instance method results while avoiding
    memory leaks by keeping only a weak reference to the object.

    Parameters
    ----------
    maxsize : int, optional
        Maximum size of the LRU cache (default is 128).
    typed : bool, optional
        If True, arguments of different types will be cached separately.

    Returns
    -------
    callable
        Decorator function to wrap methods with a weak LRU cache.
    """
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
    Converts an equation string into a calculation rule dictionary.

    The rule dictionary includes the variables involved, a calculation function
    to solve for any missing variable, and optionally a list of preferred variables
    for balancing.

    Parameters
    ----------
    equation_str : str
        A string representing the equation (e.g., "Gross Profit = Total Revenue - Cost Of Revenue").
    prefer_balance : list of str, optional
        List of variables to prioritize when balancing or recalculating.

    Returns
    -------
    dict
        A dictionary containing:
        - 'name': str, original equation string
        - 'vars': list[str], variables in the equation
        - 'calc': callable, function to calculate missing variable
        - 'prefer_balance': list[str], normalized preferred balancing variables
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
    Apply rule-based triangulation to a financial DataFrame to fill missing values.

    The function recalculates low-confidence line items using defined rules
    and preferred balancing variables.

    Parameters
    ----------
    df : pl.DataFrame
        DataFrame containing financial data with columns ["line_item", "value", "total_prob"].
    rules : list of dict
        List of rule dictionaries (as returned by `build_rule`) defining variable relationships.

    Returns
    -------
    tuple
        - pl.DataFrame: Updated DataFrame with recalculated values
        - list[str]: Notes describing which line items were recalculated
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
    """
    The main interface for interacting with SEC EDGAR filings and standardized financial data.

    This class abstracts access to company-specific fundamentals (income statement, balance sheet,
    cash flow), metadata (ticker, CIK, taxonomy, sector), and their associated taxonomy trees and labels.

    It uses the `SecApi` client to fetch filing information, determine taxonomy, and then selects
    the appropriate data resources (trees and labels) for that taxonomy.

    Attributes
    ----------
    ticker_or_cik : str | int
        The company identifier (ticker symbol or CIK).
    sec_edgar : SecApi
        Underlying SEC API client used to query filings and metadata.
    ticker : str
        Company ticker symbol.
    cik : str
        Company CIK code (10-digit zero-padded string).
    taxonomy : str
        The accounting taxonomy used by the company (e.g., "us-gaap" or "ifrs-full").
    trees : dict[str, list[Node]]
        Parsed financial statement structure definitions based on taxonomy.
    labels : pl.LazyFrame | pl.DataFrame
        Polars DataFrame or LazyFrame with taxonomy label mappings and metadata.
    sector : str
        Company’s industry sector (as identified by SEC metadata).
    """
    
    def __init__(self, ticker_or_cik: str | int):
        self.ticker_or_cik = ticker_or_cik
        self.sec_edgar = SecApi(ticker_or_cik)
        self.ticker = self.sec_edgar.id_data.ticker
        self.cik = self.sec_edgar.id_data.cik
        self.taxonomy = self.sec_edgar.facts_data.taxonomy
        self.sector = self.sec_edgar.submissions_data.sector

        self.trees = self.select_tree()
        self.labels = self.select_label()


    @staticmethod
    def load_trees(file_name: str) -> dict[str, list[Node]]:
        """
        Load taxonomy trees from a JSON file.

        Parameters
        ----------
        file_name : str
            Name of the JSON file containing taxonomy trees.

        Returns
        -------
        dict[str, list[Node]]
            Dictionary mapping ticker to a list of Node objects representing the tree.
        """
        path = files("finqual.data") / file_name
        trees_dict: dict[str, list[Node]] = {}

        with open(path, "r", encoding="utf-8") as f:
            # assume structure like { "AAPL": [ {...}, {...} ], "MSFT": [ {...} ] }
            parser = ijson.kvitems(f, "")
            for key, node_list in parser:
                # Stream each node instead of loading all
                trees_dict[key] = [Node.from_dict(n) for n in node_list]

        return trees_dict

    @staticmethod
    def load_label(file_name: str) -> pl.DataFrame:
        """
        Load label mappings from a Parquet file.

        Parameters
        ----------
        file_name : str
            Name of the Parquet file containing label data.

        Returns
        -------
        pl.DataFrame
            Polars DataFrame with taxonomy label information.
        """
        path = files("finqual.data") / file_name
        df_label = pl.scan_parquet(path)
        return df_label

    def select_tree(self) -> dict[str, list[Node]]:
        """
        Select and load the appropriate taxonomy tree based on the company's taxonomy.

        Returns
        -------
        dict[str, list[Node]]
            Dictionary of Node trees keyed by ticker.
        """
        if self.taxonomy == "us-gaap":
            return self.load_trees("gaap_trees.json")

        elif self.taxonomy == "ifrs-full":
            return self.load_trees("ifrs_trees.json")

        else:
            return self.load_trees("gaap_trees.json")

    def select_label(self) -> pl.LazyFrame | pl.DataFrame:
        """
        Select and load the appropriate label mapping based on taxonomy.

        Returns
        -------
        pl.LazyFrame | pl.DataFrame
            Polars DataFrame or LazyFrame with filtered label mappings.
        """
        # --- Determine which label file to load based on taxonomy

        label_files = {
            "us-gaap": "gaap_labels_v2.parquet",
            "ifrs-full": "ifrs_labels.parquet",
        }

        file_name = label_files.get(self.taxonomy, "gaap_labels.parquet")
        path = files("finqual.data") / file_name

        # --- Efficient loading

        needed_cols = ["count", "yf", "type", "code", "prob"]  # Adjust based on how you use df_label downstream

        df_label = (
            pl.scan_parquet(path)
            .select(needed_cols)
            .filter(pl.col("count") > 1)
        )

        return df_label

    @staticmethod
    def _previous_quarters(year: int, annual_quarter: int) -> list[list[int]]:
        """
        Calculate the three previous quarters given a year and annual quarter.

        Parameters
        ----------
        year : int
            Year of the annual quarter.
        annual_quarter : int
            Quarter number of the annual report (1-4).

        Returns
        -------
        list[list[int]]
            List of [year, quarter] pairs for the three previous quarters.
        """
        results = []
        for i in range(1, 4):
            q = annual_quarter - i
            fy = year
            if q <= 0:
                q += 4
                fy -= 1
            results.append([fy, q])
        return results

    @weak_lru(maxsize=4)
    def _process_annual_quarter(self, year: int, quarter: int, label_type: tuple) -> pl.DataFrame:
        """
        Process annual quarter data by comparing annual report with the sum of previous quarters.

        Parameters
        ----------
        year : int
            Fiscal year.
        quarter : int
            Quarter number of the annual report.
        label_type : tuple
            Statement type tuple, e.g., ("income_statement",) or ("cash_flow",).

        Returns
        -------
        pl.DataFrame
            Polars DataFrame with annual quarter values.
        """

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
                data = self.income_stmt(curr_year, curr_quarter)[:, 1]

            elif "".join(label_type) == "cash_flow":
                data = self.cash_flow(curr_year, curr_quarter)[:, 1]

            if (data == 0).all():   # Checking that it is not all 0's
                print(f"No data for {self.ticker} {curr_year}Q{curr_quarter}.")

                df_annual_quarter = pl.DataFrame({
                    "line_item": fy_result[:, 0],
                    "value": 0,
                    "total_prob": 1
                })

                return df_annual_quarter

            quarterly_results.append(data)

        quarterly_sum = sum(quarterly_results)

        # --- Subtracting annual values from the sum of the previous three quarters

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
            end_cash = fy_result[4, 1]

            fy_series = fy_result[:, 1]
            annual_quarter = fy_series - quarterly_sum

            annual_quarter[4] = end_cash    # Specific cashflow adjustment as end cash is instantaneous

            # Put it back into a dataframe with line items
            df_annual_quarter = pl.DataFrame({
                "line_item": fy_result[:, 0],
                "value": annual_quarter,
                "total_prob": 1
            })

        return df_annual_quarter

    @weak_lru(maxsize=4)
    def _process_financials(self, year: int, quarter: int | None, label_type: tuple,
                            period_type: tuple, target_yf_list: tuple, tolerance: float = 0.4) -> pl.DataFrame:
        """
        Fetch and process financial data for a given year, quarter, and statement type.

        Parameters
        ----------
        year : int
            Fiscal year.
        quarter : int | None
            Fiscal quarter; None for annual data.
        label_type : tuple
            Statement type(s), e.g., ("income_statement",), ("cash_flow",).
        period_type : tuple
            Period type(s), e.g., ("duration", "instant").
        target_yf_list : tuple
            List of target line items to retrieve.
        tolerance : float, default=0.4
            Minimum probability threshold for including a line item.

        Returns
        -------
        pl.DataFrame
            Polars DataFrame with processed financial data.
        """

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
                nodes_copy = [n.copy() for n in nodes]  # make a thread-safe copy
                tree = NodeTree(nodes_copy)

                tree.load_sec_data(sec_data_dict)
                tree.get_all_values()   # TODO: this is not deterministic, see AMZN 2024 "Total Liabilities Net Minority Interest" changes
                df_tree = tree.to_df()

                if df_tree is not None:
                    all_dfs.append(df_tree.lazy().with_columns(pl.col("balance").cast(pl.Utf8)))

            if not all_dfs:
                return pl.DataFrame()

            df_label_lazy = (
                self.labels.lazy()
                .filter(pl.col("type").is_in(label_type))
                .select(["code", "yf", "prob"])
            )

            df_total = (
                pl.concat(all_dfs, how="vertical")
                .with_columns(pl.col("balance").cast(pl.Utf8))
                .filter(pl.col("period_type").is_in(period_type))
                .join(df_label_lazy, on="code", how="inner")
                .unique()
                .filter(pl.col("yf").is_in(target_yf_list))
                .select(["yf", "prob", "value"])
                .group_by(["yf", "value"])
                .agg(pl.col("prob").sum().alias("total_prob"))
                .sort(["yf", "total_prob", "value"], descending=[False, True, False])
                .with_columns(pl.arange(0, pl.len()).alias("row_num"))  # stable tie-breaker
                .unique(subset="yf", keep="first")  # deterministic now
                .filter(pl.col("total_prob") >= tolerance)
                .drop("row_num")  # optional: remove tie-breaker
                .collect(engine="streaming")
            )

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
            # print(f"*** Finqual: There is no data available for ticker {self.ticker} for year {year} and/or quarter {quarter} - it may be too newly listed or in the future. \n")
            df_target = pl.DataFrame({"line_item": target_yf_list})
            df_target = df_target.with_columns(pl.lit(0).alias("value"))
            df_target = df_target.with_columns(pl.lit(0).alias("total_prob"))

            return df_target

    @weak_lru(maxsize=4)
    def income_stmt(self, year: int, quarter: int | None = None) -> pl.DataFrame:
        """
        Retrieve the income statement for a given year and optional quarter.

        Parameters
        ----------
        year : int
            Fiscal year.
        quarter : int | None, optional
            Fiscal quarter; None for annual report.

        Returns
        -------
        pl.DataFrame
            Polars DataFrame of the income statement, with line items as rows.
        """

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
            "Total Revenue": 1.0,
            "Gross Profit": 1.0,
            "Operating Income": 1.0,
            "Pretax Income": 1.0,
            "Net Income": 1.0
        }

        # ---

        for item, inc in increments.items():

            # --- For Gross Profit, this line item is sometimes not reported explicitly

            expected_frame = f"CY{year}" if quarter is None else f"CY{year}Q{quarter}"

            if item == "Gross Profit":
                exists = any(
                    k == "GrossProfit" and f == expected_frame
                    for k, f in zip(
                        self.sec_edgar.facts_data.sec_data['key'], 
                        self.sec_edgar.facts_data.sec_data['frame_map'])
                    )
                if not exists:
                    continue

            # ---

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

    @weak_lru(maxsize=4)
    def balance_sheet(self, year: int, quarter: int | None = None) -> pl.DataFrame:
        """
        Retrieve the balance sheet for a given year and optional quarter.

        Parameters
        ----------
        year : int
            Fiscal year.
        quarter : int | None, optional
            Fiscal quarter; None for annual report.

        Returns
        -------
        pl.DataFrame
            Polars DataFrame of the balance sheet, with line items as rows.
        """

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

    @weak_lru(maxsize=4)
    def cash_flow(self, year: int, quarter: int | None = None) -> pl.DataFrame:
        """
        Retrieve the cash flow statement for a given year and optional quarter.

        Parameters
        ----------
        year : int
            Fiscal year.
        quarter : int | None, optional
            Fiscal quarter; None for annual report.

        Returns
        -------
        pl.DataFrame
            Polars DataFrame of the cash flow statement, with line items as rows.
        """

        cashflow_list = [

            "Operating Cash Flow",
            "Depreciation And Amortization",
            
            "Investing Cash Flow",
            
            "Financing Cash Flow",
            "End Cash Position",
        ]

        df_cf = self._process_financials(
            year, quarter,
            label_type=tuple(["cash_flow"]),
            period_type=tuple(["duration", "instant"]),
            target_yf_list=tuple(cashflow_list),
        )

        label = str(year) if quarter is None else f"{year}Q{quarter}"
        df_cf = df_cf.rename({"value": label, "line_item": self.ticker})

        if "total_prob" in df_cf.columns:
            df_cf = df_cf.drop("total_prob")

        df_cf = df_cf.with_columns(
            pl.when(pl.col(label) == -0.0)
            .then(0.0)
            .otherwise(pl.col(label).round(0))
            .alias(label)
        )

        return df_cf

    def _financials_period(self, method_name: str, start_year: int, end_year: int, append_type: str, quarter: bool = False) -> pl.DataFrame:
        """
        Retrieve financial statements or ratios over a specified period.

        Parameters
        ----------
        method_name : str
            Method to call (e.g., 'income_stmt', 'balance_sheet').
        start_year : int
            Start year of the period.
        end_year : int
            End year of the period.
        append_type : str
            'statement' for financials, 'ratios' for ratios.
        quarter : bool, default=False
            If True, returns quarterly data.

        Returns
        -------
        pl.DataFrame
            Concatenated Polars DataFrame for the specified period.
        """
        func = getattr(self, method_name)

        years_period = [i for i in range(end_year, start_year - 1, -1)]

        results = {}
        with ThreadPoolExecutor(max_workers=2) as executor:
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

    def income_stmt_period(self, start_year: int, end_year: int,
                           quarter: bool = False) -> pl.DataFrame:
        """
        Retrieve income statements over a range of years or quarters.

        Parameters
        ----------
        start_year : int
            Start year of the period.
        end_year : int
            End year of the period.
        quarter : bool, default=False
            If True, returns quarterly data; otherwise annual.

        Returns
        -------
        pl.DataFrame
            Polars DataFrame with income statement values for each year/quarter.
        """
        return self._financials_period('income_stmt', start_year, end_year, 'statement', quarter)

    def balance_sheet_period(self, start_year: int, end_year: int,
                             quarter: bool = False) -> pl.DataFrame:
        """
        Retrieve balance sheets over a range of years or quarters.

        Parameters
        ----------
        start_year : int
            Start year of the period.
        end_year : int
            End year of the period.
        quarter : bool, default=False
            If True, returns quarterly data; otherwise annual.

        Returns
        -------
        pl.DataFrame
            Polars DataFrame with balance sheet values for each year/quarter.
            Drops columns where all values are zero and removes "Shares Outstanding" from main data.
        """

        df_bs = self._financials_period('balance_sheet', start_year, end_year, 'statement', quarter)
        df_filtered = df_bs.filter(pl.col(self.ticker) != "Shares Outstanding")
        cols_to_drop = [col for col in df_filtered.columns if (df_filtered[col] == 0).all()]
        df_bs = df_bs.drop(cols_to_drop)

        return df_bs

    def cash_flow_period(self, start_year: int, end_year: int,
                         quarter: bool = False) -> pl.DataFrame:
        """
        Retrieve cash flow statements over a range of years or quarters.

        Parameters
        ----------
        start_year : int
            Start year of the period.
        end_year : int
            End year of the period.
        quarter : bool, default=False
            If True, returns quarterly data; otherwise annual.

        Returns
        -------
        pl.DataFrame
            Polars DataFrame with cash flow statement values for each year/quarter.
        """
        return self._financials_period('cash_flow', start_year, end_year, 'statement', quarter)

    @weak_lru(maxsize=4)
    def income_stmt_ttm(self) -> pl.DataFrame:
        """
        Retrieve trailing twelve months (TTM) income statement.

        Returns
        -------
        pl.DataFrame
            Polars DataFrame containing TTM income statement values.
        Notes
        -----
        If insufficient quarterly data exists, falls back to annual data for TTM calculation.
        """
        current_year, current_quarter = self.sec_edgar.latest_report(quarterly=True)

        df_inc = self.income_stmt_period(current_year - 1, current_year, True)

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

    @weak_lru(maxsize=4)
    def balance_sheet_ttm(self) -> pl.DataFrame:
        """
        Retrieve trailing twelve months (TTM) balance sheet.

        Returns
        -------
        pl.DataFrame
            Polars DataFrame containing TTM balance sheet values.
        Notes
        -----
        If no balance sheet data exists, returns NaN for TTM values.
        """
        current_year, current_quarter = self.sec_edgar.latest_report(quarterly=True)
        df_bs = self.balance_sheet(current_year, current_quarter)

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

    @weak_lru(maxsize=4)
    def cash_flow_ttm(self) -> pl.DataFrame:
        """
        Retrieve trailing twelve months (TTM) cash flow statement.

        Returns
        -------
        pl.DataFrame
            Polars DataFrame containing TTM cash flow statement values.
        Notes
        -----
        Adjusts end cash position to match instantaneous nature of cash in cash flow statement.
        """
        current_year, current_quarter = self.sec_edgar.latest_report(quarterly=True)
        df_cf = self.cash_flow_period(current_year - 1, current_year, True)

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

        end_cash = df_ttm[4, 0]

        df_ttm = pl.DataFrame({
            self.ticker: line_items,
            "TTM": ttm,
        })

        # --- Adjust specific line items

        df_ttm[4, 1] = end_cash

        return df_ttm

    # ----

    def _get_ratios(self, year: int | None, ratio_definitions: dict, statement_fetchers: dict,
                    quarter: int | None = None, pct_flag: bool = False) -> dict:
        """
        Calculate financial ratios for a specific year/quarter or TTM.

        Parameters
        ----------
        year : int | None
            Fiscal year of interest; None for TTM.
        ratio_definitions : dict[str, callable]
            Dictionary of ratio name to calculation function.
        statement_fetchers : dict[str, callable]
            Dictionary mapping statement types ('income', 'balance', 'cashflow') to fetcher functions.
        quarter : int | None, default=None
            Specific quarter; None for full year or TTM.
        pct_flag : bool, default=False
            If True, ratios are expressed as percentages.

        Returns
        -------
        dict
            Dictionary containing 'Ticker', 'Period', and calculated ratios.
        """
        if pct_flag:
            ratio_multiplier = 100
        else:
            ratio_multiplier = 1

        # --- Label

        if year is None and quarter is None:
            label = "TTM"

        else:
            label = str(year) + "Q" + str(quarter) if quarter is not None else str(year)

        # --- Retrieving ratios

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

    def profitability_ratios(self, year: int | None = None, quarter: int | None = None) -> pl.DataFrame:
        """
        Calculate key profitability ratios (e.g., ROA, ROE, Gross Margin).

        Parameters
        ----------
        year : int | None, default=None
            Fiscal year; None for TTM.
        quarter : int | None, default=None
            Specific quarter; None for annual data.

        Returns
        -------
        pl.DataFrame
            Polars DataFrame with profitability ratios.
        """

        if year is None and quarter is None:

            statement_fetchers = {
                'income': lambda y, q=None: self.income_stmt_ttm(),
                'balance': lambda y, q=None: self.balance_sheet_ttm(),
            }

        else:

            statement_fetchers = {
                'income': lambda y, q=None: self.income_stmt(y, q) if q else self.income_stmt(y),
                'balance': lambda y, q=None: self.balance_sheet(y, q) if q else self.balance_sheet(y),
            }

        ratio_definitions = {
            'SG&A Ratio': lambda data: data['income'].get('Selling General And Administration') / data['income'].get('Total Revenue'),
            'R&D Ratio': lambda data: data['income'].get('Research And Development') / data['income'].get('Total Revenue'),
            'Operating Margin': lambda data: data['income'].get('Operating Income') / data['income'].get('Total Revenue'),
            'Gross Margin': lambda data: data['income'].get('Gross Profit') / data['income'].get('Total Revenue'),
            'ROA': lambda data: data['income'].get('Net Income') / data['balance'].get('Total Assets'),
            'ROE': lambda data: data['income'].get('Net Income') / data['balance'].get('Stockholders Equity'),
            'ROIC': lambda data: data['income'].get('Operating Income') * (1 - (data['income'].get('Tax Provision', 0) / data['income'].get('Pretax Income'))) / (data['balance'].get('Total Assets') - data['balance'].get('Other Short Term Investments') - data['balance'].get('Accounts Payable') - data['balance'].get('Other Current Liabilities')),
        }

        ratios = self._get_ratios(year, ratio_definitions, statement_fetchers, quarter, True)

        df_ratio = pl.DataFrame([ratios])
        df_ratio = df_ratio.fill_null(np.nan)

        return df_ratio

    def liquidity_ratios(self, year: int | None = None, quarter: int | None = None) -> pl.DataFrame:
        """
        Calculate liquidity ratios (Current Ratio, Quick Ratio, Debt-to-Equity).

        Parameters
        ----------
        year : int | None, default=None
            Fiscal year; None for TTM.
        quarter : int | None, default=None
            Specific quarter; None for annual data.

        Returns
        -------
        pl.DataFrame
            Polars DataFrame with liquidity ratios.
        """

        if year is None and quarter is None:

            statement_fetchers = {
                'balance': lambda y, q=None: self.balance_sheet_ttm(),
            }

        else:
            statement_fetchers = {
                'balance': lambda y, q=None: self.balance_sheet(y, q) if q else self.balance_sheet(y),
            }

        ratio_definitions = {
            'Current Ratio': lambda data: data['balance'].get('Current Assets') / data['balance'].get('Current Liabilities'),
            'Quick Ratio': lambda data: (data['balance'].get('Current Assets') - data['balance'].get('Inventory')) / data['balance'].get('Current Liabilities'),
            'Debt-to-Equity Ratio': lambda data: data['balance'].get('Total Liabilities Net Minority Interest') / data['balance'].get('Stockholders Equity'),
        }

        ratios = self._get_ratios(year, ratio_definitions, statement_fetchers, quarter, False)

        df_ratio = pl.DataFrame([ratios])
        df_ratio = df_ratio.fill_null(np.nan)

        return df_ratio

    def valuation_ratios(self, year: int | None = None, quarter: int | None = None) -> pl.DataFrame:
        """
        Calculate valuation ratios (EPS, P/E, P/B, EV/EBITDA) for a given period.

        Parameters
        ----------
        year : int | None, default=None
            Fiscal year; None for TTM.
        quarter : int | None, default=None
            Specific quarter; None for annual data.

        Returns
        -------
        pl.DataFrame
            Polars DataFrame with valuation ratios.
        Notes
        -----
        Historical valuation ratios are not implemented; only current/latest data is supported.
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

    def profitability_ratios_period(self, start_year: int, end_year: int, quarter: bool = False) -> pl.DataFrame:
        """
        Retrieve profitability ratios over a period of years or quarters.

        Parameters
        ----------
        start_year : int
            Start year of the period.
        end_year : int
            End year of the period.
        quarter : bool, default=False
            If True, returns quarterly ratios.

        Returns
        -------
        pl.DataFrame
            Polars DataFrame with profitability ratios over the specified period.
        """
        return self._financials_period("profitability_ratios", start_year, end_year, 'ratios', quarter)

    def liquidity_ratios_period(self, start_year: int, end_year: int, quarter: bool = False) -> pl.DataFrame:
        """
        Retrieve liquidity ratios over a period of years or quarters.

        Parameters
        ----------
        start_year : int
            Start year of the period.
        end_year : int
            End year of the period.
        quarter : bool, default=False
            If True, returns quarterly ratios.

        Returns
        -------
        pl.DataFrame
            Polars DataFrame with liquidity ratios over the specified period.
        """
        return self._financials_period("liquidity_ratios", start_year, end_year, 'ratios', quarter)

    def valuation_ratios_period(self, start_year: int, end_year: int, quarter: bool = False) -> pl.DataFrame:
        """
        Retrieve valuation ratios over a period of years or quarters.

        Parameters
        ----------
        start_year : int
            Start year of the period.
        end_year : int
            End year of the period.
        quarter : bool, default=False
            If True, returns quarterly ratios.

        Returns
        -------
        pl.DataFrame
            Polars DataFrame with valuation ratios over the specified period.
        Notes
        -----
        Only current/latest valuation ratios are supported; historical valuation is not implemented.
        """
        return self._financials_period("valuation_ratios", start_year, end_year, 'ratios', quarter)

    def get_insider_transactions(self, n: int | None) -> pl.DataFrame:

        df = self.sec_edgar.get_form4(n)

        if df is None:
            raise ValueError(f"No Form 4 found for index {n}.")

        else:
            url = df["URL"][n]
            filing_date = df["filingDate"][n]
            report_date = df["reportDate"][n]
            accession_number = df["accessionNumber"][n]

            df_form4 = retrieve_form_4(url, self.sec_edgar.headers)

            df_form4 = df_form4.with_columns([
                pl.lit(filing_date).alias("filingDate"),
                pl.lit(report_date).alias("reportDate"),
                pl.lit(accession_number).alias("accessionNumber")
            ])

        return df_form4

    def get_last_n_insider_transactions(self, n: int) -> pl.DataFrame:

        dfs = []

        for i in range(n):
            try:
                df = self.get_insider_transactions(i)
            except ValueError:
                continue  # skip missing filings

            dfs.append(df)

        combined = pl.concat(dfs)

        return combined



