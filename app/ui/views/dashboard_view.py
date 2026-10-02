import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QLabel, QPushButton, 
                               QMenu, QMessageBox, QCheckBox) # Added QCheckBox
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor, QAction , QPixmap, QIcon
from app.ui import style
from app.core.launcher import LauncherFactory

class DashboardView(QWidget):

    go_to_task_signal = Signal(str, str, str)
    
    def __init__(self, session):
        """
        Handle   Init   operation.
        """
        super().__init__()
        
        self.session = session
        self.user = session.context.user
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # --- Header ---
        header_layout = QHBoxLayout()
        welcome_lbl = QLabel(f"Welcome back, {self.user.full_name}!")
        welcome_lbl.setStyleSheet("font-size: 24px; font-weight: bold; color: #007acc;")
        header_layout.addWidget(welcome_lbl)
        header_layout.addStretch()
        
        self.chk_show_done = QCheckBox("Show Completed Tasks")
        self.chk_show_done.setStyleSheet("color: #aaa;")
        self.chk_show_done.toggled.connect(self.load_my_tasks)
        header_layout.addWidget(self.chk_show_done)
        
        btn_refresh = QPushButton("↻ Refresh")
        btn_refresh.setFixedSize(90, 30)
        btn_refresh.setStyleSheet(style.BTN_SECONDARY)
        btn_refresh.clicked.connect(self.load_my_tasks)
        header_layout.addWidget(btn_refresh)
        layout.addLayout(header_layout)

        # --- Table Initialization (FIXED COLUMNS) ---
        self.table = QTableWidget()
        self.table.setColumnCount(7) 
        self.table.setHorizontalHeaderLabels(["Project", "Software", "Engine", "Task / Dept", "Title", "Status", "Action"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        h_header = self.table.horizontalHeader()
        h_header.setSectionResizeMode(0, QHeaderView.Stretch)          # Project
        h_header.setSectionResizeMode(1, QHeaderView.ResizeToContents) # Software
        #self.table.setColumnWidth(1, 120)
        h_header.setSectionResizeMode(2, QHeaderView.ResizeToContents) # Engine
        #self.table.setColumnWidth(2, 80)
        h_header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # Task / Dept
        h_header.setSectionResizeMode(4, QHeaderView.Stretch)          # Title
        h_header.setSectionResizeMode(5, QHeaderView.Fixed)            # Status
        self.table.setColumnWidth(5, 120)
        h_header.setSectionResizeMode(6, QHeaderView.Fixed)            # Action
        self.table.setColumnWidth(6, 120)
        
        self.table.verticalHeader().setDefaultSectionSize(50)
        self.table.setStyleSheet(style.PROJECTS_TABLE)
        layout.addWidget(self.table)
        
        self.load_my_tasks()

    def load_my_tasks(self):
        """
        Handle Load My Tasks operation.
        """
        self.table.setRowCount(0)
        tasks = self.session.db.get_user_tasks(self.user.id, self.chk_show_done.isChecked())
        
        for idx, task in enumerate(tasks):
            t_id, status, dept_name, project_name, title, desc, entity_id = task
            self.table.insertRow(idx)
            
            # Obtaining locks from the database
            task_info = self.session.db.get_task_by_id(t_id)
            allowed_sw, render_engine = "all", None
            if task_info:
                dept_id = task_info[8]
                self.session.db.cursor.execute("SELECT allowed_software, render_engine FROM departments WHERE id=?", (dept_id,))
                res = self.session.db.cursor.fetchone()
                if res:
                    allowed_sw = res[0].lower() if res[0] else "all"
                    render_engine = res[1] if res[1] and res[1] != "--------" else None

            # 0. Project
            self.table.setItem(idx, 0, QTableWidgetItem(project_name))

            # 1. Software Icons
            sw_wdg = QWidget(); sw_lay = QHBoxLayout(sw_wdg)
            sw_lay.setContentsMargins(5, 0, 5, 0); sw_lay.setSpacing(4)
            
            # --- Correction: getting the complete list from the database instead of the fixed list ---
            all_softwares = self.session.db.get_software_list()
            
            for sw_name in all_softwares:
                sw_name_clean = sw_name.lower().strip()
                # Checking whether this department is allowed to use this software
                if allowed_sw == "all" or sw_name_clean in allowed_sw:
                    icon = style.get_sw_icon(sw_name_clean)
                    if icon:
                        lbl = QLabel()
                        lbl.setPixmap(QPixmap(icon).scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                        lbl.setToolTip(sw_name.strip().capitalize())
                        sw_lay.addWidget(lbl)
                        
            sw_lay.addStretch(); self.table.setCellWidget(idx, 1, sw_wdg)

            # 2. Engine Icon
            eng_wdg = QWidget(); eng_lay = QHBoxLayout(eng_wdg)
            eng_lay.setContentsMargins(5, 0, 5, 0); eng_lay.setSpacing(4)
            if render_engine:
                e_icon = style.get_engine_icon(render_engine)
                if e_icon:
                    lbl = QLabel(); lbl.setPixmap(QPixmap(e_icon).scaled(18, 18, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    lbl.setToolTip(render_engine); eng_lay.addWidget(lbl)
            eng_lay.addStretch(); self.table.setCellWidget(idx, 2, eng_wdg)

            # 3. Task / Dept
            self.table.setItem(idx, 3, QTableWidgetItem(dept_name))
            
            # 4. Title
            t_item = QTableWidgetItem(title); t_item.setToolTip(desc)
            self.table.setItem(idx, 4, t_item)
            
            # 5. Status
            s_color = style.STATUS_COLORS.get(status, "#444")
            s_wdg = QWidget(); s_lay = QHBoxLayout(s_wdg)
            s_lay.setContentsMargins(10, 0, 5, 0)
            s_box = QLabel(); s_box.setFixedSize(14, 14); s_box.setStyleSheet(f"background-color: {s_color}; border-radius: 3px;")
            s_lay.addWidget(s_box); s_lay.addWidget(QLabel(status)); s_lay.addStretch()
            self.table.setCellWidget(idx, 5, s_wdg)
            
            # 6. Action (Launch + Go) - last column
            btn_launch = QPushButton("🚀 Launch")
            btn_launch.setStyleSheet(style.LUNCH_BTN)
            btn_launch.clicked.connect(lambda _, tid=t_id: self.show_launch_menu(tid))
            
            # --- NEW: Jump to task button ---
            btn_goto = QPushButton("🎯 Go")
            btn_goto.setStyleSheet(style.BTN_SM_INFO) 
            btn_goto.setToolTip("Go to this task in Production/Assets")
            
            # Find the type (Shot or Asset) to send the signal
            e_type = "Shot" if task_info and task_info[7] else "Unknown" # default
            if task_info:
                # We check if this entity_id is in the shots or assets table (with the help of get_task_context_data)
                ctx = self.session.db.get_task_context_data(t_id)
                if ctx: e_type = ctx.get("type", "Shot")

            btn_goto.clicked.connect(lambda _, tid=t_id, eid=entity_id, etype=e_type: self.go_to_task_signal.emit(tid, etype, eid))
            # ---------------------------

            btn_container = QWidget()
            btn_lay = QHBoxLayout(btn_container)
            btn_lay.setContentsMargins(5, 5, 5, 5)
            btn_lay.addWidget(btn_goto)    # Added Go button
            btn_lay.addWidget(btn_launch)
            self.table.setCellWidget(idx, 6, btn_container)

    def _create_icon_container(self):
        """
        Handle  Create Icon Container operation.
        """
        wdg = QWidget()
        lay = QHBoxLayout(wdg)
        lay.setContentsMargins(5, 0, 5, 0)
        lay.setSpacing(5)
        return wdg, lay

    def _create_icon_label(self, path, tip, size=20):
        """
        Handle  Create Icon Label operation.
        """
        lbl = QLabel()
        pix = QPixmap(path).scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        lbl.setPixmap(pix)
        lbl.setToolTip(tip)
        return lbl
    
    # ... (functions show_launch_menu, run_launcher and ... remain unchanged) ...
    def show_launch_menu(self, task_id):
        """
        Show right-click menu to run software with smart icons
        """
        task_info = self.session.db.get_task_by_id(task_id)
        if not task_info: return
        
        dept_id = task_info[8]
        self.session.db.cursor.execute("SELECT allowed_software FROM departments WHERE id=?", (dept_id,))
        res = self.session.db.cursor.fetchone()
        allowed_sw = res[0].lower() if res else "all"

        menu = QMenu(self)
        # Fixing the error: using MENU_STYLE that we defined in the style
        menu.setStyleSheet(style.MENU_STYLE) 

        # The complete list of software from the database
        all_softwares = self.session.db.get_software_list()

        for sw in all_softwares:
            sw_name_clean = sw.lower().strip()
            
            # Check departmental access permission
            if allowed_sw == "all" or sw_name_clean in allowed_sw:
                # Getting the smart icon from the style file
                icon_path = style.get_sw_icon(sw_name_clean)
                
                action = QAction(sw, self)
                
                # If there is an icon, add it to the menu
                if icon_path and os.path.exists(icon_path):
                    action.setIcon(QIcon(icon_path))
                
                action.triggered.connect(lambda _, s=sw_name_clean: self.run_launcher(task_id, s))
                menu.addAction(action)

        menu.addSeparator()
        action_explore = QAction("Open Folder in Explorer", self)
        action_explore.triggered.connect(lambda: self.open_in_explorer(task_id))
        menu.addAction(action_explore)
        
        menu.exec(QCursor.pos())

    def run_launcher(self, task_id, software):
        """
        Handle Run Launcher operation.
        """
        context_data = self.session.db.get_task_context_data(task_id)
        if not context_data:
            QMessageBox.critical(self, "Error", "Could not resolve context.")
            return

        class MockProject:
            def __init__(self, data):
                """
                Handle   Init   operation.
                """
                self.id = data["project_id"]
                self.name = data["project_name"]
                self.root_path = data["project_root"]

        class MockTask:
            def __init__(self, data):
                """
                Handle   Init   operation.
                """
                self.id = data["task_id"]
                self.title = data["task_title"]
                self.type = data["type"]
                self.frame_start = data["frame_start"]
                self.frame_end = data["frame_end"]
                self.entity_name = data["entity_name"]
                self.parent_name = data["parent_name"]

        project = MockProject(context_data)
        task_obj = MockTask(context_data)
        
        launcher = LauncherFactory.get_launcher(self.session, software)
        if not launcher:
            QMessageBox.warning(self, "Error", f"Launcher for {software} not found.")
            return

        launcher.set_context(project, task_obj, self.user)
        success, msg = launcher.launch()
        if success:
            self.session.db.update_task_status(task_id, "In Progress")
            self.load_my_tasks()
        else:
            QMessageBox.critical(self, "Launch Error", msg)

    def open_in_explorer(self, task_id):
        """
        Handle Open In Explorer operation.
        """
        context_data = self.session.db.get_task_context_data(task_id)
        if context_data:
            os.startfile(context_data["project_root"])