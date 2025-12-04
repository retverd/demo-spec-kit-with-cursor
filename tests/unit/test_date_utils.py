"""Unit tests for date_utils module."""

from datetime import date, timedelta

import pytest

from src.utils.date_utils import get_last_7_days


def test_get_last_7_days_returns_seven_dates():
    """Test that get_last_7_days returns exactly 7 dates."""
    dates = get_last_7_days()
    assert len(dates) == 7


def test_get_last_7_days_includes_today():
    """Test that get_last_7_days includes today as the last date."""
    dates = get_last_7_days()
    today = date.today()
    assert dates[-1] == today


def test_get_last_7_days_starts_six_days_ago():
    """Test that get_last_7_days starts from today - 6 days."""
    dates = get_last_7_days()
    today = date.today()
    expected_start = today - timedelta(days=6)
    assert dates[0] == expected_start


def test_get_last_7_days_sequential_dates():
    """Test that get_last_7_days returns sequential calendar days."""
    dates = get_last_7_days()
    for i in range(len(dates) - 1):
        assert dates[i + 1] - dates[i] == timedelta(days=1)


def test_get_last_7_days_covers_seven_day_period():
    """Test that get_last_7_days covers exactly 7 days: [today, today - 6]."""
    dates = get_last_7_days()
    today = date.today()
    start_date = today - timedelta(days=6)
    
    # Check first and last dates
    assert dates[0] == start_date
    assert dates[-1] == today
    
    # Check span is 6 days (7 days total inclusive)
    assert (dates[-1] - dates[0]).days == 6


