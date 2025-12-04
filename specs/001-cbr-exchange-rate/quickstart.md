# Quick Start Guide: Extract RUB/USD Exchange Rate from CBR

**Date**: 2025-12-02  
**Feature**: 001-cbr-exchange-rate

## Overview

This guide helps developers quickly understand and start implementing the CBR exchange rate extraction feature.

## Prerequisites

- Python 3.14
- pip (Python package manager)
- Git (for version control)
- Network access to `www.cbr.ru`

## Project Setup

### 1. Install Dependencies

Create `requirements.txt`:

```txt
requests>=2.31.0
pyarrow>=14.0.0
pytest>=7.4.0
pytest-mock>=3.11.0
```

Install:

```bash
pip install -r requirements.txt
```

### 2. Project Structure

```txt
src/
├── models/
│   └── exchange_rate.py      # ExchangeRateRecord data model
├── services/
│   ├── cbr_client.py         # CBR API client
│   └── parquet_writer.py     # Parquet file writer
├── cli/
│   └── main.py               # CLI entry point
└── utils/
    ├── date_utils.py         # Date calculations
    └── validators.py         # Data validation

tests/
├── unit/
│   ├── test_cbr_client.py
│   ├── test_parquet_writer.py
│   └── test_validators.py
└── integration/
    └── test_end_to_end.py
```

## Implementation Checklist

### Phase 1: Core Data Model

- [ ] Create `src/models/exchange_rate.py`
  - Define `ExchangeRateRecord` class/dataclass
  - Fields: `date`, `exchange_rate_value`, `currency_pair`
  - Validation methods

### Phase 2: CBR API Client

- [ ] Create `src/services/cbr_client.py`
  - Implement `CBRClient` class
  - Method: `get_exchange_rates(start_date: date, end_date: date) -> list[ExchangeRateRecord]`
  - Handle XML parsing with windows-1251 encoding
  - Handle multiple Record elements from single response
  - Match dates with Records, fill missing days with null
  - Handle errors (404 = error, 500 = error)
  - Set 15-second timeout (single request)

### Phase 3: Date Utilities

- [ ] Create `src/utils/date_utils.py`
  - Function: `get_last_7_days() -> list[date]`
  - Returns list of 7 dates (today - 6 days to today)

### Phase 4: Data Validation

- [ ] Create `src/utils/validators.py`
  - Function: `validate_date(date_str: str) -> bool`
  - Function: `validate_rate(rate: float | None) -> bool`
  - Function: `validate_records(records: list[ExchangeRateRecord]) -> bool`

### Phase 5: Parquet Writer

- [ ] Create `src/services/parquet_writer.py`
  - Implement `ParquetWriter` class
  - Method: `write_exchange_rates(records: list[ExchangeRateRecord], metadata: dict) -> str`
  - Use `pyarrow` to write Parquet file
  - Set file-level metadata (report_date, period_start, period_end, data_source)
  - Generate filename with timestamp
  - Return file path

### Phase 6: CLI Interface

- [ ] Create `src/cli/main.py`
  - Use `argparse` for CLI
  - Main function:
    1. Calculate last 7 days (start_date and end_date)
    2. Call CBR client with date range (single request)
    3. Get list of ExchangeRateRecord (with null rates for missing days)
    4. Validate records
    5. Write Parquet file
    6. Handle errors with appropriate exit codes

### Phase 7: Testing

- [ ] Unit tests for each component
- [ ] Mock CBR API responses
- [ ] Test error scenarios
- [ ] Integration test for full flow

## Key Implementation Details

### CBR API Call

