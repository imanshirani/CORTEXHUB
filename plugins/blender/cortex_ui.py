# Location: plugins/blender/cortex_ui.py
import bpy
import os
import sys

# =========================================================
# 1. PATH FIX (must stay on the first lines)
# =========================================================
try:
    # Directory of this file (plugins/blender)
    current_folder = os.path.dirname(os.path.abspath(__file__))
    
    # Project root (two levels up: plugins -> Cortex_Pipeline)
    root_folder = os.path.dirname(os.path.dirname(current_folder))
    
    # Add to sys.path if missing
    if root_folder not in sys.path:
        sys.path.append(root_folder)
        
    if current_folder not in sys.path:
        sys.path.append(current_folder)
        
except Exception as e:
    print(f"!! Path Setup Error: {e}")

# =========================================================
# 2. IMPORTS (after the path fix)
# =========================================================
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QPushButton, 
                               QLabel, QFrame, QToolButton, QComboBox, QApplication, QMessageBox)
from PySide6.QtCore import Qt, QPoint

# Python can now find the app package
from app.core.database import DatabaseManager
import style 

class CortexBlenderBar(QMainWindow):
    def __init__(self, parent=None):
        """
        Handle   Init   operation.
        """
        super().__init__(parent)
        self.setWindowTitle("Cortex Pipeline")
        self.resize(760, 65)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.dragPos = QPoint()
        self.work_path = os.environ.get("CORTEX_WORK_PATH", "")
        self.task_label = os.environ.get("CORTEX_TASK_NAME", "Unknown")
        self.task_id = os.environ.get("CORTEX_TASK_ID")
        
        self.loader_win = None
        self.save_win = None

        self.main_widget = QFrame()
        self.main_widget.setObjectName("MainFrame")
        self.main_widget.setStyleSheet(style.BLENDER_FRAME)
        self.setCentralWidget(self.main_widget)
        
        self.init_ui()

    def init_ui(self):
        """
        Handle Init Ui operation.
        """
        self.layout = QHBoxLayout(self.main_widget)
        self.layout.setContentsMargins(15, 5, 15, 5)

        # 1. Logo & Task
        lbl_logo = QLabel("CORTEX")
        lbl_logo.setStyleSheet(style.LBL_LOGO)
        self.layout.addWidget(lbl_logo)

        lbl_task = QLabel(self.task_label)
        lbl_task.setStyleSheet(style.LBL_TASK)
        self.layout.addWidget(lbl_task)
        
        self.add_separator()
        
        # 2. Versions
        self.create_version_section()
        self.add_separator()
        
        # 3. Tools (including the smart button)
        self.create_tools_section()
        
        self.add_close_btn()

    def create_version_section(self):
        """
        Handle Create Version Section operation.
        """
        self.cmb_versions = QComboBox()
        self.cmb_versions.setMinimumWidth(120)
        self.refresh_versions()
        self.layout.addWidget(self.cmb_versions)

        btn_load = QToolButton(); 
        btn_load.setText("Load"); 
        btn_load.setToolTip("Open selected version")
        btn_load.setStyleSheet(style.BTN_TOOLBAR)
        btn_load.clicked.connect(self.load_version)
        self.layout.addWidget(btn_load)

        btn_refresh = QToolButton(); 
        btn_refresh.setText("↻");
        btn_refresh.setToolTip("Refresh list")
        btn_refresh.setStyleSheet(style.BTN_TOOLBAR) 
        btn_refresh.clicked.connect(self.refresh_versions)
        self.layout.addWidget(btn_refresh)

    def create_tools_section(self):
        """
        Handle Create Tools Section operation.
        """
        # Loader
        btn_loader = QPushButton("📂 Loader")
        btn_loader.setToolTip("Open Universal Loader")
        btn_loader.setStyleSheet(style.BTN_CTX_LOADER)
        btn_loader.clicked.connect(self.run_loader)
        self.layout.addWidget(btn_loader)

        # Save
        btn_save = QPushButton("Save +")
        btn_save.setToolTip("Save Incremental Version")
        btn_save.setStyleSheet(style.BTN_CTX_SAVE)
        btn_save.clicked.connect(self.run_save_dialog)        
        self.layout.addWidget(btn_save)

        # --- SMART PUBLISH BUTTON (Logic matched with Max) ---
        is_lookdev = False
        
        # Try to detect the department from the database
        if self.task_id:
            try:
                db = DatabaseManager()
                t_data = db.get_task_by_id(self.task_id)
                # t_data[2] is the department name (e.g. 'Lookdev')
                if t_data and ("lookdev" in t_data[2].lower() or "texture" in t_data[2].lower()):
                    is_lookdev = True
            except:
                pass

        if is_lookdev:
            # Lookdev: blue/teal button
            btn_pub = QPushButton("💎 Publish Look")
            # Use BTN_CTX_LOOKDEV (falls back to PUBLISH if missing)
            # Use the standard green style, or the lookdev style if you have one
            if hasattr(style, 'BTN_CTX_LOOKDEV'):
                btn_pub.setStyleSheet(style.BTN_CTX_LOOKDEV)
            else:
                btn_pub.setStyleSheet(style.BTN_CTX_PUBLISH) 
        else:
            # Default: green button
            btn_pub = QPushButton("🚀 Publish")
            btn_pub.setStyleSheet(style.BTN_CTX_PUBLISH)

        btn_pub.setToolTip("Publish Scene")        
        btn_pub.clicked.connect(self.run_publish)
        self.layout.addWidget(btn_pub)

    def add_separator(self):
        """
        Handle Add Separator operation.
        """
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setStyleSheet(style.SEPARATOR)
        self.layout.addWidget(line)
    
    def add_close_btn(self):
        """
        Handle Add Close Btn operation.
        """
        self.layout.addStretch()
        btn_close = QPushButton("✕")
        btn_close.setFixedSize(20, 20)
        btn_close.setToolTip("Close Cortex Bar")
        btn_close.setStyleSheet(style.BTN_CLOSE)
        btn_close.clicked.connect(self.close)
        self.layout.addWidget(btn_close)

    def mousePressEvent(self, event):
        """
        Handle Mousepressevent operation.
        """
        if event.button() == Qt.LeftButton:
            self.dragPos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """
        Handle Mousemoveevent operation.
        """
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.dragPos)
            event.accept()

    def refresh_versions(self):
        """
        Handle Refresh Versions operation.
        """
        self.cmb_versions.clear()
        if os.path.exists(self.work_path):
            files = [f for f in os.listdir(self.work_path) if f.endswith(".blend")]
            files.sort(reverse=True)
            self.cmb_versions.addItems(files)

    def load_version(self):
        """
        Handle Load Version operation.
        """
        f = self.cmb_versions.currentText()
        if f: bpy.ops.wm.open_mainfile(filepath=os.path.join(self.work_path, f))

    def run_loader(self):
        """
        Handle Run Loader operation.
        """
        try:
            import loader 
            import importlib
            importlib.reload(loader)
            self.loader_win = loader.BlenderLoader()
            self.loader_win.show()
        except ImportError as e:
            QMessageBox.critical(self, "Error", f"Could not import 'loader.py': {e}")
        except Exception as e:
            QMessageBox.critical(self, "Loader Error", str(e))
            print(f"Loader Err: {e}")

    def run_save_dialog(self):
        """
        Handle Run Save Dialog operation.
        """
        try:
            import save_view
            import importlib
            importlib.reload(save_view)
            self.save_win = save_view.SaveWindow()
            self.save_win.show()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Save Dialog Error:\n{e}")

    def run_publish(self):
        """
        Handle Run Publish operation.
        """
        try:
            import publisher_blender; import importlib; importlib.reload(publisher_blender)
            publisher_blender.run()
        except Exception as e: print(f"Publish Err: {e}")

cortex_win = None
def show_ui():
    """
    Handle Show Ui operation.
    """
    global cortex_win
    app = QApplication.instance() or QApplication(sys.argv)
    if cortex_win: cortex_win.close()
    cortex_win = CortexBlenderBar()
    cortex_win.show()