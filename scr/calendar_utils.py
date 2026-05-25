# calendar_utils.py
import holidays
from datetime import date
from typing import Dict, List

# Ручные переносы выходных (формат: {date: 'work' или 'holiday'})
# Актуально для 2024-2027. При необходимости дополнить или загружать из JSON.
MANUAL_TRANSFERS = {
    # 2026
    date(2026, 5, 11): 'work',   # пример переноса
    date(2026, 5, 4): 'holiday', # пример переноса
}

def is_weekend_or_holiday(d: date, year: int) -> bool:
    """Проверка на выходной с учетом праздников РФ и ручных правок"""
    if d in MANUAL_TRANSFERS:
        return MANUAL_TRANSFERS[d] == 'holiday'
    
    ru_hols = holidays.RU(years=year)
    if d in ru_hols:
        return True
    if d.weekday() >= 5:  # Сб, Вс
        return True
    return False

def get_month_work_days(year: int, month: int) -> Dict[int, bool]:
    """Возвращает {день: True если рабочий, False если выходной}"""
    days_map = {}
    if month == 2:
        max_day = 29 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 28
    else:
        max_day = [0,31,0,31,30,31,30,31,31,30,31,30,31][month]
        
    for day in range(1, max_day + 1):
        d = date(year, month, day)
        days_map[day] = not is_weekend_or_holiday(d, year)
    return days_map

def apply_calendar_to_db(year: int, month: int, db_funcs, default_hours: float = 8.0):
    """Массовое обновление кодов на В (выходной) для нерабочих дней"""
    work_map = get_month_work_days(year, month)
    employees = db_funcs.get_employees()
    data = []
    
    for emp in employees:
        for day, is_work in work_map.items():
            code = 'В' if not is_work else 'Ф/Я'
            hours = (emp['rate'] * default_hours) if (code == 'Ф/Я') else 0
            data.append({
                'emp_id': emp['id'], 'year': year, 'month': month,
                'day': day, 'code': code, 'hours': hours
            })
    db_funcs.save_month_data(year, month, data)
