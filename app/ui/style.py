import os

# Find the root path of the project (Cortex_Pipeline)
# Because this file is located in app/ui, we go back two steps
_current_dir = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(_current_dir))



# ===========================
# 1. CORE THEME & COLORS
# ===========================

DARK_THEME = """
/* General settings */
QWidget {
    background-color: #1e1e1e;
    color: #ffffff;
    font-family: 'Segoe UI', sans-serif;
}
/* Scroll many times */
QScrollBar:vertical {
    border: none;
    background: #2d2d2d;
    width: 10px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #444;
    min-height: 20px;
    border-radius: 5px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    background: none;
}
QPushButton {
    background-color: #444;
    color: white;
    border-radius: 4px;
    padding: 6px 15px;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #555;
}
"""

STATUS_COLORS = {
    "Todo": "#7f8c8d",          # gray
    "In Progress": "#3498db",   # blue
    "Review": "#e67e22",        # orange
    "Done": "#27ae60"           # green
}

# ===========================
# 2. BUTTON GENERATOR
# ===========================
def _get_btn_style(bg_color, hover_color, text_color="white", radius="4px", font_size="13px", padding="8px"):
    """
    This function generates a standard CSS style for buttons.
    """
    return f"""
        QPushButton {{
            background-color: {bg_color};
            color: {text_color};
            border: none;
            border-radius: {radius};
            font-weight: bold;
            font-size: {font_size};
            padding: {padding};
        }}
        QPushButton:hover {{
            background-color: {hover_color};
        }}
        QPushButton:pressed {{
            background-color: {bg_color};
            margin-top: 1px; /* Safe click effect */
        }}
    """

# ===========================
# 3. GLOBAL BUTTON STYLES
# ===========================

# --- Primary colors ---
COLOR_GREEN = "#28a745"
COLOR_GREEN_HOVER = "#218838"

COLOR_BLUE = "#007acc"
COLOR_BLUE_HOVER = "#005f9e"

COLOR_RED = "#d32f2f"
COLOR_RED_HOVER = "#b71c1c"

COLOR_ORANGE = "#e67e22"
COLOR_ORANGE_HOVER = "#d35400"

COLOR_CYAN = "#17a2b8"
COLOR_CYAN_HOVER = "#138496"

COLOR_GRAY = "#555555"
COLOR_GRAY_HOVER = "#666666"

# --- Standard (large) buttons ---
BTN_SUCCESS = _get_btn_style(COLOR_GREEN, COLOR_GREEN_HOVER)   # Save, Add, Create
BTN_PRIMARY = _get_btn_style(COLOR_BLUE, COLOR_BLUE_HOVER)     # Edit Main
BTN_DANGER  = _get_btn_style(COLOR_RED, COLOR_RED_HOVER)       # Delete Main
BTN_WARNING = _get_btn_style(COLOR_ORANGE, COLOR_ORANGE_HOVER) # Admin Warning
BTN_SECONDARY = _get_btn_style(COLOR_GRAY, COLOR_GRAY_HOVER)   # Cancel

# --- Table buttons (small) ---
BTN_SM_EDIT   = _get_btn_style(COLOR_BLUE, COLOR_BLUE_HOVER, font_size="11px", padding="2px 5px")
BTN_SM_DELETE = _get_btn_style(COLOR_RED, COLOR_RED_HOVER, font_size="11px", padding="2px 5px")
BTN_SM_INFO   = _get_btn_style(COLOR_CYAN, COLOR_CYAN_HOVER, font_size="11px", padding="2px 5px")

# ===========================
# 4. LEGACY ALIASES (compatibility with previous codes)
# ===========================

BTN_NEW_PROJECT = BTN_SUCCESS
BTN_SAVE = BTN_SUCCESS
ADMIN_SAVE_BTN = BTN_WARNING
BTN_ACTION_EDIT = BTN_SM_EDIT
BTN_ACTION_DEL = BTN_SM_DELETE
BTN_ACTION_MEMBERS = BTN_SM_INFO

# ===========================
# 5. INPUTS & TABLES STYLES
# ===========================
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

