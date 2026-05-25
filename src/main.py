# src/main.py
import sys
import os

# КРИТИЧЕСКИ ВАЖНО ДЛЯ PYINSTALLER
if getattr(sys, 'frozen', False):
    # Запущен как .exe — модули распакованы во временную папку _MEIPASS
    meipass = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    if meipass not in sys.path:
        sys.path.insert(0, meipass)
else:
    # Режим разработки — добавляем папку src/
    src_dir = os.path.dirname(os.path.abspath(__file__))
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

# Импорты ПОСЛЕ настройки sys.path
from PyQt6.QtWidgets import QApplication
from db import init_db
from gui import TimesheetApp


def main():
    init_db()
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = TimesheetApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
