"""Юнит-тесты модуля date_utils."""

from datetime import date, timedelta

import pytest

from src.utils.date_utils import calculate_period, get_period_dates


def test_calculate_period_returns_today_as_end():
    """period_end всегда сегодня, начало = today-(days-1)."""
    days = 5
    period_start, period_end = calculate_period(days)
    assert period_end == date.today()
    assert period_start == date.today() - timedelta(days=days - 1)


def test_get_period_dates_matches_requested_length():
    """Длина списка дат совпадает с days и покрывает период подряд."""
    days = 10
    dates = get_period_dates(days)
    assert len(dates) == days
    assert dates[0] == date.today() - timedelta(days=days - 1)
    assert dates[-1] == date.today()
    for i in range(len(dates) - 1):
        assert dates[i + 1] - dates[i] == timedelta(days=1)


def test_get_period_dates_single_day():
    """Для days=1 период состоит только из сегодняшней даты."""
    dates = get_period_dates(1)
    assert dates == [date.today()]


def test_get_period_dates_boundary_365_days():
    """Граничный кейс: поддержка периода в 365 дней."""
    dates = get_period_dates(365)
    assert len(dates) == 365
    assert dates[0] == date.today() - timedelta(days=364)
    assert dates[-1] == date.today()


def test_get_period_dates_handles_month_change(monkeypatch):
    """Корректный расчёт при смене месяца/високосных дат."""

    class FixedDate(date):
        @classmethod
        def today(cls):
            return cls(2024, 3, 1)  # после високосного дня

    monkeypatch.setattr("src.utils.date_utils.date", FixedDate)

    dates = get_period_dates(2)
    assert dates[0] == FixedDate(2024, 2, 29)
    assert dates[1] == FixedDate(2024, 3, 1)


def test_calculate_period_raises_for_invalid_days():
    """days < 1 приводит к исключению."""
    with pytest.raises(ValueError):
        calculate_period(0)
