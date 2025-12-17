"""Утилиты расчёта диапазона дат для выгрузки курсов."""

from datetime import date, timedelta
from typing import List, Tuple


def calculate_period(days: int) -> Tuple[date, date]:
    """
    Рассчитать границы периода длиной `days` дней (включительно).

    Args:
        days: Количество дней в периоде (>=1).

    Returns:
        Кортеж (period_start, period_end), где period_end = date.today().
    """
    if days < 1:
        raise ValueError("days must be >= 1")
    today = date.today()
    period_start = today - timedelta(days=days - 1)
    return period_start, today


def get_period_dates(days: int) -> List[date]:
    """
    Получить последовательность дат периода длиной `days` дней.

    Args:
        days: Количество дней.

    Returns:
        Список дат от period_start до today включительно, в хронологическом порядке.
    """
    period_start, _ = calculate_period(days)
    return [period_start + timedelta(days=i) for i in range(days)]
