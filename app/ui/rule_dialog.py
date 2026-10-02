# app/ui/rule_dialog.py
import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                               QPushButton, QHBoxLayout, QComboBox, QMessageBox, QTextEdit, QCheckBox)
from PySide6.QtCore import Qt
from app.ui import style # Using Cortex central styles

class RuleDialog(QDialog):
    def __init__(self, session, project_id=None, rule_to_edit=None, parent=None):
        """
        Handle   Init   operation.
        """
        super().__init__(parent)
        self.session = session
        self.db = session.db
        self.project_id = project_id
        self.rule_to_edit = rule_to_edit
        
        # Set title based on edit or add mode
        self.setWindowTitle("Edit Validation Rule" if rule_to_edit else "Add New Validation Rule")
        self.resize(700, 750)
        self.setStyleSheet(style.DARK_THEME) # Actions you are real
        
        self.setup_ui()
        
        if self.rule_to_edit:
            self.load_data()

    def setup_ui(self):
        """
        Handle Setup Ui operation.
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        # --- Project selection ---
        layout.addWidget(QLabel("Associated Project:"))
        self.project_combo = QComboBox()
        self.project_combo.setStyleSheet(style.COMBOBOX_STYLE) # Cortex combo box style
        self.load_projects()
        layout.addWidget(self.project_combo)

        # --- The name of the law ---
        layout.addWidget(QLabel("Rule Name (Key):"))
        self.name_input = QLineEdit()
        self.name_input.setStyleSheet(style.INPUT_STYLE) # Text input style
        self.name_input.setPlaceholderText("e.g. check_missing_textures")
        layout.addWidget(self.name_input)

        # --- Software selection ---
        layout.addWidget(QLabel("Target Software:"))
        self.soft_combo = QComboBox()
        self.soft_combo.setStyleSheet(style.COMBOBOX_STYLE) #
        self.soft_combo.addItems(["all", "max", "blender", "maya"])
        layout.addWidget(self.soft_combo)

        # --- Mandatory status ---
        self.check_mandatory = QCheckBox("Mandatory (Stops Publish on Error)")
        self.check_mandatory.setStyleSheet(style.CHECKBOX_STYLE) # Checkbox style
        self.check_mandatory.setChecked(True)
        layout.addWidget(self.check_mandatory)

        # --- Python script ---
        layout.addWidget(QLabel("Python Logic Script:"))
        self.script_input = QTextEdit()
        # Exclusive style for the code editor
        self.script_input.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #dcdcdc;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 13px;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        self.script_input.setPlaceholderText("# Access to: self (publisher), is_mandatory, errors (list), warnings (list)")
        layout.addWidget(self.script_input)

        # --- Operation buttons ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.btn_save = QPushButton("Save Rule")
        self.btn_save.setStyleSheet(style.BTN_SUCCESS) # Green button
        self.btn_save.setFixedHeight(35)
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.clicked.connect(self.save_rule)
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setStyleSheet(style.BTN_SECONDARY) # Gray button
        self.btn_cancel.setFixedHeight(35)
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

    def load_projects(self):
        """Get the list of projects from the database"""
        self.project_combo.clear()
        projects = self.db.get_all_projects()
        for proj in projects:
            self.project_combo.addItem(proj.name, proj.id)
        
        if self.project_id:
            index = self.project_combo.findData(self.project_id)
            if index >= 0: self.project_combo.setCurrentIndex(index)

    def load_data(self):
        """Load rule information for editing"""
        self.name_input.setText(self.rule_to_edit.get('rule_key', ''))
        self.soft_combo.setCurrentText(self.rule_to_edit.get('software', 'all'))
        self.script_input.setPlainText(self.rule_to_edit.get('rule_script', ''))
        self.check_mandatory.setChecked(bool(self.rule_to_edit.get('is_mandatory', 1)))

    def save_rule(self):
        """Data collection and sending to the database"""
        selected_project_id = self.project_combo.currentData()
        name = self.name_input.text().strip()
        script = self.script_input.toPlainText().strip()
        
        if not selected_project_id or not name or not script:
            QMessageBox.warning(self, "Missing Data", "Please fill all fields before saving.")
            return

        rule_data = {
            "project_id": selected_project_id,
            "software": self.soft_combo.currentText(),
            "rule_key": name,
            "rule_script": script,
            "is_mandatory": 1 if self.check_mandatory.isChecked() else 0
        }
        
        # Calling new methods in the database
        if self.rule_to_edit:
            success = self.db.update_validation_rule(self.rule_to_edit['id'], rule_data)
        else:
            success = self.db.add_validation_rule_with_script(rule_data)
        
        if success:
            self.accept()
        else:
            # Detailed error display if not registered
            QMessageBox.critical(self, "Database Error", "Failed to save rule in Database.\nCheck console for SQL errors.")