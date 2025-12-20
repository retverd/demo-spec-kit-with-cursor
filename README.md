# Финансовые выгрузки: CBR RUB/USD (Parquet) и MOEX LQDT/TQTF (XLSX)

CLI-инструмент поддерживает два сценария:

- Курсы RUB/USD за указанный период `--days` из API ЦБ РФ → Parquet.
- Дневные свечи LQDT/TQTF за указанный период `--days` из ISS‑API Мосбиржи → XLSX с именованием `lqdt_tqtf_{period_start}_to_{period_end}_{report_date}_{HHMMSS}.xlsx`.

## Установка

1. Убедитесь, что установлен Python 3.14+
2. Установите зависимости:

```bash
pip install -r requirements.txt
```

## Быстрый старт

> [!TIP]
> В Windows удобно использовать `py` вместо `python`, если `python` не добавлен в PATH.

- Курсы ЦБ (по умолчанию): `python -m src.cli.main --days 7`
- Явный вызов ЦБ: `python -m src.cli.main cbr --days 7`
- Свечи LQDT/TQTF → XLSX: `python -m src.cli.main moex-lqdt --days 7`

Ожидается:

- Код выхода `0` при успехе.
- Файл Parquet `rub_usd_{period_start}_to_{period_end}_{report_date}_{HHMMSS}.parquet` (сценарий CBR).
- Файл XLSX `lqdt_tqtf_{period_start}_to_{period_end}_{report_date}_{HHMMSS}.xlsx` с листом `candles` и колонками `Date, Open, High, Low, Close, Volume` (ровно `--days` строк по датам) для сценария MOEX.

## Коды выхода (общие для CLI)

- `0` — успех
- `1` — ошибка внешнего API (ЦБ/Мосбиржа) или HTTP‑статус 4xx/5xx
- `2` — сетевой таймаут/ошибка подключения
- `3` — некорректные/повреждённые данные от API
- `4` — ошибка файловой системы при записи
- `5` — ошибка валидации данных

## Разработка

### Структура проекта

```txt
src/
├── models/
│   ├── exchange_rate.py      # ExchangeRateRecord (CBR)
│   └── candles.py            # CandleRecord (MOEX)
├── services/
│   ├── cbr_client.py         # Клиент API ЦБ РФ (Parquet)
│   ├── moex_client.py        # Клиент ISS‑API Мосбиржи (XLSX)
│   ├── parquet_writer.py     # Запись Parquet с метаданными
│   └── xlsx_writer.py        # Запись XLSX с OHLCV
├── cli/
│   └── main.py               # Подкоманды cbr / moex-lqdt
└── utils/
    ├── date_utils.py         # Диапазоны дат (7 дней)
    └── validators.py         # Проверка курсов и свечей

tests/
├── unit/                     # Юнит-тесты CBR и MOEX
└── integration/              # E2E-поток для обеих подкоманд
```

### Запуск тестов

```bash
pytest
```

### Реальные прогоны против API (опционально)

По умолчанию тесты против реальных CBR/MOEX пропускаются, чтобы набор был стабильным без сети.
Чтобы включить:

```bash
# PowerShell
$env:RUN_REAL_API="1"; python -m pytest -q tests/integration/test_real_api_runs.py
```

Также доступен перф‑смоук для `moex-lqdt` (по умолчанию порог 20 сек), параметры:

- `MOEX_PERF_MAX_SECONDS` — порог времени (сек)
- `MOEX_PERF_DAYS` — сколько дней запрашивать (по умолчанию 7)

## Обработка ошибок

Все ошибки логируются и выводятся в stderr на русском языке (сообщения о сетевых таймаутах, HTTP‑ошибках API, некорректных данных, ошибках ФС и валидации).
