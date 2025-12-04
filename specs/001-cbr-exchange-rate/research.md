# Research: Extract RUB/USD Exchange Rate from CBR

**Date**: 2025-12-02  
**Feature**: 001-cbr-exchange-rate

## Research Questions

### 1. HTTP Client Library for CBR API Access

**Question**: What Python library should be used for making HTTP requests to the CBR website/API?

**Decision**: `requests` library

**Rationale**:

- Most widely used and stable HTTP library for Python
- Simple synchronous API suitable for CLI tool
- Excellent documentation and community support
- Handles XML/JSON responses well
- Good error handling capabilities
- No async complexity needed for single-threaded CLI tool

**Alternatives Considered**:

- `httpx`: Modern async-capable library, but adds unnecessary complexity for synchronous CLI tool
- `urllib` (standard library): Lower-level, more verbose, less user-friendly
- `aiohttp`: Async library, overkill for simple CLI tool

**Implementation Notes**:

- Use `requests.get()` for API calls
- Set appropriate timeout (e.g., 10 seconds) to meet SC-002 (30 second total)
- Handle HTTP errors (4xx, 5xx) with clear error messages
- Parse XML responses using `xml.etree.ElementTree` (standard library) or `lxml` if needed

---

### 2. Parquet File Writing with Metadata

**Question**: What Python library should be used for writing Parquet files with file-level metadata?

**Decision**: `pyarrow` (Apache Arrow)

**Rationale**:

- Industry standard for Parquet file operations
- Native support for file-level metadata (key-value pairs)
- Efficient columnar storage
- Excellent performance
- Well-maintained and widely used
- Direct API for metadata: `parquet_file.metadata.metadata` (write) and `parquet_file.metadata` (read)
- Works seamlessly with pandas if needed

**Alternatives Considered**:

- `pandas.to_parquet()`: Uses pyarrow under the hood but less direct control over metadata
- `fastparquet`: Alternative implementation, but pyarrow is more actively maintained
- Writing custom Parquet: Too complex, reinventing the wheel

**Implementation Notes**:

- Use `pyarrow.parquet.ParquetWriter` for writing
- Set metadata using `metadata` parameter in `write_table()` or via `ParquetFile.metadata.metadata`
- Metadata keys: `report_date`, `period_start`, `period_end`, `data_source`
- Read metadata via `parquet_file.metadata.metadata` (returns dict)

---

### 3. Date Handling and Calculation

**Question**: How should dates be handled for calculating the last 7 days and date formatting?

**Decision**: Python `datetime` standard library + `dateutil` (optional) for timezone handling

**Rationale**:

- `datetime` is part of standard library, no external dependency
- Sufficient for date arithmetic (calculating 7 days back)
- Well-documented and familiar to Python developers
- `dateutil.relativedelta` can be used if more complex date operations needed (but not required here)
- Format dates as ISO 8601 strings (YYYY-MM-DD) for consistency

**Alternatives Considered**:

- `arrow`: External library, adds dependency for simple date operations
- `pendulum`: Modern date library, but standard library is sufficient
- Manual date calculation: More error-prone

**Implementation Notes**:

- Use `datetime.date.today()` to get current date
- Calculate 7 days: `[today, today - 6]` (inclusive, 7 days total) - from `today - timedelta(days=6)` to `today`
- Format dates as strings: `date.isoformat()` (YYYY-MM-DD format)
- Store dates in Parquet as date type (not strings) for better querying

---

### 4. CBR API Endpoint and Data Format

**Question**: What is the CBR API endpoint and data format for exchange rates?

**Decision**: CBR Dynamic Exchange Rates API (XML format) - single request for date range

**Rationale**:

- CBR provides official daily exchange rates via web service
- Endpoint: `http://www.cbr.ru/scripts/XML_dynamic.asp?date_req1=DD/MM/YYYY&date_req2=DD/MM/YYYY&VAL_NM_RQ=R01235`
- Returns XML with exchange rates for specified date range in a single request
- USD currency code: `R01235` (internal CBR code, passed as VAL_NM_RQ parameter)
- Much more efficient: one request instead of 7 separate requests
- Response contains multiple `Record` elements, one per day with available data
- Missing days (weekends, holidays) are simply not present in the response
- Encoding: windows-1251 (need to handle properly)

**Alternatives Considered**:

- XML_daily.asp (per-day requests): Less efficient, requires 7 separate API calls
- CBR JSON API: Not officially documented, XML is the standard
- Web scraping: Less reliable, violates terms of service
- Third-party APIs: Not official, may have rate limits or costs

**Implementation Notes**:

- Construct URL with date_req1 (start date) and date_req2 (end date) in DD/MM/YYYY format
- Use VAL_NM_RQ=R01235 to request USD rates specifically
- Parse XML response to extract all Record elements
- Each Record contains Date (DD.MM.YYYY) and Value (with comma as decimal separator)
- Missing days are indicated by absence of Record for that date
- Handle encoding: response is windows-1251, convert to UTF-8 for processing
- Single request is much faster and more reliable than 7 separate requests

---

### 5. Data Validation Library

**Question**: Should we use a validation library for data validation (FR-010)?

**Decision**: Custom validation functions using standard library

**Rationale**:

- Simple validation rules (date format, numeric rate)
- Standard library `datetime` for date parsing/validation
- `float()` with try/except for numeric validation
- No need for external validation library (pydantic, cerberus) for simple CLI tool
- Keeps dependencies minimal

**Alternatives Considered**:

- `pydantic`: Excellent for complex validation, but overkill for simple data
- `cerberus`: Schema validation, adds dependency
- `marshmallow`: Serialization/validation, unnecessary complexity

**Implementation Notes**:

- Validate date: Try parsing with `datetime.strptime(date_str, '%Y-%m-%d')`
- Validate rate: Try converting to `float()`, check > 0
- Return clear error messages if validation fails

---

## Summary of Technology Choices

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| HTTP Client | `requests` | Latest | Simple, stable, well-documented |
| Parquet Library | `pyarrow` | Latest | Industry standard, metadata support |
| Date Handling | `datetime` (stdlib) | Built-in | Sufficient, no external dependency |
| Data Validation | Custom (stdlib) | Built-in | Simple rules, minimal dependencies |
| Testing | `pytest` | Latest | Standard Python testing framework |
| CLI Framework | `argparse` (stdlib) | Built-in | Simple CLI, no external dependency |

## Dependencies Summary

**Required External Dependencies**:

- `requests` - HTTP client
- `pyarrow` - Parquet file operations

**Standard Library** (no installation needed):

- `datetime` - Date handling
- `xml.etree.ElementTree` - XML parsing
- `argparse` - CLI argument parsing
- `sys` - Exit codes
- `pathlib` - File path handling

**Development Dependencies**:

- `pytest` - Testing framework
- `pytest-mock` - Mocking for tests (optional but recommended)
