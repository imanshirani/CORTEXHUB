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
        
        # Window settings
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(350, 450)
        
        # The main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Main container
        self.bg_frame = QFrame()
        self.bg_frame.setStyleSheet(style.LOGIN_BG_FRAME) # Use style
        
        # the shadow
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

        # 1. Close button
        top_layout = QHBoxLayout()
        top_layout.addStretch()
        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(30, 30)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setStyleSheet(style.LOGIN_CLOSE_BTN) # Use style
        self.btn_close.clicked.connect(self.reject)
        top_layout.addWidget(self.btn_close)
        layout.addLayout(top_layout)

        # 2. Logo and title
        title = QLabel(f"{config.APP_NAME}")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(style.LOGIN_TITLE) # Use style
        layout.addWidget(title)

        
        
        subtitle = QLabel(f"{config.SUBTITLE}")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(style.LOGIN_SUBTITLE) # Use style
        layout.addWidget(subtitle)

        # 3. Entries
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Username")
        self.user_input.setFixedHeight(45)
        self.user_input.setStyleSheet(style.LOGIN_INPUT) # Use style
        layout.addWidget(self.user_input)

        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Password")
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_input.setFixedHeight(45)
        self.pass_input.setStyleSheet(style.LOGIN_INPUT) # Use style
        layout.addWidget(self.pass_input)

        # 4. Label error
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setStyleSheet(style.LOGIN_ERROR_LBL) # Use style
        self.error_label.setFixedHeight(20)
        layout.addWidget(self.error_label)

        # 5. Login button
        self.btn_login = QPushButton("LOGIN")
        self.btn_login.setCursor(Qt.PointingHandCursor)
        self.btn_login.setFixedHeight(45)
        self.btn_login.setStyleSheet(style.LOGIN_BTN) # Use style
        self.btn_login.clicked.connect(self.check_login)
        layout.addWidget(self.btn_login)
        
        # 6. Version
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
        # Reset the style to normal
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
        """Change border color to red in case of error"""
        # Using the style error that we defined in the style file
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