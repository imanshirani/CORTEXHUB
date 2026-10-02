from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QListWidget, QListWidgetItem, QStackedWidget, QLabel, 
                               QPushButton, QMessageBox,QApplication)
from PySide6.QtCore import Qt
from app.core import config
from app.ui import style
from app.ui.components.sidebar import Sidebar
# Import pages
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
        self.setStyleSheet(style.DARK_THEME) # General style
        
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
        # The order should be exactly like the sidebar:
        self.stack.addWidget(self.dashboard_view)  # Index 0
        self.stack.addWidget(self.projects_view)   # Index 1
        self.stack.addWidget(self.assets_view)     # Index 2 (new)
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
        
        # Refresh data when entering the page (optional but recommended)
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
        self.logout_requested = True # <--- This is the life line
        self.close()

    def setup_sidebar(self):
        """Create a left menu with an exit button"""
        sidebar_container = QWidget()
        sidebar_container.setFixedWidth(220) # A little wider for beauty
        sidebar_container.setStyleSheet(style.SIDEBAR_CONTAINER)
        
        sidebar_layout = QVBoxLayout(sidebar_container)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        
        # A) Logo
        app_logo = QLabel(f"{config.APP_NAME}")
        app_logo.setStyleSheet(style.SIDEBAR_LOGO)
        app_logo.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(app_logo)

        # b) List of menus
        self.menu_list = QListWidget()
        self.menu_list.setStyleSheet(style.SIDEBAR_MENU)
        self.menu_list.currentRowChanged.connect(self.switch_view) # Connect to change page
        sidebar_layout.addWidget(self.menu_list)
        
        # c) Spacer to push the exit button down
        sidebar_layout.addStretch()

        # D) Exit button
        self.btn_logout = QPushButton("Logout")
        self.btn_logout.setCursor(Qt.PointingHandCursor)
        self.btn_logout.setStyleSheet(style.LOGOUT_BUTTON)
        self.btn_logout.clicked.connect(self.do_logout) # Connect exit function
        sidebar_layout.addWidget(self.btn_logout)
        
        # Add the entire left column to the main layout
        self.layout.addWidget(sidebar_container)

    def init_views(self):
        """Creating pages based on user access"""
        # Everyone has a dashboard
        self.dashboard_view = DashboardView(self.session)
        self.add_menu_item("Dashboard", self.dashboard_view)

        # Administrative access
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
        # Select the default front page
        self.menu_list.setCurrentRow(0)

    def add_menu_item(self, name, widget):
        """
        Handle Add Menu Item operation.
        """
        self.menu_list.addItem(name)
        self.stack.addWidget(widget)

    def switch_view(self, index):
        """Change page in StackedWidget"""
        self.content_area.setCurrentIndex(index)

    def do_logout(self):
        """Request to exit and close the window"""
        confirm = QMessageBox.question(self, "Logout", "Are you sure you want to logout?", 
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.logout_requested = True # signal to main.py
            self.close()

    def navigate_to_task(self, task_id, entity_type, entity_id):
        """Changing the tab and automatically jumping to the selected task in the dashboard"""
        # 1. Get the context (complete information about the project path) from the database
        ctx = self.session.db.get_task_context_data(task_id)
        if not ctx: return

        if entity_type == "Shot":
            # Go to the Production tab (index 3)
            self.switch_page(3)
            # Calling the jump method inside the page itself
            self.production_view.jump_to_task(ctx)
            
        elif entity_type == "Asset":
            # Go to the Assets tab (Index 2)
            self.switch_page(2)
            # Calling the jump method inside the page itself
            self.assets_view.jump_to_task(ctx)