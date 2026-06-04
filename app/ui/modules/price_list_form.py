from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QLabel
from PySide6.QtGui import QDoubleValidator

class PriceListForm(QDialog):
    def __init__(self, parent=None, item_data=None):
        super().__init__(parent)
        self.setWindowTitle("Price Item Editor")
        self.setup_ui()
        
        if item_data:
            # Load existing data...
            pass

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Net Price Input
        layout.addWidget(QLabel("Net Price:"))
        self.net_price_input = QLineEdit()
        self.net_price_input.setValidator(QDoubleValidator(0, 999999, 2))
        layout.addWidget(self.net_price_input)

        # Discount Percentage Input
        layout.addWidget(QLabel("Discount (%):"))
        self.discount_input = QLineEdit()
        self.discount_input.setValidator(QDoubleValidator(0, 100, 2))
        self.discount_input.setText("0")
        layout.addWidget(self.discount_input)

        # Total Amount (Read Only)
        layout.addWidget(QLabel("Total Amount:"))
        self.total_amount_display = QLineEdit()
        self.total_amount_display.setReadOnly(True)
        self.total_amount_display.setStyleSheet("background-color: #f0f0f0; font-weight: bold;")
        layout.addWidget(self.total_amount_display)

        # SIGNALS FOR AUTOUPDATE
        # Connect textChanged to the calculation logic
        self.net_price_input.textChanged.connect(self.calculate_total)
        self.discount_input.textChanged.connect(self.calculate_total)

    def calculate_total(self):
        """Automatically updates the total amount based on price and discount."""
        try:
            # Convert input text to floats, default to 0.0 if empty
            net_price = float(self.net_price_input.text() or 0.0)
            discount_percent = float(self.discount_input.text() or 0.0)
            
            # Calculate: Total = Net - (Net * Discount / 100)
            total = net_price * (1 - (discount_percent / 100))
            
            # Display result formatted to 2 decimal places
            self.total_amount_display.setText(f"{total:.2f}")
        except ValueError:
            self.total_amount_display.setText("0.00")