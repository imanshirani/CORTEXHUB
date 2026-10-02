import bpy
import os

class BlenderMaterialPublisher:
    def __init__(self, publish_path):
        """
        Handle   Init   operation.
        """
        # Final path: Assets/Hero/publish/lookdev/materials
        self.lookdev_dir = os.path.join(publish_path, "materials")
        if not os.path.exists(self.lookdev_dir):
            os.makedirs(self.lookdev_dir)

    def publish(self):
        """Save Blender scene materials into a library file"""
        print("\n>> [Cortex Lookdev] Publishing Blender Materials...")

        filename = "blender_native_materials.blend"
        full_path = os.path.join(self.lookdev_dir, filename)
        
        # 1. Select scene materials
        # 2. save_as_mainfile with a data filter
        try:
            # Save as a library for Link/Append
            bpy.ops.wm.save_as_mainfile(filepath=full_path, copy=True, relative_remap=True)
            print(f">> [Cortex] Blender Material Library Published: {full_path}")
            return full_path
        except Exception as e:
            print(f"!! [Cortex] Material Publish Failed: {e}")
            return None