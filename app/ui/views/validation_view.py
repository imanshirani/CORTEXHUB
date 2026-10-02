import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QComboBox, QLabel, 
                             QHeaderView, QMessageBox, QFrame)
from PySide6.QtCore import Qt
import app.ui.style as style
from app.ui.rule_dialog import RuleDialog 

class ValidationView(QWidget):
    def __init__(self, session, project_id=None):
        """
        Handle   Init   operation.
        """
        super().__init__()
        self.session = session
        self.db = session.db
        self.project_id = project_id
        
        self.setup_ui()

    def setup_ui(self):
        """
        Handle Setup Ui operation.
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # --- Project picker (so the table shows the right data) ---
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Filter by Project:"))
        
        self.project_combo = QComboBox()
        self.project_combo.setStyleSheet(style.COMBOBOX_STYLE)
        self.project_combo.setMinimumWidth(250)
        self.load_projects_list()
        self.project_combo.currentIndexChanged.connect(self.on_project_filter_changed)
        
        selector_layout.addWidget(self.project_combo)
        selector_layout.addStretch()
        layout.addLayout(selector_layout)

        # --- Header ---
        header_layout = QHBoxLayout()
        title = QLabel("Project Validation Rules")
        title.setStyleSheet(style.PROJECTS_TITLE)
        
        self.btn_add = QPushButton("+ New Rule")
        self.btn_add.setFixedSize(120, 35)
        self.btn_add.setStyleSheet(style.BTN_NEW_PROJECT)
        self.btn_add.setCursor(Qt.PointingHandCursor)
        self.btn_add.clicked.connect(self.open_add_rule_dialog)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_add)
        layout.addLayout(header_layout)

        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Rule Name", "Software", "Mandatory", "Actions"])
        self.table.setStyleSheet(style.PROJECTS_TABLE)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        self.table.setColumnWidth(1, 100)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        self.table.setColumnWidth(2, 120)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        self.table.setColumnWidth(3, 160)
        
        layout.addWidget(self.table)
        
        # Initial table load from the first project
        self.on_project_filter_changed()

    def load_projects_list(self):
        """Fill the project list in the top menu"""
        self.project_combo.clear()
        projects = self.db.get_all_projects()
        for proj in projects:
            self.project_combo.addItem(proj.name, proj.id)
        
        # If we already had an id, re-select it
        if self.project_id:
            idx = self.project_combo.findData(self.project_id)
            if idx >= 0: self.project_combo.setCurrentIndex(idx)

    def on_project_filter_changed(self):
        """When the project is changed from the top menu"""
        self.project_id = self.project_combo.currentData()
        self.refresh_table()

    def refresh_table(self):
        """
        Handle Refresh Table operation.
        """
        self.table.setRowCount(0)
        if not self.project_id:
            return
            
        # Call the database method that also returns scripts
        rules = self.db.get_all_validation_rules_extended(self.project_id)
        
        for row_idx, rule in enumerate(rules):
            # rule tuple: (id, software, rule_key, is_active, is_mandatory, rule_script)
            self.table.insertRow(row_idx)
            
            # 1. Rule name
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(rule[2])))
            
            # 2. Software
            soft_item = QTableWidgetItem(str(rule[1]).upper())
            soft_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 1, soft_item)
            
            # 3. Mandatory
            status_text = "YES" if rule[4] else "NO"
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 2, status_item)

            # 4. Action buttons
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 2, 5, 2)
            actions_layout.setSpacing(5)
            
            btn_edit = QPushButton("Edit")
            btn_edit.setStyleSheet(style.BTN_ACTION_EDIT)
            btn_edit.setFixedSize(60, 28)
            btn_edit.clicked.connect(lambda _, r=rule: self.open_edit_rule_dialog(r))
            
            btn_del = QPushButton("Del")
            btn_del.setStyleSheet(style.BTN_ACTION_DEL)
            btn_del.setFixedSize(50, 28)
            btn_del.clicked.connect(lambda _, r=rule: self.on_delete_rule(r[0]))
            
            actions_layout.addWidget(btn_edit)
            actions_layout.addWidget(btn_del)
            self.table.setCellWidget(row_idx, 3, actions_widget)

    def open_add_rule_dialog(self):
        """
        Handle Open Add Rule Dialog operation.
        """
        dialog = RuleDialog(self.session, self.project_id, parent=self)
        if dialog.exec():
            # Refresh the list immediately after the dialog is accepted
            self.refresh_table()

    def open_edit_rule_dialog(self, rule_data):
        """
        Handle Open Edit Rule Dialog operation.
        """
        # Map data for the dialog
        rule_dict = {
            "id": rule_data[0], "software": rule_data[1], "rule_key": rule_data[2], 
            "is_mandatory": rule_data[4], "rule_script": rule_data[5], "project_id": self.project_id
        }
        dialog = RuleDialog(self.session, self.project_id, rule_to_edit=rule_dict, parent=self)
        if dialog.exec():
            # Refresh the list immediately after edit
            self.refresh_table()

    def on_delete_rule(self, rule_id):
        """
        Handle On Delete Rule operation.
        """
        if QMessageBox.question(self, "Confirm", "Are you sure you want to delete this rule?") == QMessageBox.Yes:
            if self.db.delete_validation_rule(rule_id):
                self.refresh_table()