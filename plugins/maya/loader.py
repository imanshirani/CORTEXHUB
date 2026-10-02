# Location: plugins/maya/loader.py
import os
import sys
import maya.cmds as cmds
import maya.mel as mel
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
                               QListWidgetItem, QLabel, QPushButton, QTabWidget, 
                               QWidget, QSplitter, QMessageBox, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QAbstractItemView)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QColor

# Path Fix
try:
    current_script_path = os.path.dirname(os.path.abspath(__file__))
    root_path = os.path.dirname(os.path.dirname(current_script_path))
    if root_path not in sys.path: sys.path.append(root_path)
except: pass

from app.core.database import DatabaseManager
import style

class MayaLoader(QDialog):
    def __init__(self, parent=None):
        super(MayaLoader, self).__init__(parent)
        self.setWindowTitle("Cortex Universal Tool | Maya")
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
    # TAB 1: LOADER LOGIC
    # ==========================================
    def setup_loader_tab(self):
        layout = QVBoxLayout(self.tab_loader)
        splitter = QSplitter(Qt.Horizontal)
        
        w1 = QWidget(); l1 = QVBoxLayout(w1)
        l1.addWidget(QLabel("Select Task:"))
        self.list_tasks = QListWidget()
        self.list_tasks.itemClicked.connect(self.on_task_clicked)
        l1.addWidget(self.list_tasks)
        
        w2 = QWidget(); l2 = QVBoxLayout(w2)
        l2.addWidget(QLabel("Select Version:"))
        self.list_files = QListWidget()
        self.list_files.itemClicked.connect(self.on_file_clicked)
        self.list_files.itemDoubleClicked.connect(self.on_open)
        l2.addWidget(self.list_files)
        
        w3 = QWidget(); l3 = QVBoxLayout(w3)
        self.lbl_preview = QLabel("Select a file")
        self.lbl_preview.setFixedSize(300, 180)
        try: self.lbl_preview.setStyleSheet(style.LBL_THUMBNAIL)
        except: pass
        self.lbl_preview.setAlignment(Qt.AlignCenter)
        self.lbl_preview.setScaledContents(True)
        l3.addWidget(self.lbl_preview)
        
        self.btn_open = QPushButton("📂 OPEN SCENE")
        try: self.btn_open.setStyleSheet(style.BTN_SUCCESS)
        except: pass
        self.btn_open.clicked.connect(self.on_open)
        l3.addWidget(self.btn_open)
        
        self.btn_import_work = QPushButton("📥 IMPORT SCENE")
        try: self.btn_import_work.setStyleSheet(style.BTN_CTX_LOADER)
        except: pass
        self.btn_import_work.clicked.connect(self.on_import_work)
        l3.addWidget(self.btn_import_work)
        l3.addStretch()
        
        splitter.addWidget(w1); splitter.addWidget(w2); splitter.addWidget(w3)
        layout.addWidget(splitter)

    # ==========================================
    # TAB 2: SCENE MANAGER LOGIC
    # ==========================================
    def setup_manager_tab(self):
        layout = QVBoxLayout(self.tab_manager)
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("<b>Referenced Files (Maya/Alembic):</b>"))
        top_bar.addStretch()
        btn_refresh = QPushButton("↻ Refresh List")
        btn_refresh.clicked.connect(self.refresh_scene_manager)
        top_bar.addWidget(btn_refresh)
        layout.addLayout(top_bar)
        
        self.table_refs = QTableWidget(0, 5)
        self.table_refs.setHorizontalHeaderLabels(["Namespace/Node", "Current Ver", "Latest Ver", "Status", "Action"])
        self.table_refs.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_refs.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.table_refs)

    def refresh_scene_manager(self):
        """اسکن صحنه مایا برای پیدا کردن رفرنس‌ها و نودهای المبیک"""
        self.table_refs.setRowCount(0)
        
        # بررسی Reference های مایا
        refs = cmds.ls(type="reference")
        for ref_node in refs:
            if "sharedReferenceNode" in ref_node or "_UNKNOWN_" in ref_node: continue
            try:
                filepath = cmds.referenceQuery(ref_node, filename=True, withoutCopyNumber=True)
                namespace = cmds.referenceQuery(ref_node, namespace=True)
                self.add_manager_row(ref_node, filepath, namespace, is_reference=True)
            except: pass

    def add_manager_row(self, node_name, filepath, display_name, is_reference=False):
        import re
        if not filepath or not os.path.exists(filepath): return
        
        filename = os.path.basename(filepath)
        folder = os.path.dirname(filepath)
        
        match = re.search(r"_v(\d{3})", filename)
        if not match: return
            
        current_ver = int(match.group(1))
        prefix = filename.split(f"_v{match.group(1)}")[0]
        
        latest_ver = current_ver
        if os.path.exists(folder):
            for f in os.listdir(folder):
                if f.startswith(prefix) and "_v" in f and f.endswith(filename[-4:]):
                    try:
                        v = int(f.split("_v")[-1].split(".")[0])
                        if v > latest_ver: latest_ver = v
                    except: pass
        
        is_outdated = latest_ver > current_ver
        row = self.table_refs.rowCount()
        self.table_refs.insertRow(row)
        
        self.table_refs.setItem(row, 0, QTableWidgetItem(f"{display_name} ({filename})"))
        self.table_refs.setItem(row, 1, QTableWidgetItem(f"v{current_ver:03d}"))
        
        item_lat = QTableWidgetItem(f"v{latest_ver:03d}")
        item_lat.setForeground(QColor("#ff5555") if is_outdated else QColor("#55ff55"))
        self.table_refs.setItem(row, 2, item_lat)
        self.table_refs.setItem(row, 3, QTableWidgetItem("⚠️ Outdated" if is_outdated else "✅ OK"))
        
        if is_outdated:
            btn_update = QPushButton("🚀 Update")
            new_filename = filename.replace(f"v{current_ver:03d}", f"v{latest_ver:03d}")
            new_path = os.path.join(folder, new_filename).replace("\\", "/")
            if is_reference:
                btn_update.clicked.connect(lambda _, rn=node_name, np=new_path: self.update_maya_reference(rn, np))
            self.table_refs.setCellWidget(row, 4, btn_update)
        else:
            self.table_refs.setItem(row, 4, QTableWidgetItem("-"))

    def update_maya_reference(self, ref_node, new_path):
        try:
            cmds.file(new_path, loadReference=ref_node)
            QMessageBox.information(self, "Updated", "Reference updated successfully!")
            self.refresh_scene_manager()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    # ==========================================
    # TAB 3: IMPORTER LOGIC
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
        layout_r.addWidget(QLabel("Available Published Caches (ABC/FBX/MA):"))
        self.list_files_imp = QListWidget()
        layout_r.addWidget(self.list_files_imp)
        
        actions = QHBoxLayout()
        self.btn_ref_cache = QPushButton("🔗 Create Reference")
        try: self.btn_ref_cache.setStyleSheet(style.BTN_SUCCESS)
        except: pass
        self.btn_ref_cache.clicked.connect(self.on_import_cache_reference)
        actions.addWidget(self.btn_ref_cache)
        
        self.btn_imp_cache = QPushButton("📥 Import into Scene")
        self.btn_imp_cache.clicked.connect(self.on_import_cache_merge)
        actions.addWidget(self.btn_imp_cache)
        
        layout_r.addLayout(actions)
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
        if not os.path.exists(publish_3d): publish_3d = os.path.join(entity_path, "publish", "3d")
        
        for folder_name in ["obj", "abc", "maya"]:
            folder = os.path.join(publish_3d, folder_name, safe_task).replace("\\", "/")
            if os.path.exists(folder):
                for f in os.listdir(folder):
                    if f.endswith((".fbx", ".abc", ".ma", ".mb")) and f.startswith(safe_task):
                        fi = QListWidgetItem(f"📦 CACHE: {f}")
                        fi.setData(Qt.UserRole, os.path.join(folder, f))
                        self.list_files_imp.addItem(fi)
                        
        mat_folder = os.path.join(publish_3d, "lookdev", safe_task).replace("\\", "/")
        if os.path.exists(mat_folder):
            for f in os.listdir(mat_folder):
                if f.endswith((".ma", ".mb")) and f.startswith("mat_lib"):
                    fi = QListWidgetItem(f"💎 MATERIAL: {f}")
                    fi.setData(Qt.UserRole, os.path.join(mat_folder, f))
                    fi.setForeground(QColor("#00bcd4"))
                    self.list_files_imp.addItem(fi)

    def on_import_cache_reference(self):
        item = self.list_files_imp.currentItem()
        if not item: return
        path = item.data(Qt.UserRole).replace("\\", "/")
        name = os.path.basename(path).split(".")[0]
        try:
            cmds.file(path, reference=True, namespace=name, groupReference=True, groupName=f"GRP_{name}")
            QMessageBox.information(self, "Success", "File Referenced Successfully!")
            self.refresh_scene_manager()
        except Exception as e:
            QMessageBox.critical(self, "Import Error", str(e))

    def on_import_cache_merge(self):
        item = self.list_files_imp.currentItem()
        if not item: return
        path = item.data(Qt.UserRole).replace("\\", "/")
        try:
            if path.endswith(".abc"):
                if not cmds.pluginInfo("AbcImport", q=True, loaded=True): cmds.loadPlugin("AbcImport")
                cmds.file(path, i=True, type="Alembic")
            elif path.endswith(".fbx"):
                if not cmds.pluginInfo("fbxmaya", q=True, loaded=True): cmds.loadPlugin("fbxmaya")
                cmds.file(path, i=True, type="FBX")
            else:
                cmds.file(path, i=True)
            QMessageBox.information(self, "Success", "File Imported Successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Import Error", str(e))

    # ==========================================
    # TAB 4: SHOT CONTENTS (ASSEMBLY)
    # ==========================================
    def setup_shot_contents_tab(self):
        layout = QVBoxLayout(self.tab_shot_contents)
        self.lbl_shot_info = QLabel("<b>Current Shot:</b> None")
        layout.addWidget(self.lbl_shot_info)

        self.table_shot_assets = QTableWidget(0, 4)
        self.table_shot_assets.setHorizontalHeaderLabels(["Asset Name", "Category", "Status", "Action"])
        self.table_shot_assets.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_shot_assets)
        
        self.btn_assemble_all = QPushButton("🚀 ASSEMBLE ALL (Maya References)")
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
                # اولویت لود در شات: فایل‌های پابلیش شده مایا
                maya_root = os.path.join(asset[3], asset[4], "Assets", asset[2], asset[1], "publish", "3d", "maya").replace("\\", "/")
                
                has_publishes = False
                if os.path.exists(maya_root):
                    for task_folder in os.listdir(maya_root):
                        task_path = os.path.join(maya_root, task_folder).replace("\\", "/")
                        if os.path.isdir(task_path):
                            has_publishes = True
                            row = self.table_shot_assets.rowCount()
                            self.table_shot_assets.insertRow(row)
                            
                            self.table_shot_assets.setItem(row, 0, QTableWidgetItem(f"{asset[1]} ({task_folder})")) 
                            self.table_shot_assets.setItem(row, 1, QTableWidgetItem(asset[2])) 
                            
                            btn_ref = QPushButton("🔗 Reference")
                            try: btn_ref.setStyleSheet(style.BTN_CTX_XREF)
                            except: pass
                            btn_ref.clicked.connect(lambda checked=False, p=task_path: self.reference_latest_from_path(p))
                            self.table_shot_assets.setCellWidget(row, 3, btn_ref)
                            
                if not has_publishes:
                    row = self.table_shot_assets.rowCount()
                    self.table_shot_assets.insertRow(row)
                    self.table_shot_assets.setItem(row, 0, QTableWidgetItem(asset[1]))
                    self.table_shot_assets.setItem(row, 1, QTableWidgetItem(asset[2]))
                    self.table_shot_assets.setItem(row, 3, QTableWidgetItem("🚫 No Publishes"))

    def reference_latest_from_path(self, folder_path):
        if not os.path.exists(folder_path): return False
        files = [f for f in os.listdir(folder_path) if f.endswith((".ma", ".mb", ".abc"))]
        if not files: return False
            
        files.sort()
        latest_file = os.path.join(folder_path, files[-1]).replace("\\", "/")
        name = os.path.basename(latest_file).split(".")[0]

        try:
            cmds.file(latest_file, reference=True, namespace=name)
            self.refresh_scene_manager()
            return True
        except Exception as e:
            print(f"!! [Cortex] Failed to reference: {e}")
            return False

    def on_assemble_all(self):
        task_id = os.environ.get("CORTEX_TASK_ID")
        context = self.db.get_task_context_data(task_id)
        if not context or context.get('type') != "Shot": return

        linked_assets = self.db.get_shot_assets_extended(context['entity_id'])
        count = 0
        for asset in linked_assets:
            maya_root = os.path.join(asset[3], asset[4], "Assets", asset[2], asset[1], "publish", "3d", "maya").replace("\\", "/")
            if os.path.exists(maya_root):
                for task_folder in os.listdir(maya_root):
                    task_path = os.path.join(maya_root, task_folder).replace("\\", "/")
                    if os.path.isdir(task_path):
                        if self.reference_latest_from_path(task_path):
                            count += 1
        QMessageBox.information(self, "Assemble Done", f"Successfully referenced {count} assets.")

    # ==========================================
    # SHARED HELPERS (WORK FILES)
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
        
        # مسیر ورک مایا
        path = os.path.join(root, proj, entity_type_dir, context['parent_name'], context['entity_name'], 
                            "Work", "3D", safe_dept, "maya", safe_task).replace("\\", "/")
        
        if os.path.exists(path):
            files = [f for f in os.listdir(path) if f.endswith((".ma", ".mb"))]
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
                self.lbl_preview.setPixmap(QPixmap(jpg).scaled(self.lbl_preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                self.lbl_preview.setText("No Preview")

    def get_selected_path(self):
        item = self.list_files.currentItem()
        return item.data(Qt.UserRole) if item else None

    def on_open(self):
        path = self.get_selected_path()
        if not path: return
        
        # چک کردن فایل سیو نشده در مایا
        if cmds.file(q=True, modified=True):
            if QMessageBox.question(self, "Open", "Unsaved changes will be lost. Continue?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.No:
                return
        
        cmds.file(path, open=True, force=True)
        os.environ["CORTEX_TASK_ID"] = str(self.current_browsing_task_id)
        os.environ["CORTEX_WORK_PATH"] = os.path.dirname(path)
        os.environ["CORTEX_TASK_NAME"] = os.path.basename(os.path.dirname(path))
        self.accept()

    def on_import_work(self):
        path = self.get_selected_path()
        if path:
            try:
                cmds.file(path, i=True, force=True)
                QMessageBox.information(self, "Imported", "File imported successfully!")
                self.accept()
            except Exception as e: QMessageBox.critical(self, "Error", str(e))

def run():
    # پیدا کردن پنجره اصلی مایا به عنوان Parent
    import maya.OpenMayaUI as omui   # <--- کلمه .api از اینجا حذف شد
    from shiboken6 import wrapInstance
    
    maya_main_window_ptr = omui.MQtUtil.mainWindow()
    parent = wrapInstance(int(maya_main_window_ptr), QWidget)
    
    win = MayaLoader(parent)
    win.show()