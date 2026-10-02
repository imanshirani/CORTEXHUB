# Location: plugins/houdini/scripts/save_view.py
import hou
import os
import glob
import re
import shutil
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QTextEdit, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

class SaveWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cortex | Save Incremental Version")
        self.setWindowFlags(Qt.Tool) # پنجره شناور
        self.resize(400, 430)
        
        # استایل پیش‌فرض (اگر فایل style.py در دسترس نبود ارور ندهد)
        self.setStyleSheet("""
            QDialog { background-color: #2b2b2b; color: #eee; }
            QLabel { color: #ccc; }
            QTextEdit { background: #1e1e1e; border: 1px solid #555; color: white; border-radius: 4px; padding: 5px; }
            QPushButton { background-color: #0078d7; color: white; font-weight: bold; border-radius: 4px; }
            QPushButton:hover { background-color: #005a9e; }
        """)

        # دریافت اطلاعات پروژه از متغیرهای محیطی
        self.work_path = os.environ.get("CORTEX_WORK_PATH", "")
        self.task_filename = os.environ.get("CORTEX_TASK_NAME", "Houdini_Task")
        self.next_version = 1
        
        # مسیر موقت برای ذخیره عکس پریویو
        self.temp_thumb = os.path.join(os.environ.get("TEMP", "C:/temp"), "ctx_houdini_thumb.jpg").replace("\\", "/")
        
        self.init_ui()
        self.calculate_version()
        self.capture_thumbnail()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # 1. نمایش تامنیل (Preview)
        self.lbl_thumbnail = QLabel("Capturing Viewport...")
        self.lbl_thumbnail.setAlignment(Qt.AlignCenter)
        self.lbl_thumbnail.setMinimumHeight(220)
        self.lbl_thumbnail.setStyleSheet("border: 2px solid #444; background: #111; border-radius: 5px;")
        self.lbl_thumbnail.setScaledContents(True) 
        layout.addWidget(self.lbl_thumbnail)

        # 2. اطلاعات ورژن
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel("Next Version:"))
        
        self.lbl_version = QLabel("v001")
        self.lbl_version.setStyleSheet("font-weight: bold; color: #00a8ff; font-size: 16px;")
        info_layout.addWidget(self.lbl_version)
        info_layout.addStretch()
        layout.addLayout(info_layout)

        # 3. کامنت
        layout.addWidget(QLabel("Comment / Description:"))
        self.txt_comment = QTextEdit()
        self.txt_comment.setPlaceholderText("What did you change in this version?")
        self.txt_comment.setMaximumHeight(80)
        layout.addWidget(self.txt_comment)

        # 4. دکمه ذخیره
        self.btn_save = QPushButton("💾 SAVE SCENE + PREVIEW")
        self.btn_save.setFixedHeight(45)
        self.btn_save.clicked.connect(self.do_save)
        layout.addWidget(self.btn_save)

    def calculate_version(self):
        if not self.work_path or not os.path.exists(self.work_path):
            self.lbl_version.setText("v001 (New)")
            return

        search_pattern = os.path.join(self.work_path, f"{self.task_filename}_v*.hip*")
        existing_files = glob.glob(search_pattern)

        current_max = 0
        version_regex = re.compile(r"_v(\d+)\.hip")

        for f in existing_files:
            match = version_regex.search(f)
            if match:
                ver = int(match.group(1))
                if ver > current_max:
                    current_max = ver
        
        self.next_version = current_max + 1
        self.lbl_version.setText(f"v{self.next_version:03d}")

    def capture_thumbnail(self):
        """گرفتن عکس از ویوپورت هودینی (Flipbook)"""
        try:
            desktop = hou.ui.curDesktop()
            scene_viewer = desktop.paneTabOfType(hou.paneTabType.SceneViewer)
            if scene_viewer:
                viewport = scene_viewer.curViewport()
                settings = scene_viewer.flipbookSettings().stash()
                
                # تنظیم روی تک فریم فعلی
                current_frame = hou.intFrame()
                settings.frameRange((current_frame, current_frame))
                settings.output(self.temp_thumb)
                settings.resolution((640, 360)) # رزولوشن سبک برای UI
                settings.useResolution(True)
                
                # اجرای فلیپ‌بوک
                scene_viewer.flipbook(viewport, settings)
                
                # لود کردن عکس در رابط کاربری
                if os.path.exists(self.temp_thumb):
                    pixmap = QPixmap(self.temp_thumb)
                    self.lbl_thumbnail.setPixmap(pixmap)
        except Exception as e:
            self.lbl_thumbnail.setText(f"Preview Error\n{e}")

    def do_save(self):
        if not self.work_path:
            QMessageBox.critical(self, "Error", "Work path not found! Launch via Cortex.")
            return
            
        if not os.path.exists(self.work_path):
            os.makedirs(self.work_path)

        # ساخت نام فایل‌ها
        base_name = f"{self.task_filename}_v{self.next_version:03d}"
        hip_file = os.path.join(self.work_path, f"{base_name}.hip").replace("\\", "/")
        jpg_file = os.path.join(self.work_path, f"{base_name}.jpg").replace("\\", "/")
        txt_file = os.path.join(self.work_path, f"{base_name}.txt").replace("\\", "/")

        try:
            # ۱. ذخیره فایل هودینی
            hou.hipFile.save(hip_file)
            
            # ۲. کپی کردن عکس پریویو
            if os.path.exists(self.temp_thumb):
                shutil.copy2(self.temp_thumb, jpg_file)
            
            # ۳. ذخیره کامنت
            comment = self.txt_comment.toPlainText()
            if comment.strip():
                with open(txt_file, "w", encoding="utf-8") as f:
                    f.write(comment)

            self.close()
            hou.ui.displayMessage(f"Success!\nVersion v{self.next_version:03d} Saved Successfully!")
            print(f">> [Cortex] Saved: {hip_file}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Save Failed:\n{e}")

def run():
    """اجرای دیالوگ و چسباندن آن به پنجره اصلی هودینی"""
    # گرفتن پنجره اصلی هودینی تا UI ما روی هوا معلق نماند
    parent = hou.qt.mainWindow()
    win = SaveWindow(parent)
    win.show()