# Location: plugins/3dsmax/publisher_mat_max.py
import os
import pymxs
rt = pymxs.runtime

class MaterialPublisher:
    def __init__(self, publish_path):
        """
        Handle   Init   operation.
        """
        # دریافت مستقیم مسیری که از پابلیشر اصلی فرستاده شده (بدون اضافه کردن پوشه اضافی)
        self.lookdev_dir = publish_path 
        
        if not os.path.exists(self.lookdev_dir):
            os.makedirs(self.lookdev_dir)

    def publish(self, engine_name=None):
        """ذخیره مستقیم متریال‌های انجین فعال صحنه"""
        
        active_engine = engine_name if engine_name else "Unknown"
        print(f"\n>> [Cortex Lookdev] Publishing Native Materials for: {active_engine}")

        # نام فایل بر اساس انجین (مثلا mat_lib_octane.mat)
        filename = f"mat_lib_{active_engine.lower().replace(' ', '_')}.mat"
        full_path = os.path.join(self.lookdev_dir, filename).replace("\\", "/")
        
        # ذخیره کل Scene Materials به صورت یک کتابخانه واحد
        rt.saveMaterialLibrary(full_path)
        
        print(f">> [Cortex] Material Library Published: {full_path}")
        return full_path