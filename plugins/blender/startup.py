import bpy
import os
import sys
import subprocess
import importlib

class CortexState:
    project_root = os.environ.get("CORTEX_PROJECT_ROOT", "")
    work_path = os.environ.get("CORTEX_WORK_PATH", "")
    task_name = os.environ.get("CORTEX_TASK_NAME", "Unknown")
    fps = os.environ.get("CORTEX_FPS", "24")
    res_w = os.environ.get("CORTEX_RES_W", "1920")
    res_h = os.environ.get("CORTEX_RES_H", "1080")

def install_and_launch():
    """
    Handle Install And Launch operation.
    """
    # 1. Scene settings
    try: bpy.context.scene.render.fps = int(CortexState.fps)
    except: pass
    try:
        bpy.context.scene.render.resolution_x = int(CortexState.res_w)
        bpy.context.scene.render.resolution_y = int(CortexState.res_h)
    except: pass

    # 2. Check PySide6
    try:
        import PySide6
    except ImportError:
        print(">> Installing PySide6...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyside6"])

    # 3. Floating UI
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path: sys.path.append(current_dir)
        
        import cortex_ui
        importlib.reload(cortex_ui)
        cortex_ui.show_ui()
        print(">> Cortex UI Launched.")
    except Exception as e:
        print(f"!! UI Error: {e}")

# Auto-run after a short delay so Blender is fully up
if __name__ == "__main__":
    bpy.app.timers.register(install_and_launch, first_interval=1.0)