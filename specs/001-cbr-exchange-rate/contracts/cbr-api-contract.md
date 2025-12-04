# CBR API Contract: Exchange Rate Data Source

**Date**: 2025-12-02  
**Feature**: 001-cbr-exchange-rate

## API Overview

**Service**: Central Bank of Russia (ЦБ РФ) Dynamic Exchange Rates  
**Endpoint**: `http://www.cbr.ru/scripts/XML_dynamic.asp`  
**Method**: GET  
**Format**: XML  
**Encoding**: windows-1251

## Request

### Endpoint

```http
GET http://www.cbr.ru/scripts/XML_dynamic.asp?date_req1=DD/MM/YYYY&date_req2=DD/MM/YYYY&VAL_NM_RQ=R01235
```

### Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `date_req1` | string | Yes | Start date in DD/MM/YYYY format | "25/11/2025" |
| `date_req2` | string | Yes | End date in DD/MM/YYYY format | "01/12/2025" |
| `VAL_NM_RQ` | string | Yes | Currency code (R01235 for USD) | "R01235" |

### Example Request

```http
GET http://www.cbr.ru/scripts/XML_dynamic.asp?date_req1=25/11/2025&date_req2=01/12/2025&VAL_NM_RQ=R01235 HTTP/1.1
Host: www.cbr.ru
```

## Response

### Success Response (200 OK)

**Content-Type**: `text/xml; charset=windows-1251`

**Structure**:

```xml
<?xml version="1.0" encoding="windows-1251"?>
<ValCurs ID="R01235" DateRange1="25.11.2025" DateRange2="01.12.2025" name="Foreign Currency Market Dynamic">
    <Record Date="25.11.2025" Id="R01235">
        <Nominal>1</Nominal>
        <Value>78,5000</Value>
        <VunitRate>78,50</VunitRate>
    </Record>
    <Record Date="26.11.2025" Id="R01235">
        <Nominal>1</Nominal>
        <Value>78,5500</Value>
        <VunitRate>78,55</VunitRate>
    </Record>
    <!-- Missing days (weekends/holidays) are not present in response -->
    <Record Date="29.11.2025" Id="R01235">
        <Nominal>1</Nominal>
        <Value>78,6000</Value>
        <VunitRate>78,60</VunitRate>
    </Record>
</ValCurs>
```

**Key Elements**:

- `ValCurs/@ID`: Currency code (R01235 for USD)
- `ValCurs/@DateRange1`: Start date of range (DD.MM.YYYY format)
- `ValCurs/@DateRange2`: End date of range (DD.MM.YYYY format)
- `Record`: One element per day with available data
  - `Record/@Date`: Date of the rate (DD.MM.YYYY format)
  - `Record/Value`: Exchange rate as string with comma decimal separator (e.g., "78,5000" means 1 USD = 78.50 RUB)
  - `Record/VunitRate`: Rate per unit (same as Value, formatted)
  - `Record/Nominal`: Usually "1" (base unit)

**USD Currency Code**: `R01235` (constant, passed as VAL_NM_RQ parameter)

**Important Notes**:

- Missing days (weekends, holidays) are **not included** in the response
- Response encoding is **windows-1251**, must be decoded properly
- Decimal separator is **comma** (","), must be converted to dot (".") for float conversion
- Response may contain fewer than 7 records if some days have no data

### Error Responses

**404 Not Found**: Invalid date range or currency code

- Response may be empty or contain error message
- Should be handled as API error (fatal)

**500 Internal Server Error**: CBR server error

- Should be handled as API unavailable error

**Timeout**: Network timeout

- Should be handled as connection failure

## Data Extraction

### USD Rate Extraction

1. Decode response from windows-1251 to UTF-8
2. Parse XML response
3. Extract all `Record` elements from `ValCurs`
4. For each `Record`:
   - Extract `@Date` attribute (DD.MM.YYYY format)
   - Extract `Value` element text
   - Convert comma to dot: "78,5000" → "78.5000"
   - Convert to float: 78.50
   - Create ExchangeRateRecord with date and rate
