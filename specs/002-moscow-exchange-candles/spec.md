# Feature Specification: Extract Daily Candles for LQDT from Moscow Exchange

**Feature Branch**: `002-moscow-exchange-candles`  
**Created**: 2025-12-04  
**Status**: Draft  
**Input**: User description: "Добавить функционал, который извлекает дневные свечи для инструмента LQDT с доски TQTF через API Мосбиржи, и сохраняет его в xlsx-файл."

> **Примечание**: Согласно конституции проекта, все спецификации должны быть написаны на русском языке.

## Clarifications

### Session 2025-12-04

- Q: Какой период данных о свечах должен запрашиваться для инструмента LQDT с доски TQTF через API Мосбиржи? → A: Система должна запрашивать данные за последние 7 календарных дней по аналогии с уже существующим функционалом.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Extract Daily Candles from Moscow Exchange API (Priority: P1)

Пользователю необходимо получить дневные свечи (OHLCV данные: Open, High, Low, Close, Volume) для инструмента LQDT с торговой доски TQTF через API Московской биржи за последние 7 календарных дней. Система должна подключиться к API Мосбиржи, запросить данные о свечах за последние 7 дней, и успешно извлечь данные.

**Why this priority**: Это основная функциональность - без извлечения данных никакие другие операции невозможны. Это обеспечивает немедленную ценность, предоставляя доступ к данным о свечах из официального источника.

**Independent Test**: Можно полностью протестировать, выполнив процесс извлечения и проверив, что данные о свечах за указанный период успешно получены из API Мосбиржи. Тест обеспечивает ценность, подтверждая, что система может получить доступ к официальным финансовым данным.

**Acceptance Scenarios**:

1. **Given** система готова к извлечению данных, **When** выполняется запрос дневных свечей для инструмента LQDT с доски TQTF за последние 7 дней, **Then** система успешно подключается к API Мосбиржи и извлекает записи о свечах за каждый день в 7-дневном периоде
2. **Given** существуют валидные данные о свечах за запрошенный период, **When** процесс извлечения завершается, **Then** система возвращает данные, содержащие дату и значения OHLCV (Open, High, Low, Close, Volume) для каждого дня в периоде
3. **Given** API Мосбиржи недоступен, **When** предпринимается попытка извлечения данных, **Then** система выводит понятное сообщение об ошибке в консоль и возвращает ненулевой код выхода

---

### User Story 2 - Save Candles Data to XLSX Format (Priority: P2)

Пользователю необходимо, чтобы извлеченные данные о свечах были сохранены в файл формата XLSX. Система должна структурировать данные соответствующим образом, включить все необходимые поля (Date, Open, High, Low, Close, Volume), и сохранить их в файл XLSX.

**Why this priority**: Сохранение данных необходимо для последующего анализа и исторического отслеживания. Формат XLSX обеспечивает удобство работы с данными в табличных редакторах и совместимость с различными инструментами анализа.

**Independent Test**: Можно полностью протестировать, проверив, что после извлечения данных создается файл XLSX, содержащий данные о свечах со всеми необходимыми полями (Date, Open, High, Low, Close, Volume). Тест обеспечивает ценность, подтверждая, что данные правильно структурированы и доступны для будущего использования.

**Acceptance Scenarios**:

1. **Given** данные о свечах были успешно извлечены, **When** выполняется операция сохранения, **Then** создается файл XLSX, содержащий строки для всех дат в периоде с соответствующими значениями OHLCV
2. **Given** процесс извлечения данных завершился, **When** выполняется сохранение в XLSX, **Then** файл включает все необходимые колонки: Date, Open, High, Low, Close, Volume
3. **Given** существуют валидные данные, **When** файл XLSX сохраняется, **Then** файл может быть успешно открыт в табличном редакторе и все данные соответствуют извлеченным значениям

---

### Edge Cases

