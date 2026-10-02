# Location: plugins/3dsmax/style.py

# --- استایل داک اصلی (Cortex Dock) ---
MAINWIDGET = """
    QFrame#MainFrame {
        background-color: #2d2d2d;
        border-bottom: 2px solid #007acc;
    }
    QLabel {
        color: #ddd;
        font-family: 'Segoe UI';
    }
    QLabel#TaskLabel {
        color: #007acc;
        font-weight: bold;
    }
    QComboBox {
        background-color: #444;
        color: white;
        border: 1px solid #555;
        border-radius: 3px;
        padding: 2px 10px;
        min-width: 80px;
    }
    QComboBox:hover {
        border: 1px solid #007acc;
    }
    QToolButton {
        background-color: transparent;
        color: #e0e0e0;
        border-radius: 3px;
        padding: 4px;
    }
    QToolButton:hover {
        background-color: #444;
    }
    QFrame[class="Separator"] {
        background-color: #444;
        width: 1px;
    }
"""

# --- استایل پنجره سیو (Save Window) ---
SAVEWINDOW = """
    QWidget { background-color: #2d2d2d; color: #eee; font-family: 'Segoe UI'; }
    QLineEdit, QTextEdit { 
        background-color: #383838; border: 1px solid #555; 
        border-radius: 3px; color: white; padding: 5px;
    }
    QPushButton { 
        background-color: #007acc; color: white; border: none; 
        padding: 8px; border-radius: 4px; font-weight: bold; font-size: 12px;
    }
    QPushButton:hover { background-color: #0098ff; }
    QLabel#VersionLabel { font-size: 18px; color: #4CAF50; font-weight: bold; }
"""

# --- استایل پنجره پابلیش و لودر (Publish & Loader) ---
PUBLISH_DIALOG = """
    QDialog { background-color: #2d2d2d; color: #eee; font-family: 'Segoe UI'; }
    QLabel { color: #ddd; }
    
    QTextEdit, QLineEdit { 
        background-color: #383838; border: 1px solid #555; 
        border-radius: 3px; color: white; padding: 5px;
    }
    
    QGroupBox { 
        border: 1px solid #555; 
        margin-top: 10px; 
        padding-top: 15px; 
        font-weight: bold; 
    }
    QGroupBox::title { 
        subcontrol-origin: margin; 
        left: 10px; 
        padding: 0 5px; 
        color: #ccc;
    }
    
    QCheckBox { color: #ddd; spacing: 8px; }
    QCheckBox::indicator { width: 18px; height: 18px; }

    /* لیست‌ها در لودر */
    QListWidget {
        background-color: #222;
        border: 1px solid #444;
        color: #eee;
        outline: none;
    }
    QListWidget::item {
        padding: 5px;
    }
    QListWidget::item:selected {
        background-color: #007acc;
        color: white;
    }
    
    /* تب‌ها در لودر */
    QTabWidget::pane { border: 1px solid #444; }
    QTabBar::tab { background: #333; color: #aaa; padding: 8px 20px; }
    QTabBar::tab:selected { background: #555; color: white; border-bottom: 2px solid #007acc; }
"""

# --- دکمه‌های استاندارد (مورد نیاز Loader و Publisher) ---
BTN_SUCCESS = """
    QPushButton { 
        background-color: #28a745; color: white; border: none; 
        padding: 8px; border-radius: 4px; font-weight: bold; font-size: 13px;
    }
    QPushButton:hover { background-color: #34ce57; }
"""

BTN_SECONDARY = """
    QPushButton { 
        background-color: #555; color: white; border: none; 
        padding: 8px; border-radius: 4px; font-size: 13px;
    }
    QPushButton:hover { background-color: #666; }
"""

LBL_THUMBNAIL = """
    border: 2px dashed #444; background-color: #222;
"""

# --- Toolbar Buttons (دکمه‌های کوچک مثل Load, Refresh) ---
BTN_TOOLBAR = """
    QToolButton { 
        background-color: #333; 
        border: 1px solid #444; 
        border-radius: 3px; 
        color: #eee; 
        padding: 2px 8px;
    }
    QToolButton:hover { 
        background-color: #444; 
        border: 1px solid #007acc; 
    }
    QToolButton:pressed { 
        background-color: #222; 
    }
"""

