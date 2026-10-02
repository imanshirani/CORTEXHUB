from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, QComboBox, 
                               QPushButton, QHBoxLayout, QColorDialog, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from app.ui import style
from app.core import config

class DeptDialog(QDialog):
    def __init__(self, session, dept_to_edit=None, parent=None):
        """
        Handle   Init   operation.
        """
        super().__init__(parent)
        self.session = session
        self.dept_to_edit = dept_to_edit
        
        # Default color (gray)
        self.selected_color = "#888888"
        
        title = "Edit Department" if dept_to_edit else "Add Department"
        self.setWindowTitle(title)
        self.resize(300, 250)
        self.setStyleSheet(style.DIALOG_STYLESHEET)
        
        self.layout = QVBoxLayout(self)
        self.setup_ui()
        
        if self.dept_to_edit:
            self.load_data()

    def setup_ui(self):
        """
        Handle Setup Ui operation.
        """
        # Name
        self.layout.addWidget(QLabel("Department Name:"))
        self.name_input = QLineEdit()
        self.name_input.setStyleSheet(style.INPUT_STYLE)
        self.layout.addWidget(self.name_input)

        # --- Software ---
        self.layout.addWidget(QLabel("Allowed Software:"))
        self.sw_combo = QComboBox()
        self.sw_combo.setStyleSheet(style.COMBOBOX_STYLE)
        softwares = self.session.db.get_software_list()
        self.sw_combo.addItems(softwares)
        self.layout.addWidget(self.sw_combo)

        # --- Render Engine ---
        self.layout.addWidget(QLabel("Default Render Engine:"))
        self.engine_combo = QComboBox()
        self.engine_combo.setStyleSheet(style.COMBOBOX_STYLE)
        engines = self.session.db.get_render_engines_list()
        self.engine_combo.addItems(engines)
        self.layout.addWidget(self.engine_combo)

        # Color Picker
        self.layout.addWidget(QLabel("Color Code:"))
        
        color_layout = QHBoxLayout()
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(50, 30)
        self.color_btn.setStyleSheet(f"background-color: {self.selected_color}; border: 1px solid #555;")
        self.color_btn.clicked.connect(self.pick_color)
        
        self.color_hex_lbl = QLabel(self.selected_color)
        
        color_layout.addWidget(self.color_btn)
        color_layout.addWidget(self.color_hex_lbl)
        color_layout.addStretch()
        self.layout.addLayout(color_layout)

        self.layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("Save")
        self.btn_save.setStyleSheet(style.BTN_SUCCESS)
        self.btn_save.setObjectName("LoginButton")
        self.btn_save.clicked.connect(self.save_dept)
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setStyleSheet(style.BTN_SECONDARY)
        self.btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        self.layout.addLayout(btn_layout)

    def pick_color(self):
        """Open the color palette"""
        color = QColorDialog.getColor(QColor(self.selected_color), self, "Select Department Color")
        if color.isValid():
            self.selected_color = color.name() # Hex format (#RRGGBB)
            self.color_btn.setStyleSheet(f"background-color: {self.selected_color}; border: 1px solid #555;")
            self.color_hex_lbl.setText(self.selected_color)

    def load_data(self):
        """
        Handle Load Data operation.
        """
        # Load name and color
        self.name_input.setText(self.dept_to_edit.get('name', ""))
        self.selected_color = self.dept_to_edit.get('color', "#888888")
        
        # 1. Loading the software in the combo box
        if 'allowed_software' in self.dept_to_edit:
            sw_value = self.dept_to_edit['allowed_software']
            # If the value was All in the database, it must be set exactly with the combobox option
            index = self.sw_combo.findText(sw_value, Qt.MatchExactly)
            if index >= 0:
                self.sw_combo.setCurrentIndex(index)
            else:
                # If case is different, find it like this
                index = self.sw_combo.findText(sw_value, Qt.MatchFixedString)
                if index >= 0: self.sw_combo.setCurrentIndex(index)
        
        # 2. Loading the engine in combobox
        if 'render_engine' in self.dept_to_edit:
            eng_value = self.dept_to_edit['render_engine']
            index = self.engine_combo.findText(eng_value, Qt.MatchExactly)
            if index >= 0:
                self.engine_combo.setCurrentIndex(index)

        # Update the appearance of the color button
        self.color_btn.setStyleSheet(f"background-color: {self.selected_color}; border: 1px solid #555;")
        self.color_hex_lbl.setText(self.selected_color)

    def save_dept(self):
        """
        Handle Save Dept operation.
        """
        name = self.name_input.text()
        sw = self.sw_combo.currentText()
        engine = self.engine_combo.currentText()
        
        if not name:
            QMessageBox.warning(self, "Error", "Department name is required.")
            return

        if self.dept_to_edit:
            # Edit mode
            success = self.session.db.update_department_extended(
                self.dept_to_edit['id'], name, self.selected_color, sw, engine
            )
        else:
            # New construction mode (we added this method to the database in the first step)
            success = self.session.db.create_department_extended(
                name, self.selected_color, sw, engine
            )

        if success:
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Failed to save department.")