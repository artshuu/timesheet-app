import os
import tempfile
import pytest
from src import db


@pytest.fixture(autouse=True)
def temp_db(monkeypatch):
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    monkeypatch.setattr(db, 'DB_NAME', path)
    monkeypatch.setattr(db, 'get_db_path', lambda: path)
    db.init_db()
    yield
    os.unlink(path)


def test_add_and_get_employee():
    emp_id = db.add_employee({
        'full_name': 'Иванов И.И.',
        'tab_number': '001',
        'rate': 1.0,
        'position_main': 'Инженер',
        'position_part': None,
        'employment_type': 'основная'
    })
    assert emp_id is not None
    emps = db.get_employees()
    assert len(emps) == 1
    assert emps[0]['full_name'] == 'Иванов И.И.'


def test_save_and_load_month():
    emp_id = db.add_employee({
        'full_name': 'Тест',
        'tab_number': '999',
        'rate': 0.5,
        'position_main': 'X',
        'position_part': None,
        'employment_type': 'основная'
    })
    db.save_month_data(2026, 5, [
        {'emp_id': emp_id, 'year': 2026, 'month': 5, 'day': 1, 'code': 'Ф/Я', 'hours': 4.0}
    ])
    data = db.load_month_data(2026, 5)
    assert len(data) == 1
    assert data[0]['code'] == 'Ф/Я'
