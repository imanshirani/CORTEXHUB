# Location: plugins/maya/save_view.py
import os
import maya.cmds as cmds
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QTextEdit, QFrame, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
import style # Shared style

class SaveWindow(QWidget):
    def __init__(self, parent=None):
        super(SaveWindow, self).__init__(parent)
        self.setWindowTitle("Maya Incremental Save")
        self.setWindowFlags(Qt.Tool)
        self.resize(400, 450)
        self.setStyleSheet(style.SAVEWINDOW)

        self.work_path = os.environ.get("CORTEX_WORK_PATH", "")
        self.task_filename = os.environ.get("CORTEX_TASK_NAME", "MayaTask")
        self.next_version = 1
        
        self.init_ui()
        self.calculate_version()
        self.capture_thumbnail()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.lbl_thumbnail = QLabel()
        self.lbl_thumbnail.setStyleSheet(style.LBL_THUMBNAIL)
        self.lbl_thumbnail.setMinimumHeight(220)
        self.lbl_thumbnail.setScaledContents(True) 
        layout.addWidget(self.lbl_thumbnail)

        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel("Next Version:"))
        self.lbl_version = QLabel("v001")
        self.lbl_version.setObjectName("VersionLabel")
        info_layout.addWidget(self.lbl_version)
        layout.addLayout(info_layout)

        self.txt_comment = QTextEdit()
        self.txt_comment.setPlaceholderText("Notes for this version...")
        self.txt_comment.setMaximumHeight(80)
        layout.addWidget(self.txt_comment)

        self.btn_save = QPushButton("💾 SAVE MAYA SCENE")
        self.btn_save.clicked.connect(self.do_save)
        layout.addWidget(self.btn_save)

    def calculate_version(self):
        """Like Max, find the next version number"""
        if not os.path.exists(self.work_path): return
        files = [f for f in os.listdir(self.work_path) if f.endswith((".mb", ".ma"))]
        current_max = 0
        for f in files:
            if "_v" in f:
                try:
                    num = int(f.split("_v")[-1].split(".")[0])
                    if num > current_max: current_max = num
                except: pass
        self.next_version = current_max + 1
        self.lbl_version.setText(f"v{self.next_version:03d}")

    def capture_thumbnail(self):
        """Capture the Maya viewport (Max getViewportDib equivalent)"""
        temp_path = os.path.join(os.environ["TEMP"], "maya_save_thumb.jpg")
        # Playblast a single frame
        cmds.playblast(frame=cmds.currentTime(q=True), format="image", viewer=False, 
                       compression="jpg", completeFilename=temp_path, widthHeight=[480, 270])
        self.lbl_thumbnail.setPixmap(QPixmap(temp_path))

    def do_save(self):
        base_name = f"{self.task_filename}_v{self.next_version:03d}"
        maya_file = os.path.join(self.work_path, f"{base_name}.mb")
        jpg_file = os.path.join(self.work_path, f"{base_name}.jpg")

        try:
            # Save in Maya
            cmds.file(rename=maya_file)
            cmds.file(save=True, type='mayaBinary')
            
            # Save the image
            if self.lbl_thumbnail.pixmap():
                self.lbl_thumbnail.pixmap().save(jpg_file, "JPG")
            
            self.close()
            print(f">> [Cortex] Maya Version Saved: {base_name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Save Failed: {e}")