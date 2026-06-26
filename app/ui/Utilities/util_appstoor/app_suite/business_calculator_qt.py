import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

try:
    from app.ui.Utilities.util_appstoor.app_suite.utils import format_indian_currency
except ImportError:
    try:
        from utils import format_indian_currency
    except ImportError:
        def format_indian_currency(value, with_symbol=True):
            return f"₹{value:,.2f}" if with_symbol else f"{value:,.2f}"

class BusinessCalculatorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #f8f9fa;")
        
        # Colors (match light theme)
        self.colors = {
            "bg": "#f8f9fa",
            "card_bg": "#ffffff",
            "text": "#212529",
            "subtext": "#6c757d",
            "accent": "#0d6efd",
            "accent_hover": "#0b5ed7",
            "success": "#198754",
            "danger": "#dc3545",
            "border": "#dee2e6",
            "table_header": "#e9ecef",
            "table_row_alt": "#f8f9fa"
        }

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)
        
        # Header (Logo + Title)
        header_layout = QHBoxLayout()
        self.logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            self.logo_label.setPixmap(pixmap.scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
        company_name = QLabel("SQUARE V ENGINEERING ENTERPRISES")
        company_name.setStyleSheet(f"color: {self.colors['accent']}; font-weight: bold; font-size: 14px;")
        
        header_layout.addWidget(self.logo_label)
        header_layout.addWidget(company_name)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Title
        title_label = QLabel("Business Base Calculator")
        title_label.setStyleSheet(f"color: {self.colors['text']}; font-weight: bold; font-size: 20px;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Form Container
        self.form_frame = QFrame()
        self.form_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.colors['card_bg']};
                border: 1px solid {self.colors['border']};
                border-radius: 5px;
            }}
            QLabel {{
                border: none;
            }}
        """)
        form_layout = QVBoxLayout(self.form_frame)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(15)

        # Total Value Input
        total_label = QLabel("Total Value (₹)")
        total_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.total_entry = QLineEdit("100")
        self.total_entry.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {self.colors['border']};
                padding: 8px;
                border-radius: 3px;
                background-color: white;
                font-size: 14px;
            }}
        """)
        self.total_entry.textChanged.connect(self.calculate)
        form_layout.addWidget(total_label)
        form_layout.addWidget(self.total_entry)

        # Calculate Button (Optional, as it auto-calculates, but kept for UI similarity)
        self.calc_btn = QPushButton("Calculate Margins & Discounts")
        self.calc_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors['accent']};
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 10px;
                border-radius: 4px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {self.colors['accent_hover']};
            }}
        """)
        self.calc_btn.clicked.connect(self.calculate)
        form_layout.addWidget(self.calc_btn)

        # Results Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Rate (%)", "Profit (₹)", "Discount (₹)", "DiscountValue (₹)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {self.colors['card_bg']};
                border: 1px solid {self.colors['border']};
            }}
            QHeaderView::section {{
                background-color: {self.colors['table_header']};
                font-weight: bold;
                border: 1px solid {self.colors['border']};
                padding: 4px;
            }}
        """)
        form_layout.addWidget(self.table, 1)

        main_layout.addWidget(self.form_frame, 1)

        # Footer
        footer_label = QLabel("designed by govindayya.k")
        footer_label.setStyleSheet(f"color: {self.colors['subtext']}; font-style: italic;")
        footer_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(footer_label)
        
        # Initial calculation
        self.calculate()

    def calculate(self):
        self.table.setRowCount(0)
        try:
            total_val_str = self.total_entry.text().strip()
            if not total_val_str:
                return
            total_val = float(total_val_str)
        except ValueError:
            return

        rates = [1, 2, 3, 4, 5, 10, 15, 20, 25, 30]

        for idx, rate in enumerate(rates):
            margin_val = total_val * (1.0 + rate / 100.0)
            discount_val = total_val * (1.0 - rate / 100.0)
            diff_val = total_val * (rate / 100.0)
            
            self.table.insertRow(idx)
            
            # Rate
            item_rate = QTableWidgetItem(f"{rate}%")
            item_rate.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(idx, 0, item_rate)
            
            # Profit
            item_margin = QTableWidgetItem(format_indian_currency(margin_val))
            item_margin.setTextAlignment(Qt.AlignCenter)
            item_margin.setForeground(Qt.black) # Use stylesheet colors if possible, but qt color is fine
            self.table.setItem(idx, 1, item_margin)
            
            # Discount
            item_discount = QTableWidgetItem(format_indian_currency(discount_val))
            item_discount.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(idx, 2, item_discount)
            
            # Discount Value
            item_diff = QTableWidgetItem(format_indian_currency(diff_val))
            item_diff.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(idx, 3, item_diff)
