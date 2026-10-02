from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                               QPushButton, QFrame, QHBoxLayout, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from app.ui import style
from app.core import config

class LoginDialog(QDialog):
    def __init__(self, session):
        """
        Handle   Init   operation.
        """
        super().__init__()
        self.session = session
        
        # تنظیمات پنجره
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(350, 450)
        
        # لایوت اصلی
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # کانتینر اصلی
        self.bg_frame = QFrame()
        self.bg_frame.setStyleSheet(style.LOGIN_BG_FRAME) # استفاده از استایل
        
        # سایه
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 150))
        self.bg_frame.setGraphicsEffect(shadow)
        
        main_layout.addWidget(self.bg_frame)
        self.setup_ui()

    def setup_ui(self):
        """
        Handle Setup Ui operation.
        """
        layout = QVBoxLayout(self.bg_frame)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 40, 30, 30)

        # 1. دکمه بستن
        top_layout = QHBoxLayout()
        top_layout.addStretch()
        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(30, 30)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setStyleSheet(style.LOGIN_CLOSE_BTN) # استفاده از استایل
        self.btn_close.clicked.connect(self.reject)
        top_layout.addWidget(self.btn_close)
        layout.addLayout(top_layout)

        # 2. لوگو و عنوان
        title = QLabel(f"{config.APP_NAME}")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(style.LOGIN_TITLE) # استفاده از استایل
        layout.addWidget(title)

        
        
        subtitle = QLabel(f"{config.SUBTITLE}")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(style.LOGIN_SUBTITLE) # استفاده از استایل
        layout.addWidget(subtitle)

        # 3. ورودی‌ها
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Username")
        self.user_input.setFixedHeight(45)
        self.user_input.setStyleSheet(style.LOGIN_INPUT) # استفاده از استایل
        layout.addWidget(self.user_input)

        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Password")
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_input.setFixedHeight(45)
        self.pass_input.setStyleSheet(style.LOGIN_INPUT) # استفاده از استایل
        layout.addWidget(self.pass_input)

        # 4. لیبل ارور
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setStyleSheet(style.LOGIN_ERROR_LBL) # استفاده از استایل
        self.error_label.setFixedHeight(20)
        layout.addWidget(self.error_label)

        # 5. دکمه لاگین
        self.btn_login = QPushButton("LOGIN")
        self.btn_login.setCursor(Qt.PointingHandCursor)
        self.btn_login.setFixedHeight(45)
        self.btn_login.setStyleSheet(style.LOGIN_BTN) # استفاده از استایل
        self.btn_login.clicked.connect(self.check_login)
        layout.addWidget(self.btn_login)
        
        # 6. ورژن
        version_label = QLabel(f"{config.VERSION}")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet(style.LOGIN_VERSION)
        layout.addWidget(version_label)

        layout.addStretch()

        self.user_input.returnPressed.connect(self.check_login)
        self.pass_input.returnPressed.connect(self.check_login)

        self.old_pos = None

    def check_login(self):
        """
        Handle Check Login operation.
        """
        username = self.user_input.text()
        password = self.pass_input.text()

        self.error_label.setText("") 
        # ریست کردن استایل به حالت عادی
        self.user_input.setStyleSheet(style.LOGIN_INPUT)
        self.pass_input.setStyleSheet(style.LOGIN_INPUT)

        if not username or not password:
            self.error_label.setText("Please enter username and password")
            self.shake_window()
            return

        if self.session.login(username, password):
            self.accept()
        else:
            self.error_label.setText("Invalid Username or Password")
            self.shake_window()

    def shake_window(self):
        """تغییر رنگ بوردر به قرمز در صورت خطا"""
        # استفاده از استایل ارور که در فایل style تعریف کردیم
        self.user_input.setStyleSheet(style.LOGIN_INPUT_ERROR)
        self.pass_input.setStyleSheet(style.LOGIN_INPUT_ERROR)

    # --- Drag Logic ---
    def mousePressEvent(self, event):
        """
        Handle Mousepressevent operation.
        """
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        """
        Handle Mousemoveevent operation.
        """
        if self.old_pos:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        """
        Handle Mousereleaseevent operation.
        """
        self.old_pos = None