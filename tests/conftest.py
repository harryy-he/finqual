"""
Shared pytest fixtures for the finqual test suite.

Kept deliberately small — most pure-function unit tests build their own
fixtures inline so each test is self-documenting.
"""

import pytest


@pytest.fixture
def income_stmt_fixture():
    """A representative income-statement mapping used by ratio tests."""
    return {
        "Total Revenue": 1000.0,
        "Cost Of Revenue": 600.0,
        "Gross Profit": 400.0,
        "Selling General And Administration": 100.0,
        "Research And Development": 50.0,
        "Operating Income": 250.0,
        "Pretax Income": 200.0,
        "Tax Provision": 40.0,
        "Net Income": 160.0,
    }


@pytest.fixture
def balance_sheet_fixture():
    """A representative balance-sheet mapping used by ratio tests."""
    return {
        "Total Assets": 5000.0,
        "Current Assets": 1500.0,
        "Inventory": 300.0,
        "Other Short Term Investments": 200.0,
        "Current Liabilities": 800.0,
        "Accounts Payable": 100.0,
        "Other Current Liabilities": 100.0,
        "Total Liabilities Net Minority Interest": 2000.0,
        "Stockholders Equity": 3000.0,
        "Shares Outstanding": 100.0,
    }


@pytest.fixture
def cash_flow_fixture():
    """A representative cash-flow mapping used by ratio tests."""
    return {
        "Operating Cash Flow": 300.0,
        "Depreciation And Amortization": 50.0,
        "Investing Cash Flow": -100.0,
        "Financing Cash Flow": -80.0,
        "End Cash Position": 400.0,
    }
