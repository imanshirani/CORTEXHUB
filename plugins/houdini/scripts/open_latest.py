# Location: plugins/houdini/scripts/open_latest.py
import hou
import os
import glob
import re

def run():
    """Find and open the latest version in the work folder"""
    work_path = os.environ.get("CORTEX_WORK_PATH")
    task_name = os.environ.get("CORTEX_TASK_NAME", "Houdini_Task")

    if not work_path or not os.path.exists(work_path):
        hou.ui.displayMessage("Error: Work path not found!")
        return

    # Search every .hip in the work folder
    files = glob.glob(os.path.join(work_path, f"{task_name}_v*.hip*"))
    
    if not files:
        hou.ui.displayMessage("No versions found to load!")
        return

    # Sort by version number
    files.sort(key=lambda x: int(re.findall(r'_v(\d+)', x)[-1]) if re.findall(r'_v(\d+)', x) else 0)
    latest_file = files[-1].replace("\\", "/")

    # Open in Houdini
    if hou.hipFile.hasUnsavedChanges():
        res = hou.ui.displayCustomConfirmation("Save changes to current scene before loading latest?", 
                                               buttons=("Save and Open", "Open without Saving", "Cancel"))
        if res == 0: hou.hipFile.save()
        elif res == 2: return

    hou.hipFile.load(latest_file)
    print(f">> [Cortex] Opened Latest Version: {latest_file}")