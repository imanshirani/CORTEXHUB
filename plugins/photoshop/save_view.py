import os
import sys
from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel, QMessageBox
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

# Import shared stylesheet
import style

class SaveWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cortex | Save New Version")
        self.setFixedSize(400, 300)
        self.setStyleSheet(style.SAVEWINDOW) # shared save-window stylesheet
        
        # Paths from environment (set by the launcher)
        self.work_path = os.environ.get("CORTEX_WORK_PATH")
        self.task_filename = os.environ.get("CORTEX_TASK_NAME", "Asset")
        
        self.next_version = self.get_next_version()
        self.init_ui()
        self.capture_psd_preview()

    def capture_psd_preview(self):
        """Grab a quick shot of the open Photoshop document for the save dialog."""
        try:
            import photoshop.api as ps
            app = ps.Application()
            if app.documents.length > 0:
                # Temp JPEG used only as a thumbnail in this window
                temp_thumb = os.path.join(os.environ["TEMP"], "ps_cortex_temp.jpg")
                options = ps.JPEGSaveOptions(quality=5)
                app.activeDocument.saveAs(temp_thumb, options, True)
                
                pixmap = QPixmap(temp_thumb)
                self.lbl_thumbnail.setPixmap(pixmap.scaled(self.lbl_thumbnail.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except:
            self.lbl_thumbnail.setText("Could not capture Photoshop preview")

    def get_next_version(self):
        """Find the next version number from PSD files already in the work folder."""
        if not os.path.exists(self.work_path):
            return 1
        
        files = [f for f in os.listdir(self.work_path) if f.endswith(".psd")]
        versions = []
        for f in files:
            try:
                # Parse version number (e.g. Asset_v002.psd)
                ver_part = f.split("_v")[-1].split(".")[0]
                versions.append(int(ver_part))
            except: pass
            
        return max(versions) + 1 if versions else 1

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Show the next version
        self.lbl_info = QLabel(f"Saving New Version: v{self.next_version:03d}")
        self.lbl_info.setObjectName("VersionLabel") # stylesheet target
        self.lbl_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_info)

        # Preview placeholder
        self.lbl_thumbnail = QLabel("Thumbnail will be captured on save")
        self.lbl_thumbnail.setFixedSize(380, 180)
        self.lbl_thumbnail.setStyleSheet(style.LBL_THUMBNAIL)
        self.lbl_thumbnail.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_thumbnail)

        # Save button
        self.btn_save = QPushButton(f"💾 SAVE v{self.next_version:03d}")
        self.btn_save.clicked.connect(self.do_save)
        layout.addWidget(self.btn_save)

    def do_save(self):
        """Save the current Photoshop document as a new version."""
        base_name = f"{self.task_filename}_v{self.next_version:03d}"
        full_psd_path = os.path.join(self.work_path, f"{base_name}.psd").replace("\\", "/")
        
        if not os.path.exists(self.work_path):
            os.makedirs(self.work_path)

        try:
            import photoshop.api as ps
            app = ps.Application()
            
            
            if app.documents.length > 0:
                doc = app.activeDocument
                options = ps.PhotoshopSaveOptions()
                doc.saveAs(full_psd_path, options, True)
                
                thumb_path = full_psd_path.replace(".psd", ".jpg")
                jpg_options = ps.JPEGSaveOptions(quality=8)
                doc.saveAs(thumb_path, jpg_options, True)
                
                print(f">> [Cortex] Saved: {full_psd_path}")
                
                # Refresh the toolbar version list without rebuilding the whole UI
                try:
                    import cortex_ui
                    if hasattr(cortex_ui, 'cortex_ps_bar') and cortex_ui.cortex_ps_bar:
                        cortex_ui.cortex_ps_bar.refresh_versions()
                except:
                    pass

                # Show success, then close the save window
                QMessageBox.information(self, "Success", f"Saved Version {self.next_version:03d}")
                self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Save Error", str(e))

def run():
    win = SaveWindow()
    win.show()