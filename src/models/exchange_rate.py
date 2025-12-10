"""Модель данных курса RUB/USD."""

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class ExchangeRateRecord:
    """
    Представляет курс RUB/USD за один день.

    Атрибуты:
        date: Дата (YYYY-MM-DD).
        exchange_rate_value: Значение курса как численное значение; может быть None для пропусков.
        currency_pair: Валютная пара, всегда "RUB/USD".
    """

    date: date
    exchange_rate_value: Optional[float]
    currency_pair: str = "RUB/USD"