INPUT_STYLE = """
    QLineEdit {
        background-color: #333;
        border: 1px solid #555;
        border-radius: 4px;
        padding: 8px;
        color: white;
        font-size: 13px;
    }
    QLineEdit:focus {
        border: 1px solid #007acc;
        background-color: #2a2a2a;
    }
"""
LIST_WIDGET_STYLE = """
    QListWidget {
        background-color: #252525;
        border: 1px solid #555;
        border-radius: 4px;
        color: #eee;
        outline: none;
        font-size: 13px;
    }

    /* List items */
    QListWidget::item {
        padding: 8px;
        border-bottom: 1px solid #2d2d2d;
    }

    /* Hover */
    QListWidget::item:hover {
        background-color: #333;
    }

    /* Selected item */
    QListWidget::item:selected {
        background-color: #383838; /* Background color in select mode */
        color: white;
        border: 1px solid #007acc;
    }

    /* --- The style of the checkboxes in the list --- */
    QListWidget::indicator {
        width: 18px;
        height: 18px;
        background-color: #333;
        border: 1px solid #555;
        border-radius: 4px;
        margin-right: 10px; /* The distance of the checkbox from the text */
    }

    /* When the mouse hovers over the checkbox */
    QListWidget::indicator:hover {
        border: 1px solid #007acc;
        background-color: #3a3a3a;
    }

    /* When it is ticked */
    QListWidget::indicator:checked {
        background-color: #007acc;
        border: 1px solid #007acc;
        image: url(../resources/icons/check.svg); /* If you don't have an icon, blue is enough */
    }
"""
CHECKBOX_STYLE = """
    QCheckBox {
        color: #eee;
        spacing: 8px; /* Text distance from the square */
        font-size: 13px;
    }

    /* Checkbox square */
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        background-color: #333;
        border: 1px solid #555;
        border-radius: 4px; /* Compatible with LineEdit */
    }

    /* When the mouse hovers over it */
    QCheckBox::indicator:hover {
        border: 1px solid #007acc;
        background-color: #3a3a3a;
    }

    /* Checked state */
    QCheckBox::indicator:checked {
        background-color: #007acc;
        border: 1px solid #007acc;
        /* You can also add a tick icon here,
           But changing color to blue indicates selection */
        image: url(../resources/icons/check.svg); /* If you have an icon */
    }
    
    /* Inactive mode */
    QCheckBox::indicator:disabled {
        background-color: #2a2a2a;
        border: 1px solid #444;
    }
"""

RADIOBUTTON_STYLE = """
    QRadioButton {
        color: #eee;
        spacing: 8px;
        font-size: 13px;
    }

    /* Radio circle */
    QRadioButton::indicator {
        width: 18px;
        height: 18px;
        background-color: #333;
        border: 1px solid #555;
        border-radius: 10px; /* 50% radius for full circle */
    }

    /* Hover */
    QRadioButton::indicator:hover {
        border: 1px solid #007acc;
        background-color: #3a3a3a;
    }

    /* selected mode */
    QRadioButton::indicator:checked {
        background-color: #007acc; 
        border: 4px solid #333; /* The technique of creating a middle point with a border */
    }
"""

LIST_WIDGET_STYLE = """
    QListWidget {
        background-color: #252525; /* Compatible with combobox list background */
        border: 1px solid #555;
        border-radius: 4px;
        color: #eee;
        outline: none; /* Remove the dash around the selected item */
        font-size: 13px;
    }

    /* List items */
    QListWidget::item {
        padding: 8px; /* Adequate breathing space */
        border-bottom: 1px solid #2d2d2d; /* Blurred dividing line */
    }

    /* Hover over item (when not selected) */
    QListWidget::item:hover:!selected {
        background-color: #333;
    }

    /* Selected item */
    QListWidget::item:selected {
        background-color: #007acc;
        color: white;
        border: none;
        border-radius: 3px; /* A little roundness for the selected item */
    }
    
    /* Scroll bar (optional - for more beauty) */
    QListWidget QScrollBar:vertical {
        background: #252525;
        width: 8px;
        margin: 0;
    }
    QListWidget QScrollBar::handle:vertical {
        background: #555;
        min-height: 20px;
        border-radius: 4px;
    }
    QListWidget QScrollBar::handle:vertical:hover {
        background: #007acc;
    }
    QListWidget QScrollBar::add-line:vertical, QListWidget QScrollBar::sub-line:vertical {
        height: 0px;
    }
"""
SPINBOX_STYLE = """
    QSpinBox {
        background-color: #2b2b2b;
        color: white;
        border: 1px solid #555;
        border-radius: 4px;
        padding: 5px;
        padding-right: 20px;
    }
    
    QSpinBox::up-button, QSpinBox::down-button {
        background-color: #444;
        width: 20px;
        border-left: 1px solid #555;
    }

    /* Addressing up and down arrows */
    QSpinBox::up-arrow {
        image: url(resource/icons/arrow-up.svg);
        width: 12px;
        height: 12px;
    }

    QSpinBox::down-arrow {
        image: url(resource/icons/arrow-down.svg);
        width: 12px;
        height: 12px;
    }
"""

