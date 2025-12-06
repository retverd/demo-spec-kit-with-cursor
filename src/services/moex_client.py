"""MOEX ISS API client for LQDT/TQTF daily candles."""

import logging
import sys
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

import requests

from src.models.candles import CandleRecord

logger = logging.getLogger(__name__)


class MoexClientError(Exception):
    """Exception raised for MOEX client errors."""
    pass


class MoexClient:
    """
    Client for retrieving daily OHLCV candles for LQDT/TQTF from MOEX ISS API.
    """
    
    BASE_URL = "https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQTF/securities/LQDT/candles.json"
    TIMEOUT_SECONDS = 15
    EXPECTED_BOARD = "TQTF"
    INSTRUMENT = "LQDT"
    
    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()
    
    def get_daily_candles(self, start_date: date, end_date: date) -> List[CandleRecord]:
        """
        Retrieve daily candles for the given period.
        
        Returns:
            List of CandleRecord with one entry per date in [start_date, end_date].
        """
        params = {
            "from": start_date.isoformat(),
            "till": end_date.isoformat(),
            "interval": 24,
        }
        try:
            logger.info("Запрос свечей LQDT/TQTF: %s - %s", start_date, end_date)
            response = self.session.get(self.BASE_URL, params=params, timeout=self.TIMEOUT_SECONDS)
            response.raise_for_status()
            payload = response.json()
            return self._parse_payload(payload, start_date, end_date)
        except requests.Timeout as e:
            msg = "Таймаут при обращении к API Мосбиржи."
            logger.error(msg)
            print(msg, file=sys.stderr)
            raise MoexClientError(msg) from e
        except requests.ConnectionError as e:
            msg = "Сетевая ошибка при обращении к API Мосбиржи."
            logger.error(msg)
            print(msg, file=sys.stderr)
            raise MoexClientError(msg) from e
        except requests.HTTPError as e:
            status = e.response.status_code if getattr(e, "response", None) else "unknown"
            msg = f"API Мосбиржи вернуло ошибку HTTP {status}"
            logger.error(msg)
            print(msg, file=sys.stderr)
            raise MoexClientError(msg) from e
        except ValueError as e:
            msg = "Некорректный JSON от API Мосбиржи."
            logger.error(msg)
            print(msg, file=sys.stderr)
            raise MoexClientError(msg) from e
        except KeyError as e:
            msg = f"Ответ API Мосбиржи не содержит ожидаемых данных: отсутствует {e}"
            logger.error(msg)
            print(msg, file=sys.stderr)
            raise MoexClientError(msg) from e
        except MoexClientError:
            # Already logged; just re-raise
            raise
        except Exception as e:
            msg = f"Неожиданная ошибка при обращении к API Мосбиржи: {e}"
            logger.error(msg, exc_info=True)
            print(msg, file=sys.stderr)
            raise MoexClientError(msg) from e
    
    def _parse_payload(
        self,
        payload: Dict,
        start_date: date,
        end_date: date
    ) -> List[CandleRecord]:
        candles = payload.get("candles")
        if not candles or "columns" not in candles or "data" not in candles:
            raise MoexClientError("Некорректные данные от API Мосбиржи: отсутствует секция candles")
        
        columns = candles["columns"]
        data_rows = candles["data"]
        required_columns = ["open", "high", "low", "close", "volume", "begin"]
        for col in required_columns:
            if col not in columns:
                raise MoexClientError(f"Некорректные данные от API Мосбиржи: нет колонки {col}")
        
        col_index = {col: columns.index(col) for col in columns}
        
        def parse_float(value) -> Optional[float]:
            if value is None:
                return None
            try:
                number = float(value)
            except (TypeError, ValueError) as exc:
                raise MoexClientError(f"Некорректное числовое значение в ответе API: {value}") from exc
            if number < 0:
                raise MoexClientError(f"Отрицательное значение в данных API: {value}")
            return number
        
        records_by_date: Dict[date, CandleRecord] = {}
        for row in data_rows:
            try:
                begin_str = row[col_index["begin"]]
                day = datetime.fromisoformat(begin_str).date()
            except Exception as exc:
                raise MoexClientError(f"Некорректная дата свечи в ответе API: {row}") from exc
            
            if day < start_date or day > end_date:
                # Игнорируем записи вне запрошенного периода
                continue
            
            board = row[col_index["boardid"]] if "boardid" in col_index else self.EXPECTED_BOARD
            if board != self.EXPECTED_BOARD:
                raise MoexClientError(f"Получена доска {board}, ожидалась {self.EXPECTED_BOARD}")
            
            record = CandleRecord(
                date=day,
                open=parse_float(row[col_index["open"]]),
                high=parse_float(row[col_index["high"]]),
                low=parse_float(row[col_index["low"]]),
                close=parse_float(row[col_index["close"]]),
                volume=parse_float(row[col_index["volume"]]),
                instrument=self.INSTRUMENT,
                board=self.EXPECTED_BOARD,
            )
            records_by_date[day] = record
        
        # Ensure all dates are present, fill missing with None values
        records: List[CandleRecord] = []
        current_date = start_date
        while current_date <= end_date:
            record = records_by_date.get(
                current_date,
                CandleRecord(
                    date=current_date,
                    open=None,
                    high=None,
                    low=None,
                    close=None,
                    volume=None,
                    instrument=self.INSTRUMENT,
                    board=self.EXPECTED_BOARD,
                ),
            )
            records.append(record)
            current_date += timedelta(days=1)
        
        return records

