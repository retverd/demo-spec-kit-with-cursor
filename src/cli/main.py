"""CLI-точка входа для извлечения данных (CBR, MOEX)."""

import argparse
import logging
import sys
from datetime import date


from src.services.cbr_client import CBRClient, CBRClientError
from src.services.moex_client import MoexClient, MoexClientError
from src.services.parquet_writer import ParquetWriter
from src.services.xlsx_writer import XLSXWriter
from src.utils.date_utils import calculate_period
from src.utils.validators import validate_candles, validate_days, validate_records


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


def _configure_stdio_encoding() -> None:
    """Стараться писать UTF-8 в stdout/stderr, чтобы русские сообщения не портились в пайпах/логах."""
    for stream in (sys.stdout, sys.stderr):
        try:
            reconfigure = getattr(stream, "reconfigure", None)
            if callable(reconfigure):
                reconfigure(encoding="utf-8")
        except Exception:
            # Лучшее усилие: не ломаем CLI из-за проблем с потоками.
            continue


def _build_parser() -> argparse.ArgumentParser:
    # Общий парсер, чтобы опция --days работала и до, и после подкоманды.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--days",
        "-d",
        metavar="DAYS",
        help="Длительность периода в днях (обязательно, целое 1–365)",
    )

    parser = argparse.ArgumentParser(
        description="CLI для извлечения финансовых данных (CBR, MOEX). Параметр --days обязателен.",
        parents=[common],
    )
    subparsers = parser.add_subparsers(dest="command")

    # CBR command (default for backward compatibility)
    subparsers.add_parser(
        "cbr",
        parents=[common],
        help="Получить курс RUB/USD за указанный период и сохранить в Parquet",
    )

    # MOEX candles command
    subparsers.add_parser(
        "moex-lqdt",
        parents=[common],
        help="Получить дневные свечи LQDT/TQTF за указанный период и сохранить в XLSX",
    )

    return parser


def _fail_validation(message: str) -> int:
    """Единый вывод ошибок валидации с кодом EXIT_VALIDATION_ERROR."""
    logger.error(message)
    print(f"Error: {message}", file=sys.stderr)
    return EXIT_VALIDATION_ERROR


def _fail(message: str, exit_code: int, *, exc_info: bool = False) -> int:
    """Единый вывод ошибок (stderr + лог) с заданным кодом выхода."""
    logger.error(message, exc_info=exc_info)
    print(f"Error: {message}", file=sys.stderr)
    return exit_code


def _classify_cbr_error(error: Exception) -> int:
    msg = str(error).lower()
    # Поддерживаем и русские, и английские маркеры, чтобы не зависеть от формулировок.
    if "таймаут" in msg or "timeout" in msg:
        return EXIT_NETWORK_ERROR
    if "сете" in msg or "connection" in msg or "network" in msg:
        return EXIT_NETWORK_ERROR
    if "xml" in msg or "данн" in msg or "invalid" in msg or "malformed" in msg:
        return EXIT_INVALID_DATA
    return EXIT_API_ERROR


def _run_cbr(days: int) -> int:
    """Сценарий CBR с обязательным параметром days."""
    start_date, end_date = calculate_period(days)

    logger.info(
        "Извлечение курса за период: %s to %s (days=%s)",
        start_date,
        end_date,
        days,
    )

    try:
        cbr_client = CBRClient()
        records = cbr_client.get_exchange_rates(start_date, end_date)
    except CBRClientError as e:
        # Важно: ошибка должна быть видна пользователю в stderr.
        print(f"Error: {e}", file=sys.stderr)
        return _classify_cbr_error(e)

    logger.info("Валидация полученных данных за %s дней", days)
    is_valid, error_msg = validate_records(
        records, start_date, end_date, expected_days=days
    )
    if not is_valid:
        return _fail_validation(f"Валидация данных не пройдена: {error_msg}")

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
        logger.info(
            "Успешно создан Parquet файл: %s (period %s — %s)",
            filename,
            start_date,
            end_date,
        )
        print(f"Успешно создан {filename}")
        return EXIT_SUCCESS
    except IOError as e:
        return _fail(f"Ошибка файловой системы: {e}", EXIT_FILE_SYSTEM_ERROR)
    except ValueError as e:
        return _fail(f"Некорректные метаданные: {e}", EXIT_INVALID_DATA)
    except Exception as e:
        return _fail(f"Неожиданная ошибка: {e}", EXIT_FILE_SYSTEM_ERROR, exc_info=True)


