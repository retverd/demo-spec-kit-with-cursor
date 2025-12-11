# Data Model: обязательный параметр длительности (`--days`)

**Date**: 2025-12-11  
**Feature**: `001-require-interval-days`

## Overview

Новый обязательный параметр `--days` определяет длину периода для обеих подкоманд CLI (`cbr`, `moex-lqdt`). Период `[period_start, period_end]` используется при запросах к внешним API, валидации данных и формировании метаданных/имён выходных файлов Parquet (CBR) и XLSX (MOEX).

## Entities

### Interval Request (CLI Input)

**Purpose**: Пользовательский ввод, формирующий длительность периода.

| Field | Type | Nullable | Description | Validation Rules |
|-------|------|----------|-------------|------------------|
| `command` | enum (`cbr` \| `moex-lqdt`) | No | Целевая подкоманда | Должен быть одним из поддерживаемых значений |
| `days` | int | No | Длина периода в днях | Обязателен, целое число в диапазоне 1–365 |

### Date Interval

**Purpose**: Рассчитанный период выгрузки.

| Field | Type | Nullable | Description | Validation Rules |
|-------|------|----------|-------------|------------------|
| `period_start` | date | No | `today - (days - 1)` | `period_start <= period_end`, включает день запуска |
| `period_end` | date | No | `date.today()` | Совпадает с текущей локальной датой |
| `days` | int | No | Количество календарных дней | Совпадает с входным `days` |

**Derived constraints**:

- Множество дат периода имеет размер `days` и упорядочено по возрастанию.
- Для CBR и MOEX ожидается по одной записи на каждую дату периода.

### Report Metadata (выходные файлы)

**Purpose**: Фиксирует параметры запуска и периода в создаваемых файлах.

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `report_date` | string (ISO) | No | Дата формирования файла |
| `period_start` | string (ISO) | No | Начало периода (из Date Interval) |
| `period_end` | string (ISO) | No | Конец периода (из Date Interval) |
| `data_source` | string | No | `CBR` для Parquet, `MOEX-ISS` для XLSX |

**Constraints**:

- Метаданные и имя файла должны содержать фактические `period_start`/`period_end`.
- `period_start`/`period_end` согласованы с данными записей (CBR и MOEX).

### Output Artifacts

**Parquet (CBR)**: 1 строка на дату периода с полями `date`, `exchange_rate_value`, `currency_pair`.  
**XLSX (MOEX)**: 1 строка на дату периода с колонками `Date, Open, High, Low, Close, Volume`.  
**Filename patterns**: `rub_usd_{period_start}_to_{period_end}_{report_date}_{HHMMSS}.parquet`, `lqdt_tqtf_{period_start}_to_{period_end}_{report_date}_{HHMMSS}.xlsx`.

## Validation Rules

1. `days` обязателен и находится в диапазоне 1–365; валидация выполняется до сетевых запросов.
2. `period_start = today - (days - 1)`, `period_end = today`; `period_start <= period_end`.
3. Количество записей данных (CBR или MOEX) строго равно `days`; каждая дата периода представлена один раз.
4. Метаданные и имена файлов содержат те же `period_start`/`period_end`, что использовались при запросе и валидации.

## Relationships

- Interval Request → Date Interval (детерминированный расчёт по `days`).
- Date Interval → запросы внешних API (границы периода) и → валидаторы (ожидаемое число записей).
- Date Interval → Report Metadata → имена файлов/ключи метаданных.

## State Transitions

Данные неизменяемы: каждый запуск CLI создаёт новый файл с уникальным именем; изменение `days` формирует новый Date Interval и новый артефакт.
