"""Parquet file writer with metadata support."""

import os
from datetime import datetime
from typing import Dict, List

import pyarrow as pa
import pyarrow.parquet as pq

from src.models.exchange_rate import ExchangeRateRecord


class ParquetWriter:
    """
    Writer for creating Parquet files with exchange rate data and metadata.

    The writer creates Parquet files with:
    - Data rows: Exchange rate records (date, exchange_rate_value, currency_pair)
    - File metadata: report_date, period_start, period_end, data_source
    """

    def write_exchange_rates(
        self,
        records: List[ExchangeRateRecord],
        metadata: Dict[str, str],
        output_dir: str = ".",
    ) -> str:
        """
        Write exchange rate records to a Parquet file with metadata.

        Args:
            records: List of ExchangeRateRecord objects to write
            metadata: Dictionary with metadata keys:
                - report_date: Date when extraction was performed (ISO format)
                - period_start: Start date of the data period (ISO format)
                - period_end: End date of the data period (ISO format)
                - data_source: Source identifier (e.g., "CBR")
            output_dir: Directory where the file should be saved (default: current directory)

        Returns:
            Full path to the created Parquet file

        Raises:
            ValueError: If metadata is missing required keys
            IOError: If file cannot be written (permissions, disk full, etc.)
        """
        # Validate metadata
        required_keys = ["report_date", "period_start", "period_end", "data_source"]
        missing_keys = [key for key in required_keys if key not in metadata]
        if missing_keys:
            raise ValueError(f"Missing required metadata keys: {missing_keys}")

        # Generate filename
        filename = self._generate_filename(metadata, output_dir)

        # Create PyArrow schema
        schema = pa.schema(
            [
                pa.field("date", pa.date32()),
                pa.field("exchange_rate_value", pa.float64(), nullable=True),
                pa.field("currency_pair", pa.string()),
            ]
        )

        # Prepare metadata as KeyValueMetadata (PyArrow stores metadata as bytes)
        parquet_metadata = pa.KeyValueMetadata(
            {k.encode("utf-8"): v.encode("utf-8") for k, v in metadata.items()}
        )

        # Add metadata to schema
        schema = schema.with_metadata(parquet_metadata)

        # Convert records to PyArrow arrays
        dates = [r.date for r in records]
        rates = [r.exchange_rate_value for r in records]
        currency_pairs = [r.currency_pair for r in records]

        # Create arrays
        date_array = pa.array(dates, type=pa.date32())
        rate_array = pa.array(rates, type=pa.float64())
        currency_pair_array = pa.array(currency_pairs, type=pa.string())

        # Create table
        table = pa.Table.from_arrays(
            [date_array, rate_array, currency_pair_array], schema=schema
        )

        # Write Parquet file with metadata using ParquetWriter
        try:
            with pq.ParquetWriter(filename, schema) as writer:
                writer.write_table(table)
        except Exception as e:
            raise IOError(f"Failed to write Parquet file: {e}") from e

        return filename

    def _generate_filename(self, metadata: Dict[str, str], output_dir: str) -> str:
        """
        Generate filename with pattern: rub_usd_{period_start}_to_{period_end}_{report_date}_{timestamp}.parquet

        Args:
            metadata: Metadata dictionary containing period_start, period_end, report_date
            output_dir: Directory where file should be saved

        Returns:
            Full path to the file
        """
        period_start = metadata["period_start"]
        period_end = metadata["period_end"]
        report_date = metadata["report_date"]

        # Generate timestamp (HHMMSS format)
        timestamp = datetime.now().strftime("%H%M%S")

        # Construct filename
        filename = (
            f"rub_usd_{period_start}_to_{period_end}_{report_date}_{timestamp}.parquet"
        )

        return os.path.join(output_dir, filename)
