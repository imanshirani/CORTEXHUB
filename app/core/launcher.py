import os
import subprocess
import sys
from PySide6.QtCore import QSettings

try:
    current_script_path = os.path.dirname(os.path.abspath(__file__))
    app_folder = os.path.dirname(current_script_path)
    root_folder = os.path.dirname(app_folder)
    if root_folder not in sys.path: sys.path.append(root_folder)
    if app_folder not in sys.path: sys.path.append(app_folder)
    import config
except ImportError:
    class config:
        DEFAULT_FPS = 24
        DEFAULT_FRAME_WIDTH = 1920
        DEFAULT_FRAME_HEIGHT = 1080

class LauncherFactory:
    @staticmethod
    def get_launcher(session, software_name):
        """
        Handle Get Launcher operation.
        """
        software_name = software_name.lower()
        #3D
        if "max" in software_name: return MaxLauncher(session)
        elif "maya" in software_name: return MayaLauncher(session)
        elif "blender" in software_name: return BlenderLauncher(session)
        elif "houdini" in software_name: return HoudiniLauncher(session)
        #2D
        elif "photoshop" in software_name: return PhotoshopLauncher(session)
        return None

class BaseLauncher:
    def __init__(self, session):
        """
        Handle   Init   operation.
        """
        self.session = session
        self.env = os.environ.copy()
        self.software_dir = "common"
        # تعریف ریشه پروژه برای استفاده در تمام لانچرها
        current_file_path = os.path.abspath(__file__) # app/core/launcher.py
        self.root_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file_path)))

    def set_context(self, project, task, user):
        """
        Handle Set Context operation.
        """
        self.env = os.environ.copy()
        self.allowed_sw = "all"
        
        # Core Context
        self.env["CORTEX_PROJECT_ROOT"] = str(project.root_path)
        self.env["CORTEX_PROJECT_NAME"] = str(project.name)
        self.env["CORTEX_TASK_ID"] = str(task.id)
        
        safe_task_name = str(task.title).replace(" ", "_")
        self.env["CORTEX_TASK_NAME"] = safe_task_name
        self.env["CORTEX_USER"] = str(user.username)
        
        dept_name = "General"
        try:
            if hasattr(self.session, 'db'):
                query = """
                    SELECT d.name, d.allowed_software, d.render_engine 
                    FROM tasks t 
                    JOIN departments d ON t.department_id = d.id 
                    WHERE t.id = ?
                """
                self.session.db.cursor.execute(query, (task.id,))
                result = self.session.db.cursor.fetchone()
                if result:
                    dept_name = result[0]
                    self.env["CORTEX_DEPT_NAME"] = str(dept_name)
                    self.allowed_sw = result[1] if result[1] else "all"
                    render_eng = result[2] if result[2] else "--------"
                    self.env["CORTEX_RENDER_ENGINE"] = render_eng
                    print(f">> [Launcher] Dept: {dept_name} | Lock: {self.allowed_sw} | Engine: {render_eng}")
                    
        except Exception as e:
            print(f"!! Error fetching department: {e}")
        
        safe_dept_name = dept_name.replace(" ", "")

        # Configs (Reading from config.py)
        fps = getattr(config, "DEFAULT_FPS", 24)
        width = getattr(config, "DEFAULT_FRAME_WIDTH", 1920)
        height = getattr(config, "DEFAULT_FRAME_HEIGHT", 1080)
        self.env["CORTEX_FPS"] = str(fps)
        self.env["CORTEX_RES_W"] = str(width)
        self.env["CORTEX_RES_H"] = str(height)
        
        # Shot/Asset Context
        if hasattr(task, 'frame_start'):
            self.env["CORTEX_FRAME_START"] = str(task.frame_start)
            self.env["CORTEX_FRAME_END"] = str(task.frame_end)
            
        if hasattr(task, 'type'): self.env["CORTEX_ENTITY_TYPE"] = str(task.type)
        if hasattr(task, 'entity_name'): self.env["CORTEX_ENTITY_NAME"] = str(task.entity_name)
            
        # work / 2D_or_3D / Dept / Software / Task
        base_path = os.path.join(project.root_path, project.name)
        is_2d = self.software_dir in ["photoshop", "nuke", "ae", "premiere", "illustrator", "gimp"]
        dimension = "2D" if is_2d else "3D"

        entity_root = None
        task_type = getattr(task, "type", None)
        parent_name = getattr(task, "parent_name", None)
        entity_name = getattr(task, "entity_name", None)
        if task_type == "Shot" and parent_name and entity_name:
            entity_root = os.path.join(base_path, "Sequences", str(parent_name), str(entity_name))
        elif task_type == "Asset" and parent_name and entity_name:
            entity_root = os.path.join(base_path, "Assets", str(parent_name), str(entity_name))

        if entity_root:
            work_path = os.path.join(
                entity_root, "work", dimension, safe_dept_name, self.software_dir, safe_task_name
            ).replace("\\", "/")
        else:
            work_path = os.path.join(
                base_path, "work", dimension, safe_dept_name, self.software_dir, safe_task_name
            ).replace("\\", "/")

        if not os.path.exists(work_path):
            try:
                os.makedirs(work_path)
            except OSError:
                pass
            
        self.work_path = work_path
        self.env["CORTEX_WORK_PATH"] = work_path
        
    def launch(self):
        """
        Handle Launch operation.
        """
        raise NotImplementedError
