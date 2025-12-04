# Tasks: Extract RUB/USD Exchange Rate from CBR

**Input**: Design documents from `/specs/001-cbr-exchange-rate/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are included per Constitution Principle 3 and 4 - all business functions must be tested.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below follow the single project structure from plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (src/models/, src/services/, src/cli/, src/utils/, tests/unit/, tests/integration/)
- [X] T002 Create requirements.txt with dependencies: requests>=2.31.0, pyarrow>=14.0.0, pytest>=7.4.0, pytest-mock>=3.11.0
- [X] T003 [P] Create README.md with installation and usage instructions
- [X] T004 [P] Create .gitignore for Python project
- [X] T005 [P] Create pytest.ini or pyproject.toml for test configuration

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core utilities that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 [P] Implement date_utils.py in src/utils/date_utils.py with get_last_7_days() function that returns list of 7 date objects
- [X] T007 [P] Implement validators.py in src/utils/validators.py with validate_date(), validate_rate(), and validate_records() functions per data-model.md validation rules
- [X] T008 [P] Create unit tests for date_utils in tests/unit/test_date_utils.py
- [X] T009 [P] Create unit tests for validators in tests/unit/test_validators.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Extract Exchange Rate Data from CBR (Priority: P1) 🎯 MVP

**Goal**: Retrieve the official RUB/USD exchange rate data for the last 7 days from the Central Bank of Russia (ЦБ РФ) website. The system connects to the CBR data source, requests exchange rate information for the specified period, and retrieves the data successfully.

**Independent Test**: Execute the extraction process and verify that exchange rate data for 7 consecutive days is successfully retrieved from the CBR source. Can be tested by running CBR client with mocked API responses.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Create unit test for CBR client in tests/unit/test_cbr_client.py with mocked XML responses (windows-1251 encoding)
- [X] T011 [P] [US1] Test CBR client error handling (404, 500, timeout) in tests/unit/test_cbr_client.py
- [X] T012 [P] [US1] Test CBR client date range handling and missing days in tests/unit/test_cbr_client.py

### Implementation for User Story 1

- [X] T013 [P] [US1] Create ExchangeRateRecord model in src/models/exchange_rate.py with date, exchange_rate_value (nullable), currency_pair attributes per data-model.md
- [X] T014 [US1] Implement CBRClient class in src/services/cbr_client.py with get_exchange_rates(start_date, end_date) method that calls XML_dynamic.asp API per contracts/cbr-api-contract.md. Note: Set timeout to align with SC-002 (30-second total requirement; contracts specify 15-second timeout which is appropriate)
- [X] T015 [US1] Implement XML parsing with windows-1251 decoding in src/services/cbr_client.py
- [X] T016 [US1] Implement date matching logic to fill missing days with null rates in src/services/cbr_client.py
- [X] T017 [US1] Implement error handling for CBR API (network errors, timeouts, invalid responses) with console output and exit codes in src/services/cbr_client.py. Note: Timeout settings should align with SC-002 (30-second total requirement; contracts specify 15-second timeout which is appropriate)
- [X] T018 [US1] Add logging for CBR client operations in src/services/cbr_client.py. Note: Error messages must be output to console (stderr) per FR-008 and CLI contract; logging can include console output for errors

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. Can extract exchange rate data from CBR API.

---

## Phase 4: User Story 2 - Save Data to Parquet Format with Metadata (Priority: P2)

**Goal**: Persist the extracted exchange rate data in a Parquet file format with associated metadata (report date and period). The system structures the data appropriately, includes metadata about when the report was generated and what time period it covers, and saves it to a Parquet file.

**Independent Test**: Verify that after data extraction, a Parquet file is created containing the exchange rate data and metadata fields (report date, period). Can be tested by creating Parquet file and reading it back to verify structure and metadata.

### Tests for User Story 2

- [X] T019 [P] [US2] Create unit test for Parquet writer in tests/unit/test_parquet_writer.py with test file creation and metadata storage
- [X] T020 [P] [US2] Test Parquet writer with null rate values in tests/unit/test_parquet_writer.py
- [X] T021 [P] [US2] Test Parquet filename generation with timestamp in tests/unit/test_parquet_writer.py
- [X] T022 [P] [US2] Test Parquet file metadata reading in tests/unit/test_parquet_writer.py

### Implementation for User Story 2

- [X] T023 [US2] Implement ParquetWriter class in src/services/parquet_writer.py with write_exchange_rates(records, metadata) method using pyarrow per research.md
- [X] T024 [US2] Implement Parquet file-level metadata storage (report_date, period_start, period_end, data_source) in src/services/parquet_writer.py
- [X] T025 [US2] Implement filename generation with pattern rub_usd_{period_start}_to_{period_end}_{timestamp}.parquet in src/services/parquet_writer.py
- [X] T026 [US2] Implement CLI entry point in src/cli/main.py with argparse for command-line interface per contracts/cli-contract.md
- [X] T027 [US2] Integrate CLI with CBR client and Parquet writer in src/cli/main.py to implement full extraction and save flow
- [X] T028 [US2] Implement exit codes (0 for success, 1-5 for errors) in src/cli/main.py per contracts/cli-contract.md
- [X] T029 [US2] Implement error handling with console output (stderr) in src/cli/main.py
- [X] T030 [US2] Add validation step before saving (FR-010) in src/cli/main.py using validators

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. Full CLI tool is functional.

---

## Phase 5: Integration & End-to-End Testing

**Purpose**: Verify complete system works end-to-end

- [X] T031 [P] Create integration test for end-to-end flow in tests/integration/test_end_to_end.py with mocked CBR API
- [X] T032 [P] Test integration with real CBR API (optional, may require network) in tests/integration/test_end_to_end.py
- [X] T033 [P] Test CLI command execution with various scenarios in tests/integration/test_end_to_end.py

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements and finalization

- [X] T034 [P] Update README.md with usage examples and installation instructions
- [X] T035 [P] Add code comments explaining "why" for complex logic (per Constitution Principle 1)
- [X] T036 [P] Code cleanup and refactoring to follow PEP 8 conventions
- [X] T037 [P] Verify all error scenarios are handled with appropriate exit codes
- [X] T038 [P] Run quickstart.md validation to ensure all examples work
- [X] T039 [P] Add type hints to all functions for better code quality
- [X] T040 [P] Create setup.py or pyproject.toml for package installation (if needed)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User Story 1 (P1) can start after Foundational
  - User Story 2 (P2) depends on User Story 1 (needs ExchangeRateRecord model and CBR client)
- **Integration (Phase 5)**: Depends on both User Stories 1 and 2
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on User Story 1 completion (needs ExchangeRateRecord model and CBR client to extract data before saving)

### Within Each User Story

- Tests (T010-T012, T019-T022) MUST be written and FAIL before implementation
- Models (T013) before services (T014-T018, T023-T025)
- Services before CLI integration (T026-T030)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks (T003-T005) marked [P] can run in parallel
- All Foundational tasks (T006-T009) marked [P] can run in parallel
- Tests for User Story 1 (T010-T012) can run in parallel
- Tests for User Story 2 (T019-T022) can run in parallel
- Model creation (T013) can run in parallel with test writing
- Polish tasks (T034-T040) can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Create unit test for CBR client in tests/unit/test_cbr_client.py"
Task: "Test CBR client error handling in tests/unit/test_cbr_client.py"
Task: "Test CBR client date range handling in tests/unit/test_cbr_client.py"

# Launch model and tests in parallel:
Task: "Create ExchangeRateRecord model in src/models/exchange_rate.py"
Task: "Create unit test for CBR client in tests/unit/test_cbr_client.py"
```

