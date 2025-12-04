"""CBR API client for extracting exchange rate data."""

import logging
import sys
from datetime import date, timedelta
from typing import List
from xml.etree import ElementTree as ET

import requests

from src.models.exchange_rate import ExchangeRateRecord

logger = logging.getLogger(__name__)


class CBRClientError(Exception):
    """Exception raised for CBR API client errors."""
    pass


class CBRClient:
    """
    Client for retrieving exchange rate data from Central Bank of Russia (ЦБ РФ) API.
    
    The client connects to the CBR XML_dynamic.asp API endpoint to retrieve
    RUB/USD exchange rates for a specified date range.
    """
    
    BASE_URL = "http://www.cbr.ru/scripts/XML_dynamic.asp"
    CURRENCY_CODE = "R01235"  # USD currency code
    TIMEOUT_SECONDS = 15  # Aligns with SC-002 (30-second total requirement)
    
    def __init__(self):
        """Initialize the CBR client."""
        self.session = requests.Session()
    
    def get_exchange_rates(self, start_date: date, end_date: date) -> List[ExchangeRateRecord]:
        """
        Retrieve RUB/USD exchange rates for the specified date range.
        
        Args:
            start_date: Start date of the period (inclusive)
            end_date: End date of the period (inclusive)
        
        Returns:
            List of ExchangeRateRecord objects, one for each day in the range.
            Missing days (weekends/holidays) will have null exchange_rate_value.
        
        Raises:
            CBRClientError: If the API request fails, times out, or returns invalid data.
        """
        try:
            # Construct URL with date range
            url = self._build_url(start_date, end_date)
            logger.info(f"Requesting exchange rates from CBR API: {start_date} to {end_date}")
            
            # Make request with timeout (aligns with SC-002: 30-second total requirement)
            response = self.session.get(url, timeout=self.TIMEOUT_SECONDS)
            response.raise_for_status()
            
            # Decode from windows-1251 encoding
            try:
                content = response.content.decode('windows-1251')
            except UnicodeDecodeError as e:
                logger.error(f"Failed to decode response from windows-1251: {e}")
                raise CBRClientError(
                    "Invalid response encoding from CBR API. Expected windows-1251."
                ) from e
            
            # Parse XML and extract records
            records = self._parse_xml_response(content, start_date, end_date)
            
            logger.info(f"Successfully retrieved {len([r for r in records if r.exchange_rate_value is not None])} exchange rates")
            return records
            
        except requests.Timeout as e:
            error_msg = "Network timeout while connecting to CBR API. Please check your network connection."
            logger.error(error_msg)
            print(error_msg, file=sys.stderr)
            raise CBRClientError(error_msg) from e
            
        except requests.ConnectionError as e:
            error_msg = "Unable to connect to CBR API. Please check your network connection."
            logger.error(error_msg)
            print(error_msg, file=sys.stderr)
            raise CBRClientError(error_msg) from e
            
        except requests.HTTPError as e:
            error_msg = f"CBR API returned error: {e.response.status_code if hasattr(e, 'response') else 'Unknown'}"
            logger.error(error_msg)
            print(error_msg, file=sys.stderr)
            raise CBRClientError(error_msg) from e
            
        except ET.ParseError as e:
            error_msg = "Invalid or malformed XML response from CBR API."
            logger.error(f"{error_msg}: {e}")
            print(error_msg, file=sys.stderr)
            raise CBRClientError(error_msg) from e
            
        except (ValueError, KeyError, AttributeError) as e:
            error_msg = "Invalid or malformed data received from CBR API."
            logger.error(f"{error_msg}: {e}")
            print(error_msg, file=sys.stderr)
            raise CBRClientError(error_msg) from e
    
    def _build_url(self, start_date: date, end_date: date) -> str:
        """
        Build the CBR API URL with date range parameters.
        
        Args:
            start_date: Start date (DD/MM/YYYY format)
            end_date: End date (DD/MM/YYYY format)
        
        Returns:
            Complete API URL with query parameters
        """
        date_req1 = start_date.strftime('%d/%m/%Y')
        date_req2 = end_date.strftime('%d/%m/%Y')
        return (
            f"{self.BASE_URL}"
            f"?date_req1={date_req1}"
            f"&date_req2={date_req2}"
            f"&VAL_NM_RQ={self.CURRENCY_CODE}"
        )
    
    def _parse_xml_response(
        self, xml_content: str, start_date: date, end_date: date
    ) -> List[ExchangeRateRecord]:
        """
        Parse XML response and create ExchangeRateRecord objects for all dates in range.
        
        Missing days (weekends/holidays) are filled with null exchange_rate_value.
        
        Args:
            xml_content: XML content as string (already decoded from windows-1251)
            start_date: Start date of the period
            end_date: End date of the period
        
        Returns:
            List of ExchangeRateRecord objects, one for each day in the range
        """
        # Parse XML
        root = ET.fromstring(xml_content)
        
        # Extract all records from API response
        api_records = {}
        for record_elem in root.findall('Record'):
            # Extract date (DD.MM.YYYY format)
            date_str = record_elem.get('Date')
            if not date_str:
                continue
            
            # Parse date from DD.MM.YYYY to date object
            try:
                day, month, year = date_str.split('.')
                record_date = date(int(year), int(month), int(day))
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid date format in API response: {date_str}, skipping")
                continue
            
            # Extract exchange rate value
            value_elem = record_elem.find('Value')
            if value_elem is None or value_elem.text is None:
                logger.warning(f"No Value element for date {record_date}, skipping")
                continue
            
            # Convert comma to dot and parse as float
            try:
                value_str = value_elem.text.replace(',', '.')
                rate = float(value_str)
                api_records[record_date] = rate
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid rate value for date {record_date}: {value_elem.text}, skipping")
                continue
        
        # Create ExchangeRateRecord for all dates in range, filling missing days with null
        result = []
        current_date = start_date
        while current_date <= end_date:
            rate = api_records.get(current_date)  # None if missing
            result.append(ExchangeRateRecord(
                date=current_date,
                exchange_rate_value=rate,
                currency_pair="RUB/USD"
            ))
            current_date += timedelta(days=1)
        
        return result


