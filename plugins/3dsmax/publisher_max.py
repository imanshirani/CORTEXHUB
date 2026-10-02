import sys
import os
import shutil
import pymxs
from PySide6.QtWidgets import QMessageBox

# =========================================================
# PATH FIX
# =========================================================
try:
    current_script_path = os.path.dirname(os.path.abspath(__file__))
    root_path = os.path.dirname(os.path.dirname(current_script_path))
    if root_path not in sys.path:
        sys.path.append(root_path)
except Exception as e:
    print(f"!! Error setting up path: {e}")

from app.core.database import DatabaseManager
from app.ui.publish_dialog import PublishDialog
import style  # Local style (plugins/3dsmax/style.py)

rt = pymxs.runtime

class MaxPublisher:
    def __init__(self):
        """
        Handle   Init   operation.
        """
        self.db = DatabaseManager()
        self.task_id = os.environ.get("CORTEX_TASK_ID")
        self.work_path = os.environ.get("CORTEX_WORK_PATH") 
        self.user = os.environ.get("CORTEX_USER", "Unknown")
        self.entity_type = os.environ.get("CORTEX_ENTITY_TYPE", "Asset") 
        
        self.software = "max"
        if self.work_path and "maya" in self.work_path.lower(): self.software = "maya"
        elif self.work_path and "blender" in self.work_path.lower(): self.software = "blender"

    def show_dialog(self):
        """
        Handle Show Dialog operation.
        """
        if not self.task_id:
            QMessageBox.critical(None, "Context Error", "Please launch Max from Cortex.")
            return

        class MockSession:
            def __init__(self, db): self.db = db
                
        session = MockSession(self.db)
        
        try:
            import qtmax
            parent = qtmax.GetQMaxMainWindow()
        except:
            parent = None

        # --- Detect department and build the option list ---
        task_data = self.db.get_task_by_id(self.task_id)
        dept_name = task_data[2].lower() if task_data else "general"
        
        # Call get_max_options on the class
        max_opts = self.get_max_options(dept_name)
        # ---------------------------------------------------
            
        # --- STEP 1: grab a still for the UI ---
        temp_thumb = os.path.join(os.environ["TEMP"], "cortex_pub_preview.jpg")
        try:
            bmp = rt.gw.getViewportDib()
            bmp.filename = temp_thumb
            rt.save(bmp)
        except:
            temp_thumb = None

        # Build the dialog
        self.dialog = PublishDialog(
            session, 
            self.task_id, 
            parent=parent, 
            thumbnail_path=temp_thumb,
            output_config=max_opts  # <--- wire the list into the dialog
        )
        
        # Apply style
        self.dialog.setStyleSheet(style.PUBLISH_DIALOG)
        
        

        if self.dialog.exec():
            data = self.dialog.get_data()
            
            # Continue (validation, ...)
            print(">> [Cortex] Running Validations...")
            if self.validate(data) is False:
                print(">> [Cortex] PUBLISH STOPPED: Validation failed.")
                return 
            
            self.run_publish_process(data)
            
            # If lookdev and the material checkbox is on
            if 'native_lib' in data['outputs'] or 'mat_lib' in data['outputs']:
                self.export_lookdev_assets()

    def get_max_options(self, dept_name):
        """
        Handle Get Max Options operation.
        """
        options = []
        is_lookdev = "lookdev" in dept_name
        
        options.append({'key': 'source', 'label': 'Source Max File (.max)', 'checked': True, 'enabled': False})
        
        if is_lookdev:
            options.append({'key': 'mat_lib', 'label': 'OpenPBR Material Library (.mat)', 'checked': True, 'enabled': False})
            options.append({'key': 'native_lib', 'label': 'Native Engine Library', 'checked': True, 'enabled': True})
        else:
            options.append({'key': 'alembic', 'label': 'Alembic Cache (.abc)', 'checked': True, 'enabled': True})
            options.append({'key': 'export_geo', 'label': 'Export FBX (.fbx)', 'checked': True, 'enabled': True})
            
        options.append({'key': 'playblast', 'label': 'Playblast Video (.mp4)', 'checked': False, 'enabled': True})
        return options
    
    def get_publish_root(self):
        """Find the asset root so we can reach the 3d and publish folders"""
        if not self.work_path: return ""
        
        parts = self.work_path.replace("\\", "/").split("/")
        try:
            # Find the Work folder index to walk back to the asset root
            work_idx = -1
            for i, p in enumerate(parts):
                if p.lower() == "work":
                    work_idx = i
                    break
            
            if work_idx != -1:
                # Path to the asset root (e.g. .../Assets/Characters/Hero)
                return "/".join(parts[:work_idx])
        except:
            pass
        return self.work_path

    def run_publish_process(self, data):
        """
        Handle Run Publish Process operation using Dynamic Database Paths.
        """
        version_num = data['version']
        comment = data['comment']
        outputs = data['outputs']
        
        current_max_file = os.path.join(rt.sysInfo.currentDir, rt.maxFileName).replace("\\", "/")
        if not rt.maxFileName: 
            QMessageBox.warning(None, "Error", "Please save the file first.")
            return

        # 1. Read the main path from the database
        dest_3d = self.db.get_publish_path(self.task_id, software=self.software, category="3d")
        if not dest_3d:
            QMessageBox.critical(None, "Error", "Could not resolve publish path from database.")
            return

        # --- Extract the task name and build subfolders ---
        task_name = os.environ.get("CORTEX_TASK_NAME", "out").replace(" ", "_")
        
        dest_3d = os.path.join(dest_3d, task_name).replace("\\", "/")
            
        dest_obj = self.db.get_publish_path(self.task_id, software="obj", category="3d")
        if dest_obj: dest_obj = os.path.join(dest_obj, task_name).replace("\\", "/")
        
        dest_abc = self.db.get_publish_path(self.task_id, software="abc", category="3d")
        if dest_abc: dest_abc = os.path.join(dest_abc, task_name).replace("\\", "/")
        # ---------------------------------------------------
        
        base_render = self.db.get_publish_path(self.task_id, software="previews", category="renders")
        dest_render = os.path.join(base_render, f"v{version_num:03d}").replace("\\", "/") if base_render else ""

        # Create the max folder if missing
        if not os.path.exists(dest_3d): 
            os.makedirs(dest_3d)
        if dest_obj and not os.path.exists(dest_obj): 
            os.makedirs(dest_obj)
        if dest_abc and not os.path.exists(dest_abc): 
            os.makedirs(dest_abc)

        # Asset name (e.g. Hero) from the generated path
        publish_root = os.path.dirname(os.path.dirname(os.path.dirname(dest_3d)))
        asset_name = os.path.basename(publish_root)

        published_files = {}

        try:
            # 1. Save Work
            print(">> Saving Work File...")
            rt.saveMaxFile(current_max_file)

            # 2. Publish Max File
            if 'source' in outputs:
                file_name = os.path.basename(current_max_file)
                pub_max_path = os.path.join(dest_3d, file_name).replace("\\", "/")
                shutil.copy2(current_max_file, pub_max_path)
                published_files['source_max'] = pub_max_path
                print(f">> Published Max: {pub_max_path}")

            # 3. Alembic Export (REAL)
            if 'alembic' in outputs:
                if not os.path.exists(dest_abc): os.makedirs(dest_abc)
                
                abc_name = f"{asset_name}_{os.path.splitext(os.path.basename(current_max_file))[0]}.abc"
                abc_path = os.path.join(dest_abc, abc_name).replace("\\", "/")
                
                print(f">> Exporting Alembic: {abc_name}")
                if len(rt.selection) == 0: 
                    rt.select(rt.geometry)
                
                try:
                    rt.exportFile(abc_path, rt.name("noPrompt"), selectedOnly=True, using=rt.Alembic_Export)
                    published_files['alembic_cache'] = abc_path
                except Exception as e:
                    print(f"!! Alembic Export Failed: {e}")

            # 4. Playblast / Preview (REAL)
            if 'playblast' in outputs and dest_render:
                if not os.path.exists(dest_render): os.makedirs(dest_render)
                vid_path = os.path.join(dest_render, "preview.avi").replace("\\", "/")
                
                print(">> Generating Preview...")
                try:
                    rt.createPreview(
                        filename=vid_path, 
                        outputscale=100, 
                        percent=100, 
                        dspGeometry=True, 
                        dspShapes=False, 
                        dspLights=False, 
                        dspCameras=False, 
                        dspHelpers=False,
                        dspParticles=True,
                        dspBones=False 
                    )
                    published_files['playblast'] = vid_path
                except Exception as e:
                    print(f"!! Preview Failed: {e}")

            # 5. FBX Export (REAL)
            if 'export_geo' in outputs:
                if not os.path.exists(dest_obj): os.makedirs(dest_obj)
                
                fbx_name = f"{asset_name}_{os.path.splitext(os.path.basename(current_max_file))[0]}.fbx"
                fbx_path = os.path.join(dest_obj, fbx_name).replace("\\", "/")
                
                print(f">> Exporting FBX: {fbx_name}")
                try:
                    rt.exportFile(fbx_path, rt.name("noPrompt"), selectedOnly=True, using=rt.FBXEXP)
                    published_files['export_geo'] = fbx_path
                except Exception as e:
                    print(f"!! FBX Export Failed: {e}")
            
            # 6. Thumbnail (Final)
            thumb_path = os.path.join(dest_3d, os.path.splitext(os.path.basename(current_max_file))[0] + "_thumb.jpg").replace("\\", "/")
            try:
                bmp = rt.gw.getViewportDib()
                bmp.filename = thumb_path
                rt.save(bmp)
            except: pass

            # 7. Database
            success, pub_id = self.db.create_publish(
                task_id=self.task_id,
                version=version_num,
                comment=comment,
                user_name=self.user,
                thumbnail_path=thumb_path,
                files_dict=published_files
            )

            if success:
                QMessageBox.information(None, "Success", f"Publish v{version_num:03d} Done!")
                self.version_up_work_file(current_max_file)
            else:
                QMessageBox.critical(None, "DB Error", f"DB Failed: {pub_id}")

        except Exception as e:
            QMessageBox.critical(None, "Publish Failed", str(e))
            print(f"!! Publish Error: {e}")

    def version_up_work_file(self, current_path):
        """Create a new version in the work area plus a screenshot"""
        try:
            folder = os.path.dirname(current_path)
            filename = os.path.basename(current_path)
            
            if "_v" in filename.lower():
                parts = filename.lower().split("_v")
                base = filename[:len(parts[0])]
                ver_ext = parts[-1]
                ver_str = ver_ext.split(".")[0]
                ext = ver_ext.split(".")[1]
                
                if ver_str.isdigit():
                    new_ver = int(ver_str) + 1
                    new_filename = f"{base}_v{new_ver:03d}.{ext}"
                    new_path = os.path.join(folder, new_filename)
                    
                    # 1. Save the new Max file
                    rt.saveMaxFile(new_path)
                    
                    # 2. Capture and store a thumbnail for the new version
                    new_thumb_path = new_path.replace(".max", ".jpg")
                    try:
                        bmp = rt.gw.getViewportDib()
                        bmp.filename = new_thumb_path
                        rt.save(bmp)
                        print(f">> [Cortex] New Work Version & Thumbnail Created: v{new_ver:03d}")
                    except:
                        print("!! Warning: Failed to create thumbnail for new version.")
        except Exception as e:
            print(f"!! Version Up Error: {e}")
            
    #-----------------
    # Validate Data
    #-----------------
    def validate(self, data):
        """
        Handle Validate operation.
        """
        self.errors = []
        self.warnings = []
        # 1. Check the selection first
        #self._validate_max_selection(is_mandatory=True)
        
        # 2. Define a global list in MaxScript
        rt.execute("global cortex_errors = #()")
        rt.execute("cortex_errors = #()") # Reset the list for each validation pass
        
        project_id = os.environ.get("CORTEX_PROJECT_ID")
        rules = self.db.get_validation_rules_with_scripts(project_id, self.software)
        
        for rule in rules:
            script_content = rule.get('rule_script')
            if not script_content: continue

            try:
                # If the rule is Python
                if script_content.strip().startswith(("import", "from")) or "pymxs" in script_content:
                    exec(script_content, {"rt": rt, "errors": self.errors, "pymxs": pymxs, "os": os})
                else:
                    # If the rule is MaxScript
                    rt.execute(script_content)
            except Exception as e:
                self.errors.append(f"❌ Script Error in {rule.get('rule_key')}: {e}")

        # 3. Copy MaxScript errors into the Python list
        mx_errors = list(rt.cortex_errors)
        if mx_errors:
            self.errors.extend([str(err) for err in mx_errors])

        # 4. The final output can now stop the publish
        return self._show_validation_results()
    
    

    def _show_validation_results(self):
        """
        Handle  Show Validation Results operation.
        """
        # self.warnings is defined above, so this no longer errors
        if self.errors:
            QMessageBox.critical(None, "Validation Failed", "\n".join(self.errors))
            return False
        
        if self.warnings:
            msg = "\n".join(self.warnings) + "\n\nDo you want to continue anyway?"
            res = QMessageBox.warning(None, "Validation Warning", msg, QMessageBox.Yes | QMessageBox.No)
            return res == QMessageBox.Yes
        return True
    
    def _validate_max_selection(self, is_mandatory):
        """Check that something is selected in Max"""
        import pymxs
        if len(pymxs.runtime.selection) == 0:
            msg = "❌ Selection: Nothing is selected in Max!"
            if is_mandatory: self.errors.append(msg)
            else: self.warnings.append(msg)

    def run_lookdev_publish(self, data):
        """
        Handle Run Lookdev Publish operation.
        """
        # 1. Validation: artist must use only OpenPBR materials
        for mat in rt.getSceneMaterials():
            if "OpenPBR" not in str(type(mat)):
                self.errors.append(f"❌ Material Error: {mat.name} is not an OpenPBR material!")
        
        if not self._show_validation_results(): return

        # 2. Export shaders on their own
        # In Max 2026, OpenPBR integrates well with MaterialX
        mat_path = os.path.join(self.get_publish_root(), "lookdev", "master_materials.mtlx")
        # Export materials as MaterialX/OpenPBR
        
        # 3. Save the Max file as the lookdev source
        self.run_publish_process(data)

    def run_lookdev_special(self):
        """Run the lookdev-specific publish (dedicated buttons)"""
        
        if not self.task_id:
            QMessageBox.critical(None, "Error", "No Task Context!")
            return

        class MockSession:
            def __init__(self, db): self.db = db
                
        session = MockSession(self.db)
        
        try:
            import qtmax
            parent = qtmax.GetQMaxMainWindow()
        except: parent = None

        # --- FIX: lookdev option list ---
        # Pass "lookdev" so material options turn on
        lookdev_opts = self.get_max_options("lookdev") 
        # ---------------------------------------------

        # Open the dialog with that config
        self.dialog = PublishDialog(
            session, 
            self.task_id, 
            parent=parent,
            output_config=lookdev_opts  # <--- required
        )
        self.dialog.setWindowTitle("💎 Lookdev Master Publish") 
        self.dialog.setStyleSheet(style.PUBLISH_DIALOG)

        if self.dialog.exec():
            data = self.dialog.get_data()
            print(">> [Cortex] Lookdev Publish started...")
            
            # 1. Publish the Max file
            self.run_publish_process(data)
            
            # 2. Export materials if the checkbox is on
            if 'native_lib' in data['outputs'] or 'mat_lib' in data['outputs']:
                self.export_lookdev_assets()

    def export_lookdev_assets(self):
        """Call the material packager with no conversion"""
        try:
            import publisher_mat_max
            import importlib
            importlib.reload(publisher_mat_max)
            
            # Read the engine from the database
            engine = self.db.get_setting("render_engine", default="Octane") 
            task_name = os.environ.get("CORTEX_TASK_NAME", "out").replace(" ", "_")
            
            # Exact path: publish/3D/lookdev/TASK_NAME
            lookdev_base = self.db.get_publish_path(self.task_id, software="lookdev", category="3d")
            if not lookdev_base:
                # Fallback path if the database has none
                lookdev_base = os.path.join(self.get_publish_root(), "publish", "3D", "lookdev").replace("\\", "/")
                
            final_mat_path = os.path.join(lookdev_base, task_name).replace("\\", "/")
            
            # Send the exact path to the material publisher
            mat_pub = publisher_mat_max.MaterialPublisher(final_mat_path)
            mat_pub.publish(engine)
            
        except Exception as e:
            print(f"!! Material Export Failed: {e}")

def run():
    """
    Handle Run operation.
    """
    publisher = MaxPublisher()
    publisher.show_dialog()