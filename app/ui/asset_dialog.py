from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                               QPushButton, QHBoxLayout, QComboBox)
from PySide6.QtCore import Qt
from app.ui import style

class AssetDialog(QDialog):
    """    
    A dialog interface for creating or updating assets within the pipeline.

    This window handles input for asset names, categories, and project associations,
    ensuring all data conforms to the studio's naming conventions.
    """
    def __init__(self, session, asset_to_edit=None, parent=None):
        """
        Initializes the AssetDialog.

        Args:
            session (_type_): _description_
            asset_to_edit (_type_, optional): _description_. Defaults to None.
            parent (_type_, optional): _description_. Defaults to None.
        """
        super().__init__(parent)
        self.session = session
        self.asset_to_edit = asset_to_edit
        
        title = "Edit Asset" if asset_to_edit else "Create New Asset"
        self.setWindowTitle(title)
        self.setFixedSize(350, 250)
        self.setStyleSheet(style.DIALOG_STYLESHEET)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. Asset Name
        layout.addWidget(QLabel("Asset Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. HeroCharacter")
        self.name_input.setStyleSheet(style.INPUT_STYLE)
        layout.addWidget(self.name_input)
        
        # 2. Category
        layout.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        # دسته‌بندی‌های استاندارد - باید با فولدرهای اصلی پروژه هماهنگ باشد
        self.category_combo.addItems(["Characters", "Props", "Environments", "Vehicles"])
        self.category_combo.setStyleSheet(style.COMBOBOX_STYLE) # استفاده از استایل کمبوباکس
        layout.addWidget(self.category_combo)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Save Asset")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet(style.BTN_SUCCESS)
        btn_save.clicked.connect(self.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)
        
        if self.asset_to_edit:
            self.load_data()

    def load_data(self):
        """
        Handle Load Data operation.
        """
        # asset_to_edit: (id, project_id, name, category, status)
        self.name_input.setText(self.asset_to_edit[2])
        self.category_combo.setCurrentText(self.asset_to_edit[3])

    def get_data(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        return {
            "name": self.name_input.text().strip(),
            "category": self.category_combo.currentText()
        }