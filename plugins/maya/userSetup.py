# Location: plugins/maya/userSetup.py
import os
import sys
import maya.cmds as cmds
import maya.utils as utils
import maya.mel as mel

def setup_maya_scene():
    fps_str = os.environ.get("CORTEX_FPS")
    res_w = os.environ.get("CORTEX_RES_W")
    res_h = os.environ.get("CORTEX_RES_H")
    work_path = os.environ.get("CORTEX_WORK_PATH")

    if fps_str:
        fps_map = {"24": "film", "25": "pal", "30": "ntsc", "60": "ntscf"}
        maya_fps = fps_map.get(fps_str, "film")
        try: cmds.currentUnit(time=maya_fps)
        except: pass

    if res_w and res_h:
        try:
            cmds.setAttr("defaultResolution.width", int(res_w))
            cmds.setAttr("defaultResolution.height", int(res_h))
            cmds.setAttr("defaultResolution.deviceAspectRatio", float(res_w)/float(res_h))
        except: pass

    if work_path and os.path.exists(work_path):
        try:
            project_dir = os.path.dirname(work_path)
            cmds.workspace(project_dir, openWorkspace=True)
        except: pass

    utils.executeDeferred(create_cortex_native_shelf)

def create_cortex_native_shelf():
    """Build a native Maya shelf with pipeline buttons"""
    shelf_name = "Cortex"
    
    if cmds.shelfLayout(shelf_name, exists=True):
        cmds.deleteUI(shelf_name)
        
    try:
        gShelfTopLevel = mel.eval('$tmpVar=$gShelfTopLevel')
        cmds.setParent(gShelfTopLevel)
        cmds.shelfLayout(shelf_name)
        
        # ---------------------------------------------------------
        # Button 1: OPEN LATEST (new)
        # ---------------------------------------------------------
        # Finds and opens the latest file in the task folder
        cmd_latest = """import os
import maya.cmds as cmds
work = os.environ.get('CORTEX_WORK_PATH', '')
if os.path.exists(work):
    files = sorted([f for f in os.listdir(work) if f.endswith(('.ma', '.mb'))])
    if files:
        latest = os.path.join(work, files[-1]).replace('\\\\', '/')
        proceed = True
        if cmds.file(q=True, modified=True):
            res = cmds.confirmDialog(title='Unsaved Changes', message='Save current scene?', button=['Yes','No','Cancel'], defaultButton='Yes', cancelButton='Cancel', dismissString='Cancel')
            if res == 'Yes': cmds.file(save=True, force=True)
            elif res == 'Cancel': proceed = False
        if proceed:
            cmds.file(latest, open=True, force=True)
            print('\\n>> [Cortex] Opened Latest File: ' + latest)
    else: cmds.warning('No files found in task folder!')
else: cmds.warning('Task folder not found! Launch from Hub.')"""
        
        cmds.shelfButton(
            command=cmd_latest,
            annotation="Open Latest Work File for Current Task",
            imageOverlayLabel="LATEST",  
            image="timeplay.png", 
            backgroundColor=(0.5, 0.1, 0.6), # purple
            width=50, height=37
        )

        # ---------------------------------------------------------
        # Button 2: LOADER
        # ---------------------------------------------------------
        cmd_loader = "import loader; import importlib; importlib.reload(loader); loader.run()"
        cmds.shelfButton(
            command=cmd_loader,
            annotation="Open Cortex Loader",
            imageOverlayLabel="LOAD",  
            image="fileOpen.png", 
            backgroundColor=(0.1, 0.5, 0.8), 
            width=50, height=37
        )
        
        # ---------------------------------------------------------
        # Button 3: PUBLISHER
        # ---------------------------------------------------------
        cmd_publish = "import publisher_maya; import importlib; importlib.reload(publisher_maya); pub = publisher_maya.MayaPublisher(); pub.show_dialog()"
        cmds.shelfButton(
            command=cmd_publish,
            annotation="Open Cortex Publisher",
            imageOverlayLabel="PUB",
            image="export.png", 
            backgroundColor=(0.8, 0.3, 0.1), 
            width=50, height=37
        )
        
        # ---------------------------------------------------------
        # Button 4: SAVE
        # ---------------------------------------------------------
        cmd_save = "import save_view; import importlib; importlib.reload(save_view); win = save_view.SaveWindow(); win.show()"
        cmds.shelfButton(
            command=cmd_save,
            annotation="Cortex Incremental Save",
            imageOverlayLabel="SAVE",
            image="save.png", 
            backgroundColor=(0.2, 0.6, 0.2), 
            width=50, height=37
        )

        print(">> [Cortex] Native Shelf created successfully.")
    except Exception as e:
        print(f"!! [Cortex] Failed to create Shelf: {e}")

# Apply settings and build the shelf when Maya starts
setup_maya_scene()