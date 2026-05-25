from datetime import date
from src.calendar_utils import get_month_work_days, is_weekend_or_holiday

def test_new_year_is_holiday():
    """1 января — всегда выходной"""
    assert is_weekend_or_holiday(date(2026, 1, 1), 2026) is True

def test_typical_workday():
    """Среда 13 мая 2026 — рабочий день"""
    assert is_weekend_or_holiday(date(2026, 5, 13), 2026) is False

def test_weekend_is_holiday():
    """Суббота/Воскресенье — выходные"""
    assert is_weekend_or_holiday(date(2026, 5, 16), 2026) is True  # суббота
    assert is_weekend_or_holiday(date(2026, 5, 17), 2026) is True  # воскресенье

def test_month_days_count():
    """Май 2026 имеет 31 день"""
    days = get_month_work_days(2026, 5)
    assert len(days) == 31
    assert all(isinstance(v, bool) for v in days.values())
