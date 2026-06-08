import math
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QMessageBox,
    QInputDialog,
    QCompleter
)

from PySide6.QtCore import Qt

from app.services.price_list_service import PriceListService


class PriceListForm(QDialog):

    def __init__(self, parent=None, price_item=None):

        super().__init__(parent)

        self.setWindowTitle("Price List Item")
        self.setMinimumWidth(650)

        self.service = PriceListService()

        layout = QVBoxLayout(self)

        self.description = QLineEdit()
        self.model = QLineEdit()
        self.list_price = QLineEdit()
        self.list_price.textChanged.connect(self._calculate_prices)
        self.discount = QLineEdit()
        self.discount.textChanged.connect(self._calculate_prices)
        self.net_price = QLineEdit()
        self.net_price.textChanged.connect(self._calculate_total)
        self.used_qty = QLineEdit()
        self.used_qty.textChanged.connect(self._calculate_total)
        self.total_amount = QLineEdit()
        self.total_amount.setReadOnly(True)

        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self.category_combo.setInsertPolicy(QComboBox.NoInsert)

        self.category_completer = QCompleter(
            self.category_combo.model(),
            self
        )

        self.category_completer.setCaseSensitivity(
            Qt.CaseInsensitive
        )

        self.category_completer.setFilterMode(
            Qt.MatchContains
        )

        self.category_combo.setCompleter(
            self.category_completer
        )

        self.make_combo = QComboBox()
        self.make_combo.setEditable(True)
        self.make_combo.setInsertPolicy(QComboBox.NoInsert)

        self.make_completer = QCompleter(
            self.make_combo.model(),
            self
        )

        self.make_completer.setCaseSensitivity(
            Qt.CaseInsensitive
        )

        self.make_completer.setFilterMode(
            Qt.MatchContains
        )

        self.make_combo.setCompleter(
            self.make_completer
        )

        layout.addWidget(QLabel("Item Description"))
        layout.addWidget(self.description)

        layout.addWidget(QLabel("Model"))
        layout.addWidget(self.model)

        layout.addWidget(QLabel("Category"))
        layout.addWidget(self.category_combo)

        layout.addWidget(QLabel("Make"))
        layout.addWidget(self.make_combo)

        layout.addWidget(QLabel("List Price"))
        layout.addWidget(self.list_price)

        layout.addWidget(QLabel("Discount Percent"))
        layout.addWidget(self.discount)

        layout.addWidget(QLabel("Net Price"))
        layout.addWidget(self.net_price)

        layout.addWidget(QLabel("Used Qty"))
        layout.addWidget(self.used_qty)

        layout.addWidget(QLabel("Total Amount"))
        layout.addWidget(self.total_amount)

        self.new_category_btn = QPushButton("Add Category")
        self.new_category_btn.clicked.connect(
            self.add_new_category
        )

        self.new_make_btn = QPushButton("Add Make")
        self.new_make_btn.clicked.connect(
            self.add_new_make
        )

        lookup_layout = QHBoxLayout()
        lookup_layout.addWidget(self.new_category_btn)
        lookup_layout.addWidget(self.new_make_btn)

        layout.addLayout(lookup_layout)

        buttons = QPushButton("Save")
        buttons.clicked.connect(self._on_save)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(buttons)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

        self._populate_lookups()

        if price_item:

            self.description.setText(
                str(price_item[1] or "")
            )

            self.model.setText(
                str(price_item[2] or "")
            )

            self.list_price.setText(
                str(price_item[5] or "")
            )

            self.discount.setText(
                f"{(float(price_item[6]) * 100):.2f}" if price_item[6] is not None else ""
            )

            self.net_price.setText(
                str(price_item[7] or "")
            )

            self.used_qty.setText(
                str(price_item[8] or "")
            )

            self.total_amount.setText(
                str(price_item[9] or "")
            )

            self._select_combo_value(
                self.category_combo,
                price_item[10]
            )

            self._select_combo_value(
                self.make_combo,
                price_item[11]
            )

    def _calculate_prices(self):
        try:
            lp = float(self.list_price.text() or 0)
            dp = round(float(self.discount.text() or 0), 2)
            np = math.ceil(lp * (1 - dp / 100) * 10000) / 10000
            self.net_price.blockSignals(True)
            self.net_price.setText(f"{np:.4f}")
            self.net_price.blockSignals(False)
            self._calculate_total()
        except ValueError:
            pass

    def _calculate_total(self):
        try:
            np = float(self.net_price.text() or 0)
            qty = float(self.used_qty.text() or 0)
            total = np * qty
            self.total_amount.setText(f"{total:.2f}")
        except ValueError:
            pass

    def _populate_lookups(self):

        self.category_combo.clear()

        self.category_combo.addItem(
            "",
            None
        )

        for row in self.service.get_all_categories():

            self.category_combo.addItem(
                str(row[1] or ""),
                row[0]
            )

        self.make_combo.clear()

        self.make_combo.addItem(
            "",
            None
        )

        for row in self.service.get_all_makes():

            self.make_combo.addItem(
                str(row[1] or ""),
                row[0]
            )

    def add_new_category(self):

        text, ok = QInputDialog.getText(
            self,
            "New Category",
            "Category Name"
        )

        if ok and text.strip():

            self.service.create_category(
                text.strip()
            )

            self._populate_lookups()

            self._select_combo_label(
                self.category_combo,
                text.strip()
            )

    def add_new_make(self):

        text, ok = QInputDialog.getText(
            self,
            "New Make",
            "Make Name"
        )

        if ok and text.strip():

            self.service.create_make(
                text.strip()
            )

            self._populate_lookups()

            self._select_combo_label(
                self.make_combo,
                text.strip()
            )

    def _select_combo_value(self, combo, value):

        if value is None:
            combo.setCurrentIndex(0)
            return

        index = combo.findData(value)

        if index >= 0:
            combo.setCurrentIndex(index)

    def _select_combo_label(self, combo, label):

        index = combo.findText(
            label,
            Qt.MatchFixedString
        )

        if index >= 0:
            combo.setCurrentIndex(index)

    def _on_save(self):

        try:

            desc = self.description.text().strip()
            model = self.model.text().strip()
            
            if not desc:
                raise ValueError("Item Description is required")

            if not model:
                raise ValueError("Model is required")

            # Database Pre-validation: Ensure numeric strings are actually numbers
            # to avoid database transaction crashes.
            try:
                float(self.list_price.text() or 0)
                float(self.discount.text() or 0)
                float(self.net_price.text() or 0)
                float(self.used_qty.text() or 0)
            except ValueError:
                raise ValueError("List Price, Discount, Net Price, and Qty must be valid numbers")

        except Exception as e:

            QMessageBox.warning(
                self,
                "Validation",
                str(e)
            )

            return

        self.accept()

    def get_data(self):

        return {

            "item_description":
                self.description.text().strip(),

            "model":
                self.model.text().strip(),

            "list_price":
                float(self.list_price.text() or 0),

            "discount_percent":
                round(float(self.discount.text() or 0), 2) / 100.0,

            "net_price":
                float(self.net_price.text() or 0),

            "used_qty":
                float(self.used_qty.text() or 0),

            "total_amount":
                float(self.total_amount.text() or 0),

            "category_id":
                self.category_combo.currentData(),

            "make_id":
                self.make_combo.currentData()
        }