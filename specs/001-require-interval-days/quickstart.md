# Quickstart: обязательный `--days` для CLI

**Feature**: `001-require-interval-days`  
**Date**: 2025-12-11

## Подготовка

1. Установите зависимости (Python 3.14+):

```bash
pip install -r requirements.txt
```

2. Запустите из корня репозитория.

## Использование

### Курсы CBR → Parquet

```bash
python -m src.cli.main cbr --days 5
```

Ожидается файл `rub_usd_<start>_to_<end>_<report_date>_<HHMMSS>.parquet` с периодом последних 5 дней (включая сегодня).

### Свечи MOEX LQDT/TQTF → XLSX

```bash
python -m src.cli.main moex-lqdt --days 7
```

Ожидается файл `lqdt_tqtf_<start>_to_<end>_<report_date>_<HHMMSS>.xlsx` (лист `candles`) с периодом последних 7 дней (включая сегодня).

### Ошибки ввода

```bash
python -m src.cli.main --days 0         # или без --days
```

Выведет сообщение о требовании целого значения 1–365 и завершится кодом 5 без сетевых запросов и файлов.

## Коды выхода

- `0` — успех
- `1` — ошибка внешнего API
- `2` — таймаут/сеть
- `3` — некорректные данные от API
- `4` — ошибка файловой системы
- `5` — ошибка валидации (включая отсутствие/некорректный `--days`)
