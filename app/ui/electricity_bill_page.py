from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, 
    QLabel, QGroupBox, QFormLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QTabWidget, QMessageBox, QComboBox, QFileDialog,
    QTextEdit
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
import pyodbc
import csv
import os
import webbrowser
from datetime import datetime

DSN_NAME = "PostgreSQLLH"
ALL_COLS = "id, billing_month, eb_kvah_old, eb_kvah_new, eb_charged_units, eb_pf, unit_rate, total_bill_amount, derived_fixed_charges, sri_old, sri_new, sri_units, sri_pct, sri_total, sq_old, sq_new, sq_units, sq_pct, sq_total, excess_units, eb_kwh_old, eb_kwh_new"

class DB:
    @staticmethod
    def connect():
        return pyodbc.connect(f"DSN={DSN_NAME};", autocommit=True)

    @staticmethod
    def execute(sql, params=(), fetch=False, commit=False):
        conn = None
        try:
            conn = DB.connect()
            cur = conn.cursor()
            cur.execute(sql, params)
            if fetch:
                return [list(row) for row in cur.fetchall()]
            if commit:
                conn.commit()
            return True 
        except Exception as exc:
            print(f"Database Error: {exc}")
            return False 
        finally:
            if conn: conn.close()

    @staticmethod
    def fetchone(sql, params=()):
        conn = None
        try:
            conn = DB.connect()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchone()
            return list(row) if row else None
        except Exception as exc:
            print(f"Fetch Failed: {exc}")
            return None
        finally:
            if conn: conn.close()

def get_date_obj(month_str):
    try:
        return datetime.strptime(month_str, "%b-%y")
    except:
        return datetime.min

def get_fy_from_month(month_str):
    dt = get_date_obj(month_str)
    if dt == datetime.min: return "Unknown FY"
    start_year = dt.year - 1 if dt.month < 4 else dt.year
    return f"FY{start_year}-{str(start_year+1)[-2:]}"