# ----------------------------
# 3Ds Max Launcher
# ----------------------------
class MaxLauncher(BaseLauncher):
    def __init__(self, session):
        """
        Handle   Init   operation.
        """
        super().__init__(session)
        self.software_dir = "max"

    def launch(self):
        """
        Handle Launch operation.
        """
        # ۱. چک کردن قفل نرم‌افزار (اگر مکس مجاز نباشد، کلاً اجرا نشو)
        if self.allowed_sw.lower() != "all" and "max" not in self.allowed_sw.lower():
            return False, f"❌ Access Denied! This task is locked to: {self.allowed_sw.upper()}"

        # ۲. پیدا کردن مسیر EXE
        settings = QSettings("Cortex", "Pipeline")
        exe_path = settings.value("max_path", "")
        if not exe_path or not os.path.exists(exe_path):
            return False, "3ds Max path is not set."

        # ۳. پیدا کردن اسکریپت استارتاپ
        current_file_path = os.path.abspath(__file__)
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file_path)))
        script_path = os.path.join(root_dir, "plugins", "3dsmax", "startup.py")
        
        cmd = [exe_path]
        if os.path.exists(script_path):
             cmd = [exe_path, "-U", "PythonHost", script_path]

        try:
            subprocess.Popen(cmd, env=self.env)
            return True, "3ds Max Launched!"
        except Exception as e:
            return False, f"Error: {e}"

# ----------------------------
# Maya Launcher
# ----------------------------
class MayaLauncher(BaseLauncher):
    def __init__(self, session):
        super().__init__(session)
        self.software_dir = "maya"

    def launch(self):
        # چک کردن قفل نرم‌افزاری از دیتابیس
        if self.allowed_sw.lower() != "all" and "maya" not in self.allowed_sw.lower():
            return False, f"❌ Access Denied! Task locked to: {self.allowed_sw.upper()}"

        settings = QSettings("Cortex", "Pipeline")
        exe_path = settings.value("maya_path", "") 
        
        if not exe_path or not os.path.exists(exe_path):
            return False, "Maya path is not set in Settings > Utilities."

        # پیدا کردن مسیر دقیق پوشه plugins/maya در کورتکس
        current_file_path = os.path.abspath(__file__)
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file_path)))
        maya_plugin_dir = os.path.join(root_dir, "plugins", "maya").replace("\\", "/")

        # --- این دو خط جادویی هستند! ---
        # اضافه کردن مسیر پلاگین به متغیر پایتونِ مایا
        existing_python_path = self.env.get("PYTHONPATH", "")
        self.env["PYTHONPATH"] = maya_plugin_dir + os.pathsep + existing_python_path
        # -------------------------------

        try:
            # حالا مایا را با این تنظیمات جدید باز می‌کنیم
            subprocess.Popen([exe_path], env=self.env)
            return True, "Maya Launched with Cortex Pipeline!"
        except Exception as e:
            return False, str(e)


