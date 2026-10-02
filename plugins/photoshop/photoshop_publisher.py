import os
import sys
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QMessageBox, QComboBox, QFrame)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
import style 

# --- Path fix so Photoshop can find the app package ---
try:
    current_script_path = os.path.dirname(os.path.abspath(__file__))
    root_path = os.path.dirname(os.path.dirname(current_script_path))
    if root_path not in sys.path: sys.path.append(root_path)
except: pass

from app.core.database import DatabaseManager
from app.core.filesystem import FileSystemManager

class PhotoshopPublisher(QDialog):
    def __init__(self, task_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cortex | Photoshop Publisher")
        self.setFixedSize(500, 450)
        self.setStyleSheet(style.SAVEWINDOW) 
        
        self.task_id = task_id
        self.work_path = os.environ.get("CORTEX_WORK_PATH")
        self.task_name = os.environ.get("CORTEX_TASK_NAME", "Asset")
        self.db = DatabaseManager() # connect to the database
        
        self.init_ui()
        self.capture_preview()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # --- Header ---
        header = QLabel(f"PUBLISH: {self.task_name}")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #00a8ff;")
        layout.addWidget(header)

        # --- Preview ---
        self.lbl_preview = QLabel("Capturing Preview...")
        self.lbl_preview.setFixedSize(480, 200)
        self.lbl_preview.setAlignment(Qt.AlignCenter)
        self.lbl_preview.setStyleSheet("border: 2px solid #444; background: #111; border-radius: 5px;")
        layout.addWidget(self.lbl_preview)

        # --- Category picker (fully dynamic from filesystem) ---
        cat_layout = QHBoxLayout()
        cat_layout.addWidget(QLabel("Publish As:"))
        
        self.cmb_category = QComboBox()
        self.cmb_category.setStyleSheet(style.MAINWIDGET)
        self.cmb_category.setMinimumWidth(200)
        self.load_categories_from_fs() # load categories from the project structure
        cat_layout.addWidget(self.cmb_category)
        
        layout.addLayout(cat_layout)
        layout.addSpacing(10)
        
        # --- Publish button ---
        self.btn_publish = QPushButton("🚀 FINAL PUBLISH TO PIPELINE")
        self.btn_publish.setFixedHeight(45)
        self.btn_publish.setStyleSheet(style.BTN_CTX_PUBLISH) 
        self.btn_publish.clicked.connect(self.do_publish)
        layout.addWidget(self.btn_publish)

    def load_categories_from_fs(self):
        """Load 2D categories from the Cortex filesystem structure."""
        self.cmb_category.clear()
        
        context = self.db.get_task_context_data(self.task_id)
        if not context:
            self.cmb_category.addItems(["Concept Art", "Texture"])
            return

        # Use Asset vs Shot folder layout
        if context['type'] == 'Asset':
            structure = FileSystemManager.get_asset_structure(self.db)
        else:
            structure = FileSystemManager.get_shot_structure(self.db)
            
        try:
            # 2D folders under Work
            work_struct = structure.get("work", {})
            if isinstance(work_struct, dict) and "2D" in work_struct:
                categories = work_struct["2D"]
            else:
                # Fallback when the nested filesystem layout is not in place yet
                categories = ["Storyboard", "Texture", "Concept", "Matte_Painting", "UI"]
                
            # Display names for the menu (e.g. matte_painting -> Matte Painting)
            ui_categories = [str(c).replace("_", " ").title() for c in categories]
            self.cmb_category.addItems(ui_categories)
            
        except Exception as e:
            print(f"Error parsing categories: {e}")
            self.cmb_category.addItems(["Texture", "Concept"])

    def capture_preview(self):
        """Capture a screenshot from the active Photoshop document."""
        try:
            import photoshop.api as ps
            app = ps.Application()
            if app.documents.length > 0:
                temp_path = os.path.join(os.environ["TEMP"], "cortex_pub_prev.jpg")
                options = ps.JPEGSaveOptions(quality=5)
                app.activeDocument.saveAs(temp_path, options, True)
                
                pixmap = QPixmap(temp_path)
                self.lbl_preview.setPixmap(pixmap.scaled(self.lbl_preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except:
            self.lbl_preview.setText("No Active Document for Preview")

    def do_publish(self):
        """Publish using the database-resolved path."""
        category_ui = self.cmb_category.currentText()
        category_clean = category_ui.replace(" ", "_").lower() # back to filesystem form (e.g. matte_painting)
        
        # Resolve the base publish path via database.py
        # Result: .../publish/2D/matte_painting/photoshop
        base_pub_path = self.db.get_publish_path(
            task_id=self.task_id, 
            software="photoshop", 
            category=f"2D/{category_clean}"
        )
        
        if not base_pub_path:
            QMessageBox.critical(self, "Error", "Could not resolve publish path from database.")
            return

        # Append the task-name folder at the end of the path
        # Output: .../publish/2D/matte_painting/photoshop/TEST01
        publish_dir = os.path.join(base_pub_path, self.task_name).replace("\\", "/")
        
        if not os.path.exists(publish_dir):
            os.makedirs(publish_dir)

        try:
            import photoshop.api as ps
            app = ps.Application()
            
            if app.documents.length > 0:
                doc = app.activeDocument
                
                # Save PSD and PNG into the resolved publish folder
                psd_pub_path = os.path.join(publish_dir, f"{self.task_name}.psd").replace("\\", "/")
                doc.saveAs(psd_pub_path, ps.PhotoshopSaveOptions(), True)
                
                png_pub_path = os.path.join(publish_dir, f"{self.task_name}.png").replace("\\", "/")
                doc.saveAs(png_pub_path, ps.PNGSaveOptions(), True)
                
                # Register the publish in the database
                current_user = os.environ.get("CORTEX_USER", "Pipeline_User")
                self.db.create_publish(
                    task_id=self.task_id,
                    version=1,
                    user_name=current_user,
                    comment=f"Published to {category_ui}",
                    thumbnail_path=png_pub_path,
                    files_dict={"source": psd_pub_path, "output": png_pub_path}
                )
                
                # Success dialog
                msg = QMessageBox(self)
                msg.setWindowTitle("Success")
                msg.setText(f"Published successfully to:\n{publish_dir}")
                
                open_btn = msg.addButton("📂 Open Publish Folder", QMessageBox.ActionRole)
                msg.addButton("OK", QMessageBox.AcceptRole)
                msg.exec()
                
                if msg.clickedButton() == open_btn:
                    os.startfile(publish_dir)
                
                self.accept()
            else:
                QMessageBox.warning(self, "Warning", "No active document found!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Publish Failed: {e}")