# --- Context Buttons (دکمه‌های رنگی اصلی) ---
BTN_CTX_LOADER = """
    QPushButton { 
        background-color: #d35400; 
        color: white; 
        border: none; 
        border-radius: 3px; 
        padding: 4px 12px; 
        font-weight: bold; 
    }
    QPushButton:hover { background-color: #e67e22; }
"""

BTN_CTX_SAVE = """
    QPushButton { 
        background-color: #444; 
        color: white; 
        border: 1px solid #555; 
        border-radius: 3px; 
        padding: 4px 12px; 
    }
    QPushButton:hover { background-color: #555; border-color: #888; }
"""

BTN_CTX_PUBLISH = """
    QPushButton { 
        background-color: #2e7d32; 
        color: white; 
        border: none; 
        border-radius: 3px; 
        padding: 4px 12px; 
        font-weight: bold; 
    }
    QPushButton:hover { background-color: #388e3c; }
"""

BTN_CTX_XREF = """
    QPushButton { 
        background-color: #2980b9; 
        color: white; 
        border: none; 
        border-radius: 3px; 
        padding: 4px 12px; 
        font-weight: bold; 
    }
    QPushButton:hover { background-color: #3498db; }
"""

TABLE_MANAGER = """
    QTableWidget {
        background-color: #222;
        gridline-color: #444;
        border: 1px solid #444;
        color: #eee;
        selection-background-color: #444;
    }
    QHeaderView::section {
        background-color: #333;
        color: #bbb;
        padding: 4px;
        border: 1px solid #444;
        font-weight: bold;
    }
    QTableWidget::item {
        padding: 5px;
    }
    QTableWidget::item:selected {
        background-color: #007acc;
        color: white;
    }
"""

# --- دکمه آپدیت (Update Button) ---
BTN_UPDATE = """
    QPushButton {
        background-color: #d35400;
        font-weight: bold;
        color: white;
        border-radius: 3px;
        padding: 4px 8px;
    }
    QPushButton:hover {
        background-color: #e67e22;
    }
"""

# --- لیبل پیام‌های خالی (Placeholder Message) ---
LBL_PLACEHOLDER = """
    QLabel {
        color: #666;
        font-size: 16px;
        font-weight: bold;
    }
"""

BTN_CTX_LOOKDEV = """
    QPushButton { 
        background-color: #00bcd4; 
        color: #111; 
        border: none; 
        border-radius: 3px; 
        padding: 4px 12px; 
        font-weight: bold; 
    }
    QPushButton:hover { background-color: #00acc1; color: white; }
"""

BTN_CTX_OPENPBR = """
    QPushButton { 
        background-color: #00d2ff; 
        color: #111; 
        border: 2px solid #fff; 
        border-radius: 5px; 
        padding: 6px; 
        font-weight: bold; 
    }
    QPushButton:hover { background-color: #3a7bd5; color: white; }
"""

PHOTOSHOP_FRAME = """
    QFrame#MainFrame { 
        background-color: #2d2d2d; 
        border-radius: 12px; 
        border: 2px solid #00a8ff; 
    }
"""

# این متغیرها حتماً باید به صورت رشته (String) باشند
BTN_TOOLBAR = "background-color: transparent; color: #eee; font-size: 16px;"

BTN_CTX_SAVE = """
    background-color: #3d3d3d; 
    color: #eee; 
    border-radius: 4px; 
    padding: 5px;
"""

BTN_CTX_PUBLISH = """
    background-color: #09720b; 
    color: white; 
    border-radius: 4px; 
    font-weight: bold;
"""

BTN_LOAD = """
    QPushButton {
        background-color: #3d3d3d;
        color: #00a8ff;
        border: 1px solid #00a8ff;
        border-radius: 4px;
        font-weight: bold;
    }
    QPushButton:hover { background-color: #00a8ff; color: white; }
"""

BTN_CLOSE = "background-color: #c0392b; color: white; border-radius: 4px;"

SEPARATOR = "background-color: #444; width: 1px;"

LBL_LOGO = "color: #aaa; font-weight: bold; margin-right: 8px; font-family: 'Segoe UI';"

LBL_TASK = "color: #00a8ff; font-weight: bold; font-size: 14px; font-family: 'Segoe UI';"