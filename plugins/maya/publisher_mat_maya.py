# Location: plugins/maya/publisher_mat_maya.py
import os
import maya.cmds as cmds

class MaterialPublisher:
    def __init__(self, publish_path):
        """
        Initializes the Material Publisher for Maya.
        """
        # Path sent from the main publisher (no extra folder)
        self.lookdev_dir = publish_path 
        
        if not os.path.exists(self.lookdev_dir):
            os.makedirs(self.lookdev_dir)

    def publish(self, engine_name=None):
        """
        Exports the shading networks based on the active render engine.
        """
        active_engine = engine_name if engine_name else "Arnold"
        print(f"\n>> [Cortex Maya Lookdev] Publishing Native Materials for: {active_engine}")

        # Filename from the engine (e.g. mat_lib_arnold.ma)
        filename = f"mat_lib_{active_engine.lower().replace(' ', '_')}.ma"
        full_path = os.path.join(self.lookdev_dir, filename)

        # In Maya, materials are found via shading engines
        all_shading_groups = cmds.ls(type='shadingEngine')
        
        # Drop Maya default groups for a cleaner export
        exclude = ['initialShadingGroup', 'initialParticleSE']
        targets = [sg for sg in all_shading_groups if sg not in exclude]

        if not targets:
            print("!! [Cortex] No materials found to export.")
            return None

        try:
            # Select all materials and their dependents (textures, utilities, etc.)
            cmds.select(targets, noExpand=True)
            
            # Export the selection as a separate file
            # Maya ASCII (.ma) is editable in a text editor and easier to debug
            cmds.file(full_path, 
                      exportSelected=True, 
                      type='mayaAscii', 
                      force=True, 
                      preserveReferences=False)
            
            print(f">> [Cortex] Maya Material Library Published: {full_path}")
            return full_path
        except Exception as e:
            print(f"!! [Cortex] Material Export Failed: {e}")
            return None