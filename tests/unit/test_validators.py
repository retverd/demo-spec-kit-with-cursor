"""Unit tests for validators module."""

from datetime import date, timedelta

from src.models.candles import CandleRecord
from src.models.exchange_rate import ExchangeRateRecord
from src.utils.validators import (
    validate_candles,
    validate_date,
    validate_rate,
    validate_records,
)


class TestValidateDate:
    """Tests for validate_date function."""

    def test_valid_date_within_period(self):
        """Test that a date within the period is valid."""
        period_start = date(2025, 11, 25)
        period_end = date(2025, 12, 1)
        test_date = date(2025, 11, 28)

        assert validate_date(test_date, period_start, period_end) is True

    def test_valid_date_at_period_start(self):
        """Test that a date at period start is valid."""
        period_start = date(2025, 11, 25)
        period_end = date(2025, 12, 1)

        assert validate_date(period_start, period_start, period_end) is True

    def test_valid_date_at_period_end(self):
        """Test that a date at period end is valid."""
        period_start = date(2025, 11, 25)
        period_end = date(2025, 12, 1)

        assert validate_date(period_end, period_start, period_end) is True

    def test_invalid_date_before_period(self):
        """Test that a date before the period is invalid."""
        period_start = date(2025, 11, 25)
        period_end = date(2025, 12, 1)
        test_date = date(2025, 11, 24)

        assert validate_date(test_date, period_start, period_end) is False

    def test_invalid_date_after_period(self):
        """Test that a date after the period is invalid."""
        period_start = date(2025, 11, 25)
        period_end = date(2025, 12, 1)
        test_date = date(2025, 12, 2)

        assert validate_date(test_date, period_start, period_end) is False


class TestValidateRate:
    """Tests for validate_rate function."""

    def test_valid_positive_rate(self):
        """Test that a positive rate is valid."""
        assert validate_rate(78.50) is True
        assert validate_rate(100.0) is True
        assert validate_rate(0.01) is True

    def test_valid_null_rate(self):
        """Test that None (missing data) is valid."""
        assert validate_rate(None) is True

    def test_invalid_zero_rate(self):
        """Test that zero rate is invalid."""
        assert validate_rate(0.0) is False

    def test_invalid_negative_rate(self):
        """Test that negative rate is invalid."""
        assert validate_rate(-10.0) is False

    def test_invalid_string_rate(self):
        """Test that non-numeric rate is invalid."""
        assert validate_rate("78.50") is False
        assert validate_rate("invalid") is False


class TestValidateRecords:
    """Tests for validate_records function."""

    def test_valid_complete_records(self):
        """Test that 7 valid records for the period pass validation."""
        period_start = date(2025, 11, 25)
        period_end = date(2025, 12, 1)

        records = [
            ExchangeRateRecord(
                date=period_start + timedelta(days=i),
                exchange_rate_value=78.50 + i * 0.05 if i % 2 == 0 else None,
                currency_pair="RUB/USD",
            )
            for i in range(7)
        ]

        is_valid, error = validate_records(records, period_start, period_end)
        assert is_valid is True
        assert error is None

    def test_invalid_too_few_records(self):
        """Test that fewer than 7 records fails validation."""
        period_start = date(2025, 11, 25)
        period_end = date(2025, 12, 1)

        records = [
            ExchangeRateRecord(
                date=period_start + timedelta(days=i),
                exchange_rate_value=78.50,
                currency_pair="RUB/USD",
            )
            for i in range(5)  # Only 5 records
        ]

        is_valid, error = validate_records(records, period_start, period_end)
        assert is_valid is False
        assert "Expected 7 records" in error


