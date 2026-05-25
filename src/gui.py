# gui.py
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QSplitter, QTableWidget, QTableWidgetItem, 
                             QPushButton, QComboBox, QHeaderView, QFileDialog, 
                             QMessageBox, QLabel, QStatusBar, QLineEdit, QGroupBox,
                             QAbstractItemView, QStyledItemDelegate)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QFont
from db import get_employees, add_employee, delete_employee, save_month_data, load_month_data, get_setting
from calendar_utils import apply_calendar_to_db
from export import generate_excel

class CodeDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        cb = QComboBox(parent)
        cb.addItems(['Ф/Я', 'В', 'РП', 'О', 'ОД', 'Б', 'Х'])
        return cb
    def setEditorData(self, editor, index):
        editor.setCurrentText(index.data() or 'Ф/Я')
    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText())

class TimesheetApp(QMainWindow):
    CODE_COLORS = {'Ф/Я': '#C6EFCE', 'В': '#D9D9D9', 'РП': '#B4C6E7', 
                   'О': '#FCE4D6', 'ОД': '#FFF2CC', 'Б': '#FFC7CE', 'Х': '#D9D9D9'}
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Табель учета рабочего времени — Техотдел")
        self.resize(1200, 700)
        self.current_year = 2026
        self.current_month = 5
        self.setup_ui()
        self.load_employees()
        self.load_timesheet()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Верхняя панель
        top = QHBoxLayout()
        self.cb_year = QComboBox()
        self.cb_year.addItems([str(y) for y in range(2024, 2031)])
        self.cb_year.setCurrentText(str(self.current_year))
        self.cb_month = QComboBox()
        self.cb_month.addItems([f"{m:02d}" for m in range(1, 13)])
        self.cb_month.setCurrentText(f"{self.current_month:02d}")
        
        self.btn_apply_cal = QPushButton("📅 Применить календарь")
        self.btn_calc = QPushButton("🔢 Рассчитать итоги")
        self.btn_export = QPushButton("📥 Экспорт в Excel")
        self.btn_save = QPushButton("💾 Сохранить")
        
        top.addWidget(QLabel("Год:")); top.addWidget(self.cb_year)
        top.addWidget(QLabel("Месяц:")); top.addWidget(self.cb_month)
        top.addStretch()
        top.addWidget(self.btn_apply_cal)
        top.addWidget(self.btn_calc)
        top.addWidget(self.btn_export)
        top.addWidget(self.btn_save)
        layout.addLayout(top)
        
        # Сплиттер
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Левая панель (Сотрудники)
        left = QWidget()
        left_layout = QVBoxLayout(left)
        self.tbl_emp = QTableWidget()
        self.tbl_emp.setColumnCount(6)
        self.tbl_emp.setHorizontalHeaderLabels(['ID', 'ФИО', 'Таб. №', 'Ставка', 'Должность', 'Тип'])
        self.tbl_emp.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_emp.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        grp = QGroupBox("Управление сотрудниками")
        grp_layout = QHBoxLayout(grp)
        self.btn_add_emp = QPushButton("➕ Добавить")
        self.btn_del_emp = QPushButton("🗑 Удалить")
        grp_layout.addWidget(self.btn_add_emp)
        grp_layout.addWidget(self.btn_del_emp)
        
        left_layout.addWidget(self.tbl_emp)
        left_layout.addWidget(grp)
        splitter.addWidget(left)
        
        # Центральная панель (Табель)
        self.tbl_sheet = QTableWidget()
        self.tbl_sheet.setItemDelegate(CodeDelegate())
        self.setup_timesheet_grid()
        splitter.addWidget(self.tbl_sheet)
        
        splitter.setSizes([250, 950])
        layout.addWidget(splitter)
        
        # Статус-бар и подписи
        self.statusBar().showMessage("Готово")
        self.txt_signatures = QLineEdit()
        self.txt_signatures.setPlaceholderText("Ответственные (через запятую) для экспорта")
        layout.addWidget(self.txt_signatures)
        
        # Сигналы
        self.btn_add_emp.clicked.connect(self.show_add_employee_dialog)
        self.btn_del_emp.clicked.connect(self.delete_selected_employee)
        self.btn_apply_cal.clicked.connect(self.apply_calendar)
        self.btn_calc.clicked.connect(self.recalculate_totals)
        self.btn_export.clicked.connect(self.export_to_excel)
        self.btn_save.clicked.connect(self.save_current_month)
        self.cb_year.currentTextChanged.connect(self.change_month)
        self.cb_month.currentTextChanged.connect(self.change_month)
        self.tbl_emp.cellDoubleClicked.connect(self.load_employees)
        self.tbl_sheet.itemChanged.connect(self.on_cell_changed)

    def setup_timesheet_grid(self):
        self.tbl_sheet.clear()
        headers = ['ФИО', 'Таб.№', 'Ставка']
        headers += [str(d) for d in range(1, 32)]
        headers += ['Д 1-15', 'Ч 1-15', 'Д 16+', 'Ч 16+', 'Всего Д', 'Всего Ч']
        self.tbl_sheet.setColumnCount(len(headers))
        self.tbl_sheet.setHorizontalHeaderLabels(headers)
        self.tbl_sheet.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(3, 34):
            self.tbl_sheet.horizontalHeader().resizeSection(i, 40)
        for i in range(34, 40):
            self.tbl_sheet.horizontalHeader().resizeSection(i, 60)

    def load_employees(self):
        emps = get_employees()
        self.tbl_emp.setRowCount(len(emps))
        for i, e in enumerate(emps):
            for j, key in enumerate(['id', 'full_name', 'tab_number', 'rate', 'position_main', 'employment_type']):
                self.tbl_emp.setItem(i, j, QTableWidgetItem(str(e[key])))
        self.load_timesheet()

    def show_add_employee_dialog(self):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton
        dlg = QDialog(self)
        dlg.setWindowTitle("Добавить сотрудника")
        lay = QVBoxLayout(dlg)
        fields = {}
        for label, key in [('ФИО', 'full_name'), ('Таб. номер', 'tab_number'), 
                           ('Ставка (0.1-1.0)', 'rate'), ('Должность осн.', 'position_main'), 
                           ('Совместительство', 'position_part'), ('Тип занятости', 'employment_type')]:
            lay.addWidget(QLabel(label))
            if key == 'employment_type':
                cb = QComboBox(); cb.addItems(['основная', 'совместительство'])
                lay.addWidget(cb); fields[key] = cb
            elif key == 'rate':
                le = QLineEdit('1.0'); lay.addWidget(le); fields[key] = le
            else:
                le = QLineEdit(); lay.addWidget(le); fields[key] = le
                
        btn_ok = QPushButton("Сохранить")
        lay.addWidget(btn_ok)
        
        def save():
            data = {k: (w.currentText() if isinstance(w, QComboBox) else w.text()) for k, w in fields.items()}
            if not data['full_name'] or not data['tab_number']:
                QMessageBox.warning(dlg, "Ошибка", "Заполните ФИО и табельный номер")
                return
            try:
                data['rate'] = float(data['rate'])
                add_employee(data)
                dlg.accept()
                self.load_employees()
            except ValueError:
                QMessageBox.critical(dlg, "Ошибка", "Некорректная ставка")
        btn_ok.clicked.connect(save)
        dlg.exec()

    def delete_selected_employee(self):
        rows = self.tbl_emp.selectionModel().selectedRows()
        if not rows: return
        if QMessageBox.question(self, "Удаление", "Удалить выбранных сотрудников?") == QMessageBox.StandardButton.Yes:
            for r in rows:
                delete_employee(int(self.tbl_emp.item(r.row(), 0).text()))
            self.load_employees()

    def change_month(self):
        self.current_year = int(self.cb_year.currentText())
        self.current_month = int(self.cb_month.currentText())
        self.load_timesheet()

    def load_timesheet(self):
        self.setup_timesheet_grid()
        emps = get_employees()
        db_data = load_month_data(self.current_year, self.current_month)
        # Формируем быстрый доступ {emp_id: {day: {code, hours}}}
        fast = {}
        for d in db_data:
            fast.setdefault(d['employee_id'], {})[d['day']] = d
            
        self.tbl_sheet.setRowCount(len(emps))
        for i, emp in enumerate(emps):
            eid = emp['id']
            self.tbl_sheet.setItem(i, 0, QTableWidgetItem(emp['full_name']))
            self.tbl_sheet.setItem(i, 1, QTableWidgetItem(emp['tab_number']))
            self.tbl_sheet.setItem(i, 2, QTableWidgetItem(str(emp['rate'])))
            
            data = fast.get(eid, {})
            for day in range(1, 32):
                item = data.get(day, {})
                code = item.get('code', 'Ф/Я')
                self.tbl_sheet.setItem(i, 2+day, QTableWidgetItem(code))
                self.color_cell(self.tbl_sheet.item(i, 2+day), code)
                
        self.recalculate_totals()

    def color_cell(self, item, code):
        color = self.CODE_COLORS.get(code, '#FFFFFF')
        from PyQt6.QtGui import QColor, QBrush
        item.setBackground(QBrush(QColor(color)))

    def on_cell_changed(self, item):
        col = item.column()
        if col < 3 or col >= 34: return
        row = item.row()
        emp_id = int(get_employees()[row]['id'])
        day = col - 2
        code = item.text()
        rate = float(self.tbl_sheet.item(row, 2).text() or 1.0)
        hours = (rate * 8.0) if code == 'Ф/Я' else 0.0
        
        # Сохраняем в БД сразу
        save_month_data(self.current_year, self.current_month, 
                        [{'emp_id': emp_id, 'day': day, 'code': code, 'hours': hours}])
        self.color_cell(item, code)
        self.recalculate_totals()

    def recalculate_totals(self):
        for r in range(self.tbl_sheet.rowCount()):
            d15 = h15 = d16 = h16 = d_all = h_all = 0.0
            rate = float(self.tbl_sheet.item(r, 2).text() or 1.0)
            for day in range(1, 32):
                code = self.tbl_sheet.item(r, 2+day).text()
                if code and code != '':
                    h = rate * 8.0 if code == 'Ф/Я' else 0.0
                    if day <= 15: d15 += 1; h15 += h
                    else: d16 += 1; h16 += h
                    d_all += 1; h_all += h
            self.tbl_sheet.setItem(r, 34, QTableWidgetItem(str(int(d15))))
            self.tbl_sheet.setItem(r, 35, QTableWidgetItem(f"{h15:.1f}"))
            self.tbl_sheet.setItem(r, 36, QTableWidgetItem(str(int(d16))))
            self.tbl_sheet.setItem(r, 37, QTableWidgetItem(f"{h16:.1f}"))
            self.tbl_sheet.setItem(r, 38, QTableWidgetItem(str(int(d_all))))
            self.tbl_sheet.setItem(r, 39, QTableWidgetItem(f"{h_all:.1f}"))

    def apply_calendar(self):
        apply_calendar_to_db(self.current_year, self.current_month, 
                             globals()['db']) # Используем глобальный импорт функций
        self.load_timesheet()
        self.statusBar().showMessage("Календарь применен")

    def save_current_month(self):
        self.statusBar().showMessage("Сохранено")

    def export_to_excel(self):
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить Excel", "", "Excel Files (*.xlsx)")
        if not path: return
        settings = {k: get_setting(k) for k in ['institution', 'department', 'responsible', 'head_dept', 'accountant']}
        emps = get_employees()
        # Собираем данные из таблицы в формат {emp_id: {day: {code, hours}}}
        month_data = {}
        for r, emp in enumerate(emps):
            eid = emp['id']
            month_data[eid] = {}
            for day in range(1, 32):
                code = self.tbl_sheet.item(r, 2+day).text()
                h = float(self.tbl_sheet.item(r, 35).text() if day<=15 else self.tbl_sheet.item(r, 37).text()) if False else 0
                # Пересчитаем часы корректно из БД или прямо из сетки
                rate = float(emp['rate'])
                hours = rate * 8.0 if code == 'Ф/Я' else 0.0
                month_data[eid][day] = {'code': code, 'hours': hours}
                
        try:
            generate_excel(path, settings, emps, month_data, self.current_year, self.current_month)
            self.statusBar().showMessage(f"Экспортировано: {os.path.basename(path)}")
            QMessageBox.information(self, "Успех", "Файл успешно сформирован!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка экспорта", str(e))
