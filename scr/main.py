# main.py
import sys
import os
from PyQt6.QtWidgets import QApplication
from db import init_db
from gui import TimesheetApp

def resource_path(relative_path):
    """Получение абсолютного пути к ресурсам (для PyInstaller)"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(getattr(sys, '_MEIPASS'), relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def main():
    # Инициализация БД
    init_db()
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = TimesheetApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
