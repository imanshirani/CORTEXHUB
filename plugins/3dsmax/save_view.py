# Location: plugins/3dsmax/save_view.py
import os
import pymxs
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QTextEdit, QLineEdit, QFrame, QMessageBox)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QImage
import style
rt = pymxs.runtime

class SaveWindow(QWidget):
    def __init__(self, parent=None):
        """
        Handle   Init   operation.
        """
        super(SaveWindow, self).__init__(parent)
        self.setWindowTitle("Save Incremental Version")
        self.setWindowFlags(Qt.Tool) # Floating window
        self.resize(400, 400)
        
        # Dark style
        self.setStyleSheet(style.SAVEWINDOW)

        # Read project info
        self.work_path = os.environ.get("CORTEX_WORK_PATH", "")
        self.task_filename = os.environ.get("CORTEX_TASK_NAME", "UnknownTask")
        self.next_version = 1
        
        self.init_ui()
        self.calculate_version()
        self.capture_thumbnail()

    def init_ui(self):
        """
        Handle Init Ui operation.
        """
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # 1. Thumbnail (Preview)
        self.lbl_thumbnail = QLabel()
        self.lbl_thumbnail.setAlignment(Qt.AlignCenter)
        self.lbl_thumbnail.setStyleSheet(style.LBL_THUMBNAIL)
        self.lbl_thumbnail.setMinimumHeight(220)
        # Fit the image
        self.lbl_thumbnail.setScaledContents(True) 
        layout.addWidget(self.lbl_thumbnail)

        # 2. Version info
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel("Next Version:"))
        
        self.lbl_version = QLabel("v001")
        self.lbl_version.setObjectName("VersionLabel")
        info_layout.addWidget(self.lbl_version)
        info_layout.addStretch()
        layout.addLayout(info_layout)

        # 3. Comment
        layout.addWidget(QLabel("Comment / Description:"))
        self.txt_comment = QTextEdit()
        self.txt_comment.setPlaceholderText("What did you change in this version?")
        self.txt_comment.setMaximumHeight(80)
        layout.addWidget(self.txt_comment)

        # 4. Save button
        self.btn_save = QPushButton("💾 SAVE SCENE + PREVIEW")
        self.btn_save.clicked.connect(self.do_save)
        layout.addWidget(self.btn_save)

    def calculate_version(self):
        """
        Handle Calculate Version operation.
        """
        if not os.path.exists(self.work_path):
            self.lbl_version.setText("Err: No Path")
            return

        max_files = [f for f in os.listdir(self.work_path) if f.endswith(".max")]
        
        current_max = 0
        for f in max_files:
            # Only consider files that start with the task name
            if not f.startswith(self.task_filename):
                continue
            try:
                # Format: Modeling_v005.max
                part = f.split("_v")[-1] 
                num = part.split(".")[0]
                if num.isdigit():
                    val = int(num)
                    if val > current_max:
                        current_max = val
            except:
                pass
        
        self.next_version = current_max + 1
        self.lbl_version.setText(f"v{self.next_version:03d}")

    def capture_thumbnail(self):
        """Capture a still and shrink it so the window does not grow"""
        try:
            # 1. Raw (large) screenshot
            bmp = rt.gw.getViewportDib()
            temp_path = os.path.join(os.environ["TEMP"], "cortex_temp_thumb.jpg")
            bmp.filename = temp_path
            rt.save(bmp)
            
            # 2. Load the image in memory
            full_pixmap = QPixmap(temp_path)
            
            # 3. --- Resize before display ---
            # Cap width at 380px (height follows)
            scaled_pixmap = full_pixmap.scaledToWidth(380, Qt.SmoothTransformation)
            
            self.lbl_thumbnail.setPixmap(scaled_pixmap)
            
        except Exception as e:
            self.lbl_thumbnail.setText(f"No Preview\n{e}")

    def do_save(self):
        """Final save (Max + image + comment)"""
        if not os.path.exists(self.work_path):
            print("!! Work path not found.")
            return

        # 1. Build filenames
        # Max file: Modeling_v001.max
        base_name = f"{self.task_filename}_v{self.next_version:03d}"
        max_file = os.path.join(self.work_path, f"{base_name}.max")
        jpg_file = os.path.join(self.work_path, f"{base_name}.jpg") # <--- image file
        txt_file = os.path.join(self.work_path, f"{base_name}.txt") # optional text file

        try:
            # a) Save the Max file
            rt.saveMaxFile(max_file)
            print(f">> [Cortex] Scene Saved: {max_file}")
            
            # b) Save the thumbnail
            # Save the image currently shown in the window
            if self.lbl_thumbnail.pixmap():
                self.lbl_thumbnail.pixmap().save(jpg_file, "JPG")
                print(f">> [Cortex] Preview Saved: {jpg_file}")
            
            # c) Save the comment if the user wrote one
            comment = self.txt_comment.toPlainText()
            if comment.strip():
                with open(txt_file, "w", encoding="utf-8") as f:
                    f.write(comment)

            # Success message and close
            # QMessageBox.information(self, "Success", f"Version v{self.next_version:03d} Saved Successfully!")
            self.close()
            
            # Refresh the main toolbar (important)
            # Updates the version list on the toolbar
            try:
                import cortex_ui
                # Find the open instance and refresh it
                main_win = cortex_ui.qtmax.GetQMaxMainWindow()
                dock = main_win.findChild(cortex_ui.QDockWidget, "CortexDockWidget")
                if dock:
                    # Call refresh_versions on CortexDockWidget
                    # The dock is a QDockWidget; find the inner widget or the class
                    # (A bit tricky; leave it simple so it does not error)
                    pass 
            except:
                pass
            
        except Exception as e:
            print(f"!! Save Failed: {e}")
            QMessageBox.critical(self, "Error", f"Save Failed:\n{e}")

if __name__ == "__main__":
    win = SaveWindow()
    win.show()