# Feature Specification: Extract RUB/USD Exchange Rate from CBR

**Feature Branch**: `001-cbr-exchange-rate`  
**Created**: 2025-12-02  
**Status**: Draft  
**Input**: User description: "Добавить функционал, который извлекает курс рубля к доллару за последние 7 дней с сайта ЦБ РФ, и сохраняет его в parquet-файл с метаданными (дата отчёта, период)."

## Clarifications

### Session 2025-12-02

- Q: When the system runs multiple times for the same period, should it overwrite or create new files? → A: Create new file with timestamp/run identifier in filename
- Q: When exchange rate data is missing for some days, should the system still create the Parquet file or fail? → A: Create file with available data and include missing days indicator
- Q: Where should the Parquet file be saved? → A: Always save to current working directory (where command is executed)
- Q: How should the system communicate errors to the user? → A: Console output with exit codes (0 for success, non-zero for errors)
- Q: What should be the filename pattern for the Parquet files? → A: Include period dates and timestamp (e.g., rub_usd_2025-11-25_to_2025-12-01_2025-12-02_143022.parquet)
- Q: How should missing days be indicated in the Parquet file? → A: Include missing dates as rows with null/empty rate value
- Q: How should metadata (report date and period) be stored in the Parquet file? → A: Parquet file-level metadata (key-value pairs accessible via file metadata API)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Extract Exchange Rate Data from CBR (Priority: P1)

A user needs to retrieve the official RUB/USD exchange rate data for the last 7 days from the Central Bank of Russia (ЦБ РФ) website. The system should connect to the CBR data source, request exchange rate information for the specified period, and retrieve the data successfully.

**Why this priority**: This is the core functionality - without data extraction, no other operations are possible. It delivers immediate value by providing access to official exchange rate data.

**Independent Test**: Can be fully tested by executing the extraction process and verifying that exchange rate data for 7 consecutive days is successfully retrieved from the CBR source. The test delivers value by confirming the system can access and retrieve official financial data.

**Acceptance Scenarios**:

1. **Given** the system is ready to extract data, **When** a request is made for RUB/USD exchange rates for the last 7 days, **Then** the system successfully connects to the CBR data source and retrieves exchange rate records for each of the 7 days
2. **Given** valid exchange rate data exists for the requested period, **When** the extraction process completes, **Then** the system returns data containing date and exchange rate value for each day in the 7-day period
3. **Given** the CBR data source is unavailable, **When** the extraction process is attempted, **Then** the system outputs a clear error message to the console and returns a non-zero exit code

---

### User Story 2 - Save Data to Parquet Format with Metadata (Priority: P2)

A user needs the extracted exchange rate data to be persisted in a Parquet file format with associated metadata (report date and period). The system should structure the data appropriately, include metadata about when the report was generated and what time period it covers, and save it to a Parquet file.

**Why this priority**: Data persistence is essential for downstream analysis and historical tracking. The Parquet format enables efficient storage and the metadata provides context for data interpretation.

**Independent Test**: Can be fully tested by verifying that after data extraction, a Parquet file is created containing the exchange rate data and metadata fields (report date, period). The test delivers value by confirming data is properly structured and accessible for future use.

**Acceptance Scenarios**:

1. **Given** exchange rate data has been successfully extracted (even if incomplete), **When** the save operation is executed, **Then** a Parquet file is created containing rows for all 7 dates in the period, with missing days represented as rows with null rate values
2. **Given** the data extraction process has completed, **When** saving to Parquet, **Then** the file includes metadata fields (report generation date and period) stored as Parquet file-level metadata that can be accessed via the Parquet file metadata API
3. **Given** valid data exists, **When** the Parquet file is saved, **Then** the file can be successfully read back and the data matches the originally extracted values

---

### Edge Cases

