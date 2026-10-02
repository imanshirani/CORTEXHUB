# Location: plugins/houdini/scripts/hda_creator.py
import hou

def create_cortex_node():
    """ساخت خودکار نود اختصاصی کورتکس با پارامترهای حرفه‌ای"""
    
    # ۱. ایجاد نود پایه در محیط OBJ
    obj = hou.node("/obj")
    node = obj.createNode("geo", "CORTEX_PUBLISHER")
    
    # ۲. ظاهر نود (رنگ آبی کورتکس)
    node.setColor(hou.Color((0, 0.47, 0.8)))

    # ۳. دریافت گروه پارامترهای پیش‌فرض و مخفی کردن تک‌تک آن‌ها
    group = node.parmTemplateGroup()
    for pt in group.parmTemplates():
        pt.hide(True)
        group.replace(pt.name(), pt)

    # ۴. ساخت یک تب (فولدر) اختصاصی و شیک برای کورتکس
    cortex_folder = hou.FolderParmTemplate("cortex_folder", "Cortex Pipeline")

    # فیلد انتخاب نود هدف (Target Node)
    target_path = hou.StringParmTemplate("target_node", "Target Object", 1, string_type=hou.stringParmType.NodeReference)
    cortex_folder.addParmTemplate(target_path)

    # منوی انتخاب نوع خروجی
    out_type = hou.MenuParmTemplate("out_type", "Output Type", 
                                    menu_items=["vdb", "abc", "usd"],
                                    menu_labels=["VDB Cache (.vdb)", "Alembic (.abc)", "USD (.usd)"])
    cortex_folder.addParmTemplate(out_type)

    # فیلد کامنت
    comment = hou.StringParmTemplate("comment", "Comment", 1)
    cortex_folder.addParmTemplate(comment)

    # --- ساخت دکمه PUBLISH و تزریق Callback Script ---
    callback_code = """
import publisher_houdini
import importlib
importlib.reload(publisher_houdini)
node = kwargs['node']
publisher_houdini.run_publish_logic(node)
"""
    publish_btn = hou.ButtonParmTemplate("do_publish", "🚀 PUBLISH TO CORTEX")
    publish_btn.setScriptCallback(callback_code)
    publish_btn.setScriptCallbackLanguage(hou.scriptLanguage.Python)
    cortex_folder.addParmTemplate(publish_btn)

    # ۵. اضافه کردن تب کورتکس به نود
    group.append(cortex_folder)

    # ۶. اعمال نهایی روی نود
    node.setParmTemplateGroup(group)

    print(f">> [Cortex] Specialized Node Created: {node.path()}")
    return node


def create_cortex_loader_node():
    """ساخت خودکار نود اختصاصی کورتکس برای لود کردن اَسِت‌ها"""
    
    obj = hou.node("/obj")
    node = obj.createNode("geo", "CORTEX_LOADER")
    
    # ظاهر نود لودر (رنگ نارنجی کورتکس)
    node.setColor(hou.Color((0.9, 0.4, 0.1)))

    # مخفی کردن پارامترهای پیش‌فرض geo
    group = node.parmTemplateGroup()
    for pt in group.parmTemplates():
        pt.hide(True)
        group.replace(pt.name(), pt)

    # ساخت تب اختصاصی لودر
    cortex_folder = hou.FolderParmTemplate("cortex_loader_folder", "Cortex Pipeline (LOADER)")

    # فیلد انتخاب فایل از هارد (File Browser)
    file_path = hou.StringParmTemplate("file_path", "Select File (.abc, .vdb)", 1, string_type=hou.stringParmType.FileReference)
    cortex_folder.addParmTemplate(file_path)

    # --- ساخت دکمه LOAD ---
    callback_code = """
import loader_houdini
import importlib
importlib.reload(loader_houdini)
node = kwargs['node']
loader_houdini.run_load_logic(node)
"""
    load_btn = hou.ButtonParmTemplate("do_load", "📥 LOAD INTO SCENE")
    load_btn.setScriptCallback(callback_code)
    load_btn.setScriptCallbackLanguage(hou.scriptLanguage.Python)
    cortex_folder.addParmTemplate(load_btn)

    # اعمال روی نود
    group.append(cortex_folder)
    node.setParmTemplateGroup(group)

    print(f">> [Cortex] Loader Node Created: {node.path()}")
    return node