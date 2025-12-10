"""Юнит-тесты клиента ЦБ РФ."""

from datetime import date, timedelta
from unittest.mock import Mock, patch

import pytest
import requests

from src.models.exchange_rate import ExchangeRateRecord
from src.services.cbr_client import CBRClient, CBRClientError


class TestCBRClientGetExchangeRates:
    """Проверка метода CBRClient.get_exchange_rates."""
    
    @patch('src.services.cbr_client.requests.Session')
    def test_get_exchange_rates_success_with_complete_data(self, mock_session_class):
        """Успешное получение с полными 7 днями данных."""
        # Мокаем XML-ответ в windows-1251
        xml_content = '''<?xml version="1.0" encoding="windows-1251"?>
<ValCurs ID="R01235" DateRange1="25.11.2025" DateRange2="01.12.2025" name="Foreign Currency Market Dynamic">
    <Record Date="25.11.2025" Id="R01235">
        <Nominal>1</Nominal>
        <Value>78,5000</Value>
        <VunitRate>78,50</VunitRate>
    </Record>
    <Record Date="26.11.2025" Id="R01235">
        <Nominal>1</Nominal>
        <Value>78,5500</Value>
        <VunitRate>78,55</VunitRate>
    </Record>
    <Record Date="27.11.2025" Id="R01235">
        <Nominal>1</Nominal>
        <Value>78,6000</Value>
        <VunitRate>78,60</VunitRate>
    </Record>
    <Record Date="28.11.2025" Id="R01235">
        <Nominal>1</Nominal>
        <Value>78,6500</Value>
        <VunitRate>78,65</VunitRate>
    </Record>
    <Record Date="29.11.2025" Id="R01235">
        <Nominal>1</Nominal>
        <Value>78,7000</Value>
        <VunitRate>78,70</VunitRate>
    </Record>
    <Record Date="30.11.2025" Id="R01235">
        <Nominal>1</Nominal>
        <Value>78,7500</Value>
        <VunitRate>78,75</VunitRate>
    </Record>
    <Record Date="01.12.2025" Id="R01235">
        <Nominal>1</Nominal>
        <Value>78,8000</Value>
        <VunitRate>78,80</VunitRate>
    </Record>
</ValCurs>'''
        
        # Кодируем в windows-1251 для мока
        encoded_content = xml_content.encode('windows-1251')
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = encoded_content
        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = CBRClient()
        start_date = date(2025, 11, 25)
        end_date = date(2025, 12, 1)
        
        result = client.get_exchange_rates(start_date, end_date)
        
        # Проверяем результат
        assert len(result) == 7
        assert all(isinstance(r, ExchangeRateRecord) for r in result)
        assert result[0].date == date(2025, 11, 25)
        assert result[0].exchange_rate_value == 78.50
        assert result[-1].date == date(2025, 12, 1)
        assert result[-1].exchange_rate_value == 78.80
        
        # Проверяем корректность запроса
        mock_session.get.assert_called_once()
        call_args = mock_session.get.call_args
        assert "timeout" in call_args.kwargs
        assert call_args.kwargs["timeout"] == 15
        assert "R01235" in call_args.args[0]  # код валюты в URL
    
    @patch('src.services.cbr_client.requests.Session')
    def test_get_exchange_rates_with_missing_days(self, mock_session_class):
        """Получение с пропущенными днями (выходные) заполненными None."""
        # Мокаем XML с 5 днями (выходные отсутствуют)
        xml_content = '''<?xml version="1.0" encoding="windows-1251"?>
<ValCurs ID="R01235" DateRange1="25.11.2025" DateRange2="01.12.2025" name="Foreign Currency Market Dynamic">
    <Record Date="25.11.2025" Id="R01235">
        <Nominal>1</Nominal>
        <Value>78,5000</Value>
        <VunitRate>78,50</VunitRate>
    </Record>
    <Record Date="26.11.2025" Id="R01235">
        <Nominal>1</Nominal>
        <Value>78,5500</Value>
        <VunitRate>78,55</VunitRate>
    </Record>
    <Record Date="29.11.2025" Id="R01235">
        <Nominal>1</Nominal>
        <Value>78,6000</Value>
        <VunitRate>78,60</VunitRate>
    </Record>
    <Record Date="30.11.2025" Id="R01235">
        <Nominal>1</Nominal>
        <Value>78,6500</Value>
        <VunitRate>78,65</VunitRate>
    </Record>
    <Record Date="01.12.2025" Id="R01235">
        <Nominal>1</Nominal>
        <Value>78,7000</Value>
        <VunitRate>78,70</VunitRate>
    </Record>
</ValCurs>'''
        
        encoded_content = xml_content.encode('windows-1251')
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = encoded_content
        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = CBRClient()
        start_date = date(2025, 11, 25)
        end_date = date(2025, 12, 1)
        
        result = client.get_exchange_rates(start_date, end_date)
        
        # Должно быть 7 записей
        assert len(result) == 7
        
        # Пропущенные дни (27.11, 28.11) должны быть с None
        dates_with_rates = {r.date for r in result if r.exchange_rate_value is not None}
        assert date(2025, 11, 25) in dates_with_rates
        assert date(2025, 11, 26) in dates_with_rates
        assert date(2025, 11, 27) not in dates_with_rates  # Missing
        assert date(2025, 11, 28) not in dates_with_rates  # Missing
        assert date(2025, 11, 29) in dates_with_rates
        assert date(2025, 11, 30) in dates_with_rates
        assert date(2025, 12, 1) in dates_with_rates
        
        # Проверяем наличие всех дат
        all_dates = {r.date for r in result}
        expected_dates = {start_date + timedelta(days=i) for i in range(7)}
        assert all_dates == expected_dates