```python
import requests
from datetime import date, timedelta
from xml.etree import ElementTree as ET

def get_exchange_rates(start_date: date, end_date: date) -> list[ExchangeRateRecord]:
    """
    Get USD exchange rates for date range using XML_dynamic.asp API.
    Returns list of ExchangeRateRecord, with null rates for missing days.
    """
    # Construct URL with date range
    url = (
        f"http://www.cbr.ru/scripts/XML_dynamic.asp"
        f"?date_req1={start_date.strftime('%d/%m/%Y')}"
        f"&date_req2={end_date.strftime('%d/%m/%Y')}"
        f"&VAL_NM_RQ=R01235"
    )
    
    # Make request
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    
    # Decode from windows-1251 encoding
    content = response.content.decode('windows-1251')
    
    # Parse XML
    root = ET.fromstring(content)
    
    # Extract all records into a dictionary
    records = {}
    for record in root.findall('Record'):
        date_str = record.get('Date')  # Format: DD.MM.YYYY
        value_str = record.find('Value').text  # Format: "78,5000"
        
        # Parse date
        day, month, year = date_str.split('.')
        record_date = date(int(year), int(month), int(day))
        
        # Convert rate (replace comma with dot)
        rate = float(value_str.replace(',', '.'))
        
        records[record_date] = rate
    
    # Create ExchangeRateRecord for all dates in range
    result = []
    current = start_date
    while current <= end_date:
        rate = records.get(current)  # None if day has no data
        result.append(ExchangeRateRecord(
            date=current,
            exchange_rate_value=rate,
            currency_pair="RUB/USD"
        ))
        current += timedelta(days=1)
    
    return result
```

### Parquet File Writing

```python
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime

def write_parquet(records: list[ExchangeRateRecord], metadata: dict) -> str:
    # Create table from records
    data = {
        "date": [r.date for r in records],
        "exchange_rate_value": [r.exchange_rate_value for r in records],
        "currency_pair": [r.currency_pair for r in records]
    }
    table = pa.table(data)
    
    # Generate filename
    period_start = min(r.date for r in records)
    period_end = max(r.date for r in records)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"rub_usd_{period_start}_to_{period_end}_{timestamp}.parquet"
    
    # Write with metadata
    pq.write_table(
        table,
        filename,
        metadata={
            "report_date": metadata["report_date"],
            "period_start": metadata["period_start"],
            "period_end": metadata["period_end"],
            "data_source": metadata["data_source"]
        }
    )
    
    return filename
```

### Error Handling

```python
import sys

def main():
    try:
        # ... extraction logic ...
        print(f"Successfully created {filename}")
        sys.exit(0)
    except CBRAPIError as e:
        print(f"Error: CBR API unavailable: {e}", file=sys.stderr)
        sys.exit(1)
    except ValidationError as e:
        print(f"Error: Data validation failed: {e}", file=sys.stderr)
        sys.exit(5)
    except Exception as e:
        print(f"Error: Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)
```

## Testing Strategy

### Unit Tests

1. **CBR Client Tests**:
   - Mock HTTP responses with windows-1251 encoding
   - Test XML parsing with multiple Record elements
   - Test date range handling
   - Test missing days (weekends/holidays not in response)
   - Test error handling (404, 500, timeout)
   - Test encoding conversion (windows-1251 to UTF-8)
   - Test rate extraction with comma decimal separator

2. **Parquet Writer Tests**:
   - Test file creation
   - Test metadata storage
   - Test filename generation
   - Test with null values

3. **Validator Tests**:
   - Test date validation
   - Test rate validation
   - Test completeness validation

### Integration Tests

1. **End-to-End Test**:
   - Mock CBR API (use `responses` library or `pytest-mock`)
   - Test full extraction flow
   - Verify Parquet file structure
   - Verify metadata

## Common Pitfalls

1. **Date Format**: CBR uses DD/MM/YYYY in request, DD.MM.YYYY in response, but store as YYYY-MM-DD internally
2. **Decimal Separator**: CBR uses comma (",") in XML response, must convert to dot (".") for float
3. **Missing Data**: Days without data (weekends/holidays) are simply not in the response - not an error
4. **Encoding**: Response is windows-1251, must decode properly: `response.content.decode('windows-1251')`
5. **Date Range**: Calculate all 7 dates first, then match with Records from API response
6. **Timezone**: Use local date for "last 7 days" calculation
7. **Parquet Metadata**: Must be set during file creation, not after
8. **Single Request**: Use XML_dynamic.asp with date range - much more efficient than multiple requests

## Next Steps

1. Review `data-model.md` for data structure details
2. Review `contracts/` for API and CLI specifications
3. Review `research.md` for technology decisions
4. Start with Phase 1 (data model) and work sequentially
5. Write tests alongside implementation

## Resources

- [CBR Exchange Rates](https://www.cbr.ru/currency_base/)
- [PyArrow Documentation](https://arrow.apache.org/docs/python/)
- [Requests Documentation](https://requests.readthedocs.io/)
- [pytest Documentation](https://docs.pytest.org/)
