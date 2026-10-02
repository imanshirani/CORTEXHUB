import json
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog,
                               QLineEdit, QPushButton, QTabWidget, QMessageBox, 
                               QFrame, QComboBox, QTextEdit)
from PySide6.QtCore import Qt
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QIntValidator 
import datetime

from app.ui import style
from app.core import config
from app.core.filesystem import FileSystemManager
from PySide6.QtCore import Qt, QSettings

class SettingsView(QWidget):
    def __init__(self, session):
        """
        Handle   Init   operation.
        """
        super().__init__()
        self.session = session
        self.user = session.context.user
        
        layout = QVBoxLayout(self)
        
        # عنوان صفحه
        title = QLabel("Settings")
        title.setStyleSheet(style.SETTINGS_TITLE)
        layout.addWidget(title)

        # تب‌ها
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(style.TAB_STYLE)
        
        # 1. پروفایل
        self.profile_tab = QWidget()
        self.setup_profile_tab()
        self.tabs.addTab(self.profile_tab, "My Profile")

        # 2. ابزارها (تنظیمات لوکال مثل مسیر نرم‌افزارها) - [NEW TAB]
        self.utility_tab = QWidget()
        self.setup_utility_tab()
        self.tabs.addTab(self.utility_tab, "Utilities")
        
        # 2. تنظیمات ادمین (فقط اگر ادمین باشد)
        if self.user.role == "admin":
            self.admin_tab = QWidget()
            self.setup_admin_tab() # حالا این تابع کدهای جدید را هم دارد
            self.tabs.addTab(self.admin_tab, "Admin Config")
        
        # 3. درباره ما
        self.about_tab = QWidget()
        self.setup_about_tab()
        self.tabs.addTab(self.about_tab, "About")
        
        layout.addWidget(self.tabs)

    #-------------------
    # Admin Tab (MERGED & FIXED)
    #-------------------
    def setup_admin_tab(self):
        """
        Handle Setup Admin Tab operation.
        """
        layout = QVBoxLayout(self.admin_tab)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # هشدار
        info = QLabel("⚠ These settings affect the entire studio. Change with caution.")
        info.setStyleSheet(style.ADMIN_WARNING_LBL)
        layout.addWidget(info)

        # --- Section 1: General Settings ---
        layout.addWidget(QLabel("Project Server Path (Root):"))
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("e.g. Z:/Cortex_Projects")
        self.path_input.setStyleSheet(style.LOGIN_INPUT)
        current_path = self.session.db.get_setting("server_path", default="Z:/Projects")
        self.path_input.setText(current_path)
        layout.addWidget(self.path_input)

        # Global FPS
        layout.addWidget(QLabel("Global Frame Rate (FPS):"))
        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["24", "25", "30", "60"])
        self.fps_combo.setStyleSheet(style.ADMIN_COMBO)
        current_fps = self.session.db.get_setting("global_fps", default=str(config.DEFAULT_FPS))
        self.fps_combo.setCurrentText(str(current_fps))
        layout.addWidget(self.fps_combo)

        # Default Resolution
        layout.addWidget(QLabel("Default Resolution (WxH):"))
        res_layout = QHBoxLayout()
        res_layout.setSpacing(10)
        
        self.width_input = QLineEdit()
        self.width_input.setValidator(QIntValidator(1, 10000))
        self.width_input.setStyleSheet(style.LOGIN_INPUT)
        curr_w = self.session.db.get_setting("default_width", default=str(config.DEFAULT_FRAME_WIDTH))
        self.width_input.setText(str(curr_w))
        
        x_lbl = QLabel("x")
        x_lbl.setStyleSheet("color: #888; font-weight: bold; font-size: 14px;")
        
        self.height_input = QLineEdit()
        self.height_input.setValidator(QIntValidator(1, 10000))
        self.height_input.setStyleSheet(style.LOGIN_INPUT)
        curr_h = self.session.db.get_setting("default_height", default=str(config.DEFAULT_FRAME_HEIGHT))
        self.height_input.setText(str(curr_h))
        
        res_layout.addWidget(self.width_input)
        res_layout.addWidget(x_lbl)
        res_layout.addWidget(self.height_input)
        res_layout.addStretch() 
        layout.addLayout(res_layout)

        # --- Section 2: Software Settings ---
        
        # --- بخش مدیریت لیست‌ها (نرم‌افزار و رندر) ---
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #444; margin: 10px 0;")
        layout.addWidget(line)

        # فیلد لیست نرم‌افزارها
        layout.addWidget(QLabel("Allowed Softwares (Comma Separated):"))
        self.sw_list_input = QLineEdit()
        self.sw_list_input.setPlaceholderText("e.g. all, 3ds Max, Blender, Maya")
        self.sw_list_input.setStyleSheet(style.INPUT_STYLE)
        current_sw = self.session.db.get_setting("allowed_softwares_list", default="all, 3ds Max, Blender, Maya, Unreal")
        self.sw_list_input.setText(current_sw)
        layout.addWidget(self.sw_list_input)

        # فیلد لیست موتورهای رندر
        layout.addWidget(QLabel("Render Engines (Comma Separated):"))
        self.engine_list_input = QLineEdit()
        self.engine_list_input.setPlaceholderText("e.g. V-Ray, Octane, Redshift")
        self.engine_list_input.setStyleSheet(style.INPUT_STYLE)
        current_engines = self.session.db.get_setting("render_engines_list", default="--------, V-Ray, Octane, Cycles, Arnold, Redshift")
        self.engine_list_input.setText(current_engines)
        layout.addWidget(self.engine_list_input)

        # --- Section 3: Folder Structure (NEW ADDITION) ---
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #444; margin: 10px 0;")
        layout.addWidget(line)

        # 1. Project Structure
        layout.addWidget(QLabel("Project Folders Structure (JSON List):"))
        layout.addWidget(QLabel("Example: [\"Assets\", \"Sequences\"]", styleSheet="color:#777; font-size:10px;"))
        self.proj_struct_edit = QTextEdit()
        self.proj_struct_edit.setFixedHeight(80)
        self.proj_struct_edit.setStyleSheet(style.INPUT_STYLE)
        layout.addWidget(self.proj_struct_edit)

        # 2. Asset Structure (اضافه شد!)
        layout.addWidget(QLabel("Asset Folders Structure (JSON Dict):"))
        layout.addWidget(QLabel("Example: {\"work\": {\"3D\": [\"model\"]}, \"publish\": {\"2D\": [\"texture\"]}}", styleSheet="color:#777; font-size:10px;"))
        self.asset_struct_edit = QTextEdit()
        self.asset_struct_edit.setFixedHeight(120)
        self.asset_struct_edit.setStyleSheet(style.INPUT_STYLE)
        layout.addWidget(self.asset_struct_edit)

        # 3. Shot Structure
        layout.addWidget(QLabel("Shot Folders Structure (JSON Dict):"))
        layout.addWidget(QLabel("Example: {\"work\": {\"3D\": [\"layout\"]}, \"publish\": {\"2D\": [\"nuke\"]}}", styleSheet="color:#777; font-size:10px;"))
        self.shot_struct_edit = QTextEdit()
        self.shot_struct_edit.setFixedHeight(120)
        self.shot_struct_edit.setStyleSheet(style.INPUT_STYLE)
        layout.addWidget(self.shot_struct_edit)

        # لود کردن اطلاعات جیسون داخل باکس‌ها
        self.load_folder_config()

        layout.addStretch()

        # دکمه ذخیره
        btn_save = QPushButton("Save Config")
        btn_save.setFixedWidth(150)
        btn_save.setFixedHeight(40)
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet(style.ADMIN_SAVE_BTN)
        btn_save.clicked.connect(self.save_admin_config)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def load_folder_config(self):
        """
        Handle Load Folder Config operation.
        """
        # خواندن تنظیمات فولدر و نمایش در تکست‌باکس‌ها
        proj_data = FileSystemManager.get_project_structure(self.session.db)
        asset_data = FileSystemManager.get_asset_structure(self.session.db) # اضافه شد
        shot_data = FileSystemManager.get_shot_structure(self.session.db)
        
        self.proj_struct_edit.setText(json.dumps(proj_data, indent=4))
        self.asset_struct_edit.setText(json.dumps(asset_data, indent=4)) # اضافه شد
        self.shot_struct_edit.setText(json.dumps(shot_data, indent=4))

    def save_admin_config(self):
        """
        Handle Save Admin Config operation.
        """
        # 1. گرفتن مقادیر عمومی
        new_path = self.path_input.text()
        new_fps = self.fps_combo.currentText()
        new_w = self.width_input.text()
        new_h = self.height_input.text()
        new_sw_list = self.sw_list_input.text() 
        new_engine_list = self.engine_list_input.text()
        
        # 2. گرفتن مقادیر جیسون
        proj_text = self.proj_struct_edit.toPlainText()
        asset_text = self.asset_struct_edit.toPlainText() # اضافه شد
        shot_text = self.shot_struct_edit.toPlainText()

        # اعتبارسنجی
        if not new_path or not new_w or not new_h:
            QMessageBox.warning(self, "Error", "General fields cannot be empty.")
            return

        try:
            # تست می‌کنیم که آیا متن وارد شده جیسون معتبر است؟
            json.loads(proj_text)
            json.loads(asset_text) # اضافه شد
            json.loads(shot_text)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Syntax Error", f"Invalid JSON format!\n{e}")
            return
            
        # ذخیره همه تنظیمات در دیتابیس
        self.session.db.set_setting("server_path", new_path)
        self.session.db.set_setting("global_fps", new_fps)
        self.session.db.set_setting("default_width", new_w)
        self.session.db.set_setting("default_height", new_h)
        self.session.db.set_setting("project_structure", proj_text)
        self.session.db.set_setting("asset_structure", asset_text)  # اضافه شد
        self.session.db.set_setting("shot_structure", shot_text)       
        self.session.db.set_setting("allowed_softwares_list", new_sw_list)
        self.session.db.set_setting("render_engines_list", new_engine_list)
        
        QMessageBox.information(self, "Success", "Admin configurations saved to database.")
    #-------------------
    # Profile Tab
    #-------------------
    def setup_profile_tab(self):
        """
        Handle Setup Profile Tab operation.
        """
        layout = QVBoxLayout(self.profile_tab)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        layout.addWidget(QLabel("Full Name:"))
        self.name_input = QLineEdit(self.user.full_name)
        self.name_input.setStyleSheet(style.LOGIN_INPUT)
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("Username (Cannot be changed):"))
        user_input = QLineEdit(self.user.username)
        user_input.setReadOnly(True)
        user_input.setStyleSheet(style.PROFILE_READONLY_INPUT)
        layout.addWidget(user_input)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(style.SEPARATOR_LINE)
        layout.addWidget(line)

        layout.addWidget(QLabel("New Password (Leave empty to keep current):"))
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_input.setPlaceholderText("Enter new password")
        self.pass_input.setStyleSheet(style.LOGIN_INPUT)
        layout.addWidget(self.pass_input)

        layout.addWidget(QLabel("Confirm New Password:"))
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.setPlaceholderText("Repeat new password")
        self.confirm_input.setStyleSheet(style.LOGIN_INPUT)
        layout.addWidget(self.confirm_input)

        layout.addStretch()

        btn_save = QPushButton("Save Changes")
        btn_save.setFixedWidth(150)
        btn_save.setFixedHeight(40)
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet(style.LOGIN_BTN)
        btn_save.clicked.connect(self.save_profile)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def save_profile(self):
        """
        Handle Save Profile operation.
        """
        new_name = self.name_input.text()
        new_pass = self.pass_input.text()
        confirm_pass = self.confirm_input.text()
        
        if not new_name:
            QMessageBox.warning(self, "Error", "Name cannot be empty.")
            return

        if new_pass and new_pass != confirm_pass:
            QMessageBox.warning(self, "Error", "Passwords do not match!")
            return
        
        success = self.session.db.update_user_profile_safe(
            self.user.id, new_name, new_pass if new_pass else None
        )

        if success:
            QMessageBox.information(self, "Success", "Profile updated successfully!\nChanges applied on next login.")
            self.user.full_name = new_name
        else:
            QMessageBox.critical(self, "Error", "Failed to update profile.")


    # ----------------------------------------
    # TAB 2: UTILITIES (Local Settings) [NEW]
    # ----------------------------------------
    def setup_utility_tab(self):
        """
        اضافه کردن تمام نرم‌افزارهای سه‌بعدی، ادیت، موشن‌گرافیک، کامپوزیت و دو‌بعدی 
        به تنظیمات لوکال جهت استفاده در لانچر کورتکس.
        """
        layout = QVBoxLayout(self.utility_tab)
        layout.setSpacing(8) # فاصله کمتر برای جا شدن تمام موارد در صفحه
        layout.setContentsMargins(30, 20, 30, 20)
        
        info = QLabel("These settings are saved locally on this computer's registry.")
        info.setStyleSheet("color: #888; font-style: italic; margin-bottom: 5px;")
        layout.addWidget(info)
        
        layout.addWidget(QLabel("Local Software Executable Paths:", 
                               styleSheet="color:#007acc; font-weight:bold; font-size:14px;"))

        # استفاده از QSettings برای ذخیره در رجیستری ویندوز (Cortex/Pipeline)
        self.local_settings = QSettings("Cortex", "Pipeline")
        
        # دسته‌بندی نرم‌افزارهای شما برای نظم بهتر در لیست
        softwares = [
            ("--- 3D SOFTWARE ---", None),
            ("3ds Max", "max_path"),
            ("Maya", "maya_path"),
            ("Blender", "blender_path"),
            ("Houdini", "houdini_path"),
            
            ("--- COMPOSITING & VFX ---", None),
            ("Nuke", "nuke_path"),
            ("Natron", "natron_path"),
            
            ("--- EDIT & MOTION ---", None),
            ("After Effects", "ae_path"),
            ("Premiere Pro", "premiere_path"),
            ("DaVinci Resolve", "davinci_path"),
            
            ("--- 2D & TEXTURE ---", None),
            ("Photoshop", "photoshop_path"),
            ("GIMP", "gimp_path")
        ]

        self.path_inputs = {} # دیکشنری برای ذخیره رفرنس فیلدها

        for label, key in softwares:
            if key is None:
                # این یک جداکننده (Header) است
                header = QLabel(label)
                header.setStyleSheet("color: #555; font-weight: bold; margin-top: 10px; border-bottom: 1px solid #333;")
                layout.addWidget(header)
                continue

            layout.addWidget(QLabel(f"{label} Path (.exe):"))
            path_layout = QHBoxLayout()
            
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(f"Select {label} executable file...")
            line_edit.setStyleSheet(style.LOGIN_INPUT)
            # لود کردن مقدار ذخیره شده قبلی
            line_edit.setText(self.local_settings.value(key, ""))
            
            btn_browse = QPushButton("...")
            btn_browse.setFixedWidth(40)
            btn_browse.setCursor(Qt.PointingHandCursor)
            # اتصال دکمه براوز به فیلد مربوطه
            btn_browse.clicked.connect(lambda checked=False, le=line_edit: self.browse_exe(le))
            
            path_layout.addWidget(line_edit)
            path_layout.addWidget(btn_browse)
            layout.addLayout(path_layout)
            
            self.path_inputs[key] = line_edit

        layout.addStretch()

        # دکمه ذخیره نهایی
        btn_save = QPushButton("💾 SAVE ALL SOFTWARE PATHS")
        btn_save.setFixedHeight(45)
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet(style.BTN_SUCCESS) # استفاده از استایل سبز برای تایید
        btn_save.clicked.connect(self.save_utility_settings)
        layout.addWidget(btn_save)

    def save_utility_settings(self):
        """ذخیره تمام مسیرهای وارد شده در رجیستری سیستم"""
        for key, line_edit in self.path_inputs.items():
            self.local_settings.setValue(key, line_edit.text())
        
        QMessageBox.information(self, "Success", "All software paths have been updated locally.")

    def browse_exe(self, line_edit):
        """
        Handle Browse Exe operation.
        """
        path, _ = QFileDialog.getOpenFileName(self, "Select Executable", filter="Executable (*.exe)")
        if path:
            line_edit.setText(path)

    

    #-------------------
    # About Tab
    #-------------------
    def setup_about_tab(self):
        """
        Handle Setup About Tab operation.
        """
        layout = QVBoxLayout(self.about_tab)
        layout.setAlignment(Qt.AlignCenter)
        
        logo = QLabel(config.APP_NAME) 
        logo.setStyleSheet(style.ABOUT_LOGO)
        layout.addWidget(logo)
        
        version = QLabel(f"Version {config.VERSION}")
        version.setStyleSheet(style.ABOUT_VERSION)
        layout.addWidget(version)
        
        current_year = datetime.datetime.now().year
        desc_text = (
            f"{config.APP_NAME} is a specialized project management tool\n"
            "designed for Animation and VFX studios.\n\n"
            f"Developed by: {config.DEVELOPER}\n"
            f"© {current_year} All Rights Reserved."
        )
        desc = QLabel(desc_text)
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet(style.ABOUT_TEXT)
        layout.addWidget(desc)
        
        if hasattr(config, 'GITHUB'):
            github_lbl = QLabel(f"<a href='{config.GITHUB}' style='color:#007acc;'>Check updates on GitHub</a>")
            github_lbl.setOpenExternalLinks(True)
            github_lbl.setAlignment(Qt.AlignCenter)
            layout.addWidget(github_lbl)

        layout.addStretch()