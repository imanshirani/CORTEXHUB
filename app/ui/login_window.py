from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                               QPushButton)
from PySide6.QtCore import Qt
from app.ui import style
from app.core import config

class LoginWindow(QDialog): # <--- تغییر مهم: ارث‌بری از QDialog
    def __init__(self, session_manager):
        """
        Handle   Init   operation.
        """
        super().__init__()
        self.session = session_manager # دریافت سشن از ورودی
        
        self.setWindowTitle("Cortex Login")
        self.setFixedSize(350, 450)
        self.setStyleSheet(style.DARK_THEME)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(15)
        
        self.setup_ui()

    def setup_ui(self):
        """
        Handle Setup Ui operation.
        """
        # 1. Title
        title = QLabel("CORTEX HUB")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #007acc; margin-bottom: 20px;")
        self.layout.addWidget(title)

        # 2. Inputs
        self.layout.addWidget(QLabel("Username"))
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Enter username")
        self.user_input.setStyleSheet(style.LOGIN_INPUT)
        self.layout.addWidget(self.user_input)

        self.layout.addWidget(QLabel("Password"))
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_input.setStyleSheet(style.LOGIN_INPUT)
        self.pass_input.returnPressed.connect(self.handle_login)
        self.layout.addWidget(self.pass_input)

        # 3. Error Label
        self.error_lbl = QLabel("")
        self.error_lbl.setStyleSheet("color: #ff5555; font-size: 12px;")
        self.error_lbl.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.error_lbl)

        # 4. Button
        self.btn_login = QPushButton("Login")
        self.btn_login.setCursor(Qt.PointingHandCursor)
        self.btn_login.setFixedHeight(40)
        self.btn_login.setStyleSheet(style.LOGIN_BTN)
        self.btn_login.clicked.connect(self.handle_login)
        self.layout.addWidget(self.btn_login)

        version = QLabel(f"Version {config.VERSION}")
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet(style.ABOUT_VERSION)
        self.layout.addWidget(version)
        
        self.layout.addStretch()

    def handle_login(self):
        """
        Handle Handle Login operation.
        """
        username = self.user_input.text().strip()
        password = self.pass_input.text().strip()

        # استفاده از متد لاگین سشن منیجر
        if self.session.login(username, password):
            self.accept() # <--- مهم: این دستور پنجره را با موفقیت می‌بندد و exec را رد می‌کند
        else:
            self.error_lbl.setText("Invalid username or password")