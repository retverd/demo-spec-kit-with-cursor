"""CLI-точка входа для извлечения данных (CBR, MOEX)."""

import argparse
import logging
import sys
from datetime import date


from src.services.cbr_client import CBRClient, CBRClientError
from src.services.moex_client import MoexClient, MoexClientError
from src.services.parquet_writer import ParquetWriter
from src.services.xlsx_writer import XLSXWriter
from src.utils.date_utils import get_last_7_days
from src.utils.validators import validate_candles, validate_records

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Коды выхода (контракты CLI)
EXIT_SUCCESS = 0
EXIT_API_ERROR = 1
EXIT_NETWORK_ERROR = 2
EXIT_INVALID_DATA = 3
EXIT_FILE_SYSTEM_ERROR = 4
EXIT_VALIDATION_ERROR = 5

# Алиасы для обратной совместимости с существующими тестами
EXIT_CBR_API_ERROR = EXIT_API_ERROR


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="CLI для извлечения финансовых данных (CBR, MOEX)"
    )
    subparsers = parser.add_subparsers(dest="command")

    # CBR command (default for backward compatibility)
    subparsers.add_parser(
        "cbr",
        help="Получить курс RUB/USD за последние 7 дней и сохранить в Parquet",
    )

    # MOEX candles command
    subparsers.add_parser(
        "moex-lqdt",
        help="Получить дневные свечи LQDT/TQTF за последние 7 дней и сохранить в XLSX",
    )

    return parser


def _run_cbr() -> int:
    """Текущий сценарий CBR (без изменений)."""
    dates = get_last_7_days()
    start_date = dates[0]
    end_date = dates[-1]

    logger.info(f"Извлечение курса за период: {start_date} to {end_date}")

    try:
        cbr_client = CBRClient()
        records = cbr_client.get_exchange_rates(start_date, end_date)
    except CBRClientError as e:
        error_str = str(e).lower()
        if (
            "timeout" in error_str
            or "connection" in error_str
            or "network" in error_str
        ):
            return EXIT_NETWORK_ERROR
        elif "invalid" in error_str or "malformed" in error_str:
            return EXIT_INVALID_DATA
        else:
            return EXIT_API_ERROR

    logger.info("Валидация полученных данных")
    is_valid, error_msg = validate_records(records, start_date, end_date)
    if not is_valid:
        error_message = f"Валидация данных не пройдена: {error_msg}"
        logger.error(error_message)
        print(f"Error: {error_message}", file=sys.stderr)
        return EXIT_VALIDATION_ERROR

    report_date = date.today().isoformat()
    metadata = {
        "report_date": report_date,
        "period_start": start_date.isoformat(),
        "period_end": end_date.isoformat(),
        "data_source": "CBR",
    }

    try:
        writer = ParquetWriter()
        filename = writer.write_exchange_rates(records, metadata, output_dir=".")
        logger.info(f"Успешно создан Parquet файл: {filename}")
        print(f"Успешно создан {filename}")
        return EXIT_SUCCESS
    except IOError as e:
        error_message = f"Ошибка файловой системы: {e}"
        logger.error(error_message)
        print(f"Error: {error_message}", file=sys.stderr)
        return EXIT_FILE_SYSTEM_ERROR
    except ValueError as e:
        error_message = f"Некорректные метаданные: {e}"
        logger.error(error_message)
        print(f"Error: {error_message}", file=sys.stderr)
        return EXIT_INVALID_DATA
    except Exception as e:
        error_message = f"Неожиданная ошибка: {e}"
        logger.error(error_message, exc_info=True)
        print(f"Error: {error_message}", file=sys.stderr)
        return EXIT_FILE_SYSTEM_ERROR


def _classify_moex_error(error: Exception) -> int:
    error_str = str(error).lower()
    if "таймаут" in error_str or "сетевая" in error_str:
        return EXIT_NETWORK_ERROR
    if "http" in error_str or "api" in error_str:
        return EXIT_API_ERROR
    if "некоррект" in error_str or "данн" in error_str:
        return EXIT_INVALID_DATA
    return EXIT_API_ERROR


def _run_moex_lqdt() -> int:
    dates = get_last_7_days()
    start_date = dates[0]
    end_date = dates[-1]

    logger.info("Запуск режима moex-lqdt для периода %s - %s", start_date, end_date)

    try:
        client = MoexClient()
        records = client.get_daily_candles(start_date, end_date)
    except MoexClientError as e:
        return _classify_moex_error(e)

    logger.info("Проверка данных свечей")
    is_valid, error_msg = validate_candles(records, start_date, end_date)
    if not is_valid:
        error_message = f"Проверка данных свечей не пройдена: {error_msg}"
        logger.error(error_message)
        print(f"Error: {error_message}", file=sys.stderr)
        return EXIT_VALIDATION_ERROR

    try:
        writer = XLSXWriter()
        filename = writer.write_candles(
            records,
            output_dir=".",
            period_start=start_date,
            period_end=end_date,
            report_date=date.today(),
        )
        logger.info("Успешно создан XLSX-файл: %s", filename)
        print(f"Успешно создан файл: {filename}")
        return EXIT_SUCCESS
    except IOError as e:
        error_message = f"Ошибка файловой системы: {e}"
        logger.error(error_message)
        print(f"Error: {error_message}", file=sys.stderr)
        return EXIT_FILE_SYSTEM_ERROR
    except ValueError as e:
        error_message = f"Ошибка данных: {e}"
        logger.error(error_message)
        print(f"Error: {error_message}", file=sys.stderr)
        return EXIT_INVALID_DATA
    except Exception as e:
        error_message = f"Неожиданная ошибка записи XLSX: {e}"
        logger.error(error_message, exc_info=True)
        print(f"Error: {error_message}", file=sys.stderr)
        return EXIT_FILE_SYSTEM_ERROR


def main() -> int:
    """
    Главная точка входа CLI.

    Поддерживает:
    - cbr (по умолчанию): RUB/USD за 7 дней → Parquet
    - moex-lqdt: свечи LQDT/TQTF за 7 дней → XLSX
    """
    parser = _build_parser()
    args = parser.parse_args()
    command = args.command or "cbr"

    try:
        if command == "moex-lqdt":
            return _run_moex_lqdt()
        if command == "cbr":
            return _run_cbr()

        parser.print_help()
        return EXIT_INVALID_DATA
    except KeyboardInterrupt:
        logger.info("Прервано пользователем")
        print("\nПрервано пользователем", file=sys.stderr)
        return EXIT_API_ERROR
    except Exception as e:
        error_message = f"Неожиданная ошибка: {e}"
        logger.error(error_message, exc_info=True)
        print(f"Error: {error_message}", file=sys.stderr)
        return EXIT_API_ERROR


if __name__ == "__main__":
    sys.exit(main())
