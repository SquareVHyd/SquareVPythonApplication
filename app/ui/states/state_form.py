from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
)


class StateForm(QDialog):
    def __init__(self, parent=None, state=None):
        super().__init__(parent)

        self.state = state
        self.setWindowTitle("State Form")
        self.setMinimumWidth(380)

        self.setup_ui()

        if self.state:
            self.populate_form()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("State code")

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("State name")

        layout.addWidget(QLabel("State Code:"))
        layout.addWidget(self.code_input)
        layout.addWidget(QLabel("State Name:"))
        layout.addWidget(self.name_input)

        buttons = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        buttons.addWidget(self.save_btn)
        buttons.addWidget(self.cancel_btn)
        layout.addLayout(buttons)

    def populate_form(self):
        self.code_input.setText(str(self.state[1] or ""))
        self.name_input.setText(str(self.state[2] or ""))

    def validate(self):
        if not self.code_input.text().strip():
            QMessageBox.warning(self, "Validation", "State code is required")
            return False

        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Validation", "State name is required")
            return False

        return True

    def get_data(self):
        if not self.validate():
            return None

        return {
            "state_code": self.code_input.text().strip(),
            "state_name": self.name_input.text().strip(),
        }
