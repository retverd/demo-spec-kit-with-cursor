"""Клиент API ЦБ РФ для извлечения курса валют."""

import logging
import sys
from datetime import date, timedelta
from typing import List
from xml.etree import ElementTree as ET

import requests

from src.models.exchange_rate import ExchangeRateRecord

logger = logging.getLogger(__name__)


class CBRClientError(Exception):
    """Исключение для ошибок клиента ЦБ РФ."""

    pass


class CBRClient:
    """
    Клиент для получения курса RUB/USD из API ЦБ РФ.

    Подключается к эндпоинту XML_dynamic.asp и возвращает курс за указанный период.
    """

    BASE_URL = "http://www.cbr.ru/scripts/XML_dynamic.asp"
    CURRENCY_CODE = "R01235"  # USD currency code
    TIMEOUT_SECONDS = 15  # Aligns with SC-002 (30-second total requirement)

    def __init__(self):
        """Создать экземпляр клиента ЦБ РФ."""
        self.session = requests.Session()

    def get_exchange_rates(
        self, start_date: date, end_date: date
    ) -> List[ExchangeRateRecord]:
        """
        Получить курсы RUB/USD за указанный период.

        Args:
            start_date: Начало периода (включительно)
            end_date: Конец периода (включительно)

        Returns:
            Список ExchangeRateRecord по одному на день. Пропуски (выходные/праздники)
            будут иметь exchange_rate_value = None.

        Raises:
            CBRClientError: при сетевых ошибках, ошибках HTTP или некорректных данных.
        """
        try:
            # Собрать URL с параметрами дат
            url = self._build_url(start_date, end_date)
            logger.info(
                f"Requesting exchange rates from CBR API: {start_date} to {end_date}"
            )

            # Выполнить запрос с таймаутом (соответствует SC-002)
            response = self.session.get(url, timeout=self.TIMEOUT_SECONDS)
            response.raise_for_status()

            # Декодировать ответ windows-1251
            try:
                content = response.content.decode("windows-1251")
            except UnicodeDecodeError as e:
                logger.error(f"Failed to decode response from windows-1251: {e}")
                raise CBRClientError(
                    "Invalid response encoding from CBR API. Expected windows-1251."
                ) from e

            # Распарсить XML и извлечь записи
            records = self._parse_xml_response(content, start_date, end_date)

            logger.info(
                f"Successfully retrieved {len([r for r in records if r.exchange_rate_value is not None])} exchange rates"
            )
            return records

        except requests.Timeout as e:
            error_msg = "Network timeout while connecting to CBR API. Please check your network connection."
            logger.error(error_msg)
            print(error_msg, file=sys.stderr)
            raise CBRClientError(error_msg) from e

        except requests.ConnectionError as e:
            error_msg = (
                "Unable to connect to CBR API. Please check your network connection."
            )
            logger.error(error_msg)
            print(error_msg, file=sys.stderr)
            raise CBRClientError(error_msg) from e

        except requests.HTTPError as e:
            error_msg = f"CBR API returned error: {e.response.status_code if hasattr(e, 'response') else 'Unknown'}"
            logger.error(error_msg)
            print(error_msg, file=sys.stderr)
            raise CBRClientError(error_msg) from e

        except ET.ParseError as e:
            error_msg = "Invalid or malformed XML response from CBR API."
            logger.error(f"{error_msg}: {e}")
            print(error_msg, file=sys.stderr)
            raise CBRClientError(error_msg) from e

        except (ValueError, KeyError, AttributeError) as e:
            error_msg = "Invalid or malformed data received from CBR API."
            logger.error(f"{error_msg}: {e}")
            print(error_msg, file=sys.stderr)
            raise CBRClientError(error_msg) from e

    def _build_url(self, start_date: date, end_date: date) -> str:
        """
        Собрать URL API ЦБ РФ с параметрами периода.

        Args:
            start_date: Дата начала (формат DD/MM/YYYY)
            end_date: Дата окончания (формат DD/MM/YYYY)

        Returns:
            Полный URL с параметрами запроса.
        """
        date_req1 = start_date.strftime("%d/%m/%Y")
        date_req2 = end_date.strftime("%d/%m/%Y")
        return (
            f"{self.BASE_URL}"
            f"?date_req1={date_req1}"
            f"&date_req2={date_req2}"
            f"&VAL_NM_RQ={self.CURRENCY_CODE}"
        )

    def _parse_xml_response(
        self, xml_content: str, start_date: date, end_date: date
    ) -> List[ExchangeRateRecord]:
        """
        Распарсить XML и создать ExchangeRateRecord для всех дат периода.

        Пропущенные дни (выходные/праздники) получают exchange_rate_value = None.

        Args:
            xml_content: Строка XML (уже декодирована из windows-1251)
            start_date: Начало периода
            end_date: Конец периода

        Returns:
            Список ExchangeRateRecord, по одному на день периода.
        """
        # Разбор XML
        root = ET.fromstring(xml_content)

        # Извлечь все записи из ответа
        api_records = {}
        for record_elem in root.findall("Record"):
            # Дата в формате DD.MM.YYYY
            date_str = record_elem.get("Date")
            if not date_str:
                continue

            # Преобразовать дату в объект date
            try:
                day, month, year = date_str.split(".")
                record_date = date(int(year), int(month), int(day))
            except (ValueError, TypeError) as e:
                logger.warning(
                    f"Invalid date format in API response: {date_str}, skipping"
                )
                continue

            # Извлечь значение курса
            value_elem = record_elem.find("Value")
            if value_elem is None or value_elem.text is None:
                logger.warning(f"No Value element for date {record_date}, skipping")
                continue

            # Заменить запятую на точку и преобразовать в float
            try:
                value_str = value_elem.text.replace(",", ".")
                rate = float(value_str)
                api_records[record_date] = rate
            except (ValueError, TypeError) as e:
                logger.warning(
                    f"Invalid rate value for date {record_date}: {value_elem.text}, skipping"
                )
                continue

        # Сформировать записи на все даты периода, пропуски заполнить None
        result = []
        current_date = start_date
        while current_date <= end_date:
            rate = api_records.get(current_date)  # None if missing
            result.append(
                ExchangeRateRecord(
                    date=current_date, exchange_rate_value=rate, currency_pair="RUB/USD"
                )
            )
            current_date += timedelta(days=1)

        return result
