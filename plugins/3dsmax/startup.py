# Cortex Pipeline Startup (Max 2026)
# Location: plugins/3dsmax/startup.py

import os
import sys
import shutil
import inspect
import pymxs
from PySide6.QtCore import QTimer

rt = pymxs.runtime

def create_clean_mxp(project_root, project_name):
    """
    Builds the project config file (.mxp) so every Max path
    is redirected into the _max_system folder.
    """
    full_project_path = os.path.join(project_root, project_name).replace("\\", "/")
    system_dir = "_max_system"
    full_system_path = os.path.join(full_project_path, system_dir).replace("\\", "/")
    
    if not os.path.exists(full_system_path):
        try: os.makedirs(full_system_path)
        except: pass

    mxp_file = os.path.join(full_project_path, f"{project_name}.mxp").replace("\\", "/")

    config_data = {
        "Animations":      f".\\{system_dir}\\sceneassets\\animations",
        "Archives":        f".\\{system_dir}\\archives",
        "AutoBackup":      f".\\{system_dir}\\autoback",
        "BitmapProxies":   f".\\{system_dir}\\proxies",
        "Downloads":       f".\\{system_dir}\\downloads",
        "Export":          f".\\{system_dir}\\export",
        "Expressions":     f".\\{system_dir}\\express",
        "Fluid Simulations": f".\\{system_dir}\\SimCache",
        "Images":          f".\\{system_dir}\\sceneassets\\images",
        "Import":          f".\\{system_dir}\\import",
        "Materials":       f".\\{system_dir}\\materiallibraries",
        "MaxStart":        f".\\{system_dir}\\scenes",
        "Photometric":     f".\\{system_dir}\\sceneassets\\photometric",
        "Previews":        f".\\{system_dir}\\previews",
        "ProjectFolder":   full_project_path.replace("/", "\\"),
        "RenderAssets":    f".\\{system_dir}\\sceneassets\\renderassets",
        "RenderOutput":    f".\\{system_dir}\\renderoutput",
        "RenderPresets":   f".\\{system_dir}\\renderpresets",
        "Scenes":          f".\\{system_dir}\\scenes",
        "Sounds":          f".\\{system_dir}\\sceneassets\\sounds",
        "VideoPost":       f".\\{system_dir}\\vpost",
    }

    content = ["[Directories]"]
    for key, value in config_data.items():
        content.append(f"{key}={value}")

    content.append("\n[XReferenceDirs]")
    content.append(f"Dir1=.\\{system_dir}\\scenes")
    
    try:
        with open(mxp_file, "w") as f:
            f.write("\n".join(content))
        print(f">> [Cortex] Configured Clean MXP: {mxp_file}")
        return mxp_file
    except Exception as e:
        print(f"!! Error writing MXP file: {e}")
        return None

def cleanup_root_clutter(project_root, project_name):
    """Remove empty leftover folders from the root"""
    full_path = os.path.join(project_root, project_name)
    clutter = [
        "archives", "autoback", "downloads", "export", "express", 
        "import", "materiallibraries", "previews", "proxies", 
        "renderoutput", "renderpresets", "sceneassets", "scenes", 
        "SimCache", "vpost"
    ]
    print(">> [Cortex] Cleaning root folder...")
    for folder in clutter:
        p = os.path.join(full_path, folder)
        if os.path.exists(p):
            try:
                if not os.listdir(p):
                    os.rmdir(p)
            except: pass

def launch_cortex_ui():
    """
    Handle Launch Cortex Ui operation.
    """
    try:
        try: script_path = __file__
        except NameError: script_path = inspect.getfile(inspect.currentframe())

        current_dir = os.path.dirname(os.path.abspath(script_path)).replace("\\", "/")
        if current_dir not in sys.path:
            sys.path.append(current_dir)

        import cortex_ui
        import importlib
        importlib.reload(cortex_ui)
        cortex_ui.show_ui()
    except Exception as e:
        print(f"!! Cortex UI Startup Failed: {e}")

def main():
    """
    Handle Main operation.
    """
    print("\n" + "="*50)
    print("   CORTEX PIPELINE STARTUP   ")
    print("="*50)

    QTimer.singleShot(500, launch_cortex_ui)

    # Read environment variables
    project_root = os.environ.get("CORTEX_PROJECT_ROOT")
    project_name = os.environ.get("CORTEX_PROJECT_NAME")
    work_path    = os.environ.get("CORTEX_WORK_PATH")
    fps_str      = os.environ.get("CORTEX_FPS")
    
    # --- Read resolution ---
    res_w = os.environ.get("CORTEX_RES_W")
    res_h = os.environ.get("CORTEX_RES_H")
    # -------------------------------

    # 1. Project and MXP settings
    if project_root and project_name:
        mxp_path = create_clean_mxp(project_root, project_name)
        if mxp_path and os.path.exists(mxp_path):
            try:
                rt.pathConfig.load(mxp_path)
                rt.pathConfig.setCurrentProjectFolder(os.path.dirname(mxp_path))
                print(f">> [Cortex] Project Config Loaded.")
                cleanup_root_clutter(project_root, project_name)
            except Exception as e:
                print(f"!! Error loading project config: {e}")

    # 2. Scene settings (FPS & Resolution)
    if fps_str:
        try: 
            rt.frameRate = int(fps_str)
            print(f">> [Cortex] FPS Set to: {fps_str}")
        except: pass
        
    # --- Apply resolution ---
    if res_w and res_h:
        try:
            rt.renderWidth = int(res_w)
            rt.renderHeight = int(res_h)
            rt.renderPixelAspect = 1.0
            print(f">> [Cortex] Resolution Set to: {res_w}x{res_h}")
        except: pass

    # 3. Work path
    if work_path and os.path.exists(work_path):
        rt.sysInfo.currentDir = work_path

    # 4. Frame range
    start_frame = os.environ.get("CORTEX_FRAME_START")
    end_frame = os.environ.get("CORTEX_FRAME_END")
    if start_frame and end_frame:
        try:
            rt.animationRange = rt.interval(int(start_frame), int(end_frame))
        except: pass

if __name__ == "__main__":
    main()