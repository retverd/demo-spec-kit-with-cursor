"""Data validation functions for exchange rate records."""

from datetime import date, timedelta
from math import isnan
from typing import List, Optional, Union

from src.models.candles import CandleRecord
from src.models.exchange_rate import ExchangeRateRecord


def validate_date(date_value: date, period_start: date, period_end: date) -> bool:
    """
    Validate that a date is within the specified period.

    Args:
        date_value: The date to validate
        period_start: Start date of the valid period (inclusive)
        period_end: End date of the valid period (inclusive)

    Returns:
        True if date is within the period, False otherwise
    """
    return period_start <= date_value <= period_end


def validate_rate(rate: Optional[float]) -> bool:
    """
    Validate that an exchange rate value is valid.

    Args:
        rate: The exchange rate value (can be None for missing data)

    Returns:
        True if rate is None (missing data) or a positive number, False otherwise
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
    Validate a list of exchange rate records.

    Performs the following validations:
    1. Must have exactly 7 records (one per day in the 7-day period)
    2. All dates must be valid and within the period
    3. All dates must be unique (no duplicates)
    4. Non-null rates must be positive numbers
    5. All dates in the period must be present

    Args:
        records: List of ExchangeRateRecord objects to validate
        period_start: Start date of the expected period
        period_end: End date of the expected period

    Returns:
        Tuple of (is_valid, error_message). If is_valid is True, error_message is None.
    """
    # Check completeness: must have exactly 7 records
    if len(records) != 7:
        return False, f"Expected 7 records, got {len(records)}"

    # Check all dates are present and unique
    dates_seen = set()
    for record in records:
        # Validate date is within period
        if not validate_date(record.date, period_start, period_end):
            return (
                False,
                f"Date {record.date} is outside the expected period [{period_start}, {period_end}]",
            )

        # Check for duplicates
        if record.date in dates_seen:
            return False, f"Duplicate date found: {record.date}"
        dates_seen.add(record.date)

        # Validate rate
        if not validate_rate(record.exchange_rate_value):
            return (
                False,
                f"Invalid exchange rate value for date {record.date}: {record.exchange_rate_value}",
            )

        # Validate currency pair
        if record.currency_pair != "RUB/USD":
            return (
                False,
                f"Invalid currency pair: {record.currency_pair}, expected RUB/USD",
            )

    # Check all dates in period are present
    expected_dates = {period_start + timedelta(days=i) for i in range(7)}
    if dates_seen != expected_dates:
        missing = expected_dates - dates_seen
        return False, f"Missing dates in records: {missing}"

    return True, None


def _is_non_negative_number(value: Union[int, float]) -> bool:
    """Check that value is a number >= 0 and not NaN."""
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
    Validate OHLCV candle records for the LQDT/TQTF 7-day period.

    Checks:
    1. Count matches the expected day span.
    2. Dates are unique and within [start_date, end_date].
    3. Prices/volume are non-negative numbers when present.
    4. Instrument and board match expected values.
    5. All dates in the period are present.

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
