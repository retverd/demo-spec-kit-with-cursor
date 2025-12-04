# CLI Contract: Extract RUB/USD Exchange Rate from CBR

**Date**: 2025-12-02  
**Feature**: 001-cbr-exchange-rate

## Command Interface

### Command Name

`extract-cbr-rates` (or similar, to be determined during implementation)

### Usage

```bash
extract-cbr-rates
```

### Description

Extracts RUB/USD exchange rate data for the last 7 calendar days from the Central Bank of Russia (ЦБ РФ) website and saves it to a Parquet file in the current working directory.

### Arguments

**None** - The command takes no arguments. The 7-day period is automatically calculated from the current date.

### Options

**None** - Future versions may add options for:

- Custom date range
- Output directory
- Verbose logging

### Behavior

1. Calculates the last 7 calendar days: [today, today - 6] (inclusive, 7 days total)
2. Connects to CBR API using XML_dynamic.asp with date range (single request for all 7 days)
3. Retrieves exchange rate data for the date range
4. Validates the retrieved data
5. Creates a Parquet file with:
   - Data rows: One row per day (7 total) with date, exchange_rate_value, currency_pair
   - File metadata: report_date, period_start, period_end, data_source
6. Saves file to current working directory with filename pattern: `rub_usd_YYYY-MM-DD_to_YYYY-MM-DD_YYYY-MM-DD_HHMMSS.parquet`

### Exit Codes

- `0`: Success - Data extracted and file created successfully
- `1`: Error - CBR API unavailable or returned error
- `2`: Error - Network timeout or connection failure
- `3`: Error - Invalid or malformed data from CBR
- `4`: Error - File system error (permissions, disk full, etc.)
- `5`: Error - Data validation failed

### Output

**Success**:

- Console: Minimal success message
- File: Parquet file created in current directory
- Exit code: 0

**Error**:

- Console: Clear error message describing the failure
- File: No file created
- Exit code: Non-zero (1-5 as defined above)

### Examples

**Successful execution**:

```bash
$ extract-cbr-rates
$ echo $?
0
$ ls *.parquet
rub_usd_2025-11-25_to_2025-12-01_2025-12-02_143022.parquet
```

**Error - CBR unavailable**:

```bash
$ extract-cbr-rates
Error: Unable to connect to CBR API. Please check your network connection.
$ echo $?
1
```

**Error - Validation failure**:

```bash
$ extract-cbr-rates
Error: Invalid exchange rate data received from CBR. Rate value must be positive.
$ echo $?
5
```

---

## Input/Output Contract

### Contract Input

- **Source**: CBR API (external)
- **Format**: XML response from `http://www.cbr.ru/scripts/XML_dynamic.asp?date_req1=DD/MM/YYYY&date_req2=DD/MM/YYYY&VAL_NM_RQ=R01235`
- **Frequency**: 1 API call (single request for date range)

### Contract Output

- **Format**: Parquet file
- **Location**: Current working directory
- **Filename Pattern**: `rub_usd_{period_start}_to_{period_end}_{report_date}_{timestamp}.parquet`
- **Structure**: See data-model.md

---

## Error Handling Contract

All errors must:

1. Output clear, user-friendly error message to console (stderr)
2. Return appropriate non-zero exit code
3. Not create output file on error
4. Not crash or show stack traces to user

---

## Future Extensibility

The CLI interface is designed to be extensible:

- Options for custom date ranges
- Options for output directory
- Options for verbose/debug mode
- Options for different currency pairs (future feature)
