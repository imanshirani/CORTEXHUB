import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QTextEdit, QPushButton, QCheckBox, QGroupBox, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from app.ui import style

class PublishDialog(QDialog):
    def __init__(self, session, task_id, parent=None, thumbnail_path=None, software="max", output_config=None):
        """
        Handle   Init   operation.
        """
        super().__init__(parent)
        self.session = session
        self.task_id = task_id
        self.thumbnail_path = thumbnail_path
        self.software = software
        
        self.output_config = output_config or [] 
        
        # 1. دریافت اطلاعات کانتکست
        self.context = self.session.db.get_task_context_data(task_id)
        
        # --- SAFETY CHECK ---
        if not self.context:
            self.setWindowTitle("Context Error")
            self.resize(300, 150)
            self.setStyleSheet(style.DIALOG_STYLESHEET)
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("❌ <b>CRITICAL ERROR</b>"))
            layout.addWidget(QLabel("Task ID not found in Database."))
            layout.addWidget(QLabel("Did you reset the DB while Max was open?"))
            layout.addWidget(QLabel("<b>Please Restart 3ds Max.</b>"))
            btn = QPushButton("Close")
            btn.clicked.connect(self.reject)
            layout.addWidget(btn)
            return
        # --------------------

        self.current_version = self.session.db.get_latest_version(task_id)
        self.next_version = self.current_version + 1
        
        self.setWindowTitle(f"Publish Helper ({self.software.title()}) - v{self.next_version:03d}")
        self.resize(500, 650)
        self.setStyleSheet(style.DIALOG_STYLESHEET)
        
        self.init_ui()
        self.load_thumbnail()

    def init_ui(self):
        """
        Handle Init Ui operation.
        """
        if not self.context: return
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # --- Header ---
        header_layout = QHBoxLayout()
        self.lbl_thumb = QLabel()
        self.lbl_thumb.setFixedSize(220, 140)
        self.lbl_thumb.setStyleSheet("background-color: #222; border: 2px dashed #555;")
        self.lbl_thumb.setAlignment(Qt.AlignCenter)
        self.lbl_thumb.setScaledContents(True) # فیت کردن عکس
        header_layout.addWidget(self.lbl_thumb)
        
        info_layout = QVBoxLayout()
        info_layout.addWidget(QLabel(f"Task: <b>{self.context.get('task_title')}</b>"))
        info_layout.addWidget(QLabel(f"Entity: {self.context.get('entity_name')}"))
        lbl_ver = QLabel(f"v{self.next_version:03d}")
        lbl_ver.setStyleSheet("font-size: 32px; font-weight: bold; color: #28a745;")
        info_layout.addWidget(lbl_ver)
        info_layout.addStretch()
        header_layout.addLayout(info_layout)
        layout.addLayout(header_layout)

        # --- Outputs ---
        group_out = QGroupBox("Publish Outputs")
        v_out = QVBoxLayout(group_out)
        self.checks = {}

        # اینجا دیگر هیچ شرط ایف و السی نداریم!
        # فقط روی لیستی که تحویل گرفتیم لوپ می‌زنیم
        for item in self.output_config:
            # item مثال: {'key': 'source', 'label': 'Max File', 'checked': True, 'enabled': False}
            chk = QCheckBox(item['label'])
            chk.setChecked(item.get('checked', True))
            chk.setEnabled(item.get('enabled', True))
            v_out.addWidget(chk)
            
            # ذخیره با کلید مشخص (مثلاً 'source' یا 'alembic')
            self.checks[item['key']] = chk

        layout.addWidget(group_out)

        # --- Comment ---
        layout.addWidget(QLabel("Comment (Required):"))
        self.txt_comment = QTextEdit()
        self.txt_comment.setPlaceholderText("Description of changes...")
        self.txt_comment.setMaximumHeight(80)
        layout.addWidget(self.txt_comment)

        # --- Buttons ---
        btn_layout = QHBoxLayout()
        btn_pub = QPushButton("🚀 PUBLISH NOW")
        btn_pub.setStyleSheet(style.BTN_SUCCESS)
        btn_pub.setFixedHeight(40)
        btn_pub.clicked.connect(self.do_publish)
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setStyleSheet(style.BTN_SECONDARY)
        btn_cancel.setFixedHeight(40)
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_pub)
        layout.addLayout(btn_layout)

    def load_thumbnail(self):
        """لود کردن عکس از مسیری که مکس فرستاده"""
        if self.thumbnail_path and os.path.exists(self.thumbnail_path):
            pix = QPixmap(self.thumbnail_path)
            self.lbl_thumb.setPixmap(pix)
        else:
            self.lbl_thumb.setText("No Preview")

    def get_data(self):
        """
        Handle Get Data operation.
        """
        selected_outputs = []
        for key, chk in self.checks.items():
            if chk.isChecked():
                selected_outputs.append(key)
        return {
            "version": self.next_version,
            "comment": self.txt_comment.toPlainText(),
            "outputs": selected_outputs
        }

    def do_publish(self):
        """
        Handle Do Publish operation.
        """
        if len(self.txt_comment.toPlainText()) < 3:
            QMessageBox.warning(self, "Warning", "Please write a comment.")
            return
        self.accept()