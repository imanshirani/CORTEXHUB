from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                               QPushButton, QHBoxLayout, QSpinBox)
from PySide6.QtCore import Qt
from app.ui import style

class ShotDialog(QDialog):
    def __init__(self, session, shot_to_edit=None, parent=None):
        """
        Handle   Init   operation.
        """
        super().__init__(parent)
        self.session = session
        self.shot_to_edit = shot_to_edit
        
        title = "Edit Shot" if shot_to_edit else "Create New Shot"
        self.setWindowTitle(title)
        self.setFixedSize(350, 250)
        self.setStyleSheet(style.DIALOG_STYLESHEET)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. Shot Name
        layout.addWidget(QLabel("Shot Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. SH_010")
        self.name_input.setStyleSheet(style.INPUT_STYLE)
        layout.addWidget(self.name_input)
        
        # 2. Frame Range
        range_layout = QHBoxLayout()
        
        # Start Frame
        s_layout = QVBoxLayout()
        s_layout.addWidget(QLabel("Start Frame:"))
        self.start_spin = QSpinBox()
        self.start_spin.setRange(0, 1000000)
        self.start_spin.setValue(1001)
        self.start_spin.setStyleSheet(style.SPINBOX_STYLE)
        s_layout.addWidget(self.start_spin) # این خط بود
        
        # End Frame
        e_layout = QVBoxLayout()
        e_layout.addWidget(QLabel("End Frame:"))
        self.end_spin = QSpinBox()
        self.end_spin.setRange(0, 1000000)
        self.end_spin.setValue(1100)
        self.end_spin.setStyleSheet(style.SPINBOX_STYLE)
        
        # ++++++ این خط جا افتاده بود! ++++++
        e_layout.addWidget(self.end_spin) 
        # +++++++++++++++++++++++++++++++++++
        
        range_layout.addLayout(s_layout)
        range_layout.addLayout(e_layout)
        layout.addLayout(range_layout)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Save Shot")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet(style.BTN_SUCCESS)
        btn_save.clicked.connect(self.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)
        
        if self.shot_to_edit:
            self.load_data()

    def load_data(self):
        """
        Handle Load Data operation.
        """
        self.name_input.setText(self.shot_to_edit[2])
        self.start_spin.setValue(self.shot_to_edit[3])
        self.end_spin.setValue(self.shot_to_edit[4])

    def get_data(self):
        """
        Handle Get Data operation.
        """
        return {
            "name": self.name_input.text().strip(),
            "start": self.start_spin.value(),
            "end": self.end_spin.value()
        }