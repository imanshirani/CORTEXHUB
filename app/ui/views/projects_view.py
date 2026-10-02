from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                               QTableWidgetItem, QPushButton, QHeaderView, QMessageBox, QLabel)
from PySide6.QtCore import Qt
from app.ui import style
from app.ui.project_dialog import ProjectDialog
from app.ui.members_dialog import ProjectMembersDialog
from PySide6.QtCore import Signal

class ProjectsView(QWidget):
    project_selected = Signal(str)

    def on_project_clicked(self):
        """
        Handle On Project Clicked operation.
        """
        # Find the selected project id from the table
        row = self.table.currentRow()
        project_id = self.table.item(row, 0).text() 
        
        # Broadcast a signal to the rest of the app
        self.project_selected.emit(project_id)
        
    def __init__(self, session):
        """
        Handle   Init   operation.
        """
        super().__init__()
        self.session = session
        
        layout = QVBoxLayout(self)
        
        # 1. Set margins from the edges (same as the users page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # --- Header ---
        header_layout = QHBoxLayout()
        
        # Title
        title = QLabel("Active Projects")
        title.setStyleSheet(style.PROJECTS_TITLE)
        
        # Green button
        self.btn_add = QPushButton("+ New Project")
        self.btn_add.setFixedSize(120, 35)
        self.btn_add.setCursor(Qt.PointingHandCursor)
        self.btn_add.setStyleSheet(style.BTN_NEW_PROJECT)
        self.btn_add.clicked.connect(self.open_add_dialog)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_add)
        layout.addLayout(header_layout)

        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(5) 
        self.table.setHorizontalHeaderLabels(["Project Name", "Code", "Root Path", "Status", "Actions"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # --- 2. Exact column widths (main fix) ---
        header = self.table.horizontalHeader()
        
        # Stretching text columns (Name, Path)
        header.setSectionResizeMode(0, QHeaderView.Stretch) # Name
        header.setSectionResizeMode(2, QHeaderView.Stretch) # Path
        
        # Fixed-width columns (Code, Status, Actions)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        self.table.setColumnWidth(1, 80)  # Narrow width for the code (e.g. TTN)
        
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        self.table.setColumnWidth(3, 100) # Fixed width for status
        
        # Actions column (most important)
        # Three buttons: 70+60+50 plus gaps ~= 220px
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        self.table.setColumnWidth(4, 240) 
        
        # Row height
        self.table.verticalHeader().setDefaultSectionSize(50)
        self.table.verticalHeader().setVisible(True) # Row numbers clutter the table; hide like user management
        
        self.table.setStyleSheet(style.PROJECTS_TABLE)
        
        layout.addWidget(self.table)
        self.load_projects()

    def load_projects(self):
        """
        Handle Load Projects operation.
        """
        self.table.setRowCount(0)
        projects = self.session.db.get_all_projects()
        
        for row_idx, proj in enumerate(projects):
            self.table.insertRow(row_idx)
            
            # 1. Name
            self.table.setItem(row_idx, 0, QTableWidgetItem(proj.name))
            
            # 2. Code (center aligned)
            code_item = QTableWidgetItem(proj.code)
            code_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 1, code_item)
            
            # 3. Path
            self.table.setItem(row_idx, 2, QTableWidgetItem(proj.root_path))
            
            # 4. Status (center aligned)
            status = getattr(proj, 'status', 'Active') 
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 3, status_item)

            # 5. Actions Buttons
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            
            # Zero margins so buttons sit centered without extra space
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(5) 
            actions_layout.setAlignment(Qt.AlignCenter) # Center all buttons in the cell
            
            # Members
            btn_members = QPushButton("Members")
            btn_members.setFixedSize(70, 28) # Slightly taller
            btn_members.setCursor(Qt.PointingHandCursor)
            btn_members.setStyleSheet(style.BTN_ACTION_MEMBERS)
            btn_members.clicked.connect(lambda _, p=proj: self.open_members_dialog(p))
            
            # Edit
            btn_edit = QPushButton("Edit")
            btn_edit.setFixedSize(60, 28)
            btn_edit.setCursor(Qt.PointingHandCursor)
            btn_edit.setStyleSheet(style.BTN_ACTION_EDIT)
            btn_edit.clicked.connect(lambda _, p=proj: self.open_edit_dialog(p))
            
            # Delete
            btn_del = QPushButton("Del")
            btn_del.setFixedSize(50, 28)
            btn_del.setCursor(Qt.PointingHandCursor)
            btn_del.setStyleSheet(style.BTN_ACTION_DEL)
            btn_del.clicked.connect(lambda _, p=proj: self.delete_project(p))
            
            actions_layout.addWidget(btn_members)
            actions_layout.addWidget(btn_edit)
            actions_layout.addWidget(btn_del)
            
            self.table.setCellWidget(row_idx, 4, actions_widget)

    # ... (open_add_dialog, open_edit_dialog, delete_project, open_members_dialog unchanged) ...
    def open_add_dialog(self):
        """
        Handle Open Add Dialog operation.
        """
        dialog = ProjectDialog(self.session, parent=self)
        if dialog.exec():
            self.load_projects()

    def open_edit_dialog(self, project):
        """
        Handle Open Edit Dialog operation.
        """
        dialog = ProjectDialog(self.session, project_to_edit=project, parent=self)
        if dialog.exec():
            self.load_projects()

    def delete_project(self, project):
        """
        Handle Delete Project operation.
        """
        confirm = QMessageBox.question(self, "Confirm Delete", 
                                       f"Are you sure you want to delete '{project.name}'?\nThis cannot be undone!",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            if self.session.db.delete_project(project.id):
                self.load_projects()

    def open_members_dialog(self, project):
        """
        Handle Open Members Dialog operation.
        """
        dialog = ProjectMembersDialog(self.session, project, parent=self)
        dialog.exec()