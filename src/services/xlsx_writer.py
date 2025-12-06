"""XLSX writer for LQDT/TQTF candles."""

import os
from datetime import date, datetime
from typing import List, Optional

import openpyxl

from src.models.candles import CandleRecord


class XLSXWriter:
    """Writes candle data to XLSX with required naming pattern and headers."""

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
        Write candles to XLSX.

        Args:
            records: List of CandleRecord for the period (expected 7 days).
            output_dir: Directory to save the file.
            period_start: Period start date; if None, derived from records.
            period_end: Period end date; if None, derived from records.
            report_date: Date of extraction; if None, uses today.

        Returns:
            Full path to created XLSX file.

        Raises:
            ValueError: When records are empty.
            IOError: When file cannot be written.
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
