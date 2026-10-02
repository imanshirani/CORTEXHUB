# Location: plugins/houdini/scripts/456.py
import hou
import os
import hdefereval

def setup_cortex_interface():
    """نمایش وضعیت تسک و ورژن‌ها در کنسول یا نوار وضعیت هودینی"""
    task_name = os.environ.get("CORTEX_TASK_NAME", "Unknown")
    work_path = os.environ.get("CORTEX_WORK_PATH", "")
    
    # چاپ وضعیت در نوار پایین هودینی (Status Bar)
    hou.ui.setStatusMessage(f"Cortex Pipeline | Task: {task_name} | Path: {work_path}")
    print(f">> [Cortex] Ready for Task: {task_name}")

setup_cortex_interface()

def setup_houdini_scene():
    """تنظیمات اولیه صحنه مطابق با استانداردهای پروژه"""
    print(">> [Cortex] Initializing Houdini Scene...")
    
    try:
        fps = float(os.environ.get("CORTEX_FPS", 24))
        res_w = int(os.environ.get("CORTEX_RES_W", 1920))
        res_h = int(os.environ.get("CORTEX_RES_H", 1080))

        hou.setFps(fps)
        
        # تنظیم رزولوشن (برای زمانی که نود Mantra یا Karma ساخته میشه)
        for node in hou.nodeType(hou.ropNodeTypeCategory(), "ifd").instances():
            node.parm("res_override").set(1)
            node.parm("res_fraction").set("specific")
            node.parm("res_sizex").set(res_w)
            node.parm("res_sizey").set(res_h)

        print(f">> [Cortex] Scene Configured: {fps}FPS | {res_w}x{res_h}")
    except Exception as e:
        print(f"!! [Cortex] Setup Error: {e}")

def force_show_cortex_shelf():
    """نمایش خودکار تب کورتکس در نوار ابزار هودینی"""
    try:
        desktop = hou.ui.curDesktop()
        if not desktop: return

        shelf_dock = desktop.shelfDock()
        current_sets = shelf_dock.shelfSets()
        if not current_sets: return
        
        # انتخاب دسته فعلی (معمولا همون اولی)
        active_set = current_sets[0] 
        current_shelves = list(active_set.shelves())
        
        # پیدا کردن تب کورتکس
        cortex_shelf = hou.shelves.shelves().get("cortex_shelf_tab")
        
        if cortex_shelf:
            if cortex_shelf not in current_shelves:
                current_shelves.append(cortex_shelf)
                # تب را به دسته (Set) اضافه می‌کنیم، نه به داک
                active_set.setShelves(current_shelves) 
                print(">> [Cortex] Toolbar tab loaded into UI.")
        else:
            print("!! [Cortex] Cannot find 'cortex_shelf_tab' in memory!")
            
    except Exception as e:
        print(f"!! [Cortex] Shelf Error: {e}")

# اجرای دستورات
setup_houdini_scene()


def show_cortex_banner():
    """نمایش اطلاعات تسک در لحظه ورود"""
    task = os.environ.get("CORTEX_TASK_NAME", "Unknown Task")
    user = os.environ.get("CORTEX_USER", "Artist")
    
    message = f"--- CORTEX PIPELINE --- | USER: {user} | TASK: {task}"
    
    # نمایش در Status Bar پایین هودینی
    hou.ui.setStatusMessage(message)
    
    # ساخت یک نود یادداشت (Sticky Note) در محیط OBJ برای راهنمایی آرتیست (اختیاری)
    obj = hou.node("/obj")
    note_name = "CORTEX_INFO"
    existing = obj.node(note_name)
    if not existing:
        note = obj.createStickyNote(note_name)
        note.setText(f"CORTEX PROJECT INFO\n\nTask: {task}\nUser: {user}\nStatus: Active")
        note.setColor(hou.Color((0, 0.5, 1)))

show_cortex_banner()

def update_houdini_title():
    task = os.environ.get("CORTEX_TASK_NAME", "No Task")
    ver = "v000" # این را می‌توانیم داینامیک کنیم
    # تغییر عنوان پنجره هودینی
    hou.ui.setStatusMessage(f"Cortex Pipeline | Task: {task} | {ver}")

update_houdini_title()

# هودینی باید اول UI رو لود کنه بعد شلف رو اضافه کنیم، پس از hdefereval استفاده می‌کنیم
hdefereval.executeDeferred(force_show_cortex_shelf)