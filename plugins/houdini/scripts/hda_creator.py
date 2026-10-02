# Location: plugins/houdini/scripts/hda_creator.py
import hou

def create_cortex_node():
    """Create a Cortex node with pipeline parameters"""
    
    # 1. Base node in OBJ
    obj = hou.node("/obj")
    node = obj.createNode("geo", "CORTEX_PUBLISHER")
    
    # 2. Node look (Cortex blue)
    node.setColor(hou.Color((0, 0.47, 0.8)))

    # 3. Hide default parameter groups one by one
    group = node.parmTemplateGroup()
    for pt in group.parmTemplates():
        pt.hide(True)
        group.replace(pt.name(), pt)

    # 4. Dedicated Cortex folder/tab
    cortex_folder = hou.FolderParmTemplate("cortex_folder", "Cortex Pipeline")

    # Target node field
    target_path = hou.StringParmTemplate("target_node", "Target Object", 1, string_type=hou.stringParmType.NodeReference)
    cortex_folder.addParmTemplate(target_path)

    # Output-type menu
    out_type = hou.MenuParmTemplate("out_type", "Output Type", 
                                    menu_items=["vdb", "abc", "usd"],
                                    menu_labels=["VDB Cache (.vdb)", "Alembic (.abc)", "USD (.usd)"])
    cortex_folder.addParmTemplate(out_type)

    # Comment field
    comment = hou.StringParmTemplate("comment", "Comment", 1)
    cortex_folder.addParmTemplate(comment)

    # --- PUBLISH button and callback script ---
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

    # 5. Add the Cortex tab to the node
    group.append(cortex_folder)

    # 6. Apply on the node
    node.setParmTemplateGroup(group)

    print(f">> [Cortex] Specialized Node Created: {node.path()}")
    return node


def create_cortex_loader_node():
    """Create a Cortex loader node for assets"""
    
    obj = hou.node("/obj")
    node = obj.createNode("geo", "CORTEX_LOADER")
    
    # Loader look (Cortex orange)
    node.setColor(hou.Color((0.9, 0.4, 0.1)))

    # Hide default geo parameters
    group = node.parmTemplateGroup()
    for pt in group.parmTemplates():
        pt.hide(True)
        group.replace(pt.name(), pt)

    # Loader tab
    cortex_folder = hou.FolderParmTemplate("cortex_loader_folder", "Cortex Pipeline (LOADER)")

    # File browser on disk
    file_path = hou.StringParmTemplate("file_path", "Select File (.abc, .vdb)", 1, string_type=hou.stringParmType.FileReference)
    cortex_folder.addParmTemplate(file_path)

    # --- LOAD button ---
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

    # Apply on the node
    group.append(cortex_folder)
    node.setParmTemplateGroup(group)

    print(f">> [Cortex] Loader Node Created: {node.path()}")
    return node