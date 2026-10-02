import os
import sys
import re
import pymxs
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

rt = pymxs.runtime

class LoaderWindow(QDialog):
    def __init__(self, parent=None):
        """
        Handle   Init   operation.
        """
        super(LoaderWindow, self).__init__(parent)
        self.setWindowTitle("Cortex Universal Tool")
        self.resize(1100, 650)
        self.setStyleSheet(style.PUBLISH_DIALOG)
        
        self.db = DatabaseManager()
        self.current_user = os.environ.get("CORTEX_USER", "admin")
        self.user_obj = self.db.get_user_by_username(self.current_user)
        
        self.init_ui()
        self.load_my_tasks()
        self.refresh_scene_manager() # Initial scene check
        self.refresh_shot_contents()

    def init_ui(self):
        """
        Handle Init Ui operation.
        """
        main_layout = QVBoxLayout(self)
        
        # --- Tabs ---
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Tab 1: Loader (previous code)
        self.tab_loader = QWidget()
        self.setup_loader_tab()
        self.tabs.addTab(self.tab_loader, "📂 Loader")
        
        # Tab 2: Scene Manager (new)
        self.tab_manager = QWidget()
        self.setup_manager_tab()
        self.tabs.addTab(self.tab_manager, "♻️ Scene Manager")
        
        # Tab 3: Importer
        self.tab_importer = QWidget()
        self.setup_importer_tab()
        self.tabs.addTab(self.tab_importer, "📥 Importer (Cross-App)")

        # Tab 4: Shot Contents
        self.tab_shot_contents = QWidget()
        self.setup_shot_contents_tab()
        self.tabs.addTab(self.tab_shot_contents, "🎬 Shot Contents")

    # ==========================================
    # TAB 1: LOADER LOGIC
    # ==========================================
    def setup_loader_tab(self):
        """
        Handle Setup Loader Tab operation.
        """
        layout = QVBoxLayout(self.tab_loader)
        
        splitter = QSplitter(Qt.Horizontal)
        
        # Col 1: Tasks
        w1 = QWidget()
        l1 = QVBoxLayout(w1)
        l1.addWidget(QLabel("Select Task:"))
        self.list_tasks = QListWidget()
        self.list_tasks.itemClicked.connect(self.on_task_clicked)
        l1.addWidget(self.list_tasks)
        
        # Col 2: Files
        w2 = QWidget()
        l2 = QVBoxLayout(w2)
        l2.addWidget(QLabel("Select Version:"))
        self.list_files = QListWidget()
        self.list_files.itemClicked.connect(self.on_file_clicked)
        self.list_files.itemDoubleClicked.connect(self.on_open)
        l2.addWidget(self.list_files)
        
        # Col 3: Actions
        w3 = QWidget()
        l3 = QVBoxLayout(w3)
        l3.setSpacing(10)
        
        self.lbl_preview = QLabel("Select a file")
        self.lbl_preview.setFixedSize(300, 180)
        self.lbl_preview.setStyleSheet(style.LBL_THUMBNAIL)
        self.lbl_preview.setAlignment(Qt.AlignCenter)
        self.lbl_preview.setScaledContents(True)
        l3.addWidget(self.lbl_preview)
        
        l3.addWidget(QLabel("<b>Actions:</b>"))
        
        self.btn_open = QPushButton("📂 OPEN SCENE")
        self.btn_open.setStyleSheet(style.BTN_SUCCESS)
        self.btn_open.clicked.connect(self.on_open)
        l3.addWidget(self.btn_open)
        
        self.btn_merge = QPushButton("➕ MERGE (Lookdev)")
        self.btn_merge.setStyleSheet(style.BTN_CTX_LOADER)
        self.btn_merge.clicked.connect(self.on_merge)
        l3.addWidget(self.btn_merge)
        
        self.btn_xref = QPushButton("🔗 XREF SCENE (Stage)")
        self.btn_xref.setToolTip("Link file as overlay (For Layout/Animation)")
        self.btn_xref.setStyleSheet(style.BTN_CTX_XREF)
        self.btn_xref.clicked.connect(self.on_xref)
        l3.addWidget(self.btn_xref)
        
        l3.addStretch()
        
        splitter.addWidget(w1); splitter.addWidget(w2); splitter.addWidget(w3)
        splitter.setStretchFactor(0, 1); splitter.setStretchFactor(1, 1); splitter.setStretchFactor(2, 0)
        layout.addWidget(splitter)

    # ==========================================
    # TAB 2: SCENE MANAGER LOGIC (NEW)
    # ==========================================
    def setup_manager_tab(self):
        """
        Handle Setup Manager Tab operation.
        """
        layout = QVBoxLayout(self.tab_manager)
        
        # Header with Refresh
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("<b>Managed Assets (XRefs):</b>"))
        top_bar.addStretch()
        btn_refresh_man = QPushButton("↻ Refresh List")
        btn_refresh_man.setStyleSheet(style.BTN_TOOLBAR)
        btn_refresh_man.clicked.connect(self.refresh_scene_manager)
        top_bar.addWidget(btn_refresh_man)
        layout.addLayout(top_bar)
        
        # Table
        self.table_refs = QTableWidget()
        self.table_refs.setColumnCount(5)
        self.table_refs.setHorizontalHeaderLabels(["Asset Name", "Current Ver", "Latest Ver", "Status", "Action"])
        self.table_refs.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_refs.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_refs.setStyleSheet(style.TABLE_MANAGER)
        layout.addWidget(self.table_refs)

    def refresh_scene_manager(self):
        """Scan the scene for XRefs and check for updates"""
        self.table_refs.setRowCount(0)
        
        # 1. XRef count from Max
        xref_count = rt.xrefs.getXRefFileCount()
        for i in range(1, xref_count + 1):
            # MaxScript indexes start at 1
            file_path = rt.xrefs.getXRefFile(i).filename
            filename = os.path.basename(file_path)
            folder = os.path.dirname(file_path)
            
            # 2. Parse the filename (Body_v001.max)
            # Regex for vXXX
            match = re.search(r"_v(\d{3})", filename)
            
            asset_name = filename
            current_ver = 0
            latest_ver = 0
            status = "Unknown"
            
            if match:
                ver_str = match.group(1)
                current_ver = int(ver_str)
                prefix = filename.split(f"_v{ver_str}")[0] # Body
                
                # 3. Look in the folder for a newer version
                if os.path.exists(folder):
                    files = os.listdir(folder)
                    max_v = current_ver
                    for f in files:
                        if f.startswith(prefix) and f.endswith(".max") and "_v" in f:
                            try:
                                v = int(f.split("_v")[-1].split(".")[0])
                                if v > max_v: max_v = v
                            except: pass
                    latest_ver = max_v
            
            # 4. Set status
            is_outdated = latest_ver > current_ver
            
            # 5. Fill the table
            row = self.table_refs.rowCount()
            self.table_refs.insertRow(row)
            
            self.table_refs.setItem(row, 0, QTableWidgetItem(filename))
            self.table_refs.setItem(row, 1, QTableWidgetItem(f"v{current_ver:03d}"))
            
            # Latest
            item_lat = QTableWidgetItem(f"v{latest_ver:03d}")
            if is_outdated:
                item_lat.setForeground(QColor("#ff5555")) # red
            else:
                item_lat.setForeground(QColor("#55ff55")) # green
            self.table_refs.setItem(row, 2, item_lat)
            
            # Status
            status_text = "⚠️ Outdated" if is_outdated else "✅ OK"
            self.table_refs.setItem(row, 3, QTableWidgetItem(status_text))
            
            # Action Button
            if is_outdated:
                btn_update = QPushButton("🚀 Update")
                btn_update.setStyleSheet(style.BTN_UPDATE)
                # Store the Max index and new path on the button
                new_filename = filename.replace(f"v{current_ver:03d}", f"v{latest_ver:03d}")
                new_full_path = os.path.join(folder, new_filename)
                # Pass checked into the lambda to avoid TypeError
                btn_update.clicked.connect(lambda checked=False, idx=i, path=new_full_path: self.do_update_xref(idx, path))
                self.table_refs.setCellWidget(row, 4, btn_update)
            else:
                self.table_refs.setItem(row, 4, QTableWidgetItem("-"))

        for obj in rt.objects:
            mat_path = rt.getUserProp(obj, "Cortex_Mat_Source")
            if mat_path and os.path.exists(mat_path):
                mat_name = rt.getUserProp(obj, "Cortex_Mat_Name")
                self.add_material_row_to_manager(obj, mat_name, mat_path)


    def add_material_row_to_manager(self, obj, mat_name, current_path):
        """
        Handle Add Material Row To Manager operation.
        """
        # Check the folder for a newer version
        folder = os.path.dirname(current_path)
        # Native materials usually keep a fixed name,
        # but if .mat files are versioned, that is checked here
        
        row = self.table_refs.rowCount()
        self.table_refs.insertRow(row)
        
        self.table_refs.setItem(row, 0, QTableWidgetItem(f"🎨 {obj.name} ({mat_name})"))
        self.table_refs.setItem(row, 1, QTableWidgetItem("Native Mat"))
        self.table_refs.setItem(row, 3, QTableWidgetItem("✅ Linked"))
        
        # Re-Apply button to refresh a material if the file on disk changed
        btn_reapply = QPushButton("🔄 Re-Apply")
        btn_reapply.setStyleSheet(style.BTN_UPDATE)
        btn_reapply.clicked.connect(lambda: self.reapply_single_material(obj, current_path, mat_name))
        self.table_refs.setCellWidget(row, 4, btn_reapply)

    def do_update_xref(self, xref_index, new_path):
        """Run the update in Max with the fixed method"""
        try:
            # 1. Get the XRef (Max indexes start at 1)
            xref_entry = rt.xrefs.getXRefFile(xref_index)
            
            # 2. Point the file path at the new version
            xref_entry.filename = new_path
            
            # 3. Refresh the scene
            # Use this instead of rt.xrefs.updateChangedXRefFiles:
            pymxs.runtime.xrefs.updateChangedXRefs()
            
            
            # If the line above still errors, use this fallback:
            # rt.execute("xrefs.updateChangedXRefFiles()")
            
            QMessageBox.information(self, "Updated", f"Updated to: {os.path.basename(new_path)}")
            self.refresh_scene_manager()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Update Failed: {str(e)}")

    # ==========================================
    # TAB 3: IMPORTER (PLACEHOLDER)
    # ==========================================
    def setup_importer_tab(self):
        """
        Handle Setup Importer Tab operation.
        """
        layout = QVBoxLayout(self.tab_importer)
        
        # --- Tabs are disabled for now so the splitter works ---
        # Functions like setup_geo_sub_tab are not defined yet and would crash
        
        splitter = QSplitter(Qt.Horizontal)
        
        # Left: task list
        self.list_tasks_imp = QListWidget()
        self.list_tasks_imp.itemClicked.connect(self.on_task_clicked_importer)
        layout_l = QVBoxLayout()
        layout_l.addWidget(QLabel("Select Source Task:"))
        layout_l.addWidget(self.list_tasks_imp)
        w_left = QWidget(); w_left.setLayout(layout_l)
        
        # Right: file list
        self.list_files_imp = QListWidget()
        layout_r = QVBoxLayout()
        layout_r.addWidget(QLabel("Available Interchange Files (FBX/ABC/MAT):"))
        layout_r.addWidget(self.list_files_imp)
        
        # Existing import button
        self.btn_import_fbx = QPushButton("📥 Import FBX/ABC to Scene")
        self.btn_import_fbx.setStyleSheet(style.BTN_SUCCESS)
        self.btn_import_fbx.clicked.connect(self.on_import_fbx)
        layout_r.addWidget(self.btn_import_fbx)

        # --- New material button (this is the only addition) ---
        self.btn_assign_mat = QPushButton("🎨 ASSIGN NATIVE MATERIALS")
        self.btn_assign_mat.setStyleSheet(style.BTN_CTX_LOOKDEV)
        self.btn_assign_mat.clicked.connect(self.on_assign_materials) 
        layout_r.addWidget(self.btn_assign_mat)
        
        w_right = QWidget(); w_right.setLayout(layout_r)
        
        splitter.addWidget(w_left)
        splitter.addWidget(w_right)
        layout.addWidget(splitter)
        
        self.refresh_importer_tasks()


    # ==========================================
    # Tab 4: Shot Contents
    # ==========================================

    def setup_shot_contents_tab(self):
        """
        Handle Setup Shot Contents Tab operation.
        """
        layout = QVBoxLayout(self.tab_shot_contents)
        
        self.lbl_shot_info = QLabel("<b>Current Shot:</b> None")
        self.lbl_shot_info.setStyleSheet("color: #007acc; font-size: 14px;")
        layout.addWidget(self.lbl_shot_info)

        self.table_shot_assets = QTableWidget()
        self.table_shot_assets.setColumnCount(4)
        self.table_shot_assets.setHorizontalHeaderLabels(["Asset Name", "Category", "Status", "Action"])
        self.table_shot_assets.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_shot_assets.setStyleSheet(style.TABLE_MANAGER)
        layout.addWidget(self.table_shot_assets)
        
        self.btn_assemble_all = QPushButton("🚀 ASSEMBLE ALL ASSETS (XREF)")
        self.btn_assemble_all.setStyleSheet(style.BTN_SUCCESS)
        self.btn_assemble_all.setFixedHeight(40)
        layout.addWidget(self.btn_assemble_all)

    def refresh_shot_contents(self):
        """Show assets linked to the open shot in Max"""
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
                # Root of the max folder
                max_root = os.path.join(asset[3], asset[4], "Assets", asset[2], asset[1], "publish", "3d", "max").replace("\\", "/")
                
                has_caches = False
                if os.path.exists(max_root):
                    # Walk subfolders (BODY, HEAD, ...)
                    for task_folder in os.listdir(max_root):
                        task_path = os.path.join(max_root, task_folder).replace("\\", "/")
                        if os.path.isdir(task_path):
                            has_caches = True
                            row = self.table_shot_assets.rowCount()
                            self.table_shot_assets.insertRow(row)
                            
                            self.table_shot_assets.setItem(row, 0, QTableWidgetItem(f"{asset[1]} ({task_folder})")) 
                            self.table_shot_assets.setItem(row, 1, QTableWidgetItem(asset[2])) 
                            
                            btn_xref = QPushButton("🔗 XRef Latest")
                            btn_xref.setStyleSheet(style.BTN_CTX_XREF)
                            btn_xref.clicked.connect(lambda checked=False, p=task_path: self.xref_latest_from_path(p))
                            self.table_shot_assets.setCellWidget(row, 3, btn_xref)
                            
                if not has_caches:
                    row = self.table_shot_assets.rowCount()
                    self.table_shot_assets.insertRow(row)
                    self.table_shot_assets.setItem(row, 0, QTableWidgetItem(asset[1]))
                    self.table_shot_assets.setItem(row, 1, QTableWidgetItem(asset[2]))
                    self.table_shot_assets.setItem(row, 3, QTableWidgetItem("🚫 No Publishes"))


    # ==========================================
    # SHARED LOGIC (LOADER)
    # ==========================================

    def on_import_interchange(self):
        """Smart FBX or Alembic import into Max"""
        item = self.list_files_imp.currentItem()
        if not item: return
        path = item.data(Qt.UserRole)
        
        try:
            if path.endswith(".fbx"):
                rt.FBXImporterSetParam("ScaleConversion", True)
                rt.importFile(path, rt.Name("noPrompt"), using=rt.FBXIMP)
            
            elif path.endswith(".abc"):
                # Alembic import in Max
                # Import brings the object in with an Alembic Mesh modifier
                rt.importFile(path, rt.Name("noPrompt"), using=rt.Alembic_Import)
                
            QMessageBox.information(self, "Success", f"Imported: {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.critical(self, "Import Error", str(e))
            
    def refresh_importer_tasks(self):
        """
        Handle Refresh Importer Tasks operation.
        """
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
        
        # 1. Scan folders including the task subfolder
        for folder_name in ["obj", "abc", "vdb"]:
            folder = os.path.join(publish_3d, folder_name, safe_task).replace("\\", "/")
            if os.path.exists(folder):
                for f in os.listdir(folder):
                    if f.endswith((".fbx", ".abc", ".vdb")) and f.startswith(safe_task):
                        fi = QListWidgetItem(f"📦 CACHE: {f}")
                        fi.setData(Qt.UserRole, os.path.join(folder, f))
                        self.list_files_imp.addItem(fi)

        # 2. Add material paths from the task subfolder
        mat_folder = os.path.join(publish_3d, "lookdev", safe_task).replace("\\", "/")
        if not os.path.exists(mat_folder): 
            mat_folder = os.path.join(publish_3d, "lookdev", "materials").replace("\\", "/")
            
        if os.path.exists(mat_folder):
            for f in os.listdir(mat_folder):
                if f.endswith(".mat") and (f.startswith(safe_task) or "material" in f.lower()):
                    fi = QListWidgetItem(f"💎 MATERIAL: {f}")
                    fi.setData(Qt.UserRole, os.path.join(mat_folder, f))
                    fi.setForeground(QColor("#00bcd4")) 
                    self.list_files_imp.addItem(fi)

    def on_import_fbx(self):
        """Smart FBX import into Max"""
        item = self.list_files_imp.currentItem()
        if not item: return
        path = item.data(Qt.UserRole)
        if not path or not os.path.exists(path): return

        try:
            # Max FBX importer settings to match Blender
            # Blender is usually Z-up; Max is Z-up too but conversion can flip to Y-up
            rt.FBXImporterSetParam("ScaleConversion", True)
            rt.FBXImporterSetParam("UpAxis", "Z") 
            rt.FBXImporterSetParam("FileUnits", "Centimeters")
            
            # Import without opening the options dialog (faster)
            rt.importFile(path, rt.Name("noPrompt"), using=rt.FBXIMP)
            
            QMessageBox.information(self, "Success", f"Imported: {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.critical(self, "Import Error", str(e))

    
    def load_my_tasks(self):
        """
        Handle Load My Tasks operation.
        """
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
        
        # Path follows Work / 3D / Dept / max / Task
        path = os.path.join(root, proj, entity_type_dir, context['parent_name'], context['entity_name'], 
                            "Work", "3D", safe_dept, "max", safe_task).replace("\\", "/")
        
        if os.path.exists(path):
            files = [f for f in os.listdir(path) if f.endswith(".max")]
            files.sort(reverse=True)
            for f in files:
                fi = QListWidgetItem(f)
                fi.setData(Qt.UserRole, os.path.join(path, f))
                self.list_files.addItem(fi)

    def on_file_clicked(self, item):
        """
        Handle On File Clicked operation.
        """
        path = item.data(Qt.UserRole)
        if path:
            jpg = path.replace(".max", ".jpg")
            if os.path.exists(jpg):
                pix = QPixmap(jpg)
                self.lbl_preview.setPixmap(pix.scaled(self.lbl_preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                self.lbl_preview.setText("No Preview")

    def get_selected_path(self):
        """
        Handle Get Selected Path operation.
        """
        item = self.list_files.currentItem()
        return item.data(Qt.UserRole) if item else None

    def on_open(self):
        """
        Handle On Open operation.
        """
        path = self.get_selected_path()
        if not path: return
        if QMessageBox.question(self, "Open", "Unsaved changes lost. Continue?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            rt.loadMaxFile(path)
            os.environ["CORTEX_TASK_ID"] = str(self.current_browsing_task_id)
            os.environ["CORTEX_WORK_PATH"] = os.path.dirname(path)
            os.environ["CORTEX_TASK_NAME"] = os.path.basename(os.path.dirname(path))
            self.accept()
            try: import cortex_ui; cortex_ui.show_ui() 
            except: pass

    def on_merge(self):
        """
        Handle On Merge operation.
        """
        path = self.get_selected_path()
        if path:
            try:
                rt.mergeMaxFile(path, rt.Name("mergeDups"), rt.Name("useSceneMtlDups"))
                QMessageBox.information(self, "Merged", "File merged!")
                self.accept()
            except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def on_xref(self):
        """
        Handle On Xref operation.
        """
        path = self.get_selected_path()
        if path:
            try:
                rt.xrefs.addNewXRefFile(path)
                QMessageBox.information(self, "XRef", "Scene XRef added!")
                self.accept()
                self.refresh_scene_manager() # Auto refresh manager
            except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def on_assign_materials(self):
        """Load a material library and assign by name"""
        item = self.list_files_imp.currentItem()
        if not item or not item.text().startswith("💎"): 
            QMessageBox.warning(self, "Warning", "Please select a MATERIAL file.")
            return
            
        mat_path = item.data(Qt.UserRole)
        
        try:
            temp_lib = rt.loadTempMaterialLibrary(mat_path)
            assign_count = 0
            for m in temp_lib:
                clean_name = m.name.replace("PBR_", "")
                obj = rt.getNodeByName(clean_name)
                
                if obj:
                    obj.material = m
                    # Store the file path on the object AppData for later
                    rt.setUserProp(obj, "Cortex_Mat_Source", mat_path)
                    rt.setUserProp(obj, "Cortex_Mat_Name", m.name)
                    assign_count += 1
            
            QMessageBox.information(self, "Success", f"Assigned {assign_count} materials to objects!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Assignment Failed: {e}")


    def xref_latest_from_path(self, asset_3d_path):
        """Find the latest published version and bring it in as an XRef"""
        # 1. Check that 3d/max exists on disk
        if not os.path.exists(asset_3d_path):
            print(f">> [Cortex Error] Path not found: {asset_3d_path}")
            return

        # 2. List all Max files
        files = [f for f in os.listdir(asset_3d_path) if f.endswith(".max")]
        
        if not files:
            print(f">> [Cortex Warning] No .max files found in: {asset_3d_path}")
            return
            
        # 3. Sort so the last vXXX is at the end of the list
        files.sort()
        latest_filename = files[-1] # Last item in the list
        full_path = os.path.join(asset_3d_path, latest_filename).replace("\\", "/")

        try:
            # 4. XRef command in Max
            print(f">> [Cortex] Attempting to XRef: {latest_filename}")
            rt.xrefs.addNewXRefFile(full_path)
            
            # 5. Refresh the manager table so the new file appears
            self.refresh_scene_manager() 
        except Exception as e:
            print(f"!! [Cortex] XRef Failed for {latest_filename}: {e}")

    def on_assemble_all(self):
        """Import every asset linked to the shot in one click"""
        task_id = os.environ.get("CORTEX_TASK_ID")
        context = self.db.get_task_context_data(task_id)
        if not context or context.get('type') != "Shot": return

        linked_assets = self.db.get_shot_assets_extended(context['entity_id'])
        count = 0
        for asset in linked_assets:
            max_root = os.path.join(asset[3], asset[4], "Assets", asset[2], asset[1], "publish", "3d", "max").replace("\\", "/")
            if os.path.exists(max_root):
                for task_folder in os.listdir(max_root):
                    task_path = os.path.join(max_root, task_folder).replace("\\", "/")
                    if os.path.isdir(task_path):
                        self.xref_latest_from_path(task_path)
                        count += 1
        
        QMessageBox.information(self, "Assemble Done", f"Successfully assembled {count} assets as XRefs.")

def run():
    """
    Handle Run operation.
    """
    try: import qtmax; parent = qtmax.GetQMaxMainWindow()
    except: parent = None
    win = LoaderWindow(parent)
    win.show()