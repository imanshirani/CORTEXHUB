import sqlite3
import uuid
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "cortex.db")

class DatabaseManager:
    """
    Core database controller for the Cortex Pipeline.
    Manages connections to SQLite (local) or PostgreSQL (server) backends.
    """

    def __init__(self):
        """
        Handle   Init   operation.
        """
        from app.core import config
        
        # 1. ابتدا بر اساس کانفیگ متصل شو
        if config.DB_TYPE == "postgres":
            try:
                import psycopg2
                self.conn = psycopg2.connect(**config.DB_CONFIG)
                self.cursor = self.conn.cursor() # <--- اول تعریف کرسر
                print(">> [Cortex] Connected to PostgreSQL Server.")
            except ImportError:
                print("!! [Error] psycopg2 not found.")
                return
        else:
            self.conn = sqlite3.connect(DB_PATH)
            self.cursor = self.conn.cursor() # <--- اول تعریف کرسر
            print(f">> [Cortex] Using Local SQLite: {DB_PATH}")
        
        # 2. حالا که کرسر ساخته شده، بقیه کارها را انجام بده
        self.create_tables()
        self.perform_migrations()
        self.create_indexes() # <--- حالا این خط بدون ارور اجرا می‌شود
        self.seed_data()

    def create_tables(self):
        """ساخت جداول پایه (فقط اگر وجود نداشته باشند اجرا می‌شود)"""
        # Departments
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS departments (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE,
                color TEXT
            )
        """)
        
        # Users
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE,
                password TEXT,
                full_name TEXT,
                role TEXT
                -- ستون department_id را اینجا نمی‌گذاریم تا Migration تست شود
                -- یا اگر دیتابیس جدید است، خود Migration اضافه‌اش می‌کند
            )
        """)

        # Projects
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT,
                code TEXT,
                root_path TEXT,
                status TEXT DEFAULT 'Active',
                render_engine TEXT,
                software TEXT
            )
        """)

        # --- FIX: جدول اعضای پروژه (که باعث ارور شده بود) ---
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_members (
                project_id TEXT,
                user_id TEXT,
                permission TEXT DEFAULT 'edit',
                PRIMARY KEY (project_id, user_id),
                FOREIGN KEY(project_id) REFERENCES projects(id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        # Sequences
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sequences (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                name TEXT,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            )
        """)

        # Shots
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS shots (
                id TEXT PRIMARY KEY,
                sequence_id TEXT,
                name TEXT,
                frame_start INTEGER DEFAULT 1001,
                frame_end INTEGER DEFAULT 1100,
                status TEXT DEFAULT 'Not Started',
                FOREIGN KEY(sequence_id) REFERENCES sequences(id)
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS shot_assets (
                shot_id TEXT,
                asset_id TEXT,
                PRIMARY KEY (shot_id, asset_id),
                FOREIGN KEY(shot_id) REFERENCES shots(id),
                FOREIGN KEY(asset_id) REFERENCES assets(id)
            )
        """)

        # Tasks        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                entity_id TEXT,
                entity_type TEXT,
                department_id TEXT,   -- دقت کنید: department_id
                assignee_id TEXT,
                title TEXT,           
                description TEXT,     
                status TEXT DEFAULT 'Todo',
                start_date TEXT,      -- NEW: تاریخ شروع
                due_date TEXT,        -- NEW: تاریخ تحویل (ددلاین)
                estimated_hours REAL, -- NEW: زمان تخمینی
                FOREIGN KEY(department_id) REFERENCES departments(id),
                FOREIGN KEY(assignee_id) REFERENCES users(id)
            )
        """)

        # Assets
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                name TEXT,
                category TEXT,
                status TEXT,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            )
        """)

        # Settings
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # Publishes
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS publishes (
                id TEXT PRIMARY KEY,
                task_id TEXT,
                version INTEGER,
                
                comment TEXT,
                created_by TEXT,       -- نام یوزر
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                thumbnail_path TEXT,   -- مسیر عکس تامنیل
                
                FOREIGN KEY(task_id) REFERENCES tasks(id)
            )
        """)

        # جدول فایل‌های خروجی
        # چرا جدا؟ چون یک پابلیش ممکن است ۱۰ تا فایل تولید کند (Alembic, Max, MP4, Texture, ...)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS published_files (
                id TEXT PRIMARY KEY,
                publish_id TEXT,
                
                file_type TEXT,        -- مثلا: 'source_max', 'alembic_cache', 'preview_mov', 'render_pass'
                file_path TEXT,        -- مسیر فایل روی هارد
                
                FOREIGN KEY(publish_id) REFERENCES publishes(id)
            )
        """)

        # validates ruls
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS validation_rules (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                software TEXT,        
                rule_key TEXT,        
                rule_script TEXT,     -- این ستون برای ذخیره کدهای پایتون حیاتی است
                is_active INTEGER DEFAULT 1,
                is_mandatory INTEGER DEFAULT 1,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            )
        """)

        # Naming Conventions
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS naming_conventions (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                category TEXT,         -- Characters, Props, etc.
                prefix TEXT,           -- e.g. 'CHR_'
                suffix TEXT,           -- e.g. '_GEO'
                required_objects TEXT, -- e.g. 'Head,Body,L_Eye,R_Eye' (comma separated)
                FOREIGN KEY(project_id) REFERENCES projects(id)
            )
        """)

        self.cursor.execute("""
                    CREATE TABLE IF NOT EXISTS naming_standards (
                        id TEXT PRIMARY KEY,
                        project_id TEXT,        -- این ستون جا افتاده بود
                        category TEXT,          
                        prefix TEXT,            
                        suffix TEXT,            
                        required_hierarchy TEXT,
                        FOREIGN KEY(project_id) REFERENCES projects(id)
                    )
                """)

        self.conn.commit()

    def create_indexes(self):
        """ساخت ایندکس‌های حیاتی برای حفظ سرعت در پروژه‌های بزرگ"""
        try:
            # ایندکس روی موجودیت‌ها (برای لود سریع تسک‌های شات/است)
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_entity ON tasks(entity_id)")
            # ایندکس روی یوزرها (برای لود سریع داشبورد شخصی)
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_assignee ON tasks(assignee_id)")
            # ایندکس روی تاریخ‌ها (برای گزارش‌گیری سریع ددلاین‌ها در آینده)
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_due ON tasks(due_date)")
            
            self.conn.commit()
            print(">> [Cortex] Database Indexes verified.")
        except Exception as e:
            print(f"!! [Warning] Index creation failed: {e}")

    def perform_migrations(self):
        """بررسی و تعمیر هوشمند ساختار جداول"""
        
        # --- 1. بررسی جدول TASKS ---
        self.cursor.execute("PRAGMA table_info(tasks)")
        columns_info = self.cursor.fetchall()
        columns = [info[1] for info in columns_info]
        
        # A. تبدیل dept_id به department_id
        if "department_id" not in columns:
            print("Migration: Adding 'department_id' to tasks...")
            self.cursor.execute("ALTER TABLE tasks ADD COLUMN department_id TEXT")
        
        # اگر ستون قدیمی dept_id وجود دارد، اطلاعاتش را منتقل کن
        if "dept_id" in columns:
            print("Migration: Transferring data from dept_id to department_id...")
            # این کوئری فقط جاهایی که department_id خالی است را پر می‌کند
            self.cursor.execute("UPDATE tasks SET department_id = dept_id WHERE department_id IS NULL")

        # B. تبدیل shot_id به entity_id
        if "entity_id" not in columns:
            print("Migration: Adding 'entity_id' to tasks...")
            self.cursor.execute("ALTER TABLE tasks ADD COLUMN entity_id TEXT")
        
        if "shot_id" in columns:
            print("Migration: Transferring data from shot_id to entity_id...")
            self.cursor.execute("UPDATE tasks SET entity_id = shot_id WHERE entity_id IS NULL")

        # C. اضافه کردن سایر ستون‌های جدید
        if "entity_type" not in columns:
            self.cursor.execute("ALTER TABLE tasks ADD COLUMN entity_type TEXT DEFAULT 'Shot'")
            
        if "assignee_id" not in columns:
            self.cursor.execute("ALTER TABLE tasks ADD COLUMN assignee_id TEXT")
            
        if "title" not in columns:
            self.cursor.execute("ALTER TABLE tasks ADD COLUMN title TEXT")
            
        if "description" not in columns:
            self.cursor.execute("ALTER TABLE tasks ADD COLUMN description TEXT")

        # --- D. اضافه کردن ستون‌های زمان‌بندی (مایگریشن جدید) ---
        if "start_date" not in columns:
            print("Migration: Adding 'start_date' to tasks...")
            self.cursor.execute("ALTER TABLE tasks ADD COLUMN start_date TEXT")
            
        if "due_date" not in columns:
            print("Migration: Adding 'due_date' to tasks...")
            self.cursor.execute("ALTER TABLE tasks ADD COLUMN due_date TEXT")
            
        if "estimated_hours" not in columns:
            print("Migration: Adding 'estimated_hours' to tasks...")
            self.cursor.execute("ALTER TABLE tasks ADD COLUMN estimated_hours REAL")

        # --- 2. بررسی جدول USERS ---
        self.cursor.execute("PRAGMA table_info(users)")
        user_cols = [info[1] for info in self.cursor.fetchall()]
        if "department_id" not in user_cols:
            self.cursor.execute("ALTER TABLE users ADD COLUMN department_id TEXT")

        # --- بررسی جدول PROJECTS ---
        self.cursor.execute("PRAGMA table_info(projects)")
        proj_columns = [info[1] for info in self.cursor.fetchall()]
        
        if "status" not in proj_columns:
            self.cursor.execute("ALTER TABLE projects ADD COLUMN status TEXT DEFAULT 'Active'")

        # --- اضافه کردن ستون‌های جدید ---
        if "render_engine" not in proj_columns:
            print("Migration: Adding 'render_engine'...")
            self.cursor.execute("ALTER TABLE projects ADD COLUMN render_engine TEXT DEFAULT '--------'")
            
        if "software" not in proj_columns:
            print("Migration: Adding 'software'...")
            self.cursor.execute("ALTER TABLE projects ADD COLUMN software TEXT DEFAULT '--------'")

        # --- بررسی و آپدیت جدول DEPARTMENTS برای قفل‌ها ---
        self.cursor.execute("PRAGMA table_info(departments)")
        dept_cols = [info[1] for info in self.cursor.fetchall()]
        
        if "allowed_software" not in dept_cols:
            print(">> [Migration] Adding 'allowed_software' to departments...")
            self.cursor.execute("ALTER TABLE departments ADD COLUMN allowed_software TEXT DEFAULT 'all'")
            
        if "render_engine" not in dept_cols:
            print(">> [Migration] Adding 'render_engine' to departments...")
            self.cursor.execute("ALTER TABLE departments ADD COLUMN render_engine TEXT DEFAULT '--------'")

        # 1. Migration مربوط به validation_rules (نگه دارید)
        try:
            self.cursor.execute("PRAGMA table_info(validation_rules)")
            val_columns = [info[1] for info in self.cursor.fetchall()]
            
            if "rule_script" not in val_columns:
                self.cursor.execute("ALTER TABLE validation_rules ADD COLUMN rule_script TEXT")
                self.conn.commit()
            
            if "is_mandatory" not in val_columns:
                self.cursor.execute("ALTER TABLE validation_rules ADD COLUMN is_mandatory INTEGER DEFAULT 1")
                self.conn.commit()
        except Exception as e:
            print(f"!! Migration Failed (Validation Rules): {e}")

        # 2. Migration مربوط به naming_standards (اضافه کنید)
        try:
            self.cursor.execute("PRAGMA table_info(naming_standards)")
            columns = [info[1] for info in self.cursor.fetchall()]
            if "project_id" not in columns:
                print(">> [Migration] Adding 'project_id' to naming_standards...")
                self.cursor.execute("ALTER TABLE naming_standards ADD COLUMN project_id TEXT")
                self.conn.commit()
        except Exception as e:
            print(f"!! Migration Error (Naming Standards): {e}")

    def seed_data(self):
        """فقط اگر هیچ یوزری در دیتابیس نبود، یوزر اولیه را بساز"""
        self.cursor.execute("SELECT COUNT(*) FROM users")
        if self.cursor.fetchone()[0] == 0:
            # دیتابیس خالی است، پس یوزر اولیه را بساز
            self.cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)",
                                ("u1", "iman", "1234", "Iman Shirani", "admin", None))

            self.cursor.execute("INSERT INTO projects VALUES (?, ?, ?, ?, ?, ?, ?)",
                                ("p1", "Project Titan", "TTN", r"D:\Projects\Titan", "Active", "Octane", "3ds Max"))

            self.conn.commit()
            print("--- Database Initialized with Default User ---")

    # --- بقیه توابع کمکی (CRUD) ---

    def get_user_by_username(self, username):
        """
        Handle Get User By Username operation.
        """
        # نیاز به ایمپورت مدل‌ها در بالای فایل نیست اگر فقط تاپل برگردانیم، 
        # اما چون در Session مدل می‌سازیم، اینجا دیتای خام (Row) می‌دهیم یا مدل.
        # برای سادگی فعلا مدل را اینجا ایمپورت می‌کنیم
        from app.core.models import User
        
        self.cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        row = self.cursor.fetchone()
        if row:
            # row = (id, username, password, full_name, role, department_id)
            # مطمئن می‌شویم که ایندکس‌ها درست است.
            # چون department_id ستون آخر (اینکس ۵) است.
            return User(id=row[0], username=row[1], full_name=row[3], role=row[4]) 
            # نکته: ما پسورد و department_id را فعلا در مدل User ساده استفاده نکردیم
        return None

    def check_password(self, username, password):
        """
        Handle Check Password operation.
        """
        self.cursor.execute("SELECT password FROM users WHERE username=?", (username,))
        row = self.cursor.fetchone()
        if row and row[0] == password:
            return True
        return False

    
    
    # ---------------
    # Projects Database Operations
    # ---------------
    def create_project(self, name, code, root_path, render_engine, software):
        """
        Handle Create Project operation.
        """
        new_id = str(uuid.uuid4())
        try:
            self.cursor.execute("INSERT INTO projects VALUES (?, ?, ?, ?, ?, ?, ?)",
                                (new_id, name, code, root_path, "Active", render_engine, software))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"DB Error: {e}")
            return False
        
    def get_all_projects(self):
        """
        Handle Get All Projects operation.
        """
        from app.core.models import Project
        self.cursor.execute("SELECT * FROM projects")
        rows = self.cursor.fetchall()
        projects = []
        for row in rows:
            # هندل کردن پروژه‌هایی که شاید ستون status نداشته باشند (اگر مایگریشن فیل شود)
            # اما چون مایگریشن داریم، فرض می‌کنیم row[4] استاتوس است.
            status = row[4] if len(row) > 4 else "Active"
            render_engine = row[5] if len(row) > 5 else "--------"
            software = row[6] if len(row) > 6 else "--------"
            projects.append(Project(
                id=row[0], name=row[1], code=row[2], root_path=row[3],
                status=status, render_engine=render_engine, software=software
            ))
        return projects
    
    def update_project(self, project_id, name, code, root_path, status, render_engine, software):
        """
        Handle Update Project operation.
        """
        try:
            query = """UPDATE projects SET name=?, code=?, root_path=?, status=?, render_engine=?, software=? WHERE id=?"""
            self.cursor.execute(query, (name, code, root_path, status, render_engine, software, project_id))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Project Update Error: {e}")
            return False

    def delete_project(self, project_id):
        """حذف پروژه و تمام متعلقات آن (Shots, Assets, Tasks, Members)"""
        try:
            print(f">> Deleting project {project_id} and all children...")
            
            # 1. حذف تسک‌های مربوط به ASSETS
            self.cursor.execute("""
                DELETE FROM tasks WHERE entity_id IN (
                    SELECT id FROM assets WHERE project_id = ?
                )
            """, (project_id,))

            # 2. حذف تمام ASSETS
            self.cursor.execute("DELETE FROM assets WHERE project_id=?", (project_id,))

            # 3. حذف تسک‌های مربوط به SHOTS
            self.cursor.execute("""
                DELETE FROM tasks WHERE entity_id IN (
                    SELECT s.id FROM shots s
                    JOIN sequences seq ON s.sequence_id = seq.id
                    WHERE seq.project_id = ?
                )
            """, (project_id,))

            # 4. حذف تمام SHOTS
            self.cursor.execute("""
                DELETE FROM shots WHERE sequence_id IN (
                    SELECT id FROM sequences WHERE project_id = ?
                )
            """, (project_id,))

            # 5. حذف تمام SEQUENCES
            self.cursor.execute("DELETE FROM sequences WHERE project_id=?", (project_id,))
            
            # 6. حذف اعضای پروژه
            self.cursor.execute("DELETE FROM project_members WHERE project_id=?", (project_id,))

            # 7. حذف خود پروژه
            self.cursor.execute("DELETE FROM projects WHERE id=?", (project_id,))
            
            self.conn.commit()
            print(">> Project deleted successfully.")
            return True
            
        except sqlite3.Error as e:
            print(f"!! Project Delete Error: {e}")
            self.conn.rollback()
            return False
        
    def get_project_member_ids(self, project_id):
        """لیست آیدی یوزرهایی که عضو پروژه هستند را برمی‌گرداند"""
        self.cursor.execute("SELECT user_id FROM project_members WHERE project_id=?", (project_id,))
        rows = self.cursor.fetchall()
        # تبدیل لیست تاپل‌ها به یک لیست ساده از آیدی‌ها: ['id1', 'id2']
        return [row[0] for row in rows]

    def update_project_members(self, project_id, user_ids):
        """لیست اعضای پروژه را با لیست جدید جایگزین می‌کند"""
        try:
            # 1. اول همه اعضای قبلی این پروژه را پاک کن (Reset)
            self.cursor.execute("DELETE FROM project_members WHERE project_id=?", (project_id,))
            
            # 2. حالا لیست جدید (تیک‌خورده‌ها) را اضافه کن
            for user_id in user_ids:
                # permission_level را فعلا پیش‌فرض 'edit' می‌گذاریم
                self.cursor.execute("INSERT INTO project_members VALUES (?, ?, ?)", 
                                    (project_id, user_id, "edit"))
            
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Member Update Error: {e}")
            return False
        
    def get_project_users(self, project_id):
        """لیست کامل یوزرهایی که عضو پروژه هستند (برای پر کردن کامبوباکس)"""
        # این کوئری با استفاده از JOIN، اطلاعات یوزرها را از جدول users می‌کشد
        # به شرطی که آیدی آن‌ها در جدول project_members باشد.
        query = """
            SELECT u.id, u.full_name, u.role 
            FROM users u
            JOIN project_members pm ON u.id = pm.user_id
            WHERE pm.project_id = ?
        """
        self.cursor.execute(query, (project_id,))
        return self.cursor.fetchall()
    
    def get_project_by_id(self, project_id):
        """
        Handle Get Project By Id operation.
        """
        from app.core.models import Project
        self.cursor.execute("SELECT * FROM projects WHERE id=?", (project_id,))
        row = self.cursor.fetchone()
        if row:
            status = row[4] if len(row) > 4 else "Active"
            render_engine = row[5] if len(row) > 5 else "--------"
            software = row[6] if len(row) > 6 else "--------"
            return Project(
                id=row[0], name=row[1], code=row[2], root_path=row[3],
                status=status, render_engine=render_engine, software=software
            )
        return None
        

    # ---------------
    # User Database Operations
    # ---------------
    def create_user(self, username, password, full_name, role="artist", department_id=None):
        """ساختن کاربر جدید"""
        new_id = str(uuid.uuid4())
        try:
            # این خط ۶ مقدار رو وارد دیتابیس میکنه (با احتساب department_id)
            self.cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)",
                                (new_id, username, password, full_name, role, department_id))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            print("Username already exists!")
            return False

    def update_user(self, user_id, full_name, username, password, role, department_id):
        """ویرایش اطلاعات کاربر"""
        try:
            # دقت کن: نام ستون در دیتابیس 'department_id' است، نه 'dept_id'
            if password:
                query = """UPDATE users SET full_name=?, username=?, password=?, role=?, department_id=? WHERE id=?"""
                params = (full_name, username, password, role, department_id, user_id)
            else:
                query = """UPDATE users SET full_name=?, username=?, role=?, department_id=? WHERE id=?"""
                params = (full_name, username, role, department_id, user_id)
            
            self.cursor.execute(query, params)
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Update Error: {e}")
            return False
        
    def update_user_profile_safe(self, user_id, full_name, password=None):
        """فقط نام و رمز عبور را آپدیت می‌کند (بدون تغییر نقش یا دپارتمان)"""
        try:
            if password:
                query = "UPDATE users SET full_name=?, password=? WHERE id=?"
                self.cursor.execute(query, (full_name, password, user_id))
            else:
                query = "UPDATE users SET full_name=? WHERE id=?"
                self.cursor.execute(query, (full_name, user_id))
            
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Profile Update Error: {e}")
            return False

    def delete_user(self, user_id):
        """حذف کاربر"""
        try:
            self.cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Delete Error: {e}")
            return False
            
    
    # ----------------
    # Departments Database Operations
    # ----------------
    def create_department(self, name, color):
        """ساخت دپارتمان جدید"""
        new_id = str(uuid.uuid4())
        try:
            self.cursor.execute("INSERT INTO departments VALUES (?, ?, ?)",
                                (new_id, name, color))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Dept Create Error: {e}")
            return False

    def update_department(self, dept_id, name, color):
        """ویرایش دپارتمان"""
        try:
            self.cursor.execute("UPDATE departments SET name=?, color=? WHERE id=?",
                                (name, color, dept_id))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Dept Update Error: {e}")
            return False

    def delete_department(self, dept_id):
        """حذف دپارتمان"""
        try:
            # نکته: اگر کاربری عضو این دپارتمان باشد، در دیتابیس رابطه‌ای بهتر است
            # کاربر را به 'No Department' تغییر دهیم، اما فعلاً ساده حذف می‌کنیم
            self.cursor.execute("DELETE FROM departments WHERE id=?", (dept_id,))
            # کاربرانی که عضو این دپارتمان بودند را بی‌پناه کن (Null)
            self.cursor.execute("UPDATE users SET department_id=NULL WHERE department_id=?", (dept_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Dept Delete Error: {e}")
            return False
        
    def get_all_departments(self):
        """دریافت لیست کامل دپارتمان‌ها شامل تمام قفل‌ها"""
        query = "SELECT id, name, color, allowed_software, render_engine FROM departments"
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
    def create_department_extended(self, name, color, sw, engine):
        """ساخت دپارتمان جدید با تمام قفل‌های نرم‌افزاری و رندر"""
        new_id = str(uuid.uuid4())
        try:
            query = "INSERT INTO departments (id, name, color, allowed_software, render_engine) VALUES (?, ?, ?, ?, ?)"
            self.cursor.execute(query, (new_id, name, color, sw, engine))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Dept Create Extended Error: {e}")
            return False
        
    def update_department_extended(self, dept_id, name, color, sw, engine):
        """
        Handle Update Department Extended operation.
        """
        try:
            query = "UPDATE departments SET name=?, color=?, allowed_software=?, render_engine=? WHERE id=?"
            self.cursor.execute(query, (name, color, sw, engine, dept_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False
    def get_software_list(self):
        """دریافت لیست نرم‌افزارها از تنظیمات ادمین یا فایل کانفیگ"""
        data = self.get_setting("allowed_softwares_list")
        if data:
            return [s.strip() for s in data.split(",")]
        # اگر در دیتابیس نبود، از لیست ثابت در کانفیگ استفاده کن
        from app.core import config
        return config.ALLOWED_SOFTWARES
    
    def get_render_engines_list(self):
        """دریافت لیست موتورهای رندر از تنظیمات ادمین یا فایل کانفیگ"""
        data = self.get_setting("render_engines_list")
        if data:
            return [s.strip() for s in data.split(",")]
        from app.core import config
        return config.RENDER_ENGINES
    
    def get_department_by_id(self, dept_id):
        """دریافت اطلاعات یک دپارتمان خاص بر اساس آیدی"""
        query = "SELECT id, name, color, allowed_software, render_engine FROM departments WHERE id = ?"
        self.cursor.execute(query, (dept_id,))
        return self.cursor.fetchone()

    # این متد را هم در database.py اصلاح کن تا dept_id لود شود
    def get_all_users(self):
        """
        Handle Get All Users operation.
        """
        from app.core.models import User
        self.cursor.execute("SELECT * FROM users")
        rows = self.cursor.fetchall()
        users = []
        for row in rows:
            # row: (id, username, password, fullname, role, dept_id)
            u = User(id=row[0], username=row[1], full_name=row[3], role=row[4])
            u.dept_id = row[5] # این خط برای لود شدن دپارتمان در ادیت ضروری است
            users.append(u)
        return users
    
    # ---------------
    # Sequence & Shot & Task Database Operations
    # ---------------
    # 1. Sequences
    def create_sequence(self, project_id, name):
        """
        Handle Create Sequence operation.
        """
        new_id = str(uuid.uuid4())
        try:
            self.cursor.execute("INSERT INTO sequences VALUES (?, ?, ?)", 
                                (new_id, project_id, name))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Seq Create Error: {e}")
            return False

    def get_sequences(self, project_id):
        """این همان تابعی است که گم شده بود"""
        self.cursor.execute("SELECT * FROM sequences WHERE project_id=?", (project_id,))
        return self.cursor.fetchall()

    def delete_sequence(self, seq_id):
        """حذف سکانس به همراه شات‌ها و تسک‌هایشان"""
        try:
            # 1. حذف تسک‌های شات‌های این سکانس
            self.cursor.execute("""
                DELETE FROM tasks WHERE entity_id IN (
                    SELECT id FROM shots WHERE sequence_id = ?
                )
            """, (seq_id,))
            
            # 2. حذف شات‌ها
            self.cursor.execute("DELETE FROM shots WHERE sequence_id=?", (seq_id,))
            
            # 3. حذف خود سکانس
            self.cursor.execute("DELETE FROM sequences WHERE id=?", (seq_id,))
            self.conn.commit()
            return True
        except sqlite3.Error:
            return False
        
    def get_sequence_by_id(self, seq_id):
        """دریافت اطلاعات یک سکانس خاص با استفاده از ID"""
        query = "SELECT id, project_id, name FROM sequences WHERE id = ?"
        self.cursor.execute(query, (seq_id,))
        return self.cursor.fetchone()

    def update_sequence(self, seq_id, new_name):
        """آپدیت نام سکانس در دیتابیس"""
        try:
            query = "UPDATE sequences SET name = ? WHERE id = ?"
            self.cursor.execute(query, (new_name, seq_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Update Sequence Error: {e}")
            return False


    # 2. Shots
    def create_shot(self, sequence_id, name, start=1001, end=1100):
        """
        Handle Create Shot operation.
        """
        import uuid
        new_id = str(uuid.uuid4())
        try:
            self.cursor.execute("INSERT INTO shots VALUES (?, ?, ?, ?, ?, ?)", 
                                (new_id, sequence_id, name, start, end, "Not Started"))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Create Shot Error: {e}")
            return False

    def get_shots(self, sequence_id):
        """
        Handle Get Shots operation.
        """
        self.cursor.execute("SELECT * FROM shots WHERE sequence_id=?", (sequence_id,))
        return self.cursor.fetchall()
    
    def update_shot(self, shot_id, name, start_frame, end_frame):
        """
        Handle Update Shot operation.
        """
        try:
            query = "UPDATE shots SET name=?, frame_start=?, frame_end=? WHERE id=?"
            self.cursor.execute(query, (name, start_frame, end_frame, shot_id))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Update Shot Error: {e}")
            return False
        
    def get_shot_assets_extended(self, shot_id):
        """لیست کامل اطلاعات اَسِت‌های یک شات"""
        query = """
            SELECT a.id, a.name, a.category, p.root_path, p.name
            FROM assets a
            JOIN shot_assets sa ON a.id = sa.asset_id
            JOIN projects p ON a.project_id = p.id
            WHERE sa.shot_id = ?
        """
        self.cursor.execute(query, (shot_id,))
        return self.cursor.fetchall()
    
    def update_shot_assets(self, shot_id, asset_ids):
        """
        Handle Update Shot Assets operation.
        """
        try:
            self.cursor.execute("DELETE FROM shot_assets WHERE shot_id = ?", (shot_id,))
            for a_id in asset_ids:
                self.cursor.execute("INSERT INTO shot_assets (shot_id, asset_id) VALUES (?, ?)", (shot_id, a_id))
            self.conn.commit() # اصلاح شد
            return True
        except Exception as e:
            print(f"!! Error updating shot assets: {e}")
            return False
    
    def link_asset_to_shot(self, shot_id, asset_id):
        """ایجاد ارتباط بین اَسِت و شات بدون دخالت دستی در دیتابیس"""
        query = "INSERT OR IGNORE INTO shot_assets (shot_id, asset_id) VALUES (?, ?)"
        self.cursor.execute(query, (shot_id, asset_id))
        self.conn.commit()

    def unlink_asset_from_shot(self, shot_id, asset_id):
        """حذف ارتباط در صورت تغییر تصمیم ادمین"""
        query = "DELETE FROM shot_assets WHERE shot_id = ? AND asset_id = ?"
        self.cursor.execute(query, (shot_id, asset_id))
        self.conn.commit()
            
    # این متد را هم اضافه کنید تا اطلاعات یک شات را بگیریم (برای پر کردن دیالوگ ادیت)
    def get_shot_by_id(self, shot_id):
        """
        Handle Get Shot By Id operation.
        """
        self.cursor.execute("SELECT * FROM shots WHERE id=?", (shot_id,))
        return self.cursor.fetchone()

    def delete_shot(self, shot_id):
        """حذف شات به همراه تسک‌هایش"""
        try:
            # اول تسک‌ها
            self.cursor.execute("DELETE FROM tasks WHERE entity_id=?", (shot_id,))
            # بعد خود شات
            self.cursor.execute("DELETE FROM shots WHERE id=?", (shot_id,))
            self.conn.commit()
            return True
        except sqlite3.Error:
            return False

    # 3. Tasks
    def create_task(self, entity_id, dept_id, assignee_id, title, description="", start_date=None, due_date=None, estimated_hours=None, entity_type="Shot"):
        """
        Handle Create Task operation.
        """
        import uuid
        new_id = str(uuid.uuid4())
        try:
            query = """
                INSERT INTO tasks (id, entity_id, department_id, assignee_id, status, title, description, entity_type, start_date, due_date, estimated_hours) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            self.cursor.execute(query, (new_id, entity_id, dept_id, assignee_id, "Todo", title, description, entity_type, start_date, due_date, estimated_hours))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Create Task Error: {e}")
            return False

    def get_tasks(self, entity_id):
        """
        Handle Get Tasks operation.
        """
        # دریافت تسک‌ها به همراه تاریخ‌ها
        query = """
            SELECT t.id, t.status, d.name, u.username, d.color, t.title, t.description, t.start_date, t.due_date
            FROM tasks t
            LEFT JOIN departments d ON t.department_id = d.id
            LEFT JOIN users u ON t.assignee_id = u.id
            WHERE t.entity_id = ? 
        """
        self.cursor.execute(query, (entity_id,))
        return self.cursor.fetchall()
        
    def get_task_by_id(self, task_id):
        """دریافت اطلاعات کامل یک تسک برای نمایش در دیالوگ (به همراه تاریخ‌ها)"""
        query = """
            SELECT 
                t.id,              -- 0
                t.status,          -- 1
                d.name,            -- 2 (Dept Name)
                u.username,        -- 3 (Assignee Name)
                d.color,           -- 4
                t.title,           -- 5
                t.description,     -- 6
                t.entity_id,       -- 7
                t.department_id,   -- 8
                t.assignee_id,     -- 9
                t.start_date,      -- 10
                t.due_date,        -- 11
                t.estimated_hours  -- 12
            FROM tasks t
            LEFT JOIN departments d ON t.department_id = d.id
            LEFT JOIN users u ON t.assignee_id = u.id
            WHERE t.id = ?
        """
        self.cursor.execute(query, (task_id,))
        return self.cursor.fetchone()

    def update_task_details(self, task_id, title, description, assignee_id, dept_id, start_date=None, due_date=None, estimated_hours=None):
        """ویرایش اطلاعات اصلی یک تسک به همراه زمان‌بندی"""
        try:
            query = """
                UPDATE tasks 
                SET title=?, description=?, assignee_id=?, department_id=?,
                    start_date=?, due_date=?, estimated_hours=?
                WHERE id=?
            """
            self.cursor.execute(query, (title, description, assignee_id, dept_id, start_date, due_date, estimated_hours, task_id))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"!! Update Task Details Error: {e}")
            return False       
    
    
    def delete_task(self, task_id):
        """
        Handle Delete Task operation.
        """
        try:
            self.cursor.execute("DELETE FROM tasks WHERE id=?", (task_id,))
            self.conn.commit()
            return True
        except sqlite3.Error:
            return False
            
    def update_task_status(self, task_id, new_status):
        """
        Handle Update Task Status operation.
        """
        try:
            self.cursor.execute("UPDATE tasks SET status=? WHERE id=?", (new_status, task_id))
            self.conn.commit()
            return True
        except sqlite3.Error:
            return False
        
    
        
    def get_user_tasks(self, user_id, include_done=False):
        """
        دریافت تسک‌های کاربر.
        include_done: اگر False باشد، کارهای تمام شده (Done) را نشان نمی‌دهد.
        """
        base_query = """
            SELECT 
                t.id, 
                t.status, 
                d.name, 
                COALESCE(p_shot.name, p_asset.name) as project_name,
                t.title, 
                t.description, 
                t.entity_id
            FROM tasks t
            LEFT JOIN departments d ON t.department_id = d.id
            
            LEFT JOIN shots s ON t.entity_id = s.id
            LEFT JOIN sequences seq ON s.sequence_id = seq.id
            LEFT JOIN projects p_shot ON seq.project_id = p_shot.id
            
            LEFT JOIN assets a ON t.entity_id = a.id
            LEFT JOIN projects p_asset ON a.project_id = p_asset.id
            
            WHERE t.assignee_id = ?
            AND (p_shot.id IS NOT NULL OR p_asset.id IS NOT NULL)
        """
        
        # اگر تیک نمایش کارهای تمام شده خاموش باشد، فیلتر کن
        if not include_done:
            base_query += " AND t.status != 'Done'"
            
        # مرتب‌سازی: کارهای جدیدتر بالا
        base_query += " ORDER BY t.status DESC"

        self.cursor.execute(base_query, (user_id,))
        return self.cursor.fetchall()
        
    def get_task_context_data(self, task_id):
        """
        Retrieves full contextual information for a specific task to be used by launchers.
        
        Args:
            task_id (str): Unique UUID of the task.
            
        Returns:
            dict: Comprehensive data including project path, entity name, and frame ranges.
            None: If the task ID is not found.
        """
        # اول خود تسک را می‌گیریم
        task = self.get_task_by_id(task_id)
        if not task: return None
        
        # task = (id, status, dept_name, user_name, color, title, desc, entity_id, dept_id, assignee_id)
        entity_id = task[7]
        task_title = task[5]

        # 1. چک کنیم آیا SHOT است؟
        self.cursor.execute("""
            SELECT s.id, s.name, s.frame_start, s.frame_end, seq.name, p.id, p.name, p.root_path
            FROM shots s
            JOIN sequences seq ON s.sequence_id = seq.id
            JOIN projects p ON seq.project_id = p.id
            WHERE s.id = ?
        """, (entity_id,))
        shot_data = self.cursor.fetchone()
        
        if shot_data:
            return {
                "type": "Shot",
                "entity_id": shot_data[0],        # <--- این خط باید حتما باشد
                "task_id": task_id,
                "task_title": task_title,
                "entity_name": shot_data[1],      
                "parent_name": shot_data[4],      
                "frame_start": shot_data[2],
                "frame_end": shot_data[3],
                "project_id": shot_data[5],
                "project_name": shot_data[6],
                "project_root": shot_data[7]
            }

        # 2. چک کنیم آیا ASSET است؟
        self.cursor.execute("""
            SELECT a.id, a.name, a.category, p.id, p.name, p.root_path
            FROM assets a
            JOIN projects p ON a.project_id = p.id
            WHERE a.id = ?
        """, (entity_id,))
        asset_data = self.cursor.fetchone()

        if asset_data:
            return {
                "type": "Asset",
                "entity_id": asset_data[0],       # <--- این خط جا مانده بود!
                "task_id": task_id,
                "task_title": task_title,
                "entity_name": asset_data[1],     # Asset Name (Batman)
                "parent_name": asset_data[2],     # Category (Characters)
                "frame_start": 1001,              # Default for Asset
                "frame_end": 1001,                # Default for Asset
                "project_id": asset_data[3],
                "project_name": asset_data[4],
                "project_root": asset_data[5]
            }
            
        return None
        

    # ---------------------------
    # Settings Database operations
    # ---------------------------
    def set_setting(self, key, value):
        """ذخیره یا آپدیت یک تنظیم"""
        try:
            self.cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Setting Error: {e}")
            return False

    def get_setting(self, key, default=None):
        """خواندن یک تنظیم"""
        try:
            self.cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
            row = self.cursor.fetchone()
            return row[0] if row else default
        except sqlite3.Error:
            return default

    def set_default_setting(self, key, value):
        """فقط اگر تنظیم وجود نداشت، آن را بساز"""
        if self.get_setting(key) is None:
            self.set_setting(key, value)


    # -------------------------
    # ASSETS database operations
    # -------------------------
    def create_asset(self, project_id, name, category):
        """
        Handle Create Asset operation.
        """
        import uuid
        new_id = str(uuid.uuid4())
        try:
            self.cursor.execute("INSERT INTO assets VALUES (?, ?, ?, ?, ?)", 
                                (new_id, project_id, name, category, "Not Started"))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Create Asset Error: {e}")
            return False

    def get_assets(self, project_id, category=None):
        """
        Handle Get Assets operation.
        """
        if category:
            self.cursor.execute("SELECT * FROM assets WHERE project_id=? AND category=?", (project_id, category))
        else:
            self.cursor.execute("SELECT * FROM assets WHERE project_id=?", (project_id,))
        return self.cursor.fetchall()

    def get_asset_by_id(self, asset_id):
        """
        Handle Get Asset By Id operation.
        """
        self.cursor.execute("SELECT * FROM assets WHERE id=?", (asset_id,))
        return self.cursor.fetchone()

    def update_asset(self, asset_id, name, category):
        """
        Handle Update Asset operation.
        """
        try:
            self.cursor.execute("UPDATE assets SET name=?, category=? WHERE id=?", (name, category, asset_id))
            self.conn.commit()
            return True
        except sqlite3.Error:
            return False

    def delete_asset(self, asset_id):
        """حذف است به همراه تسک‌هایش"""
        try:
            # 1. ابتدا حذف تسک‌های وابسته برای جلوگیری از ارور
            self.cursor.execute("DELETE FROM tasks WHERE entity_id=?", (asset_id,))
            # 2. حذف خود اسِت
            self.cursor.execute("DELETE FROM assets WHERE id=?", (asset_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Delete Asset DB Error: {e}")
            self.conn.rollback()
            return False
        
    # -------------------------
    # Publish database operations
    # -------------------------
    def create_publish(self, task_id, version, comment, user_name, thumbnail_path, files_dict):
        """
        Registers a new publish entry and links its associated files.
        
        Args:
            task_id (str): The task being published.
            version (int): Incremental version number.
            comment (str): Artist's description of changes.
            user_name (str): Name of the publisher.
            thumbnail_path (str): Path to the generated preview image.
            files_dict (dict): Dictionary mapping file types to their physical paths.
            
        Returns:
            tuple: (bool success, str publish_id or error_message).
        """
        import uuid
        pub_id = str(uuid.uuid4())
        
        try:
            # 1. ثبت خود پابلیش
            self.cursor.execute("""
                INSERT INTO publishes (id, task_id, version, comment, created_by, thumbnail_path)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (pub_id, task_id, version, comment, user_name, thumbnail_path))
            
            # 2. ثبت تک تک فایل‌ها
            for f_type, f_path in files_dict.items():
                file_id = str(uuid.uuid4())
                self.cursor.execute("""
                    INSERT INTO published_files (id, publish_id, file_type, file_path)
                    VALUES (?, ?, ?, ?)
                """, (file_id, pub_id, f_type, f_path))
            
            self.conn.commit()
            return True, pub_id
            
        except sqlite3.Error as e:
            print(f"Publish DB Error: {e}")
            return False, str(e)

    def get_latest_version(self, task_id):
        """پیدا کردن آخرین شماره ورژن برای یک تسک (برای اینکه ورژن بعدی را بسازیم)"""
        self.cursor.execute("SELECT MAX(version) FROM publishes WHERE task_id=?", (task_id,))
        row = self.cursor.fetchone()
        return row[0] if row[0] else 0
    
    def get_publish_path(self, task_id, software="max", category="3d"):
        """
        تولید مسیر هوشمند پابلیش بر اساس ساختار تعریف شده در فایل سیستم
        """
        context = self.get_task_context_data(task_id)
        if not context:
            return None
            
        root = context['project_root']
        proj = context['project_name']
        entity_dir = "Assets" if context['type'] == 'Asset' else "Sequences"
        
        # مسیر ریشه اَسِت یا شات: D:/.../Project Titan/Assets/Characters/Hero
        base_path = os.path.join(root, proj, entity_dir, context['parent_name'], context['entity_name'])
        
        # خواندن ساختار از تنظیمات (یا استفاده از پیش‌فرض)
        from app.core.filesystem import FileSystemManager
        if context['type'] == 'Asset':
            structure = FileSystemManager.get_asset_structure(self)
        else:
            structure = FileSystemManager.get_shot_structure(self)
            
        # بررسی اینکه آیا category (مثلا 3d یا 2d) در پوشه publish تعریف شده است؟
        # فرض پیش‌فرض: publish -> 3d -> max
        publish_dir = "publish"
        
        # ساخت مسیر نهایی: base_path / publish / category / software
        # مثال: D:/.../Hero/publish/3d/max
        final_path = os.path.join(base_path, publish_dir, category, software).replace("\\", "/")
        
        return final_path
    # ---------------------
    # Validation Operations
    # ---------------------

    def get_all_validation_rules_extended(self, project_id):
        """دریافت تمام ستون‌ها از جمله اسکریپت برای نمایش در پنل ادمین"""
        query = """
            SELECT id, software, rule_key, is_active, is_mandatory, rule_script 
            FROM validation_rules 
            WHERE project_id = ?
        """
        self.cursor.execute(query, (project_id,))
        return self.cursor.fetchall()

    def add_validation_rule_with_script(self, data):
        """درج قانون جدید به همراه اسکریپت پایتون از طریق RuleDialog"""
        import uuid
        new_id = str(uuid.uuid4())
        try:
            self.cursor.execute("""
                INSERT INTO validation_rules 
                (id, project_id, software, rule_key, rule_script, is_active, is_mandatory) 
                VALUES (?, ?, ?, ?, ?, 1, ?)
            """, (new_id, data['project_id'], data['software'], data['rule_key'], 
                  data['rule_script'], data['is_mandatory']))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"DB Error (Add Rule): {e}")
            return False

    def update_validation_rule(self, rule_id, data):
        """ویرایش قانون موجود و آپدیت اسکریپت یا نام آن"""
        try:
            query = """
                UPDATE validation_rules 
                SET software=?, rule_key=?, rule_script=?, is_mandatory=? 
                WHERE id=?
            """
            self.cursor.execute(query, (data['software'], data['rule_key'], 
                                        data['rule_script'], data['is_mandatory'], rule_id))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"DB Error (Update Rule): {e}")
            return False

    def delete_validation_rule(self, rule_id):
        """حذف فیزیکی قانون از دیتابیس"""
        try:
            self.cursor.execute("DELETE FROM validation_rules WHERE id=?", (rule_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"DB Error (Delete Rule): {e}")
            return False

    def get_validation_rules_with_scripts(self, project_id, software):
        """این متد توسط پابلیشر (مکس/بلندر) برای اجرای اسکریپت‌ها فراخوانی می‌شود"""
        query = """
            SELECT rule_key, rule_script, is_mandatory 
            FROM validation_rules 
            WHERE project_id = ? AND (software = ? OR software = 'all') AND is_active = 1
        """
        self.cursor.execute(query, (project_id, software))
        rows = self.cursor.fetchall()
        # تبدیل به لیست دیکشنری برای استفاده راحت در exec() پابلیشر
        return [{"rule_key": r[0], "rule_script": r[1], "is_mandatory": r[2]} for r in rows]
    

    # ---------------------
    # Naming Operations
    # ---------------------
    def get_naming_convention(self, project_id, category):
        """
        Handle Get Naming Convention operation.
        """
        query = "SELECT prefix, suffix, required_objects FROM naming_conventions WHERE project_id=? AND category=?"
        self.cursor.execute(query, (project_id, category))
        row = self.cursor.fetchone()
        if row:
            return {
                "prefix": row[0],
                "suffix": row[1],
                "required_objects": row[2].split(',') if row[2] else []
            }
        return None
    
    # ---------------------------------------------------------
    # NAMING STANDARDS OPERATIONS (CRUD)
    # ---------------------------------------------------------

    def add_naming_standard(self, data):
        """اضافه کردن یک استاندارد نام‌گذاری جدید"""
        try:
            standard_id = str(uuid.uuid4())
            query = """
                INSERT INTO naming_standards (id, project_id, category, prefix, suffix, required_hierarchy)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            self.cursor.execute(query, (
                standard_id,
                data['project_id'],
                data['category'],
                data.get('prefix', ''),
                data.get('suffix', ''),
                data.get('required_hierarchy', '')
            ))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"DB Error (Add Naming Standard): {e}")
            return False

    def get_naming_standards(self, project_id):
        """دریافت تمام استانداردهای یک پروژه"""
        query = "SELECT * FROM naming_standards WHERE project_id = ?"
        self.cursor.execute(query, (project_id,))
        return self.cursor.fetchall()

    def update_naming_standard(self, standard_id, data):
        """ویرایش یک استاندارد موجود"""
        try:
            query = """
                UPDATE naming_standards 
                SET category=?, prefix=?, suffix=?, required_hierarchy=?
                WHERE id=?
            """
            self.cursor.execute(query, (
                data['category'],
                data['prefix'],
                data['suffix'],
                data['required_hierarchy'],
                standard_id
            ))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"DB Error (Update Naming Standard): {e}")
            return False

    def delete_naming_standard(self, standard_id):
        """حذف یک استاندارد"""
        try:
            self.cursor.execute("DELETE FROM naming_standards WHERE id=?", (standard_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"DB Error (Delete Naming Standard): {e}")
            return False

    def get_naming_standard_by_category(self, project_id, category):
        """
        این متد اصلی است که پابلیشر از آن استفاده خواهد کرد 
        تا بفهمد مثلا برای یک Character چه قوانینی وجود دارد
        """
        query = "SELECT * FROM naming_standards WHERE project_id = ? AND category = ?"
        self.cursor.execute(query, (project_id, category))
        row = self.cursor.fetchone()
        if row:
            return {
                "id": row[0],
                "project_id": row[1],
                "category": row[2],
                "prefix": row[3],
                "suffix": row[4],
                "required_hierarchy": row[5]
            }
        return None