class ElectricityBillPage(QWidget):
    def __init__(self):
        super().__init__()
        self.current_edit_id = None
        self.setup_ui()
        self.update_global_dropdowns()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        
        # Tab 1: Entry
        self.tab_entry = QWidget()
        self.setup_entry_tab()
        self.tabs.addTab(self.tab_entry, "1. New/Edit Entry")
        
        # Tab 2: History
        self.tab_history = QWidget()
        self.setup_history_tab()
        self.tabs.addTab(self.tab_history, "2. Bill History")
        
        # Tab 3: Financial Trends
        self.tab_trends = QWidget()
        self.setup_trends_tab()
        self.tabs.addTab(self.tab_trends, "3. Financial Trends")

        # Tab 4: PF Trend
        self.tab_pf = QWidget()
        self.setup_pf_tab()
        self.tabs.addTab(self.tab_pf, "4. PF Trend")

        # Tab 5: Report
        self.tab_report = QWidget()
        self.setup_report_tab()
        self.tabs.addTab(self.tab_report, "5. Monthly Report")

        self.main_layout.addWidget(self.tabs)

    def setup_entry_tab(self):
        layout = QVBoxLayout(self.tab_entry)
        
        # EB Main Section
        eb_group = QGroupBox("EB Main Bill Details")
        eb_form = QFormLayout(eb_group)
        
        self.ent_month = QLineEdit(); self.ent_month.setPlaceholderText("e.g., Mar-26")
        self.ent_rate = QLineEdit("7.7")
        self.ent_total_bill = QLineEdit()
        self.ent_kvah_old = QLineEdit(); self.ent_kvah_new = QLineEdit()
        self.ent_eb_units = QLineEdit()
        self.ent_kwh_old = QLineEdit(); self.ent_kwh_new = QLineEdit()
        self.ent_eb_pf = QLineEdit(); self.ent_eb_pf.setReadOnly(True)
        
        self.lbl_eb_kvah_hint = QLabel("Prev: --"); self.lbl_eb_kvah_hint.setStyleSheet("color: gray;")
        self.lbl_eb_kwh_hint = QLabel("Prev: --"); self.lbl_eb_kwh_hint.setStyleSheet("color: gray;")

        eb_form.addRow("Billing Month:", self.ent_month)
        eb_form.addRow("Unit Rate (Rs):", self.ent_rate)
        eb_form.addRow("Total Bill (Rs):", self.ent_total_bill)
        eb_form.addRow("KVAH Old:", self.ent_kvah_old)
        eb_form.addRow("", self.lbl_eb_kvah_hint)
        eb_form.addRow("KVAH New:", self.ent_kvah_new)
        eb_form.addRow("Charged Units:", self.ent_eb_units)
        eb_form.addRow("KWH Old:", self.ent_kwh_old)
        eb_form.addRow("", self.lbl_eb_kwh_hint)
        eb_form.addRow("KWH New:", self.ent_kwh_new)
        eb_form.addRow("Calculated PF:", self.ent_eb_pf)
        
        layout.addWidget(eb_group)
        
        # Local Sub-Meters
        local_group = QGroupBox("Local Sub-Meters Detail")
        local_form = QFormLayout(local_group)
        
        self.sri_old = QLineEdit(); self.sri_new = QLineEdit()
        self.sq_old = QLineEdit(); self.sq_new = QLineEdit()
        
        self.lbl_sri_hint = QLabel("Prev: --"); self.lbl_sri_hint.setStyleSheet("color: gray;")
        self.lbl_sq_hint = QLabel("Prev: --"); self.lbl_sq_hint.setStyleSheet("color: gray;")

        local_form.addRow(QLabel("<b>SRINIVAS (MF: 20)</b>"), QLabel(""))
        local_form.addRow("Old Reading:", self.sri_old)
        local_form.addRow("", self.lbl_sri_hint)
        local_form.addRow("New Reading:", self.sri_new)
        
        local_form.addRow(QLabel("<b>SQUARE V (MF: 1)</b>"), QLabel(""))
        local_form.addRow("Old Reading:", self.sq_old)
        local_form.addRow("", self.lbl_sq_hint)
        local_form.addRow("New Reading:", self.sq_new)
        
        layout.addWidget(local_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("💾 Calculate & Save Record")
        self.btn_save.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        self.btn_save.clicked.connect(self.process_logic)
        
        self.btn_clear = QPushButton("🧹 Clear Form")
        self.btn_clear.clicked.connect(self.clear_form)
        
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_clear)
        layout.addLayout(btn_layout)
        layout.addStretch()

    def setup_history_tab(self):
        layout = QVBoxLayout(self.tab_history)
        
        top_bar = QHBoxLayout()
        self.fy_filter = QComboBox()
        self.fy_filter.addItem("All Data")
        top_bar.addWidget(QLabel("<b>Financial Year:</b>"))
        top_bar.addWidget(self.fy_filter)
        
        self.fy_filter.currentTextChanged.connect(self.load_history)
        
        export_btn = QPushButton("📥 Export to CSV")
        export_btn.clicked.connect(self.export_to_csv)
        top_bar.addWidget(export_btn)
        top_bar.addStretch()
        
        layout.addLayout(top_bar)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(8)
        self.history_table.setHorizontalHeaderLabels([
            "ID", "Month", "Total Bill (₹)", "Excess (KVAH)", "Diff (KWH)", "PF", "Srinivas (₹)", "Square V (₹)"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.history_table.itemDoubleClicked.connect(self.load_record_for_edit)
        
        layout.addWidget(self.history_table)

    def setup_trends_tab(self):
        layout = QVBoxLayout(self.tab_trends)
        controls = QHBoxLayout()
        
        self.trend_selector = QComboBox()
        self.trend_selector.addItems(["Financial Billed (Rs)", "Units Consumed", "Excess Units Trend", "KWH vs KVAH Units"])
        
        self.trend_fy_filter = QComboBox()
        self.trend_fy_filter.addItem("All Data")
        
        gen_btn = QPushButton("📈 Generate Trend")
        gen_btn.clicked.connect(self.plot_trends)
        
        controls.addWidget(QLabel("Trend Type:"))
        controls.addWidget(self.trend_selector)
        controls.addWidget(QLabel("FY Filter:"))
        controls.addWidget(self.trend_fy_filter)
        controls.addWidget(gen_btn)
        controls.addStretch()
        
        layout.addLayout(controls)
        
        self.trend_figure, self.trend_ax = plt.subplots(figsize=(8, 4))
        self.trend_canvas = FigureCanvas(self.trend_figure)
        self.trend_toolbar = NavigationToolbar(self.trend_canvas, self)
        
        layout.addWidget(self.trend_toolbar)
        layout.addWidget(self.trend_canvas)

    def setup_pf_tab(self):
        layout = QVBoxLayout(self.tab_pf)
        btn = QPushButton("🔄 Refresh PF Efficiency Trend")
        btn.clicked.connect(self.plot_pf)
        layout.addWidget(btn)
        
        self.pf_figure, self.pf_ax = plt.subplots(figsize=(8, 4))
        self.pf_canvas = FigureCanvas(self.pf_figure)
        self.pf_toolbar = NavigationToolbar(self.pf_canvas, self)
        
        layout.addWidget(self.pf_toolbar)
        layout.addWidget(self.pf_canvas)

    def setup_report_tab(self):
        layout = QVBoxLayout(self.tab_report)
        
        controls = QHBoxLayout()
        self.report_month_combo = QComboBox()
        
        preview_btn = QPushButton("👁️ Preview Report")
        preview_btn.clicked.connect(self.preview_report)
        
        html_btn = QPushButton("📄 Print / Save HTML")
        html_btn.setStyleSheet("background-color: #ff5722; color: white; font-weight: bold;")
        html_btn.clicked.connect(self.generate_html_report)
        
        controls.addWidget(QLabel("Select Month:"))
        controls.addWidget(self.report_month_combo)
        controls.addWidget(preview_btn)
        controls.addWidget(html_btn)
        controls.addStretch()
        
        layout.addLayout(controls)
        
        self.report_preview = QTextEdit()
        self.report_preview.setReadOnly(True)
        self.report_preview.setFont(QFont("Courier New", 10))
        layout.addWidget(self.report_preview)

    def update_global_dropdowns(self):
        rows = DB.execute('SELECT DISTINCT billing_month FROM public."tbl_EBbillR1"', fetch=True)
        if not rows: return
        
        raw_months = [r[0] for r in rows if r[0]]
        sorted_months = sorted(raw_months, key=get_date_obj)
        
        fys = sorted(list(set([get_fy_from_month(m) for m in sorted_months if get_fy_from_month(m) != "Unknown FY"])))
        
        # Update FY Filters
        self.fy_filter.blockSignals(True)
        self.fy_filter.clear()
        self.fy_filter.addItem("All Data")
        self.fy_filter.addItems(fys)
        self.fy_filter.blockSignals(False)

        self.trend_fy_filter.clear()
        self.trend_fy_filter.addItem("All Data")
        self.trend_fy_filter.addItems(fys)

        # Update Month Combo
        self.report_month_combo.clear()
        self.report_month_combo.addItems(reversed(sorted_months))
        
        self.load_history()
        self.plot_trends()
        self.plot_pf()
        self.fetch_latest_readings()

    def fetch_latest_readings(self):
        row = DB.fetchone('SELECT eb_kvah_new, sri_new, sq_new, eb_kwh_new FROM public."tbl_EBbillR1" ORDER BY id DESC LIMIT 1')
        if row:
            self.lbl_eb_kvah_hint.setText(f"Prev: {row[0]}")
            self.lbl_sri_hint.setText(f"Prev: {row[1]}")
            self.lbl_sq_hint.setText(f"Prev: {row[2]}")
            self.lbl_eb_kwh_hint.setText(f"Prev: {row[3] if row[3] else 0}")

    def clear_form(self):
        self.current_edit_id = None
        self.btn_save.setText("Calculate & Save NEW Record")
        self.btn_save.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        
        fields = [
            self.ent_month, self.ent_rate, self.ent_total_bill, self.ent_kvah_old, self.ent_kvah_new,
            self.ent_eb_units, self.ent_eb_pf, self.ent_kwh_old, self.ent_kwh_new,
            self.sri_old, self.sri_new, self.sq_old, self.sq_new
        ]
        for f in fields: f.clear()
        self.ent_rate.setText("7.7")
        self.fetch_latest_readings()

    def process_logic(self):
        try:
            month = self.ent_month.text()
            rate = float(self.ent_rate.text())
            total_bill = float(self.ent_total_bill.text())
            eb_units = float(self.ent_eb_units.text())
            
            kvah_old = int(self.ent_kvah_old.text() or 0)
            kvah_new = int(self.ent_kvah_new.text() or 0)
            kwh_old = int(self.ent_kwh_old.text() or 0)
            kwh_new = int(self.ent_kwh_new.text() or 0)

            sri_old_val = int(self.sri_old.text() or 0)
            sri_new_val = int(self.sri_new.text() or 0)
            sq_old_val = int(self.sq_old.text() or 0)
            sq_new_val = int(self.sq_new.text() or 0)

            kwh_diff = kwh_new - kwh_old
            kvah_diff = kvah_new - kvah_old
            eb_pf = round(kwh_diff / kvah_diff, 4) if kvah_diff > 0 else 0.0
            self.ent_eb_pf.setText(str(eb_pf))

            units_charge_total = eb_units * rate
            derived_fixed_charges = total_bill - units_charge_total
            half_fixed = derived_fixed_charges / 2

            sri_units = (sri_new_val - sri_old_val) * 20
            sq_units = (sq_new_val - sq_old_val) * 1
            total_local = sri_units + sq_units
            excess_units = eb_units - total_local

            sri_pct = sri_units / total_local if total_local > 0 else 0
            sq_pct = sq_units / total_local if total_local > 0 else 0

            sri_shared_amt = (excess_units * sri_pct) * rate
            sq_shared_amt = (excess_units * sq_pct) * rate

            sri_final = (sri_units * rate) + half_fixed + sri_shared_amt
            sq_final = (sq_units * rate) + half_fixed + sq_shared_amt

            data_tuple = (month, kvah_old, kvah_new, eb_units, eb_pf, rate, total_bill, derived_fixed_charges,
                          sri_old_val, sri_new_val, sri_units, sri_pct, sri_final,
                          sq_old_val, sq_new_val, sq_units, sq_pct, sq_final, excess_units, kwh_old, kwh_new)

            if self.current_edit_id:
                query = f"""UPDATE public."tbl_EBbillR1" SET 
                            billing_month=?, eb_kvah_old=?, eb_kvah_new=?, eb_charged_units=?, eb_pf=?, unit_rate=?, 
                            total_bill_amount=?, derived_fixed_charges=?, 
                            sri_old=?, sri_new=?, sri_units=?, sri_pct=?, sri_total=?, 
                            sq_old=?, sq_new=?, sq_units=?, sq_pct=?, sq_total=?, excess_units=?,
                            eb_kwh_old=?, eb_kwh_new=?
                            WHERE id=?"""
                result = DB.execute(query, data_tuple + (self.current_edit_id,), commit=True)
            else:
                query = f"""INSERT INTO public."tbl_EBbillR1" 
                            (billing_month, eb_kvah_old, eb_kvah_new, eb_charged_units, eb_pf, unit_rate, 
                            total_bill_amount, derived_fixed_charges, 
                            sri_old, sri_new, sri_units, sri_pct, sri_total, 
                            sq_old, sq_new, sq_units, sq_pct, sq_total, excess_units, eb_kwh_old, eb_kwh_new) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
                result = DB.execute(query, data_tuple, commit=True)

            if result:
                QMessageBox.information(self, "Success", "Record saved successfully!")
                self.clear_form()
                self.update_global_dropdowns()
        except Exception as e:
            QMessageBox.critical(self, "Input Error", f"Ensure all fields are valid.\nError: {e}")

    def load_history(self):
        self.history_table.setRowCount(0)
        rows = DB.execute(f'SELECT {ALL_COLS} FROM public."tbl_EBbillR1"', fetch=True)
        if not rows: return
        
        rows = sorted(rows, key=lambda x: get_date_obj(x[1]), reverse=True)
        
        target_fy = self.fy_filter.currentText()
        if target_fy != "All Data":
            rows = [r for r in rows if get_fy_from_month(r[1]) == target_fy]

        self.history_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            kwh_diff = (r[21] - r[20]) if (r[21] is not None and r[20] is not None) else 0
            items = [
                str(r[0]), str(r[1]), f"{r[7]:.2f}", f"{r[19]:.1f}", 
                str(kwh_diff), str(r[5]), f"{r[13]:.2f}", f"{r[18]:.2f}"
            ]
            for j, val in enumerate(items):
                self.history_table.setItem(i, j, QTableWidgetItem(val))

    def load_record_for_edit(self, item):
        row_idx = item.row()
        record_id = int(self.history_table.item(row_idx, 0).text())
        
        row = DB.fetchone(f'SELECT {ALL_COLS} FROM public."tbl_EBbillR1" WHERE id=?', (record_id,))
        if row:
            self.clear_form()
            self.current_edit_id = record_id
            self.btn_save.setText(f"UPDATE Record #{record_id}")
            self.btn_save.setStyleSheet("background-color: #ff9800; color: white; font-weight: bold; padding: 8px;")
            
            self.ent_month.setText(str(row[1]))
            self.ent_kvah_old.setText(str(row[2])); self.ent_kvah_new.setText(str(row[3]))
            self.ent_eb_units.setText(str(row[4]))
            self.ent_eb_pf.setText(str(row[5]))
            self.ent_rate.setText(str(row[6]))
            self.ent_total_bill.setText(str(row[7]))
            self.sri_old.setText(str(row[9])); self.sri_new.setText(str(row[10]))
            self.sq_old.setText(str(row[14])); self.sq_new.setText(str(row[15]))
            
            if row[20] is not None: self.ent_kwh_old.setText(str(row[20]))
            if row[21] is not None: self.ent_kwh_new.setText(str(row[21]))
            
            self.tabs.setCurrentIndex(0)

    def export_to_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Visible History", "", "CSV Files (*.csv)")
        if not path: return
        
        try:
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(ALL_COLS.split(", "))
                for row in range(self.history_table.rowCount()):
                    record_id = self.history_table.item(row, 0).text()
                    data = DB.fetchone(f'SELECT * FROM public."tbl_EBbillR1" WHERE id=?', (record_id,))
                    writer.writerow(data)
            QMessageBox.information(self, "Success", "Data exported successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))

    def plot_trends(self):
        self.trend_ax.clear()
        data = DB.execute(f'SELECT {ALL_COLS} FROM public."tbl_EBbillR1"', fetch=True)
        if not data: return

        data = sorted(data, key=lambda x: get_date_obj(x[1]))
        fy = self.trend_fy_filter.currentText()
        if fy != "All Data":
            data = [r for r in data if get_fy_from_month(r[1]) == fy]

        months = [r[1] for r in data]
        sel = self.trend_selector.currentText()

        if sel == "Financial Billed (Rs)":
            self.trend_ax.plot(months, [r[7] for r in data], marker='D', label='Total Bill', color='black', ls='--')
            self.trend_ax.plot(months, [r[13] for r in data], marker='o', label='Srinivas', color='blue')
            self.trend_ax.plot(months, [r[18] for r in data], marker='s', label='Square V', color='orange')
        elif sel == "Units Consumed":
            self.trend_ax.plot(months, [r[4] for r in data], marker='D', label='Total Units', color='black', ls='--')
        elif sel == "Excess Units Trend":
            self.trend_ax.plot(months, [r[19] for r in data], marker='^', label='System Loss', color='red')
        elif sel == "KWH vs KVAH Units":
            kvah = [r[3]-r[2] for r in data]; kwh = [r[21]-r[20] for r in data]
            self.trend_ax.plot(months, kvah, marker='o', label='KVAH (Billed)')
            self.trend_ax.plot(months, kwh, marker='^', label='KWH (Actual)')

        self.trend_ax.set_title(f"{sel} Trend")
        self.trend_ax.legend()
        self.trend_ax.grid(True, alpha=0.3)
        self.trend_figure.autofmt_xdate()
        self.trend_canvas.draw()

    def plot_pf(self):
        self.pf_ax.clear()
        data = DB.execute('SELECT billing_month, eb_pf FROM public."tbl_EBbillR1"', fetch=True)
        if not data: return
        
        data = sorted(data, key=lambda x: get_date_obj(x[0]))
        months, pfs = [r[0] for r in data], [r[1] for r in data]
        
        self.pf_ax.plot(months, pfs, marker='^', color='purple', lw=2, label='PF Efficiency')
        self.pf_ax.axhline(0.99, color='green', ls=':', label='Target')
        self.pf_ax.axhline(0.90, color='red', ls=':', label='Penalty')
        self.pf_ax.set_title("System Power Factor Trend")
        self.pf_ax.legend()
        self.pf_figure.autofmt_xdate()
        self.pf_canvas.draw()

    def preview_report(self):
        month = self.report_month_combo.currentText()
        row = DB.fetchone(f'SELECT {ALL_COLS} FROM public."tbl_EBbillR1" WHERE billing_month=?', (month,))
        if not row: return

        text = f"""
=======================================================
        MONTHLY ELECTRICITY REPORT: {row[1]}
=======================================================

>> UTILITY BILL SUMMARY
Total Bill Amount Paid : Rs {row[7]:.2f}
Total Charged Units    : {row[4]}
Unit Rate              : Rs {row[6]:.2f}
System Power Factor    : {row[5]}
Derived Fixed Charges  : Rs {row[8]:.2f}
System Loss (Excess)   : {row[19]:.1f} Units

>> SRINIVAS ACCOUNT (MF: 20)
Units Consumed         : {row[11]}
FINAL INVOICE AMOUNT   : Rs {row[13]:.2f}

>> SQUARE V ACCOUNT (MF: 1)
Units Consumed         : {row[16]}
FINAL INVOICE AMOUNT   : Rs {row[18]:.2f}
=======================================================
"""
        self.report_preview.setText(text)

    def generate_html_report(self):
        month = self.report_month_combo.currentText()
        row = DB.fetchone(f'SELECT {ALL_COLS} FROM public."tbl_EBbillR1" WHERE billing_month=?', (month,))
        if not row: return

        html = f"""
        <html><head><style>
            body {{ font-family: Arial; padding: 40px; }}
            .header {{ text-align: center; border-bottom: 2px solid #004d99; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ padding: 10px; border: 1px solid #ddd; text-align: left; }}
            .total {{ background: #e6f2ff; font-weight: bold; }}
        </style></head><body>
            <div class="header">
                <h1>SVEE Electricity Bill Allocation</h1>
                <h3>Period: {row[1]}</h3>
            </div>
            <table>
                <tr><th>Description</th><th>Details</th></tr>
                <tr><td>Total Billed Amount</td><td><b>₹{row[7]:,.2f}</b></td></tr>
                <tr><td>Total Units</td><td>{row[4]}</td></tr>
                <tr><td>Power Factor</td><td>{row[5]}</td></tr>
            </table>
            <h3>Tenant Breakdown</h3>
            <table>
                <tr><th>Tenant</th><th>Units</th><th>Total Allocation</th></tr>
                <tr><td>Srinivas</td><td>{row[11]}</td><td class="total">₹{row[13]:,.2f}</td></tr>
                <tr><td>Square V</td><td>{row[16]}</td><td class="total">₹{row[18]:,.2f}</td></tr>
            </table>
            <p style="margin-top: 40px; font-size: 10px;">Generated via Enterprise ERP</p>
        </body></html>
        """
        path = os.path.abspath("temp_bill_report.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        webbrowser.open('file://' + path)