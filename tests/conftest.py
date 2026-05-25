# tests/conftest.py
import sys
import os

# Добавляем папку src в sys.path, чтобы тесты могли импортировать модули
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
