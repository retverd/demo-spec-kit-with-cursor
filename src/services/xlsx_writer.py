"""Запись свечей LQDT/TQTF в XLSX."""

import os
from datetime import date, datetime
from typing import List, Optional

import openpyxl

from src.models.candles import CandleRecord


class XLSXWriter:
    """Сохраняет свечи в XLSX с нужным именованием и заголовками."""

    HEADERS = ["Date", "Open", "High", "Low", "Close", "Volume"]

    def write_candles(
        self,
        records: List[CandleRecord],
        output_dir: str = ".",
        period_start: Optional[date] = None,
        period_end: Optional[date] = None,
        report_date: Optional[date] = None,
    ) -> str:
        """
        Записать свечи в XLSX.

        Args:
            records: Список свечей за период (ожидается 7 дней).
            output_dir: Каталог для сохранения файла.
            period_start: Начало периода; если None, берётся из записей.
            period_end: Конец периода; если None, берётся из записей.
            report_date: Дата выгрузки; если None, используется сегодня.

        Returns:
            Полный путь к созданному файлу.

        Raises:
            ValueError: Если список записей пуст.
            IOError: При ошибке записи файла.
        """
        if not records:
            raise ValueError("Нет данных свечей для записи")

        period_start = period_start or min(r.date for r in records)
        period_end = period_end or max(r.date for r in records)
        report_date_value = report_date or date.today()

        os.makedirs(output_dir, exist_ok=True)
        filename = self._generate_filename(
            period_start, period_end, report_date_value, output_dir
        )

        try:
            workbook = openpyxl.Workbook()
            sheet = workbook.active
            sheet.title = "candles"
            sheet.append(self.HEADERS)

            for record in records:
                sheet.append(
                    [
                        record.date.isoformat(),
                        record.open,
                        record.high,
                        record.low,
                        record.close,
                        record.volume,
                    ]
                )

            workbook.save(filename)
        except Exception as exc:
            raise IOError(f"Не удалось записать XLSX-файл: {exc}") from exc

        return filename

    def _generate_filename(
        self,
        period_start: date,
        period_end: date,
        report_date: date,
        output_dir: str,
    ) -> str:
        timestamp = datetime.now().strftime("%H%M%S")
        period_start_str = period_start.isoformat()
        period_end_str = period_end.isoformat()
        report_date_str = report_date.isoformat()
        name = f"lqdt_tqtf_{period_start_str}_to_{period_end_str}_{report_date_str}_{timestamp}.xlsx"
        return os.path.join(output_dir, name)
