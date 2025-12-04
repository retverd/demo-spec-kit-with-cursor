"""Unit tests for Parquet writer."""

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
    """Tests for ParquetWriter.write_exchange_rates method."""
    
    def test_write_exchange_rates_creates_file(self):
        """Test that write_exchange_rates creates a Parquet file."""
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
        """Test that file-level metadata is stored correctly."""
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
            
            # Read metadata from file (use context manager to ensure proper cleanup)
            with pq.ParquetFile(filename) as parquet_file:
                file_metadata = parquet_file.metadata.metadata
                
                assert file_metadata is not None
                assert b"report_date" in file_metadata
                assert b"period_start" in file_metadata
                assert b"period_end" in file_metadata
                assert b"data_source" in file_metadata
                
                # Decode metadata values
                decoded_metadata = {
                    k.decode('utf-8'): v.decode('utf-8')
                    for k, v in file_metadata.items()
                }
                assert decoded_metadata["report_date"] == "2025-12-02"
                assert decoded_metadata["period_start"] == "2025-11-25"
                assert decoded_metadata["period_end"] == "2025-12-01"
                assert decoded_metadata["data_source"] == "CBR"
    
    def test_write_exchange_rates_stores_data_correctly(self):
        """Test that exchange rate data is stored correctly in Parquet file."""
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
            
            # Read data from file
            table = pq.read_table(filename)
            df = table.to_pandas()
            
            assert len(df) == 7
            assert 'date' in df.columns
            assert 'exchange_rate_value' in df.columns
            assert 'currency_pair' in df.columns
            
            # Verify data values
            assert df.iloc[0]['date'] == date(2025, 11, 25)
            assert df.iloc[0]['exchange_rate_value'] == 78.50
            assert df.iloc[-1]['date'] == date(2025, 12, 1)
            assert df.iloc[-1]['exchange_rate_value'] == 78.80
            assert all(df['currency_pair'] == "RUB/USD")


class TestParquetWriterWithNullValues:
    """Tests for Parquet writer with null rate values."""
    
    def test_write_exchange_rates_with_null_values(self):
        """Test that null rate values are handled correctly."""
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
            
            # Read data from file
            table = pq.read_table(filename)
            df = table.to_pandas()
            
            assert len(df) == 7
            # Check that null values are preserved
            assert pd.isna(df.iloc[1]['exchange_rate_value'])
            assert pd.isna(df.iloc[3]['exchange_rate_value'])
            # Check that non-null values are present
            assert df.iloc[0]['exchange_rate_value'] == 78.50
            assert df.iloc[2]['exchange_rate_value'] == 78.50


class TestParquetWriterFilenameGeneration:
    """Tests for Parquet filename generation."""
    
    def test_filename_includes_period_dates(self):
        """Test that filename includes period start and end dates."""
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
        """Test that filename includes timestamp."""
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
            
            # Filename pattern: rub_usd_YYYY-MM-DD_to_YYYY-MM-DD_YYYY-MM-DD_HHMMSS.parquet
            # Should contain report_date and timestamp
            assert "2025-12-02" in basename
            # Should have timestamp pattern (HHMMSS)
            parts = basename.replace('.parquet', '').split('_')
            assert len(parts) >= 5  # rub, usd, start, to, end, date, timestamp
    
    def test_filename_pattern_matches_specification(self):
        """Test that filename matches the specified pattern."""
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
            
            # Pattern: rub_usd_YYYY-MM-DD_to_YYYY-MM-DD_YYYY-MM-DD_HHMMSS.parquet
            assert basename.startswith("rub_usd_")
            assert "_to_" in basename
            assert basename.endswith(".parquet")


class TestParquetWriterMetadataReading:
    """Tests for reading metadata from Parquet files."""
    
    def test_read_metadata_from_file(self):
        """Test that metadata can be read back from the file."""
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
            
            # Read metadata using Parquet API (use context manager to ensure proper cleanup)
            with pq.ParquetFile(filename) as parquet_file:
                file_metadata = parquet_file.metadata.metadata
                
                # Decode metadata
                decoded_metadata = {
                    k.decode('utf-8'): v.decode('utf-8')
                    for k, v in file_metadata.items()
                }
                
                assert decoded_metadata["report_date"] == "2025-12-02"
                assert decoded_metadata["period_start"] == "2025-11-25"
                assert decoded_metadata["period_end"] == "2025-12-01"
                assert decoded_metadata["data_source"] == "CBR"

