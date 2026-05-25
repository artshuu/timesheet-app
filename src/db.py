# src/db.py
import sqlite3
import os
import sys
from typing import List, Dict, Optional
from contextlib import contextmanager

DB_NAME = "timesheet.db"


def get_db_path():
    """Учет пути при сборке в .exe (PyInstaller)"""
    if getattr(sys, 'frozen', False):
        # Запущен как .exe — БД создается рядом с исполняемым файлом
        return os.path.join(os.path.dirname(sys.executable), DB_NAME)
    # Режим разработки — БД создается в папке src/
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_NAME)


@contextmanager
def get_connection():
    """Контекстный менеджер для безопасной работы с БД"""
    conn = sqlite3.connect(get_db_path())
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Инициализация базы данных и создание таблиц"""
    with get_connection() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS employees ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "full_name TEXT NOT NULL, "
            "tab_number TEXT UNIQUE NOT NULL, "
            "rate REAL DEFAULT 1.0, "
            "position_main TEXT, "
            "position_part TEXT, "
            "employment_type TEXT DEFAULT 'основная')"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS timesheet ("
            "employee_id INTEGER, "
            "year INTEGER, "
            "month INTEGER, "
            "day INTEGER, "
            "code TEXT DEFAULT 'Ф/Я', "
            "hours REAL DEFAULT 0, "
            "PRIMARY KEY (employee_id, year, month, day), "
            "FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS settings ("
            "key TEXT PRIMARY KEY, "
            "value TEXT)"
        )
        defaults = {
            "institution": "ФГБОУ ВО «Технический Университет»",
            "department": "Технический отдел",
            "responsible": "Иванов И.И.",
            "head_dept": "Петров П.П.",
            "accountant": "Сидорова С.С."
        }
        for k, v in defaults.items():
            conn.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (k, v)
            )


def get_employees() -> List[Dict]:
    """Получение списка всех сотрудников"""
    with get_connection() as conn:
        cur = conn.execute("SELECT * FROM employees ORDER BY full_name")
        return [dict(r) for r in cur.fetchall()]


def add_employee(data: Dict) -> Optional[int]:
    """Добавление или обновление сотрудника"""
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT OR REPLACE INTO employees "
            "(full_name, tab_number, rate, position_main, position_part, employment_type) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (data['full_name'], data['tab_number'], data['rate'],
             data['position_main'], data.get('position_part'), data['employment_type'])
        )
        return cur.lastrowid


def delete_employee(emp_id: int):
    """Удаление сотрудника по ID"""
    with get_connection() as conn:
        conn.execute("DELETE FROM employees WHERE id=?", (emp_id,))


def save_month_data(year: int, month: int, data: List[Dict]):
    """Сохранение данных табеля за месяц"""
    with get_connection() as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO timesheet "
            "(employee_id, year, month, day, code, hours) "
            "VALUES (:emp_id, :year, :month, :day, :code, :hours)",
            data
        )


def load_month_data(year: int, month: int) -> List[Dict]:
    """Загрузка данных табеля за указанный месяц"""
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT employee_id, day, code, hours FROM timesheet "
            "WHERE year=? AND month=?",
            (year, month)
        )
        return [dict(r) for r in cur.fetchall()]


def get_setting(key: str) -> str:
    """Получение значения настройки по ключу"""
    with get_connection() as conn:
        cur = conn.execute("SELECT value FROM settings WHERE key=?", (key,))
        row = cur.fetchone()
        return row['value'] if row else ""
