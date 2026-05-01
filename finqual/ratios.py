"""
Pure financial ratio functions.

Every function in this module takes plain ``dict`` mappings (line item → value)
as inputs and returns a ``float``. They are deliberately decoupled from
networking, caching and Polars so they can be unit-tested in isolation.

The ``Mapping`` argument lets callers pass either a ``dict`` or a Polars row
adapter that quacks like one. Missing keys raise ``KeyError`` and
zero-denominator division raises ``ZeroDivisionError`` — both are caught by
the orchestrating layer in :mod:`finqual.core`.
"""

from __future__ import annotations

from typing import Mapping

Number = float | int


# ------------------------------------------------------------------ #
# Profitability
# ------------------------------------------------------------------ #

def sga_ratio(income: Mapping[str, Number]) -> float:
    return income["Selling General And Administration"] / income["Total Revenue"]


def rd_ratio(income: Mapping[str, Number]) -> float:
    return income["Research And Development"] / income["Total Revenue"]


def operating_margin(income: Mapping[str, Number]) -> float:
    return income["Operating Income"] / income["Total Revenue"]


def gross_margin(income: Mapping[str, Number]) -> float:
    return income["Gross Profit"] / income["Total Revenue"]


def roa(income: Mapping[str, Number], balance: Mapping[str, Number]) -> float:
    return income["Net Income"] / balance["Total Assets"]


def roe(income: Mapping[str, Number], balance: Mapping[str, Number]) -> float:
    return income["Net Income"] / balance["Stockholders Equity"]


def roic(income: Mapping[str, Number], balance: Mapping[str, Number]) -> float:
    """
    Return on Invested Capital.

    NOPAT / Invested Capital, with NOPAT = Operating Income × (1 − tax rate)
    and Invested Capital = Total Assets − non-interest-bearing current
    liabilities (here approximated as the sum of short-term investments,
    accounts payable and other current liabilities).
    """
    tax_rate = income.get("Tax Provision", 0) / income["Pretax Income"]
    nopat = income["Operating Income"] * (1 - tax_rate)
    invested_capital = (
        balance["Total Assets"]
        - balance["Other Short Term Investments"]
        - balance["Accounts Payable"]
        - balance["Other Current Liabilities"]
    )
    return nopat / invested_capital


# ------------------------------------------------------------------ #
# Liquidity / leverage
# ------------------------------------------------------------------ #

def current_ratio(balance: Mapping[str, Number]) -> float:
    return balance["Current Assets"] / balance["Current Liabilities"]


def quick_ratio(balance: Mapping[str, Number]) -> float:
    return (balance["Current Assets"] - balance["Inventory"]) / balance["Current Liabilities"]


def debt_to_equity(balance: Mapping[str, Number]) -> float:
    return balance["Total Liabilities Net Minority Interest"] / balance["Stockholders Equity"]


# ------------------------------------------------------------------ #
# Valuation
# ------------------------------------------------------------------ #

def eps(income: Mapping[str, Number], balance: Mapping[str, Number]) -> float:
    return income["Net Income"] / balance["Shares Outstanding"]


def pe(income: Mapping[str, Number], balance: Mapping[str, Number], share_price: Number) -> float:
    return share_price / eps(income, balance)


def pb(income: Mapping[str, Number], balance: Mapping[str, Number], share_price: Number) -> float:
    book_value = balance["Total Assets"] - balance["Total Liabilities Net Minority Interest"]
    return (share_price * balance["Shares Outstanding"]) / book_value


def ev_ebitda(
    income: Mapping[str, Number],
    balance: Mapping[str, Number],
    cashflow: Mapping[str, Number],
    share_price: Number,
) -> float:
    """Approximation: EV ≈ Market Cap + End Cash Position; EBITDA ≈ Operating Income + D&A."""
    enterprise_value = balance["Shares Outstanding"] * share_price + cashflow["End Cash Position"]
    ebitda = income["Operating Income"] + cashflow["Depreciation And Amortization"]
    return enterprise_value / ebitda


__all__ = [
    "sga_ratio",
    "rd_ratio",
    "operating_margin",
    "gross_margin",
    "roa",
    "roe",
    "roic",
    "current_ratio",
    "quick_ratio",
    "debt_to_equity",
    "eps",
    "pe",
    "pb",
    "ev_ebitda",
]
