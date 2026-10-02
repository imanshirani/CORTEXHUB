# Location: plugins/houdini/scripts/loader.py
import os
import sys
import re
import hou
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
                               QListWidgetItem, QLabel, QPushButton, QTabWidget, 
                               QWidget, QSplitter, QMessageBox, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QAbstractItemView)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap, QColor

# Path Fix
try:
    current_script_path = os.path.dirname(os.path.abspath(__file__))
    root_path = os.path.dirname(os.path.dirname(current_script_path))
    if root_path not in sys.path: sys.path.append(root_path)
except: pass

from app.core.database import DatabaseManager
import style

class LoaderWindow(QDialog):
    def __init__(self, parent=None):
        super(LoaderWindow, self).__init__(parent)
        self.setWindowTitle("Cortex Universal Tool | Houdini")
        self.resize(1100, 650)
        
        try: self.setStyleSheet(style.PUBLISH_DIALOG)
        except: pass
        
        self.db = DatabaseManager()
        self.current_user = os.environ.get("CORTEX_USER", "admin")
        self.user_obj = self.db.get_user_by_username(self.current_user)
        self.current_browsing_task_id = None
        
        self.init_ui()
        self.load_my_tasks()
        self.refresh_scene_manager()
        self.refresh_shot_contents()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Tabs
        self.tab_loader = QWidget()
        self.setup_loader_tab()
        self.tabs.addTab(self.tab_loader, "📂 Loader (Work Files)")
        
        self.tab_manager = QWidget()
        self.setup_manager_tab()
        self.tabs.addTab(self.tab_manager, "♻️ Scene Manager")
        
        self.tab_importer = QWidget()
        self.setup_importer_tab()
        self.tabs.addTab(self.tab_importer, "📥 Importer (Caches)")

        self.tab_shot_contents = QWidget()
        self.setup_shot_contents_tab()
        self.tabs.addTab(self.tab_shot_contents, "🎬 Shot Contents")

    # ==========================================
    # TAB 1: LOADER LOGIC (WORK FILES)
    # ==========================================
    def setup_loader_tab(self):
        layout = QVBoxLayout(self.tab_loader)
        splitter = QSplitter(Qt.Horizontal)
        
        # Col 1: Tasks
        w1 = QWidget(); l1 = QVBoxLayout(w1)
        l1.addWidget(QLabel("Select Task:"))
        self.list_tasks = QListWidget()
        self.list_tasks.itemClicked.connect(self.on_task_clicked)
        l1.addWidget(self.list_tasks)
        
        # Col 2: Files
        w2 = QWidget(); l2 = QVBoxLayout(w2)
        l2.addWidget(QLabel("Select Version:"))
        self.list_files = QListWidget()
        self.list_files.itemClicked.connect(self.on_file_clicked)
        self.list_files.itemDoubleClicked.connect(self.on_open)
        l2.addWidget(self.list_files)
        
        # Col 3: Actions
        w3 = QWidget(); l3 = QVBoxLayout(w3)
        l3.setSpacing(10)
        
        self.lbl_preview = QLabel("Select a file")
        self.lbl_preview.setFixedSize(300, 180)
        try: self.lbl_preview.setStyleSheet(style.LBL_THUMBNAIL)
        except: pass
        self.lbl_preview.setAlignment(Qt.AlignCenter)
        self.lbl_preview.setScaledContents(True)
        l3.addWidget(self.lbl_preview)
        
        l3.addWidget(QLabel("<b>Actions:</b>"))
        
        self.btn_open = QPushButton("📂 OPEN SCENE")
        try: self.btn_open.setStyleSheet(style.BTN_SUCCESS)
        except: pass
        self.btn_open.clicked.connect(self.on_open)
        l3.addWidget(self.btn_open)
        
        self.btn_merge = QPushButton("➕ MERGE SCENE")
        try: self.btn_merge.setStyleSheet(style.BTN_CTX_LOADER)
        except: pass
        self.btn_merge.clicked.connect(self.on_merge)
        l3.addWidget(self.btn_merge)
        
        l3.addStretch()
        
        splitter.addWidget(w1); splitter.addWidget(w2); splitter.addWidget(w3)
        splitter.setStretchFactor(0, 1); splitter.setStretchFactor(1, 1); splitter.setStretchFactor(2, 0)
        layout.addWidget(splitter)

    # ==========================================
    # TAB 2: SCENE MANAGER LOGIC
    # ==========================================
    def setup_manager_tab(self):
        layout = QVBoxLayout(self.tab_manager)
        
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("<b>Managed Caches (Alembic/VDB):</b>"))
        top_bar.addStretch()
        btn_refresh_man = QPushButton("↻ Refresh List")
        try: btn_refresh_man.setStyleSheet(style.BTN_TOOLBAR)
        except: pass
        btn_refresh_man.clicked.connect(self.refresh_scene_manager)
        top_bar.addWidget(btn_refresh_man)
        layout.addLayout(top_bar)
        
        self.table_refs = QTableWidget(0, 5)
        self.table_refs.setHorizontalHeaderLabels(["Node/Asset", "Current Ver", "Latest Ver", "Status", "Action"])
        self.table_refs.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_refs.setSelectionBehavior(QAbstractItemView.SelectRows)
        try: self.table_refs.setStyleSheet(style.TABLE_MANAGER)
        except: pass
        layout.addWidget(self.table_refs)

    def refresh_scene_manager(self):
        """اسکن صحنه هودینی برای پیدا کردن نودهای Alembic و VDB"""
        self.table_refs.setRowCount(0)
        
        # پیدا کردن تمام نودهای کش در صحنه
        cache_nodes = []
        for node in hou.node("/").allSubChildren():
            ntype = node.type().name()
            if ntype in ["alembic", "alembicarchive"]:
                cache_nodes.append((node, "fileName"))
            elif ntype == "file":
                path = node.parm("file").evalAsString()
                if path.endswith((".vdb", ".abc", ".bgeo", ".bgeo.sc")):
                    cache_nodes.append((node, "file"))

        for node, parm_name in cache_nodes:
            file_path = node.parm(parm_name).evalAsString()
            if not file_path or not os.path.exists(file_path): continue
            
            filename = os.path.basename(file_path)
            folder = os.path.dirname(file_path)
            
            match = re.search(r"_v(\d{3})", filename)
            if not match: continue
                
            ver_str = match.group(1)
            current_ver = int(ver_str)
            prefix = filename.split(f"_v{ver_str}")[0]
            
            latest_ver = current_ver
            if os.path.exists(folder):
                files = os.listdir(folder)
                for f in files:
                    if f.startswith(prefix) and f.endswith(filename[-4:]) and "_v" in f:
                        try:
                            v = int(f.split("_v")[-1].split(".")[0])
                            if v > latest_ver: latest_ver = v
                        except: pass
            
            is_outdated = latest_ver > current_ver
            
            row = self.table_refs.rowCount()
            self.table_refs.insertRow(row)
            
            self.table_refs.setItem(row, 0, QTableWidgetItem(f"{node.name()} ({filename})"))
            self.table_refs.setItem(row, 1, QTableWidgetItem(f"v{current_ver:03d}"))
            
            item_lat = QTableWidgetItem(f"v{latest_ver:03d}")
            item_lat.setForeground(QColor("#ff5555") if is_outdated else QColor("#55ff55"))
            self.table_refs.setItem(row, 2, item_lat)
            
            self.table_refs.setItem(row, 3, QTableWidgetItem("⚠️ Outdated" if is_outdated else "✅ OK"))
            
            if is_outdated:
                btn_update = QPushButton("🚀 Update Cache")
                try: btn_update.setStyleSheet(style.BTN_UPDATE)
                except: pass
                new_filename = filename.replace(f"v{current_ver:03d}", f"v{latest_ver:03d}")
                new_full_path = os.path.join(folder, new_filename).replace("\\", "/")
                btn_update.clicked.connect(lambda checked=False, n=node, p=parm_name, path=new_full_path: self.do_update_cache(n, p, path))
                self.table_refs.setCellWidget(row, 4, btn_update)
            else:
                self.table_refs.setItem(row, 4, QTableWidgetItem("-"))

    def do_update_cache(self, node, parm_name, new_path):
        """آپدیت مسیر فایل در نود هودینی"""
        try:
            node.parm(parm_name).set(new_path)
            QMessageBox.information(self, "Updated", f"Node updated to: {os.path.basename(new_path)}")
            self.refresh_scene_manager()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Update Failed: {str(e)}")

    # ==========================================
    # TAB 3: IMPORTER LOGIC (CACHES & MATERIALS)
    # ==========================================
    def setup_importer_tab(self):
        layout = QVBoxLayout(self.tab_importer)
        splitter = QSplitter(Qt.Horizontal)
        
        w_left = QWidget(); layout_l = QVBoxLayout(w_left)
        layout_l.addWidget(QLabel("Select Source Task:"))
        self.list_tasks_imp = QListWidget()
        self.list_tasks_imp.itemClicked.connect(self.on_task_clicked_importer)
        layout_l.addWidget(self.list_tasks_imp)
        
        w_right = QWidget(); layout_r = QVBoxLayout(w_right)
        layout_r.addWidget(QLabel("Available Published Caches (ABC/VDB/HIP):"))
        self.list_files_imp = QListWidget()
        layout_r.addWidget(self.list_files_imp)
        
        self.btn_import_cache = QPushButton("📥 Import Selected Cache")
        try: self.btn_import_cache.setStyleSheet(style.BTN_SUCCESS)
        except: pass
        self.btn_import_cache.clicked.connect(self.on_import_cache)
        layout_r.addWidget(self.btn_import_cache)
        
        splitter.addWidget(w_left); splitter.addWidget(w_right)
        layout.addWidget(splitter)
        self.refresh_importer_tasks()

    def refresh_importer_tasks(self):
        self.list_tasks_imp.clear()
        if not self.user_obj: return
        tasks = self.db.get_user_tasks(self.user_obj.id, include_done=True)
        for t in tasks:
            item = QListWidgetItem(f"{t[3]} | {t[4]}")
            item.setData(Qt.UserRole, t[0])
            self.list_tasks_imp.addItem(item)

    def on_task_clicked_importer(self, item):
        task_id = item.data(Qt.UserRole)
        self.list_files_imp.clear()
        context = self.db.get_task_context_data(task_id)
        if not context: return
        
        root = context['project_root']
        proj = context['project_name']
        entity_path = os.path.join(root, proj, "Assets", context['parent_name'], context['entity_name']).replace("\\", "/")
        
        safe_task = context['task_title'].replace(" ", "_")
        
        publish_3d = os.path.join(entity_path, "publish", "3D")
        if not os.path.exists(publish_3d): 
            publish_3d = os.path.join(entity_path, "publish", "3d")
            
        for folder_name in ["abc", "vdb"]:
            # حالا به جای اینکه فقط تو پوشه abc بگرده، میره تو abc/BODY
            folder = os.path.join(publish_3d, folder_name, safe_task).replace("\\", "/")
            if os.path.exists(folder):
                for f in os.listdir(folder):
                    if f.endswith(f".{folder_name}") and f.startswith(safe_task):
                        fi = QListWidgetItem(f"📦 CACHE: {f}")
                        fi.setData(Qt.UserRole, os.path.join(folder, f))
                        self.list_files_imp.addItem(fi)
                        
        mat_folder = os.path.join(publish_3d, "lookdev", safe_task).replace("\\", "/")
        if os.path.exists(mat_folder):
            for f in os.listdir(mat_folder):
                if (f.endswith(".hip") or f.endswith(".hipnc")) and (f.startswith(safe_task) or "material" in f.lower()):
                    fi = QListWidgetItem(f"💎 MAT LIBRARY: {f}")
                    fi.setData(Qt.UserRole, os.path.join(mat_folder, f))
                    fi.setForeground(QColor("#00bcd4"))
                    self.list_files_imp.addItem(fi)

    def on_import_cache(self):
        """ایجاد هوشمند نود بر اساس نوع فایل"""
        item = self.list_files_imp.currentItem()
        if not item: return
        path = item.data(Qt.UserRole).replace("\\", "/")
        
        try:
            name = os.path.basename(path).split(".")[0]
            obj = hou.node("/obj")
            
            if path.endswith(".abc"):
                container = obj.createNode("alembicarchive", f"ABC_{name}")
                container.parm("fileName").set(path)
                container.parm("buildHierarchy").pressButton()
                QMessageBox.information(self, "Success", "Alembic Archive created!")
                
            elif path.endswith(".vdb"):
                container = obj.createNode("geo", f"VDB_{name}")
                file_node = container.createNode("file")
                file_node.parm("file").set(path)
                QMessageBox.information(self, "Success", "VDB File Node created!")
                
            elif path.endswith(".hip"): # Material Library
                hou.hipFile.merge(path)
                QMessageBox.information(self, "Success", "Material Library Merged into /mat!")
                
            self.refresh_scene_manager()
        except Exception as e:
            QMessageBox.critical(self, "Import Error", str(e))

    # ==========================================
    # TAB 4: SHOT CONTENTS LOGIC
    # ==========================================
    def setup_shot_contents_tab(self):
        layout = QVBoxLayout(self.tab_shot_contents)
        self.lbl_shot_info = QLabel("<b>Current Shot:</b> None")
        layout.addWidget(self.lbl_shot_info)

        self.table_shot_assets = QTableWidget(0, 4)
        self.table_shot_assets.setHorizontalHeaderLabels(["Asset Name", "Category", "Status", "Action"])
        self.table_shot_assets.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_shot_assets)
        
        self.btn_assemble_all = QPushButton("🚀 ASSEMBLE ALL (Alembic Caches)")
        try: self.btn_assemble_all.setStyleSheet(style.BTN_SUCCESS)
        except: pass
        self.btn_assemble_all.clicked.connect(self.on_assemble_all)
        layout.addWidget(self.btn_assemble_all)

    def refresh_shot_contents(self):
        self.table_shot_assets.setRowCount(0)
        task_id = os.environ.get("CORTEX_TASK_ID")
        if not task_id: return

        context = self.db.get_task_context_data(task_id)
        if not context or context.get('type') != "Shot": return

        self.lbl_shot_info.setText(f"<b>Current Shot:</b> {context['parent_name']} / {context['entity_name']}")
        shot_id = context.get('entity_id') 
        
        if shot_id:
            linked_assets = self.db.get_shot_assets_extended(shot_id)
            for asset in linked_assets:
                # ریشه پوشه abc
                abc_root = os.path.join(asset[3], asset[4], "Assets", asset[2], asset[1], "publish", "3d", "abc").replace("\\", "/")
                
                has_caches = False
                if os.path.exists(abc_root):
                    # گشتن در تمام زیرپوشه‌ها (BODY, HEAD و...)
                    for task_folder in os.listdir(abc_root):
                        task_path = os.path.join(abc_root, task_folder).replace("\\", "/")
                        if os.path.isdir(task_path):
                            has_caches = True
                            row = self.table_shot_assets.rowCount()
                            self.table_shot_assets.insertRow(row)
                            
                            # نمایش نام اَسِت به همراه نام قطعه
                            self.table_shot_assets.setItem(row, 0, QTableWidgetItem(f"{asset[1]} ({task_folder})")) 
                            self.table_shot_assets.setItem(row, 1, QTableWidgetItem(asset[2])) 
                            
                            btn_load = QPushButton("📥 Load Alembic")
                            try: btn_load.setStyleSheet(style.BTN_CTX_XREF)
                            except: pass
                            btn_load.clicked.connect(lambda checked=False, p=task_path: self.load_latest_cache(p))
                            self.table_shot_assets.setCellWidget(row, 3, btn_load)
                
                if not has_caches:
                    row = self.table_shot_assets.rowCount()
                    self.table_shot_assets.insertRow(row)
                    self.table_shot_assets.setItem(row, 0, QTableWidgetItem(asset[1]))
                    self.table_shot_assets.setItem(row, 1, QTableWidgetItem(asset[2]))
                    self.table_shot_assets.setItem(row, 3, QTableWidgetItem("🚫 No Caches"))

    def load_latest_cache(self, folder_path):
        """پیدا کردن آخرین نسخه کش Alembic و لود آن در صحنه"""
        if not os.path.exists(folder_path):
            print(f">> [Cortex Warning] No caches found at: {folder_path}")
            return False

        files = [f for f in os.listdir(folder_path) if f.endswith(".abc")]
        if not files: return False
            
        files.sort()
        latest_file = os.path.join(folder_path, files[-1]).replace("\\", "/")

        try:
            name = os.path.basename(latest_file).split(".")[0]
            container = hou.node("/obj").createNode("alembicarchive", f"ASSET_{name}")
            container.parm("fileName").set(latest_file)
            container.parm("buildHierarchy").pressButton()
            self.refresh_scene_manager()
            return True
        except Exception as e:
            print(f"!! [Cortex Error] Failed to load cache: {e}")
            return False

    def on_assemble_all(self):
        task_id = os.environ.get("CORTEX_TASK_ID")
        context = self.db.get_task_context_data(task_id)
        if not context or context.get('type') != "Shot": return

        linked_assets = self.db.get_shot_assets_extended(context['entity_id'])
        count = 0
        for asset in linked_assets:
            abc_root = os.path.join(asset[3], asset[4], "Assets", asset[2], asset[1], "publish", "3d", "abc").replace("\\", "/")
            if os.path.exists(abc_root):
                for task_folder in os.listdir(abc_root):
                    task_path = os.path.join(abc_root, task_folder).replace("\\", "/")
                    if os.path.isdir(task_path):
                        if self.load_latest_cache(task_path):
                            count += 1
        
        QMessageBox.information(self, "Assemble Done", f"Successfully loaded {count} Asset Caches.")

    # ==========================================
    # SHARED HELPERS
    # ==========================================
    def load_my_tasks(self):
        self.list_tasks.clear()
        if not self.user_obj: return
        tasks = self.db.get_user_tasks(self.user_obj.id, include_done=True)
        for t in tasks:
            item = QListWidgetItem(f"{t[3]} | {t[4]} ({t[1]})")
            item.setData(Qt.UserRole, t[0])
            self.list_tasks.addItem(item)

    def on_task_clicked(self, item):
        task_id = item.data(Qt.UserRole)
        self.list_files.clear()
        self.lbl_preview.setText("Select File")
        context = self.db.get_task_context_data(task_id)
        if not context: return
        self.current_browsing_task_id = task_id 
        
        root = context['project_root']
        proj = context['project_name']
        entity_type_dir = "Assets" if context['type'] == 'Asset' else "Sequences"
        
        dept_name = "General"
        try:
            self.db.cursor.execute("SELECT d.name FROM tasks t JOIN departments d ON t.department_id=d.id WHERE t.id=?", (task_id,))
            res = self.db.cursor.fetchone()
            if res: dept_name = res[0]
        except: pass
        
        safe_dept = dept_name.replace(" ", "")
        safe_task = context['task_title'].replace(" ", "_")
        
        # اصلاح مسیر دقیقاً بر اساس ساختار لانچر شما
        # ساختار: work / 3D / Dept / software / Task
        path = os.path.join(root, proj, entity_type_dir, context['parent_name'], context['entity_name'], 
                            "work", "3D", safe_dept, "houdini", safe_task).replace("\\", "/")
        
        if os.path.exists(path):
            # پیدا کردن فایل‌های هودینی (hip و hipnc برای نسخه آموزشی)
            files = [f for f in os.listdir(path) if f.endswith(".hip") or f.endswith(".hipnc")]
            files.sort(reverse=True)
            for f in files:
                fi = QListWidgetItem(f)
                fi.setData(Qt.UserRole, os.path.join(path, f))
                self.list_files.addItem(fi)

    def on_file_clicked(self, item):
        path = item.data(Qt.UserRole)
        if path:
            jpg = path.rsplit(".", 1)[0] + ".jpg"
            if os.path.exists(jpg):
                pix = QPixmap(jpg)
                self.lbl_preview.setPixmap(pix.scaled(self.lbl_preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                self.lbl_preview.setText("No Preview")

    def get_selected_path(self):
        item = self.list_files.currentItem()
        return item.data(Qt.UserRole) if item else None

    def on_open(self):
        path = self.get_selected_path()
        if not path: return
        if hou.hipFile.hasUnsavedChanges():
            if QMessageBox.question(self, "Open", "Unsaved changes lost. Continue?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.No:
                return
        
        hou.hipFile.load(path)
        os.environ["CORTEX_TASK_ID"] = str(self.current_browsing_task_id)
        os.environ["CORTEX_WORK_PATH"] = os.path.dirname(path)
        os.environ["CORTEX_TASK_NAME"] = os.path.basename(os.path.dirname(path))
        self.accept()

    def on_merge(self):
        path = self.get_selected_path()
        if path:
            try:
                hou.hipFile.merge(path)
                QMessageBox.information(self, "Merged", "File merged successfully!")
                self.accept()
            except Exception as e: QMessageBox.critical(self, "Error", str(e))

def run():
    parent = hou.qt.mainWindow()
    win = LoaderWindow(parent)
    win.show()