class TestCBRClientErrorHandling:
    """Проверка обработки ошибок клиента ЦБ РФ."""
    
    @patch('src.services.cbr_client.requests.Session')
    def test_get_exchange_rates_404_error(self, mock_session_class):
        """Обработка ошибки 404 Not Found."""
        mock_response = Mock()
        mock_response.status_code = 404
        http_error = requests.HTTPError("404 Not Found")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = CBRClient()
        start_date = date(2025, 11, 25)
        end_date = date(2025, 12, 1)
        
        with pytest.raises(CBRClientError) as exc_info:
            client.get_exchange_rates(start_date, end_date)
        
        assert "CBR API" in str(exc_info.value) or "unavailable" in str(exc_info.value).lower()
    
    @patch('src.services.cbr_client.requests.Session')
    def test_get_exchange_rates_500_error(self, mock_session_class):
        """Обработка ошибки 500 Internal Server Error."""
        mock_response = Mock()
        mock_response.status_code = 500
        http_error = requests.HTTPError("500 Internal Server Error")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = CBRClient()
        start_date = date(2025, 11, 25)
        end_date = date(2025, 12, 1)
        
        with pytest.raises(CBRClientError) as exc_info:
            client.get_exchange_rates(start_date, end_date)
        
        assert "CBR API" in str(exc_info.value) or "unavailable" in str(exc_info.value).lower()
    
    @patch('src.services.cbr_client.requests.Session')
    def test_get_exchange_rates_timeout_error(self, mock_session_class):
        """Обработка сетевого таймаута."""
        mock_session = Mock()
        mock_session.get.side_effect = requests.Timeout("Request timed out")
        mock_session_class.return_value = mock_session
        
        client = CBRClient()
        start_date = date(2025, 11, 25)
        end_date = date(2025, 12, 1)
        
        with pytest.raises(CBRClientError) as exc_info:
            client.get_exchange_rates(start_date, end_date)
        
        assert "timeout" in str(exc_info.value).lower() or "connection" in str(exc_info.value).lower()
    
    @patch('src.services.cbr_client.requests.Session')
    def test_get_exchange_rates_connection_error(self, mock_session_class):
        """Обработка ошибки соединения."""
        mock_session = Mock()
        mock_session.get.side_effect = requests.ConnectionError("Connection failed")
        mock_session_class.return_value = mock_session
        
        client = CBRClient()
        start_date = date(2025, 11, 25)
        end_date = date(2025, 12, 1)
        
        with pytest.raises(CBRClientError) as exc_info:
            client.get_exchange_rates(start_date, end_date)
        
        assert "connection" in str(exc_info.value).lower() or "network" in str(exc_info.value).lower()
    
    @patch('src.services.cbr_client.requests.Session')
    def test_get_exchange_rates_invalid_xml(self, mock_session_class):
        """Обработка некорректного XML-ответа."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"Invalid XML content"
        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = CBRClient()
        start_date = date(2025, 11, 25)
        end_date = date(2025, 12, 1)
        
        with pytest.raises(CBRClientError) as exc_info:
            client.get_exchange_rates(start_date, end_date)
        
        assert "invalid" in str(exc_info.value).lower() or "malformed" in str(exc_info.value).lower()


class TestCBRClientDateRangeHandling:
    """Проверка работы с диапазоном дат в клиенте ЦБ РФ."""
    
    @patch('src.services.cbr_client.requests.Session')
    def test_get_exchange_rates_date_range_calculation(self, mock_session_class):
        """Диапазон дат вычисляется корректно, включены все даты."""
        xml_content = '''<?xml version="1.0" encoding="windows-1251"?>
<ValCurs ID="R01235" DateRange1="25.11.2025" DateRange2="01.12.2025" name="Foreign Currency Market Dynamic">
    <Record Date="25.11.2025" Id="R01235">
        <Nominal>1</Nominal>
        <Value>78,5000</Value>
        <VunitRate>78,50</VunitRate>
    </Record>
    <Record Date="01.12.2025" Id="R01235">
        <Nominal>1</Nominal>
        <Value>78,8000</Value>
        <VunitRate>78,80</VunitRate>
    </Record>
</ValCurs>'''
        
        encoded_content = xml_content.encode('windows-1251')
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = encoded_content
        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = CBRClient()
        start_date = date(2025, 11, 25)
        end_date = date(2025, 12, 1)
        
        result = client.get_exchange_rates(start_date, end_date)
        
        # Все 7 дат присутствуют
        assert len(result) == 7
        result_dates = [r.date for r in result]
        expected_dates = [start_date + timedelta(days=i) for i in range(7)]
        assert result_dates == expected_dates
        
        # Проверяем, что в URL даты в формате DD/MM/YYYY
        call_args = mock_session.get.call_args
        url = call_args[0][0]  # First positional argument
        assert '25/11/2025' in url
        assert '01/12/2025' in url

