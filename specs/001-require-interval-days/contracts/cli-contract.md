# CLI Contract: обязательный параметр `--days` для CBR и MOEX

**Date**: 2025-12-11  
**Feature**: 001-require-interval-days

## Command Interface

### Command Names

- `cbr` (значение по умолчанию при отсутствии подкоманды)
- `moex-lqdt`

### Usage

```bash
python -m src.cli.main cbr --days <N>
python -m src.cli.main moex-lqdt --days <N>
# краткая форма
python -m src.cli.main --days <N>   # эквивалентно подкоманде cbr
```

### Arguments

| Name | Required | Type | Description | Validation / Errors |
|------|----------|------|-------------|---------------------|
| `--days`, `-d` | Yes | int | Длина периода в днях | Обязательно; целое число 1–365. Нарушение → сообщение об ошибке и код 5, без сетевых запросов |

### Behavior

1. CLI валидирует `--days` (целое, 1–365); при ошибке завершает работу с кодом 5 и понятным сообщением.
2. Рассчитывает период: `period_start = today - (days - 1)`, `period_end = today` (локальная дата); выводит даты в логах.
3. Для `cbr`:
   - Запрашивает курсы за период у CBR, валидирует записи.
   - Создаёт Parquet с метаданными и именем `rub_usd_{period_start}_to_{period_end}_{report_date}_{HHMMSS}.parquet`.
4. Для `moex-lqdt`:
   - Запрашивает дневные свечи LQDT/TQTF у MOEX ISS за период, валидирует записи.
   - Создаёт XLSX `lqdt_tqtf_{period_start}_to_{period_end}_{report_date}_{HHMMSS}.xlsx` (лист `candles`, колонки `Date, Open, High, Low, Close, Volume`).
5. Ошибки ввода не вызывают сетевые обращения и не создают файлов.

### Exit Codes

- `0` — успех
- `1` — ошибка внешнего API (HTTP 4xx/5xx, бизнес-ошибки)
- `2` — таймаут/сетевая ошибка
- `3` — некорректные/повреждённые данные от API
- `4` — ошибка файловой системы
- `5` — ошибка валидации (включая отсутствие/некорректный `--days`)

### Output

**Success**:

- Консоль: сообщение об успешном создании файла + отображение периода.
- Файл: Parquet (CBR) или XLSX (MOEX) в рабочей директории, имя содержит период и дату отчёта.
- Код выхода: `0`.

**Error**:

- Консоль (stderr): понятное сообщение (на русском) с причиной.
- Файл: не создаётся.
- Код выхода: см. таблицу Exit Codes.

### Examples

Успешный запуск CBR на 5 дней:

```bash
$ python -m src.cli.main cbr --days 5
Успешно создан rub_usd_2025-12-07_to_2025-12-11_2025-12-11_143000.parquet
```

Ошибка отсутствия параметра:

```bash
$ python -m src.cli.main moex-lqdt
Error: Параметр --days обязателен (целое число 1–365)
$ echo $LASTEXITCODE
5
```