---

## Parallel Example: User Story 2

```bash
# Launch all tests for User Story 2 together:
Task: "Create unit test for Parquet writer in tests/unit/test_parquet_writer.py"
Task: "Test Parquet writer with null rate values in tests/unit/test_parquet_writer.py"
Task: "Test Parquet filename generation in tests/unit/test_parquet_writer.py"
Task: "Test Parquet file metadata reading in tests/unit/test_parquet_writer.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently - can extract data from CBR
5. Deploy/demo if ready (data extraction working)

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP - data extraction!)
3. Add User Story 2 → Test independently → Deploy/Demo (Complete CLI tool)
4. Add Integration tests → Validate end-to-end
5. Polish → Production ready

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (CBR client, models)
   - Developer B: Can work on User Story 2 tests in parallel (T019-T022)
3. After User Story 1 completes:
   - Developer A: User Story 2 implementation (Parquet writer, CLI)
   - Developer B: Integration tests
4. Both stories complete and integrate

---

## Notes

- [P] tasks = different files, no dependencies
- [US1], [US2] labels map tasks to specific user stories for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- User Story 1 delivers MVP (data extraction)
- User Story 2 completes the feature (data persistence)
- All tasks include exact file paths for clarity

---

## Task Summary

**Total Tasks**: 40

**By Phase**:

- Phase 1 (Setup): 5 tasks
- Phase 2 (Foundational): 4 tasks
- Phase 3 (User Story 1): 9 tasks (3 tests + 6 implementation)
- Phase 4 (User Story 2): 12 tasks (4 tests + 8 implementation)
- Phase 5 (Integration): 3 tasks
- Phase 6 (Polish): 7 tasks

**By User Story**:

- User Story 1 (P1): 9 tasks
- User Story 2 (P2): 12 tasks

**Parallel Opportunities**: 25 tasks marked [P] can run in parallel

**Suggested MVP Scope**: Phases 1-3 (Setup + Foundational + User Story 1) = 18 tasks

**Independent Test Criteria**:

- User Story 1: Execute CBR client with mocked API, verify 7 days of data retrieved
- User Story 2: Create Parquet file from test data, verify structure and metadata

**Format Validation**: ✅ All tasks follow checklist format with checkbox, ID, optional [P] marker, optional [Story] label, and file paths
