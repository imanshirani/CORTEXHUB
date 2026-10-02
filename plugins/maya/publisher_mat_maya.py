# Location: plugins/maya/publisher_mat_maya.py
import os
import maya.cmds as cmds

class MaterialPublisher:
    def __init__(self, publish_path):
        """
        Initializes the Material Publisher for Maya.
        """
        # دریافت مستقیم مسیری که از پابلیشر اصلی فرستاده شده (بدون فولدر اضافی)
        self.lookdev_dir = publish_path 
        
        if not os.path.exists(self.lookdev_dir):
            os.makedirs(self.lookdev_dir)

    def publish(self, engine_name=None):
        """
        Exports the shading networks based on the active render engine.
        """
        active_engine = engine_name if engine_name else "Arnold"
        print(f"\n>> [Cortex Maya Lookdev] Publishing Native Materials for: {active_engine}")

        # نام فایل بر اساس انجین (مثلاً mat_lib_arnold.ma)
        filename = f"mat_lib_{active_engine.lower().replace(' ', '_')}.ma"
        full_path = os.path.join(self.lookdev_dir, filename)

        # در مایا ما متریال‌ها را بر اساس Shading Engineها پیدا می‌کنیم
        all_shading_groups = cmds.ls(type='shadingEngine')
        
        # حذف گروه‌های پیش‌فرض مایا برای خروجی تمیزتر
        exclude = ['initialShadingGroup', 'initialParticleSE']
        targets = [sg for sg in all_shading_groups if sg not in exclude]

        if not targets:
            print("!! [Cortex] No materials found to export.")
            return None

        try:
            # انتخاب تمام متریال‌ها و متعلقاتشان (Textures, Utilities, etc.)
            cmds.select(targets, noExpand=True)
            
            # اکسپورت کردن بخش‌های انتخاب شده به صورت یک فایل مجزا
            # استفاده از Maya ASCII (.ma) چون قابل ویرایش با نوت‌پد هم هست و خطایابی‌اش راحت‌تر است
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