"""Юнит-тесты ParquetWriter."""

import os
import tempfile
from datetime import date, datetime, timedelta

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
import pandas as pd

from src.models.exchange_rate import ExchangeRateRecord
from src.services.parquet_writer import ParquetWriter


class TestParquetWriterWriteExchangeRates:
    """Проверка метода ParquetWriter.write_exchange_rates."""
    
    def test_write_exchange_rates_creates_file(self):
        """Создаётся Parquet-файл."""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = ParquetWriter()
            records = [
                ExchangeRateRecord(
                    date=date(2025, 11, 25) + timedelta(days=i),
                    exchange_rate_value=78.50 + i * 0.05,
                    currency_pair="RUB/USD"
                )
                for i in range(7)
            ]
            metadata = {
                "report_date": "2025-12-02",
                "period_start": "2025-11-25",
                "period_end": "2025-12-01",
                "data_source": "CBR"
            }
            
            filename = writer.write_exchange_rates(records, metadata, tmpdir)
            
            assert os.path.exists(filename)
            assert filename.endswith('.parquet')
    
    def test_write_exchange_rates_stores_metadata(self):
        """Метаданные файла сохраняются корректно."""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = ParquetWriter()
            records = [
                ExchangeRateRecord(
                    date=date(2025, 11, 25) + timedelta(days=i),
                    exchange_rate_value=78.50 + i * 0.05,
                    currency_pair="RUB/USD"
                )
                for i in range(7)
            ]
            metadata = {
                "report_date": "2025-12-02",
                "period_start": "2025-11-25",
                "period_end": "2025-12-01",
                "data_source": "CBR"
            }
            
            filename = writer.write_exchange_rates(records, metadata, tmpdir)
            
            # Читаем метаданные из файла (контекст для корректного закрытия)
            with pq.ParquetFile(filename) as parquet_file:
                file_metadata = parquet_file.metadata.metadata
                
                assert file_metadata is not None
                assert b"report_date" in file_metadata
                assert b"period_start" in file_metadata
                assert b"period_end" in file_metadata
                assert b"data_source" in file_metadata
                
                # Декодируем значения метаданных
                decoded_metadata = {
                    k.decode('utf-8'): v.decode('utf-8')
                    for k, v in file_metadata.items()
                }
                assert decoded_metadata["report_date"] == "2025-12-02"
                assert decoded_metadata["period_start"] == "2025-11-25"
                assert decoded_metadata["period_end"] == "2025-12-01"
                assert decoded_metadata["data_source"] == "CBR"
    
    def test_write_exchange_rates_stores_data_correctly(self):
        """Данные курса сохраняются корректно."""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = ParquetWriter()
            records = [
                ExchangeRateRecord(
                    date=date(2025, 11, 25) + timedelta(days=i),
                    exchange_rate_value=78.50 + i * 0.05,
                    currency_pair="RUB/USD"
                )
                for i in range(7)
            ]
            metadata = {
                "report_date": "2025-12-02",
                "period_start": "2025-11-25",
                "period_end": "2025-12-01",
                "data_source": "CBR"
            }
            
            filename = writer.write_exchange_rates(records, metadata, tmpdir)
            
            # Читаем данные из файла
            table = pq.read_table(filename)
            df = table.to_pandas()
            
            assert len(df) == 7
            assert 'date' in df.columns
            assert 'exchange_rate_value' in df.columns
            assert 'currency_pair' in df.columns
            
            # Проверяем значения
            assert df.iloc[0]['date'] == date(2025, 11, 25)
            assert df.iloc[0]['exchange_rate_value'] == 78.50
            assert df.iloc[-1]['date'] == date(2025, 12, 1)
            assert df.iloc[-1]['exchange_rate_value'] == 78.80
            assert all(df['currency_pair'] == "RUB/USD")


class TestParquetWriterWithNullValues:
    """Проверка обработки None значений."""
    
    def test_write_exchange_rates_with_null_values(self):
        """None значения обрабатываются корректно."""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = ParquetWriter()
            records = [
                ExchangeRateRecord(
                    date=date(2025, 11, 25) + timedelta(days=i),
                    exchange_rate_value=78.50 if i % 2 == 0 else None,  # Every other day is null
                    currency_pair="RUB/USD"
                )
                for i in range(7)
            ]
            metadata = {
                "report_date": "2025-12-02",
                "period_start": "2025-11-25",
                "period_end": "2025-12-01",
                "data_source": "CBR"
            }
            
            filename = writer.write_exchange_rates(records, metadata, tmpdir)
            
            # Читаем данные
            table = pq.read_table(filename)
            df = table.to_pandas()
            
            assert len(df) == 7
            # Проверяем, что None сохранены
            assert pd.isna(df.iloc[1]['exchange_rate_value'])
            assert pd.isna(df.iloc[3]['exchange_rate_value'])
            # Проверяем ненулевые значения
            assert df.iloc[0]['exchange_rate_value'] == 78.50
            assert df.iloc[2]['exchange_rate_value'] == 78.50


