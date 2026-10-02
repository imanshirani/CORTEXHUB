from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class User:
    id: str
    username: str
    full_name: str
    role: str  # 'admin', 'supervisor', 'artist'
    avatar_url: Optional[str] = None

@dataclass
class Project:
    id: str
    name: str
    code: str
    root_path: str
    status: str = "Active"
    render_engine: str = "--------"
    software: str = "--------"
    
    # فعلاً این‌ها را اینجا نگه می‌داریم، حتی اگر در دیتابیس نباشند
    # در آینده می‌توانیم این‌ها را هم به جدول projects اضافه کنیم
    framerate: int = 24 
    resolution: tuple = (1920, 1080)

@dataclass
class Task:
    id: str
    name: str       # 'modeling', 'lighting'
    status: str     # 'todo', 'wip', 'done'
    assignee_id: str

@dataclass
class Context:
    """
    این کلاس مهم‌ترین بخش است.
    نشان می‌دهد الان کاربر دقیقاً کجای پایپ‌لاین ایستاده.
    """
    user: Optional[User] = None
    project: Optional[Project] = None
    sequence: Optional[str] = None
    shot: Optional[str] = None
    task: Optional[Task] = None