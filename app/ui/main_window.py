from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QListWidget, QListWidgetItem, QStackedWidget, QLabel, 
                               QPushButton, QMessageBox,QApplication)
from PySide6.QtCore import Qt
from app.core import config
from app.ui import style
from app.ui.components.sidebar import Sidebar
# ایمپورت صفحات
from app.ui.views.dashboard_view import DashboardView
from app.ui.views.users_view import UsersView
from app.ui.views.projects_view import ProjectsView
from app.ui.views.studio_view import StudioView
from app.ui.views.production_view import ProductionView
from app.ui.views.settings_view import SettingsView
from app.ui.views.assets_view import AssetsView
from app.ui.views.validation_view import ValidationView
from app.ui.views.naming_standard_view import NamingStandardView

class MainWindow(QMainWindow):
    def __init__(self, session):
        """
        Handle   Init   operation.
        """
        super().__init__()
        self.session = session
        self.logout_requested = False
        self.setWindowTitle("Cortex Pipeline")
        screen = QApplication.primaryScreen().geometry()
        screen = QApplication.primaryScreen().availableGeometry()
        width = 1280
        height = int(screen.height() * 0.85)
        self.resize(width, height)
        self.setMinimumSize(1000, 600)
        self.setStyleSheet(style.DARK_THEME) # استایل کلی
        
        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. Sidebar
        self.sidebar = Sidebar(session.context.user.role)
        self.sidebar.page_changed.connect(self.switch_page)
        self.sidebar.btn_logout.clicked.connect(self.logout)
        main_layout.addWidget(self.sidebar)
        
        # 2. Content Area (Stacked Widget)
        self.stack = QStackedWidget()
        
        # --- Create Views ---
        self.dashboard_view = DashboardView(session)
        self.projects_view = ProjectsView(session)
        self.assets_view = AssetsView(session)         
        self.production_view = ProductionView(session)
        self.studio_view = StudioView(session)
        self.users_view = UsersView(session)
        self.settings_view = SettingsView(session)
        self.validation_view = ValidationView(self.session, project_id=None)
        self.naming_view = NamingStandardView(self.session, project_id=None)

        self.dashboard_view.go_to_task_signal.connect(self.navigate_to_task)

        # --- Add to Stack (ORDER MATTERS!) ---
        # ترتیب باید دقیقاً مثل سایدبار باشد:
        self.stack.addWidget(self.dashboard_view)  # Index 0
        self.stack.addWidget(self.projects_view)   # Index 1
        self.stack.addWidget(self.assets_view)     # Index 2 (جدید)
        self.stack.addWidget(self.production_view) # Index 3
        self.stack.addWidget(self.studio_view)     # Index 4
        self.stack.addWidget(self.users_view)      # Index 5
        self.stack.addWidget(self.settings_view)   # Index 6        
        self.stack.addWidget(self.validation_view) # Index 7
        self.stack.addWidget(self.naming_view)     # Index 8

        
        
        
        main_layout.addWidget(self.stack)

    def switch_page(self, index):
        """
        Handle Switch Page operation.
        """
        self.stack.setCurrentIndex(index)
        
        # رفرش کردن دیتا وقتی وارد صفحه می‌شویم (اختیاری ولی پیشنهادی)
        if index == 1: # Projects
            self.projects_view.load_projects()
        elif index == 2: # Assets
            self.assets_view.refresh_project_list()
        elif index == 3: # Production
            self.production_view.refresh_project_list()
        elif index == 4: # Studio
            self.studio_view.load_depts()
        elif index == 5: # Users
            self.users_view.load_users()

    def logout(self):
        """
        Handle Logout operation.
        """
        self.logout_requested = True # <--- این خط حیاتی است
        self.close()

    def setup_sidebar(self):
        """ساخت منوی سمت چپ با دکمه خروج"""
        sidebar_container = QWidget()
        sidebar_container.setFixedWidth(220) # کمی عریض‌تر برای زیبایی
        sidebar_container.setStyleSheet(style.SIDEBAR_CONTAINER)
        
        sidebar_layout = QVBoxLayout(sidebar_container)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        
        # الف) لوگو
        app_logo = QLabel(f"{config.APP_NAME}")
        app_logo.setStyleSheet(style.SIDEBAR_LOGO)
        app_logo.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(app_logo)

        # ب) لیست منوها
        self.menu_list = QListWidget()
        self.menu_list.setStyleSheet(style.SIDEBAR_MENU)
        self.menu_list.currentRowChanged.connect(self.switch_view) # اتصال به تغییر صفحه
        sidebar_layout.addWidget(self.menu_list)
        
        # ج) فاصله انداز (Spacer) برای هل دادن دکمه خروج به پایین
        sidebar_layout.addStretch()

        # د) دکمه خروج
        self.btn_logout = QPushButton("Logout")
        self.btn_logout.setCursor(Qt.PointingHandCursor)
        self.btn_logout.setStyleSheet(style.LOGOUT_BUTTON)
        self.btn_logout.clicked.connect(self.do_logout) # اتصال عملکرد خروج
        sidebar_layout.addWidget(self.btn_logout)
        
        # اضافه کردن کل ستون سمت چپ به لایوت اصلی
        self.layout.addWidget(sidebar_container)

    def init_views(self):
        """ساخت صفحات بر اساس دسترسی کاربر"""
        # همه داشبورد را دارند
        self.dashboard_view = DashboardView(self.session)
        self.add_menu_item("Dashboard", self.dashboard_view)

        # دسترسی‌های مدیریتی
        if self.user.role in ["admin", "supervisor"]:
            self.projects_view = ProjectsView(self.session)
            self.add_menu_item("Projects Manager", self.projects_view)
            
            self.prod_view = ProductionView(self.session)
            self.add_menu_item("Production Tracker", self.prod_view)

        if self.user.role == "admin":
            self.studio_view = StudioView(self.session)
            self.add_menu_item("Studio & Depts", self.studio_view)
            self.validation_view = ValidationView(self.session, project_id=None)
            self.add_menu_item("Validation Rules", self.validation_view)
            
            self.users_view = UsersView(self.session)
            self.add_menu_item("User Management", self.users_view)

        if hasattr(self, 'projects_view') and hasattr(self, 'validation_view'):
            self.projects_view.project_selected.connect(self.validation_view.set_project)

        self.settings_view = SettingsView(self.session)
        self.add_menu_item("Settings", self.settings_view)
        # انتخاب پیش‌فرض صفحه اول
        self.menu_list.setCurrentRow(0)

    def add_menu_item(self, name, widget):
        """
        Handle Add Menu Item operation.
        """
        self.menu_list.addItem(name)
        self.stack.addWidget(widget)

    def switch_view(self, index):
        """تغییر صفحه در StackedWidget"""
        self.content_area.setCurrentIndex(index)

    def do_logout(self):
        """درخواست خروج و بستن پنجره"""
        confirm = QMessageBox.question(self, "Logout", "Are you sure you want to logout?", 
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.logout_requested = True # سیگنال به main.py
            self.close()

    def navigate_to_task(self, task_id, entity_type, entity_id):
        """تغییر تب و پرش اتوماتیک به تسک انتخاب شده در داشبورد"""
        # 1. دریافت کانتکست (اطلاعات کامل مسیر پروژه) از دیتابیس
        ctx = self.session.db.get_task_context_data(task_id)
        if not ctx: return

        if entity_type == "Shot":
            # رفتن به تب Production (ایندکس 3)
            self.switch_page(3)
            # فراخوانی متد پرش در داخل خود صفحه
            self.production_view.jump_to_task(ctx)
            
        elif entity_type == "Asset":
            # رفتن به تب Assets (ایندکس 2)
            self.switch_page(2)
            # فراخوانی متد پرش در داخل خود صفحه
            self.assets_view.jump_to_task(ctx)