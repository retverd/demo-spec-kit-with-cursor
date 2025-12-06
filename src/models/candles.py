"""Модель данных свечи для LQDT/TQTF (Мосбиржа)."""

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class CandleRecord:
    """
    Представляет дневную свечу (OHLCV) для инструмента LQDT на доске TQTF.

    Атрибуты:
        date: Дата свечи.
        open: Цена открытия (None если данных нет).
        high: Максимальная цена (None если данных нет).
        low: Минимальная цена (None если данных нет).
        close: Цена закрытия (None если данных нет).
        volume: Объём торгов (None если данных нет).
        instrument: Идентификатор инструмента, по умолчанию "LQDT".
        board: Код доски, по умолчанию "TQTF".
    """

    date: date
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    close: Optional[float]
    volume: Optional[float]
    instrument: str = "LQDT"
    board: str = "TQTF"
