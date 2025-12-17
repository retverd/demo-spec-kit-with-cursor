# Tasks: Обязательный ввод длительности интервала в CLI

**Input**: Design documents from `/specs/001-require-interval-days/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli-contract.md, quickstart.md

> Все задачи и комментарии на русском языке.

**Tests**: Тестовые задачи включены, так как спецификация требует независимые проверки CLI.

**Organization**: Задачи сгруппированы по пользовательским историям.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Можно выполнять параллельно (разные файлы, нет зависимостей).
- **[Story]**: US1/US2/US3 для соответствующей пользовательской истории.
- Все описания содержат путь к файлу.

## Path Conventions

- Single project: `src/`, `tests/` в корне.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Подготовка окружения и зависимостей.

- [X] T001 Проверить/зафиксировать зависимости в `requirements.txt` (requests, pyarrow, openpyxl, pandas).
- [X] T002 Настроить базовую конфигурацию логирования CLI в `src/cli/main.py` (формат с датой/уровнем).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Общие утилиты и валидации, блокирующие все истории.
**⚠️ CRITICAL**: Никакая пользовательская история не начинается до завершения этой фазы.

- [X] T003 Реализовать расчёт периода в `src/utils/date_utils.py` (today, period_start = today-(days-1)).
- [X] T004 [P] Добавить валидацию `days` (1–365, целое) в `src/utils/validators.py`.
- [X] T005 Настроить константы/коды выхода (EXIT_VALIDATION_ERROR=5) и единый хелпер ошибок в `src/cli/main.py`.
- [X] T006 [P] Подготовить общий вывод периода в логах/сообщениях в `src/cli/main.py` (start/end как строки).

---

## Phase 3: User Story 1 - Курс CBR с обязательным числом дней (Priority: P1) 🎯 MVP

**Goal**: Команда `cbr` требует `--days`, считает период, формирует Parquet с метаданными.
**Independent Test**: `python -m src.cli.main cbr --days 5` создаёт Parquet за 5 дней, логи/имя файла отражают период, код выхода 0.

### Tests for User Story 1

- [X] T007 [P] [US1] Добавить положительные проверки расчёта периода в `tests/unit/test_date_utils.py`.
- [X] T008 [P] [US1] Покрыть CLI `cbr --days` юнит-тестами парсинга/логирования в `tests/unit/test_cli_main.py`.
- [X] T025 [P] [US1] Расширить юнит-тесты на граничные случаи (`--days 365`, смена месяца/високосный день) в `tests/unit/test_date_utils.py` и `tests/unit/test_cli_main.py`.

### Implementation for User Story 1

- [X] T009 [P] [US1] Обновить парсер/обработчик `cbr` в `src/cli/main.py`: обязательный `--days`, расчёт периода, вывод дат до сетевых вызовов.
- [X] T010 [P] [US1] Принять период в `src/services/cbr_client.py`, передавать границы в запросы и включать в метаданные/имя Parquet.
- [X] T011 [US1] Расширить интеграционный сценарий CBR с `--days` в `tests/integration/test_end_to_end.py` (проверка периода и имени файла).

**Checkpoint**: User Story 1 работает и тестируется независимо.

---

## Phase 4: User Story 2 - Свечи MOEX с обязательным числом дней (Priority: P2)

**Goal**: Команда `moex-lqdt` требует `--days`, считает период, формирует XLSX с метаданными.
**Independent Test**: `python -m src.cli.main moex-lqdt --days 7` создаёт XLSX за 7 дней, логи/имя файла отражают период, код выхода 0.

### Tests for User Story 2

- [X] T012 [P] [US2] Добавить юнит-тесты CLI `moex-lqdt --days` для парсинга/логирования в `tests/unit/test_cli_main.py`.

### Implementation for User Story 2

- [X] T013 [P] [US2] Обновить обработчик `moex-lqdt` в `src/cli/main.py`: обязательный `--days`, расчёт периода, вывод дат.
- [X] T014 [P] [US2] Принять период в `src/services/moex_client.py`, передавать границы в запросы и включать в метаданные/имя XLSX.
- [X] T015 [US2] Расширить интеграционный сценарий MOEX с `--days` в `tests/integration/test_end_to_end.py` (проверка периода, имени XLSX и листа `candles`).

**Checkpoint**: User Stories 1 и 2 работают и тестируются независимо.

---

## Phase 5: User Story 3 - Ошибки неверной длительности (Priority: P3)

**Goal**: Некорректные/отсутствующие `--days` завершают CLI с сообщением об ошибке и кодом 5 без сетевых вызовов/файлов.
**Independent Test**: Запуск `cbr` или `moex-lqdt` без/с неверным `--days` возвращает сообщение, код 5, файлы не создаются.

### Tests for User Story 3

- [X] T016 [P] [US3] Добавить негативные проверки диапазона/типа `days` в `tests/unit/test_validators.py`.
- [X] T017 [P] [US3] Добавить юнит-тесты CLI ошибок (`--days 0`, отсутствует, нецелое) в `tests/unit/test_cli_main.py` (код 5, без вызовов сервисов).

### Implementation for User Story 3

- [X] T018 [P] [US3] Реализовать обработку ошибок ввода/выход код 5 в `src/cli/main.py` (русские сообщения, без сетевых вызовов).
- [X] T019 [US3] Добавить интеграционные сценарии ошибочного ввода в `tests/integration/test_end_to_end.py` (нет файлов, код 5).

**Checkpoint**: Все ошибки ввода корректно обрабатываются и тестируются независимо.

---

## Phase 6: Реальные интеграции и регрессия (Конституция: Принцип 3)

- [ ] T022 [US1] Прогнать `python -m src.cli.main cbr --days {1,7,30}` против реального API CBR; зафиксировать время отклика, пропускную способность и корректность периода в логах/выходных Parquet.
- [ ] T023 [US2] Прогнать `python -m src.cli.main moex-lqdt --days {1,7,30}` против реального API MOEX; зафиксировать время отклика, пропускную способность и корректность периода в логах/выходных XLSX.
- [ ] T024 Регрессионный прогон существующих сценариев/форматов для `cbr` и `moex-lqdt`: сравнить структуру файлов, коды выхода и именование с эталонными выборками после добавления обязательного `--days`.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Документация и финальные проверки.

- [ ] T020 [P] Синхронизировать примеры и коды выхода в `specs/001-require-interval-days/quickstart.md` с финальной реализацией.
- [ ] T021 Провести быстрый прогон `python -m src.cli.main --help` и обновить подсказки/описания в `src/cli/main.py`, если требуется.

---

## Dependencies & Execution Order

- Setup (Phase 1) → Foundational (Phase 2) → US1 (P1) → US2 (P2) → US3 (P3) → Polish.
- Истории независимы после Foundational; US2/US3 могут идти параллельно при готовом фундаменте, но MVP = US1.

### User Story Dependencies

- User Story 1 (P1): зависит от Foundational.
- User Story 2 (P2): зависит от Foundational; опирается на общие утилиты, но не на реализацию US1.
- User Story 3 (P3): зависит от Foundational; использует общие валидаторы и CLI обработку.

### Within Each User Story

- Тесты пишутся и падают до реализации.
- Валидация/утилиты → обновление CLI → сервисы → интеграционные проверки.

### Parallel Opportunities

- Foundational: T004 и T006 могут выполняться параллельно.
- US1: T007/T008 и T009/T010 можно делать параллельно (разные файлы), затем T011.
- US2: T012 и T013/T014 параллельно, затем T015.
- US3: T016/T017 параллельно, затем T018/T019.

### Parallel Example: User Story 1

```bash
# Параллельные задачи для US1
T007: tests/unit/test_date_utils.py
T008: tests/unit/test_cli_main.py
T009: src/cli/main.py
T010: src/services/cbr_client.py
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Завершить Setup + Foundational.
2. Реализовать US1 (CLI cbr с обязательным `--days`).
3. Прогнать юнит и интеграцию для US1.
4. Демонстрация/деплой MVP.

### Incremental Delivery

1. Setup + Foundational → база.
2. US1 → тесты/демо.
3. US2 → тесты/демо.
4. US3 → тесты/демо.

### Parallel Team Strategy

- После Foundational: отдельные исполнители на US1, US2, US3.
- Координация только по общим утилитам/CLI интерфейсу.

---

## Notes

- [P] = разные файлы, нет незавершённых зависимостей.
- Каждая история тестируема автономно по критериям выше.
- Проверять, что ошибки валидации срабатывают до сетевых вызовов.