class TestParquetWriterFilenameGeneration:
    """Проверка генерации имени файла Parquet."""
    
    def test_filename_includes_period_dates(self):
        """Имя содержит даты начала и конца периода."""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = ParquetWriter()
            records = [
                ExchangeRateRecord(
                    date=date(2025, 11, 25) + timedelta(days=i),
                    exchange_rate_value=78.50,
                    currency_pair="RUB/USD"
                )
                for i in range(7)
            ]
            metadata = {
                "report_date": "2025-12-02",
                "period_start": "2025-11-25",
                "period_end": "2025-12-01",
                "data_source": "CBR"
            }
            
            filename = writer.write_exchange_rates(records, metadata, tmpdir)
            basename = os.path.basename(filename)
            
            assert "2025-11-25" in basename
            assert "2025-12-01" in basename
            assert "rub_usd" in basename.lower()
    
    def test_filename_includes_timestamp(self):
        """Имя содержит метку времени."""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = ParquetWriter()
            records = [
                ExchangeRateRecord(
                    date=date(2025, 11, 25) + timedelta(days=i),
                    exchange_rate_value=78.50,
                    currency_pair="RUB/USD"
                )
                for i in range(7)
            ]
            metadata = {
                "report_date": "2025-12-02",
                "period_start": "2025-11-25",
                "period_end": "2025-12-01",
                "data_source": "CBR"
            }
            
            filename = writer.write_exchange_rates(records, metadata, tmpdir)
            basename = os.path.basename(filename)
            
            # Шаблон: rub_usd_YYYY-MM-DD_to_YYYY-MM-DD_YYYY-MM-DD_HHMMSS.parquet
            # Должен содержать report_date и timestamp
            assert "2025-12-02" in basename
            # Should have timestamp pattern (HHMMSS)
            parts = basename.replace('.parquet', '').split('_')
            assert len(parts) >= 5  # rub, usd, start, to, end, date, timestamp
    
    def test_filename_pattern_matches_specification(self):
        """Имя соответствует ожидаемому шаблону."""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = ParquetWriter()
            records = [
                ExchangeRateRecord(
                    date=date(2025, 11, 25) + timedelta(days=i),
                    exchange_rate_value=78.50,
                    currency_pair="RUB/USD"
                )
                for i in range(7)
            ]
            metadata = {
                "report_date": "2025-12-02",
                "period_start": "2025-11-25",
                "period_end": "2025-12-01",
                "data_source": "CBR"
            }
            
            filename = writer.write_exchange_rates(records, metadata, tmpdir)
            basename = os.path.basename(filename)
            
            # Шаблон: rub_usd_YYYY-MM-DD_to_YYYY-MM-DD_YYYY-MM-DD_HHMMSS.parquet
            assert basename.startswith("rub_usd_")
            assert "_to_" in basename
            assert basename.endswith(".parquet")


class TestParquetWriterMetadataReading:
    """Чтение метаданных из файлов Parquet."""
    
    def test_read_metadata_from_file(self):
        """Метаданные читаются из файла."""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = ParquetWriter()
            records = [
                ExchangeRateRecord(
                    date=date(2025, 11, 25) + timedelta(days=i),
                    exchange_rate_value=78.50 + i * 0.05,
                    currency_pair="RUB/USD"
                )
                for i in range(7)
            ]
            metadata = {
                "report_date": "2025-12-02",
                "period_start": "2025-11-25",
                "period_end": "2025-12-01",
                "data_source": "CBR"
            }
            
            filename = writer.write_exchange_rates(records, metadata, tmpdir)
            
            # Читаем метаданные через Parquet API (контекст для корректного закрытия)
            with pq.ParquetFile(filename) as parquet_file:
                file_metadata = parquet_file.metadata.metadata
                
                # Декодируем метаданные
                decoded_metadata = {
                    k.decode('utf-8'): v.decode('utf-8')
                    for k, v in file_metadata.items()
                }
                
                assert decoded_metadata["report_date"] == "2025-12-02"
                assert decoded_metadata["period_start"] == "2025-11-25"
                assert decoded_metadata["period_end"] == "2025-12-01"
                assert decoded_metadata["data_source"] == "CBR"

