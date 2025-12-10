"""Функции валидации данных курсов и свечей."""

from datetime import date, timedelta
from math import isnan
from typing import List, Optional, Union

from src.models.candles import CandleRecord
from src.models.exchange_rate import ExchangeRateRecord


def validate_date(date_value: date, period_start: date, period_end: date) -> bool:
    """
    Проверить, что дата входит в заданный период.

    Args:
        date_value: Дата для проверки
        period_start: Начало периода (включительно)
        period_end: Конец периода (включительно)

    Returns:
        True если дата входит в период, иначе False
    """
    return period_start <= date_value <= period_end


def validate_rate(rate: Optional[float]) -> bool:
    """
    Проверить корректность значения курса.

    Args:
        rate: Значение курса (может быть None для пропущенных данных)

    Returns:
        True для None (отсутствие данных) или положительного числа, иначе False
    """
    if rate is None:
        return True  # Missing data is valid
    # Reject non-numeric types (strings, etc.)
    if not isinstance(rate, (int, float)):
        return False
    try:
        rate_float = float(rate)
        return rate_float > 0
    except (ValueError, TypeError):
        return False


def validate_records(
    records: List[ExchangeRateRecord], period_start: date, period_end: date
) -> tuple[bool, Optional[str]]:
    """
    Проверить список записей курса.

    Валидируется:
    1. Ровно 7 записей (по дню в семидневном периоде).
    2. Все даты должны быть корректными и находиться внутри периода.
    3. Дубликаты дат не допускаются.
    4. Ненулевые значения курса должны быть положительными.
    5. Все даты периода должны присутствовать в списке записей.

    Args:
        records: Список объектов класса ExchangeRateRecord для валидации.
        period_start: Начало периода.
        period_end: Конец периода.

    Returns:
        (is_valid, error_message). При успехе error_message = None.
    """
    # Проверка на полноту: ровно 7 записей
    if len(records) != 7:
        return False, f"Expected 7 records, got {len(records)}"

    # Проверка наличия всех дат периода и их уникальности
    dates_seen = set()
    for record in records:
        # Дата должна быть в периоде
        if not validate_date(record.date, period_start, period_end):
            return (
                False,
                f"Date {record.date} is outside the expected period [{period_start}, {period_end}]",
            )

        # Проверка на дубликаты
        if record.date in dates_seen:
            return False, f"Duplicate date found: {record.date}"
        dates_seen.add(record.date)

        # Проверка значения курса
        if not validate_rate(record.exchange_rate_value):
            return (
                False,
                f"Invalid exchange rate value for date {record.date}: {record.exchange_rate_value}",
            )

        # Проверка валютной пары
        if record.currency_pair != "RUB/USD":
            return (
                False,
                f"Invalid currency pair: {record.currency_pair}, expected RUB/USD",
            )

    # Проверка наличия всех дат периода
    expected_dates = {period_start + timedelta(days=i) for i in range(7)}
    if dates_seen != expected_dates:
        missing = expected_dates - dates_seen
        return False, f"Missing dates in records: {missing}"

    return True, None


def _is_non_negative_number(value: Union[int, float]) -> bool:
    """Проверить, что число неотрицательно и не NaN."""
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return False
    if isnan(numeric):
        return False
    return numeric >= 0


def validate_candles(
    records: List[CandleRecord], start_date: date, end_date: date
) -> tuple[bool, Optional[str]]:
    """
    Проверить записи OHLCV для периода 7 дней LQDT/TQTF.

    Проверяется:
    1. Количество записей соответствует длине периода.
    2. Даты уникальны и внутри [start_date, end_date].
    3. Цены/объём неотрицательны, если присутствуют.
    4. Instrument и board соответствуют ожидаемым.
    5. Присутствуют все даты периода.

    Returns:
        (is_valid, error_message)
    """
    if start_date > end_date:
        return False, "Start date is after end date"

    expected_days = (end_date - start_date).days + 1
    if len(records) != expected_days:
        return False, f"Expected {expected_days} records, got {len(records)}"

    dates_seen = set()
    for record in records:
        if not validate_date(record.date, start_date, end_date):
            return (
                False,
                f"Date {record.date} is outside the expected period [{start_date}, {end_date}]",
            )

        if record.date in dates_seen:
            return False, f"Duplicate date found: {record.date}"
        dates_seen.add(record.date)

        if record.instrument != "LQDT":
            return False, f"Invalid instrument: {record.instrument}"
        if record.board != "TQTF":
            return False, f"Invalid board: {record.board}"

        for field_name in ("open", "high", "low", "close", "volume"):
            value = getattr(record, field_name)
            if value is None:
                continue
            if not _is_non_negative_number(value):
                return (
                    False,
                    f"Invalid {field_name} value for date {record.date}: {value}",
                )

    expected_dates = {start_date + timedelta(days=i) for i in range(expected_days)}
    if dates_seen != expected_dates:
        missing = sorted(expected_dates - dates_seen)
        return False, f"Missing dates in records: {missing}"

    return True, None