class TestValidateCandles:
    """Tests for validate_candles function."""

    def test_valid_candles(self):
        """Valid 7-day candle set passes validation."""
        start_date = date(2025, 11, 25)
        end_date = date(2025, 12, 1)
        records = [
            CandleRecord(
                date=start_date + timedelta(days=i),
                open=100.0 + i,
                high=101.0 + i,
                low=99.0 + i,
                close=100.5 + i,
                volume=1000 + i,
            )
            for i in range(7)
        ]

        is_valid, error = validate_candles(records, start_date, end_date)
        assert is_valid is True
        assert error is None

    def test_missing_date(self):
        """Fail when a date from the period is missing."""
        start_date = date(2025, 11, 25)
        end_date = date(2025, 12, 1)
        records = [
            CandleRecord(
                date=start_date + timedelta(days=i),
                open=None,
                high=None,
                low=None,
                close=None,
                volume=None,
            )
            for i in range(6)
        ]

        is_valid, error = validate_candles(records, start_date, end_date)
        assert is_valid is False
        assert "Expected 7 records" in error

    def test_negative_value(self):
        """Negative prices or volume should fail validation."""
        start_date = date(2025, 11, 25)
        end_date = date(2025, 12, 1)
        records = [
            CandleRecord(
                date=start_date + timedelta(days=i),
                open=-1.0 if i == 0 else 1.0,
                high=2.0,
                low=0.5,
                close=1.5,
                volume=100.0,
            )
            for i in range(7)
        ]

        is_valid, error = validate_candles(records, start_date, end_date)
        assert is_valid is False
        assert "Invalid open value" in error

    def test_wrong_board_or_instrument(self):
        """Unexpected instrument/board should fail."""
        start_date = date(2025, 11, 25)
        end_date = date(2025, 12, 1)
        records = [
            CandleRecord(
                date=start_date + timedelta(days=i),
                open=1.0,
                high=2.0,
                low=0.5,
                close=1.5,
                volume=100.0,
                instrument="WRONG" if i == 0 else "LQDT",
                board="TQBR" if i == 1 else "TQTF",
            )
            for i in range(7)
        ]

        is_valid, error = validate_candles(records, start_date, end_date)
        assert is_valid is False
        assert "Invalid instrument" in error or "Invalid board" in error

    def test_duplicate_date(self):
        """Duplicate date should be rejected."""
        start_date = date(2025, 11, 25)
        end_date = date(2025, 12, 1)
        records = [
            CandleRecord(
                date=start_date,
                open=1.0,
                high=2.0,
                low=0.5,
                close=1.5,
                volume=100.0,
            )
        ] + [
            CandleRecord(
                date=start_date + timedelta(days=i),
                open=1.0,
                high=2.0,
                low=0.5,
                close=1.5,
                volume=100.0,
            )
            for i in range(1, 7)
        ]
        # introduce duplicate of start_date
        records[1] = CandleRecord(
            date=start_date,
            open=1.0,
            high=2.0,
            low=0.5,
            close=1.5,
            volume=100.0,
        )

        is_valid, error = validate_candles(records, start_date, end_date)
        assert is_valid is False
        assert "Duplicate date" in error

    def test_invalid_too_many_records(self):
        """Test that more than 7 records fails validation."""
        period_start = date(2025, 11, 25)
        period_end = date(2025, 12, 1)

        records = [
            ExchangeRateRecord(
                date=period_start + timedelta(days=i),
                exchange_rate_value=78.50,
                currency_pair="RUB/USD",
            )
            for i in range(8)  # 8 records
        ]

        is_valid, error = validate_records(records, period_start, period_end)
        assert is_valid is False
        assert "Expected 7 records" in error

    def test_invalid_duplicate_dates(self):
        """Test that duplicate dates fail validation."""
        period_start = date(2025, 11, 25)
        period_end = date(2025, 12, 1)

        records = [
            ExchangeRateRecord(
                date=period_start, exchange_rate_value=78.50, currency_pair="RUB/USD"
            )
        ] * 7  # All same date

        is_valid, error = validate_records(records, period_start, period_end)
        assert is_valid is False
        assert "Duplicate date" in error

    def test_invalid_date_outside_period(self):
        """Test that dates outside period fail validation."""
        period_start = date(2025, 11, 25)
        period_end = date(2025, 12, 1)

        records = [
            ExchangeRateRecord(
                date=period_start + timedelta(days=i) if i < 6 else date(2025, 12, 10),
                exchange_rate_value=78.50,
                currency_pair="RUB/USD",
            )
            for i in range(7)
        ]

        is_valid, error = validate_records(records, period_start, period_end)
        assert is_valid is False
        assert "outside the expected period" in error

    def test_invalid_negative_rate(self):
        """Test that negative rates fail validation."""
        period_start = date(2025, 11, 25)
        period_end = date(2025, 12, 1)

        records = [
            ExchangeRateRecord(
                date=period_start + timedelta(days=i),
                exchange_rate_value=-10.0 if i == 0 else 78.50,
                currency_pair="RUB/USD",
            )
            for i in range(7)
        ]

        is_valid, error = validate_records(records, period_start, period_end)
        assert is_valid is False
        assert "Invalid exchange rate value" in error

    def test_invalid_currency_pair(self):
        """Test that wrong currency pair fails validation."""
        period_start = date(2025, 11, 25)
        period_end = date(2025, 12, 1)

        records = [
            ExchangeRateRecord(
                date=period_start + timedelta(days=i),
                exchange_rate_value=78.50,
                currency_pair="EUR/USD" if i == 0 else "RUB/USD",
            )
            for i in range(7)
        ]

        is_valid, error = validate_records(records, period_start, period_end)
        assert is_valid is False
        assert "Invalid currency pair" in error

    def test_invalid_missing_dates(self):
        """Test that missing dates in period fail validation."""
        period_start = date(2025, 11, 25)
        period_end = date(2025, 12, 1)

        # Create 6 records (missing one date) - this will fail the count check first
        # which is the correct behavior: fewer records means missing dates
        records = [
            ExchangeRateRecord(
                date=period_start + timedelta(days=i),
                exchange_rate_value=78.50,
                currency_pair="RUB/USD",
            )
            for i in range(6)  # Only 6 dates, missing one
        ]

        is_valid, error = validate_records(records, period_start, period_end)
        assert is_valid is False
        # With fewer than 7 records, validation fails at count check
        assert "Expected 7 records" in error