# ----------------------------
# Houdini Launcher
# ----------------------------
class HoudiniLauncher(BaseLauncher):
    def __init__(self, session):
        """Initializes the Houdini Launcher context."""
        super().__init__(session)
        self.software_dir = "houdini"

    def launch(self):
        # ۱. بررسی اجازه دسترسی (قفل دپارتمان)
        if self.allowed_sw.lower() != "all" and "houdini" not in self.allowed_sw.lower():
            return False, f"❌ Access Denied! Task locked to: {self.allowed_sw.upper()}"

        # ۲. خواندن مسیر EXE از تنظیمات لوکال
        settings = QSettings("Cortex", "Pipeline")
        exe_path = settings.value("houdini_path", "")
        
        if not exe_path or not os.path.exists(exe_path):
            return False, "Houdini path is not set in Settings > Utilities."

        # ۳. پیدا کردن مسیر ریشه پروژه برای آدرس‌دهی پلاگین‌ها
        current_file_path = os.path.abspath(__file__)
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file_path)))
        houdini_plugin_dir = os.path.join(root_dir, "plugins", "houdini")

        # ۴. تنظیم متغیرهای محیطی اختصاصی هودینی
        # معرفی مسیر پلاگین به عنوان ریشه برای هودینی
        self.env["CORTEX_HOUDINI"] = houdini_plugin_dir
        
        # معرفی مسیر اسکریپت‌ها به پایتونِ هودینی (برای شناسایی publisher_houdini.py)
        scripts_path = os.path.join(houdini_plugin_dir, "scripts")
        self.env["PYTHONPATH"] = scripts_path + os.pathsep + self.env.get("PYTHONPATH", "")

        # ست کردن JOB برای دسترسی به فایل‌ها با علامت $JOB در هودینی
        self.env["JOB"] = self.work_path 
        
        # معرفی مسیر پکیج‌های هودینی (برای لود شدن خودکار شلف و تنظیمات)
        self.env["HOUDINI_PACKAGE_DIR"] = houdini_plugin_dir
        
        # باز کردن کنسول هودینی برای مشاهده لاگ‌های کورتکس
        self.env["HOUDINI_WINDOW_CONSOLE"] = "1"
        
        try:
            # ۵. اجرای هودینی با محیط ایزوله شده (env)
            subprocess.Popen([exe_path], env=self.env)
            return True, "Houdini Launched with Cortex Professional Engine!"
        except Exception as e:
            return False, f"Houdini Launch Failed: {str(e)}"

# ----------------------------
# Blender Launcher
# ----------------------------
class BlenderLauncher(BaseLauncher):
    def __init__(self, session):
        """
        Handle   Init   operation.
        """
        super().__init__(session)
        self.software_dir = "blender" # نام فولدر در مسیر ورک

    def launch(self):
        """
        Handle Launch operation.
        """
        if self.allowed_sw.lower() != "all" and "blender" not in self.allowed_sw.lower():
            return False, f"❌ Access Denied! This task is locked to: {self.allowed_sw.upper()}"

        # 1. گرفتن مسیر فایل exe
        settings = QSettings("Cortex", "Pipeline")
        exe_path = settings.value("blender_path", "")
        
        if not exe_path or not os.path.exists(exe_path):
            return False, "Blender path is not set. Go to Utilities tab."

        # 2. پیدا کردن مسیر startup.py مخصوص بلندر
        # مسیر: plugins/blender/startup.py
        current_file_path = os.path.abspath(__file__)
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file_path)))
        script_path = os.path.join(root_dir, "plugins", "blender", "startup.py")
        
        # 3. دستور اجرا
        # بلندر برخلاف مکس، اسکریپت را با فلگ --python اجرا می‌کند
        cmd = [exe_path]
        
        if os.path.exists(script_path):
            print(f"Loading Blender Startup: {script_path}")
            # دستور: blender.exe --python path/to/startup.py
            cmd.extend(["--python", script_path])
        else:
            print(f"Warning: Blender startup script not found at {script_path}")

        try:
            # اجرای بلندر با متغیرهای محیطی کورتکس
            subprocess.Popen(cmd, env=self.env)
            return True, "Blender Launched Successfully!"
        except Exception as e:
            return False, str(e)
        



# ----------------------------
# Photoshop Launcher
# ----------------------------
class PhotoshopLauncher(BaseLauncher):
    def __init__(self, session):
        super().__init__(session)
        self.software_dir = "photoshop"

    def launch(self):
        # بررسی دسترسی دپارتمان
        if self.allowed_sw.lower() != "all" and "photoshop" not in self.allowed_sw.lower():
            return False, f"❌ Access Denied! Task locked to: {self.allowed_sw.upper()}"

        settings = QSettings("Cortex", "Pipeline")
        exe_path = settings.value("photoshop_path", "")

        if not exe_path or not os.path.exists(exe_path):
            return False, "Photoshop path is not set in Settings > Utilities."
        
        # ۱. باز کردن خود فتوشاپ
        try:
            subprocess.Popen([exe_path], env=self.env)
            
            # ۲. پیدا کردن و اجرای استارتاپ کورتکس به صورت مستقل
            # حالا self.root_dir به درستی کار می‌کند
            startup_path = os.path.join(self.root_dir, "plugins", "photoshop", "startup.py")
            
            if os.path.exists(startup_path):
                subprocess.Popen(
                    [sys.executable, startup_path], 
                    env=self.env,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS if os.name == 'nt' else 0
                )
            
            return True, "Photoshop Launched & Toolbar Initializing..."
        except Exception as e:
            return False, str(e)