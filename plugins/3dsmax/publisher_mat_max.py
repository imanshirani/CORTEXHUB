# Location: plugins/3dsmax/publisher_mat_max.py
import os
import pymxs
rt = pymxs.runtime

class MaterialPublisher:
    def __init__(self, publish_path):
        """
        Handle   Init   operation.
        """
        # Use the path from the main publisher (no extra folder)
        self.lookdev_dir = publish_path 
        
        if not os.path.exists(self.lookdev_dir):
            os.makedirs(self.lookdev_dir)

    def publish(self, engine_name=None):
        """Save the active render-engine materials directly"""
        
        active_engine = engine_name if engine_name else "Unknown"
        print(f"\n>> [Cortex Lookdev] Publishing Native Materials for: {active_engine}")

        # Filename from the engine (e.g. mat_lib_octane.mat)
        filename = f"mat_lib_{active_engine.lower().replace(' ', '_')}.mat"
        full_path = os.path.join(self.lookdev_dir, filename).replace("\\", "/")
        
        # Save all Scene Materials as one library
        rt.saveMaterialLibrary(full_path)
        
        print(f">> [Cortex] Material Library Published: {full_path}")
        return full_path