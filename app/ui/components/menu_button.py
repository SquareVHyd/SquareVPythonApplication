from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import Qt

class MenuButton(QPushButton):
    """A custom styled button for sidebar navigation menus."""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #000000;
                text-align: left;
                padding: 10px 16px;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                outline: none;
            }
            QPushButton:hover:!disabled {
                background-color: #e0f2fe;
                color: #000000;
            }
            QPushButton:checked {
                background-color: #e2e8f0;
                color: #000000;
                border: 1px solid #cbd5e1;
                border-left: 4px solid #3b82f6;
                border-top-left-radius: 0px;
                border-bottom-left-radius: 0px;
                padding-left: 12px;
            }
            QPushButton:disabled {
                color: #94a3b8;
                background-color: transparent;
                border: none;
            }
        """)
