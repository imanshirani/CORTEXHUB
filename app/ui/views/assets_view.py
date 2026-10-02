from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
                               QLabel, QPushButton, QMessageBox, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QComboBox, QMenu,QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor, QIcon, QPixmap

from app.ui import style
from app.ui.asset_dialog import AssetDialog
from app.ui.task_dialog import TaskDialog
from app.ui.task_details_dialog import TaskDetailsDialog
from app.core.filesystem import FileSystemManager
import os

class AssetsView(QWidget):
    def __init__(self, session):
        """
        Handle   Init   operation.
        """
        super().__init__()
        self.session = session
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(20)
        
        # --- FIX: ابتدا تعریف ویجت‌ها (قبل از فراخوانی توابع دیگر) ---
        
        # 1. تعریف لیست کتگوری
        self.cat_list = QListWidget()
        self.cat_list.setStyleSheet(style.LIST_WIDGET_STYLE)
        self.cat_list.addItems(["Characters", "Props", "Environments", "Vehicles"])
        self.cat_list.itemClicked.connect(self.load_assets)
        self.cat_list.setCurrentRow(0) # انتخاب پیش‌فرض
        
        # 2. تعریف لیست است‌ها
        self.asset_list = QListWidget()
        self.asset_list.setStyleSheet(style.LIST_WIDGET_STYLE)
        self.asset_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.asset_list.customContextMenuRequested.connect(self.open_asset_menu)
        self.asset_list.itemClicked.connect(self.load_tasks)

        
        
        # 3. تعریف جدول تسک‌ها
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

        self.task_table.verticalHeader().setDefaultSectionSize(50)
        self.task_table.verticalHeader().setVisible(False)
        self.task_table.setStyleSheet(style.PROJECTS_TABLE)

        self.task_table.itemSelectionChanged.connect(self.update_preview_panel)
        # --- حالا که ویجت‌ها ساخته شدند، می‌توانیم توابع را صدا بزنیم ---

        # Project Selector (بالای صفحه)
        self.setup_project_selector()
        
        # 4. ساخت پنل پیش‌نمایش (ستون چهارم)
        self.preview_panel = QFrame()
        self.preview_panel.setStyleSheet("background-color: #2b2b2b; border-radius: 8px; padding: 10px;")
        self.preview_layout = QVBoxLayout(self.preview_panel)
        self.preview_layout.setAlignment(Qt.AlignTop)
        
        self.lbl_preview_thumb = QLabel("🖼️ No Task Selected")
        self.lbl_preview_thumb.setFixedSize(240, 135) # سایز استاندارد 16:9
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

        # Columns Layout (حالا 4 ستون را کنار هم می‌چینیم)
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(20)
        
        columns_layout.addLayout(self.create_column("Categories", self.cat_list, None))
        columns_layout.addLayout(self.create_column("Assets", self.asset_list, self.add_asset))
        columns_layout.addLayout(self.create_column("Tasks", self.task_table, self.add_task))
        
        # اضافه کردن ستون چهارم به لی‌اوت اصلی
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
        lbl = QLabel("Active Project:")
        lbl.setStyleSheet(style.SECTION_TITLE)
        
        self.project_combo = QComboBox()
        self.project_combo.setMinimumWidth(250)
        self.project_combo.setFixedHeight(35)
        self.project_combo.setStyleSheet(style.ADMIN_COMBO)
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
        # حالا چون cat_list ساخته شده، این خط ارور نمی‌دهد
        if self.cat_list.currentItem():
            self.load_assets(self.cat_list.currentItem())

    def create_column(self, title, widget, add_callback):
        """
        Handle Create Column operation.
        """
        col_layout = QVBoxLayout()
        col_layout.setSpacing(10)
        
        header = QHBoxLayout()
        lbl = QLabel(title)
        lbl.setStyleSheet("font-weight: bold; color: #aaa; font-size: 14px;")
        header.addWidget(lbl)
        header.addStretch()
        
        if add_callback:
            btn = QPushButton("+")
            btn.setFixedSize(30, 30)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(style.BTN_ADD_SMALL)
            btn.clicked.connect(add_callback)
            header.addWidget(btn)
        
        col_layout.addLayout(header)
        col_layout.addWidget(widget)
        return col_layout

    # --- Logic ---

    def load_assets(self, item):
        """
        Handle Load Assets operation.
        """
        if not item: return
        self.asset_list.clear()
        self.task_table.setRowCount(0)
        
        project = self.session.context.project
        if not project: return
        
        category = item.text() # Characters, Props...
        assets = self.session.db.get_assets(project.id, category)
        
        for asset in assets:
            # asset: (id, proj_id, name, cat, status)
            a_id, _, name, _, _ = asset
            list_item = QListWidgetItem(name)
            list_item.setData(Qt.UserRole, a_id)
            self.asset_list.addItem(list_item)

    def add_asset(self):
        """
        Handle Add Asset operation.
        """
        project = self.session.context.project
        current_cat = self.cat_list.currentItem()
        if not project:
            QMessageBox.warning(self, "Error", "No project selected.")
            return
            
        dialog = AssetDialog(self.session, parent=self)
        if current_cat:
            dialog.category_combo.setCurrentText(current_cat.text())
            
        if dialog.exec():
            data = dialog.get_data()
            name = data["name"]
            category = data["category"]
            
            if self.session.db.create_asset(project.id, name, category):
                # ساخت فولدر فیزیکی
                proj_path = os.path.join(project.root_path, project.name)
                FileSystemManager.create_asset_structure(self.session.db, proj_path, category, name)
                
                # رفرش اگر در همان کتگوری هستیم
                if current_cat and current_cat.text() == category:
                    self.load_assets(current_cat)
            else:
                QMessageBox.critical(self, "Error", "Failed to create asset in DB.")

    def open_asset_menu(self, position):
        """
        Handle Open Asset Menu operation.
        """
        item = self.asset_list.itemAt(position)
        if not item: return
        
        asset_id = item.data(Qt.UserRole)
        
        menu = QMenu()
        menu.setStyleSheet(style.MENU_STYLE)
        edit_action = menu.addAction("Edit Asset")
        menu.addSeparator()
        del_action = menu.addAction("Delete Asset")
        
        action = menu.exec(self.asset_list.mapToGlobal(position))
        
        if action == edit_action:
            self.edit_asset(asset_id)
        elif action == del_action:
            self.delete_asset_logic(item)

    def edit_asset(self, asset_id):
        """
        Handle Edit Asset operation.
        """
        # ۱. دریافت اطلاعات قدیمی برای پیدا کردن مسیر فولدر فعلی
        asset_data = self.session.db.get_asset_by_id(asset_id) 
        if not asset_data: return

        old_name = asset_data[2]  # نام قدیمی اَسِت
        category = asset_data[3]  # دسته‌بندی (مثل Characters)

        # ۲. باز کردن دیالوگ ویرایش
        dialog = AssetDialog(self.session, asset_to_edit=asset_data, parent=self)
        
        if dialog.exec():
            new_data = dialog.get_data()
            new_name = new_data['name']
            
            # ۳. آپدیت دیتابیس
            success = self.session.db.update_asset(asset_id, new_name, new_data['category'])
            
            if success:
                # ۴. ری‌نیم فیزیکی فولدر در صورتی که نام تغییر کرده باشد
                if old_name != new_name:
                    project = self.session.context.project
                    # ساخت مسیر کامل فولدر فعلی روی هارد
                    # مسیر: ProjectRoot/ProjectName/Assets/Category/OldName
                    old_folder_path = os.path.join(
                        project.root_path, 
                        project.name, 
                        "Assets", 
                        category, 
                        old_name
                    ).replace("\\", "/") # استانداردسازی مسیر برای ویندوز/شبکه

                    # فراخوانی متد ری‌نیم از فایل سیستم تو
                    if FileSystemManager.rename_folder(old_folder_path, new_name):
                        print(f">> [Cortex] Folder renamed from {old_name} to {new_name}")
                    else:
                        QMessageBox.warning(
                            self, 
                            "Folder Rename Failed", 
                            "Database updated, but physical folder could not be renamed.\n"
                            "Check if a file or folder is open in another app."
                        )
                
                self.load_assets(self.cat_list.currentItem())
            else:
                QMessageBox.critical(self, "Error", "Failed to update asset in Database.")

    def delete_asset_logic(self, item):
        """
        Handle Delete Asset Logic operation.
        """
        asset_id = item.data(Qt.UserRole)
        asset_name = item.text()
        
        confirm = QMessageBox.question(
            self, "Confirm Delete", 
            f"Are you sure you want to delete asset '{asset_name}' and all its tasks?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            # حذف از دیتابیس
            if self.session.db.delete_asset(asset_id):
                # رفرش کردن لیست اسِت‌ها
                current_cat = self.cat_list.currentItem()
                if current_cat:
                    self.load_assets(current_cat)
                QMessageBox.information(self, "Success", "Asset deleted successfully.")
            else:
                QMessageBox.critical(self, "Error", "Failed to delete asset from database.")

    # --- Task Logic ---
    def create_color_widget(self, text, color_code):
        """
        Handle Create Color Widget operation.
        """
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 0, 5, 0)
        layout.setSpacing(8)
        
        color_box = QLabel()
        color_box.setFixedSize(14, 14)
        safe_color = color_code if color_code else "transparent"
        border = "1px solid #666" if color_code else "none"
        color_box.setStyleSheet(f"background-color: {safe_color}; border: {border}; border-radius: 3px;")
        
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
        asset_id = item.data(Qt.UserRole)
        tasks = self.session.db.get_tasks(asset_id) 
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

            # ستون 1: User (ذخیره ID در اینجا برای کار کردن کلیک‌راست و آپدیت پنل)
            user_item = QTableWidgetItem(str(user_name))
            user_item.setData(Qt.UserRole, t_id)
            self.task_table.setItem(idx, 1, user_item)
            
            # ستون 2: Status
            status_color = style.STATUS_COLORS.get(status, "#444")
            s_wdg = self.create_color_widget(status, status_color)
            self.task_table.setCellWidget(idx, 2, s_wdg)
            
        # پاک کردن پنل پیش‌نمایش وقتی لیست جدید لود می‌شود
        self.task_table.clearSelection()
        self.update_preview_panel()

    def add_task(self):
        """
        Handle Add Task operation.
        """
        current_asset = self.asset_list.currentItem()
        if not current_asset: 
            QMessageBox.warning(self, "Error", "Select an Asset first.")
            return
        
        project = self.session.context.project
        dialog = TaskDialog(self.session, project.id, parent=self)
        if dialog.exec():
            data = dialog.get_data()
            asset_id = current_asset.data(Qt.UserRole)
            
            self.session.db.create_task(
                entity_id=asset_id,
                dept_id=data["dept_id"],
                assignee_id=data["assignee_id"],
                title=data["title"],
                description=data["description"],
                start_date=data.get("start_date"),
                due_date=data.get("due_date"),
                estimated_hours=data.get("estimated_hours"),
                entity_type="Asset"
            )
            self.load_tasks(current_asset)

    def open_task_menu(self, position):
        """
        Handle Open Task Menu operation.
        """
        row = self.task_table.currentRow()
        if row == -1: return
        
        # آیدی تسک را از ستون User (ستون 1 در جدول سه ستونه) می‌خوانیم
        item = self.task_table.item(row, 1) 
        if not item: return
        task_id = item.data(Qt.UserRole)

        menu = QMenu()
        menu.setStyleSheet(style.MENU_STYLE)
        view_action = menu.addAction("View Details")
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
        elif action == edit_action:
            self.edit_task(task_id)
        elif action == del_action:
            self.delete_task(task_id)

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

    def delete_task(self, task_id):
        """
        Handle Delete Task operation.
        """
        confirm = QMessageBox.question(self, "Delete", "Delete this task?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.session.db.delete_task(task_id)
            self.load_tasks(self.asset_list.currentItem())

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
            
            # اضافه کردن اطلاعات آخرین پابلیش به تایم‌لاین
            publish_info = f"<br><br>✨ Last Publish: <b>v{version:03d}</b><br>🕒 {pub_date}"

            if thumb_path and os.path.exists(thumb_path):
                # لود کردن عکس در لیبل
                pixmap = QPixmap(thumb_path)
                # کراپ و تغییر سایز هوشمند (بدون دفرمه شدن)
                pixmap = pixmap.scaled(240, 135, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                self.lbl_preview_thumb.setPixmap(pixmap)
            else:
                self.lbl_preview_thumb.clear()
                self.lbl_preview_thumb.setText("🖼️ Image Missing")
        else:
            self.lbl_preview_thumb.clear()
            self.lbl_preview_thumb.setText("🖼️ No Publish Yet")
            publish_info = "<br><br>✨ Last Publish: <b>None</b>"

        # 4. آپدیت متن تایم‌لاین (اطلاعات ددلاین + اطلاعات آخرین پابلیش)
        self.lbl_preview_timeline.setText(f"📅 Start: <b>{start_date}</b><br>🚨 Due: <b>{due_date}</b><br>⏱️ Est. Time: <b>{hours} hrs</b>{publish_info}")


    def open_shot_builder(self, shot_id, shot_name):
        """
        Handle Open Shot Builder operation.
        """
        from app.ui.shot_builder import ShotBuilder
        dialog = ShotBuilder(self.session, shot_id, shot_name, parent=self)
        dialog.exec()

    def set_task_status(self, task_id, status):
        """آپدیت سریع وضعیت و رفرش جدول"""
        if self.session.db.update_task_status(task_id, status):
            self.load_tasks(self.asset_list.currentItem())
            # ---> این خط باعث می‌شود پیش‌نمایش نپرد <---
            self.select_task_row(task_id)

    def edit_task(self, task_id):
        """
        Handle Edit Task operation.
        """
        task_data = self.session.db.get_task_by_id(task_id)
        if not task_data: return
        
        project = self.session.context.project
        # باز کردن دیالوگ
        from app.ui.task_dialog import TaskDialog
        dialog = TaskDialog(self.session, project.id, task_to_edit=task_data, parent=self)
        
        if dialog.exec():
            data = dialog.get_data()
            success = self.session.db.update_task_details(
                task_id, 
                data["title"], 
                data["description"], 
                data["assignee_id"], 
                data["dept_id"],
                start_date=data.get("start_date"),
                due_date=data.get("due_date"),
                estimated_hours=data.get("estimated_hours")
            )
            if success:
                self.load_tasks(self.asset_list.currentItem())
                # ---> این خط جادویی باعث می‌شود پیش‌نمایش آپدیت شود <---
                self.select_task_row(task_id)

    def select_task_row(self, task_id):
        """پیدا کردن سطر تسک، اسکرول به آن و آپدیت تصویر"""
        for row in range(self.task_table.rowCount()):
            item = self.task_table.item(row, 1) 
            if item and str(item.data(Qt.UserRole)) == str(task_id):
                self.task_table.selectRow(row)
                self.task_table.scrollToItem(item) # ---> اسکرول خودکار
                self.update_preview_panel()        # ---> اجرای قطعی
                break

    def jump_to_task(self, ctx):
        """پیدا کردن و انتخاب اتوماتیک پروژه، دسته‌بندی، اَسِت و تسک"""
        # 1. تنظیم پروژه
        idx = self.project_combo.findData(ctx["project_id"])
        if idx >= 0:
            if self.project_combo.currentIndex() != idx:
                self.project_combo.setCurrentIndex(idx)

        # 2. پیدا کردن کتگوری
        for i in range(self.cat_list.count()):
            item = self.cat_list.item(i)
            if item.text() == ctx["parent_name"]: 
                self.cat_list.setCurrentItem(item)
                self.load_assets(item)
                break
        
        # 3. پیدا کردن اَسِت
        for i in range(self.asset_list.count()):
            item = self.asset_list.item(i)
            if str(item.data(Qt.UserRole)) == str(ctx["entity_id"]):
                self.asset_list.setCurrentItem(item)
                self.load_tasks(item)
                break
        
        # 4. اسکرول و انتخاب دقیق تسک
        self.select_task_row(ctx["task_id"])