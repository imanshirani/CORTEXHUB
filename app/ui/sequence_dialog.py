from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt
from app.ui import style

class SequenceDialog(QDialog):
    def __init__(self, session, seq_to_edit=None, parent=None):
        """
        Handle   Init   operation.
        """
        super().__init__(parent)
        self.session = session
        self.seq_to_edit = seq_to_edit
        
        title = "Edit / Rename Sequence" if seq_to_edit else "Create New Sequence"
        self.setWindowTitle(title)
        self.setFixedSize(350, 180)
        self.setStyleSheet(style.DIALOG_STYLESHEET)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        layout.addWidget(QLabel("Sequence Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. SEQ_01")
        self.name_input.setStyleSheet(style.INPUT_STYLE)
        layout.addWidget(self.name_input)
        
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Save Sequence")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet(style.BTN_SUCCESS)
        btn_save.clicked.connect(self.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)
        
        if self.seq_to_edit:
            # Data returned from the database: (id, project_id, name)
            self.name_input.setText(self.seq_to_edit[2])

    def get_data(self):
        """
        Handle Get Data operation.
        """
        return self.name_input.text().strip()