def _classify_moex_error(error: Exception) -> int:
    error_str = str(error).lower()
    logger.debug("Классификация ошибки MOEX: %s", error_str)
    if "таймаут" in error_str or "сетевая" in error_str:
        return EXIT_NETWORK_ERROR
    if "http" in error_str or "api" in error_str:
        return EXIT_API_ERROR
    if "некоррект" in error_str or "данн" in error_str:
        return EXIT_INVALID_DATA
    return EXIT_API_ERROR


def _run_moex_lqdt(days: int) -> int:
    start_date, end_date = calculate_period(days)

    logger.info(
        "Запуск режима moex-lqdt для периода %s - %s (days=%s)",
        start_date,
        end_date,
        days,
    )

    try:
        client = MoexClient()
        records = client.get_daily_candles(start_date, end_date)
    except MoexClientError as e:
        # Выводим причину в stderr, затем классифицируем код выхода
        print(f"Error: {e}", file=sys.stderr)
        return _classify_moex_error(e)

    logger.info("Проверка данных свечей за %s дней", days)
    is_valid, error_msg = validate_candles(records, start_date, end_date)
    if not is_valid:
        return _fail_validation(f"Проверка данных свечей не пройдена: {error_msg}")

    try:
        writer = XLSXWriter()
        filename = writer.write_candles(
            records,
            output_dir=".",
            period_start=start_date,
            period_end=end_date,
            report_date=date.today(),
        )
        logger.info(
            "Успешно создан XLSX-файл: %s (period %s — %s)",
            filename,
            start_date,
            end_date,
        )
        print(f"Успешно создан файл: {filename}")
        return EXIT_SUCCESS
    except IOError as e:
        return _fail(f"Ошибка файловой системы: {e}", EXIT_FILE_SYSTEM_ERROR)
    except ValueError as e:
        return _fail(f"Ошибка данных: {e}", EXIT_INVALID_DATA)
    except Exception as e:
        return _fail(
            f"Неожиданная ошибка записи XLSX: {e}",
            EXIT_FILE_SYSTEM_ERROR,
            exc_info=True,
        )


def main(argv: list[str] | None = None) -> int:
    """
    Главная точка входа CLI.

    Поддерживает:
    - cbr (по умолчанию): RUB/USD за --days дней → Parquet
    - moex-lqdt: свечи LQDT/TQTF за --days дней → XLSX
    """
    _configure_stdio_encoding()
    parser = _build_parser()

    # Если argv не передан, используем sys.argv[1:], но игнорируем pytest-пути.
    if argv is None:
        argv = sys.argv[1:]
        if argv and (
            "pytest" in argv[0] or "tests" in argv[0] or argv[0].endswith(".py")
        ):
            argv = []

    args = parser.parse_args(argv)
    command = args.command or "cbr"

    is_valid_days, days_error = validate_days(args.days)
    if not is_valid_days:
        return _fail_validation(days_error or "Некорректный параметр --days")

    days_value = int(args.days)  # validate_days гарантирует корректность

    try:
        if command == "moex-lqdt":
            return _run_moex_lqdt(days_value)
        if command == "cbr":
            return _run_cbr(days_value)

        parser.print_help()
        return EXIT_INVALID_DATA
    except KeyboardInterrupt:
        logger.info("Прервано пользователем")
        print("\nПрервано пользователем", file=sys.stderr)
        return EXIT_API_ERROR
    except Exception as e:
        return _fail(f"Неожиданная ошибка: {e}", EXIT_API_ERROR, exc_info=True)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
