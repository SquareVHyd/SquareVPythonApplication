import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, 
    QFrame, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QMessageBox, QApplication
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

class BusbarCalculatorWidget(QWidget):
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
            "success_hover": "#157347",
            "danger": "#dc3545",
            "danger_hover": "#bb2d3b",
            "border": "#dee2e6",
            "table_header": "#e9ecef",
            "table_row_alt": "#f8f9fa"
        }

        self.history = []

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
        title_label = QLabel("Busbar Amps, Weight & Cost Calculator")
        title_label.setStyleSheet(f"color: {self.colors['text']}; font-weight: bold; font-size: 20px;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        self.create_form(main_layout)
        self.create_summary_cards(main_layout)
        self.create_table(main_layout)

        # Footer
        footer_label = QLabel("designed by govindayya.k")
        footer_label.setStyleSheet(f"color: {self.colors['subtext']}; font-style: italic;")
        footer_label.setAlignment(Qt.AlignRight)
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
            }}
        """

    def create_form(self, main_layout):
        form_frame = QFrame()
        form_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.colors['card_bg']};
                border: 1px solid {self.colors['border']};
                border-radius: 5px;
            }}
            QLabel {{ border: none; font-weight: bold; font-size: 12px; }}
        """)
        
        grid = QGridLayout(form_frame)
        grid.setContentsMargins(15, 15, 15, 15)
        grid.setSpacing(15)
        
        # --- COLUMN 1 ---
        # Metal
        grid.addWidget(QLabel("Metal"), 0, 0)
        self.metal_combo = QComboBox()
        self.metal_combo.addItems(["Copper", "Aluminium"])
        self.metal_combo.setStyleSheet(self._combo_style())
        self.metal_combo.currentIndexChanged.connect(self.on_metal_change)
        grid.addWidget(self.metal_combo, 1, 0)

        # Run
        grid.addWidget(QLabel("Run (No. of Bars)"), 2, 0)
        self.run_combo = QComboBox()
        self.run_combo.setEditable(True)
        self.run_combo.addItems(["1", "2", "3", "4", "5"])
        self.run_combo.setCurrentText("1")
        self.run_combo.setStyleSheet(self._combo_style())
        grid.addWidget(self.run_combo, 3, 0)
        
        # Length
        grid.addWidget(QLabel("Length (meters)"), 4, 0)
        self.length_entry = QLineEdit("2.0")
        self.length_entry.setStyleSheet(self._input_style())
        grid.addWidget(self.length_entry, 5, 0)

        # --- COLUMN 2 ---
        # Width
        grid.addWidget(QLabel("Width (mm)"), 0, 1)
        self.width_entry = QLineEdit("50")
        self.width_entry.setStyleSheet(self._input_style())
        grid.addWidget(self.width_entry, 1, 1)

        # Thickness
        grid.addWidget(QLabel("Thickness (mm)"), 2, 1)
        self.thick_combo = QComboBox()
        self.thick_combo.setEditable(True)
        self.thick_combo.addItems(["3", "6", "10", "12", "15"])
        self.thick_combo.setCurrentText("10")
        self.thick_combo.setStyleSheet(self._combo_style())
        grid.addWidget(self.thick_combo, 3, 1)

        # Cost
        grid.addWidget(QLabel("Cost / kg (₹)"), 4, 1)
        self.cost_entry = QLineEdit("750")
        self.cost_entry.setStyleSheet(self._input_style())
        grid.addWidget(self.cost_entry, 5, 1)

        # --- COLUMN 3 ---
        # Current Density
        grid.addWidget(QLabel("Current Density (A/mm²)"), 0, 2)
        self.density_combo = QComboBox()
        self.density_combo.setEditable(True)
        self.density_combo.addItems(["1.0", "1.2", "1.6"])
        self.density_combo.setCurrentText("0.8")
        self.density_combo.setStyleSheet(self._combo_style())
        grid.addWidget(self.density_combo, 1, 2)

        # Mat Density
        grid.addWidget(QLabel("Mat. Density (g/cm³)"), 2, 2)
        self.mat_density_entry = QLineEdit("8.96")
        self.mat_density_entry.setStyleSheet(self._input_style())
        grid.addWidget(self.mat_density_entry, 3, 2)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.calc_btn = QPushButton("Calculate")
        self.calc_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors['accent']};
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
                border: none;
            }}
            QPushButton:hover {{ background-color: {self.colors['accent_hover']}; }}
        """)
        self.calc_btn.clicked.connect(self.calculate)
        
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors['danger']};
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
                border: none;
            }}
            QPushButton:hover {{ background-color: {self.colors['danger_hover']}; }}
        """)
        self.clear_btn.clicked.connect(self.clear_history)

        btn_layout.addWidget(self.calc_btn)
        btn_layout.addWidget(self.clear_btn)
        
        btn_container = QWidget()
        btn_container.setLayout(btn_layout)
        grid.addWidget(btn_container, 4, 2, 2, 1, Qt.AlignBottom)

        main_layout.addWidget(form_frame)

    def create_summary_cards(self, main_layout):
        self.summary_frame = QFrame()
        self.summary_frame.setStyleSheet("border: none; background: transparent;")
        summary_layout = QHBoxLayout(self.summary_frame)
        summary_layout.setContentsMargins(0, 0, 0, 0)
        summary_layout.setSpacing(10)

        card_data = [
            ("TOTAL ITEMS", "count", "0", self.colors["text"]),
            ("TOTAL LENGTH (m)", "length", "0.0", self.colors["accent"]),
            ("TOTAL QTY (3.6m)", "qty_36", "0.0", "#6f42c1"),
            ("TOTAL WEIGHT", "weight", "0.0 kg", self.colors["danger"]),
            ("TOTAL COST", "cost", "₹0.0", self.colors["success"])
        ]
        
        self.summary_cards = {}
        for title, key, val, color in card_data:
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {self.colors['card_bg']};
                    border: 1px solid {self.colors['border']};
                    border-radius: 5px;
                }}
                QLabel {{ border: none; }}
            """)
            layout = QVBoxLayout(card)
            layout.setContentsMargins(10, 10, 10, 10)
            
            lbl_title = QLabel(title)
            lbl_title.setStyleSheet(f"color: {self.colors['subtext']}; font-weight: bold; font-size: 10px;")
            lbl_title.setAlignment(Qt.AlignCenter)
            
            lbl_val = QLabel(val)
            lbl_val.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 16px;")
            lbl_val.setAlignment(Qt.AlignCenter)
            
            lbl_split = QLabel("Cu: 0 | Al: 0")
            lbl_split.setStyleSheet(f"color: {self.colors['subtext']}; font-style: italic; font-size: 10px;")
            lbl_split.setAlignment(Qt.AlignCenter)
            
            layout.addWidget(lbl_title)
            layout.addWidget(lbl_val)
            layout.addWidget(lbl_split)
            
            self.summary_cards[key] = (lbl_val, lbl_split)
            summary_layout.addWidget(card)
            
        main_layout.addWidget(self.summary_frame)

    def create_table(self, main_layout):
        controls_row = QHBoxLayout()
        controls_label = QLabel("Calculated Records List")
        controls_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        copy_btn = QPushButton("📋 Copy to Excel")
        copy_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors['success']};
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 4px;
                border: none;
            }}
            QPushButton:hover {{ background-color: {self.colors['success_hover']}; }}
        """)
        copy_btn.clicked.connect(self.copy_to_clipboard)
        
        controls_row.addWidget(controls_label)
        controls_row.addStretch()
        controls_row.addWidget(copy_btn)
        main_layout.addLayout(controls_row)

        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "No.", "Metal", "Size (R x W x T x L)", "Amps (A)", "Qty (3.6m)", 
            "Wt/m (kg)", "Tot Wt (kg)", "Tot Cost (₹)", "Action"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeToContents)
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
        main_layout.addWidget(self.table, 1)

    def on_metal_change(self, index):
        metal = self.metal_combo.currentText()
        self.density_combo.clear()
        if metal == "Copper":
            self.density_combo.addItems(["1.0", "1.2", "1.6"])
            self.density_combo.setCurrentText("0.8")
            self.mat_density_entry.setText("8.96")
            self.cost_entry.setText("750")
        else:  # Aluminium
            self.density_combo.addItems(["0.6", "0.8", "0.9"])
            self.density_combo.setCurrentText("0.8")
            self.mat_density_entry.setText("2.70")
            self.cost_entry.setText("220")

    def calculate(self):
        try:
            run = float(self.run_combo.currentText())
            width = float(self.width_entry.text())
            thick = float(self.thick_combo.currentText())
            length = float(self.length_entry.text())
            density = float(self.density_combo.currentText())
            mat_density = float(self.mat_density_entry.text())
            cost_per_kg = float(self.cost_entry.text())
            metal = self.metal_combo.currentText()

            amps = run * width * thick * density
            qty_36 = (length * run) / 3.6
            wt_per_meter = (width * thick * mat_density) / 1000.0
            tot_weight = wt_per_meter * length * run
            tot_cost = tot_weight * cost_per_kg

            record = {
                "metal": metal, "run": run, "width": width, "thick": thick,
                "length": length, "density": density, "amps": amps,
                "qty_36": qty_36, "wt_m": wt_per_meter, "tot_wt": tot_weight, "tot_cost": tot_cost
            }
            self.history.append(record)
            self.render_history()
        except ValueError:
            pass

    def render_history(self):
        self.table.setRowCount(0)
        
        total_length = total_qty_36 = total_weight = total_cost = 0.0
        cu_count = al_count = 0
        cu_length = al_length = cu_qty_36 = al_qty_36 = cu_weight = al_weight = cu_cost = al_cost = 0.0

        for idx, rec in enumerate(self.history):
            self.table.insertRow(idx)
            
            size_str = f"{int(rec['run'])}x{int(rec['width'])}x{int(rec['thick'])}@{rec['length']:.1f}m"
            formatted_amps = format_indian_currency(rec["amps"], with_symbol=False)
            formatted_qty_36 = format_indian_currency(rec["qty_36"], with_symbol=False)
            formatted_wt_m = format_indian_currency(rec["wt_m"], with_symbol=False)
            formatted_tot_wt = format_indian_currency(rec["tot_wt"], with_symbol=False)
            formatted_cost = format_indian_currency(rec["tot_cost"], with_symbol=True)
            
            items = [
                str(idx + 1), rec["metal"], size_str, formatted_amps, 
                formatted_qty_36, formatted_wt_m, formatted_tot_wt, formatted_cost
            ]
            
            for col, text in enumerate(items):
                it = QTableWidgetItem(text)
                it.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(idx, col, it)
                
            del_btn = QPushButton("Delete")
            del_btn.setStyleSheet(f"background-color: {self.colors['danger']}; color: white; border-radius: 3px;")
            del_btn.clicked.connect(lambda checked, i=idx: self.delete_record(i))
            self.table.setCellWidget(idx, 8, del_btn)

            item_len = rec["length"] * rec["run"]
            total_length += item_len
            total_qty_36 += rec["qty_36"]
            total_weight += rec["tot_wt"]
            total_cost += rec["tot_cost"]

            if rec["metal"] == "Copper":
                cu_count += 1
                cu_length += item_len
                cu_qty_36 += rec["qty_36"]
                cu_weight += rec["tot_wt"]
                cu_cost += rec["tot_cost"]
            else:
                al_count += 1
                al_length += item_len
                al_qty_36 += rec["qty_36"]
                al_weight += rec["tot_wt"]
                al_cost += rec["tot_cost"]

        # Update summary cards
        self.summary_cards["count"][0].setText(str(len(self.history)))
        self.summary_cards["count"][1].setText(f"Cu: {cu_count} | Al: {al_count}")
        
        self.summary_cards["length"][0].setText(format_indian_currency(total_length, with_symbol=False) + " m")
        self.summary_cards["length"][1].setText(f"Cu: {format_indian_currency(cu_length, with_symbol=False)}m | Al: {format_indian_currency(al_length, with_symbol=False)}m")

        self.summary_cards["qty_36"][0].setText(format_indian_currency(total_qty_36, with_symbol=False) + " bars")
        self.summary_cards["qty_36"][1].setText(f"Cu: {format_indian_currency(cu_qty_36, with_symbol=False)} | Al: {format_indian_currency(al_qty_36, with_symbol=False)}")

        self.summary_cards["weight"][0].setText(format_indian_currency(total_weight, with_symbol=False) + " kg")
        self.summary_cards["weight"][1].setText(f"Cu: {format_indian_currency(cu_weight, with_symbol=False)}kg | Al: {format_indian_currency(al_weight, with_symbol=False)}kg")

        self.summary_cards["cost"][0].setText(format_indian_currency(total_cost, with_symbol=True))
        self.summary_cards["cost"][1].setText(f"Cu: {format_indian_currency(cu_cost, with_symbol=True)} | Al: {format_indian_currency(al_cost, with_symbol=True)}")

    def delete_record(self, index):
        if 0 <= index < len(self.history):
            del self.history[index]
            self.render_history()

    def clear_history(self):
        self.history = []
        self.render_history()

    def copy_to_clipboard(self):
        if not self.history:
            QMessageBox.information(self, "Clipboard", "History is empty. Add some calculations first!")
            return

        headers = ["No.", "Metal", "Run", "Width (mm)", "Thickness (mm)", "Length (m)", "Current Density (A/mm²)", "Amps (A)", "Qty (3.6m lengths)", "Wt/m (kg/m)", "Tot Wt (kg)", "Tot Cost (₹)"]
        tsv_lines = ["\t".join(headers)]

        total_length = total_qty_36 = total_weight = total_cost = 0.0
        cu_count = al_count = cu_length = al_length = cu_qty_36 = al_qty_36 = cu_weight = al_weight = cu_cost = al_cost = 0.0

        for idx, rec in enumerate(self.history):
            row_data = [
                str(idx + 1), rec["metal"], str(rec["run"]), str(rec["width"]), str(rec["thick"]),
                str(rec["length"]), str(rec["density"]), f"{rec['amps']:.1f}", f"{rec['qty_36']:.1f}",
                f"{rec['wt_m']:.1f}", f"{rec['tot_wt']:.1f}", f"{rec['tot_cost']:.1f}"
            ]
            tsv_lines.append("\t".join(row_data))

            item_len = rec["length"] * rec["run"]
            total_length += item_len
            total_qty_36 += rec["qty_36"]
            total_weight += rec["tot_wt"]
            total_cost += rec["tot_cost"]

            if rec["metal"] == "Copper":
                cu_count += 1
                cu_length += item_len
                cu_qty_36 += rec["qty_36"]
                cu_weight += rec["tot_wt"]
                cu_cost += rec["tot_cost"]
            else:
                al_count += 1
                al_length += item_len
                al_qty_36 += rec["qty_36"]
                al_weight += rec["tot_wt"]
                al_cost += rec["tot_cost"]

        tsv_lines.append("")
        
        totals_row = [""] * len(headers)
        totals_row[0] = "TOTALS"
        totals_row[5] = f"{total_length:.1f}"
        totals_row[8] = f"{total_qty_36:.1f}"
        totals_row[10] = f"{total_weight:.1f}"
        totals_row[11] = f"{total_cost:.1f}"
        tsv_lines.append("\t".join(totals_row))

        cu_row = [""] * len(headers)
        cu_row[0] = "Copper Totals"
        cu_row[1] = f"{cu_count} items"
        cu_row[5] = f"{cu_length:.1f}"
        cu_row[8] = f"{cu_qty_36:.1f}"
        cu_row[10] = f"{cu_weight:.1f}"
        cu_row[11] = f"{cu_cost:.1f}"
        tsv_lines.append("\t".join(cu_row))

        al_row = [""] * len(headers)
        al_row[0] = "Aluminium Totals"
        al_row[1] = f"{al_count} items"
        al_row[5] = f"{al_length:.1f}"
        al_row[8] = f"{al_qty_36:.1f}"
        al_row[10] = f"{al_weight:.1f}"
        al_row[11] = f"{al_cost:.1f}"
        tsv_lines.append("\t".join(al_row))

        QApplication.clipboard().setText("\n".join(tsv_lines))
        QMessageBox.information(self, "Clipboard", "Calculations and Totals copied to clipboard!\nYou can now open Excel and paste.")
