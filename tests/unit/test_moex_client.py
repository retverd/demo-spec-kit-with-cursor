"""Юнит-тесты для MoexClient."""

from datetime import date
from unittest.mock import Mock, patch

import pytest
import requests

from src.models.candles import CandleRecord
from src.services.moex_client import MoexClient, MoexClientError


@patch("src.services.moex_client.requests.Session")
def test_success_get_daily_candles(mock_session_class):
    """Проверяет маппинг ответа API и заполнение пропущенных дат."""
    payload = {
        "candles": {
            "columns": [
                "open",
                "close",
                "high",
                "low",
                "value",
                "volume",
                "begin",
                "end",
                "boardid",
            ],
            "data": [
                [
                    10.0,
                    11.0,
                    12.0,
                    9.0,
                    0.0,
                    100.0,
                    "2025-11-28 10:00:00",
                    "2025-11-28 18:45:00",
                    "TQTF",
                ],
                [
                    11.0,
                    12.0,
                    13.0,
                    10.0,
                    0.0,
                    200.0,
                    "2025-11-30 10:00:00",
                    "2025-11-30 18:45:00",
                    "TQTF",
                ],
            ],
        }
    }
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = payload
    mock_session = Mock()
    mock_session.get.return_value = mock_response
    mock_session_class.return_value = mock_session

    client = MoexClient()
    records = client.get_daily_candles(date(2025, 11, 28), date(2025, 12, 4))

    assert len(records) == 7
    assert records[0].date == date(2025, 11, 28)
    assert isinstance(records[0], CandleRecord)
    assert records[0].open == 10.0
    # Пропущенная дата 2025-11-29 должна быть заполнена значениями None
    assert records[1].date == date(2025, 11, 29)
    assert records[1].open is None
    # Предоставление второй записи
    assert records[2].date == date(2025, 11, 30)
    assert records[2].close == 12.0
    # Обеспечение наличия всех дат в периоде через 2025-12-04
    assert records[-1].date == date(2025, 12, 4)


@patch("src.services.moex_client.requests.Session")
def test_http_error_raises_moex_client_error(mock_session_class):
    """HTTP 5xx вызывает MoexClientError."""
    mock_response = Mock()
    http_error = requests.HTTPError("500")
    mock_response.raise_for_status.side_effect = http_error
    mock_session = Mock()
    mock_session.get.return_value = mock_response
    mock_session_class.return_value = mock_session

    client = MoexClient()
    with pytest.raises(MoexClientError):
        client.get_daily_candles(date(2025, 11, 28), date(2025, 12, 4))


@patch("src.services.moex_client.requests.Session")
def test_timeout_raises_moex_client_error(mock_session_class):
    """Таймаут сети вызывает MoexClientError."""
    mock_session = Mock()
    mock_session.get.side_effect = requests.Timeout("timeout")
    mock_session_class.return_value = mock_session

    client = MoexClient()
    with pytest.raises(MoexClientError):
        client.get_daily_candles(date(2025, 11, 28), date(2025, 12, 4))
