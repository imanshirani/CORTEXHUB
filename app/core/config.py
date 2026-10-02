import os

APP_NAME = "Cortex HUB"
SUBTITLE = "Pipeline Management"
VERSION = "V 0.0.1"
DEVELOPER = "Iman Shirani"
WEBSITE = "CORTEX"
GITHUB = "https://github.com/ImanShirani/Cortex-HUB"
PAYPAL = "https://paypal.me/ImanShirani"

# Fixed colors (that don't change)
COLOR_PRIMARY = "#007acc"
COLOR_ERROR = "#ff5555"

DEFAULT_FPS = 24
DEFAULT_FRAME_WIDTH = 1920
DEFAULT_FRAME_HEIGHT = 1080

ALLOWED_SOFTWARES = ["all", "3ds Max", "Blender", "Maya", "Unreal", "Houdini"]
RENDER_ENGINES = ["--------", "V-Ray", "Octane", "Cycles", "Arnold", "Redshift"]



# 'sqlite' or 'postgres'
DB_TYPE = "sqlite" 

# If DB_TYPE is 'postgres', this is the configuration for PostgreSQL (if the admin wants to use the server)
DB_CONFIG = {
    "host": "localhost",
    "database": "cortex_db",
    "user": "admin",
    "password": "your_password",
    "port": "5432"
}