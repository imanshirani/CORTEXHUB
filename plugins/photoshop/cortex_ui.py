import os
import sys
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QLabel, 
                               QFrame, QToolButton, QComboBox, QMessageBox, QApplication)
from PySide6.QtCore import Qt, QPoint
import style 

class PhotoshopCortexBar(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cortex Photoshop Toolbar")
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(850, 65)
        
        # دریافت اطلاعات از محیط
        self.work_path = os.environ.get("CORTEX_WORK_PATH", "")
        self.task_label = os.environ.get("CORTEX_TASK_NAME", "Unknown")
        self.project_name = os.environ.get("CORTEX_PROJECT_NAME", "Project")
        self.task_id = os.environ.get("CORTEX_TASK_ID")

        # فریم اصلی مشابه بلندر
        self.main_widget = QFrame(self)
        self.main_widget.setObjectName("MainFrame")
        self.main_widget.setStyleSheet(style.PHOTOSHOP_FRAME)
        self.main_widget.setFixedSize(850, 60)
        
        self.init_ui()

    def init_ui(self):
        self.layout = QHBoxLayout(self.main_widget)
        self.layout.setContentsMargins(15, 5, 15, 5)

        # 1. Logo & Project/Task Name
        lbl_logo = QLabel("CORTEX")
        lbl_logo.setStyleSheet(style.LBL_LOGO)
        self.layout.addWidget(lbl_logo)

        # نمایش نام پروژه و تسک در کنار هم
        lbl_task = QLabel(f"{self.project_name} | {self.task_label}")
        lbl_task.setStyleSheet(style.LBL_TASK)
        self.layout.addWidget(lbl_task)
        
        self.add_separator()
        
        # 2. Versions Section (مشابه بلندر)
        self.cmb_versions = QComboBox()
        self.cmb_versions.setMinimumWidth(150)
        self.cmb_versions.setStyleSheet(style.MAINWIDGET)
        self.refresh_versions()
        self.layout.addWidget(self.cmb_versions)
        self.cmb_versions.activated.connect(self.open_selected_version)

        btn_refresh = QToolButton()
        btn_refresh.setText("↻")
        btn_refresh.setStyleSheet(style.BTN_TOOLBAR) 
        btn_refresh.clicked.connect(self.refresh_versions)
        self.layout.addWidget(btn_refresh)

        self.layout.addWidget(self.cmb_versions)

        # اضافه کردن دکمه لود اختصاصی
        self.btn_load = QPushButton("📂 Load")
        self.btn_load.setFixedWidth(70)
        self.btn_load.setStyleSheet(style.BTN_TOOLBAR) # یا استایل آبی دلخواه
        self.btn_load.clicked.connect(self.open_selected_version)
        self.layout.addWidget(self.btn_load)

        self.add_separator()
        
        # 3. Tools Section
        # دکمه ساخت سند جدید (مخصوص فتوشاپ)
        btn_new = QPushButton("📄 New")
        btn_new.setToolTip("Create Canvas with Project Resolution")
        btn_new.setStyleSheet(style.BTN_CTX_SAVE)
        btn_new.clicked.connect(self.create_doc)
        self.layout.addWidget(btn_new)

        # دکمه Save Incremental
        btn_save = QPushButton("Save +")
        btn_save.setStyleSheet(style.BTN_CTX_SAVE)
        btn_save.clicked.connect(self.run_save_dialog)        
        self.layout.addWidget(btn_save)

        # دکمه Publish با استایل سبز استاندارد
        btn_pub = QPushButton("🚀 Publish")
        btn_pub.setStyleSheet(style.BTN_CTX_PUBLISH)
        btn_pub.clicked.connect(self.run_publish)
        self.layout.addWidget(btn_pub)
        
        # دکمه بستن
        btn_close = QPushButton("✕")
        btn_close.setFixedSize(25, 25)
        btn_close.setStyleSheet(style.BTN_CLOSE)
        btn_close.clicked.connect(self.quit_app) 
        self.layout.addWidget(btn_close)


    def quit_app(self):
        """بستن کامل کورتکس و آزاد کردن رم سیستم"""
        self.close()
        QApplication.quit()

    def add_separator(self):
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setStyleSheet(style.SEPARATOR)
        self.layout.addWidget(line)

    def refresh_versions(self):
        """فقط لیست کردن فایل‌های PSD بدون باز کردن آن‌ها"""
        self.cmb_versions.clear()
        if os.path.exists(self.work_path):
            files = [f for f in os.listdir(self.work_path) if f.endswith(".psd")]
            if files:
                files.sort(reverse=True)
                self.cmb_versions.addItems(files)
            else:
                self.cmb_versions.addItem("No versions found")

    def create_doc(self):
        """ساخت داکیومنت بر اساس رزولوشن ست شده در لانچر"""
        try:
            import photoshop.api as ps
            app = ps.Application()
            app.preferences.rulerUnits = ps.Units.Pixels
            w = int(os.environ.get("CORTEX_RES_W", 1920))
            h = int(os.environ.get("CORTEX_RES_H", 1080))
            app.documents.add(width=w, height=h, name=f"Cortex_{self.task_label}")
        except: pass

    def run_save_dialog(self):
        from save_view import SaveWindow
        self.save_win = SaveWindow()
        self.save_win.show()

    def run_publish(self):
        """باز کردن ایمن پنجره پابلیشر"""
        try:
            import photoshop_publisher
            # به جای ری‌لود کردن کلاس، مستقیماً از ماژول استفاده کن
            self.pub_win = photoshop_publisher.PhotoshopPublisher(self.task_id)
            self.pub_win.show()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Publisher Error: {e}")

    # قابلیت جابه‌جایی با موس
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragPos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.dragPos)


    def open_selected_version(self):
        """باز کردن ورژن انتخاب شده در فتوشاپ"""
        selected_file = self.cmb_versions.currentText()
        
        # چک کردن اعتبار فایل
        if not selected_file or "No" in selected_file:
            QMessageBox.warning(self, "Warning", "Please select a valid version.")
            return

        file_path = os.path.join(self.work_path, selected_file).replace("\\", "/")
        
        if not os.path.exists(file_path):
            QMessageBox.critical(self, "Error", "File not found on disk!")
            return

        try:
            import photoshop.api as ps
            app = ps.Application()
            app.load(file_path) # باز کردن فایل
            print(f">> [Cortex] File Loaded: {selected_file}")
        except Exception as e:
            print(f">> [Error] Photoshop Load Failed: {e}")

cortex_ps_bar = None # تعریف متغیر گلوبال برای جلوگیری از Garbage Collection

def show_ui():
    global cortex_ps_bar
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    # --- این خط جادویی مشکل بسته شدن تولبار را برای همیشه حل میکند ---
    app.setQuitOnLastWindowClosed(False) 
    
    cortex_ps_bar = PhotoshopCortexBar()
    cortex_ps_bar.show()
    
    if __name__ == "__main__":
        sys.exit(app.exec())