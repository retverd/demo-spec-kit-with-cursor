"""Юнит-тесты модуля date_utils."""

from datetime import date, timedelta

from src.utils.date_utils import get_last_7_days


def test_get_last_7_days_returns_seven_dates():
    """Проверка того, что функция возвращает ровно 7 дат."""
    dates = get_last_7_days()
    assert len(dates) == 7


def test_get_last_7_days_includes_today():
    """Проверка того, что последняя дата — сегодня."""
    dates = get_last_7_days()
    today = date.today()
    assert dates[-1] == today


def test_get_last_7_days_starts_six_days_ago():
    """Проверка того, что первая дата — сегодня минус 6 дней."""
    dates = get_last_7_days()
    today = date.today()
    expected_start = today - timedelta(days=6)
    assert dates[0] == expected_start


def test_get_last_7_days_sequential_dates():
    """Проверка того, что даты идут последовательно по дням."""
    dates = get_last_7_days()
    for i in range(len(dates) - 1):
        assert dates[i + 1] - dates[i] == timedelta(days=1)


def test_get_last_7_days_covers_seven_day_period():
    """Проверка того, что функция покрывает диапазон из 7 дней: [сегодня-6, сегодня]."""
    dates = get_last_7_days()
    today = date.today()
    start_date = today - timedelta(days=6)

    # Проверяем первую и последнюю даты
    assert dates[0] == start_date
    assert dates[-1] == today

    # Проверка того, что разница между первой и последней датой равна 6 дням (7 дней включительно)
    assert (dates[-1] - dates[0]).days == 6