- Когда API Мосбиржи временно недоступен или возвращает ошибку, система выводит понятное сообщение об ошибке в консоль и возвращает ненулевой код выхода
- Когда данные о свечах отсутствуют для одного или нескольких дней в запрошенном периоде, система создает файл XLSX со строками для всех дат в периоде, где отсутствующие дни имеют значения NULL
- Когда запрошенный период включает выходные дни или праздники, когда торговля не ведется, система создает файл XLSX со строками для всех дат в периоде, где дни без торговли имеют значения NULL
- Когда во время извлечения данных возникает сетевой таймаут или сбой подключения, система выводит понятное сообщение об ошибке на русском языке в консоль и завершает работу с ненулевым кодом выхода в соответствии с FR-007 и SC-004
- Когда файловая система заполнена или отсутствуют права на запись при сохранении файла XLSX, система выводит понятное сообщение об ошибке на русском языке в консоль и завершает работу с ненулевым кодом выхода, соответствующим ошибке файловой системы, не создавая частично записанных или повреждённых файлов
- Когда API Мосбиржи возвращает невалидные или некорректно сформированные данные, система рассматривает такой ответ как ошибочный, логирует проблему, выводит понятное сообщение об ошибке на русском языке и завершает работу с ненулевым кодом выхода в соответствии с FR-007 и FR-009
- Когда система запускается несколько раз для одного и того же периода, она создает новый файл с именем, включающим период дат и временную метку извлечения (например, `lqdt_tqtf_2025-11-25_to_2025-12-01_2025-12-02_143022.xlsx`) для сохранения истории запусков
- Когда инструмент LQDT не найден на доске TQTF или не имеет данных за запрошенный период, система выводит понятное сообщение об ошибке в консоль и возвращает ненулевой код выхода

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST connect to Moscow Exchange API to retrieve candle data
- **FR-002**: System MUST extract daily candles (OHLCV data) for instrument LQDT from board TQTF for the last 7 calendar days: [today, today - 6] (inclusive, 7 days total)
- **FR-003**: System MUST retrieve candle records that include at minimum: Date, Open price, High price, Low price, Close price, and Volume
- **FR-004**: System MUST save the extracted data to an XLSX file format in the current working directory (where the command is executed)
- **FR-005**: System MUST create a new XLSX file with a filename that includes the period dates (start and end) and extraction timestamp when run multiple times for the same period (e.g., `lqdt_tqtf_2025-11-25_to_2025-12-01_2025-12-02_143022.xlsx`) to preserve historical runs
- **FR-006**: System MUST include all required columns in the XLSX file: Date, Open, High, Low, Close, Volume
- **FR-007**: System MUST handle errors gracefully when the Moscow Exchange API is unavailable or returns errors, providing clear error messages via console output and returning appropriate exit codes (0 for success, non-zero for errors)
- **FR-008**: System MUST create the XLSX file with available candle data even when some days are missing, and MUST include rows for all 7 dates in the period with null values for missing days
- **FR-009**: System MUST validate that retrieved data contains valid date and numeric OHLCV values before saving
- **FR-010**: System MUST handle cases where instrument LQDT is not found on board TQTF or has no data for the requested period by providing appropriate error messages

### Key Entities *(include if feature involves data)*

- **Candle Record**: Represents a single day's OHLCV candle data. Key attributes: date (the calendar date for this candle), open (opening price as a numeric value), high (highest price as a numeric value), low (lowest price as a numeric value), close (closing price as a numeric value), volume (trading volume as a numeric value, which may be null/zero for missing days), instrument (identifier for LQDT), board (identifier for TQTF). The XLSX file MUST contain exactly one row per day in the 7-day period, with missing days having empty or null values.

### Localization Requirements

- **LR-001**: Все пользовательские сообщения (включая сообщения об ошибках и вывод CLI) для функциональности извлечения и сохранения свечей LQDT/TQTF ДОЛЖНЫ быть на русском языке в соответствии с Принципом 6 конституции проекта.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Data extraction process completes within 20 seconds under normal network conditions
- **SC-002**: XLSX file is successfully created and contains all extracted candle records with correct date and OHLCV values
- **SC-003**: XLSX file includes all required columns (Date, Open, High, Low, Close, Volume) and can be opened correctly in standard spreadsheet applications
- **SC-004**: System handles API unavailability errors by providing clear error messages via console output and returning non-zero exit codes without crashing
- **SC-005**: Saved XLSX file can be successfully opened in spreadsheet applications and all data values match the originally extracted values
- **SC-006**: System handles cases where instrument or board is invalid by providing clear error messages and returning appropriate exit codes

## Assumptions

- The Moscow Exchange API provides candle (OHLCV) data in a structured format (JSON, XML, or similar) that can be programmatically accessed
- Daily candles are available for trading days, and weekends/holidays may not have candle data when markets are closed
- The system has network access to reach the Moscow Exchange API
- The system has write permissions to save files in the current working directory
- XLSX files are saved to the current working directory where the extraction command is executed
- XLSX file format is appropriate for the use case and compatible with downstream data processing needs
- The date range for extraction is the last 7 calendar days: [today, today - 6] (inclusive, 7 days total)
- Instrument LQDT exists on board TQTF and has historical candle data available
- The Moscow Exchange API is publicly accessible so no authentication required
- The API supports querying by instrument code (LQDT), board code (TQTF), and date range
