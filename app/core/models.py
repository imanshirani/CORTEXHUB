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
    
    # We'll keep these here for now, even if they're not in the database
    # In the future, we can add these to the projects table
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
    This class is the most important part.
    It shows exactly where the user is in the pipeline.
    """
    user: Optional[User] = None
    project: Optional[Project] = None
    sequence: Optional[str] = None
    shot: Optional[str] = None
    task: Optional[Task] = None