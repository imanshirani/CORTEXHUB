from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                               QPushButton, QHBoxLayout, QComboBox, QMessageBox)
from PySide6.QtCore import Qt
from app.ui import style

class UserDialog(QDialog):
    def __init__(self, session, user_to_edit=None, parent=None):
        """
        Handle   Init   operation.
        """
        super().__init__(parent)
        self.session = session
        self.user_to_edit = user_to_edit # If it has this value, it means we are in Edit mode
        
        title = "Edit User" if user_to_edit else "Add New User"
        self.setWindowTitle(title)
        self.resize(350, 450)
        self.setStyleSheet(style.DIALOG_STYLESHEET)
        
        self.layout = QVBoxLayout(self)
        self.setup_ui()
        
        if self.user_to_edit:
            self.load_user_data()

    def setup_ui(self):
        """
        Handle Setup Ui operation.
        """
        # Full Name
        self.layout.addWidget(QLabel("Full Name:"))
        self.fullname_input = QLineEdit()
        self.fullname_input.setStyleSheet(style.INPUT_STYLE)
        self.layout.addWidget(self.fullname_input)

        # Username
        self.layout.addWidget(QLabel("Username:"))
        self.username_input = QLineEdit()
        self.username_input.setStyleSheet(style.INPUT_STYLE)
        self.layout.addWidget(self.username_input)

        # Password
        self.layout.addWidget(QLabel("Password:"))
        self.password_input = QLineEdit()
        self.password_input.setStyleSheet(style.INPUT_STYLE)
        self.password_input.setPlaceholderText("Leave empty to keep current password" if self.user_to_edit else "")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.layout.addWidget(self.password_input)

        # Role
        self.layout.addWidget(QLabel("Role:"))
        self.role_combo = QComboBox()
        self.role_combo.setStyleSheet(style.COMBOBOX_STYLE)
        self.role_combo.addItems(["artist", "supervisor", "admin"])
        self.layout.addWidget(self.role_combo)

        # Department
        self.layout.addWidget(QLabel("Department:"))
        self.dept_combo = QComboBox()
        self.dept_combo.setStyleSheet(style.COMBOBOX_STYLE)
        # Loading departments by managing 5 database fields
        self.dept_combo.addItem("None", None)
        depts = self.session.db.get_all_departments()
        for d in depts:
            # d[0] id, d[1] name
            self.dept_combo.addItem(d[1], d[0])
        
        self.layout.addWidget(self.dept_combo)

        self.layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("Save")
        self.btn_save.setObjectName("LoginButton")
        self.btn_save.clicked.connect(self.save_user)
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        self.layout.addLayout(btn_layout)

    def load_user_data(self):
        """
        Handle Load User Data operation.
        """
        self.fullname_input.setText(self.user_to_edit.full_name)
        self.username_input.setText(self.user_to_edit.username)
        self.role_combo.setCurrentText(self.user_to_edit.role)
        
        # Selecting the user's department in edit mode
        if hasattr(self.user_to_edit, 'dept_id') and self.user_to_edit.dept_id:
            index = self.dept_combo.findData(self.user_to_edit.dept_id)
            if index >= 0:
                self.dept_combo.setCurrentIndex(index)

    def save_user(self):
        """
        Handle Save User operation.
        """
        data = {
            "full_name": self.fullname_input.text(),
            "username": self.username_input.text(),
            "password": self.password_input.text(),
            "role": self.role_combo.currentText(),
            "dept_id": self.dept_combo.currentData()
        }
        
        if not data["username"] or not data["full_name"]:
            QMessageBox.warning(self, "Error", "Username and Name are required!")
            return

        if self.user_to_edit:
            # Update Existing
            success = self.session.db.update_user(
                self.user_to_edit.id, 
                data["full_name"], data["username"], data["password"], 
                data["role"], data["dept_id"]
            )
        else:
            # Create New
            if not data["password"]:
                QMessageBox.warning(self, "Error", "Password is required for new users!")
                return
            success = self.session.db.create_user(
                data["username"], data["password"], data["full_name"], 
                data["role"], data["dept_id"]
            )

        if success:
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Operation failed (Username might be taken).")