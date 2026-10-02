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
        self.setWindowFlags(Qt.Tool) # پنجره شناور
        self.resize(400, 400)
        
        # استایل دارک
        self.setStyleSheet(style.SAVEWINDOW)

        # دریافت اطلاعات پروژه
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

        # 1. نمایش تامنیل (Preview)
        self.lbl_thumbnail = QLabel()
        self.lbl_thumbnail.setAlignment(Qt.AlignCenter)
        self.lbl_thumbnail.setStyleSheet(style.LBL_THUMBNAIL)
        self.lbl_thumbnail.setMinimumHeight(220)
        # این ویژگی باعث می‌شود عکس فیت شود
        self.lbl_thumbnail.setScaledContents(True) 
        layout.addWidget(self.lbl_thumbnail)

        # 2. اطلاعات ورژن
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel("Next Version:"))
        
        self.lbl_version = QLabel("v001")
        self.lbl_version.setObjectName("VersionLabel")
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
            # فقط فایل‌هایی که با نام تسک شروع می‌شوند را بررسی کن
            if not f.startswith(self.task_filename):
                continue
            try:
                # فرمت: Modeling_v005.max
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
        """گرفتن عکس و کوچک کردن آن برای جلوگیری از بزرگ شدن پنجره"""
        try:
            # 1. گرفتن اسکرین‌شات خام (بزرگ)
            bmp = rt.gw.getViewportDib()
            temp_path = os.path.join(os.environ["TEMP"], "cortex_temp_thumb.jpg")
            bmp.filename = temp_path
            rt.save(bmp)
            
            # 2. لود کردن عکس در حافظه
            full_pixmap = QPixmap(temp_path)
            
            # 3. --- نکته مهم: تغییر سایز عکس قبل از نمایش ---
            # عکس را به عرض 380 پیکسل محدود می‌کنیم (ارتفاع اتوماتیک تنظیم می‌شود)
            scaled_pixmap = full_pixmap.scaledToWidth(380, Qt.SmoothTransformation)
            
            self.lbl_thumbnail.setPixmap(scaled_pixmap)
            
        except Exception as e:
            self.lbl_thumbnail.setText(f"No Preview\n{e}")

    def do_save(self):
        """عملیات ذخیره نهایی (مکس + عکس + کامنت)"""
        if not os.path.exists(self.work_path):
            print("!! Work path not found.")
            return

        # 1. ساخت نام فایل‌ها
        # فایل مکس: Modeling_v001.max
        base_name = f"{self.task_filename}_v{self.next_version:03d}"
        max_file = os.path.join(self.work_path, f"{base_name}.max")
        jpg_file = os.path.join(self.work_path, f"{base_name}.jpg") # <--- فایل تصویر
        txt_file = os.path.join(self.work_path, f"{base_name}.txt") # فایل تکست (اختیاری)

        try:
            # الف) ذخیره فایل مکس
            rt.saveMaxFile(max_file)
            print(f">> [Cortex] Scene Saved: {max_file}")
            
            # ب) ذخیره تصویر (Thumbnail)
            # عکسی که الان در پنجره میبینیم را برمیداریم و ذخیره میکنیم
            if self.lbl_thumbnail.pixmap():
                self.lbl_thumbnail.pixmap().save(jpg_file, "JPG")
                print(f">> [Cortex] Preview Saved: {jpg_file}")
            
            # ج) ذخیره کامنت (اگر کاربر چیزی نوشته بود)
            comment = self.txt_comment.toPlainText()
            if comment.strip():
                with open(txt_file, "w", encoding="utf-8") as f:
                    f.write(comment)

            # نمایش پیغام موفقیت و بستن پنجره
            # QMessageBox.information(self, "Success", f"Version v{self.next_version:03d} Saved Successfully!")
            self.close()
            
            # رفرش کردن تولبار اصلی (خیلی مهم)
            # این خط باعث می‌شود لیست ورژن‌ها در نوار ابزار بالا آپدیت شود
            try:
                import cortex_ui
                # پیدا کردن نمونه باز شده و رفرش کردن آن
                main_win = cortex_ui.qtmax.GetQMaxMainWindow()
                dock = main_win.findChild(cortex_ui.QDockWidget, "CortexDockWidget")
                if dock:
                    # دسترسی به متد refresh_versions داخل کلاس CortexDockWidget
                    # چون dock خودش QDockWidget است، باید ویجت داخلی یا خود کلاس را پیدا کنیم
                    # (این بخش کمی تریکی است، فعلا ساده رها می‌کنیم تا ارور ندهد)
                    pass 
            except:
                pass
            
        except Exception as e:
            print(f"!! Save Failed: {e}")
            QMessageBox.critical(self, "Error", f"Save Failed:\n{e}")

if __name__ == "__main__":
    win = SaveWindow()
    win.show()