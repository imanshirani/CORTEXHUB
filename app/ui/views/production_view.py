from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
                               QLabel, QPushButton, QInputDialog, QMessageBox, QLineEdit,
                               QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QFrame, QMenu)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QAction, QCursor, QIcon, QPixmap
from app.ui.task_dialog import TaskDialog
from app.ui import style
from app.ui.task_details_dialog import TaskDetailsDialog
from app.core.filesystem import FileSystemManager
from app.ui.shot_dialog import ShotDialog
from app.ui.sequence_dialog import SequenceDialog
import os

class ProductionView(QWidget):
    def __init__(self, session):
        """
        Handle   Init   operation.
        """
        super().__init__()
        self.session = session
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(20)
        
        # 1. Sequence list (new style)
        self.seq_list = QListWidget()
        self.seq_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.seq_list.customContextMenuRequested.connect(self.open_seq_menu)
        self.seq_list.itemClicked.connect(self.load_shots)
        self.seq_list.setStyleSheet(style.LIST_WIDGET_STYLE) # <---
        
        # 2. Shot list (new style)
        self.shot_list = QListWidget()
        self.shot_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.shot_list.customContextMenuRequested.connect(self.open_shot_menu)
        self.shot_list.itemClicked.connect(self.load_tasks)
        self.shot_list.setStyleSheet(style.LIST_WIDGET_STYLE) # <---
        
        # 3. Task table (new style)
        self.task_table = QTableWidget()
        self.task_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.task_table.customContextMenuRequested.connect(self.open_task_menu)
        self.task_table.setColumnCount(3)
        self.task_table.setHorizontalHeaderLabels(["Dept", "User", "Status"])
        self.task_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        header = self.task_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents) # Dept
        header.setSectionResizeMode(1, QHeaderView.Stretch)          # User
        header.setSectionResizeMode(2, QHeaderView.Fixed)            # Status
        self.task_table.setColumnWidth(2, 120)
        
        self.task_table.verticalHeader().setDefaultSectionSize(50) # <--- We increased the height of the lines to fit the photo
        self.task_table.verticalHeader().setVisible(False)
        self.task_table.setStyleSheet(style.PROJECTS_TABLE)
        
        # --- Binding task click to preview panel ---
        self.task_table.itemSelectionChanged.connect(self.update_preview_panel)
        
        # 4. Project selector
        self.setup_project_selector()

        # 5. Creating a preview panel (fourth column)
        self.preview_panel = QFrame()
        self.preview_panel.setStyleSheet("background-color: #2b2b2b; border-radius: 8px; padding: 10px;")
        self.preview_layout = QVBoxLayout(self.preview_panel)
        self.preview_layout.setAlignment(Qt.AlignTop)
        
        self.lbl_preview_thumb = QLabel("🖼️ No Task Selected")
        self.lbl_preview_thumb.setFixedSize(240, 135) # Size 16:9
        self.lbl_preview_thumb.setStyleSheet("background-color: #111; border: 1px solid #444; border-radius: 4px; font-size: 14px; color: #777;")
        self.lbl_preview_thumb.setAlignment(Qt.AlignCenter)
        
        self.lbl_preview_title = QLabel("---")
        self.lbl_preview_title.setStyleSheet("font-size: 16px; font-weight: bold; color: white; margin-top: 10px;")
        
        self.lbl_preview_timeline = QLabel("Start: --- \nDue: --- \nHours: ---")
        self.lbl_preview_timeline.setStyleSheet("font-size: 13px; color: #aaa; margin-top: 10px; line-height: 1.5;")
        
        self.lbl_preview_desc = QLabel("Description:\n---")
        self.lbl_preview_desc.setStyleSheet("font-size: 13px; color: #ccc; margin-top: 15px;")
        self.lbl_preview_desc.setWordWrap(True)
        
        self.preview_layout.addWidget(self.lbl_preview_thumb)
        self.preview_layout.addWidget(self.lbl_preview_title)
        self.preview_layout.addWidget(self.lbl_preview_timeline)
        self.preview_layout.addWidget(self.lbl_preview_desc)
        self.preview_layout.addStretch()

        # 6. Arrange widgets in 4 columns
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(20)
        
        columns_layout.addLayout(self.create_column("Sequences", self.seq_list, self.add_sequence))
        columns_layout.addLayout(self.create_column("Shots", self.shot_list, self.add_shot))
        columns_layout.addLayout(self.create_column("Tasks", self.task_table, self.add_task))
        
        # The fourth column
        preview_col_layout = QVBoxLayout()
        preview_header = QLabel("Preview & Timeline")
        preview_header.setStyleSheet("font-weight: bold; color: #aaa; font-size: 14px; margin-bottom: 10px;")
        preview_col_layout.addWidget(preview_header)
        preview_col_layout.addWidget(self.preview_panel)
        
        columns_layout.addLayout(preview_col_layout)
        self.layout.addLayout(columns_layout)

    def setup_project_selector(self):
        """
        Handle Setup Project Selector operation.
        """
        top_layout = QHBoxLayout()
        
        lbl = QLabel("Select Project:")
        lbl.setStyleSheet(style.SECTION_TITLE) # Use standard titles
        
        self.project_combo = QComboBox()
        self.project_combo.setMinimumWidth(250)
        self.project_combo.setFixedHeight(35)
        # Combobox style can also be moved to style.py
        self.project_combo.setStyleSheet(style.COMBOBOX_STYLE)
        self.project_combo.currentIndexChanged.connect(self.on_project_changed)
        
        top_layout.addWidget(lbl)
        top_layout.addWidget(self.project_combo)
        top_layout.addStretch()
        
        self.layout.addLayout(top_layout)
        self.refresh_project_list()

    def refresh_project_list(self):
        """
        Handle Refresh Project List operation.
        """
        self.project_combo.clear()
        projects = self.session.db.get_all_projects()
        for proj in projects:
            self.project_combo.addItem(proj.name, userData=proj.id)
        if projects:
            self.on_project_changed(0)

    def on_project_changed(self, index):
        """
        Handle On Project Changed operation.
        """
        if index == -1: return
        proj_id = self.project_combo.itemData(index)
        self.session.set_active_project(proj_id)
        self.load_sequences()

    def create_column(self, title, widget, add_callback):
        """
        Handle Create Column operation.
        """
        col_layout = QVBoxLayout()
        col_layout.setSpacing(10)
        
        header = QHBoxLayout()
        lbl = QLabel(title)
        lbl.setStyleSheet("font-weight: bold; color: #aaa; font-size: 14px;")
        
        btn = QPushButton("+")
        btn.setFixedSize(30, 30)
        btn.setCursor(Qt.PointingHandCursor)
        # Use the green but smaller button style
        btn.setStyleSheet(style.BTN_ADD_SMALL)
        btn.clicked.connect(add_callback)
        
        header.addWidget(lbl)
        header.addStretch()
        header.addWidget(btn)
        
        col_layout.addLayout(header)
        col_layout.addWidget(widget)
        return col_layout

    # ... (the rest of the logic functions load_sequences, load_shots and ... should be copied without change) ...
    # Just check the load_tasks function so that the color style is not damaged (because we left it transparent, it should work)
    
    # --- Sequences Logic ---
    def load_sequences(self):
        """
        Handle Load Sequences operation.
        """
        self.seq_list.clear()
        self.shot_list.clear()
        self.task_table.setRowCount(0)
        
        project = self.session.context.project
        if not project: return

        seqs = self.session.db.get_sequences(project.id)
        for row in seqs:
            if len(row) >= 3:
                seq_id = row[0]
                name = row[2]
                display_name = str(name) if name else "Unnamed Sequence"
                item = QListWidgetItem(display_name)
                item.setData(Qt.UserRole, seq_id)
                self.seq_list.addItem(item)

    def add_sequence(self):
        """
        Handle Add Sequence operation.
        """
        project = self.session.context.project
        if not project:
            QMessageBox.warning(self, "Error", "No active project selected!")
            return

        dialog = SequenceDialog(self.session, parent=self)
        if dialog.exec() == QInputDialog.Accepted:
            name = dialog.get_data()
            if name:
                if self.session.db.create_sequence(project.id, name):
                    project_full_path = os.path.join(project.root_path, project.name)
                    
                    # Fixed: send only two arguments (path and sequence name)
                    FileSystemManager.create_sequence_structure(project_full_path, name)
                    
                    self.load_sequences()

    # --- Shots Logic ---
    def load_shots(self, item):
        """
        Handle Load Shots operation.
        """
        self.shot_list.clear()
        self.task_table.setRowCount(0)
        seq_id = item.data(Qt.UserRole)
        shots = self.session.db.get_shots(seq_id)
        for shot in shots:
            shot_id, _, name, start, end, status = shot
            display_text = f"{name} ({start}-{end})"
            list_item = QListWidgetItem(display_text)
            list_item.setData(Qt.UserRole, shot_id)
            self.shot_list.addItem(list_item)


    

    # ----------------------------------------
    # SHOT ADD LOGIC (NEW)
    # ----------------------------------------
    def add_shot(self):
        """
        Handle Add Shot operation.
        """
        current_seq = self.seq_list.currentItem()
        if not current_seq:
            QMessageBox.warning(self, "Error", "Select a Sequence first!")
            return
            
        project = self.session.context.project
        seq_name = current_seq.text()
        seq_id = current_seq.data(Qt.UserRole)
        
        # Using the new dialog (ShotDialog)
        dialog = ShotDialog(self.session, parent=self)
        
        # Find buttons in ShotDialog
        for btn in dialog.findChildren(QPushButton):
            text = btn.text().replace("&", "")
            if text in ["OK", "Ok", "Save"]:
                btn.setText("Save Shot")
                btn.setStyleSheet(style.BTN_ADD_SMALL)
            elif text == "Cancel":
                btn.hide() # Remove the cancel button

        
        if dialog.exec():
            data = dialog.get_data()
            name = data["name"]
            
            # 1. Construction in the database
            if self.session.db.create_shot(seq_id, name, data["start"], data["end"]):
                
                project_full_path = os.path.join(project.root_path, project.name)
                
                # Passing db as the first argument
                FileSystemManager.create_shot_structure(self.session.db, project_full_path, seq_name, name)
                
                self.load_shots(current_seq)

    

    def edit_shot(self, item):
        """Edit shot (name + frames) + handle folder renaming"""
        shot_id = item.data(Qt.UserRole)
        project = self.session.context.project
        current_seq = self.seq_list.currentItem()
        
        # 1. Getting the current information from the database
        shot_data = self.session.db.get_shot_by_id(shot_id)
        if not shot_data: 
            QMessageBox.warning(self, "Error", "Could not fetch shot data.")
            return
        
        old_name = shot_data[2] # The old name of the shot
        
        # 2. Opening a dialog with previous information
        dialog = ShotDialog(self.session, shot_to_edit=shot_data, parent=self)
        if dialog.exec():
            data = dialog.get_data()
            new_name = data["name"]
            
            # 3. If the name has changed, rename the folder
            if new_name != old_name:
                project_path = os.path.join(project.root_path, project.name)
                seq_path = os.path.join(project_path, "Sequences", current_seq.text())
                old_shot_path = os.path.join(seq_path, old_name)
                
                if not FileSystemManager.rename_folder(old_shot_path, new_name):
                    QMessageBox.critical(self, "Error", 
                        f"Could not rename folder '{old_name}' on disk!\nMake sure no files are open.")
                    return # The operation stops
            
            # 4. Database update (name + frames)
            if self.session.db.update_shot(shot_id, new_name, data["start"], data["end"]):
                self.load_shots(current_seq)
            else:
                QMessageBox.critical(self, "Error", "Database update failed.")


    # --- Tasks Logic ---
    def add_task(self):
        """
        Handle Add Task operation.
        """
        current_shot = self.shot_list.currentItem()
        if not current_shot: return
        
        project = self.session.context.project
        dialog = TaskDialog(self.session, project.id, parent=self)
        if dialog.exec():
            data = dialog.get_data()
            shot_id = current_shot.data(Qt.UserRole)
            
            # Sending new date data to the database
            success = self.session.db.create_task(
                entity_id=shot_id,
                dept_id=data["dept_id"],
                assignee_id=data["assignee_id"],
                title=data["title"],
                description=data["description"],
                start_date=data["start_date"],       # <---
                due_date=data["due_date"],           # <---
                estimated_hours=data["estimated_hours"] # <---
            )
            if success: self.load_tasks(current_shot)

    def create_color_widget(self, text, color_code):
        """
        Handle Create Color Widget operation.
        """
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 0, 5, 0)
        layout.setSpacing(8)
        
        # colored square
        color_box = QLabel()
        color_box.setFixedSize(14, 14) # A little smaller for tasks
        safe_color = color_code if color_code else "transparent"
        border = "1px solid #666" if color_code else "none"
        color_box.setStyleSheet(f"background-color: {safe_color}; border: {border}; border-radius: 3px;")
        
        # text
        label = QLabel(text)
        label.setStyleSheet("color: #ddd; background: transparent;")
        
        layout.addWidget(color_box)
        layout.addWidget(label)
        layout.addStretch()
        return widget

    def load_tasks(self, item):
        """
        Handle Load Tasks operation.
        """
        self.task_table.setRowCount(0)
        shot_id = item.data(Qt.UserRole)
        tasks = self.session.db.get_tasks(shot_id)
        
        for idx, task in enumerate(tasks):
            t_id = task[0]
            status = task[1]
            dept_name = task[2]
            user_name = task[3]
            color = task[4]
            title = task[5]
            
            self.task_table.insertRow(idx)
            
            # Column 0: Dept
            wdg_dept = self.create_color_widget(dept_name, color)
            wdg_dept.setToolTip(f"<b>{title}</b>")
            self.task_table.setCellWidget(idx, 0, wdg_dept)
            
            # Column 1: User (we store the ID here)
            user_item = QTableWidgetItem(str(user_name))
            user_item.setData(Qt.UserRole, t_id)
            self.task_table.setItem(idx, 1, user_item)
            
            # Column 2: Status
            status_color = style.STATUS_COLORS.get(status, "#444")
            s_wdg = self.create_color_widget(status, status_color)
            self.task_table.setCellWidget(idx, 2, s_wdg)

        self.task_table.clearSelection()
        self.update_preview_panel()

    # (Right click menu functions should all be in their place)
    def open_seq_menu(self, position):
        """
        Handle Open Seq Menu operation.
        """
        item = self.seq_list.itemAt(position)
        if not item: return
        menu = QMenu()
        menu.setStyleSheet(style.MENU_STYLE)
        rename_action = menu.addAction("Rename Sequence")
        delete_action = menu.addAction("Delete Sequence")
        action = menu.exec(QCursor.pos())
        if action == rename_action: self.rename_sequence(item)
        elif action == delete_action: self.delete_sequence(item)

    # ----------------------------------------
    # SEQUENCE RENAME LOGIC
    # ----------------------------------------
    def rename_sequence(self, item):
        """
        Handle Rename Sequence operation.
        """
        seq_id = item.data(Qt.UserRole)
        project = self.session.context.project
        
        # 1. Getting information from the database (now there is a method)
        seq_data = self.session.db.get_sequence_by_id(seq_id)
        if not seq_data: return

        # 2. Open a new dialog
        dialog = SequenceDialog(self.session, seq_to_edit=seq_data, parent=self)
        if dialog.exec():
            new_name = dialog.get_data()
            old_name = seq_data[2]
            
            if new_name and new_name != old_name:
                # 3. Rename the folder on the hard drive
                project_path = os.path.join(project.root_path, project.name)
                seq_root = os.path.join(project_path, "Sequences")
                old_path = os.path.join(seq_root, old_name)
                
                if FileSystemManager.rename_folder(old_path, new_name):
                    # 4. Database update
                    if self.session.db.update_sequence(seq_id, new_name):
                        item.setText(new_name)
                        self.load_sequences() # Refresh to be sure
                

    def delete_sequence(self, item):
        """
        Handle Delete Sequence operation.
        """
        confirm = QMessageBox.question(self, "Confirm", f"Delete sequence '{item.text()}'?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            seq_id = item.data(Qt.UserRole)
            if self.session.db.delete_sequence(seq_id): self.load_sequences()

    # ----------------------------------------------------------------
    # SHOT MENU & EDIT LOGIC (FIXED)
    # ----------------------------------------------------------------
    def open_shot_menu(self, position):
        """
        Handle Open Shot Menu operation.
        """
        item = self.shot_list.itemAt(position)
        if not item: return
        
        shot_id = item.data(Qt.UserRole)
        shot_name = item.text()

        menu = QMenu()
        menu.setStyleSheet(style.MENU_STYLE)
        
        # 1. Add shot builder option
        builder_action = menu.addAction("🎬 Build Shot Composition")
        menu.addSeparator()
        
        # 2. Edit and delete options (your own codes)
        edit_action = menu.addAction("Edit / Rename Shot")
        delete_action = menu.addAction("Delete Shot")
        
        action = menu.exec(QCursor.pos())
        
        # Manage clicks
        if action == builder_action:
            # Calling the shot builder method
            from app.ui.shot_builder import ShotBuilder
            dialog = ShotBuilder(self.session, shot_id, shot_name, parent=self)
            dialog.exec()
        elif action == edit_action:
            self.edit_shot(item) # Your own subject
        elif action == delete_action:
            self.delete_shot(item)

    def edit_shot(self, item):
        """Edit shot (name + frames) + handle folder renaming"""
        shot_id = item.data(Qt.UserRole)
        project = self.session.context.project
        current_seq = self.seq_list.currentItem()
        
        # 1. Getting the current information from the database
        # (You must have the function get_shot_by_id in database.py)
        shot_data = self.session.db.get_shot_by_id(shot_id)
        if not shot_data: 
            QMessageBox.warning(self, "Error", "Could not fetch shot data.")
            return
        
        old_name = shot_data[2] # The old name of the shot
        
        # 2. Opening a dialog with previous information
        dialog = ShotDialog(self.session, shot_to_edit=shot_data, parent=self)
        if dialog.exec():
            data = dialog.get_data()
            new_name = data["name"]
            
            # 3. If the name has changed, rename the folder
            if new_name != old_name:
                project_path = os.path.join(project.root_path, project.name)
                seq_path = os.path.join(project_path, "Sequences", current_seq.text())
                old_shot_path = os.path.join(seq_path, old_name)
                
                if not FileSystemManager.rename_folder(old_shot_path, new_name):
                    QMessageBox.critical(self, "Error", 
                        f"Could not rename folder '{old_name}' on disk!\nMake sure no files are open.")
                    return # The operation stops
            
            # 4. Database update (name + frames)
            if self.session.db.update_shot(shot_id, new_name, data["start"], data["end"]):
                self.load_shots(current_seq)
            else:
                QMessageBox.critical(self, "Error", "Database update failed.")

    def delete_shot(self, item):
        """
        Handle Delete Shot operation.
        """
        confirm = QMessageBox.question(self, "Confirm", "Delete this shot?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            shot_id = item.data(Qt.UserRole)
            if self.session.db.delete_shot(shot_id): self.load_shots(self.seq_list.currentItem())
            

    def open_task_menu(self, position):
        """
        Handle Open Task Menu operation.
        """
        row = self.task_table.currentRow()
        if row == -1: return
        
        # Read ID from column 1
        item = self.task_table.item(row, 1)
        if not item: return
        task_id = item.data(Qt.UserRole)

        menu = QMenu()
        menu.setStyleSheet(style.MENU_STYLE)
        view_action = menu.addAction("View Details")
        
        # Add Edit option
        edit_action = menu.addAction("Edit Task") 
        
        menu.addSeparator()
        
        status_menu = menu.addMenu("Set Status")
        status_menu.addAction("Todo", lambda: self.set_task_status(task_id, "Todo"))
        status_menu.addAction("In Progress", lambda: self.set_task_status(task_id, "In Progress"))
        status_menu.addAction("Review", lambda: self.set_task_status(task_id, "Review"))
        status_menu.addAction("Done", lambda: self.set_task_status(task_id, "Done"))
        
        menu.addSeparator()
        del_action = menu.addAction("Delete Task")
        
        action = menu.exec(QCursor.pos())
        
        if action == view_action:
            self.view_task_details(task_id)
        elif action == edit_action:    # Edit handling
            self.edit_task(task_id)
        elif action == del_action:
            self.delete_task(task_id)

    # --- New function to perform editing operations ---
    def edit_task(self, task_id):
        """
        Handle Edit Task operation.
        """
        task_data = self.session.db.get_task_by_id(task_id)
        if not task_data: return

        project = self.session.context.project
        dialog = TaskDialog(self.session, project.id, task_to_edit=task_data, parent=self)
        
        if dialog.exec():
            data = dialog.get_data()
            success = self.session.db.update_task_details(
                task_id, 
                data["title"], 
                data["description"], 
                data["assignee_id"], 
                data["dept_id"],
                start_date=data["start_date"],       # <---
                due_date=data["due_date"],           # <---
                estimated_hours=data["estimated_hours"] # <---
            )
            if success: self.load_tasks(self.shot_list.currentItem())

    # --- New function to open dialog ---
    def view_task_details(self, task_id):
        """
        Handle View Task Details operation.
        """
        # 1. Getting new information from the database
        task_data = self.session.db.get_task_by_id(task_id)
        
        if task_data:
            # 2. Display dialog
            dialog = TaskDetailsDialog(task_data, parent=self)
            dialog.exec()
        else:
            QMessageBox.warning(self, "Error", "Could not fetch task details.")

    def set_task_status(self, task_id, status):
        """
        Handle Set Task Status operation.
        """
        self.session.db.update_task_status(task_id, status)
        self.load_tasks(self.shot_list.currentItem())

    def delete_task(self, task_id):
        """
        Handle Delete Task operation.
        """
        confirm = QMessageBox.question(self, "Delete", "Delete this task?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.session.db.delete_task(task_id)
            self.load_tasks(self.shot_list.currentItem())

    def create_preview_widget(self, title, start_date, due_date):
        """Create a widget for the first column: photo + title + date"""
        wdg = QWidget()
        layout = QHBoxLayout(wdg)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        
        # Photo section (placeholder - in the future, we will read the actual published photo from the database)
        lbl_thumb = QLabel()
        lbl_thumb.setFixedSize(80, 50)
        lbl_thumb.setStyleSheet("background-color: #222; border-radius: 4px; border: 1px solid #444;")
        lbl_thumb.setText("🖼️") # Temporary icon
        lbl_thumb.setAlignment(Qt.AlignCenter)
        
        # Text and timeline section
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        lbl_title = QLabel(f"<b>{title}</b>")
        lbl_title.setStyleSheet("color: white; font-size: 13px;")
        
        # Beautiful timeline
        sd = start_date if start_date else "----/--/--"
        dd = due_date if due_date else "----/--/--"
        lbl_time = QLabel(f"⏱️ {sd}  ➔  {dd}")
        lbl_time.setStyleSheet("color: #aaa; font-size: 11px;")
        
        text_layout.addWidget(lbl_title)
        text_layout.addWidget(lbl_time)
        text_layout.addStretch()
        
        layout.addWidget(lbl_thumb)
        layout.addLayout(text_layout)
        layout.addStretch()
        return wdg

    def load_tasks(self, item):
        """
        Handle Load Tasks operation.
        """
        self.task_table.setRowCount(0)
        shot_id = item.data(Qt.UserRole)
        tasks = self.session.db.get_tasks(shot_id)
        
        for idx, task in enumerate(tasks):
            t_id = task[0]
            status = task[1]
            dept_name = task[2]
            user_name = task[3]
            color = task[4]
            title = task[5]
            
            self.task_table.insertRow(idx)
            
            # Column 0: Dept
            wdg_dept = self.create_color_widget(dept_name, color)
            wdg_dept.setToolTip(f"<b>{title}</b>")
            self.task_table.setCellWidget(idx, 0, wdg_dept)
            
            # Column 1: User (we save the ID here so that right click works)
            user_item = QTableWidgetItem(str(user_name))
            user_item.setData(Qt.UserRole, t_id)
            self.task_table.setItem(idx, 1, user_item)
            
            # Column 2: Status
            status_color = style.STATUS_COLORS.get(status, "#444")
            s_wdg = self.create_color_widget(status, status_color)
            self.task_table.setCellWidget(idx, 2, s_wdg)

        self.task_table.clearSelection()
        # This line causes the right panel to update when the list is loaded
        self.update_preview_panel()


    def update_preview_panel(self):
        """Loading selected task information along with photo and date from database"""
        row = self.task_table.currentRow()
        if row == -1:
            self.lbl_preview_thumb.clear()
            self.lbl_preview_thumb.setText("🖼️ No Task Selected")
            self.lbl_preview_title.setText("---")
            self.lbl_preview_timeline.setText("Start: --- \nDue: --- \nHours: ---")
            self.lbl_preview_desc.setText("Description:\n---")
            return
            
        item = self.task_table.item(row, 1)
        if not item: return
        task_id = item.data(Qt.UserRole)
        
        # 1. Getting the main information of the task from the database
        task = self.session.db.get_task_by_id(task_id)
        if not task: return
        
        title = task[5]
        desc = task[6] if task[6] else "No description."
        start_date = task[10] if len(task)>10 and task[10] else "Not Set"
        due_date = task[11] if len(task)>11 and task[11] else "Not Set"
        hours = task[12] if len(task)>12 and task[12] else "0"
        
        self.lbl_preview_title.setText(f"{title}")
        self.lbl_preview_desc.setText(f"<b>Description:</b><br>{desc}")
        
        # 2. Taking the last photo and publication date from the publish table
        try:
            query = """
                SELECT thumbnail_path, created_at, version 
                FROM publishes 
                WHERE task_id=? 
                ORDER BY version DESC LIMIT 1
            """
            self.session.db.cursor.execute(query, (task_id,))
            latest_pub = self.session.db.cursor.fetchone()
        except Exception as e:
            print(f"Error fetching publish data: {e}")
            latest_pub = None

        publish_info = ""

        # 3. Checking if there is a photo or not
        if latest_pub:
            thumb_path = latest_pub[0]
            pub_date = latest_pub[1]
            version = latest_pub[2]
            
            publish_info = f"<br><br>✨ Last Publish: <b>v{version:03d}</b><br>🕒 {pub_date}"

            if thumb_path and os.path.exists(thumb_path):
                pixmap = QPixmap(thumb_path)
                pixmap = pixmap.scaled(240, 135, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                self.lbl_preview_thumb.setPixmap(pixmap)
            else:
                self.lbl_preview_thumb.clear()
                self.lbl_preview_thumb.setText("🖼️ Image Missing")
        else:
            self.lbl_preview_thumb.clear()
            self.lbl_preview_thumb.setText("🖼️ No Publish Yet")
            publish_info = "<br><br>✨ Last Publish: <b>None</b>"

        # 4. Timeline text update
        self.lbl_preview_timeline.setText(f"📅 Start: <b>{start_date}</b><br>🚨 Due: <b>{due_date}</b><br>⏱️ Est. Time: <b>{hours} hrs</b>{publish_info}")


    def select_task_row(self, task_id):
        """Find the task line, scroll to it and update the image"""
        for row in range(self.task_table.rowCount()):
            item = self.task_table.item(row, 1) 
            # Convert to string to ensure exact match
            if item and str(item.data(Qt.UserRole)) == str(task_id):
                self.task_table.selectRow(row)
                self.task_table.scrollToItem(item) # ---> Auto scroll to task
                self.update_preview_panel()        # ---> Definitive execution of the preview
                break

    def jump_to_task(self, ctx):
        """Automatic search and selection of project, sequence, shot and task"""
        # 1. Setting up the project
        idx = self.project_combo.findData(ctx["project_id"])
        if idx >= 0:
            if self.project_combo.currentIndex() != idx:
                self.project_combo.setCurrentIndex(idx)
            else:
                # If the project is the same, make sure the lists are not empty
                if self.seq_list.count() == 0:
                    self.load_sequences()

        # 2. Find the sequence
        for i in range(self.seq_list.count()):
            item = self.seq_list.item(i)
            if item.text() == ctx["parent_name"]: 
                self.seq_list.setCurrentItem(item)
                self.load_shots(item) 
                break
        
        # 3. Find the shot
        for i in range(self.shot_list.count()):
            item = self.shot_list.item(i)
            if str(item.data(Qt.UserRole)) == str(ctx["entity_id"]):
                self.shot_list.setCurrentItem(item)
                self.load_tasks(item) 
                break
        
        # 4. Scrolling and choosing the exact task
        self.select_task_row(ctx["task_id"])