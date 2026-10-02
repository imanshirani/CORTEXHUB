import os
import json

class FileSystemManager:
    # ==========================================
    # 1. DEFAULT STRUCTURES
    # ==========================================
    DEFAULT_PROJECT_STRUCTURE = [
        "Assets/Characters",
        "Assets/Props",
        "Assets/Environments",
        "Sequences",
        "Editorial",
        "Production/Scripts",
        "Production/Docs"
    ]

    DEFAULT_ASSET_STRUCTURE = {
        "work": {
            "3D": [], #<--- At this time it's empty because make it from Departmants Database
            "2D": ["concept", "texture", "matte_painting", "storyboard"]
        },
        "publish": {
            "3D": {"max": [], "maya": [], "abc": [], "obj": [], "fbx": [], "cache": []},
            "2D": {"photoshop": [], "substance": []}
        },
        "review": ["playblasts", "renders"] 
    }  

    DEFAULT_SHOT_STRUCTURE = {
        "work": {
            "3D": ["layout", "animation", "lighting", "fx"],
            "2D": ["comp", "roto", "prep"]
        },
        "publish": {
            "3D": {"max": [], "maya": [], "cache": [], "abc": []}, 
            "2D": {"nuke": [], "ae": [], "renders": []}
        },
        "review": ["dailies"]
    }  

    # ==========================================
    # 2. CORE RECURSIVE BUILDER (smart construction engine)
    # ==========================================
    @staticmethod
    def _create_folders_recursively(base_path, structure):
        """Build nested folders to infinite levels"""
        if isinstance(structure, dict):
            for folder_name, sub_structure in structure.items():
                new_path = os.path.join(base_path, folder_name)
                os.makedirs(new_path, exist_ok=True)
                FileSystemManager._create_folders_recursively(new_path, sub_structure)
        elif isinstance(structure, list):
            for folder_name in structure:
                new_path = os.path.join(base_path, folder_name)
                os.makedirs(new_path, exist_ok=True)

    # ==========================================
    # 3. GETTERS (read functions from the database that were deleted)
    # ==========================================
    @staticmethod
    def get_project_structure(db):
        """Reading the project structure from the database or using the default"""
        json_data = db.get_setting("project_structure")
        if json_data:
            try:
                return json.loads(json_data)
            except json.JSONDecodeError:
                pass
        return FileSystemManager.DEFAULT_PROJECT_STRUCTURE

    @staticmethod
    def get_asset_structure(db):
        """Read the structure from the database or use the default"""
        json_data = db.get_setting("asset_structure")
        if json_data:
            try:
                return json.loads(json_data)
            except json.JSONDecodeError:
                pass
        return FileSystemManager.DEFAULT_ASSET_STRUCTURE

    @staticmethod
    def get_shot_structure(db):
        """Reading the shot structure from the database or using the default"""
        json_data = db.get_setting("shot_structure")
        if json_data:
            try:
                return json.loads(json_data)
            except json.JSONDecodeError:
                pass
        return FileSystemManager.DEFAULT_SHOT_STRUCTURE

    # ==========================================
    # 4. BUILDERS (functions for creating folders on the hard drive)
    # ==========================================
    @staticmethod
    def create_project_structure(db, root_path):
        """Creating project folders based on settings"""
        if not os.path.exists(root_path):
            try: os.makedirs(root_path)
            except OSError: return False

        structure = FileSystemManager.get_project_structure(db)
        FileSystemManager._create_folders_recursively(root_path, structure)
        return True

    @staticmethod
    def create_sequence_structure(project_root, seq_name):
        """Create sequence folder"""
        seq_path = os.path.join(project_root, "Sequences", seq_name)
        os.makedirs(seq_path, exist_ok=True)
        return True

    @staticmethod
    def create_asset_structure(db, project_root, category, asset_name):
        """Creating asset folders based on any type of complex structure"""
        asset_root = os.path.join(project_root, "Assets", category, asset_name)
        if os.path.exists(asset_root): return True
            
        try:
            os.makedirs(asset_root)
            structure = FileSystemManager.get_asset_structure(db)
            FileSystemManager._create_folders_recursively(asset_root, structure)
            return True
        except OSError:
            return False

    @staticmethod
    def create_shot_structure(db, project_root, seq_name, shot_name):
        """Creating folder shots based on smart settings"""
        shot_root = os.path.join(project_root, "Sequences", seq_name, shot_name)
        if os.path.exists(shot_root): return True 
            
        try:
            os.makedirs(shot_root)
            structure = FileSystemManager.get_shot_structure(db)
            FileSystemManager._create_folders_recursively(shot_root, structure)
            return True
        except OSError:
            return False
        
    # ==========================================
    # 5. UTILITIES
    # ==========================================
    @staticmethod
    def rename_folder(old_path, new_name):
        """Changing the name of the folder (for use in the admin panel)"""
        if not os.path.exists(old_path):
            return False
        parent_dir = os.path.dirname(old_path)
        new_path = os.path.join(parent_dir, new_name)
        try:
            os.rename(old_path, new_path)
            return True
        except OSError:
            return False