
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QComboBox,
                             QTableWidgetItem, QPushButton, QLabel, QHeaderView, QMessageBox)
from PySide6.QtCore import Qt
from app.ui import style
from app.ui.naming_standard_dialog import NamingStandardDialog

class NamingStandardView(QWidget):
    def __init__(self, session, project_id):
        """
        Handle   Init   operation.
        """
        super().__init__()
        self.session = session
        self.db = session.db
        self.project_id = project_id
        
        self.setup_ui()
        self.refresh_table()

    def setup_ui(self):
        """
        Handle Setup Ui operation.
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # --- ۱. اضافه کردن انتخاب‌گر پروژه برای رفع مشکل None بودن ID ---
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Filter by Project:"))
        
        self.project_combo = QComboBox()
        self.project_combo.setStyleSheet(style.COMBOBOX_STYLE)
        self.project_combo.setMinimumWidth(250)
        
        # لود کردن لیست پروژه‌ها از دیتابیس
        projects = self.db.get_all_projects()
        for proj in projects:
            self.project_combo.addItem(proj.name, proj.id)
            
        self.project_combo.currentIndexChanged.connect(self.on_project_changed)
        selector_layout.addWidget(self.project_combo)
        selector_layout.addStretch()
        layout.addLayout(selector_layout)

        # --- ۲. هدر و دکمه افزودن ---
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("<h2>Naming Standards</h2>"))
        header_layout.addStretch()
        
        self.btn_add = QPushButton("+ Add Standard")
        self.btn_add.setStyleSheet(style.BTN_SUCCESS)
        self.btn_add.clicked.connect(self.open_add_dialog)
        header_layout.addWidget(self.btn_add)
        
        layout.addLayout(header_layout)

        # --- ۳. جدول نمایش داده‌ها ---
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Category", "Prefix", "Suffix", "Hierarchy", "Actions"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet(style.TABLE_MANAGER)
        layout.addWidget(self.table)

        # اجرای اولیه برای لود دیتای اولین پروژه
        self.on_project_changed()

    def on_project_changed(self):
        """آپدیت آیدی پروژه و رفرش جدول"""
        self.project_id = self.project_combo.currentData()
        self.refresh_table()

    def refresh_table(self):
        """
        Handle Refresh Table operation.
        """
        self.table.setRowCount(0)

        # اگر هنوز پروژه‌ای انتخاب نشده، از متد خارج شو
        if not self.project_id:
            return

        # فراخوانی متد دیتابیس با آیدی پروژه انتخاب شده
        standards = self.db.get_naming_standards(self.project_id)
        
        for row_idx, std in enumerate(standards):
            self.table.insertRow(row_idx)
            # نمایش ستون‌ها بر اساس ساختار متد get_naming_standards
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(std[2]))) # Category
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(std[3]))) # Prefix
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(std[4]))) # Suffix
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(std[5]))) # Hierarchy

            # بخش دکمه‌های عملیاتی (بدون تغییر)
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            btn_edit = QPushButton("Edit")
            btn_edit.setStyleSheet(style.BTN_ACTION_EDIT)
            btn_edit.clicked.connect(lambda _, s=std: self.open_edit_dialog(s))
            
            btn_del = QPushButton("Del")
            btn_del.setStyleSheet(style.BTN_ACTION_DEL)
            btn_del.clicked.connect(lambda _, s=std: self.on_delete(s[0]))
            
            actions_layout.addWidget(btn_edit)
            actions_layout.addWidget(btn_del)
            self.table.setCellWidget(row_idx, 4, actions_widget)

    

    def load_projects_list(self):
        """پر کردن لیست پروژه‌ها از دیتابیس"""
        self.project_combo.clear()
        projects = self.db.get_all_projects()
        for proj in projects:
            self.project_combo.addItem(proj.name, proj.id)

    def on_project_changed(self):
        """آپدیت کردن آیدی پروژه فعلی"""
        self.project_id = self.project_combo.currentData()
        self.refresh_table()

    def open_add_dialog(self):
        """
        Handle Open Add Dialog operation.
        """
        # حتما self.project_id را پاس بده
        dialog = NamingStandardDialog(self.session, self.project_id, parent=self)
        if dialog.exec():
            self.refresh_table()

    def open_edit_dialog(self, std_data):
        """
        Handle Open Edit Dialog operation.
        """
        std_dict = {
            "id": std_data[0], "category": std_data[2], 
            "prefix": std_data[3], "suffix": std_data[4], "required_hierarchy": std_data[5]
        }
        if NamingStandardDialog(self.session, self.project_id, standard_to_edit=std_dict, parent=self).exec():
            self.refresh_table()

    def on_delete(self, std_id):
        """
        Handle On Delete operation.
        """
        if QMessageBox.question(self, "Delete", "Are you sure?") == QMessageBox.Yes:
            if self.db.delete_naming_standard(std_id):
                self.refresh_table()