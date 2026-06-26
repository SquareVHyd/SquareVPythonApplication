import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QFrame
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QPixmap, QIcon

# Ensure utils is imported properly depending on execution context
try:
    from app.ui.Utilities.util_appstoor.app_suite.utils import format_indian_currency
except ImportError:
    try:
        from utils import format_indian_currency
    except ImportError:
        def format_indian_currency(value, with_symbol=True):
            return f"₹{value:,.2f}" if with_symbol else f"{value:,.2f}"

class GstCalculatorWidget(QWidget):
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
            "disabled": "#e9ecef"
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
        title_label = QLabel("GST Calculator")
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

        # Calculation Mode
        mode_label = QLabel("Calculation Mode")
        mode_label.setStyleSheet("font-weight: bold;")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Add GST (Calculate Final Price)", "Remove GST (Calculate Net Price)"])
        self.mode_combo.setStyleSheet(self._combo_style())
        self.mode_combo.currentIndexChanged.connect(self.on_mode_change)
        form_layout.addWidget(mode_label)
        form_layout.addWidget(self.mode_combo)

        # Net Price
        self.net_label = QLabel("Net Price (₹)")
        self.net_label.setStyleSheet("font-weight: bold;")
        self.net_entry = QLineEdit("1000")
        self.net_entry.setStyleSheet(self._input_style())
        form_layout.addWidget(self.net_label)
        form_layout.addWidget(self.net_entry)

        # GST Rate
        rate_label = QLabel("GST Rate (%)")
        rate_label.setStyleSheet("font-weight: bold;")
        self.rate_combo = QComboBox()
        self.rate_combo.setEditable(True)
        self.rate_combo.addItems(["5", "12", "18", "28"])
        self.rate_combo.setCurrentText("18")
        self.rate_combo.setStyleSheet(self._combo_style())
        form_layout.addWidget(rate_label)
        form_layout.addWidget(self.rate_combo)

        # Final Price
        self.final_label = QLabel("Final Amount (₹)")
        self.final_label.setStyleSheet("font-weight: bold;")
        self.final_entry = QLineEdit()
        self.final_entry.setStyleSheet(self._input_style())
        self.final_entry.setEnabled(False)
        form_layout.addWidget(self.final_label)
        form_layout.addWidget(self.final_entry)

        # Calculate Button
        self.calc_btn = QPushButton("Calculate")
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

        # Results area
        self.res_net_label = QLabel("Net Price: ₹0.00")
        self.res_net_label.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {self.colors['text']};")
        
        self.res_gst_label = QLabel("GST Amount: ₹0.00")
        self.res_gst_label.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {self.colors['danger']};")
        
        self.res_final_label = QLabel("Final Amount: ₹0.00")
        self.res_final_label.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {self.colors['success']};")

        form_layout.addWidget(self.res_net_label)
        form_layout.addWidget(self.res_gst_label)
        form_layout.addWidget(self.res_final_label)

        main_layout.addWidget(self.form_frame, 0, Qt.AlignTop | Qt.AlignHCenter)
        self.form_frame.setMinimumWidth(340)

        main_layout.addStretch()

        # Footer
        footer_label = QLabel("designed by govindayya.k")
        footer_label.setStyleSheet(f"color: {self.colors['subtext']}; font-style: italic;")
        footer_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(footer_label)

    def _combo_style(self):
        return f"""
            QComboBox {{
                border: 1px solid {self.colors['border']};
                padding: 5px;
                border-radius: 3px;
                background-color: white;
            }}
        """

    def _input_style(self):
        return f"""
            QLineEdit {{
                border: 1px solid {self.colors['border']};
                padding: 5px;
                border-radius: 3px;
                background-color: white;
                color: {self.colors['text']};
            }}
            QLineEdit:disabled {{
                background-color: {self.colors['disabled']};
                color: {self.colors['subtext']};
            }}
        """

    def on_mode_change(self, index):
        if index == 0:  # Add GST
            self.net_entry.setEnabled(True)
            self.final_entry.setEnabled(False)
            self.final_entry.clear()
        else:  # Remove GST
            self.final_entry.setEnabled(True)
            self.net_entry.setEnabled(False)
            self.net_entry.clear()
            self.final_entry.setText("1180")

    def calculate(self):
        try:
            mode = self.mode_combo.currentIndex()
            gst_rate_str = self.rate_combo.currentText()
            gst_rate = float(gst_rate_str) if gst_rate_str else 0.0

            if mode == 0:  # Add GST
                net_price = float(self.net_entry.text())
                gst_amount = net_price * (gst_rate / 100.0)
                final_amount = net_price + gst_amount
                
                self.final_entry.setEnabled(True)
                self.final_entry.setText(f"{final_amount:.1f}")
                self.final_entry.setEnabled(False)
            else:  # Remove GST
                final_amount = float(self.final_entry.text())
                net_price = final_amount / (1.0 + (gst_rate / 100.0))
                gst_amount = final_amount - net_price
                
                self.net_entry.setEnabled(True)
                self.net_entry.setText(f"{net_price:.1f}")
                self.net_entry.setEnabled(False)

            self.res_net_label.setText(f"Net Price: {format_indian_currency(net_price)}")
            self.res_gst_label.setText(f"GST Amount: {format_indian_currency(gst_amount)}")
            self.res_final_label.setText(f"Final Amount: {format_indian_currency(final_amount)}")

        except ValueError:
            self.res_net_label.setText("Invalid numbers entered.")
            self.res_gst_label.setText("")
            self.res_final_label.setText("")
