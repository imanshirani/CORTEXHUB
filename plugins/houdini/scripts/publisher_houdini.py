# Location: plugins/houdini/scripts/publisher_houdini.py
import hou
import os
import sys

try:
    root = os.environ.get("CORTEX_PIPELINE")
    if root and root not in sys.path:
        sys.path.append(root)
except:
    pass

from app.core.database import DatabaseManager

def capture_thumbnail(output_path):
    """Flipbook the Houdini viewport for a preview"""
    try:
        desktop = hou.ui.curDesktop()
        scene_viewer = desktop.paneTabOfType(hou.paneTabType.SceneViewer)
        if not scene_viewer: return False
        viewport = scene_viewer.curViewport()
        settings = scene_viewer.flipbookSettings().stash()
        settings.frameRange((hou.intFrame(), hou.intFrame()))
        settings.output(output_path)
        settings.resolution((960, 540))
        scene_viewer.flipbook(viewport, settings)
        return True
    except Exception as e:
        print(f"!! [Cortex] Thumbnail Error: {e}")
        return False

def run_publish_logic(node):
    db = DatabaseManager()
    
    task_id = os.environ.get("CORTEX_TASK_ID")
    user = os.environ.get("CORTEX_USER", "HoudiniArtist")
    
    if not task_id:
        hou.ui.displayMessage("Error: Please launch Houdini via Cortex HUB!")
        return

    output_type = node.parm("out_type").evalAsString()
    target_path = node.parm("target_node").evalAsNode()
    comment = node.parm("comment").evalAsString()
    
    if not target_path:
        hou.ui.displayMessage("Please select a Target Node to export (e.g., /obj/box_object1/OUT_BOX)")
        return

    # Task name becomes a subfolder (e.g. BODY or HEAD)
    task_name = os.environ.get("CORTEX_TASK_NAME", "out").replace(" ", "_")

    dest_cache = db.get_publish_path(task_id, software=output_type, category="3d")
    dest_hip = db.get_publish_path(task_id, software="houdini", category="3d")

    if not dest_cache or not dest_hip:
        hou.ui.displayMessage("Error: Could not resolve publish path from database.")
        return

    # --- Add the task subfolder to publish paths ---
    dest_cache = os.path.join(dest_cache, task_name).replace("\\", "/")
    dest_hip = os.path.join(dest_hip, task_name).replace("\\", "/")
    # -----------------------------------------------

    os.makedirs(dest_cache, exist_ok=True)
    os.makedirs(dest_hip, exist_ok=True)

    ver = db.get_latest_version(task_id) + 1
    
    cache_filename = f"{task_name}_v{ver:03d}.{output_type}"
    hip_filename = f"{task_name}_v{ver:03d}.hip"
    thumb_name = f"{task_name}_v{ver:03d}_thumb.jpg"
    
    final_cache_path = os.path.join(dest_cache, cache_filename).replace("\\", "/")
    final_hip_path = os.path.join(dest_hip, hip_filename).replace("\\", "/")
    thumb_path = os.path.join(dest_hip, thumb_name).replace("\\", "/")

    print(f">> [Cortex] Starting Publish Process...")
    print(f">> [Cortex] Target Cache Path: {final_cache_path}")

    try:
        # a) Save the main Houdini file
        hou.hipFile.save(final_hip_path)
        capture_thumbnail(thumb_path)
        
        # c) Export data (ABC or VDB)
        if output_type == "vdb":
            target_path.geometry().saveToFile(final_cache_path)
            print(">> [Cortex] VDB Export Complete.")
            
        elif output_type == "abc":
            print(">> [Cortex] Exporting Alembic (Please wait...)")
            
            if target_path.type().category() == hou.sopNodeTypeCategory():
                rop = target_path.parent().createNode("rop_alembic")
                rop.setInput(0, target_path)
                rop.parm("filename").set(final_cache_path)
                rop.parm("trange").set(1) 
                rop.render() 
                rop.destroy()
            else:
                rop = hou.node("/out").createNode("alembic")
                rop.parm("objects").set(target_path.path())
                rop.parm("filename").set(final_cache_path)
                rop.parm("trange").set(1)
                rop.render()
                rop.destroy()
                
            print(">> [Cortex] Alembic Export Complete.")
            
        # 4. Register in the database
        db.create_publish(
            task_id=task_id,
            version=ver,
            comment=comment if comment else "Published from Houdini",
            user_name=user,
            thumbnail_path=thumb_path if os.path.exists(thumb_path) else "",
            files_dict={
                "houdini": final_hip_path,
                output_type: final_cache_path
            }
        )
        
        print(f">> [Cortex] SUCCESS! Cache saved to: {final_cache_path}")
        hou.ui.displayMessage(f"🚀 Success! \nCache: {final_cache_path}\nScene: {final_hip_path}")
        
    except Exception as e:
        print(f"!! [Cortex] Publish Failed: {str(e)}")
        hou.ui.displayMessage(f"Publish Failed: {str(e)}")

def run():
    import hda_creator
    import importlib
    importlib.reload(hda_creator)
    hda_creator.create_cortex_node()