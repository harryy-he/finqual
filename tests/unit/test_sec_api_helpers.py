"""Unit tests for the pure-Polars helpers in ``finqual.sec_edgar.sec_api``.

These exercise ``map_missing_frames`` and ``convert_to_quarters`` against
small synthetic DataFrames — no network access required.
"""

import polars as pl

from finqual.sec_edgar.sec_api import map_missing_frames, convert_to_quarters


def _base_row(**overrides):
    """Defaults for a SEC-style fact row, overrideable per test."""
    base = {
        "key": "Revenue",
        "start": "None",
        "end": "2024-12-31",
        "description": "test",
        "val": 100.0,
        "unit": "USD",
        "frame": None,
        "form": "10-K",
        "fp": "FY",
    }
    base.update(overrides)
    return base


def test_map_missing_frames_fills_from_start_end():
    df = pl.DataFrame([
        _base_row(start="2024-01-01", end="2024-12-31", frame="CY2024", val=100),
        # Same start+end, missing frame → should be filled.
        _base_row(start="2024-01-01", end="2024-12-31", frame=None, val=200, fp="Q4"),
    ])
    out = map_missing_frames(df)
    # Both rows should now have a non-null frame_map; second row gets 'CY2024' from neighbour.
    frames = out["frame_map"].to_list()
    assert all(f is not None for f in frames)
    assert "CY2024" in frames


def test_map_missing_frames_appends_I_for_instant_rows():
    """When start='None' (instant), the resulting frame_map ends in 'I'."""
    df = pl.DataFrame([
        _base_row(start="None", end="2024-12-31", frame="CY2024Q4I", val=10, fp="FY"),
    ])
    out = map_missing_frames(df)
    fm = out["frame_map"][0]
    assert fm.endswith("I")


def test_convert_to_quarters_single_quarter_value_unchanged():
    df = pl.DataFrame([
        _base_row(start="2024-01-01", end="2024-03-31", frame="CY2024Q1", val=100, fp="Q1"),
    ])
    df = map_missing_frames(df)
    out = convert_to_quarters(df)
    # Single row → quarter_val should equal val.
    assert out["quarter_val"][0] == 100.0
    assert out["val"][0] == 100.0


def test_convert_to_quarters_subtracts_cumulative_values():
    """Cumulative reporting: Q1=100, H1=250 → derived Q2 = 250-100 = 150."""
    df = pl.DataFrame([
        _base_row(start="2024-01-01", end="2024-03-31", frame="CY2024Q1", val=100, fp="Q1"),
        _base_row(start="2024-01-01", end="2024-06-30", frame="CY2024Q2", val=250, fp="Q2"),
    ])
    df = map_missing_frames(df)
    out = convert_to_quarters(df)
    # Latest row should have quarter_val = 150 (250 - 100).
    q2_row = out.filter(pl.col("frame_map") == "CY2024Q2").row(0, named=True)
    assert q2_row["quarter_val"] == 150.0
    assert q2_row["val"] == 150.0


def test_convert_to_quarters_keeps_instant_values_as_is():
    """Frame containing 'I' (instant) should not be subtracted.

    Instant facts in real SEC data have no ``start`` date. The SEC api
    pipeline serialises that absence as the literal string ``"None"`` until
    ``convert_to_quarters`` parses dates; for an isolated unit test we feed
    a parsable placeholder date so the strptime step succeeds.
    """
    df = pl.DataFrame([
        _base_row(start="2024-12-30", end="2024-12-31", frame="CY2024Q4I", val=500, fp="FY"),
    ])
    df = map_missing_frames(df)
    out = convert_to_quarters(df)
    assert out["quarter_val"][0] == 500.0
    assert out["val"][0] == 500.0
