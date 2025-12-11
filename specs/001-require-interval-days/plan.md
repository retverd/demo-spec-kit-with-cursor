# Implementation Plan: Обязательный ввод длительности интервала в CLI

**Branch**: `001-require-interval-days` | **Date**: 2025-12-11 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-require-interval-days/spec.md`

> Все артефакты должны быть на русском языке (Конституция, Принцип 6).

## Summary

Для подкоманд `cbr` и `moex-lqdt` параметр длительности в днях становится обязательным: пользователь передаёт `--days N`, CLI валидирует диапазон (1–365) до любых сетевых вызовов, рассчитывает период `[today-(N-1), today]`, отражает его в логах и метаданных файлов, а при ошибке ввода завершает работу с понятным сообщением и ненулевым кодом выхода без обращения к внешним API.

## Technical Context

**Language/Version**: Python 3.14  
**Primary Dependencies**:

- `requests` — HTTP-клиент для CBR и MOEX;
- `pyarrow` — запись Parquet для CBR;
- `openpyxl` — запись XLSX для MOEX;
- `pandas` — вспомогательные операции с данными (зависимость проекта);
- `argparse`, `logging` — стандартная библиотека.
**Storage**: Локальные файлы Parquet/XLSX в рабочей директории.  
**Testing**: `pytest` + `pytest-mock`; мокирование HTTP/ФС в unit, интеграционные проверки CLI.  
**Target Platform**: Кроссплатформенный CLI (Windows / Linux / macOS).  
**Project Type**: Single CLI-проект (`src/` + `tests/`).  
**Constraints**:
- `--days` обязателен для `cbr` и `moex-lqdt`, допустимый диапазон 1–365 (валидация до сети);
- Конечная дата всегда `date.today()` (локальная), старт = `today - (days - 1)`; период включителен;
- Сообщения об ошибках и логи — на русском языке; коды выхода совместимы с текущими (ошибки ввода → EXIT_VALIDATION_ERROR=5);
- Метаданные файлов и имена должны отражать фактический период.
**Scale/Scope**: Две подкоманды CLI, до 365 записей за запуск; вывод остаётся в локальной ФС.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- ✅ Все артефакты (план, спека, исследования) ведутся на русском языке.
- ✅ План тестирования включает интеграционные сценарии CLI; для внешних систем будут отдельные проверки с реальными API CBR/MOEX и перф-наблюдением только на таких интеграциях.
- ✅ Независимые компоненты (CBR, MOEX) тестируются автономно; общие утилиты покрываются отдельными юнитами без перекрёстных зависимостей.
- ✅ Ключевые бизнес-функции (выгрузка курсов и свечей, вычисление периода, запись файлов, ошибки ввода) покрываются интеграционными и негативными сценариями.
- ✅ Воспроизводимость: зависимости зафиксированы в `requirements.txt`/`pyproject.toml`; генерация файлов идемпотентна и не перезаписывает существующие файлы.

**GATE STATUS (pre-Phase 0): PASS** — нарушений не выявлено.  
**GATE STATUS (post-Phase 1 design): PASS** — артефакты (research/data-model/contracts/quickstart) оформлены на русском, интеграционные проверки с реальными API CBR/MOEX запланированы отдельно от unit-тестов.

## Project Structure

### Documentation (this feature)

```text
specs/001-require-interval-days/
├── plan.md              # Этот файл (вывод команды /speckit.plan)
├── spec.md              # Спецификация фичи
├── research.md          # Phase 0: решения по требованиям к days/периоду
├── data-model.md        # Phase 1: сущности days/период/артефакты
├── quickstart.md        # Phase 1: примеры запуска CLI с --days
├── contracts/
│   └── cli-contract.md  # Phase 1: контракт CLI (аргументы, коды выхода)
├── checklists/
│   └── requirements.md  # Уже существует
└── tasks.md             # Создаётся /speckit.tasks (не этим шагом)
```

### Source Code (repository root)

```text
src/
├── cli/
│   └── main.py          # Добавить required --days, единый парсинг и вывод периода
├── utils/
│   ├── date_utils.py    # Обобщить расчёт диапазона на N дней
│   └── validators.py    # Добавить валидацию входного параметра days и проверок периода
├── services/
│   ├── cbr_client.py    # Использует рассчитанный период (без логики периода внутри)
│   └── moex_client.py   # Аналогично
├── models/              # Без изменений (данные остаются прежними)
tests/
├── unit/
│   ├── test_date_utils.py
│   ├── test_validators.py
│   └── test_cli_main.py # Добавить/обновить для --days (новый файл при необходимости)
└── integration/
    └── test_end_to_end.py # Обновить сценарии CLI с обязательным days
```

**Structure Decision**: остаёмся в одном CLI-проекте; изменения локализованы в слое парсинга аргументов, утилитах дат и проверках, с минимальными правками сервисов/тестов.

## Complexity Tracking

Нарушений конституции не планируется; таблица не требуется.
