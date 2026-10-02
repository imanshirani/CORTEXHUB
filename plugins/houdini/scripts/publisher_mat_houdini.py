# Location: plugins/houdini/scripts/publisher_mat_houdini.py
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

def run_lookdev_publish():
    """ذخیره و پابلیش کتابخانه متریال از نود /mat با ساختار تسک"""
    db = DatabaseManager()
    task_id = os.environ.get("CORTEX_TASK_ID")
    task_name = os.environ.get("CORTEX_TASK_NAME", "out").replace(" ", "_")
    
    if not task_id:
        hou.ui.displayMessage("Error: Please launch Houdini via Cortex HUB!")
        return

    # ۱. گرفتن مسیر پایه متریال از دیتابیس (publish/3d/lookdev)
    mat_pub_dir = db.get_publish_path(task_id, software="lookdev", category="3d")
    if not mat_pub_dir:
        hou.ui.displayMessage("Error: Could not resolve lookdev path from DB.")
        return

    # ۲. اضافه کردن زیرپوشه تسک (مثلاً BODY یا HEAD)
    mat_pub_dir = os.path.join(mat_pub_dir, task_name).replace("\\", "/")
    
    if not os.path.exists(mat_pub_dir):
        os.makedirs(mat_pub_dir)

    mat_file = os.path.join(mat_pub_dir, "material_library.hip").replace("\\", "/")
    
    mat_context = hou.node("/mat")
    children = mat_context.children()

    if not children:
        hou.ui.displayMessage("No materials found in /mat context!")
        return

    try:
        mat_context.saveChildrenToFile(children, "*", mat_file)
        hou.ui.displayMessage(f"💎 Lookdev Library Published!\nLocation: {mat_file}")
        print(f">> [Cortex] Materials exported: {mat_file}")
    except Exception as e:
        hou.ui.displayMessage(f"!! Material Publish Failed: {e}")