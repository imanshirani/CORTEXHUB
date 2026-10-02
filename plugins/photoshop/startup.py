import os
import sys
import subprocess
import importlib

def install_dependencies():
    """
    Check and auto-install Photoshop Python libraries.
    """
    try:
        import photoshop
        print(">> [Cortex] Photoshop API is already installed.")
    except ImportError:
        print(">> [Cortex] Photoshop API not found. Installing...")
        try:
            # Use sys.executable so the package lands in the current interpreter
            subprocess.check_call([sys.executable, "-m", "pip", "install", "photoshop-python-api"])
            print(">> [Cortex] Photoshop API installed successfully.")
        except Exception as e:
            print(f"!! [Cortex] Failed to install Photoshop API: {e}")

def init_photoshop_cortex():
    print(">> [Cortex] Initializing Photoshop Integration...")
    install_dependencies()

    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(os.path.dirname(current_dir)) 

    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)

    try:
        import cortex_ui
        importlib.reload(cortex_ui)
        cortex_ui.show_ui()
    except Exception as e:
        print(f"!! [Cortex] Startup Error: {e}")

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    
    # Create a QApplication when this module is run standalone
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    init_photoshop_cortex()
    
    # Keep the process alive so the toolbar stays visible
    sys.exit(app.exec())