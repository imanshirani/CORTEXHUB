# Location: plugins/maya/publisher_maya.py
import sys
import os
import shutil
import maya.cmds as cmds  # معادل pymxs در مکس
from PySide6.QtWidgets import QMessageBox

# =========================================================
# PATH FIX (برای دسترسی به هسته اپلیکیشن)
# =========================================================
try:
    current_script_path = os.path.dirname(os.path.abspath(__file__))
    # بازگشت به ریشه پروژه (Cortex_Pipeline)
    root_path = os.path.dirname(os.path.dirname(current_script_path))
    if root_path not in sys.path:
        sys.path.append(root_path)
except Exception as e:
    print(f"!! Error setting up path: {e}")

from app.core.database import DatabaseManager
from app.ui.publish_dialog import PublishDialog

class MayaPublisher:
    def __init__(self):
        """Initializes the Maya Publisher context."""
        self.db = DatabaseManager()
        self.task_id = os.environ.get("CORTEX_TASK_ID")
        self.work_path = os.environ.get("CORTEX_WORK_PATH") 
        self.user = os.environ.get("CORTEX_USER", "Unknown")
        self.software = "maya"

    def show_dialog(self):
        """Displays the Cortex Publish Dialog inside Maya."""
        if not self.task_id:
            QMessageBox.critical(None, "Context Error", "Please launch Maya from Cortex.")
            return

        # شبیه‌سازی Session برای دیالوگ
        class MockSession:
            def __init__(self, db): self.db = db
        session = MockSession(self.db)
        
        # در مایا نیازی به qtmax نیست، مستقیماً از دیالوگ استفاده می‌کنیم
        parent = None 

        # تشخیص دپارتمان برای فعال کردن گزینه‌های خروجی
        task_data = self.db.get_task_by_id(self.task_id)
        dept_name = task_data[2].lower() if task_data else "general"
        maya_opts = self.get_maya_options(dept_name)
            
        # گرفتن اسکرین‌شات از ویوپورت مایا برای تامنیل
        temp_thumb = os.path.join(os.environ["TEMP"], "cortex_maya_thumb.jpg")
        try:
            # دستور مایا برای ذخیره ویوپورت فعلی
            cmds.playblast(frame=cmds.currentTime(q=True), format="image", 
                           viewer=False, compression="jpg", completeFilename=temp_thumb,
                           widthHeight=[480, 270])
        except:
            temp_thumb = None

        self.dialog = PublishDialog(
            session, 
            self.task_id, 
            parent=parent, 
            thumbnail_path=temp_thumb,
            output_config=maya_opts
        )

        if self.dialog.exec():
            data = self.dialog.get_data()
            if self.validate(data):
                self.run_publish_process(data)

    def get_maya_options(self, dept_name):
        """Returns export options specific to Maya."""
        options = []
        options.append({'key': 'source', 'label': 'Maya Scene (.mb)', 'checked': True, 'enabled': False})
        
        if "lookdev" in dept_name:
            options.append({'key': 'maya_shader', 'label': 'Maya Shader Network', 'checked': True, 'enabled': True})
        else:
            options.append({'key': 'alembic', 'label': 'Alembic Cache (.abc)', 'checked': True, 'enabled': True})
            options.append({'key': 'export_geo', 'label': 'Export FBX (.fbx)', 'checked': True, 'enabled': True})
            
        return options

    def run_publish_process(self, data):
        """Executes the actual saving and exporting in Maya using Dynamic Paths."""
        import shutil 
        version_num = data['version']
        comment = data['comment']
        outputs = data['outputs']
        
        current_file = cmds.file(q=True, sn=True)
        if not current_file:
            QMessageBox.warning(None, "Error", "Please save your Maya file first.")
            return

        dest_3d = self.db.get_publish_path(self.task_id, software=self.software, category="3d")
        if not dest_3d:
            QMessageBox.critical(None, "Error", "Could not resolve publish path from database.")
            return

        task_name = os.environ.get("CORTEX_TASK_NAME", "out").replace(" ", "_")
        
        dest_3d = os.path.join(dest_3d, task_name).replace("\\", "/")
            
        dest_obj = self.db.get_publish_path(self.task_id, software="obj", category="3d")
        if dest_obj: dest_obj = os.path.join(dest_obj, task_name).replace("\\", "/")
        
        dest_abc = self.db.get_publish_path(self.task_id, software="abc", category="3d")
        if dest_abc: dest_abc = os.path.join(dest_abc, task_name).replace("\\", "/")

        if not os.path.exists(dest_3d): os.makedirs(dest_3d)
        if dest_obj and not os.path.exists(dest_obj): os.makedirs(dest_obj)
        if dest_abc and not os.path.exists(dest_abc): os.makedirs(dest_abc)

        published_files = {}

        try:
            # 1. Save Scene
            print(">> Saving Work File...")
            cmds.file(save=True, force=True)

            thumb_source = getattr(self.dialog, 'thumbnail_path', None)
            if thumb_source and os.path.exists(thumb_source):
                work_thumb = os.path.splitext(current_file)[0] + ".jpg"
                try: shutil.copy2(thumb_source, work_thumb)
                except: pass

            # 2. Publish Maya File
            if 'source' in outputs:
                pub_path = os.path.join(dest_3d, os.path.basename(current_file)).replace("\\", "/")
                shutil.copy2(current_file, pub_path)
                published_files['source_maya'] = pub_path
                print(f">> Published Maya: {pub_path}")

                if thumb_source and os.path.exists(thumb_source):
                    pub_thumb = os.path.splitext(pub_path)[0] + ".jpg"
                    try: shutil.copy2(thumb_source, pub_thumb)
                    except: pass

            # 3. Alembic Export
            if 'alembic' in outputs:
                if not cmds.pluginInfo("AbcExport", q=True, loaded=True):
                    cmds.loadPlugin("AbcExport")
                
                # رفع باگ نامگذاری: حالا دقیقاً مثل هودینی و مکس اسم می‌گیرد (مثلا BODY_v002.abc)
                abc_name = f"{task_name}_v{version_num:03d}.abc"
                abc_path = os.path.join(dest_abc, abc_name).replace("\\", "/")
                
                print(f">> Exporting Alembic: {abc_name}")
                
                # رفع باگ Root: پیدا کردن تمام آبجکت‌های اصلی (Top-level) در صحنه
                top_nodes = cmds.ls(assemblies=True)
                if not top_nodes:
                    raise Exception("Scene is empty! Nothing to export.")
                    
                root_args = " ".join([f"-root {node}" for node in top_nodes])
                
                # اکسپورت با استفاده از نودهای پیدا شده
                cmds.AbcExport(j=f"-frameRange 1 1 {root_args} -file \"{abc_path}\"")
                published_files['alembic'] = abc_path

            # 4. FBX Export
            if 'export_geo' in outputs:
                if not cmds.pluginInfo("fbxmaya", q=True, loaded=True):
                    cmds.loadPlugin("fbxmaya")
                
                # رفع باگ نامگذاری FBX
                fbx_name = f"{task_name}_v{version_num:03d}.fbx"
                fbx_path = os.path.join(dest_obj, fbx_name).replace("\\", "/")
                
                print(f">> Exporting FBX: {fbx_name}")
                cmds.file(fbx_path, force=True, options="v=0;", typ="FBX export", pr=True, ea=True)
                published_files['export_geo'] = fbx_path

            # ثبت در دیتابیس
            success, pub_id = self.db.create_publish(
                task_id=self.task_id,
                version=version_num,
                comment=comment,
                user_name=self.user,
                thumbnail_path=thumb_source,
                files_dict=published_files
            )
            
            if success:
                QMessageBox.information(None, "Success", f"Maya Publish v{version_num:03d} Done!")
            else:
                QMessageBox.critical(None, "DB Error", "Failed to register publish in DB.")

        except Exception as e:
            QMessageBox.critical(None, "Publish Failed", str(e))
            print(f"!! Maya Publish Error: {e}")

    def get_publish_root(self):
        """Helper to find the asset root folder."""
        # همان منطقی که در مکس داشتی اینجا هم کار می‌کند
        parts = self.work_path.replace("\\", "/").split("/")
        for i, p in enumerate(parts):
            if p.lower() == "work":
                return "/".join(parts[:i])
        return self.work_path

    def validate(self, data):
        """Basic validation for Maya scene."""
        # اینجا می‌توانیم چک کنیم که مثلاً اسمی خالی نباشد یا تاریخچه (History) پاک شده باشد
        return True
    
    def export_lookdev_assets(self):
        """فراخوانی سیستم بسته‌بندی متریال مایا با مسیر دقیق"""
        try:
            import publisher_mat_maya
            import importlib
            importlib.reload(publisher_mat_maya)
            
            engine = self.db.get_setting("render_engine", default="Arnold") 
            task_name = os.environ.get("CORTEX_TASK_NAME", "out").replace(" ", "_")
            
            # ساخت مسیر دقیق: publish/3D/lookdev/TASK_NAME
            lookdev_base = self.db.get_publish_path(self.task_id, software="lookdev", category="3d")
            if not lookdev_base:
                lookdev_base = os.path.join(self.get_publish_root(), "publish", "3D", "lookdev").replace("\\", "/")
                
            final_mat_path = os.path.join(lookdev_base, task_name).replace("\\", "/")
            
            mat_pub = publisher_mat_maya.MaterialPublisher(final_mat_path)
            mat_pub.publish(engine)
            
        except Exception as e:
            print(f"!! [Cortex] Error in Maya Lookdev Export: {e}")

def run():
    publisher = MayaPublisher()
    publisher.show_dialog()