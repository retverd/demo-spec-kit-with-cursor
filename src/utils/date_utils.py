"""Date range calculation utilities for exchange rate extraction."""

from datetime import date, timedelta
from typing import List


def get_last_7_days() -> List[date]:
    """
    Calculate the last 7 calendar days: [today, today - 6] (inclusive, 7 days total).
    
    Returns:
        List of 7 date objects, starting from today - 6 days ago and ending with today.
        Dates are in chronological order (oldest first).
    
    Example:
        If today is 2025-12-02, returns:
        [date(2025-11-26), date(2025-11-27), ..., date(2025-12-02)]
    """
    today = date.today()
    # Calculate 7 days: [today, today - 6] (inclusive, 7 days total)
    start_date = today - timedelta(days=6)
    return [start_date + timedelta(days=i) for i in range(7)]

