"""Exchange rate data model."""

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class ExchangeRateRecord:
    """
    Represents a single day's RUB/USD exchange rate data.
    
    Attributes:
        date: Calendar date for this exchange rate (YYYY-MM-DD format)
        exchange_rate_value: RUB/USD exchange rate as a numeric value.
            May be None for missing days (weekends/holidays).
        currency_pair: Identifier for the currency pair (always "RUB/USD")
    """
    date: date
    exchange_rate_value: Optional[float]
    currency_pair: str = "RUB/USD"


