
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
                               QListWidgetItem, QPushButton, QLabel)
from PySide6.QtCore import Qt
from app.ui import style

class ShotBuilder(QDialog):
    def __init__(self, session, shot_id, shot_name, parent=None):
        """
        Handle   Init   operation.
        """
        super().__init__(parent)
        self.session = session
        self.shot_id = shot_id
        self.setWindowTitle(f"🎬 Shot Builder: {shot_name}")
        self.setMinimumSize(400, 500)
        self.setStyleSheet(style.DIALOG_STYLESHEET)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Select Assets for this Shot:"))

        # لیست اَسِت‌ها با قابلیت چک‌باکس
        self.asset_list = QListWidget()
        self.asset_list.setStyleSheet(style.LIST_WIDGET_STYLE) 
        layout.addWidget(self.asset_list)

        # دکمه‌ها
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Save Composition")
        btn_save.setStyleSheet(style.BTN_SUCCESS)
        btn_save.clicked.connect(self.save_composition)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

        self.load_assets()

    def load_assets(self):
        """لود کردن تمام اَسِت‌های پروژه و تیک زدن موارد لینک شده"""
        # ۱. گرفتن تمام اَسِت‌های پروژه فعلی
        proj_id = self.session.context.project.id
        all_assets = self.session.db.get_assets(proj_id, None) # None برای دریافت تمام کتگوری‌ها
        
        # ۲. گرفتن آیدی اَسِت‌هایی که قبلاً به این شات لینک شده‌اند
        current_links = [str(a[0]) for a in self.session.db.get_shot_assets_extended(self.shot_id)]

        for asset in all_assets:
            # asset: (id, proj_id, name, cat, status)
            item = QListWidgetItem(f"{asset[2]} ({asset[3]})")
            item.setData(Qt.UserRole, asset[0])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            
            # اگر قبلاً لینک شده بود، تیک بزن
            if str(asset[0]) in current_links:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            
            self.asset_list.addItem(item)

    def save_composition(self):
        """
        Handle Save Composition operation.
        """
        selected_ids = []
        for i in range(self.asset_list.count()):
            item = self.asset_list.item(i)
            if item.checkState() == Qt.Checked:
                selected_ids.append(item.data(Qt.UserRole))
        
        if self.session.db.update_shot_assets(self.shot_id, selected_ids):
            self.accept()