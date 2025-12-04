"""CLI entry point for exchange rate extraction."""

import argparse
import logging
import sys
from datetime import date

from src.models.exchange_rate import ExchangeRateRecord
from src.services.cbr_client import CBRClient, CBRClientError
from src.services.parquet_writer import ParquetWriter
from src.utils.date_utils import get_last_7_days
from src.utils.validators import validate_records

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Exit codes per CLI contract
EXIT_SUCCESS = 0
EXIT_CBR_API_ERROR = 1
EXIT_NETWORK_ERROR = 2
EXIT_INVALID_DATA = 3
EXIT_FILE_SYSTEM_ERROR = 4
EXIT_VALIDATION_ERROR = 5


def main() -> int:
    """
    Main CLI entry point.
    
    Extracts RUB/USD exchange rate data for the last 7 days from CBR and saves to Parquet file.
    
    Returns:
        Exit code (0 for success, 1-5 for errors)
    """
    parser = argparse.ArgumentParser(
        description="Extract RUB/USD exchange rate data for the last 7 days from CBR and save to Parquet file"
    )
    # No arguments needed per CLI contract
    args = parser.parse_args()
    
    try:
        # Calculate date range: [today, today - 6] (inclusive, 7 days total)
        dates = get_last_7_days()
        start_date = dates[0]
        end_date = dates[-1]
        
        logger.info(f"Extracting exchange rates for period: {start_date} to {end_date}")
        
        # Extract data from CBR API
        try:
            cbr_client = CBRClient()
            records = cbr_client.get_exchange_rates(start_date, end_date)
        except CBRClientError as e:
            # Error message already printed to stderr by CBRClient
            # Determine exit code based on error type
            error_str = str(e).lower()
            if "timeout" in error_str or "connection" in error_str or "network" in error_str:
                return EXIT_NETWORK_ERROR
            elif "invalid" in error_str or "malformed" in error_str:
                return EXIT_INVALID_DATA
            else:
                return EXIT_CBR_API_ERROR
        
        # Validate data before saving (FR-010)
        logger.info("Validating extracted data")
        is_valid, error_msg = validate_records(records, start_date, end_date)
        if not is_valid:
            error_message = f"Data validation failed: {error_msg}"
            logger.error(error_message)
            print(f"Error: {error_message}", file=sys.stderr)
            return EXIT_VALIDATION_ERROR
        
        # Prepare metadata
        report_date = date.today().isoformat()
        metadata = {
            "report_date": report_date,
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "data_source": "CBR"
        }
        
        # Write to Parquet file
        try:
            writer = ParquetWriter()
            filename = writer.write_exchange_rates(records, metadata, output_dir=".")
            logger.info(f"Successfully created Parquet file: {filename}")
            print(f"Successfully created {filename}")
            return EXIT_SUCCESS
        except IOError as e:
            error_message = f"File system error: {e}"
            logger.error(error_message)
            print(f"Error: {error_message}", file=sys.stderr)
            return EXIT_FILE_SYSTEM_ERROR
        except ValueError as e:
            error_message = f"Invalid metadata: {e}"
            logger.error(error_message)
            print(f"Error: {error_message}", file=sys.stderr)
            return EXIT_INVALID_DATA
        except Exception as e:
            error_message = f"Unexpected error: {e}"
            logger.error(error_message, exc_info=True)
            print(f"Error: {error_message}", file=sys.stderr)
            return EXIT_FILE_SYSTEM_ERROR
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        print("\nInterrupted by user", file=sys.stderr)
        return EXIT_CBR_API_ERROR
    except Exception as e:
        error_message = f"Unexpected error: {e}"
        logger.error(error_message, exc_info=True)
        print(f"Error: {error_message}", file=sys.stderr)
        return EXIT_CBR_API_ERROR


if __name__ == "__main__":
    sys.exit(main())

