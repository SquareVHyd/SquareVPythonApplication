from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox
)
from PySide6.QtCore import Qt

class GenericSpecForm(QDialog):
    def __init__(self, parent=None, item_description="", remark_makes="", mode="Add"):
        super().__init__(parent)
        self.setWindowTitle(f"{mode} Generic Item")
        self.setMinimumWidth(400)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Generic Item Description *"))
        self.description_input = QLineEdit()
        self.description_input.setText(item_description)
        self.description_input.setPlaceholderText("Enter generic item description...")
        layout.addWidget(self.description_input)

        layout.addWidget(QLabel("Remark/Makes"))
        self.remark_makes_input = QLineEdit()
        self.remark_makes_input.setText(remark_makes)
        self.remark_makes_input.setPlaceholderText("Enter makes separated by / ...")
        layout.addWidget(self.remark_makes_input)

        # Action Buttons
        save_btn = QPushButton("Save")
        save_btn.setStyleSheet("background-color: #2563eb; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
        save_btn.clicked.connect(self._on_save)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #64748b; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
        cancel_btn.clicked.connect(self.reject)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.description_input.setFocus()

    def keyPressEvent(self, event):
        """Allow saving on pressing Enter."""
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._on_save()
            return
        super().keyPressEvent(event)

    def _on_save(self):
        desc = self.description_input.text().strip()
        if not desc:
            QMessageBox.warning(self, "Validation Error", "Generic Item Description cannot be empty.")
            return
        self.accept()

    def get_description(self):
        return self.description_input.text().strip()

    def get_remark_makes(self):
        return self.remark_makes_input.text().strip()
