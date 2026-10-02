import os
import sys
from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel, QMessageBox
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

# اضافه کردن مسیر استایل
import style

class SaveWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cortex | Save New Version")
        self.setFixedSize(400, 300)
        self.setStyleSheet(style.SAVEWINDOW) # استفاده از استایل استاندارد شما
        
        # دریافت مسیرها از محیط (ست شده توسط Launcher)
        self.work_path = os.environ.get("CORTEX_WORK_PATH")
        self.task_filename = os.environ.get("CORTEX_TASK_NAME", "Asset")
        
        self.next_version = self.get_next_version()
        self.init_ui()
        self.capture_psd_preview()

    def capture_psd_preview(self):
        """گرفتن یک شات سریع از سند باز فتوشاپ برای نمایش در پنجره سیو"""
        try:
            import photoshop.api as ps
            app = ps.Application()
            if app.documents.length > 0:
                # ذخیره یک جی‌پی‌جی موقت برای نمایش در این پنجره
                temp_thumb = os.path.join(os.environ["TEMP"], "ps_cortex_temp.jpg")
                options = ps.JPEGSaveOptions(quality=5)
                app.activeDocument.saveAs(temp_thumb, options, True)
                
                pixmap = QPixmap(temp_thumb)
                self.lbl_thumbnail.setPixmap(pixmap.scaled(self.lbl_thumbnail.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except:
            self.lbl_thumbnail.setText("Could not capture Photoshop preview")

    def get_next_version(self):
        """یافتن شماره ورژن بعدی بر اساس فایل‌های موجود در پوشه ورک"""
        if not os.path.exists(self.work_path):
            return 1
        
        files = [f for f in os.listdir(self.work_path) if f.endswith(".psd")]
        versions = []
        for f in files:
            try:
                # جدا کردن شماره ورژن (مثلاً Asset_v002.psd)
                ver_part = f.split("_v")[-1].split(".")[0]
                versions.append(int(ver_part))
            except: pass
            
        return max(versions) + 1 if versions else 1

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # نمایش ورژن جدید
        self.lbl_info = QLabel(f"Saving New Version: v{self.next_version:03d}")
        self.lbl_info.setObjectName("VersionLabel") # برای استایل دهی
        self.lbl_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_info)

        # پیش‌نمایش (Placeholder)
        self.lbl_thumbnail = QLabel("Thumbnail will be captured on save")
        self.lbl_thumbnail.setFixedSize(380, 180)
        self.lbl_thumbnail.setStyleSheet(style.LBL_THUMBNAIL)
        self.lbl_thumbnail.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_thumbnail)

        # دکمه ذخیره
        self.btn_save = QPushButton(f"💾 SAVE v{self.next_version:03d}")
        self.btn_save.clicked.connect(self.do_save)
        layout.addWidget(self.btn_save)

    def do_save(self):
        """اجرای عملیات ذخیره در فتوشاپ"""
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
                
                # رفرش کردن لیست در تولبار بدون لود مجدد کل UI
                try:
                    import cortex_ui
                    if hasattr(cortex_ui, 'cortex_ps_bar') and cortex_ui.cortex_ps_bar:
                        cortex_ui.cortex_ps_bar.refresh_versions()
                except:
                    pass

                # اول پیام موفقیت را نشان بده، بعد پنجره سیو را ببند
                QMessageBox.information(self, "Success", f"Saved Version {self.next_version:03d}")
                self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Save Error", str(e))

def run():
    win = SaveWindow()
    win.show()