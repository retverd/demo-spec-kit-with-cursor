"""Запись данных обменного курса в Parquet с метаданными."""

import os
from datetime import datetime
from typing import Dict, List

import pyarrow as pa
import pyarrow.parquet as pq

from src.models.exchange_rate import ExchangeRateRecord


class ParquetWriter:
    """
    Писатель данных курса RUB/USD в Parquet с метаданными.

    Создаёт файлы с:
    - строками данных: дата, значение курса, валютная пара
    - метаданными файла: report_date, period_start, period_end, data_source
    """

    def write_exchange_rates(
        self,
        records: List[ExchangeRateRecord],
        metadata: Dict[str, str],
        output_dir: str = ".",
    ) -> str:
        """
        Записать курсы в Parquet с метаданными.

        Args:
            records: Список ExchangeRateRecord для записи.
            metadata: Словарь с ключами:
                - report_date: дата выгрузки (ISO)
                - period_start: начало периода (ISO)
                - period_end: конец периода (ISO)
                - data_source: источник (например, "CBR")
            output_dir: каталог для сохранения (по умолчанию текущий).

        Returns:
            Полный путь к созданному файлу.

        Raises:
            ValueError: если отсутствуют обязательные ключи.
            IOError: при ошибке записи файла.
        """
        # Проверка метаданных
        required_keys = ["report_date", "period_start", "period_end", "data_source"]
        missing_keys = [key for key in required_keys if key not in metadata]
        if missing_keys:
            raise ValueError(f"Missing required metadata keys: {missing_keys}")

        # Сгенерировать имя файла
        filename = self._generate_filename(metadata, output_dir)

        # Создать схему PyArrow
        schema = pa.schema(
            [
                pa.field("date", pa.date32()),
                pa.field("exchange_rate_value", pa.float64(), nullable=True),
                pa.field("currency_pair", pa.string()),
            ]
        )

        # Подготовить метаданные как KeyValueMetadata (PyArrow хранит байты)
        parquet_metadata = pa.KeyValueMetadata(
            {k.encode("utf-8"): v.encode("utf-8") for k, v in metadata.items()}
        )

        # Добавить метаданные в схему
        schema = schema.with_metadata(parquet_metadata)

        # Конвертировать записи в массивы PyArrow
        dates = [r.date for r in records]
        rates = [r.exchange_rate_value for r in records]
        currency_pairs = [r.currency_pair for r in records]

        # Создать массивы
        date_array = pa.array(dates, type=pa.date32())
        rate_array = pa.array(rates, type=pa.float64())
        currency_pair_array = pa.array(currency_pairs, type=pa.string())

        # Сформировать таблицу
        table = pa.Table.from_arrays(
            [date_array, rate_array, currency_pair_array], schema=schema
        )

        # Записать файл Parquet с метаданными
        try:
            with pq.ParquetWriter(filename, schema) as writer:
                writer.write_table(table)
        except Exception as e:
            raise IOError(f"Failed to write Parquet file: {e}") from e

        return filename

    def _generate_filename(self, metadata: Dict[str, str], output_dir: str) -> str:
        """
        Сгенерировать имя по шаблону:
        rub_usd_{period_start}_to_{period_end}_{report_date}_{timestamp}.parquet

        Args:
            metadata: словарь с period_start, period_end, report_date
            output_dir: каталог для сохранения

        Returns:
            Полный путь к файлу.
        """
        period_start = metadata["period_start"]
        period_end = metadata["period_end"]
        report_date = metadata["report_date"]

        # Сгенерировать метку времени (HHMMSS)
        timestamp = datetime.now().strftime("%H%M%S")

        # Собрать имя файла
        filename = (
            f"rub_usd_{period_start}_to_{period_end}_{report_date}_{timestamp}.parquet"
        )

        return os.path.join(output_dir, filename)
