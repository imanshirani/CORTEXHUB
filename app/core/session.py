import json
import os
from app.core.models import Context
from app.core.database import DatabaseManager

class SessionManager:
    _instance = None  # نگهداری تنها نمونه کلاس (Singleton)

    def __new__(cls):
        """
        این متد تضمین می‌کند فقط یک SessionManager در کل برنامه وجود دارد.
        همچنین دیتابیس فقط یک بار وصل می‌شود.
        """
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
            
            # --- شروع: کدهای راه‌اندازی (فقط یکبار اجرا می‌شوند) ---
            cls._instance.db = DatabaseManager()
            cls._instance.context = Context()
            # --- پایان ---
            
        return cls._instance

    def login(self, username, password):
        """استفاده از دیتابیس برای لاگین"""
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

    