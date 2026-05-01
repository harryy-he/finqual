"""Unit tests for the small period/quarter helper functions."""

from datetime import datetime, timedelta, timezone

import pytest

from finqual.core import _parse_period_to_start_date, Finqual


def test_parse_period_years():
    now = datetime.now(timezone.utc)
    result = _parse_period_to_start_date("2y")
    # Should be ~ 2 years before now (allow tiny clock drift).
    assert (now.year - result.year) == 2


def test_parse_period_months():
    now = datetime.now(timezone.utc)
    result = _parse_period_to_start_date("6m")
    expected_month = (now.month - 6) % 12 or 12
    assert result.month == expected_month


def test_parse_period_days():
    now = datetime.now(timezone.utc)
    result = _parse_period_to_start_date("30d")
    delta = now - result
    # Allow a tiny tolerance for the call latency.
    assert timedelta(days=29, hours=23) <= delta <= timedelta(days=30, hours=1)


def test_parse_period_invalid_unit_raises():
    with pytest.raises(ValueError):
        _parse_period_to_start_date("5z")


def test_parse_period_empty_string_raises():
    with pytest.raises(ValueError):
        _parse_period_to_start_date("y")  # no integer prefix → int('') fails


def test_previous_quarters_no_wraparound():
    # FY2024 ends in Q4 → previous three quarters: 2024Q3, Q2, Q1
    out = Finqual._previous_quarters(2024, 4)
    assert out == [[2024, 3], [2024, 2], [2024, 1]]


def test_previous_quarters_wraparound_from_q1():
    # FY2024 ends in Q1 → previous three quarters: 2023Q4, Q3, Q2
    out = Finqual._previous_quarters(2024, 1)
    assert out == [[2023, 4], [2023, 3], [2023, 2]]


def test_previous_quarters_wraparound_from_q2():
    # FY2024 ends in Q2 → previous three quarters: 2024Q1, 2023Q4, 2023Q3
    out = Finqual._previous_quarters(2024, 2)
    assert out == [[2024, 1], [2023, 4], [2023, 3]]
