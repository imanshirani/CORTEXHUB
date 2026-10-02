from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QTextEdit, 
                               QPushButton, QHBoxLayout, QFrame)
from PySide6.QtCore import Qt
from app.ui import style

class TaskDetailsDialog(QDialog):
    def __init__(self, task_data, parent=None):
        """
        Handle   Init   operation.
        """
        super().__init__(parent)
        self.setWindowTitle("Task Details")
        self.resize(400, 450)
        self.setStyleSheet(style.DIALOG_STYLESHEET)
        
        
        
        # --- Important fix: correct mapping of database indexes ---
        # The data structure that comes from get_task_by_id:
        # 0: id, 1: status, 2: dept_name, 3: username, 4: color, 
        # 5: title, 6: description, 7: entity_id, 8: dept_id, 9: assignee_id
        
        try:
            self.task_id = task_data[0]
            self.status = task_data[1]
            self.dept_name = task_data[2]
            self.user_name = task_data[3]
            self.dept_color = task_data[4]
            self.title = task_data[5]
            self.description = task_data[6]
        except IndexError:
            # If for any reason the data was less (to be compatible with old codes)
            self.title = "Error loading data"
            self.description = str(task_data)
            self.status = "Unknown"
            self.dept_name = "-"
            self.user_name = "-"
            self.dept_color = None

        self.init_ui()

    def init_ui(self):
        """
        Handle Init Ui operation.
        """
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 1. Header (Dept Color + Title)
        header_layout = QHBoxLayout()
        
        # Department color
        if self.dept_color:
            color_box = QLabel()
            color_box.setFixedSize(16, 16)
            color_box.setStyleSheet(f"background-color: {self.dept_color}; border-radius: 8px;")
            header_layout.addWidget(color_box)

        # Task title
        lbl_title = QLabel(self.title)
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        header_layout.addWidget(lbl_title)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)

        # 2. Status & User info
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel(f"Assignee: <b>{self.user_name}</b>"))
        info_layout.addStretch()
        
        # Status Badge
        lbl_status = QLabel(f" {self.status} ")
        status_color = style.STATUS_COLORS.get(self.status, "#555")
        lbl_status.setStyleSheet(f"background-color: {status_color}; border-radius: 4px; color: white; padding: 2px 6px;")
        info_layout.addWidget(lbl_status)
        
        layout.addLayout(info_layout)
        
        # dividing line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #444;")
        layout.addWidget(line)

        # 3. Description Area
        layout.addWidget(QLabel("Description:"))
        self.txt_desc = QTextEdit()
        self.txt_desc.setReadOnly(True)
        self.txt_desc.setPlainText(self.description if self.description else "No description provided.")
        layout.addWidget(self.txt_desc)

        # 4. Close Button
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)