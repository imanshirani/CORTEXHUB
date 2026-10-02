import json
import os
from app.core.models import Context
from app.core.database import DatabaseManager

class SessionManager:
    _instance = None  # Maintaining a single class instance (Singleton)

    def __new__(cls):
        """
        This method ensures that there is only one SessionManager in the entire application.
        Also, the database is connected only once.
        """
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
            
            # --- Start: startup codes (run only once) ---
            cls._instance.db = DatabaseManager()
            cls._instance.context = Context()
            # --- the end ---
            
        return cls._instance

    def login(self, username, password):
        """Using database for login"""
        if self.db.check_password(username, password):
            user = self.db.get_user_by_username(username)
            self.context.user = user
            print(f"Logged in successfully: {user.full_name}")
            return True
        return False

    def get_projects(self):
        """
        Handle Get Projects operation.
        """
        return self.db.get_all_projects()

    def set_active_project(self, project_id):
        """
        Handle Set Active Project operation.
        """
        projects = self.get_projects()
        for proj in projects:
            if proj.id == project_id:
                self.context.project = proj
                return proj
        return None

    