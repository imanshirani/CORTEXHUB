from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                               QTableWidgetItem, QPushButton, QHeaderView, QMessageBox, QLabel)
from PySide6.QtCore import Qt
from app.ui import style
from app.ui.user_dialog import UserDialog

class UsersView(QWidget):
    def __init__(self, session):
        """
        Handle   Init   operation.
        """
        super().__init__()
        self.session = session
        
        layout = QVBoxLayout(self)
        
        # 1. Layout settings (same as Projects View)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # 2. Header
        header_layout = QHBoxLayout()
        title = QLabel("Manage Users")
        title.setStyleSheet(style.SECTION_TITLE)
        
        self.btn_add = QPushButton("+ Add User")
        self.btn_add.setFixedSize(120, 35)
        self.btn_add.setCursor(Qt.PointingHandCursor)
        self.btn_add.setStyleSheet(style.BTN_NEW_PROJECT) # Standard green button
        self.btn_add.clicked.connect(self.open_add_dialog)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_add)
        layout.addLayout(header_layout)

        # 3. Users table
        self.table = QTableWidget()
        self.table.setColumnCount(5) # Changed from 4 to 5
        self.table.setHorizontalHeaderLabels(["Name", "Username", "Role", "Department", "Actions"])
        
        # Disable in-cell editing (double-click)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # Column setup
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch) # Name
        header.setSectionResizeMode(1, QHeaderView.Stretch) # Username
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        self.table.setColumnWidth(2, 80) # Role
        header.setSectionResizeMode(3, QHeaderView.Stretch) # Department [NEW]
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        self.table.setColumnWidth(4, 140) # Actions
        
        # Table appearance
        self.table.verticalHeader().setDefaultSectionSize(50) # Row height
        self.table.verticalHeader().setVisible(True) # Show row numbers
        self.table.setStyleSheet(style.PROJECTS_TABLE)
        
        layout.addWidget(self.table)
        
        # Refresh button (optional; we usually refresh automatically)
        # layout.addWidget(self.btn_refresh) 

        self.load_users()

    def load_users(self):
        """
        Handle Load Users operation.
        """
        self.table.setRowCount(0)
        users = self.session.db.get_all_users()
        
        for row_idx, user in enumerate(users):
            self.table.insertRow(row_idx)
            
            # Columns 0-2: basic info
            self.table.setItem(row_idx, 0, QTableWidgetItem(user.full_name))
            self.table.setItem(row_idx, 1, QTableWidgetItem(user.username))
            self.table.setItem(row_idx, 2, QTableWidgetItem(user.role))
            
            # Column 3: department name (new)
            dept_name = "None"
            if hasattr(user, 'dept_id') and user.dept_id:
                dept_info = self.session.db.get_department_by_id(user.dept_id)
                if dept_info:
                    dept_name = dept_info[1] # Department name
            self.table.setItem(row_idx, 3, QTableWidgetItem(dept_name))
            
            # Column 4: action buttons (index fix)
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            
            btn_edit = QPushButton("Edit")
            btn_edit.setFixedSize(60, 28)
            btn_edit.setStyleSheet(style.BTN_ACTION_EDIT)
            btn_edit.clicked.connect(lambda _, u=user: self.open_edit_dialog(u))
            
            btn_del = QPushButton("Del")
            btn_del.setFixedSize(50, 28)
            btn_del.setStyleSheet(style.BTN_ACTION_DEL)
            btn_del.clicked.connect(lambda _, u=user: self.delete_user(u))
            
            actions_layout.addWidget(btn_edit)
            actions_layout.addWidget(btn_del)
            
            self.table.setCellWidget(row_idx, 4, actions_widget)

    def open_add_dialog(self):
        """
        Handle Open Add Dialog operation.
        """
        dialog = UserDialog(self.session, parent=self)
        if dialog.exec():
            self.load_users()

    def open_edit_dialog(self, user):
        """
        Handle Open Edit Dialog operation.
        """
        dialog = UserDialog(self.session, user_to_edit=user, parent=self)
        if dialog.exec():
            self.load_users()

    def delete_user(self, user):
        """
        Handle Delete User operation.
        """
        if user.username == self.session.context.user.username:
            QMessageBox.warning(self, "Stop", "You cannot delete yourself!")
            return
        confirm = QMessageBox.question(self, "Confirm", f"Delete user {user.full_name}?", 
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            if self.session.db.delete_user(user.id):
                self.load_users()