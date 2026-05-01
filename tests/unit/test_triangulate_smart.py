"""Unit tests for ``finqual.core.triangulate_smart``."""

import polars as pl

from finqual.core import build_rule, triangulate_smart


def make_df(rows):
    """Build the expected (line_item, value, total_prob) DataFrame."""
    return pl.DataFrame(
        rows, schema={"line_item": pl.Utf8, "value": pl.Float64, "total_prob": pl.Float64}
    )


def test_recalculates_low_confidence_value():
    """A low-confidence Gross Profit should be back-solved from Revenue and COGS."""
    df = make_df([
        {"line_item": "Total Revenue", "value": 1000.0, "total_prob": 5.0},
        {"line_item": "Cost Of Revenue", "value": 600.0, "total_prob": 5.0},
        # Wrong / low-confidence value:
        {"line_item": "Gross Profit", "value": 999.0, "total_prob": 1.0},
    ])
    rules = [build_rule("Gross Profit = Total Revenue - Cost Of Revenue",
                        prefer_balance=["Gross Profit"])]

    df_out, notes = triangulate_smart(df, rules)
    gp = df_out.filter(pl.col("line_item") == "Gross Profit").row(0)
    assert gp[1] == 400.0  # value
    assert gp[2] == 1.0    # total_prob bumped to 1.0 after recalculation
    assert any("Gross Profit" in n for n in notes)


def test_skips_when_rule_dependencies_missing():
    """If a rule references a variable not in the DF, it is skipped silently."""
    df = make_df([
        {"line_item": "Total Revenue", "value": 1000.0, "total_prob": 5.0},
        # No Cost Of Revenue row at all.
        {"line_item": "Gross Profit", "value": 999.0, "total_prob": 1.0},
    ])
    rules = [build_rule("Gross Profit = Total Revenue - Cost Of Revenue")]
    df_out, notes = triangulate_smart(df, rules)
    # Nothing should change (the missing var triggers a KeyError caught by triangulate_smart).
    assert notes == []
    assert df_out.filter(pl.col("line_item") == "Gross Profit").row(0)[1] == 999.0


def test_does_not_modify_high_confidence_values():
    """All variables ≥3.0 prob → nothing recalculated."""
    df = make_df([
        {"line_item": "Total Revenue", "value": 1000.0, "total_prob": 5.0},
        {"line_item": "Cost Of Revenue", "value": 600.0, "total_prob": 5.0},
        {"line_item": "Gross Profit", "value": 400.0, "total_prob": 5.0},
    ])
    rules = [build_rule("Gross Profit = Total Revenue - Cost Of Revenue")]
    df_out, notes = triangulate_smart(df, rules)
    assert notes == []
    assert df_out.filter(pl.col("line_item") == "Gross Profit").row(0)[1] == 400.0


def test_output_columns_are_floats():
    df = make_df([
        {"line_item": "A", "value": 10.0, "total_prob": 5.0},
        {"line_item": "B", "value": 4.0, "total_prob": 5.0},
        {"line_item": "C", "value": 0.0, "total_prob": 1.0},
    ])
    rules = [build_rule("A = B + C")]  # Solve for C: 10 = 4 + 6
    df_out, _ = triangulate_smart(df, rules)
    assert df_out.schema["value"] == pl.Float64
    assert df_out.schema["total_prob"] == pl.Float64


def test_prefers_balance_variable_when_tied():
    """When two candidates have the same low confidence, prefer-balance breaks the tie."""
    df = make_df([
        {"line_item": "A", "value": 100.0, "total_prob": 5.0},
        {"line_item": "B", "value": 60.0, "total_prob": 1.0},   # low conf
        {"line_item": "C", "value": 999.0, "total_prob": 1.0},  # low conf, but preferred
    ])
    rules = [build_rule("A = B + C", prefer_balance=["C"])]
    df_out, notes = triangulate_smart(df, rules)
    # C should be the one rebalanced; A and B remain.
    a = df_out.filter(pl.col("line_item") == "A").row(0)
    b = df_out.filter(pl.col("line_item") == "B").row(0)
    c = df_out.filter(pl.col("line_item") == "C").row(0)
    assert a[1] == 100.0
    assert b[1] == 60.0
    assert c[1] == 40.0   # 100 - 60
    assert any("C" in n for n in notes)