COMBOBOX_STYLE = """
    QComboBox {
        background-color: #333;
        border: 1px solid #555;
        border-radius: 4px;
        padding: 6px;
        padding-left: 10px;
        color: white;
    }
    
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 25px;
        border-left: 1px solid #555;
        background-color: #444; 
    }

    /* Addressing directly from the root of the project */
    QComboBox::down-arrow {
        image: url(resource/icons/arrow-down.svg);
        width: 14px;
        height: 14px;
    }
"""

PROJECTS_TABLE = """
    QTableWidget { 
        background-color: #252525; 
        border: 1px solid #333;
        border-radius: 5px;
        gridline-color: #333; 
    }
    QHeaderView::section:horizontal { 
        background-color: #333; 
        padding: 8px; 
        border: none; 
        font-weight: bold; 
        border-right: 1px solid #444;
        height: 35px;
        color: #eee;
    }
    QHeaderView::section:vertical {
        background-color: #252525;
        color: #888;
        padding-left: 5px;
        border: none;
        border-right: 1px solid #333;
        width: 30px;
    }
    QTableWidget::item { 
        padding-left: 10px; 
        border-bottom: 1px solid #2d2d2d;
        background-color: transparent;
        color: #ddd;
    }
    QTableWidget::item:selected {
        background-color: #444;
        color: white;
    }
    QTableCornerButton::section {
        background-color: #333;
        border: none;
    }
"""

LIST_WIDGET_STYLE = """
    QListWidget {
        background-color: #252525;
        border: 1px solid #333;
        border-radius: 5px;
        color: #eee;
    }
    QListWidget::item {
        padding: 10px;
        border-bottom: 1px solid #2d2d2d;
    }
    QListWidget::item:selected {
        background-color: #444;
        color: white;
        border-left: 3px solid #007acc;
    }
"""

# ===========================
# 6. RESTORED STYLES (Login, Sidebar, etc.)
# ===========================

# --- Common ---
SECTION_TITLE = "font-size: 18px; font-weight: bold; color: #ccc;"
PROJECTS_TITLE = SECTION_TITLE

# --- Sidebar ---
SIDEBAR_CONTAINER = "background-color: #252525; border-right: 1px solid #333;"
SIDEBAR_LOGO = "font-size: 20px; font-weight: bold; color: #007acc; padding: 20px 0;"
SIDEBAR_MENU = """
    QListWidget { border: none; background: transparent; outline: none; }
    QListWidget::item { padding: 15px; color: #aaa; border-left: 3px solid transparent; }
    QListWidget::item:selected { background: #333; color: white; border-left: 3px solid #007acc; }
    QListWidget::item:hover { background: #2d2d2d; }
    QListWidget QScrollBar:vertical {width: 0px; }
"""
LOGOUT_BUTTON = """
    QPushButton { 
        background-color: #d32f2f; color: white; border: none; 
        font-weight: bold; text-align: left; padding: 15px; border-radius: 0px; 
    }
    QPushButton:hover { background-color: #b71c1c; }
"""

