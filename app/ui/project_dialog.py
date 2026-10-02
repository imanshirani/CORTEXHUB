import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                               QPushButton, QHBoxLayout, QFileDialog, QComboBox, QMessageBox)
from PySide6.QtCore import Qt
from app.ui import style

# 1. ایمپورت کردن فایل سیستم (این خط حیاتی است)
from app.core.filesystem import FileSystemManager 

class ProjectDialog(QDialog):
    def __init__(self, session, project_to_edit=None, parent=None):
        """
        Handle   Init   operation.
        """
        super().__init__(parent)
        self.session = session
        self.project_to_edit = project_to_edit
        
        title = "Edit Project" if project_to_edit else "Create New Project"
        self.setWindowTitle(title)
        self.resize(400, 350)
        self.setStyleSheet(style.DIALOG_STYLESHEET) # یا استایل مورد نظر خودتان
        
        self.layout = QVBoxLayout(self)
        self.setup_ui()
        
        if self.project_to_edit:
            self.load_data()

    def setup_ui(self):
        """
        Handle Setup Ui operation.
        """
        # 1. Project Name
        self.layout.addWidget(QLabel("Project Name:"))
        self.name_input = QLineEdit()
        self.name_input.setStyleSheet(style.INPUT_STYLE)
        self.layout.addWidget(self.name_input)

        # 2. Project Code
        self.layout.addWidget(QLabel("Code (3 chars):"))
        self.code_input = QLineEdit()
        self.code_input.setStyleSheet(style.INPUT_STYLE)
        self.code_input.setMaxLength(3)
        self.layout.addWidget(self.code_input)

        # 3. Status
        self.layout.addWidget(QLabel("Status:"))
        self.status_combo = QComboBox()
        self.status_combo.setStyleSheet(style.COMBOBOX_STYLE)
        self.status_combo.addItems(["Active", "Archived", "On Hold"])
        self.layout.addWidget(self.status_combo)

        # 4. Root Path
        self.layout.addWidget(QLabel("Root Directory:"))
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setStyleSheet(style.INPUT_STYLE)
        self.btn_browse = QPushButton("...")
        self.btn_browse.setFixedWidth(40)
        self.btn_browse.setStyleSheet(style.BTN_BROWSE)
        self.btn_browse.clicked.connect(self.browse_folder)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.btn_browse)
        self.layout.addLayout(path_layout)

        # --- New: Assembly Software ---
        self.layout.addWidget(QLabel("Assembly/Stage Software:"))
        self.software_combo = QComboBox()
        self.software_combo.setStyleSheet(style.COMBOBOX_STYLE)
        self.software_combo.addItems(["3ds Max", "Maya", "Unreal Engine", "Blender", "Houdini"])
        self.layout.addWidget(self.software_combo)

        # --- New: Render Engine ---
        self.layout.addWidget(QLabel("Render Engine:"))
        self.render_combo = QComboBox()
        self.render_combo.setStyleSheet(style.COMBOBOX_STYLE)
        self.render_combo.addItems(["Octane", "V-Ray", "Corona", "Arnold", "Redshift", "Cycles"])
        self.layout.addWidget(self.render_combo)

        self.layout.addStretch()

        # 5. Buttons
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("Save Project")
        self.btn_save.setStyleSheet(style.BTN_SUCCESS)
        # self.btn_save.setObjectName("LoginButton") # اگر استایل خاصی دارید
        self.btn_save.clicked.connect(self.save_project)
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setStyleSheet(style.BTN_SECONDARY)
        self.btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        self.layout.addLayout(btn_layout)

    def browse_folder(self):
        """
        Handle Browse Folder operation.
        """
        folder = QFileDialog.getExistingDirectory(self, "Select Project Root")
        if folder:
            self.path_input.setText(folder)

    def load_data(self):
        """
        Handle Load Data operation.
        """
        p = self.project_to_edit
        self.name_input.setText(p.name)
        self.code_input.setText(p.code)
        self.path_input.setText(p.root_path)
        if hasattr(p, 'status'):
            self.status_combo.setCurrentText(p.status)
        if hasattr(p, 'software'):
            self.software_combo.setCurrentText(p.software)
        if hasattr(p, 'render_engine'):
            self.render_combo.setCurrentText(p.render_engine)

    def save_project(self):
        """
        Handle Save Project operation.
        """
        # 2. حتما از strip استفاده کنید تا فاصله اضافی باعث ارور نشود
        name = self.name_input.text().strip()
        code = self.code_input.text().upper().strip()
        path = self.path_input.text().strip()
        status = self.status_combo.currentText()
        software = self.software_combo.currentText()
        render_engine = self.render_combo.currentText()

        if not name or not code or not path:
            QMessageBox.warning(self, "Missing Data", "Please fill all fields.")
            return

        if self.project_to_edit:
            success = self.session.db.update_project(
                self.project_to_edit.id, name, code, path, status, render_engine, software)
        else:
            # Create New Project
            success = self.session.db.create_project(name, code, path, render_engine, software)
            
            # --- بخش مهم: ساخت فولدرها ---
            if success:
                # ساخت مسیر کامل: Root + Project Name
                full_project_path = os.path.join(path, name)
                
                # صدا زدن تابع ساخت فولدر
                FileSystemManager.create_project_structure(self.session.db, full_project_path)
            # -----------------------------

        if success:
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Operation failed.")