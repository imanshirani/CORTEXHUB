import sys
import os


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication, QDialog
from app.core.session import SessionManager
from app.ui.login_window import LoginWindow
from app.ui.main_window import MainWindow
from app.ui import style

def main():
    """
    Handle Main operation.
    """
    app = QApplication(sys.argv)
    #app.setStyleSheet(style.DARK_THEME + style.INPUT_STYLE + style.DIALOG_STYLESHEET)
    #app.setStyleSheet(
        #style.DARK_THEME + "\n" + 
        #style.INPUT_STYLE + "\n" + 
        #style.DIALOG_STYLESHEET + "\n" + 
        #style.DIALOG_BUTTON_STYLE
    #)

    while True:
        try:
            
            session = SessionManager()
            login_dialog = LoginWindow(session)
            if login_dialog.exec() == QDialog.Accepted:
                window = MainWindow(session)
                window.show()
                app.exec()
                
                if not getattr(window, 'logout_requested', False):
                    break
            else:
                
                break
                
        except Exception as e:
            print(f"Critical Error: {e}")
            break

    sys.exit()

if __name__ == "__main__":
    main()