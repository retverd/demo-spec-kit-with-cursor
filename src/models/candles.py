"""Candle data model for MOEX LQDT/TQTF daily candles."""

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class CandleRecord:
    """
    Represents a single day's OHLCV candle for LQDT on board TQTF.

    Attributes:
        date: Calendar date of the candle.
        open: Opening price (None if no data).
        high: Highest price (None if no data).
        low: Lowest price (None if no data).
        close: Closing price (None if no data).
        volume: Trading volume (None if no data).
        instrument: Instrument identifier, defaults to "LQDT".
        board: Board identifier, defaults to "TQTF".
    """

    date: date
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    close: Optional[float]
    volume: Optional[float]
    instrument: str = "LQDT"
    board: str = "TQTF"
