import os
import sys
import bpy
import re
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
                               QListWidgetItem, QLabel, QPushButton, QSplitter, 
                               QWidget, QMessageBox, QTabWidget, QTableWidget, 
                               QHeaderView, QAbstractItemView, QTableWidgetItem) 
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QColor


# Path Fix
try:
    current_folder = os.path.dirname(os.path.abspath(__file__))
    root_folder = os.path.dirname(os.path.dirname(current_folder))
    if root_folder not in sys.path:
        sys.path.append(root_folder)
except: pass

from app.core.database import DatabaseManager
import style

class BlenderLoader(QDialog):
    def __init__(self):
        """
        Handle   Init   operation.
        """
        super().__init__()
        self.setWindowTitle("Cortex Universal Loader (Blender)")
        self.resize(1000, 600)
        self.setStyleSheet(style.PUBLISH_DIALOG)
        
        self.db = DatabaseManager()
        self.user_name = os.environ.get("CORTEX_USER", "Unknown")
        self.user = self.db.get_user_by_username(self.user_name)
        
        self.init_ui()
        self.load_tasks()
        self.refresh_shot_contents()

    def init_ui(self):
        """
        Handle Init Ui operation.
        """
        main_layout = QVBoxLayout(self)
        
        # --- Tabs Setup ---
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Tab 1: Loader (همان UI قبلی که جابجا شد)
        self.tab_loader = QWidget()
        self.setup_loader_tab()
        self.tabs.addTab(self.tab_loader, "📂 Loader")

        
        # Tab 2: Scene Manager (جدید)
        self.tab_manager = QWidget()
        self.setup_manager_tab()
        self.tabs.addTab(self.tab_manager, "♻️ Scene Manager")
        
        # Tab 3: Importer (جدید)
        self.tab_importer = QWidget()
        self.setup_importer_tab()
        self.tabs.addTab(self.tab_importer, "📥 Importer (Cross-App)")

        # tab 4: shot contents
        self.tab_shot_contents = QWidget()
        self.setup_shot_contents_tab()
        self.tabs.addTab(self.tab_shot_contents, "🎬 Shot Contents")
        
        # بررسی اولیه برای تب منیجر
        self.refresh_scene_manager()

    # ==========================================
    # TAB 1: LOADER UI (Refactored)
    # ==========================================
    def setup_loader_tab(self):
        """
        Handle Setup Loader Tab operation.
        """
        layout = QVBoxLayout(self.tab_loader)
        
        # Header (Common)
        header = QHBoxLayout()
        header.addWidget(QLabel("📂 <b>Universal Loader</b>"))
        layout.addLayout(header)

        splitter = QSplitter(Qt.Horizontal)
        
        # Col 1: Tasks
        w1 = QWidget()
        l1 = QVBoxLayout(w1)
        l1.addWidget(QLabel("Select Task:"))
        self.list_tasks = QListWidget()
        self.list_tasks.itemClicked.connect(self.on_task_click)
        l1.addWidget(self.list_tasks)
        
        # Col 2: Files
        w2 = QWidget()
        l2 = QVBoxLayout(w2)
        l2.addWidget(QLabel("Select Version:"))
        self.list_files = QListWidget()
        self.list_files.itemClicked.connect(self.on_file_click)
        self.list_files.itemDoubleClicked.connect(self.on_open)
        l2.addWidget(self.list_files)
        
        # Col 3: Actions
        w3 = QWidget()
        l3 = QVBoxLayout(w3)
        l3.setSpacing(10)
        
        # Preview
        self.lbl_prev = QLabel("Select File")
        self.lbl_prev.setFixedSize(300, 180)
        self.lbl_prev.setStyleSheet(style.LBL_THUMBNAIL)
        self.lbl_prev.setScaledContents(True)
        self.lbl_prev.setAlignment(Qt.AlignCenter)
        l3.addWidget(self.lbl_prev)
        
        l3.addWidget(QLabel("<b>Actions:</b>"))
        
        # Buttons
        self.btn_open = QPushButton("📂 OPEN SCENE")
        self.btn_open.setToolTip("Open file for editing")
        self.btn_open.setStyleSheet(style.BTN_SUCCESS)
        self.btn_open.clicked.connect(self.on_open)
        l3.addWidget(self.btn_open)
        
        self.btn_append = QPushButton("➕ APPEND (Lookdev)")
        self.btn_append.setToolTip("Import Collections (Editable)")
        self.btn_append.setStyleSheet(style.BTN_CTX_LOADER)
        self.btn_append.clicked.connect(self.on_append)
        l3.addWidget(self.btn_append)
        
        self.btn_link = QPushButton("🔗 LINK (Stage)")
        self.btn_link.setToolTip("Link Collections (Read-Only / Auto Update)")
        self.btn_link.setStyleSheet(style.BTN_CTX_XREF)         
        self.btn_link.clicked.connect(self.on_link)
        l3.addWidget(self.btn_link)
        
        l3.addStretch()
        
        splitter.addWidget(w1); splitter.addWidget(w2); splitter.addWidget(w3)
        splitter.setStretchFactor(0, 1); splitter.setStretchFactor(1, 1); splitter.setStretchFactor(2, 0)
        layout.addWidget(splitter)

    # ==========================================
    # TAB 2: SCENE MANAGER LOGIC (Blender Specific)
    # ==========================================
    def setup_manager_tab(self):
        """
        Handle Setup Manager Tab operation.
        """
        layout = QVBoxLayout(self.tab_manager)
        
        # Top Bar
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("<b>Managed Libraries (.blend links):</b>"))
        top_bar.addStretch()
        btn_refresh = QPushButton("↻ Refresh")
        btn_refresh.setStyleSheet(style.BTN_TOOLBAR)
        btn_refresh.clicked.connect(self.refresh_scene_manager)
        top_bar.addWidget(btn_refresh)
        layout.addLayout(top_bar)
        
        # Table
        self.table_refs = QTableWidget()
        self.table_refs.setColumnCount(5)
        self.table_refs.setHorizontalHeaderLabels(["Library Name", "Current Ver", "Latest Ver", "Status", "Action"])
        self.table_refs.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_refs.setSelectionBehavior(QAbstractItemView.SelectRows)
        # استفاده از استایل مرکزی
        self.table_refs.setStyleSheet(style.TABLE_MANAGER)
        layout.addWidget(self.table_refs)

    def refresh_scene_manager(self):
        """اسکن لینک‌های بلندر (bpy.data.libraries)"""
        self.table_refs.setRowCount(0)
        
        # در بلندر، فایل‌های لینک شده در libraries ذخیره می‌شوند
        for lib in bpy.data.libraries:
            if not lib.filepath: continue
            
            # تبدیل مسیر نسبی (//) به مطلق برای بررسی فایل
            abs_path = bpy.path.abspath(lib.filepath)
            filename = os.path.basename(abs_path)
            folder = os.path.dirname(abs_path)
            
            # آنالیز ورژن (Regex)
            match = re.search(r"_v(\d{3})", filename)
            
            current_ver = 0
            latest_ver = 0
            is_outdated = False
            
            if match:
                ver_str = match.group(1)
                current_ver = int(ver_str)
                prefix = filename.split(f"_v{ver_str}")[0]
                
                # جستجو برای ورژن جدیدتر
                if os.path.exists(folder):
                    files = os.listdir(folder)
                    max_v = current_ver
                    for f in files:
                        if f.startswith(prefix) and f.endswith(".blend") and "_v" in f:
                            try:
                                v = int(f.split("_v")[-1].split(".")[0])
                                if v > max_v: max_v = v
                            except: pass
                    latest_ver = max_v
                    
            is_outdated = latest_ver > current_ver
            
            # پر کردن جدول
            row = self.table_refs.rowCount()
            self.table_refs.insertRow(row)
            
            self.table_refs.setItem(row, 0, QTableWidgetItem(lib.name)) # نام لایبرری در بلندر
            self.table_refs.setItem(row, 1, QTableWidgetItem(f"v{current_ver:03d}"))
            
            item_lat = QTableWidgetItem(f"v{latest_ver:03d}")
            item_lat.setForeground(QColor("#ff5555") if is_outdated else QColor("#55ff55"))
            self.table_refs.setItem(row, 2, item_lat)
            
            status_text = "⚠️ Outdated" if is_outdated else "✅ OK"
            self.table_refs.setItem(row, 3, QTableWidgetItem(status_text))
            
            if is_outdated:
                btn_upd = QPushButton("🚀 Update")
                btn_upd.setStyleSheet(style.BTN_UPDATE)
                
                # ساخت مسیر جدید
                new_filename = filename.replace(f"v{current_ver:03d}", f"v{latest_ver:03d}")
                new_full_path = os.path.join(folder, new_filename)
                
                # اتصال دکمه به تابع آپدیت
                # نکته: ما اسم لایبرری را پاس می‌دهیم چون در بلندر با نام دسترسی داریم
                btn_upd.clicked.connect(lambda checked, lib_name=lib.name, path=new_full_path: self.do_update_library(lib_name, path))
                self.table_refs.setCellWidget(row, 4, btn_upd)
            else:
                self.table_refs.setItem(row, 4, QTableWidgetItem("-"))

    def do_update_library(self, lib_name, new_path):
        """اجرای آپدیت در بلندر"""
        try:
            lib = bpy.data.libraries.get(lib_name)
            if lib:
                # 1. تغییر مسیر فایل
                lib.filepath = new_path
                # 2. ریلود کردن دیتا از مسیر جدید
                lib.reload()
                
                QMessageBox.information(self, "Updated", f"Library '{lib_name}' updated successfully!")
                self.refresh_scene_manager()
            else:
                QMessageBox.warning(self, "Error", "Library not found in memory.")
                
        except Exception as e:
            QMessageBox.critical(self, "Update Error", str(e))

    # ==========================================
    # TAB 3: IMPORTER (Placeholder)
    # ==========================================
    def setup_importer_tab(self):
        """
        Handle Setup Importer Tab operation.
        """
        layout = QVBoxLayout(self.tab_importer)
        
        splitter = QSplitter(Qt.Horizontal)
        
        # سمت چپ: لیست تسک‌ها
        self.list_tasks_imp = QListWidget()
        self.list_tasks_imp.itemClicked.connect(self.on_task_clicked_importer)
        layout_l = QVBoxLayout()
        layout_l.addWidget(QLabel("Select Source Task:"))
        layout_l.addWidget(self.list_tasks_imp)
        w_left = QWidget(); w_left.setLayout(layout_l)
        
        # سمت راست: لیست فایل‌های Interchange
        self.list_files_imp = QListWidget()
        layout_r = QVBoxLayout()
        layout_r.addWidget(QLabel("Available Interchange Files (FBX/ABC):"))
        layout_r.addWidget(self.list_files_imp)
        
        self.btn_import_fbx = QPushButton("📥 Import FBX/ABC to Scene")
        self.btn_import_fbx.setStyleSheet(style.BTN_SUCCESS)
        self.btn_import_fbx.clicked.connect(self.on_import_interchange)
        layout_r.addWidget(self.btn_import_fbx)
        
        w_right = QWidget(); w_right.setLayout(layout_r)
        
        splitter.addWidget(w_left)
        splitter.addWidget(w_right)
        layout.addWidget(splitter)
        
        self.refresh_importer_tasks()

    def refresh_importer_tasks(self):
        """
        Handle Refresh Importer Tasks operation.
        """
        self.list_tasks_imp.clear()
        if not self.user: return
        tasks = self.db.get_user_tasks(self.user.id, include_done=True)
        for t in tasks:
            item = QListWidgetItem(f"{t[3]} | {t[4]}")
            item.setData(Qt.UserRole, t[0])
            self.list_tasks_imp.addItem(item)

    # ==========================================
    # Tab 4: Shot Contents
    # ==========================================
    def setup_shot_contents_tab(self):
        """
        Handle Setup Shot Contents Tab operation.
        """
        layout = QVBoxLayout(self.tab_shot_contents)
        
        self.lbl_shot_info = QLabel("<b>Current Shot:</b> None")
        self.lbl_shot_info.setStyleSheet("color: #d35400; font-size: 14px;") # رنگ نارنجی بلندر
        layout.addWidget(self.lbl_shot_info)

        self.table_shot_assets = QTableWidget()
        self.table_shot_assets.setColumnCount(4)
        self.table_shot_assets.setHorizontalHeaderLabels(["Asset Name", "Category", "Status", "Action"])
        self.table_shot_assets.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_shot_assets.setStyleSheet(style.TABLE_MANAGER) #
        layout.addWidget(self.table_shot_assets)
        
        self.btn_assemble_all = QPushButton("🚀 ASSEMBLE ALL ASSETS (LINK)")
        self.btn_assemble_all.setStyleSheet(style.BTN_SUCCESS) #
        self.btn_assemble_all.setFixedHeight(40)
        self.btn_assemble_all.clicked.connect(self.on_assemble_all)
        layout.addWidget(self.btn_assemble_all)

    # --- Logic ---

    def on_task_clicked_importer(self, item):
        """
        Handle On Task Clicked Importer operation.
        """
        task_id = item.data(Qt.UserRole)
        self.list_files_imp.clear()
        
        context = self.db.get_task_context_data(task_id)
        if not context: return
        
        # ۱. استخراج نام تسک برای فیلتر (مثلاً Head)
        task_name_filter = context['task_title'].lower() 

        root = context['project_root']
        proj = context['project_name']
        entity_path = os.path.join(root, proj, "Assets", context['parent_name'], context['entity_name'])
        fbx_folder = os.path.join(entity_path, "3d", "obj")
        
        if os.path.exists(fbx_folder):
            # ۲. اعمال فیلتر هوشمند: فقط فایل‌هایی که نام تسک در آن‌هاست
            all_files = os.listdir(fbx_folder)
            filtered_files = [f for f in all_files 
                              if (f.endswith(".fbx") or f.endswith(".abc")) 
                              and task_name_filter in f.lower()]
            
            filtered_files.sort(reverse=True)
            for f in filtered_files:
                fi = QListWidgetItem(f)
                fi.setData(Qt.UserRole, os.path.join(fbx_folder, f))
                self.list_files_imp.addItem(fi)

    def refresh_shot_contents(self):
        """نمایش اَسِت‌های مرتبط با شات در بلندر"""
        self.table_shot_assets.setRowCount(0)
        task_id = os.environ.get("CORTEX_TASK_ID")
        if not task_id: return

        context = self.db.get_task_context_data(task_id)
        if not context or context.get('type') != "Shot": return

        # استفاده از کلید هوشمند entity_id که در دیتابیس اصلاح کردیم
        shot_id = context.get('entity_id') 
        
        if shot_id:
            linked_assets = self.db.get_shot_assets_extended(shot_id)
            for asset in linked_assets:
                row = self.table_shot_assets.rowCount()
                self.table_shot_assets.insertRow(row)
                self.table_shot_assets.setItem(row, 0, QTableWidgetItem(asset[1])) 
                self.table_shot_assets.setItem(row, 1, QTableWidgetItem(asset[2])) 
                
                # ساخت مسیر بر اساس فایل سیستم بلندر
                asset_path = os.path.join(asset[3], asset[4], "Assets", asset[2], asset[1], "Work", "blender")
                
                btn_link = QPushButton("🔗 LINK Latest")
                btn_link.setStyleSheet(style.BTN_CTX_XREF)
                # در بلندر از متد on_link استفاده می‌کنیم
                btn_link.clicked.connect(lambda chk=False, p=asset_path: self.link_latest_asset(p))
                self.table_shot_assets.setCellWidget(row, 3, btn_link)

    def on_import_interchange(self):
        """ایمپورت هوشمند به بلندر"""
        item = self.list_files_imp.currentItem()
        if not item: return
        path = item.data(Qt.UserRole)
        if not path or not os.path.exists(path): return

        try:
            if path.endswith(".fbx"):
                # ایمپورت FBX با تنظیمات مقیاس درست برای هماهنگی با مکس
                bpy.ops.import_scene.fbx(filepath=path, use_manual_orientation=False, global_scale=1.0)
            elif path.endswith(".abc"):
                # ایمپورت Alembic برای انیمیشن‌ها
                bpy.ops.wm.alembic_import(filepath=path, as_background_job=False)
            
            QMessageBox.information(self, "Success", f"Imported: {os.path.basename(path)}")
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to import: {str(e)}")
            
    def load_tasks(self):
        """
        Handle Load Tasks operation.
        """
        if not self.user: return
        self.list_tasks.clear()
        tasks = self.db.get_user_tasks(self.user.id, include_done=True)
        for t in tasks:
            display = f"{t[3]} | {t[4]} ({t[1]})"
            item = QListWidgetItem(display)
            item.setData(Qt.UserRole, t[0])
            self.list_tasks.addItem(item)

    def on_task_click(self, item):
        """
        Handle On Task Click operation.
        """
        self.list_files.clear()
        self.lbl_prev.setText("Select File")
        self.lbl_prev.setPixmap(QPixmap())
        
        task_id = item.data(Qt.UserRole)
        ctx = self.db.get_task_context_data(task_id)
        if not ctx: return
        
        root = ctx['project_root']
        proj = ctx['project_name']
        cat = "Assets" if ctx['type'] == 'Asset' else "Sequences"
        
        dept = "General"
        try:
            self.db.cursor.execute("SELECT d.name FROM tasks t JOIN departments d ON t.department_id=d.id WHERE t.id=?", (task_id,))
            res = self.db.cursor.fetchone()
            if res: dept = res[0].replace(" ", "")
        except: pass
            
        task_title = ctx['task_title'].replace(" ", "_")
        
        self.target_path = os.path.join(root, proj, cat, ctx['parent_name'], ctx['entity_name'], 
                                        "Work", "blender", dept, task_title)
        self.target_task_id = task_id
        self.target_task_name = task_title
        
        if os.path.exists(self.target_path):
            files = [f for f in os.listdir(self.target_path) if f.endswith(".blend")]
            files.sort(reverse=True)
            for f in files:
                fi = QListWidgetItem(f)
                fi.setData(Qt.UserRole, os.path.join(self.target_path, f))
                self.list_files.addItem(fi)
        else:
            self.list_files.addItem("No Work Folder")

    def on_file_click(self, item):
        """
        Handle On File Click operation.
        """
        path = item.data(Qt.UserRole)
        if not path: return
        
        base, _ = os.path.splitext(path)
        jpg = base + ".jpg"
        
        if os.path.exists(jpg):
            pix = QPixmap(jpg)
            self.lbl_prev.setPixmap(pix.scaled(self.lbl_prev.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.lbl_prev.setText("No Preview")

    def get_selected_path(self):
        """
        Handle Get Selected Path operation.
        """
        item = self.list_files.currentItem()
        if not item: return None
        return item.data(Qt.UserRole)

    # --- ACTIONS ---

    def on_assemble_all(self):
        """وارد کردن تمام اَسِت‌های لینک شده به شات (مخصوص بلندر)"""
        task_id = os.environ.get("CORTEX_TASK_ID")
        context = self.db.get_task_context_data(task_id)
        
        if not context or context.get('type') != "Shot":
            QMessageBox.warning(self, "Context Error", "This action is only available within a Shot task.")
            return

        # دریافت لیست اَسِت‌ها از دیتابیس
        linked_assets = self.db.get_shot_assets_extended(context['entity_id'])
        
        count = 0
        for asset in linked_assets:
            # ساخت مسیر Work بلندر: Assets/Category/Name/Work/blender
            # دقت کن که در دیتابیس: asset[3]=root, asset[4]=project_name, asset[2]=category, asset[1]=name
            asset_work_path = os.path.join(asset[3], asset[4], "Assets", asset[2], asset[1], "Work", "blender")
            
            if os.path.exists(asset_work_path):
                # پیدا کردن آخرین فایل blend
                found_files = []
                for root, dirs, files in os.walk(asset_work_path):
                    for f in files:
                        if f.endswith(".blend") and "_v" in f:
                            found_files.append(os.path.join(root, f))
                
                if found_files:
                    found_files.sort(reverse=True)
                    latest_file = found_files[0]
                    
                    # ذخیره مسیر در متغیر موقت کلاس و اجرای لینک
                    self.target_file_to_load = latest_file 
                    try:
                        # استفاده از متد load_asset که قبلا تعریف کردیم (Link=True)
                        self.load_asset(link=True) 
                        count += 1
                    except Exception as e:
                        print(f"!! Link Error for {asset[1]}: {e}")
        
        if count > 0:
            QMessageBox.information(self, "Assemble Done", f"Successfully linked {count} assets.")
        else:
            QMessageBox.warning(self, "No Assets", "No published blender files found for these assets.")

    def on_open(self):
        """
        Handle On Open operation.
        """
        path = self.get_selected_path()
        if not path: return
        
        print(f">> Opening: {path}")
        os.environ["CORTEX_WORK_PATH"] = self.target_path
        os.environ["CORTEX_TASK_ID"] = str(self.target_task_id)
        os.environ["CORTEX_TASK_NAME"] = self.target_task_name
        
        bpy.ops.wm.open_mainfile(filepath=path)
        self.close()
        
        try:
            import cortex_ui
            if cortex_ui.cortex_win: cortex_ui.show_ui()
        except: pass

    def load_asset(self, link=True):
        """تابع هوشمند: اول تلاش برای لود کالکشن، اگر نبود لود آبجکت"""
        path = self.get_selected_path()
        if not path: return
        
        try:
            # متغیرها برای ذخیره نتیجه
            loaded_collections = []
            loaded_objects = []

            # 1. بررسی و استخراج محتویات فایل
            with bpy.data.libraries.load(path, link=link) as (data_from, data_to):
                # سناریو الف: اگر فایل استاندارد است و کالکشن دارد
                if data_from.collections:
                    data_to.collections = data_from.collections
                # سناریو ب: اگر فایل کالکشن ندارد (فال‌بک به آبجکت‌ها)
                elif data_from.objects:
                    data_to.objects = data_from.objects
                else:
                    QMessageBox.warning(self, "Empty File", "No Collections or Objects found in this file.")
                    return

            # دسترسی به دیتاهای لود شده (بعد از بسته شدن with)
            if hasattr(data_to, 'collections'):
                loaded_collections = data_to.collections
            if hasattr(data_to, 'objects'):
                loaded_objects = data_to.objects

            # 2. وارد کردن به صحنه
            # الف) وارد کردن کالکشن‌ها (روش تمیز)
            for col in loaded_collections:
                if col is not None:
                    if link:
                        # ساخت Instance (روش استاندارد Staging)
                        empty = bpy.data.objects.new(col.name, None)
                        empty.instance_type = 'COLLECTION'
                        empty.instance_collection = col
                        bpy.context.collection.objects.link(empty)
                    else:
                        # اپند کردن کامل (روش Lookdev)
                        bpy.context.collection.children.link(col)
            
            # ب) وارد کردن آبجکت‌ها (اگر کالکشنی نبود)
            count_obj = 0
            for obj in loaded_objects:
                if obj is not None:
                    # چک می‌کنیم که قبلا لینک نشده باشد
                    if obj.name not in bpy.context.scene.objects:
                        bpy.context.collection.objects.link(obj)
                        count_obj += 1

            # گزارش نتیجه
            total = len([c for c in loaded_collections if c]) + count_obj
            action = "Linked" if link else "Appended"
            
            if total > 0:
                print(f">> {action} Done: {os.path.basename(path)}")
                QMessageBox.information(self, "Success", f"Successfully {action} {total} items.")
                self.close()
            else:
                QMessageBox.warning(self, "Warning", "Nothing valid imported.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load: {e}")
            print(f"Load Error Details: {e}")
            import traceback
            traceback.print_exc()

    def on_append(self):
        """
        Handle On Append operation.
        """
        self.load_asset(link=False) # Append = Editable

    def on_link(self):
        """
        Handle On Link operation.
        """
        self.load_asset(link=True)  # Link = Read Only (Reference)

    def link_latest_asset(self, blender_work_path):
        """یافتن آخرین فایل .blend در پوشه ورک و لینک کردن آن"""
        if not os.path.exists(blender_work_path): return
        
        # اسکن تمام ساب‌فولدرها برای پیدا کردن جدیدترین فایل
        all_files = []
        for root, dirs, files in os.walk(blender_work_path):
            for f in files:
                if f.endswith(".blend"):
                    all_files.append(os.path.join(root, f))
        
        if not all_files: return
        all_files.sort(reverse=True) # جدیدترین ورژن
        
        # ذخیره در متغیر موقت و اجرای لینک
        self.target_file_to_load = all_files[0]
        self.on_link()

    

def run():
    """
    Handle Run operation.
    """
    win = BlenderLoader()
    win.show()