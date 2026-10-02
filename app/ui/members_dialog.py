from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QPushButton, 
                               QHBoxLayout, QListWidget, QListWidgetItem, QMessageBox)
from PySide6.QtCore import Qt
from app.ui import style

class ProjectMembersDialog(QDialog):
    def __init__(self, session, project, parent=None):
        """
        Handle   Init   operation.
        """
        super().__init__(parent)
        self.session = session
        self.project = project
        
        self.setWindowTitle(f"Manage Members: {project.name}")
        self.resize(300, 400)
        self.setStyleSheet(style.DIALOG_STYLESHEET)
        
        self.layout = QVBoxLayout(self)
        
        # title
        lbl = QLabel("Select users for this project:")
        lbl.setStyleSheet("color: #aaa; margin-bottom: 5px;")
        self.layout.addWidget(lbl)

        # List with checkboxes
        self.user_list = QListWidget()
        self.user_list.setStyleSheet(style.LIST_WIDGET_STYLE)
        self.layout.addWidget(self.user_list)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("Save Changes")
        self.btn_save.setStyleSheet(style.BTN_PRIMARY)
        self.btn_save.setObjectName("LoginButton")
        self.btn_save.clicked.connect(self.save_members)
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setStyleSheet(style.BTN_SECONDARY)
        self.btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        self.layout.addLayout(btn_layout)

        self.load_users()

    def load_users(self):
        """
        Handle Load Users operation.
        """
        # 1. Getting all system users
        all_users = self.session.db.get_all_users()
        
        # 2. Get the current members of this project (IDs only)
        current_member_ids = self.session.db.get_project_member_ids(self.project.id)
        
        for user in all_users:
            item = QListWidgetItem(f"{user.full_name} ({user.role})")
            item.setData(Qt.UserRole, user.id)
            
            # Add a checkbox
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            
            # If the user ID is in the list of members, check it
            if user.id in current_member_ids:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
                
            self.user_list.addItem(item)

    def save_members(self):
        """
        Handle Save Members operation.
        """
        # Collecting ticked user IDs
        selected_ids = []
        for i in range(self.user_list.count()):
            item = self.user_list.item(i)
            if item.checkState() == Qt.Checked:
                selected_ids.append(item.data(Qt.UserRole))
        
        # Save in database
        if self.session.db.update_project_members(self.project.id, selected_ids):
            QMessageBox.information(self, "Success", "Project members updated!")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Failed to update members.")