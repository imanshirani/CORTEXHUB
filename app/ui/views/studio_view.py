from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                               QTableWidgetItem, QPushButton, QHeaderView, QMessageBox, QLabel)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor , QPixmap
from app.ui import style
from app.ui.dept_dialog import DeptDialog

class StudioView(QWidget):
    def __init__(self, session):
        """
        Handle   Init   operation.
        """
        super().__init__()
        self.session = session
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Studio Departments")
        title.setStyleSheet(style.SECTION_TITLE)
        
        self.btn_add = QPushButton("+ Add Dept")
        self.btn_add.setFixedSize(120, 35)
        self.btn_add.setCursor(Qt.PointingHandCursor)
        self.btn_add.setStyleSheet(style.BTN_NEW_PROJECT)
        self.btn_add.clicked.connect(self.open_add_dialog)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_add)
        layout.addLayout(header_layout)

        # --- Table Initialization (FIXED for 5 Columns) ---
        self.table = QTableWidget()
        self.table.setColumnCount(5) # Column count matches load_depts
        self.table.setHorizontalHeaderLabels(["Department Name", "Software", "Engine", "Color Preview", "Actions"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        header = self.table.horizontalHeader()
        
        # How columns resize
        header.setSectionResizeMode(0, QHeaderView.Stretch)           # Department name stretches
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Software icons
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Engine icon
        
        header.setSectionResizeMode(3, QHeaderView.Fixed)            # Color preview
        self.table.setColumnWidth(3, 150)
        
        header.setSectionResizeMode(4, QHeaderView.Fixed)            # Action buttons
        self.table.setColumnWidth(4, 180)
        
        self.table.verticalHeader().setDefaultSectionSize(50)
        self.table.verticalHeader().setVisible(True)
        self.table.setStyleSheet(style.PROJECTS_TABLE) #
        
        layout.addWidget(self.table)
        self.load_depts()

    def create_color_widget(self, text, color_code):
        """Helper that builds a widget with a color square and a label"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 0, 10, 0) # Left/right margin
        layout.setSpacing(10)
        
        # 1. Color square
        color_box = QLabel()
        color_box.setFixedSize(20, 20)
        # If the database has no color (None), default to gray
        safe_color = color_code if color_code else "#555"
        color_box.setStyleSheet(f"background-color: {safe_color}; border: 1px solid #777; border-radius: 4px;")
        
        # 2. Text (color code)
        label = QLabel(text if text else "N/A")
        label.setStyleSheet("color: #ccc; background: transparent; font-family: monospace;")
        
        layout.addWidget(color_box)
        layout.addWidget(label)
        layout.addStretch()
        
        return widget

    def load_depts(self):
        """
        Handle Load Depts operation.
        """
        self.table.setRowCount(0)
        # Add extra header columns if needed (set column count to 5 in __init__)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Department Name", "Software", "Engine", "Color", "Actions"])
        
        rows = self.session.db.get_all_departments()
        
        for row_idx, row in enumerate(rows):
            # Five values: id, name, color, sw, engine
            dept_id, name, color, sw, engine = row 
            
            # Build the full object (do not overwrite it incorrectly)
            dept_obj = {
                "id": dept_id, 
                "name": name, 
                "color": color, 
                "allowed_software": sw, 
                "render_engine": engine
            }
            
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(name))

            # --- Software Icons column (same as dashboard) ---
            sw_widget = QWidget()
            sw_layout = QHBoxLayout(sw_widget)
            sw_layout.setContentsMargins(5, 0, 5, 0)
            
            # --- Main change: read a dynamic list from the database ---
            all_softwares = self.session.db.get_software_list()
            
            for s in all_softwares:
                s_clean = s.lower().strip() # Normalize name so spaces/case do not break matching
                # Check department permission
                if sw.lower() == "all" or s_clean in sw.lower():
                    icon_path = style.get_sw_icon(s_clean)
                    if icon_path:
                        lbl = QLabel()
                        # Use QPixmap for the icon
                        lbl.setPixmap(QPixmap(icon_path).scaled(18, 18, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                        lbl.setToolTip(s.strip().capitalize()) # Show the name on hover
                        sw_layout.addWidget(lbl)
                        
            sw_layout.addStretch()
            self.table.setCellWidget(row_idx, 1, sw_widget)

            # --- Engine Icon column ---
            eng_widget = QWidget()
            eng_layout = QHBoxLayout(eng_widget)
            eng_layout.setContentsMargins(5, 0, 5, 0)
            if engine and engine != "--------":
                e_icon = style.get_engine_icon(engine) #
                if e_icon:
                    e_lbl = QLabel()
                    e_lbl.setPixmap(QPixmap(e_icon).scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    eng_layout.addWidget(e_lbl)
            eng_layout.addStretch()
            self.table.setCellWidget(row_idx, 2, eng_widget)

            # Color and action columns (indexes 3 and 4)
            self.table.setCellWidget(row_idx, 3, self.create_color_widget(color, color))

            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            
            btn_edit = QPushButton("Edit")
            btn_edit.setStyleSheet(style.BTN_SM_EDIT)
            # The full dept_obj is now passed to the dialog
            btn_edit.clicked.connect(lambda _, d=dept_obj: self.open_edit_dialog(d))
            
            btn_del = QPushButton("Del")
            btn_del.setStyleSheet(style.BTN_SM_DELETE)
            btn_del.clicked.connect(lambda _, d_id=dept_id: self.delete_dept(d_id))
            
            actions_layout.addWidget(btn_edit)
            actions_layout.addWidget(btn_del)
            self.table.setCellWidget(row_idx, 4, actions_widget)

    def open_add_dialog(self):
        """
        Handle Open Add Dialog operation.
        """
        dialog = DeptDialog(self.session, parent=self)
        if dialog.exec():
            self.load_depts()

    def open_edit_dialog(self, dept_obj):
        """
        Handle Open Edit Dialog operation.
        """
        dialog = DeptDialog(self.session, dept_to_edit=dept_obj, parent=self)
        if dialog.exec():
            self.load_depts()

    def delete_dept(self, dept_id):
        """
        Handle Delete Dept operation.
        """
        confirm = QMessageBox.question(self, "Delete", "Delete this department?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.session.db.delete_department(dept_id)
            self.load_depts()