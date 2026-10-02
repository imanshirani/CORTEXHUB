
import os
import qtmax
import pymxs
from PySide6.QtWidgets import (QDockWidget, QWidget, QHBoxLayout, QVBoxLayout, 
                               QPushButton, QLabel, QFrame, QToolButton, QComboBox, QSizePolicy)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont, QAction
import style

rt = pymxs.runtime



class CortexDockWidget(QDockWidget):
    def __init__(self, parent=None):
        """
        Handle   Init   operation.
        """
        super(CortexDockWidget, self).__init__("Cortex Pipeline", parent)
        
        self.setObjectName("CortexDockWidget")
        self.setAllowedAreas(Qt.TopDockWidgetArea | Qt.BottomDockWidgetArea)
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        
        # Read the work path from environment variables
        self.work_path = os.environ.get("CORTEX_WORK_PATH", "")
        self.task_label = os.environ.get("CORTEX_TASK_NAME", 
                          os.environ.get("CORTEX_TASK_ID", "Unknown"))
        # --- Main widget ---
        self.main_widget = QFrame()
        self.main_widget.setObjectName("MainFrame")
        self.main_widget.setStyleSheet(style.MAINWIDGET)
        self.setWidget(self.main_widget)

        self.layout = QHBoxLayout(self.main_widget)
        self.layout.setContentsMargins(5, 2, 5, 2)
        self.layout.setSpacing(10)

        # 1. Logo and task name
        self.create_context_section()
        self.add_separator()

        # 2. File management (versions)
        self.create_version_section()
        self.add_separator()

        # 3. Main tools
        self.create_tools_section()
        
        self.layout.addStretch() # Fill leftover space

        # Initial file scan
        self.refresh_versions()

    def create_context_section(self):
        """
        Handle Create Context Section operation.
        """
        # Cortex icon or label
        lbl_logo = QLabel("CORTEX")
        lbl_logo.setStyleSheet(style.MAINWIDGET)
        self.layout.addWidget(lbl_logo)
        
        # Show the cleaned task name
        lbl_task = QLabel(self.task_label) 
        lbl_task.setObjectName("TaskLabel")
        lbl_task.setStyleSheet(style.MAINWIDGET)
        self.layout.addWidget(lbl_task)

    def create_version_section(self):
        """
        Handle Create Version Section operation.
        """
        # Layout for this section
        v_layout = QHBoxLayout()
        v_layout.setSpacing(4)

        # "Version:" label
        v_layout.addWidget(QLabel("Ver:"))

        # Version combobox
        self.cmb_versions = QComboBox()
        self.cmb_versions.setToolTip("Select a version to Open")
        # When the user changes version, load the file (carefully)
        # self.cmb_versions.currentIndexChanged.connect(self.on_version_change) 
        v_layout.addWidget(self.cmb_versions)

        # Load button (separate so files are not loaded by accident)
        btn_load = QToolButton()
        btn_load.setText("Load") # or a Play icon
        btn_load.setStyleSheet(style.BTN_TOOLBAR) # <--- shared toolbar style
        btn_load.clicked.connect(self.load_selected_version)
        v_layout.addWidget(btn_load)

        # Refresh button (after a new save)
        btn_refresh = QToolButton()
        btn_refresh.setText("↻")
        btn_refresh.setToolTip("Refresh File List")
        btn_refresh.setStyleSheet(style.BTN_TOOLBAR)
        btn_refresh.clicked.connect(self.refresh_versions)
        v_layout.addWidget(btn_refresh)

        # Open-folder button
        btn_explore = QToolButton()
        btn_explore.setText("📂")
        btn_explore.setToolTip("Open in Explorer")
        btn_explore.setStyleSheet(style.BTN_TOOLBAR) 
        btn_explore.clicked.connect(self.open_explorer)
        v_layout.addWidget(btn_explore)

        self.layout.addLayout(v_layout)

    def create_tools_section(self):
        """
        Handle Create Tools Section operation.
        """
        # --- New Loader button ---
        btn_loader = QPushButton("📂 Loader / Workfiles")
        btn_loader.setToolTip("Manage Tasks and Load Files")
        btn_loader.clicked.connect(self.run_loader)
        btn_loader.setStyleSheet(style.BTN_CTX_LOADER)
        self.layout.addWidget(btn_loader)
        # ------------------------
        # Save
        btn_save = QPushButton("Save +")
        btn_save.setToolTip("Save Incremental Version")
        btn_save.clicked.connect(self.run_save)
        btn_save.setStyleSheet(style.BTN_CTX_SAVE)
        self.layout.addWidget(btn_save)

        
        

        # Lookdev Publish Button
        dept_env = os.environ.get("CORTEX_DEPT_NAME", "").lower()
        
        
        if "lookdev" in dept_env or "texture" in dept_env:
            btn_lookdev = QPushButton("💎 Lookdev Publish")
            btn_lookdev.setStyleSheet(style.BTN_CTX_LOOKDEV)
            btn_lookdev.clicked.connect(self.run_lookdev_publish)
            self.layout.addWidget(btn_lookdev)
        
        # Publish Button
        else:
            btn_pub = QPushButton("Publish")
            btn_pub.setStyleSheet(style.BTN_CTX_PUBLISH)
            btn_pub.clicked.connect(self.run_publish)
            self.layout.addWidget(btn_pub)

    def add_separator(self):
        """
        Handle Add Separator operation.
        """
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setProperty("class", "Separator")
        self.layout.addWidget(line)

    # --- File logic ---
    def refresh_versions(self):
        """Scan the work folder for 3ds Max files"""
        self.cmb_versions.clear()
        
        if not self.work_path or not os.path.exists(self.work_path):
            self.cmb_versions.addItem("No Work Path")
            return

        try:
            # Collect every .max file
            files = [f for f in os.listdir(self.work_path) if f.lower().endswith(".max")]
            # Reverse sort (newest first)
            files.sort(reverse=True)
            
            if not files:
                self.cmb_versions.addItem("No Files")
            else:
                self.cmb_versions.addItems(files)
                
            print(f">> [Cortex] Found {len(files)} versions.")
        except Exception as e:
            print(f"!! Error scanning files: {e}")

    def load_selected_version(self):
        """Load the file selected in the combo"""
        filename = self.cmb_versions.currentText()
        if not filename or filename in ["No Work Path", "No Files"]:
            return

        full_path = os.path.join(self.work_path, filename)
        
        if os.path.exists(full_path):
            # Use the Max command to load the file
            # quiet=True skips prompts (you can remove it)
            print(f">> Loading: {filename}")
            rt.loadMaxFile(full_path)
        else:
            print("!! File not found.")

    def open_explorer(self):
        """Open the folder in Windows Explorer"""
        if self.work_path and os.path.exists(self.work_path):
            os.startfile(self.work_path)
        else:
            print("!! Work path does not exist.")

    # --- Tool functions ---
    def run_save(self):
        """
        Handle Run Save operation.
        """
        print(">> [Cortex] Launching Save UI...")
        try:
            # 1. Import the save-window module
            import save_view
            import importlib
            importlib.reload(save_view) # Reload so code changes apply
            
            # 2. Build and show the window
            # Pass self as parent so the window stays on Max
            self.save_win = save_view.SaveWindow()
            self.save_win.show()
            
        except Exception as e:
            print(f"!! Error launching Save UI: {e}")
            import traceback
            traceback.print_exc()


    def run_publish(self):
        """
        Handle Run Publish operation.
        """
        print(">> [Cortex] Launching Publish UI...")
        try:
            # 1. Import the publisher module we built
            import publisher_max
            import importlib
            importlib.reload(publisher_max) # Reload so code changes apply
            
            # 2. Run the function
            publisher_max.run()
            
        except Exception as e:
            print(f"!! Error launching Publish UI: {e}")
            import traceback
            traceback.print_exc()

    def run_loader(self):
        """
        Handle Run Loader operation.
        """
        print(">> [Cortex] Launching Loader...")
        try:
            import loader
            import importlib
            importlib.reload(loader)
            loader.run()
        except Exception as e:
            print(f"!! Error launching Loader: {e}")
            import traceback
            traceback.print_exc()

    def run_lookdev_publish(self):
        """
        Handle Run Lookdev Publish operation.
        """
        print(">> [Cortex] Launching Lookdev Publisher...")
        try:
            import publisher_max
            import importlib
            importlib.reload(publisher_max)
            # Call the new method added in the next step
            pub = publisher_max.MaxPublisher()
            pub.run_lookdev_special() 
        except Exception as e:
            print(f"!! Error: {e}")
    

def show_ui():
    """Show the UI and make sure old docks are removed"""
    main_win = qtmax.GetQMaxMainWindow()
    if not main_win: return

    dock_obj_name = "CortexDockWidget"

    # --- FIX: delete every old dock ---
    # Walk all children and remove any named Cortex instead of a single findChild
    # This guarantees duplicate docks are gone
    children = main_win.findChildren(QDockWidget)
    for child in children:
        if child.objectName() == dock_obj_name:
            main_win.removeDockWidget(child)
            child.setParent(None)
            child.close()
            child.deleteLater()
    # -----------------------------------

    # Build a new dock with the context set by the Loader
    cortex_dock = CortexDockWidget(main_win)
    main_win.addDockWidget(Qt.TopDockWidgetArea, cortex_dock)
    cortex_dock.show()
    print(">> Cortex UI Refreshed ✅")