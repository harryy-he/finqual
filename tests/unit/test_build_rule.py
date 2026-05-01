"""Unit tests for ``finqual.core.build_rule``."""

from finqual.core import build_rule


def test_extracts_variables_from_equation():
    rule = build_rule("Gross Profit = Total Revenue - Cost Of Revenue")
    expected = {"Gross Profit", "Total Revenue", "Cost Of Revenue"}
    assert set(rule["vars"]) == expected
    assert rule["name"] == "Gross Profit = Total Revenue - Cost Of Revenue"


def test_solves_for_lhs_when_rhs_known():
    rule = build_rule("Gross Profit = Total Revenue - Cost Of Revenue")
    result = rule["calc"](
        gross_profit=None,
        total_revenue=1000.0,
        cost_of_revenue=600.0,
    )
    assert result == 400.0


def test_solves_for_rhs_variable_with_subtraction_sign():
    rule = build_rule("Gross Profit = Total Revenue - Cost Of Revenue")
    # Gross Profit and Total Revenue known → Cost Of Revenue = TR - GP = 1000 - 400 = 600
    result = rule["calc"](
        gross_profit=400.0,
        total_revenue=1000.0,
        cost_of_revenue=None,
    )
    assert result == 600.0


def test_solves_for_rhs_variable_with_addition_sign():
    rule = build_rule(
        "Pretax Income = Operating Income - Interest Expense + Other Non Operating Income Expense"
    )
    # Solve for Other Non Operating Income Expense:
    # 200 = 250 - 30 + X  →  X = -20
    result = rule["calc"](
        pretax_income=200.0,
        operating_income=250.0,
        interest_expense=30.0,
        other_non_operating_income_expense=None,
    )
    assert result == -20.0


def test_returns_none_when_more_than_one_unknown():
    rule = build_rule("A = B - C")
    result = rule["calc"](a=None, b=None, c=10.0)
    assert result is None


def test_returns_none_when_no_unknown():
    rule = build_rule("A = B - C")
    result = rule["calc"](a=1.0, b=2.0, c=1.0)
    # All known → calc has nothing to solve.
    assert result is None


def test_prefer_balance_keys_normalised():
    rule = build_rule("Gross Profit = Total Revenue - Cost Of Revenue",
                      prefer_balance=["Gross Profit"])
    assert rule["prefer_balance"] == ["gross_profit"]
