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
        
        # 1. لیست سکانس (استایل جدید)
        self.seq_list = QListWidget()
        self.seq_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.seq_list.customContextMenuRequested.connect(self.open_seq_menu)
        self.seq_list.itemClicked.connect(self.load_shots)
        self.seq_list.setStyleSheet(style.LIST_WIDGET_STYLE) # <---
        
        # 2. لیست شات (استایل جدید)
        self.shot_list = QListWidget()
        self.shot_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.shot_list.customContextMenuRequested.connect(self.open_shot_menu)
        self.shot_list.itemClicked.connect(self.load_tasks)
        self.shot_list.setStyleSheet(style.LIST_WIDGET_STYLE) # <---
        
        # 3. جدول تسک (استایل جدید)
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
        
        self.task_table.verticalHeader().setDefaultSectionSize(50) # <--- ارتفاع سطرها را بیشتر کردیم تا عکس جا شود
        self.task_table.verticalHeader().setVisible(False)
        self.task_table.setStyleSheet(style.PROJECTS_TABLE)
        
        # --- اتصال کلیک روی تسک به پنل پیش‌نمایش ---
        self.task_table.itemSelectionChanged.connect(self.update_preview_panel)
        
        # 4. سلکتور پروژه
        self.setup_project_selector()

        # 5. ساخت پنل پیش‌نمایش (ستون چهارم)
        self.preview_panel = QFrame()
        self.preview_panel.setStyleSheet("background-color: #2b2b2b; border-radius: 8px; padding: 10px;")
        self.preview_layout = QVBoxLayout(self.preview_panel)
        self.preview_layout.setAlignment(Qt.AlignTop)
        
        self.lbl_preview_thumb = QLabel("🖼️ No Task Selected")
        self.lbl_preview_thumb.setFixedSize(240, 135) # سایز 16:9
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

        # 6. چیدن ویجت‌ها در 4 ستون
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(20)
        
        columns_layout.addLayout(self.create_column("Sequences", self.seq_list, self.add_sequence))
        columns_layout.addLayout(self.create_column("Shots", self.shot_list, self.add_shot))
        columns_layout.addLayout(self.create_column("Tasks", self.task_table, self.add_task))
        
        # ستون چهارم
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
        lbl.setStyleSheet(style.SECTION_TITLE) # استفاده از تایتل استاندارد
        
        self.project_combo = QComboBox()
        self.project_combo.setMinimumWidth(250)
        self.project_combo.setFixedHeight(35)
        # استایل کمبو باکس را هم می‌شود به style.py برد
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
        # استفاده از استایل دکمه سبز اما کوچکتر
        btn.setStyleSheet(style.BTN_ADD_SMALL)
        btn.clicked.connect(add_callback)
        
        header.addWidget(lbl)
        header.addStretch()
        header.addWidget(btn)
        
        col_layout.addLayout(header)
        col_layout.addWidget(widget)
        return col_layout

    # ... (بقیه توابع لاجیک load_sequences, load_shots و ... بدون تغییر کپی شوند) ...
    # فقط تابع load_tasks را چک کن که استایل رنگش خراب نشود (چون transparent گذاشتیم باید کار کند)
    
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
                    
                    # اصلاح شده: فقط دو آرگومان بفرست (مسیر و نام سکانس)
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
        
        # استفاده از دیالوگ جدید (ShotDialog)
        dialog = ShotDialog(self.session, parent=self)
        
        # پیدا کردن دکمه‌ها در ShotDialog
        for btn in dialog.findChildren(QPushButton):
            text = btn.text().replace("&", "")
            if text in ["OK", "Ok", "Save"]:
                btn.setText("Save Shot")
                btn.setStyleSheet(style.BTN_ADD_SMALL)
            elif text == "Cancel":
                btn.hide() # حذف دکمه کنسل

        
        if dialog.exec():
            data = dialog.get_data()
            name = data["name"]
            
            # 1. ساخت در دیتابیس
            if self.session.db.create_shot(seq_id, name, data["start"], data["end"]):
                
                project_full_path = os.path.join(project.root_path, project.name)
                
                # پاس دادن db به عنوان آرگومان اول
                FileSystemManager.create_shot_structure(self.session.db, project_full_path, seq_name, name)
                
                self.load_shots(current_seq)

    

    def edit_shot(self, item):
        """ویرایش شات (نام + فریم‌ها) + هندل کردن تغییر نام فولدر"""
        shot_id = item.data(Qt.UserRole)
        project = self.session.context.project
        current_seq = self.seq_list.currentItem()
        
        # 1. گرفتن اطلاعات فعلی از دیتابیس
        shot_data = self.session.db.get_shot_by_id(shot_id)
        if not shot_data: 
            QMessageBox.warning(self, "Error", "Could not fetch shot data.")
            return
        
        old_name = shot_data[2] # نام قدیمی شات
        
        # 2. باز کردن دیالوگ با اطلاعات قبلی
        dialog = ShotDialog(self.session, shot_to_edit=shot_data, parent=self)
        if dialog.exec():
            data = dialog.get_data()
            new_name = data["name"]
            
            # 3. اگر نام تغییر کرده، فولدر را رینیم کن
            if new_name != old_name:
                project_path = os.path.join(project.root_path, project.name)
                seq_path = os.path.join(project_path, "Sequences", current_seq.text())
                old_shot_path = os.path.join(seq_path, old_name)
                
                if not FileSystemManager.rename_folder(old_shot_path, new_name):
                    QMessageBox.critical(self, "Error", 
                        f"Could not rename folder '{old_name}' on disk!\nMake sure no files are open.")
                    return # عملیات متوقف می‌شود
            
            # 4. آپدیت دیتابیس (نام + فریم‌ها)
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
            
            # ارسال دیتای جدید تاریخ به دیتابیس
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
        
        # مربع رنگی
        color_box = QLabel()
        color_box.setFixedSize(14, 14) # کمی کوچکتر برای تسک‌ها
        safe_color = color_code if color_code else "transparent"
        border = "1px solid #666" if color_code else "none"
        color_box.setStyleSheet(f"background-color: {safe_color}; border: {border}; border-radius: 3px;")
        
        # متن
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
            
            # ستون 0: Dept
            wdg_dept = self.create_color_widget(dept_name, color)
            wdg_dept.setToolTip(f"<b>{title}</b>")
            self.task_table.setCellWidget(idx, 0, wdg_dept)
            
            # ستون 1: User (آیدی را اینجا ذخیره می‌کنیم)
            user_item = QTableWidgetItem(str(user_name))
            user_item.setData(Qt.UserRole, t_id)
            self.task_table.setItem(idx, 1, user_item)
            
            # ستون 2: Status
            status_color = style.STATUS_COLORS.get(status, "#444")
            s_wdg = self.create_color_widget(status, status_color)
            self.task_table.setCellWidget(idx, 2, s_wdg)

        self.task_table.clearSelection()
        self.update_preview_panel()

    # (توابع منوی کلیک راست همگی سرجای خودشان باشند)
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
        
        # 1. گرفتن اطلاعات از دیتابیس (حالا متد وجود دارد)
        seq_data = self.session.db.get_sequence_by_id(seq_id)
        if not seq_data: return

        # 2. باز کردن دیالوگ جدید
        dialog = SequenceDialog(self.session, seq_to_edit=seq_data, parent=self)
        if dialog.exec():
            new_name = dialog.get_data()
            old_name = seq_data[2]
            
            if new_name and new_name != old_name:
                # 3. تغییر نام فولدر روی هارد
                project_path = os.path.join(project.root_path, project.name)
                seq_root = os.path.join(project_path, "Sequences")
                old_path = os.path.join(seq_root, old_name)
                
                if FileSystemManager.rename_folder(old_path, new_name):
                    # 4. آپدیت دیتابیس
                    if self.session.db.update_sequence(seq_id, new_name):
                        item.setText(new_name)
                        self.load_sequences() # رفرش برای اطمینان
                

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
        
        # ۱. اضافه کردن گزینه شات بیلدر
        builder_action = menu.addAction("🎬 Build Shot Composition")
        menu.addSeparator()
        
        # ۲. گزینه‌های ادیت و حذف (کدهای خودت)
        edit_action = menu.addAction("Edit / Rename Shot")
        delete_action = menu.addAction("Delete Shot")
        
        action = menu.exec(QCursor.pos())
        
        # مدیریت کلیک‌ها
        if action == builder_action:
            # فراخوانی متد شات بیلدر
            from app.ui.shot_builder import ShotBuilder
            dialog = ShotBuilder(self.session, shot_id, shot_name, parent=self)
            dialog.exec()
        elif action == edit_action:
            self.edit_shot(item) # تابع خودت
        elif action == delete_action:
            self.delete_shot(item)

    def edit_shot(self, item):
        """ویرایش شات (نام + فریم‌ها) + هندل کردن تغییر نام فولدر"""
        shot_id = item.data(Qt.UserRole)
        project = self.session.context.project
        current_seq = self.seq_list.currentItem()
        
        # 1. گرفتن اطلاعات فعلی از دیتابیس
        # (باید تابع get_shot_by_id را در database.py داشته باشید)
        shot_data = self.session.db.get_shot_by_id(shot_id)
        if not shot_data: 
            QMessageBox.warning(self, "Error", "Could not fetch shot data.")
            return
        
        old_name = shot_data[2] # نام قدیمی شات
        
        # 2. باز کردن دیالوگ با اطلاعات قبلی
        dialog = ShotDialog(self.session, shot_to_edit=shot_data, parent=self)
        if dialog.exec():
            data = dialog.get_data()
            new_name = data["name"]
            
            # 3. اگر نام تغییر کرده، فولدر را رینیم کن
            if new_name != old_name:
                project_path = os.path.join(project.root_path, project.name)
                seq_path = os.path.join(project_path, "Sequences", current_seq.text())
                old_shot_path = os.path.join(seq_path, old_name)
                
                if not FileSystemManager.rename_folder(old_shot_path, new_name):
                    QMessageBox.critical(self, "Error", 
                        f"Could not rename folder '{old_name}' on disk!\nMake sure no files are open.")
                    return # عملیات متوقف می‌شود
            
            # 4. آپدیت دیتابیس (نام + فریم‌ها)
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
        
        # خواندن ID از ستون 1
        item = self.task_table.item(row, 1)
        if not item: return
        task_id = item.data(Qt.UserRole)

        menu = QMenu()
        menu.setStyleSheet(style.MENU_STYLE)
        view_action = menu.addAction("View Details")
        
        # اضافه کردن گزینه Edit
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
        elif action == edit_action:    # هندل کردن ادیت
            self.edit_task(task_id)
        elif action == del_action:
            self.delete_task(task_id)

    # --- تابع جدید برای انجام عملیات ادیت ---
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

    # --- تابع جدید برای باز کردن دیالوگ ---
    def view_task_details(self, task_id):
        """
        Handle View Task Details operation.
        """
        # 1. گرفتن اطلاعات تازه از دیتابیس
        task_data = self.session.db.get_task_by_id(task_id)
        
        if task_data:
            # 2. نمایش دیالوگ
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
        """ساخت ویجت برای ستون اول: عکس + تایتل + تاریخ"""
        wdg = QWidget()
        layout = QHBoxLayout(wdg)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        
        # بخش عکس (پلیسهولدر - در آینده عکس واقعی پابلیش را از دیتابیس می‌خوانیم)
        lbl_thumb = QLabel()
        lbl_thumb.setFixedSize(80, 50)
        lbl_thumb.setStyleSheet("background-color: #222; border-radius: 4px; border: 1px solid #444;")
        lbl_thumb.setText("🖼️") # آیکون موقت
        lbl_thumb.setAlignment(Qt.AlignCenter)
        
        # بخش متن و تایم‌لاین
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        lbl_title = QLabel(f"<b>{title}</b>")
        lbl_title.setStyleSheet("color: white; font-size: 13px;")
        
        # تایم‌لاین زیبا
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
            
            # ستون 0: Dept
            wdg_dept = self.create_color_widget(dept_name, color)
            wdg_dept.setToolTip(f"<b>{title}</b>")
            self.task_table.setCellWidget(idx, 0, wdg_dept)
            
            # ستون 1: User (آیدی را اینجا ذخیره می‌کنیم تا کلیک‌راست کار کند)
            user_item = QTableWidgetItem(str(user_name))
            user_item.setData(Qt.UserRole, t_id)
            self.task_table.setItem(idx, 1, user_item)
            
            # ستون 2: Status
            status_color = style.STATUS_COLORS.get(status, "#444")
            s_wdg = self.create_color_widget(status, status_color)
            self.task_table.setCellWidget(idx, 2, s_wdg)

        self.task_table.clearSelection()
        # این خط باعث می‌شود وقتی لیست لود شد، پنل سمت راست آپدیت شود
        self.update_preview_panel()


    def update_preview_panel(self):
        """لود کردن اطلاعات تسک انتخاب شده به همراه عکس و تاریخ از دیتابیس"""
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
        
        # 1. گرفتن اطلاعات اصلی تسک از دیتابیس
        task = self.session.db.get_task_by_id(task_id)
        if not task: return
        
        title = task[5]
        desc = task[6] if task[6] else "No description."
        start_date = task[10] if len(task)>10 and task[10] else "Not Set"
        due_date = task[11] if len(task)>11 and task[11] else "Not Set"
        hours = task[12] if len(task)>12 and task[12] else "0"
        
        self.lbl_preview_title.setText(f"{title}")
        self.lbl_preview_desc.setText(f"<b>Description:</b><br>{desc}")
        
        # 2. گرفتن آخرین عکس و تاریخ پابلیش از جدول publishes
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

        # 3. چک کردن اینکه آیا عکسی وجود دارد یا نه
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

        # 4. آپدیت متن تایم‌لاین
        self.lbl_preview_timeline.setText(f"📅 Start: <b>{start_date}</b><br>🚨 Due: <b>{due_date}</b><br>⏱️ Est. Time: <b>{hours} hrs</b>{publish_info}")


    def select_task_row(self, task_id):
        """پیدا کردن سطر تسک، اسکرول به آن و آپدیت تصویر"""
        for row in range(self.task_table.rowCount()):
            item = self.task_table.item(row, 1) 
            # تبدیل به string برای اطمینان از تطابق دقیق
            if item and str(item.data(Qt.UserRole)) == str(task_id):
                self.task_table.selectRow(row)
                self.task_table.scrollToItem(item) # ---> اسکرول خودکار به سمت تسک
                self.update_preview_panel()        # ---> اجرای قطعی پیش‌نمایش
                break

    def jump_to_task(self, ctx):
        """پیدا کردن و انتخاب اتوماتیک پروژه، سکانس، شات و تسک"""
        # 1. تنظیم پروژه
        idx = self.project_combo.findData(ctx["project_id"])
        if idx >= 0:
            if self.project_combo.currentIndex() != idx:
                self.project_combo.setCurrentIndex(idx)
            else:
                # اگر پروژه همان بود، مطمئن شویم لیست‌ها خالی نیستند
                if self.seq_list.count() == 0:
                    self.load_sequences()

        # 2. پیدا کردن سکانس
        for i in range(self.seq_list.count()):
            item = self.seq_list.item(i)
            if item.text() == ctx["parent_name"]: 
                self.seq_list.setCurrentItem(item)
                self.load_shots(item) 
                break
        
        # 3. پیدا کردن شات
        for i in range(self.shot_list.count()):
            item = self.shot_list.item(i)
            if str(item.data(Qt.UserRole)) == str(ctx["entity_id"]):
                self.shot_list.setCurrentItem(item)
                self.load_tasks(item) 
                break
        
        # 4. اسکرول و انتخاب دقیق تسک
        self.select_task_row(ctx["task_id"])