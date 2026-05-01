"""Unit tests for the pure ratio functions in ``finqual.ratios``."""

import math

import pytest

from finqual import ratios


# ------------------------------------------------------------------ #
# Profitability
# ------------------------------------------------------------------ #

def test_gross_margin(income_stmt_fixture):
    assert ratios.gross_margin(income_stmt_fixture) == pytest.approx(0.40)


def test_operating_margin(income_stmt_fixture):
    assert ratios.operating_margin(income_stmt_fixture) == pytest.approx(0.25)


def test_sga_ratio(income_stmt_fixture):
    assert ratios.sga_ratio(income_stmt_fixture) == pytest.approx(0.10)


def test_rd_ratio(income_stmt_fixture):
    assert ratios.rd_ratio(income_stmt_fixture) == pytest.approx(0.05)


def test_roa(income_stmt_fixture, balance_sheet_fixture):
    # 160 / 5000
    assert ratios.roa(income_stmt_fixture, balance_sheet_fixture) == pytest.approx(0.032)


def test_roe(income_stmt_fixture, balance_sheet_fixture):
    # 160 / 3000
    assert ratios.roe(income_stmt_fixture, balance_sheet_fixture) == pytest.approx(0.05333, rel=1e-3)


def test_roic(income_stmt_fixture, balance_sheet_fixture):
    # tax rate = 40 / 200 = 0.20  → NOPAT = 250 * 0.8 = 200
    # invested = 5000 - 200 - 100 - 100 = 4600
    # ROIC = 200 / 4600
    assert ratios.roic(income_stmt_fixture, balance_sheet_fixture) == pytest.approx(200 / 4600)


# ------------------------------------------------------------------ #
# Liquidity / leverage
# ------------------------------------------------------------------ #

def test_current_ratio(balance_sheet_fixture):
    assert ratios.current_ratio(balance_sheet_fixture) == pytest.approx(1.875)


def test_quick_ratio(balance_sheet_fixture):
    # (1500 - 300) / 800 = 1.5
    assert ratios.quick_ratio(balance_sheet_fixture) == pytest.approx(1.5)


def test_debt_to_equity(balance_sheet_fixture):
    assert ratios.debt_to_equity(balance_sheet_fixture) == pytest.approx(2000 / 3000)


# ------------------------------------------------------------------ #
# Valuation
# ------------------------------------------------------------------ #

def test_eps(income_stmt_fixture, balance_sheet_fixture):
    # 160 / 100
    assert ratios.eps(income_stmt_fixture, balance_sheet_fixture) == pytest.approx(1.6)


def test_pe(income_stmt_fixture, balance_sheet_fixture):
    # share_price = 16  → P/E = 16 / 1.6 = 10
    assert ratios.pe(income_stmt_fixture, balance_sheet_fixture, share_price=16.0) == pytest.approx(10.0)


def test_pb(income_stmt_fixture, balance_sheet_fixture):
    # market_cap = 100 * 16 = 1600
    # book_value = 5000 - 2000 = 3000
    # P/B = 1600 / 3000
    assert ratios.pb(income_stmt_fixture, balance_sheet_fixture, share_price=16.0) == pytest.approx(1600 / 3000)


def test_ev_ebitda(income_stmt_fixture, balance_sheet_fixture, cash_flow_fixture):
    # EV = 100 * 16 + 400 = 2000
    # EBITDA = 250 + 50 = 300
    expected = 2000 / 300
    assert ratios.ev_ebitda(income_stmt_fixture, balance_sheet_fixture, cash_flow_fixture, 16.0) == pytest.approx(expected)


# ------------------------------------------------------------------ #
# Error paths
# ------------------------------------------------------------------ #

def test_zero_denominator_raises_zero_division():
    with pytest.raises(ZeroDivisionError):
        ratios.gross_margin({"Total Revenue": 0, "Gross Profit": 100})


def test_missing_key_raises_key_error():
    with pytest.raises(KeyError):
        ratios.roe({"Net Income": 100}, {})  # Stockholders Equity missing


def test_handles_mapping_like_inputs():
    """The functions accept any Mapping, not strictly dict."""
    from collections import OrderedDict
    inc = OrderedDict([("Total Revenue", 100.0), ("Gross Profit", 30.0)])
    assert math.isclose(ratios.gross_margin(inc), 0.3)