5. For dates in the requested range that have no `Record`:
   - Create ExchangeRateRecord with date and null rate value

### Date Handling

- Request date format: DD/MM/YYYY (e.g., "25/11/2025")
- Response date format: DD.MM.YYYY (e.g., "25.11.2025")
- Convert to ISO format: YYYY-MM-DD (e.g., "2025-11-25")
- Calculate all 7 dates in range, match with Records from API

### Missing Data Handling

- Days without data (weekends, holidays) will not have a `Record` in the response
- System must:
  1. Calculate all 7 dates in the requested range
  2. Match Records from API response to dates
  3. Create ExchangeRateRecord with null rate for dates without matching Record

## Rate Limits

**Not documented**, but should:

- Single request is more efficient than multiple requests
- Handle rate limiting gracefully if encountered
- Conservative approach: one request per execution

## Reliability

- **Availability**: Generally high, but may have occasional downtime
- **Data Freshness**: Rates updated daily, typically by end of business day
- **Weekends/Holidays**: No new rates published, those days will not appear in response
- **Encoding**: Response uses windows-1251, must be handled correctly

## Error Handling

### Missing Data (days not in response)

- **Behavior**: Normal - weekends/holidays don't have rates
- **Action**: Create ExchangeRateRecord with null rate value for missing days
- **Continue**: Proceed with file creation (FR-009)

### API Unavailable (500, timeout, connection error)

- **Behavior**: Fatal error
- **Action**: Output error message, return exit code 1
- **Stop**: Do not create file

### Invalid Response Format

- **Behavior**: Fatal error
- **Action**: Output error message, return exit code 3
- **Stop**: Do not create file

### Encoding Errors

- **Behavior**: Fatal error
- **Action**: Output error message, return exit code 3
- **Stop**: Do not create file

## Implementation Notes

1. **Single Request**: Make one request with date range (date_req1 to date_req2)
2. **Encoding**: Decode response from windows-1251: `response.content.decode('windows-1251')`
3. **Parsing**: Use `xml.etree.ElementTree` or `lxml` for XML parsing
4. **Rate Conversion**: Replace comma with dot: `value.replace(',', '.')` then `float()`
5. **Date Matching**: Calculate all 7 dates, match with Records, fill missing with null
6. **Timeout**: Set request timeout to 15 seconds (single request, more time available)
7. **Efficiency**: One request is much faster than 7 separate requests

## Example Implementation

```python
from datetime import date, timedelta
import requests
from xml.etree import ElementTree as ET

def get_exchange_rates(start_date: date, end_date: date) -> list[ExchangeRateRecord]:
    # Construct URL
    url = (
        f"http://www.cbr.ru/scripts/XML_dynamic.asp"
        f"?date_req1={start_date.strftime('%d/%m/%Y')}"
        f"&date_req2={end_date.strftime('%d/%m/%Y')}"
        f"&VAL_NM_RQ=R01235"
    )
    
    # Make request
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    
    # Decode from windows-1251
    content = response.content.decode('windows-1251')
    
    # Parse XML
    root = ET.fromstring(content)
    
    # Extract all records
    records = {}
    for record in root.findall('Record'):
        date_str = record.get('Date')  # DD.MM.YYYY
        value_str = record.find('Value').text  # "78,5000"
        
        # Convert date
        day, month, year = date_str.split('.')
        record_date = date(int(year), int(month), int(day))
        
        # Convert rate
        rate = float(value_str.replace(',', '.'))
        
        records[record_date] = rate
    
    # Create ExchangeRateRecord for all dates in range
    result = []
    current = start_date
    while current <= end_date:
        rate = records.get(current)  # None if missing
        result.append(ExchangeRateRecord(
            date=current,
            exchange_rate_value=rate,
            currency_pair="RUB/USD"
        ))
        current += timedelta(days=1)
    
    return result
```
