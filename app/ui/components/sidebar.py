from PySide6.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QListWidgetItem, 
                               QPushButton, QLabel)
from PySide6.QtCore import Qt, Signal
from app.ui import style
from app.core import config

class Sidebar(QWidget):
    # Signal to change page (sends page index number)
    page_changed = Signal(int)
    
    def __init__(self, user_role):
        """
        Handle   Init   operation.
        """
        super().__init__()
        self.user_role = user_role
        
        # Original container style
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
        # Important note: we use itemClicked instead of currentRowChanged
        # so that we can read the data stored in the item
        self.menu_list.itemClicked.connect(self.on_menu_click)
        
        # --- Definition of menu items with "actual page number" ---
        # Structure: ("displayname", "access", "index number in MainWindow")
        # These numbers must be exactly the same as the order of addWidget in main_window.py
        menu_structure = [
            ("Dashboard",          "all",   0),
            ("Projects Manager",   "all",   1),
            ("Assets Manager",     "all",   2),
            ("Production Tracker", "all",   3),            
            ("Studio & Depts",     "admin", 4), 
            ("User Management",    "admin", 5),            
            ("Validation Rules",   "admin", 7), # Index 7 for validation according to your code
            ("Naming Standards",   "admin", 8),  # Index 8 for the new naming system
            ("Settings",           "all",   6)
        ]
        
        for title, role, page_index in menu_structure:
            # Filtering logic based on user role
            if role == "all" or role == self.user_role:
                item = QListWidgetItem(title)
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                
                # --- Key tip: store the actual page number inside the item ---
                item.setData(Qt.UserRole, page_index)
                
                self.menu_list.addItem(item)
            
        # Default selection (dashboard)
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
        """When the item is clicked, it reads and sends the actual page number"""
        real_page_index = item.data(Qt.UserRole)
        self.page_changed.emit(real_page_index)