from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QComboBox,
    QTextEdit,
)

from app.services.customer_service import CustomerService
from app.services.state_service import StateService
from app.ui.states.state_page import StatePage


class CustomerForm(QDialog):
    def __init__(self, parent=None, customer=None):
        super().__init__(parent)

        self.setWindowTitle("Customer Form")
        self.setMinimumWidth(520)
        self.customer = customer

        self.customer_service = CustomerService()
        self.state_service = StateService()

        self.setup_ui()
        self.load_states()

        if self.customer:
            self.populate_form()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Customer name")

        self.mail_input = QLineEdit()
        self.mail_input.setPlaceholderText("Mail")

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Phone")

        self.address_input = QTextEdit()
        self.address_input.setPlaceholderText("Address")
        self.address_input.setFixedHeight(80)

        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("City")

        self.state_combo = QComboBox()
        self.state_combo.setEditable(True)
        self.state_combo.setInsertPolicy(QComboBox.NoInsert)
        self.state_combo.lineEdit().setPlaceholderText("Type new state code - name or select existing")
        self.state_combo.activated.connect(self.on_state_combo_activated)

        self.pin_input = QLineEdit()
        self.pin_input.setPlaceholderText("PIN")

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Notes")
        self.notes_input.setFixedHeight(80)

        self.gst_input = QLineEdit()
        self.gst_input.setPlaceholderText("GSTN Code")

        self.attachments_input = QLineEdit()
        self.attachments_input.setPlaceholderText("Attachments")

        layout.addWidget(QLabel("Customer Name:"))
        layout.addWidget(self.name_input)
        layout.addWidget(QLabel("Mail:"))
        layout.addWidget(self.mail_input)
        layout.addWidget(QLabel("Phone:"))
        layout.addWidget(self.phone_input)
        layout.addWidget(QLabel("Address:"))
        layout.addWidget(self.address_input)
        layout.addWidget(QLabel("City:"))
        layout.addWidget(self.city_input)
        layout.addWidget(QLabel("State:"))
        layout.addWidget(self.state_combo)
        layout.addWidget(QLabel("PIN:"))
        layout.addWidget(self.pin_input)
        layout.addWidget(QLabel("Notes:"))
        layout.addWidget(self.notes_input)
        layout.addWidget(QLabel("GSTN Code:"))
        layout.addWidget(self.gst_input)
        layout.addWidget(QLabel("Attachments:"))
        layout.addWidget(self.attachments_input)

        buttons = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        self.save_btn.clicked.connect(self.save)
        self.cancel_btn.clicked.connect(self.reject)

        buttons.addWidget(self.save_btn)
        buttons.addWidget(self.cancel_btn)
        layout.addLayout(buttons)

    def load_states(self):
        states, _ = self.state_service.get_all_states()
        self.state_combo.clear()

        self.state_combo.addItem("Add new state...", None)
        for row in states:
            state_id = row[0]
            state_code = row[1]
            state_name = row[2]
            self.state_combo.addItem(f"{state_code} - {state_name}", state_id)

    def populate_form(self):
        self.name_input.setText(str(self.customer[1] or ""))
        self.mail_input.setText(str(self.customer[2] or ""))
        self.phone_input.setText(str(self.customer[3] or ""))
        self.address_input.setPlainText(str(self.customer[4] or ""))
        self.city_input.setText(str(self.customer[5] or ""))
        self.pin_input.setText(str(self.customer[7] or ""))
        self.notes_input.setPlainText(str(self.customer[8] or ""))
        self.gst_input.setText(str(self.customer[9] or ""))
        self.attachments_input.setText(str(self.customer[10] or ""))

        state_id = self.customer[6]
        if state_id is not None:
            index = self.state_combo.findData(state_id)
            if index != -1:
                self.state_combo.setCurrentIndex(index)
            else:
                self.state_combo.setEditText(str(self.customer[6]))

    def _find_state_id_from_text(self, text):
        normalized_text = text.strip().lower()
        if not normalized_text or normalized_text == "add new state...":
            return None

        for i in range(self.state_combo.count()):
            display_text = self.state_combo.itemText(i).strip().lower()
            if display_text == normalized_text:
                return self.state_combo.itemData(i)
            if " - " in display_text:
                code, name = display_text.split(" - ", 1)
                code = code.strip().lower()
                name = name.strip().lower()
                if code == normalized_text or name == normalized_text:
                    return self.state_combo.itemData(i)
        return None

    def _parse_state_input(self, text):
        text = text.strip()
        if not text:
            return None, None

        if " - " in text:
            state_code, state_name = [part.strip() for part in text.split(" - ", 1)]
            return state_code or self._generate_state_code(text), state_name or text

        state_code = self._generate_state_code(text)
        return state_code, text

    def _generate_state_code(self, text):
        words = [word for word in text.replace("-", " ").split() if word]
        if not words:
            return text[:3].upper()
        code = "".join(word[0].upper() for word in words)
        return code[:3]

    def _find_or_create_state(self, current_text):
        state_id = self._find_state_id_from_text(current_text)
        if state_id is not None:
            return state_id

        state_code, state_name = self._parse_state_input(current_text)
        if not state_name:
            return None

        # reuse existing state if either code or name matches
        states, _ = self.state_service.get_all_states()
        for row in states:
            existing_code = str(row[1] or "").strip().lower()
            existing_name = str(row[2] or "").strip().lower()
            if existing_code == state_code.strip().lower() or existing_name == state_name.strip().lower():
                return row[0]

        self.state_service.create(state_code, state_name)
        self.load_states()

        state_id = self._find_state_id_from_text(f"{state_code} - {state_name}")
        if state_id is not None:
            index = self.state_combo.findData(state_id)
            if index != -1:
                self.state_combo.setCurrentIndex(index)
        return state_id

    def _get_state_id(self):
        current_id = self.state_combo.currentData()
        if current_id is not None:
            return current_id

        typed_text = self.state_combo.currentText().strip()
        if typed_text.lower() == "add new state...":
            return None

        return self._find_or_create_state(typed_text)

    def on_state_combo_activated(self, index):
        if index < 0:
            return

        if self.state_combo.itemData(index) is None and self.state_combo.itemText(index) == "Add new state...":
            self.open_state_table_dialog()
            return

        self.state_combo.setCurrentIndex(index)

    def open_state_table_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Manage States")
        dialog.setMinimumSize(600, 500)

        layout = QVBoxLayout(dialog)
        state_page = StatePage()
        layout.addWidget(state_page)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        if dialog.exec() == QDialog.Accepted:
            self.load_states()
            typed_text = self.state_combo.currentText().strip()
            state_id = self._find_state_id_from_text(typed_text)
            if state_id is not None:
                self.state_combo.setCurrentIndex(self.state_combo.findData(state_id))

    def validate(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Validation", "Customer Name is required")
            return False

        if not self.city_input.text().strip():
            QMessageBox.warning(self, "Validation", "Customer City is required")
            return False

        typed_text = self.state_combo.currentText().strip()
        if self.state_combo.currentData() is None and (not typed_text or typed_text.lower() == "add new state..."):
            QMessageBox.warning(self, "Validation", "State selection or entry is required")
            return False

        return True

    def save(self):
        if not self.validate():
            return

        state_id = self._get_state_id()
        if state_id is None:
            QMessageBox.warning(self, "Validation", "State selection or entry is required")
            return

        customer_data = {
            "customer_name": self.name_input.text().strip(),
            "mail": self.mail_input.text().strip(),
            "phone": self.phone_input.text().strip(),
            "address": self.address_input.toPlainText().strip(),
            "city": self.city_input.text().strip(),
            "state_id": state_id,
            "pin": int(self.pin_input.text().strip()) if self.pin_input.text().strip().isdigit() else None,
            "notes": self.notes_input.toPlainText().strip(),
            "gstn_code": self.gst_input.text().strip(),
            "attachments": self.attachments_input.text().strip(),
        }

        try:
            if self.customer:
                self.customer_service.update_customer(
                    self.customer[0],
                    **customer_data,
                )
            else:
                self.customer_service.create_customer(**customer_data)

            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Save Error", f"Unable to save customer: {exc}")