# --- Login Dialog ---
LOGIN_BG_FRAME = "QFrame { background-color: #1e1e1e; border-radius: 15px; border: 1px solid #333; }"
LOGIN_CLOSE_BTN = "QPushButton { color: #666; background: transparent; border: none; font-size: 16px; } QPushButton:hover { color: #ff5555; }"
LOGIN_TITLE = "font-size: 28px; font-weight: bold; color: #007acc; letter-spacing: 2px;"
LOGIN_SUBTITLE = "font-size: 12px; color: #888; margin-bottom: 20px;"
LOGIN_INPUT = INPUT_STYLE # Use the same standard input style
LOGIN_INPUT_ERROR = """
    QLineEdit {
        background-color: #2b2b2b; border: 1px solid #ff5555; border-radius: 8px;
        color: white; padding-left: 15px; font-size: 14px;
    }
"""
LOGIN_BTN = _get_btn_style(COLOR_BLUE, COLOR_BLUE_HOVER, radius="8px", font_size="14px")
LOGIN_ERROR_LBL = "color: #ff5555; font-size: 12px; font-weight: bold;"
LOGIN_VERSION = "color: #555; font-size: 10px; margin-top: 5px;"

# --- Tabs & Settings ---
TAB_STYLE = """
    QTabWidget::pane { border: 1px solid #444; background: #252525; border-radius: 5px; }
    QTabBar::tab { background: #333; color: #aaa; padding: 10px 20px; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px; }
    QTabBar::tab:selected { background: #252525; color: white; border: 1px solid #444; border-bottom: 1px solid #252525; font-weight: bold; }
    QTabBar::tab:hover { background: #444; }
"""
SETTINGS_TITLE = "font-size: 24px; font-weight: bold; color: #eee; margin-bottom: 10px;"
ADMIN_WARNING_LBL = "color: #e67e22; font-weight: bold; margin-bottom: 10px;"
ADMIN_COMBO = """
    QComboBox { padding: 5px; background: #333; color: white; border: 1px solid #555; border-radius: 4px; }
    QComboBox::drop-down { border: none; }
"""
PROFILE_READONLY_INPUT = "background-color: #333; color: #777; padding: 10px; border: none; border-radius: 5px;"
SEPARATOR_LINE = "color: #444; margin: 10px 0;"

# --- About ---
ABOUT_LOGO = "font-size: 40px; font-weight: bold; color: #007acc;"
ABOUT_VERSION = "color: #666; font-size: 12px; margin-bottom: 20px;"
ABOUT_TEXT = "font-size: 14px; color: #ccc; line-height: 1.5;"

#lunch Btn
LUNCH_BTN = "QPushButton { background-color: #6f42c1; color: white; border-radius: 4px; font-weight: bold; } QPushButton:hover { background-color: #5a32a3; }"


# ===========================
# 7. DIALOG STYLES (New Standard)
# ===========================

