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
        
        # 1. First, connect based on the configuration
        if config.DB_TYPE == "postgres":
            try:
                import psycopg2
                self.conn = psycopg2.connect(**config.DB_CONFIG)
                self.cursor = self.conn.cursor() # <--- First define the cursor
                print(">> [Cortex] Connected to PostgreSQL Server.")
            except ImportError:
                print("!! [Error] psycopg2 not found.")
                return
        else:
            self.conn = sqlite3.connect(DB_PATH)
            self.cursor = self.conn.cursor() # <--- First define the cursor
            print(f">> [Cortex] Using Local SQLite: {DB_PATH}")
        
        # 2. Now that the cursor is created, do the rest
        self.create_tables()
        self.perform_migrations()
        self.create_indexes() # <--- Now this line runs without error
        self.seed_data()

    def create_tables(self):
        """Creating base tables (runs only if they don't exist)"""
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
                -- We don't leave the department_id column here to test Migration
                -- Or if the database is new, Migration will add it
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

        # --- FIX: project members table (which caused the error) ---
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
                department_id TEXT, -- pay attention: department_id
                assignee_id TEXT,
                title TEXT,           
                description TEXT,     
                status TEXT DEFAULT 'Todo',
                start_date TEXT, -- NEW: Start date
                due_date TEXT, -- NEW: Delivery date (deadline)
                estimated_hours REAL, -- NEW: estimated time
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
                created_by TEXT, -- username
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                thumbnail_path TEXT, -- Thumbnail image path
                
                FOREIGN KEY(task_id) REFERENCES tasks(id)
            )
        """)

        # Table of output files
        # Why separate? Because one publication may generate 10 files (Alembic, Max, MP4, Texture, ...)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS published_files (
                id TEXT PRIMARY KEY,
                publish_id TEXT,
                
                file_type TEXT,        -- e.g. 'source_max', 'alembic_cache', 'preview_mov', 'render_pass'
                file_path TEXT, -- the path of the file on the hard drive
                
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
                rule_script TEXT, -- This column is critical for storing Python code
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
                        project_id TEXT, -- This column was inserted
                        category TEXT,          
                        prefix TEXT,            
                        suffix TEXT,            
                        required_hierarchy TEXT,
                        FOREIGN KEY(project_id) REFERENCES projects(id)
                    )
                """)

        self.conn.commit()

    def create_indexes(self):
        """Building critical indexes to maintain speed in large projects"""
        try:
            # Index on entities (for fast loading of SHOT tasks)
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_entity ON tasks(entity_id)")
            # Index on users (for fast loading of personal dashboard)
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_assignee ON tasks(assignee_id)")
            # Index on dates (for quick reporting of future deadlines)
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_due ON tasks(due_date)")
            
            self.conn.commit()
            print(">> [Cortex] Database Indexes verified.")
        except Exception as e:
            print(f"!! [Warning] Index creation failed: {e}")

    def perform_migrations(self):
        """Check and intelligently repair the structure of the tables"""
        
        # --- 1. Checking the TASKS table ---
        self.cursor.execute("PRAGMA table_info(tasks)")
        columns_info = self.cursor.fetchall()
        columns = [info[1] for info in columns_info]
        
        # A. Convert dept_id to department_id
        if "department_id" not in columns:
            print("Migration: Adding 'department_id' to tasks...")
            self.cursor.execute("ALTER TABLE tasks ADD COLUMN department_id TEXT")
        
        # If the old dept_id column exists, transfer its information
        if "dept_id" in columns:
            print("Migration: Transferring data from dept_id to department_id...")
            # This query only fills the places where department_id is empty
            self.cursor.execute("UPDATE tasks SET department_id = dept_id WHERE department_id IS NULL")

        # B. Convert shot_id to entity_id
        if "entity_id" not in columns:
            print("Migration: Adding 'entity_id' to tasks...")
            self.cursor.execute("ALTER TABLE tasks ADD COLUMN entity_id TEXT")
        
        if "shot_id" in columns:
            print("Migration: Transferring data from shot_id to entity_id...")
            self.cursor.execute("UPDATE tasks SET entity_id = shot_id WHERE entity_id IS NULL")

        # C. Add other new columns
        if "entity_type" not in columns:
            self.cursor.execute("ALTER TABLE tasks ADD COLUMN entity_type TEXT DEFAULT 'Shot'")
            
        if "assignee_id" not in columns:
            self.cursor.execute("ALTER TABLE tasks ADD COLUMN assignee_id TEXT")
            
        if "title" not in columns:
            self.cursor.execute("ALTER TABLE tasks ADD COLUMN title TEXT")
            
        if "description" not in columns:
            self.cursor.execute("ALTER TABLE tasks ADD COLUMN description TEXT")

        # --- D. Add schedule columns (new migration) ---
        if "start_date" not in columns:
            print("Migration: Adding 'start_date' to tasks...")
            self.cursor.execute("ALTER TABLE tasks ADD COLUMN start_date TEXT")
            
        if "due_date" not in columns:
            print("Migration: Adding 'due_date' to tasks...")
            self.cursor.execute("ALTER TABLE tasks ADD COLUMN due_date TEXT")
            
        if "estimated_hours" not in columns:
            print("Migration: Adding 'estimated_hours' to tasks...")
            self.cursor.execute("ALTER TABLE tasks ADD COLUMN estimated_hours REAL")

        # --- 2. Checking the USERS table ---
        self.cursor.execute("PRAGMA table_info(users)")
        user_cols = [info[1] for info in self.cursor.fetchall()]
        if "department_id" not in user_cols:
            self.cursor.execute("ALTER TABLE users ADD COLUMN department_id TEXT")

        # --- Checking the PROJECTS table ---
        self.cursor.execute("PRAGMA table_info(projects)")
        proj_columns = [info[1] for info in self.cursor.fetchall()]
        
        if "status" not in proj_columns:
            self.cursor.execute("ALTER TABLE projects ADD COLUMN status TEXT DEFAULT 'Active'")

        # --- Add new columns ---
        if "render_engine" not in proj_columns:
            print("Migration: Adding 'render_engine'...")
            self.cursor.execute("ALTER TABLE projects ADD COLUMN render_engine TEXT DEFAULT '--------'")
            
        if "software" not in proj_columns:
            print("Migration: Adding 'software'...")
            self.cursor.execute("ALTER TABLE projects ADD COLUMN software TEXT DEFAULT '--------'")

        # --- Checking and updating the DEPARTMENTS table for locks ---
        self.cursor.execute("PRAGMA table_info(departments)")
        dept_cols = [info[1] for info in self.cursor.fetchall()]
        
        if "allowed_software" not in dept_cols:
            print(">> [Migration] Adding 'allowed_software' to departments...")
            self.cursor.execute("ALTER TABLE departments ADD COLUMN allowed_software TEXT DEFAULT 'all'")
            
        if "render_engine" not in dept_cols:
            print(">> [Migration] Adding 'render_engine' to departments...")
            self.cursor.execute("ALTER TABLE departments ADD COLUMN render_engine TEXT DEFAULT '--------'")

        # 1. Migration related to validation_rules (hold)
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

        # 2. Migration related to naming_standards (add)
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
        """Create the primary user only if there is no user in the database"""
        self.cursor.execute("SELECT COUNT(*) FROM users")
        if self.cursor.fetchone()[0] == 0:
            # The database is empty, so create the primary user
            self.cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)",
                                ("u1", "admin", "123456", "Admin", "admin", None))

            self.cursor.execute("INSERT INTO projects VALUES (?, ?, ?, ?, ?, ?, ?)",
                                ("p1", "Project Titan", "TTN", r"D:\Projects\Titan", "Active", "Octane", "3ds Max"))

            self.conn.commit()
            print("--- Database Initialized with Default User ---")

    # --- Other auxiliary functions (CRUD) ---

    def get_user_by_username(self, username):
        """
        Handle Get User By Username operation.
        """
        # There is no need to import models at the top of the file if we only return a tuple.
        # But because we create a model in Session, here we give raw data (Row) or model.
        # For simplicity, we import the model here
        from app.core.models import User
        
        self.cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        row = self.cursor.fetchone()
        if row:
            # row = (id, username, password, full_name, role, department_id)
            # We make sure the indexes are correct.
            # Because department_id is the last column (index 5).
            return User(id=row[0], username=row[1], full_name=row[3], role=row[4]) 
            # Note: We did not use password and department_id in simple User model
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
            # Handling projects that may not have a status column (if the migration fails)
            # But since we have migration, we assume row[4] is status.
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
        """Deleting the project and all its belongings (Shots, Assets, Tasks, Members)"""
        try:
            print(f">> Deleting project {project_id} and all children...")
            
            # 1. Removing tasks related to ASSETS
            self.cursor.execute("""
                DELETE FROM tasks WHERE entity_id IN (
                    SELECT id FROM assets WHERE project_id = ?
                )
            """, (project_id,))

            # 2. Completely delete ASSETS
            self.cursor.execute("DELETE FROM assets WHERE project_id=?", (project_id,))

            # 3. Removing tasks related to SHOTS
            self.cursor.execute("""
                DELETE FROM tasks WHERE entity_id IN (
                    SELECT s.id FROM shots s
                    JOIN sequences seq ON s.sequence_id = seq.id
                    WHERE seq.project_id = ?
                )
            """, (project_id,))

            # 4. Delete all SHOTS
            self.cursor.execute("""
                DELETE FROM shots WHERE sequence_id IN (
                    SELECT id FROM sequences WHERE project_id = ?
                )
            """, (project_id,))

            # 5. REMOVE ALL SEQUENCES
            self.cursor.execute("DELETE FROM sequences WHERE project_id=?", (project_id,))
            
            # 6. Removal of project members
            self.cursor.execute("DELETE FROM project_members WHERE project_id=?", (project_id,))

            # 7. Delete the project itself
            self.cursor.execute("DELETE FROM projects WHERE id=?", (project_id,))
            
            self.conn.commit()
            print(">> Project deleted successfully.")
            return True
            
        except sqlite3.Error as e:
            print(f"!! Project Delete Error: {e}")
            self.conn.rollback()
            return False
        
    def get_project_member_ids(self, project_id):
        """Returns the list of IDs of users who are members of the project"""
        self.cursor.execute("SELECT user_id FROM project_members WHERE project_id=?", (project_id,))
        rows = self.cursor.fetchall()
        # Convert the list of tuples to a simple list of ids: ['id1', 'id2']
        return [row[0] for row in rows]

    def update_project_members(self, project_id, user_ids):
        """Replaces the list of project members with the new list"""
        try:
            # 1. First, delete all previous members of this project (Reset)
            self.cursor.execute("DELETE FROM project_members WHERE project_id=?", (project_id,))
            
            # 2. Now add the new list (checkmarks).
            for user_id in user_ids:
                # We'll leave the permission_level at the default 'edit' for now
                self.cursor.execute("INSERT INTO project_members VALUES (?, ?, ?)", 
                                    (project_id, user_id, "edit"))
            
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Member Update Error: {e}")
            return False
        
    def get_project_users(self, project_id):
        """The complete list of users who are members of the project (to fill combobox)"""
        # This query pulls user information from the users table using JOIN
        # Provided that their ID is in the project_members table.
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
        """Create a new user"""
        new_id = str(uuid.uuid4())
        try:
            # This line enters 6 values ​​into the database (including department_id).
            self.cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)",
                                (new_id, username, password, full_name, role, department_id))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            print("Username already exists!")
            return False

    def update_user(self, user_id, full_name, username, password, role, department_id):
        """Edit user information"""
        try:
            # Pay attention: the column name in the database is 'department_id', not 'dept_id'
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
        """It only updates the name and password (without changing the role or department)."""
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
        """Delete user"""
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
        """Building a new department"""
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
        """Editing department"""
        try:
            self.cursor.execute("UPDATE departments SET name=?, color=? WHERE id=?",
                                (name, color, dept_id))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Dept Update Error: {e}")
            return False

    def delete_department(self, dept_id):
        """Deletion of the department"""
        try:
            # Note: If the user is a member of this department, there is a better relationship in the database
            # Let's change the user to 'No Department', but we'll just delete it for now
            self.cursor.execute("DELETE FROM departments WHERE id=?", (dept_id,))
            # Delete users who were members of this department (Null)
            self.cursor.execute("UPDATE users SET department_id=NULL WHERE department_id=?", (dept_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Dept Delete Error: {e}")
            return False
        
    def get_all_departments(self):
        """Get the complete list of departments including all locks"""
        query = "SELECT id, name, color, allowed_software, render_engine FROM departments"
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
    def create_department_extended(self, name, color, sw, engine):
        """Building a new department with all software locks and rendering"""
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
        """Get the software list from admin settings or config file"""
        data = self.get_setting("allowed_softwares_list")
        if data:
            return [s.strip() for s in data.split(",")]
        # If it is not in the database, use the fixed list in the config
        from app.core import config
        return config.ALLOWED_SOFTWARES
    
    def get_render_engines_list(self):
        """Get the list of rendering engines from admin settings or config file"""
        data = self.get_setting("render_engines_list")
        if data:
            return [s.strip() for s in data.split(",")]
        from app.core import config
        return config.RENDER_ENGINES
    
    def get_department_by_id(self, dept_id):
        """Get information of a specific department based on ID"""
        query = "SELECT id, name, color, allowed_software, render_engine FROM departments WHERE id = ?"
        self.cursor.execute(query, (dept_id,))
        return self.cursor.fetchone()

    # Modify this method in database.py to load dept_id
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
            u.dept_id = row[5] # This line is necessary to load the department in the edit
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
        """This is the function that was missing"""
        self.cursor.execute("SELECT * FROM sequences WHERE project_id=?", (project_id,))
        return self.cursor.fetchall()

    def delete_sequence(self, seq_id):
        """Delete the sequence along with their shots and tasks"""
        try:
            # 1. Removing the tasks of the shots of this sequence
            self.cursor.execute("""
                DELETE FROM tasks WHERE entity_id IN (
                    SELECT id FROM shots WHERE sequence_id = ?
                )
            """, (seq_id,))
            
            # 2. Delete her chat
            self.cursor.execute("DELETE FROM shots WHERE sequence_id=?", (seq_id,))
            
            # 3. Delete the sequence itself
            self.cursor.execute("DELETE FROM sequences WHERE id=?", (seq_id,))
            self.conn.commit()
            return True
        except sqlite3.Error:
            return False
        
    def get_sequence_by_id(self, seq_id):
        """Get the information of a specific sequence using ID"""
        query = "SELECT id, project_id, name FROM sequences WHERE id = ?"
        self.cursor.execute(query, (seq_id,))
        return self.cursor.fetchone()

    def update_sequence(self, seq_id, new_name):
        """Update the name of the sequence in the database"""
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
        """Full list of one-shot asset information"""
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
            self.conn.commit() # It was corrected
            return True
        except Exception as e:
            print(f"!! Error updating shot assets: {e}")
            return False
    
    def link_asset_to_shot(self, shot_id, asset_id):
        """Creating a connection between assets and shots without manual intervention in the database"""
        query = "INSERT OR IGNORE INTO shot_assets (shot_id, asset_id) VALUES (?, ?)"
        self.cursor.execute(query, (shot_id, asset_id))
        self.conn.commit()

    def unlink_asset_from_shot(self, shot_id, asset_id):
        """Delete communication in case of change of admin's decision"""
        query = "DELETE FROM shot_assets WHERE shot_id = ? AND asset_id = ?"
        self.cursor.execute(query, (shot_id, asset_id))
        self.conn.commit()
            
    # Add this method to get the information of a shot (to fill the edit dialog)
    def get_shot_by_id(self, shot_id):
        """
        Handle Get Shot By Id operation.
        """
        self.cursor.execute("SELECT * FROM shots WHERE id=?", (shot_id,))
        return self.cursor.fetchone()

    def delete_shot(self, shot_id):
        """Delete the shot along with its tasks"""
        try:
            # First the tasks
            self.cursor.execute("DELETE FROM tasks WHERE entity_id=?", (shot_id,))
            # Then the shot itself
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
        # Receive tasks with dates
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
        """Get the complete information of a task to display in the dialogue (with dates)"""
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
        """Editing the main information of a task along with the schedule"""
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
        Receive user tasks.
        include_done: If it is False, it will not show done tasks.
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
        
        # If the Show completed tasks tick is off, filter
        if not include_done:
            base_query += " AND t.status != 'Done'"
            
        # Sort: Newer works up
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
        # First we take the task itself
        task = self.get_task_by_id(task_id)
        if not task: return None
        
        # task = (id, status, dept_name, user_name, color, title, desc, entity_id, dept_id, assignee_id)
        entity_id = task[7]
        task_title = task[5]

        # 1. Let's check if it is SHOT?
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
                "entity_id": shot_data[0],        # <--- This line must be
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

        # 2. Let's check if it is an ASSET?
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
                "entity_id": asset_data[0],       # <--- This line was left!
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
        """Save or update a setting"""
        try:
            self.cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Setting Error: {e}")
            return False

    def get_setting(self, key, default=None):
        """Reading a setting"""
        try:
            self.cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
            row = self.cursor.fetchone()
            return row[0] if row else default
        except sqlite3.Error:
            return default

    def set_default_setting(self, key, value):
        """Only if the setting does not exist, create it"""
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
        """It is deleted along with its tasks"""
        try:
            # 1. First remove dependent tasks to avoid errors
            self.cursor.execute("DELETE FROM tasks WHERE entity_id=?", (asset_id,))
            # 2. Delete the set itself
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
            # 1. Registration of self-publishing
            self.cursor.execute("""
                INSERT INTO publishes (id, task_id, version, comment, created_by, thumbnail_path)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (pub_id, task_id, version, comment, user_name, thumbnail_path))
            
            # 2. Registration of individual files
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
        """Finding the latest version number for a task (to build the next version)"""
        self.cursor.execute("SELECT MAX(version) FROM publishes WHERE task_id=?", (task_id,))
        row = self.cursor.fetchone()
        return row[0] if row[0] else 0
    
    def get_publish_path(self, task_id, software="max", category="3d"):
        """
        Generation of intelligent publishing path based on the structure defined in the file system
        """
        context = self.get_task_context_data(task_id)
        if not context:
            return None
            
        root = context['project_root']
        proj = context['project_name']
        entity_dir = "Assets" if context['type'] == 'Asset' else "Sequences"
        
        # Asset or shot root path: D:/.../Project Titan/Assets/Characters/Hero
        base_path = os.path.join(root, proj, entity_dir, context['parent_name'], context['entity_name'])
        
        # Read structure from configuration (or use default)
        from app.core.filesystem import FileSystemManager
        if context['type'] == 'Asset':
            structure = FileSystemManager.get_asset_structure(self)
        else:
            structure = FileSystemManager.get_shot_structure(self)
            
        # Checking if category (eg 3d or 2d) is defined in the publish folder?
        # Default assumption: publish -> 3d -> max
        publish_dir = "publish"
        
        # Make the final path: base_path / publish / category / software
        # Example: D:/.../Hero/publish/3d/max
        final_path = os.path.join(base_path, publish_dir, category, software).replace("\\", "/")
        
        return final_path
    # ---------------------
    # Validation Operations
    # ---------------------

    def get_all_validation_rules_extended(self, project_id):
        """Get all the columns including the script to display in the admin panel"""
        query = """
            SELECT id, software, rule_key, is_active, is_mandatory, rule_script 
            FROM validation_rules 
            WHERE project_id = ?
        """
        self.cursor.execute(query, (project_id,))
        return self.cursor.fetchall()

    def add_validation_rule_with_script(self, data):
        """Insert new rule along with Python script through RuleDialog"""
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
        """Edit the existing law and update the script or its name"""
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
        """Physical removal of the law from the database"""
        try:
            self.cursor.execute("DELETE FROM validation_rules WHERE id=?", (rule_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"DB Error (Delete Rule): {e}")
            return False

    def get_validation_rules_with_scripts(self, project_id, software):
        """This method is called by Publisher (Max/Blender) to run scripts"""
        query = """
            SELECT rule_key, rule_script, is_mandatory 
            FROM validation_rules 
            WHERE project_id = ? AND (software = ? OR software = 'all') AND is_active = 1
        """
        self.cursor.execute(query, (project_id, software))
        rows = self.cursor.fetchall()
        # Convert to dictionary list for convenient use in Publisher's exec()
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
        """Add a new naming standard"""
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
        """Get all the standards of a project"""
        query = "SELECT * FROM naming_standards WHERE project_id = ?"
        self.cursor.execute(query, (project_id,))
        return self.cursor.fetchall()

    def update_naming_standard(self, standard_id, data):
        """Edit an existing standard"""
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
        """Remove a standard"""
        try:
            self.cursor.execute("DELETE FROM naming_standards WHERE id=?", (standard_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"DB Error (Delete Naming Standard): {e}")
            return False

    def get_naming_standard_by_category(self, project_id, category):
        """
        This is the main method that the publisher will use
        To understand, for example, what are the rules for a character
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