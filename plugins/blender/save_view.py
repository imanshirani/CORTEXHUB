import os
import bpy
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QTextEdit, QMessageBox)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap
import style

class SaveWindow(QWidget):
    def __init__(self):
        """
        Handle   Init   operation.
        """
        super().__init__()
        self.setWindowTitle("Save Version")
        self.resize(420, 520) 
        self.setStyleSheet(style.SAVEWINDOW)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

        self.work_path = os.environ.get("CORTEX_WORK_PATH", "")
        self.task_name = os.environ.get("CORTEX_TASK_NAME", "Unknown")
        
        self.init_ui()
        # کمی تاخیر بیشتر برای اطمینان از لود شدن
        QTimer.singleShot(300, self.capture_preview)

    def init_ui(self):
        """
        Handle Init Ui operation.
        """
        layout = QVBoxLayout(self)
        
        self.lbl_thumb = QLabel("Generating Preview...")
        self.lbl_thumb.setFixedSize(400, 230)
        self.lbl_thumb.setStyleSheet(style.LBL_THUMBNAIL)
        self.lbl_thumb.setAlignment(Qt.AlignCenter)
        self.lbl_thumb.setScaledContents(True)
        layout.addWidget(self.lbl_thumb)

        self.next_ver = self.get_next_version()
        lbl_ver = QLabel(f"Next Version: v{self.next_ver:03d}")
        lbl_ver.setStyleSheet("color: #4CAF50; font-weight: bold; font-size: 16px; margin-top: 10px;")
        layout.addWidget(lbl_ver)

        layout.addWidget(QLabel("Comment:"))
        self.txt_comment = QTextEdit()
        self.txt_comment.setPlaceholderText("Description...")
        self.txt_comment.setMaximumHeight(80)
        layout.addWidget(self.txt_comment)

        btn_save = QPushButton("💾 SAVE SCENE")
        btn_save.setStyleSheet(style.BTN_SUCCESS)
        btn_save.setFixedHeight(40)
        btn_save.clicked.connect(self.do_save)
        layout.addWidget(btn_save)

    def get_next_version(self):
        """
        Handle Get Next Version operation.
        """
        if not os.path.exists(self.work_path): return 1
        files = [f for f in os.listdir(self.work_path) if f.endswith(".blend")]
        ver = 1
        for f in files:
            if "_v" in f:
                try:
                    v = int(f.split("_v")[-1].split(".")[0])
                    if v >= ver: ver = v + 1
                except: pass
        return ver

    def capture_preview(self):
        """گرفتن عکس با پیدا کردن دقیق پنجره و اسکرین"""
        temp_path = os.path.join(os.environ["TEMP"], "cortex_blend_thumb.jpg")
        
        # 1. پیدا کردن پنجره‌ای که دارای نمای 3D است
        found_window = None
        found_area = None
        
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    found_window = window
                    found_area = area
                    break
            if found_window: break
        
        if not found_window or not found_area:
            self.lbl_thumb.setText("Error: No 3D View found!")
            print("Preview Error: Could not find any window with VIEW_3D area.")
            return

        try:
            # 2. ذخیره تنظیمات رندر
            scene = bpy.context.scene
            old_path = scene.render.filepath
            old_fmt = scene.render.image_settings.file_format
            
            scene.render.image_settings.file_format = 'JPEG'
            scene.render.filepath = temp_path
            
            # 3. استفاده از Override با پنجره و اسکرین صحیح
            # نکته: حتماً باید screen را هم پاس بدهیم تا ارور nullptr ندهد
            with bpy.context.temp_override(window=found_window, screen=found_window.screen, area=found_area):
                bpy.ops.render.opengl(write_still=True)
            
            # 4. بازگرداندن تنظیمات
            scene.render.filepath = old_path
            scene.render.image_settings.file_format = old_fmt
            
            if os.path.exists(temp_path):
                self.lbl_thumb.setPixmap(QPixmap(temp_path))
            else:
                self.lbl_thumb.setText("Preview Failed")
                
        except Exception as e:
            self.lbl_thumb.setText(f"Err: {e}")
            print(f"Capture Exception: {e}")
            import traceback
            traceback.print_exc()

    def do_save(self):
        """
        Handle Do Save operation.
        """
        base_name = f"{self.task_name}_v{self.next_ver:03d}"
        blend_path = os.path.join(self.work_path, f"{base_name}.blend")
        jpg_path = os.path.join(self.work_path, f"{base_name}.jpg")
        txt_path = os.path.join(self.work_path, f"{base_name}.txt")
        
        try:
            bpy.ops.wm.save_as_mainfile(filepath=blend_path, check_existing=False)
            
            if self.lbl_thumb.pixmap() and not self.lbl_thumb.text().startswith("Err"):
                self.lbl_thumb.pixmap().save(jpg_path, "JPG")
            
            comment = self.txt_comment.toPlainText()
            if comment.strip():
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(comment)
            
            self.close()
            import cortex_ui
            if cortex_ui.cortex_win: cortex_ui.cortex_win.refresh_versions()
            
        except Exception as e:
            QMessageBox.critical(self, "Save Error", str(e))