DIALOG_THEME = """
    QDialog {
        background-color: #252525;
        color: #eee;
        border: 1px solid #444;
    }
    QLabel {
        font-size: 14px;
        color: #ccc;
        margin-top: 8px;
    }
    /* Using existing input styles */
    QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox {
        background-color: #333;
        border: 1px solid #555;
        border-radius: 4px;
        padding: 6px;
        color: white;
        font-size: 13px;
    }
    QLineEdit:focus, QTextEdit:focus {
        border: 1px solid #007acc;
        background-color: #2a2a2a;
    }
    /* combo box */
    QComboBox {
        background-color: #333;
        color: white;
        border: 1px solid #555;
        border-radius: 4px;
        padding: 6px;
    }
    QComboBox::drop-down {
        border: none;
        background: transparent;
    }
    QComboBox:on {
        border: 1px solid #007acc;
    }
"""
DIALOG_STYLESHEET = """
    /* 1. Main window background */
    QDialog {
        background-color: #252525;
        color: #ffffff;
        font-family: 'Segoe UI', sans-serif;
    }

    /* 2. Texts and labels */
    QLabel {
        font-size: 14px;
        color: #cccccc;
        font-weight: normal;
        margin-bottom: 2px;
    }
    /* We bold the important labels (like headlines). */
    QLabel[class="Header"] {
        font-size: 16px;
        font-weight: bold;
        color: #ffffff;
        margin-bottom: 10px;
    }

    /* 3. All inputs (text, number, drop-down list) */
    QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {
        background-color: #333333;
        border: 1px solid #505050;
        border-radius: 4px;
        padding: 6px; # More interior space for beauty
        color: #ffffff;
        font-size: 13px;
        selection-background-color: #007acc;
    }

    /* Focus mode (when input is clicked) */
    QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {
        border: 1px solid #007acc; /* It will turn blue */
        background-color: #2a2a2a;
    }

    /* Special combo box settings */
    QComboBox::drop-down {
        border: none;
        background: transparent;
        width: 20px;
    }
    QComboBox QAbstractItemView {
        background-color: #333333;
        color: #ffffff;
        border: 1px solid #505050;
        selection-background-color: #007acc;
    }

    /* 4. Lists (such as the list of members) */
    QListWidget {
        background-color: #333333;
        border: 1px solid #505050;
        border-radius: 4px;
        color: #eeeeee;
        padding: 5px;
    }
    QListWidget::item {
        padding: 8px;
        border-bottom: 1px solid #3d3d3d;
    }
    QListWidget::item:selected {
        background-color: #007acc;
        color: white;
        border: none;
        border-radius: 3px;
    }

    /* 5. Browse (...) button */
    QPushButton[class="Browse"] {
        background-color: #444;
        border: 1px solid #555;
        border-radius: 4px;
        color: #ddd;
        font-weight: bold;
    }
    QPushButton[class="Browse"]:hover {
        background-color: #555;
        border-color: #777;
    }
"""
# File browsing button (Browse)
BTN_BROWSE = """
    QPushButton {
        background-color: #444;
        color: #ddd;
        border: 1px solid #555;
        border-radius: 4px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #555;
        border-color: #777;
    }
"""

# --- (+) button ---

BTN_ADD_SMALL = _get_btn_style(COLOR_GREEN, COLOR_GREEN_HOVER, font_size="16px", padding="2px")

# --- OK and Cancel ---

DIALOG_BUTTON_STYLE = f"""
    QPushButton {{ 
        min-width: 80px; 
        padding: 6px 12px; 
        border-radius: 4px; 
        font-weight: bold; 
        background-color: {COLOR_GRAY}; /* Default gray */
        color: white;
    }}
    QPushButton:hover {{
        background-color: {COLOR_GRAY_HOVER};
    }}
    /* Identifying the confirmation buttons (OK/Save/Yes) and turning them green */
    QPushButton[text="OK"], QPushButton[text="&OK"], QPushButton[text="Save"], QPushButton[text="Yes"] {{
        background-color: {COLOR_GREEN};
    }}
    QPushButton[text="OK"]:hover, QPushButton[text="Save"]:hover {{
        background-color: {COLOR_GREEN_HOVER};
    }}
"""
MENU_STYLE = """
    QMenu {
        background-color: #252525;
        border: 1px solid #444;
        color: #eee;
        padding: 5px;
    }
    QMenu::item {
        padding: 8px 25px 8px 25px; /* Space for icons and text */
        border-radius: 3px;
    }
    QMenu::item:selected {
        background-color: #007acc;
        color: white;
    }
    QMenu::icon {
        margin-left: 10px;
    }
    QMenu::separator {
        height: 1px;
        background: #444;
        margin: 5px 10px;
    }
"""
# ------------------
# ICONS
#-------------------
# Fixed path of software icons folder
SOFTWARE_ICON_DIR = os.path.join(PROJECT_ROOT, "resource", "icons", "software")

def get_sw_icon(software_name):
    """
    Get the full path of the PNG file for each software
    """
    icon_path = os.path.join(SOFTWARE_ICON_DIR, f"{software_name.lower()}.png")
    if os.path.exists(icon_path):
        return icon_path
    return None

def get_engine_icon(engine_name):
    """Getting the render engine icon path"""
    if not engine_name or engine_name == "--------": return None
    icon_path = os.path.join(PROJECT_ROOT, "resource", "icons", "engines", f"{engine_name.lower()}.png")
    return icon_path if os.path.exists(icon_path) else None