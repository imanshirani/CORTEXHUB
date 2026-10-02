from PySide6.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QListWidgetItem, 
                               QPushButton, QLabel)
from PySide6.QtCore import Qt, Signal
from app.ui import style
from app.core import config

class Sidebar(QWidget):
    # سیگنال برای تغییر صفحه (شماره ایندکس صفحه را می‌فرستد)
    page_changed = Signal(int)
    
    def __init__(self, user_role):
        """
        Handle   Init   operation.
        """
        super().__init__()
        self.user_role = user_role
        
        # استایل کانتینر اصلی
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(style.SIDEBAR_CONTAINER)
        self.setFixedWidth(260)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. Logo Area
        logo = QLabel(config.APP_NAME)
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet(style.SIDEBAR_LOGO)
        layout.addWidget(logo)
        
        # 2. Menu Items
        self.menu_list = QListWidget()
        self.menu_list.setStyleSheet(style.SIDEBAR_MENU)
        # نکته مهم: به جای currentRowChanged از itemClicked استفاده می‌کنیم
        # تا بتوانیم دیتای ذخیره شده در آیتم را بخوانیم
        self.menu_list.itemClicked.connect(self.on_menu_click)
        
        # --- تعریف آیتم‌های منو به همراه "شماره صفحه واقعی" ---
        # ساختار: ("نام نمایشی", "دسترسی", "شماره ایندکس در MainWindow")
        # این شماره‌ها باید دقیقاً با ترتیب addWidget در main_window.py یکی باشند
        menu_structure = [
            ("Dashboard",          "all",   0),
            ("Projects Manager",   "all",   1),
            ("Assets Manager",     "all",   2),
            ("Production Tracker", "all",   3),            
            ("Studio & Depts",     "admin", 4), 
            ("User Management",    "admin", 5),            
            ("Validation Rules",   "admin", 7), # ایندکس ۷ برای ولیدیشن طبق کد شما
            ("Naming Standards",   "admin", 8),  # ایندکس ۸ برای سیستم جدید نام‌گذاری
            ("Settings",           "all",   6)
        ]
        
        for title, role, page_index in menu_structure:
            # لاجیک فیلتر کردن بر اساس نقش کاربر
            if role == "all" or role == self.user_role:
                item = QListWidgetItem(title)
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                
                # --- نکته کلیدی: ذخیره شماره صفحه واقعی در داخل آیتم ---
                item.setData(Qt.UserRole, page_index)
                
                self.menu_list.addItem(item)
            
        # انتخاب پیش‌فرض (داشبورد)
        if self.menu_list.count() > 0:
            self.menu_list.setCurrentRow(0)
        
        layout.addWidget(self.menu_list)
        #layout.addStretch()
        
        # 3. Logout Button
        self.btn_logout = QPushButton(f"Logout ({self.user_role})")
        self.btn_logout.setCursor(Qt.PointingHandCursor)
        self.btn_logout.setStyleSheet(style.LOGOUT_BUTTON)
        layout.addWidget(self.btn_logout)

    def on_menu_click(self, item):
        """وقتی روی آیتم کلیک شد، شماره صفحه واقعی را می‌خواند و می‌فرستد"""
        real_page_index = item.data(Qt.UserRole)
        self.page_changed.emit(real_page_index)