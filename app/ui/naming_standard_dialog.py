
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                               QPushButton, QHBoxLayout, QComboBox, QMessageBox)
from PySide6.QtCore import Qt
from app.ui import style

class NamingStandardDialog(QDialog):
    def __init__(self, session, project_id=None, standard_to_edit=None, parent=None):
        """
        Handle   Init   operation.
        """
        super().__init__(parent)
        self.session = session
        self.db = session.db
        self.project_id = project_id
        self.standard_to_edit = standard_to_edit
        
        self.setWindowTitle("Edit Naming Standard" if standard_to_edit else "Add Naming Standard")
        self.resize(450, 500)
        self.setStyleSheet(style.DARK_THEME)
        
        self.setup_ui()
        if self.standard_to_edit:
            self.load_data()

    def setup_ui(self):
        """
        Handle Setup Ui operation.
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        # Category (e.g. Characters, Props)
        layout.addWidget(QLabel("Asset Category:"))
        self.cat_combo = QComboBox()
        self.cat_combo.addItems(["Characters", "Props", "Environments", "Vehicles"])
        self.cat_combo.setStyleSheet(style.COMBOBOX_STYLE)
        layout.addWidget(self.cat_combo)

        # Prefix
        layout.addWidget(QLabel("Required Prefix (e.g. CHR_):"))
        self.prefix_input = QLineEdit()
        self.prefix_input.setStyleSheet(style.INPUT_STYLE)
        layout.addWidget(self.prefix_input)

        # Suffix
        layout.addWidget(QLabel("Required Suffix:"))
        self.suffix_input = QLineEdit()
        self.suffix_input.setStyleSheet(style.INPUT_STYLE)
        layout.addWidget(self.suffix_input)

        # Required Hierarchy
        layout.addWidget(QLabel("Required Objects (Comma separated):"))
        self.hierarchy_input = QLineEdit()
        self.hierarchy_input.setPlaceholderText("e.g. Body, Head, Rig")
        self.hierarchy_input.setStyleSheet(style.INPUT_STYLE)
        layout.addWidget(self.hierarchy_input)

        layout.addStretch()

        # Save Button
        self.btn_save = QPushButton("Save Standard")
        self.btn_save.setStyleSheet(style.BTN_SUCCESS)
        self.btn_save.clicked.connect(self.save_standard)
        layout.addWidget(self.btn_save)

    def load_data(self):
        """
        Handle Load Data operation.
        """
        self.cat_combo.setCurrentText(self.standard_to_edit['category'])
        self.prefix_input.setText(self.standard_to_edit.get('prefix', ''))
        self.suffix_input.setText(self.standard_to_edit.get('suffix', ''))
        self.hierarchy_input.setText(self.standard_to_edit.get('required_hierarchy', ''))

    def save_standard(self):
        """
        Handle Save Standard operation.
        """
        if not self.project_id:
            QMessageBox.warning(self, "Error", "No project context found!")
            return

        data = {
            "project_id": self.project_id, # حتما از مقداری که از View آمده استفاده کن
            "category": self.cat_combo.currentText(),
            "prefix": self.prefix_input.text().strip(),
            "suffix": self.suffix_input.text().strip(),
            "required_hierarchy": self.hierarchy_input.text().strip()
        }
        
        if self.standard_to_edit:
            success = self.db.update_naming_standard(self.standard_to_edit['id'], data)
        else:
            success = self.db.add_naming_standard(data)

        if success:
            print(f">> Naming Standard Saved for project: {self.project_id}") # برای دیباگ
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Failed to save naming standard.")