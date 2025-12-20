"""Pytest configuration.

Цель: обеспечить корректную кириллицу в выводе (stdout/stderr) при запуске тестов из VS Code Testing на Windows.
Некоторые комбинации VS Code/pytest могут использовать не-UTF-8 кодировку, из-за чего сообщения становятся "кракозябрами".
"""

from __future__ import annotations

import sys


def pytest_configure() -> None:
    """Принудительно включить UTF-8 для stdout/stderr (best-effort)."""
    for stream in (sys.stdout, sys.stderr):
        try:
            reconfigure = getattr(stream, "reconfigure", None)
            if callable(reconfigure):
                reconfigure(encoding="utf-8")
        except Exception:
            # Не ломаем тестовый прогон, если поток не поддерживает reconfigure.
            pass
