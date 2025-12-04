# Implementation Plan: Extract RUB/USD Exchange Rate from CBR

**Branch**: `001-cbr-exchange-rate` | **Date**: 2025-12-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-cbr-exchange-rate/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Extract RUB/USD exchange rate data for the last 7 days from the Central Bank of Russia (ЦБ РФ) website and save it to a Parquet file with metadata. The system will be a command-line tool that connects to the CBR data source using XML_dynamic.asp API (single request for date range), retrieves exchange rate information, validates the data, and persists it in Parquet format with file-level metadata (report date and period). Missing days will be represented as rows with null rate values.

## Technical Context

**Language/Version**: Python 3.14  
**Primary Dependencies**: requests (HTTP client), pyarrow (Parquet operations), datetime (stdlib, date handling)  
**Storage**: Parquet files (local filesystem)  
**Testing**: pytest  
**Target Platform**: Cross-platform (Windows, Linux, macOS) - CLI tool  
**Project Type**: single (CLI application)  
**Performance Goals**: Complete extraction and save within 30 seconds under normal network conditions (per SC-002). Single API request for date range improves performance compared to multiple requests.  
**Constraints**: Must handle network timeouts, missing data gracefully; console output with exit codes; save to current working directory  
**Scale/Scope**: Single-user CLI tool; processes 7 days of exchange rate data per execution

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle 1: Code Quality
- ✅ **PASS**: Code will be structured modularly (extraction service, Parquet writer, CLI interface)
- ✅ **PASS**: Clear naming conventions (Python PEP 8)
- ✅ **PASS**: Functions will be focused and single-purpose

### Principle 2: Repeatability
- ✅ **PASS**: Deterministic data extraction (same input = same output)
- ✅ **PASS**: Versioned dependencies (requirements.txt)
- ✅ **PASS**: Idempotent file creation (timestamped filenames prevent overwrites)

### Principle 3: Testing Standards
- ✅ **PASS**: pytest framework selected
- ✅ **PASS**: Tests will be isolated (mock CBR API responses)
- ✅ **PASS**: Fast execution (unit tests with mocks)

### Principle 4: Business Function Coverage
- ✅ **PASS**: Core extraction function will have tests
- ✅ **PASS**: Parquet file creation will have tests
- ✅ **PASS**: Error handling will have tests
- ✅ **PASS**: Data validation will have tests

### Principle 5: Documentation
- ✅ **PASS**: README with installation and usage instructions
- ✅ **PASS**: Code comments explaining "why" for complex logic
- ✅ **PASS**: Architecture decisions documented in plan

**GATE STATUS**: ✅ **PASS** - All principles satisfied

## Project Structure

### Documentation (this feature)

```text
specs/001-cbr-exchange-rate/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── models/
│   └── exchange_rate.py      # ExchangeRateRecord data model
├── services/
│   ├── cbr_client.py         # CBR API client for data extraction
│   └── parquet_writer.py     # Parquet file writer with metadata
├── cli/
│   └── main.py               # CLI entry point and argument parsing
└── utils/
    ├── date_utils.py         # Date range calculation utilities
    └── validators.py         # Data validation functions

tests/
├── unit/
│   ├── test_cbr_client.py
│   ├── test_parquet_writer.py
│   ├── test_validators.py
│   └── test_date_utils.py
└── integration/
    └── test_end_to_end.py    # Full extraction and save flow
```

**Structure Decision**: Single project structure chosen as this is a CLI tool. Code organized into models (data structures), services (business logic), CLI (user interface), and utils (helper functions). Tests mirror source structure with unit and integration test separation.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations - structure is simple and appropriate for a CLI tool.
