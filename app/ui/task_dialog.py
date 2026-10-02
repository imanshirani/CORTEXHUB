# Location: app/ui/task_dialog.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, QTextEdit, 
                               QComboBox, QPushButton, QHBoxLayout, QMessageBox,
                               QDateEdit, QDoubleSpinBox, QGridLayout, QGroupBox)
from PySide6.QtCore import QDate
from app.ui import style

class TaskDialog(QDialog):
    """
    A dialog interface for creating or editing pipeline tasks.
    Supports setting deadlines, estimated hours, and assignments.
    """
    def __init__(self, session, project_id, task_to_edit=None, parent=None):
        """
        Handle   Init   operation.
        """
        super().__init__(parent)
        self.session = session
        self.project_id = project_id
        self.task_to_edit = task_to_edit 
        
        self.setWindowTitle("Create New Task")
        if task_to_edit:
            self.setWindowTitle("Edit Task")
            
        self.resize(450, 600)
        self.setStyleSheet(style.DIALOG_STYLESHEET)
        
        self.init_ui()
        
        if task_to_edit:
            self.populate_fields()

    def init_ui(self):
        """
        Handle Init Ui operation.
        """
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # 1. Title
        layout.addWidget(QLabel("Task Title:"))
        self.title_input = QLineEdit()
        self.title_input.setStyleSheet(style.INPUT_STYLE)
        self.title_input.setPlaceholderText("e.g. Modeling_Character_Base")
        layout.addWidget(self.title_input)

        # 2. Assignment Group
        assign_group = QGroupBox("Assignment")
        assign_layout = QHBoxLayout(assign_group)
        
        self.dept_combo = QComboBox()
        self.dept_combo.setStyleSheet(style.COMBOBOX_STYLE)
        self.load_departments()
        
        self.user_combo = QComboBox()
        self.user_combo.setStyleSheet(style.COMBOBOX_STYLE)
        self.load_users()
        
        assign_layout.addWidget(QLabel("Dept:"))        
        assign_layout.addWidget(self.dept_combo)        
        assign_layout.addWidget(QLabel("User:"))
        assign_layout.addWidget(self.user_combo)
        
        #self.setstyleSheet(style.COMBOBOX_STYLE)
        layout.addWidget(assign_group)

        # 3. Schedule Group (NEW)
        schedule_group = QGroupBox("Schedule & Deadline")
        schedule_layout = QGridLayout(schedule_group)
        
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate()) # today's date
        self.start_date.setStyleSheet(style.INPUT_STYLE)
        
        self.due_date = QDateEdit()
        self.due_date.setCalendarPopup(True)
        self.due_date.setDate(QDate.currentDate().addDays(3)) # Default 3 days later
        self.due_date.setStyleSheet(style.INPUT_STYLE)
        
        self.est_hours = QDoubleSpinBox()
        self.est_hours.setRange(0.5, 500.0)
        self.est_hours.setValue(8.0)
        self.est_hours.setSuffix(" hrs")
        self.est_hours.setStyleSheet(style.INPUT_STYLE)

        schedule_layout.addWidget(QLabel("Start Date:"), 0, 0)
        schedule_layout.addWidget(self.start_date, 0, 1)
        schedule_layout.addWidget(QLabel("Due Date (Deadline):"), 1, 0)
        schedule_layout.addWidget(self.due_date, 1, 1)
        schedule_layout.addWidget(QLabel("Estimated Time:"), 2, 0)
        schedule_layout.addWidget(self.est_hours, 2, 1)
        
        layout.addWidget(schedule_group)

        # 4. Description
        layout.addWidget(QLabel("Description:"))
        self.desc_input = QTextEdit()
        self.desc_input.setStyleSheet(style.INPUT_STYLE)
        self.desc_input.setPlaceholderText("Task details...")
        layout.addWidget(self.desc_input)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Save Task" if self.task_to_edit else "Create Task")
        btn_save.setStyleSheet(style.BTN_SUCCESS)
        btn_save.clicked.connect(self.accept)
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setStyleSheet(style.BTN_SECONDARY)
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def load_departments(self):
        """
        Handle Load Departments operation.
        """
        depts = self.session.db.get_all_departments()
        for d in depts:
            self.dept_combo.addItem(d[1], userData=d[0])

    def load_users(self):
        """
        Handle Load Users operation.
        """
        users = self.session.db.get_project_users(self.project_id)
        self.user_combo.addItem("Unassigned", userData=None)
        for u in users:
            self.user_combo.addItem(u[1], userData=u[0])

    def populate_fields(self):
        """
        Handle Populate Fields operation.
        """
        try:
            self.title_input.setText(self.task_to_edit[5])
            self.desc_input.setPlainText(self.task_to_edit[6])
            
            idx = self.dept_combo.findData(self.task_to_edit[8])
            if idx >= 0: self.dept_combo.setCurrentIndex(idx)
            
            idx = self.user_combo.findData(self.task_to_edit[9])
            if idx >= 0: self.user_combo.setCurrentIndex(idx)
            
            # Loading the dates (indexes 10, 11, 12 that we created in the database)
            if len(self.task_to_edit) > 10 and self.task_to_edit[10]:
                self.start_date.setDate(QDate.fromString(self.task_to_edit[10], "yyyy-MM-dd"))
            if len(self.task_to_edit) > 11 and self.task_to_edit[11]:
                self.due_date.setDate(QDate.fromString(self.task_to_edit[11], "yyyy-MM-dd"))
            if len(self.task_to_edit) > 12 and self.task_to_edit[12] is not None:
                self.est_hours.setValue(float(self.task_to_edit[12]))
                
        except Exception as e:
            print(f"Error populating fields: {e}")

    def get_data(self):
        """
        Collects and formats all input data from the dialog fields.
        
        Returns:
            dict: Containing title, dept_id, assignee_id, description, 
                  start_date, due_date, and estimated_hours.
        """
        return {
            "title": self.title_input.text(),
            "dept_id": self.dept_combo.currentData(),
            "assignee_id": self.user_combo.currentData(),
            "description": self.desc_input.toPlainText(),
            "start_date": self.start_date.date().toString("yyyy-MM-dd"),
            "due_date": self.due_date.date().toString("yyyy-MM-dd"),
            "estimated_hours": self.est_hours.value()
        }