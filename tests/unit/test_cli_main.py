"""Юнит-тесты CLI для обязательного параметра --days."""

from datetime import date, timedelta
from typing import List

from src.cli import main as cli
from src.models.candles import CandleRecord
from src.models.exchange_rate import ExchangeRateRecord


def test_main_requires_days_argument(monkeypatch):
    """Отсутствие --days приводит к коду выхода 5 без вызова клиентов."""
    called = {"cbr": False, "moex": False}

    class StubCBR:
        def __init__(self):
            called["cbr"] = True

    class StubMoex:
        def __init__(self):
            called["moex"] = True

    monkeypatch.setattr(cli, "CBRClient", StubCBR)
    monkeypatch.setattr(cli, "MoexClient", StubMoex)

    exit_code = cli.main([])

    assert exit_code == cli.EXIT_VALIDATION_ERROR
    assert called["cbr"] is False
    assert called["moex"] is False


def test_main_rejects_invalid_days_value():
    """Некорректный диапазон days возвращает код 5."""
    exit_code = cli.main(["cbr", "--days", "0"])
    assert exit_code == cli.EXIT_VALIDATION_ERROR


def test_main_rejects_non_integer_days():
    """Нечисловое значение days возвращает код 5."""
    exit_code = cli.main(["cbr", "--days", "abc"])
    assert exit_code == cli.EXIT_VALIDATION_ERROR


def test_cbr_command_uses_days_and_passes_period(monkeypatch, tmp_path):
    """CLI передаёт период из calculate_period в клиента и писатель."""
    days_value = 3
    start = date(2025, 12, 1)
    end = date(2025, 12, 3)

    monkeypatch.setattr(cli, "calculate_period", lambda _: (start, end))

    captured_args = {}

    class StubCBR:
        def get_exchange_rates(
            self, start_date: date, end_date: date
        ) -> List[ExchangeRateRecord]:
            captured_args["start_date"] = start_date
            captured_args["end_date"] = end_date
            return [
                ExchangeRateRecord(
                    date=start_date + timedelta(days=i),
                    exchange_rate_value=80.0 + i,
                )
                for i in range(days_value)
            ]

    class StubParquetWriter:
        def write_exchange_rates(self, records, metadata, output_dir="."):
            captured_args["records_len"] = len(records)
            captured_args["metadata"] = metadata
            return tmp_path / "out.parquet"

    monkeypatch.setattr(cli, "CBRClient", StubCBR)
    monkeypatch.setattr(cli, "ParquetWriter", StubParquetWriter)
    monkeypatch.setattr(
        cli,
        "validate_records",
        lambda records, ps, pe, expected_days=None: (True, None),
    )

    exit_code = cli.main(["cbr", "--days", str(days_value)])

    assert exit_code == cli.EXIT_SUCCESS
    assert captured_args["start_date"] == start
    assert captured_args["end_date"] == end
    assert captured_args["records_len"] == days_value
    assert captured_args["metadata"]["period_start"] == start.isoformat()
    assert captured_args["metadata"]["period_end"] == end.isoformat()


def test_moex_command_uses_days(monkeypatch, tmp_path):
    """moex-lqdt CLI использует period_start/period_end и пишет XLSX."""
    days_value = 2
    start = date(2025, 12, 10)
    end = date(2025, 12, 11)

    monkeypatch.setattr(cli, "calculate_period", lambda _: (start, end))

    captured_args = {}

    class StubMoex:
        def get_daily_candles(self, start_date: date, end_date: date):
            captured_args["start_date"] = start_date
            captured_args["end_date"] = end_date
            return [
                CandleRecord(
                    date=start_date, open=1, high=2, low=0.5, close=1.5, volume=10
                ),
                CandleRecord(
                    date=end_date, open=1, high=2, low=0.5, close=1.5, volume=10
                ),
            ]

    class StubXlsxWriter:
        def write_candles(
            self,
            records,
            output_dir=".",
            period_start=None,
            period_end=None,
            report_date=None,
        ):
            captured_args["records_len"] = len(records)
            captured_args["period_start"] = period_start
            captured_args["period_end"] = period_end
            return tmp_path / "out.xlsx"

    monkeypatch.setattr(cli, "MoexClient", StubMoex)
    monkeypatch.setattr(cli, "XLSXWriter", StubXlsxWriter)
    monkeypatch.setattr(cli, "validate_candles", lambda records, ps, pe: (True, None))

    exit_code = cli.main(["moex-lqdt", "--days", str(days_value)])

    assert exit_code == cli.EXIT_SUCCESS
    assert captured_args["start_date"] == start
    assert captured_args["end_date"] == end
    assert captured_args["records_len"] == days_value
    assert captured_args["period_start"] == start
    assert captured_args["period_end"] == end


def test_cbr_accepts_upper_boundary_days(monkeypatch, tmp_path):
    """Граничное значение 365 дней принимается и не падает по валидации."""
    days_value = 365
    start = date(2024, 1, 1)
    end = date(2024, 12, 31)

    monkeypatch.setattr(cli, "calculate_period", lambda _: (start, end))

    class StubCBR:
        def get_exchange_rates(self, start_date: date, end_date: date):
            base_records = [
                ExchangeRateRecord(date=start_date, exchange_rate_value=80.0),
                ExchangeRateRecord(date=end_date, exchange_rate_value=81.0),
            ]
            filler = [
                ExchangeRateRecord(
                    date=start_date + timedelta(days=i), exchange_rate_value=None
                )
                for i in range(1, days_value - 1)
            ]
            return base_records + filler

    class StubParquetWriter:
        def write_exchange_rates(self, records, metadata, output_dir="."):
            return tmp_path / "out.parquet"

    monkeypatch.setattr(cli, "CBRClient", StubCBR)
    monkeypatch.setattr(cli, "ParquetWriter", StubParquetWriter)
    monkeypatch.setattr(
        cli,
        "validate_records",
        lambda records, ps, pe, expected_days=None: (True, None),
    )

    exit_code = cli.main(["cbr", "--days", str(days_value)])

    assert exit_code == cli.EXIT_SUCCESS