- When the CBR website is temporarily unavailable or returns an error, the system outputs a clear error message to the console and returns a non-zero exit code
- When exchange rate data is missing for one or more days within the 7-day period, the system creates the Parquet file with rows for all 7 dates, where missing days have null rate values
- When the requested period includes weekends or holidays when exchange rates might not be published, the system creates the Parquet file with rows for all 7 dates, where missing days have null rate values (same as FR-009)
- How does the system handle network timeouts or connection failures during data extraction?
- What happens if the file system is full or write permissions are missing when saving the Parquet file?
- How does the system handle invalid or malformed data returned from the CBR source?
- When the system is run multiple times for the same period, it creates a new file with a filename including period dates and extraction timestamp (e.g., `rub_usd_2025-11-25_to_2025-12-01_2025-12-02_143022.parquet`) to preserve historical runs

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST connect to the Central Bank of Russia (ЦБ РФ) data source to retrieve exchange rate information
- **FR-002**: System MUST extract RUB/USD exchange rate data for the last 7 calendar days: [today, today - 6] (inclusive, 7 days total)
- **FR-003**: System MUST retrieve exchange rate records that include at minimum: date and exchange rate value
- **FR-004**: System MUST save the extracted data to a Parquet file format in the current working directory (where the command is executed)
- **FR-005**: System MUST create a new Parquet file with a filename that includes the period dates (start and end) and extraction timestamp when run multiple times for the same period (e.g., `rub_usd_2025-11-25_to_2025-12-01_2025-12-02_143022.parquet`) to preserve historical runs
- **FR-006**: System MUST include metadata in the saved file indicating the report generation date (date when the extraction was performed), stored as Parquet file-level metadata (key-value pairs accessible via Parquet file metadata API)
- **FR-007**: System MUST include metadata in the saved file indicating the period covered by the data (start date and end date of the 7-day period), stored as Parquet file-level metadata (key-value pairs accessible via Parquet file metadata API)
- **FR-008**: System MUST handle errors gracefully when the CBR data source is unavailable or returns errors, providing clear error messages via console output and returning appropriate exit codes (0 for success, non-zero for errors)
- **FR-009**: System MUST create the Parquet file with available exchange rate data even when some days are missing, and MUST include rows for all dates in the 7-day period with null rate values for missing days
- **FR-010**: System MUST validate that retrieved data contains valid date and numeric exchange rate values before saving

### Key Entities *(include if feature involves data)*

- **Exchange Rate Record**: Represents a single day's exchange rate data. Key attributes: date (the calendar date for this rate), exchange_rate_value (the RUB/USD exchange rate as a numeric value, which may be null for missing days), currency_pair (identifier for RUB/USD pair). The Parquet file MUST contain exactly one row per day in the 7-day period, with missing days having null rate values.
- **Report Metadata**: Represents information about the data extraction and report generation. Key attributes: report_date (the date when the extraction was performed), period_start (the earliest date in the data period), period_end (the latest date in the data period), data_source (identifier for CBR as the source). This metadata is stored as Parquet file-level metadata (key-value pairs) accessible via the Parquet file metadata API, not as data columns.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: System successfully extracts exchange rate data for at least 5 out of 7 requested days (accounting for potential missing weekend/holiday data)
- **SC-002**: Data extraction process completes within 30 seconds under normal network conditions
- **SC-003**: Parquet file is successfully created and contains all extracted exchange rate records with correct date and rate values
- **SC-004**: Parquet file includes metadata fields (report date and period) stored as file-level metadata that can be read and interpreted correctly via Parquet file metadata API
- **SC-005**: System handles data source unavailability errors by providing clear error messages via console output and returning non-zero exit codes without crashing
- **SC-006**: Saved Parquet file can be successfully read back and all data values match the originally extracted values

## Assumptions

- The CBR data source provides exchange rate data in a structured format (XML, JSON, or similar) that can be programmatically accessed
- Exchange rates are published daily on business days, and weekends/holidays may not have published rates
- The system has network access to reach the CBR website or API
- The system has write permissions to save files in the current working directory
- Parquet files are saved to the current working directory where the extraction command is executed
- Parquet file format is appropriate for the use case and compatible with downstream data processing needs
- The "last 7 days" refers to calendar days, and the system should attempt to retrieve data for all 7 days even if some may be unavailable
- The report date metadata should reflect when the extraction was performed, not when the exchange rates were published
- The period metadata should indicate the date range of the exchange rate data (start and end dates of the 7-day window)
