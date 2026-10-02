import sys
import os
import shutil
import bpy
from PySide6.QtWidgets import QMessageBox

try:
    current_script_path = os.path.dirname(os.path.abspath(__file__))
    root_path = os.path.dirname(os.path.dirname(current_script_path))
    if root_path not in sys.path: sys.path.append(root_path)
except: pass

from app.core.database import DatabaseManager
from app.ui.publish_dialog import PublishDialog
import style

class BlenderPublisher:
    def __init__(self):
        """
        Handle   Init   operation.
        """
        self.db = DatabaseManager()
        self.task_id = os.environ.get("CORTEX_TASK_ID")
        self.work_path = os.environ.get("CORTEX_WORK_PATH")
        self.user = os.environ.get("CORTEX_USER", "Unknown")
        self.software = "blender"

    def get_3d_view_context(self):
        """
        Find a valid window and 3D region for operators
        """
        for window in bpy.context.window_manager.windows:
            screen = window.screen
            for area in screen.areas:
                if area.type == 'VIEW_3D':
                    for region in area.regions:
                        if region.type == 'WINDOW':
                            return window, screen, area, region
        return None, None, None, None

    def show_dialog(self):
        """
        Handle Show Dialog operation.
        """
        if not self.task_id:
            QMessageBox.critical(None, "Error", "No Context. Please use Loader.")
            return

        # 1. Task info
        task_data = self.db.get_task_by_id(self.task_id)
        dept_name = task_data[2].lower() if task_data else "general"
        
        # 2. Blender settings (checkboxes)
        blender_opts = self.get_blender_options(dept_name)

        class MockSession:
            def __init__(self, db):
                self.db = db
        session = MockSession(self.db)

        # 3. Take the still first
        temp_thumb = None 
        # Temp image path
        temp_thumb_path = os.path.join(os.environ["TEMP"], "cortex_blend_preview.jpg")
        
        window, screen, area, region = self.get_3d_view_context()
        
        if window and area:
            try:
                # Store current render settings
                scene = window.scene
                old_filepath = scene.render.filepath
                old_format = scene.render.image_settings.file_format
                
                # Configure for a still
                scene.render.image_settings.file_format = 'JPEG'
                scene.render.filepath = temp_thumb_path
                
                # Capture with override
                with bpy.context.temp_override(window=window, screen=screen, area=area, region=region):
                    bpy.ops.render.opengl(write_still=True)
                
                # Confirm the image was written
                if os.path.exists(temp_thumb_path):
                    temp_thumb = temp_thumb_path
                
                # Restore settings
                scene.render.filepath = old_filepath
                scene.render.image_settings.file_format = old_format
                
            except Exception as e:
                print(f"Thumbnail Capture Failed: {e}")
                temp_thumb = None
        else:
            print(">> [Cortex Warning] No 3D View found for thumbnail.")

        # 4. Build and show the dialog (temp_thumb is set)
        self.dialog = PublishDialog(
            session, 
            self.task_id, 
            parent=None, 
            thumbnail_path=temp_thumb, 
            output_config=blender_opts 
        )
        self.dialog.setStyleSheet(style.PUBLISH_DIALOG)
        
        # Change the title if needed
        if "lookdev" in dept_name:
            self.dialog.setWindowTitle("💎 Lookdev Master Publish")
        elif "model" in dept_name:
            self.dialog.setWindowTitle("📦 Modeling Publish")

        # 5. Run the dialog
        if self.dialog.exec():
            data = self.dialog.get_data()
            
            # Validation first
            if self.validate(data) is False:
                return

            # Then the publish
            if "lookdev" in dept_name:
                self.run_lookdev_process(data)
            else:
                self.run_publish_process(data)

    

    def get_publish_root(self):
        """Find the asset root in the Blender layout: Work/blender/Dept/Task"""
        if not self.work_path: return ""
        parts = self.work_path.replace("\\", "/").split("/")
        try:
            # Find the Work folder and walk three levels up
            for i, p in enumerate(parts):
                if p.lower() == "work":
                    return "/".join(parts[:i])
        except: pass
        return self.work_path
    
    def get_blender_options(self, dept_name):
        """Build the output list from the department for Blender"""
        options = []
        is_lookdev = "lookdev" in dept_name
        
        # 1. Source File
        options.append({
            'key': 'source', 
            'label': 'Source Blender File (.blend)', 
            'checked': True, 
            'enabled': False 
        })
        
        # 2. Smart Options
        if is_lookdev:
            options.append({
                'key': 'materials', 
                'label': 'Export Materials (.blend lib)', 
                'checked': True, 
                'enabled': True
            })
        else:
            options.append({'key': 'alembic', 'label': 'Alembic Cache (.abc)', 'checked': True, 'enabled': True})
            options.append({'key': 'export_geo', 'label': 'Export FBX (.fbx)', 'checked': True, 'enabled': True})
            
        # 3. Playblast
        options.append({'key': 'playblast', 'label': 'Playblast Video (.mp4)', 'checked': False, 'enabled': True})
        
        return options

    def run_publish_process(self, data):
        """
        Handle Run Publish Process operation.
        """
        version_num = data['version']
        comment = data['comment']
        outputs = data['outputs']
        
        current_file = bpy.data.filepath
        if not current_file:
            QMessageBox.warning(None, "Error", "Save file first!")
            return

        entity_root = self.get_publish_root()
        if not entity_root: return

        dest_3d = os.path.join(entity_root, "3d", "blender")
        if not os.path.exists(dest_3d): os.makedirs(dest_3d)
        
        dest_cache = os.path.join(entity_root, "3d", "cache", f"v{version_num:03d}")
        dest_render = os.path.join(entity_root, "renders", "previews", f"v{version_num:03d}")

        published_files = {}
        
        # 1. Correct context
        window, screen, area, region = self.get_3d_view_context()
        
        # 2. Dict for temp_override
        # Only fill it if window and region were found
        override_args = {}
        if window and area:
            override_args = {
                'window': window, 
                'screen': screen, 
                'area': area, 
                'region': region
            }

        try:
            # A. Save Work
            bpy.ops.wm.save_mainfile(filepath=current_file)
            
            # B. Publish Source
            if 'source' in outputs:
                filename = os.path.basename(current_file)
                pub_path = os.path.join(dest_3d, filename)
                shutil.copy2(current_file, pub_path)
                published_files['source_blender'] = pub_path
                print(f">> Published Blend: {pub_path}")

            # C. FBX Export
            if 'export_geo' in outputs:
                dest_obj = os.path.join(entity_root, "3d", "obj")
                if not os.path.exists(dest_obj): os.makedirs(dest_obj)
                
                # Asset name (e.g. Hero)
                asset_name = os.path.basename(entity_root)
                
                # New name: Hero_Head_v002.fbx
                fbx_name = f"{asset_name}_{os.path.splitext(os.path.basename(current_file))[0]}.fbx"
                fbx_path = os.path.join(dest_obj, fbx_name)
                
                if override_args:
                    print(f">> Exporting FBX: {fbx_name}")
                    with bpy.context.temp_override(**override_args):
                        bpy.ops.export_scene.fbx(filepath=fbx_path, use_selection=True, axis_forward='-Z', axis_up='Y')
                    published_files['export_geo'] = fbx_path

            # D. Alembic Export
            if 'alembic' in outputs:
                dest_obj = os.path.join(entity_root, "3d", "obj")
                if not os.path.exists(dest_obj): os.makedirs(dest_obj)
                
                asset_name = os.path.basename(entity_root)
                abc_name = f"{asset_name}_{os.path.splitext(os.path.basename(current_file))[0]}.abc"
                abc_path = os.path.join(dest_obj, abc_name)
                
                if override_args:
                    print(f">> Exporting Alembic: {abc_name}")
                    with bpy.context.temp_override(**override_args):
                        bpy.ops.wm.alembic_export(filepath=abc_path, selected=True)
                    published_files['alembic_cache'] = abc_path
            
            # E. Playblast
            if 'playblast' in outputs:
                if not os.path.exists(dest_render): os.makedirs(dest_render)
                vid_path = os.path.join(dest_render, "preview.avi")
                
                old_fp = bpy.context.scene.render.filepath
                old_fmt = bpy.context.scene.render.image_settings.file_format
                
                bpy.context.scene.render.image_settings.file_format = 'AVI_JPEG'
                bpy.context.scene.render.filepath = vid_path
                
                if override_args:
                    with bpy.context.temp_override(**override_args):
                        bpy.ops.render.opengl(animation=True)
                    published_files['playblast'] = vid_path
                
                # Restore settings
                bpy.context.scene.render.filepath = old_fp
                bpy.context.scene.render.image_settings.file_format = old_fmt

            # F. Thumbnail
            thumb_path = os.path.join(dest_3d, os.path.splitext(os.path.basename(current_file))[0] + "_thumb.jpg")
            
            old_fp = bpy.context.scene.render.filepath
            old_fmt = bpy.context.scene.render.image_settings.file_format
            bpy.context.scene.render.image_settings.file_format = 'JPEG'
            bpy.context.scene.render.filepath = thumb_path
            
            if override_args:
                with bpy.context.temp_override(**override_args):
                    bpy.ops.render.opengl(write_still=True)

            bpy.context.scene.render.filepath = old_fp
            bpy.context.scene.render.image_settings.file_format = old_fmt

            # G. DB
            success, pub_id = self.db.create_publish(
                task_id=self.task_id, version=version_num, comment=comment,
                user_name=self.user, thumbnail_path=thumb_path, files_dict=published_files
            )

            if success:
                QMessageBox.information(None, "Success", f"Publish v{version_num:03d} Done!")
                self.version_up_work_file(current_file)

        except Exception as e:
            QMessageBox.critical(None, "Error", str(e))
            print(f"!! Publish Error: {e}")
            import traceback
            traceback.print_exc()
    def export_lookdev_assets(self):
        """Call the Blender material packager"""
        try:
            import publisher_mat_blender
            import importlib
            importlib.reload(publisher_mat_blender)
            
            # Pass the asset root to the material publisher
            mat_pub = publisher_mat_blender.BlenderMaterialPublisher(self.get_publish_root())
            mat_pub.publish()
            
        except Exception as e:
            print(f"!! Blender Material Export Failed: {e}")

        
    def run_lookdev_publish(self, data):
        """Publish materials only when needed (same as Max)"""
        # 1. Did the user tick materials in the UI?
        if 'materials' not in data['outputs']:
            return

        print(">> [Cortex] Publishing Blender Native Materials...")
        
        # 2. Find the asset root and build publish/lookdev
        entity_root = self.get_publish_root()
        mat_path = os.path.join(entity_root, "publish", "lookdev", "materials")
        if not os.path.exists(mat_path): os.makedirs(mat_path)

        # 3. Save materials in a separate native file
        # Light file: shader data only
        filename = f"{os.path.basename(entity_root)}_mat_lib.blend"
        full_path = os.path.join(mat_path, filename)
        
        # Save material datablocks only
        bpy.ops.wm.save_as_mainfile(filepath=full_path, copy=True)

    def version_up_work_file(self, current_path):
        """
        Handle Version Up Work File operation.
        """
        try:
            folder = os.path.dirname(current_path)
            filename = os.path.basename(current_path)
            if "_v" in filename:
                parts = filename.split("_v")
                base = parts[0]
                ver_ext = parts[-1]
                ver_str = ver_ext.split(".")[0]
                ext = ver_ext.split(".")[1]
                if ver_str.isdigit():
                    new_ver = int(ver_str) + 1
                    new_name = f"{base}_v{new_ver:03d}.{ext}"
                    new_path = os.path.join(folder, new_name)
                    bpy.ops.wm.save_as_mainfile(filepath=new_path)
        except: pass


    #-----------------
    # Validate Data
    #-----------------
    def validate(self, data):
        """
        Handle Validate operation.
        """
        project_id = os.environ.get("CORTEX_PROJECT_ID")
        # Load rules including the script text from the database
        rules = self.db.get_validation_rules_with_scripts(project_id, self.software)
        
        self.errors = []
        self.warnings = []

        for rule in rules:
            # rule dict needs rule_script, is_mandatory, and rule_key
            script_content = rule.get('rule_script')
            if not script_content:
                continue

            # Script execution namespace
            local_vars = {
                "self": self, 
                "is_mandatory": rule.get('is_mandatory', 1),
                "errors": self.errors,     # Pass the error list through
                "warnings": self.warnings  # Pass the warning list through
            }
            
            try:
                # Run the script stored in the database
                exec(script_content, {}, local_vars)
            except Exception as e:
                self.errors.append(f"Validator Error ({rule.get('rule_key')}): {str(e)}")

        return self._show_validation_results()
    
    def _validate_naming(self, is_mandatory):
        """Check that the filename contains a version (shared)"""
        # Detect the file path from the DCC
        if self.software == "max":
            import pymxs
            current_file = pymxs.runtime.maxFileName
        else:
            import bpy
            current_file = bpy.data.filepath

        if "_v" not in current_file.lower():
            msg = "❌ Naming Error: Version suffix (_v001) is missing."
            if is_mandatory: self.errors.append(msg)
            else: self.warnings.append(msg)

    def _show_validation_results(self):
        """Show the final messages to the user"""
        if self.errors:
            QMessageBox.critical(None, "Validation Failed", "\n".join(self.errors))
            return False
        
        if self.warnings:
            msg = "\n".join(self.warnings) + "\n\nDo you want to continue anyway?"
            res = QMessageBox.warning(None, "Validation Warning", msg, QMessageBox.Yes | QMessageBox.No)
            return res == QMessageBox.Yes
        return True
    
    def _validate_blender_scale(self, is_mandatory):
        """Check that scale is applied in Blender"""
        import bpy
        for obj in bpy.context.selected_objects:
            if any(abs(s - 1.0) > 0.001 for s in obj.scale):
                msg = f"❌ Scale: '{obj.name}' scale is not applied (1,1,1)."
                if is_mandatory: self.errors.append(msg)
                else: self.warnings.append(msg)
    
def run():
    """
    Handle Run operation.
    """
    pub = BlenderPublisher()
    pub.show_dialog()