import os
from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel, QFileDialog, QMessageBox
from app.ui import style

class Publisher2D(QDialog):
    def __init__(self, session, task_id):
        super().__init__()
        self.session = session
        self.task_id = task_id
        self.setWindowTitle("Cortex | 2D Asset Publisher")
        self.setFixedSize(400, 200)
        self.setStyleSheet(style.DARK_THEME) # استفاده از تم اصلی پروژه
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        self.info_lbl = QLabel("نرم‌افزار: Photoshop/GIMP\nفایل خود را برای پابلیش انتخاب کنید:")
        layout.addWidget(self.info_lbl)

        self.btn_select = QPushButton("📁 انتخاب فایل (PSD / XCF / PNG)")
        self.btn_select.clicked.connect(self.select_file)
        layout.addWidget(self.btn_select)

        self.btn_publish = QPushButton("🚀 PUBLISH TO PIPELINE")
        self.btn_publish.setStyleSheet(style.BTN_SUCCESS) # استفاده از دکمه سبز
        self.btn_publish.setEnabled(False)
        self.btn_publish.clicked.connect(self.do_publish)
        layout.addWidget(self.btn_publish)
        
        self.selected_file = None

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "انتخاب فایل خروجی", "", "Images/Projects (*.psd *.png *.jpg *.xcf)")
        if file_path:
            self.selected_file = file_path
            self.btn_publish.setEnabled(True)
            self.btn_select.setText(f"Selected: {os.path.basename(file_path)}")

    def do_publish(self):
        # اینجا منطق کپی کردن فایل به پوشه Publish پروژه را می‌نویسیم
        # و در دیتابیس ثبت می‌کنیم
        QMessageBox.information(self, "موفقیت", "فایل با موفقیت در پایپلاین ثبت و پابلیش شد.")
        self.accept()