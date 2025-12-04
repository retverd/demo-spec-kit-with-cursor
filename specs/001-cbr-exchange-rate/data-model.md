# Data Model: Extract RUB/USD Exchange Rate from CBR

**Date**: 2025-12-02  
**Feature**: 001-cbr-exchange-rate

## Overview

The data model consists of two main entities:

1. **Exchange Rate Record** - Represents daily exchange rate data stored in Parquet data rows
2. **Report Metadata** - Represents extraction metadata stored as Parquet file-level metadata

## Entities

### Exchange Rate Record

**Purpose**: Represents a single day's RUB/USD exchange rate data.

**Storage**: Parquet file data rows (one row per day in the 7-day period)

**Attributes**:

| Field Name | Type | Nullable | Description | Validation Rules |
|-----------|------|----------|-------------|------------------|
| `date` | date | No | Calendar date for this exchange rate (YYYY-MM-DD format) | Must be a valid date within the 7-day period |
| `exchange_rate_value` | float64 | Yes | RUB/USD exchange rate (e.g., 78.50 means 1 USD = 78.50 RUB) | If null, indicates missing data for that day. If present, must be > 0 |
| `currency_pair` | string | No | Identifier for the currency pair | Always "RUB/USD" |

**Constraints**:

- Exactly one row per day in the 7-day period (7 rows total)
- Missing days have `exchange_rate_value = null`
- `date` must be sequential (consecutive calendar days)
- `currency_pair` is constant for all rows

**Example Data**:
```
date       | exchange_rate_value | currency_pair
-----------|---------------------|--------------
2025-11-25 | 78.50               | RUB/USD
2025-11-26 | 78.55               | RUB/USD
2025-11-27 | null                | RUB/USD  (missing data)
2025-11-28 | 78.60               | RUB/USD
2025-11-29 | 78.65               | RUB/USD
2025-11-30 | null                | RUB/USD  (weekend)
2025-12-01 | 78.70               | RUB/USD
```

---

### Report Metadata

**Purpose**: Represents information about the data extraction and report generation.

**Storage**: Parquet file-level metadata (key-value pairs accessible via Parquet metadata API)

**Attributes**:

| Key Name | Type | Description | Example |
|----------|------|-------------|---------|
| `report_date` | string (ISO date) | Date when the extraction was performed | "2025-12-02" |
| `period_start` | string (ISO date) | Earliest date in the data period | "2025-11-25" |
| `period_end` | string (ISO date) | Latest date in the data period | "2025-12-01" |
| `data_source` | string | Identifier for the data source | "CBR" |

**Constraints**:

- All dates in ISO 8601 format (YYYY-MM-DD)
- `period_start` must be <= `period_end`
- `report_date` is typically >= `period_end` (extraction happens after or on the last day)
- `data_source` is constant ("CBR")

**Access Pattern**:

- Written: Set as key-value pairs in Parquet file metadata during file creation
- Read: Accessed via `parquet_file.metadata.metadata` (returns dict)

**Example Metadata**:

```python
{
    "report_date": "2025-12-02",
    "period_start": "2025-11-25",
    "period_end": "2025-12-01",
    "data_source": "CBR"
}
```

---

## Data Flow

1. **Extraction Phase**:
   - System requests exchange rate data from CBR API for each of 7 days
   - For each day, creates an `ExchangeRateRecord` with:
     - `date`: The requested date
     - `exchange_rate_value`: Parsed rate from CBR API (or null if missing)
     - `currency_pair`: "RUB/USD"

2. **Validation Phase**:
   - Validates all records (FR-010):
     - Dates are valid and within the 7-day period
     - Non-null rates are positive numbers
     - All 7 days are present (some may have null rates)

3. **Storage Phase**:
   - Creates Parquet file with:
     - Data rows: All 7 `ExchangeRateRecord` objects
     - File metadata: `ReportMetadata` as key-value pairs
   - Filename includes period and timestamp (FR-005)

---

## Validation Rules

### Exchange Rate Record Validation

**From FR-010**: System MUST validate that retrieved data contains valid date and numeric exchange rate values before saving.

1. **Date Validation**:
   - Must be parseable as ISO date (YYYY-MM-DD)
   - Must be within the calculated 7-day period
   - Must be unique (no duplicate dates)

2. **Exchange Rate Value Validation**:
   - If not null: Must be convertible to float
   - If not null: Must be > 0
   - If null: Valid (indicates missing data)

3. **Completeness Validation**:
   - Must have exactly 7 records (one per day)
   - All dates must be present (even if rate is null)

### Report Metadata Validation

1. **Date Format Validation**:
   - All date fields must be ISO 8601 format (YYYY-MM-DD)
   - Dates must be parseable

2. **Logical Validation**:
   - `period_start` <= `period_end`
   - `period_start` and `period_end` match the data rows' date range

---

## Parquet Schema

**Data Columns**:

- `date`: date32 (Parquet date type)
- `exchange_rate_value`: double (nullable)
- `currency_pair`: string (UTF-8)

**File Metadata** (key-value pairs):

- `report_date`: string
- `period_start`: string
- `period_end`: string
- `data_source`: string

---

## Relationships

- **One-to-Many**: One `ReportMetadata` → Many `ExchangeRateRecord` (one report contains 7 rate records)
- **Temporal**: Records are ordered by `date` (sequential calendar days)

---

## State Transitions

N/A - Data is immutable once written. Each extraction creates a new file with a timestamp.

---

## Error Scenarios

1. **Missing Data for Some Days**:
   - State: `exchange_rate_value = null` for those days
   - File is still created (FR-009)
   - All 7 days present in data rows

2. **Invalid Data from CBR**:
   - Validation fails (FR-010)
   - Error message to console
   - Non-zero exit code
   - File not created

3. **Network Failure**:
   - No data retrieved
   - Error message to console
   - Non-zero exit code
   - File not created

