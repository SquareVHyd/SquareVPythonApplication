import os
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, 
    QLabel, QGroupBox, QFormLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QTabWidget, QMessageBox, QComboBox, QFileDialog,
    QDateEdit
)
from PySide6.QtCore import Qt, QDate

# reportlab imports for PDF generation
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from app.ui.searchable_table import NumericTableWidgetItem

FILE_PATH = r"G:\My Drive\SVEE2\01 CompanyDocs\10 ZED\04 Records\02-Filled Records\TimelyDeliveryRecords.xlsx"

COLUMNS = [
    "Buyer (Bill to)", "Description of Goods", "Quantity", "Per", 
    "Order Date", "Despatched Date", "Delivery Date", "Invoice No.", 
    "e-Way Bill No.", "Sl No", "HSN/SAC", "Unit Rate", "Amount", "Total Amount", "Lapped Days"
]
NUMERIC_COLS = ["Quantity", "Unit Rate", "Amount", "Total Amount"]
DATE_COLS = ["Order Date", "Despatched Date", "Delivery Date"]

class TimelyDeliveryPage(QWidget):
    def __init__(self):
        super().__init__()
        self.df = pd.DataFrame(columns=COLUMNS)
        self.filtered_df = pd.DataFrame()
        self.load_data()
        self.setup_ui()
        self.refresh_table()

    def load_data(self):
        if os.path.exists(FILE_PATH):
            try:
                self.df = pd.read_excel(FILE_PATH)
                for col in COLUMNS:
                    if col not in self.df.columns: self.df[col] = ""
                self.calculate_lapped_days()
            except Exception as e:
                print(f"Excel Read Error: {e}")
                self.df = pd.DataFrame(columns=COLUMNS)
        else:
            self.df = pd.DataFrame(columns=COLUMNS)

    def calculate_lapped_days(self):
        self.df['Order Date'] = pd.to_datetime(self.df['Order Date'], errors='coerce')
        self.df['Delivery Date'] = pd.to_datetime(self.df['Delivery Date'], errors='coerce')
        
        def calc_diff(row):
            if pd.notnull(row['Order Date']) and pd.notnull(row['Delivery Date']):
                return int((row['Delivery Date'] - row['Order Date']).days)
            return 0
            
        self.df['Lapped Days'] = self.df.apply(calc_diff, axis=1)

    def format_value(self, col, val):
        if pd.isna(val) or str(val).strip() == "":
            return ""
        if col in DATE_COLS:
            try: return pd.to_datetime(val).strftime('%d-%b-%Y')
            except: return str(val)
        elif col in ["e-Way Bill No.", "HSN/SAC", "Sl No", "Lapped Days"]:
            try: return str(int(float(val)))
            except: return str(val)
        elif col in NUMERIC_COLS:
            try: return f"{float(val):,.2f}"
            except: return str(val)
        return str(val)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # --- Filter Section ---
        filter_group = QGroupBox("Search & Date Range Filters")
        filter_layout = QHBoxLayout(filter_group)
        
        filter_layout.addWidget(QLabel("Search:"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Common Filter (Text)...")
        self.search_box.textChanged.connect(self.refresh_table)
        filter_layout.addWidget(self.search_box)
        
        filter_layout.addWidget(QLabel("From:"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate(datetime.now().year, 1, 1))
        filter_layout.addWidget(self.date_from)
        
        filter_layout.addWidget(QLabel("To:"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate(datetime.now().year, 12, 31))
        filter_layout.addWidget(self.date_to)
        
        apply_btn = QPushButton("📅 Apply Date Filter")
        apply_btn.clicked.connect(self.refresh_table)
        filter_layout.addWidget(apply_btn)
        
        reset_btn = QPushButton("🧹 Reset All")
        reset_btn.clicked.connect(self.clear_filters)
        filter_layout.addWidget(reset_btn)
        
        layout.addWidget(filter_group)

        self.tabs = QTabWidget()
        
        # Tab 1: Data Records
        self.tab_records = QWidget()
        self.setup_records_tab()
        self.tabs.addTab(self.tab_records, "📝 Data Records")
        
        # Tab 2: Dashboard
        self.tab_dashboard = QWidget()
        self.setup_dashboard_tab()
        self.tabs.addTab(self.tab_dashboard, "📊 Dashboard")
        
        # Tab 3: Trends
        self.tab_trends = QWidget()
        self.setup_trends_tab()
        self.tabs.addTab(self.tab_trends, "📈 Trend Analysis")
        
        layout.addWidget(self.tabs)
        
        # Status Bar
        self.status_lbl = QLabel("Ready")
        layout.addWidget(self.status_lbl)

    def setup_records_tab(self):
        layout = QVBoxLayout(self.tab_records)
        
        self.table = QTableWidget()
        self.table.setColumnCount(len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.itemDoubleClicked.connect(self.edit_selected_record)
        layout.addWidget(self.table)
        
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("➕ Add New Record")
        add_btn.clicked.connect(self.add_record)
        
        edit_btn = QPushButton("✏️ Edit Selected")
        edit_btn.clicked.connect(self.edit_selected_record)
        
        del_btn = QPushButton("🗑️ Delete")
        del_btn.clicked.connect(self.delete_record)
        
        export_pdf_btn = QPushButton("📄 Export PDF")
        export_pdf_btn.clicked.connect(self.export_pdf)
        
        export_excel_btn = QPushButton("📊 Export Excel")
        export_excel_btn.clicked.connect(self.export_excel)
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(export_pdf_btn)
        btn_layout.addWidget(export_excel_btn)
        layout.addLayout(btn_layout)

    def setup_dashboard_tab(self):
        layout = QVBoxLayout(self.tab_dashboard)
        
        kpi_layout = QHBoxLayout()
        self.lbl_tot_rev = QLabel("Total Revenue\n₹ 0.00")
        self.lbl_tot_qty = QLabel("Total Quantity\n0")
        self.lbl_invoices = QLabel("Total Invoices\n0")
        self.lbl_avg_days = QLabel("Avg Lapped Days\n0 Days")
        
        for lbl in [self.lbl_tot_rev, self.lbl_tot_qty, self.lbl_invoices, self.lbl_avg_days]:
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-size: 16px; font-weight: bold; border: 1px solid #ccc; padding: 10px; background: #f9f9f9;")
            kpi_layout.addWidget(lbl)
        
        layout.addLayout(kpi_layout)
        
        stats_layout = QHBoxLayout()
        
        # Top Buyers
        buyer_group = QGroupBox("Top 5 Buyers (By Revenue)")
        buyer_vbox = QVBoxLayout(buyer_group)
        self.buyer_table = QTableWidget(0, 3)
        self.buyer_table.setHorizontalHeaderLabels(["Buyer", "Revenue", "Qty"])
        self.buyer_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        buyer_vbox.addWidget(self.buyer_table)
        stats_layout.addWidget(buyer_group)
        
        # Top Products
        prod_group = QGroupBox("Top 5 Products (By Revenue)")
        prod_vbox = QVBoxLayout(prod_group)
        self.prod_table = QTableWidget(0, 3)
        self.prod_table.setHorizontalHeaderLabels(["Product", "Revenue", "Qty"])
        self.prod_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        prod_vbox.addWidget(self.prod_table)
        stats_layout.addWidget(prod_group)
        
        layout.addLayout(stats_layout)

    def setup_trends_tab(self):
        layout = QVBoxLayout(self.tab_trends)
        
        controls = QHBoxLayout()
        self.trend_metric = QComboBox()
        self.trend_metric.addItems(["Total Revenue", "Total Quantity", "Avg Lapped Days"])
        
        self.trend_group = QComboBox()
        self.trend_group.addItems(["Overall", "Buyer", "Product"])
        
        self.trend_freq = QComboBox()
        self.trend_freq.addItems(["Daily", "Weekly", "Monthly"])
        
        gen_btn = QPushButton("📈 Generate Trend")
        gen_btn.clicked.connect(self.update_trends)
        
        controls.addWidget(QLabel("Metric:"))
        controls.addWidget(self.trend_metric)
        controls.addWidget(QLabel("Group By:"))
        controls.addWidget(self.trend_group)
        controls.addWidget(QLabel("Frequency:"))
        controls.addWidget(self.trend_freq)
        controls.addWidget(gen_btn)
        controls.addStretch()
        layout.addLayout(controls)
        
        self.fig, self.ax = plt.subplots(figsize=(10, 5))
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar(self.canvas, self)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

    def refresh_table(self):
        self.table.setRowCount(0)
        self.filtered_df = self.df.copy()
        
        search = self.search_box.text().lower()
        if search:
            self.filtered_df = self.filtered_df[self.filtered_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]

        start_dt = pd.to_datetime(self.date_from.date().toPython())
        end_dt = pd.to_datetime(self.date_to.date().toPython())
        
        self.filtered_df['Delivery Date'] = pd.to_datetime(self.filtered_df['Delivery Date'], errors='coerce')
        mask = (self.filtered_df['Delivery Date'] >= start_dt) & (self.filtered_df['Delivery Date'] <= end_dt)
        self.filtered_df = self.filtered_df[mask]

        self.table.setRowCount(len(self.filtered_df))
        for i, (idx, row) in enumerate(self.filtered_df.iterrows()):
            for j, col in enumerate(COLUMNS):
                val = self.format_value(col, row[col])
                item = NumericTableWidgetItem(val)
                item.setData(Qt.UserRole, idx) # Store original index
                self.table.setItem(i, j, item)
        
        self.update_status()
        self.update_dashboard()
        self.update_trends()

    def update_status(self):
        q_sum = pd.to_numeric(self.filtered_df['Quantity'], errors='coerce').sum()
        a_sum = pd.to_numeric(self.filtered_df['Amount'], errors='coerce').sum()
        t_sum = pd.to_numeric(self.filtered_df['Total Amount'], errors='coerce').sum()
        self.status_lbl.setText(f" Showing {len(self.filtered_df)} Records | Total Qty: {q_sum:,.0f} | Total Amt: {a_sum:,.2f} | Grand Total: {t_sum:,.2f}")

    def clear_filters(self):
        self.search_box.clear()
        self.date_from.setDate(QDate(datetime.now().year, 1, 1))
        self.date_to.setDate(QDate(datetime.now().year, 12, 31))
        self.refresh_table()

    def update_dashboard(self):
        df_calc = self.filtered_df.copy()
        df_calc['Total Amount'] = pd.to_numeric(df_calc['Total Amount'], errors='coerce').fillna(0)
        df_calc['Quantity'] = pd.to_numeric(df_calc['Quantity'], errors='coerce').fillna(0)
        df_calc['Lapped Days'] = pd.to_numeric(df_calc['Lapped Days'], errors='coerce').fillna(0)

        tot_rev = df_calc['Total Amount'].sum()
        tot_qty = df_calc['Quantity'].sum()
        tot_inv = df_calc['Invoice No.'].nunique()
        valid_lapped = df_calc[df_calc['Lapped Days'] > 0]
        avg_days = valid_lapped['Lapped Days'].mean() if not valid_lapped.empty else 0

        self.lbl_tot_rev.setText(f"Total Revenue\n₹ {tot_rev:,.2f}")
        self.lbl_tot_qty.setText(f"Total Quantity\n{tot_qty:,.0f}")
        self.lbl_invoices.setText(f"Total Invoices\n{tot_inv}")
        self.lbl_avg_days.setText(f"Avg Lapped Days\n{avg_days:.1f} Days")

        # Top Buyers
        self.buyer_table.setRowCount(0)
        if not df_calc.empty:
            top_buyers = df_calc.groupby('Buyer (Bill to)').agg({'Total Amount': 'sum', 'Quantity': 'sum'}).reset_index()
            top_buyers = top_buyers.sort_values(by='Total Amount', ascending=False).head(5)
            self.buyer_table.setRowCount(len(top_buyers))
            for i, (_, row) in enumerate(top_buyers.iterrows()):
                self.buyer_table.setItem(i, 0, QTableWidgetItem(str(row['Buyer (Bill to)'])))
                self.buyer_table.setItem(i, 1, QTableWidgetItem(f"₹ {row['Total Amount']:,.2f}"))
                self.buyer_table.setItem(i, 2, QTableWidgetItem(f"{row['Quantity']:,.0f}"))

        # Top Products
        self.prod_table.setRowCount(0)
        if not df_calc.empty:
            top_prods = df_calc.groupby('Description of Goods').agg({'Total Amount': 'sum', 'Quantity': 'sum'}).reset_index()
            top_prods = top_prods.sort_values(by='Total Amount', ascending=False).head(5)
            self.prod_table.setRowCount(len(top_prods))
            for i, (_, row) in enumerate(top_prods.iterrows()):
                self.prod_table.setItem(i, 0, QTableWidgetItem(str(row['Description of Goods'])))
                self.prod_table.setItem(i, 1, QTableWidgetItem(f"₹ {row['Total Amount']:,.2f}"))
                self.prod_table.setItem(i, 2, QTableWidgetItem(f"{row['Quantity']:,.0f}"))

    def update_trends(self):
        self.ax.clear()
        df_plot = self.filtered_df.copy()
        df_plot['Delivery Date'] = pd.to_datetime(df_plot['Delivery Date'], errors='coerce')
        df_plot = df_plot.dropna(subset=['Delivery Date'])
        
        if df_plot.empty:
            self.ax.text(0.5, 0.5, "No Data Available", ha='center', va='center', fontsize=12)
            self.canvas.draw()
            return

        metric = self.trend_metric.currentText()
        group_by = self.trend_group.currentText()
        freq_choice = self.trend_freq.currentText()
        freq_map = {"Daily": "D", "Weekly": "W", "Monthly": "MS"}
        freq = freq_map.get(freq_choice, "MS")

        val_col = 'Total Amount' if metric == "Total Revenue" else ('Quantity' if metric == "Total Quantity" else 'Lapped Days')
        agg_func = 'mean' if metric == "Avg Lapped Days" else 'sum'

        df_plot.set_index('Delivery Date', inplace=True)
        try:
            if group_by == "Overall":
                trend_data = df_plot[val_col].resample(freq).agg(agg_func)
                trend_data.plot(ax=self.ax, marker='o', linestyle='-', linewidth=2, color='dodgerblue')
                self.ax.set_title(f"Overall {metric} ({freq_choice})")
            else:
                group_col = 'Buyer (Bill to)' if group_by == "Buyer" else 'Description of Goods'
                top_5 = df_plot.groupby(group_col)[val_col].agg(agg_func).nlargest(5).index
                df_top = df_plot[df_plot[group_col].isin(top_5)]
                pivot = pd.pivot_table(df_top, values=val_col, index=df_top.index, columns=group_col, aggfunc=agg_func)
                trend_data = pivot.resample(freq).agg(agg_func)
                trend_data.plot(ax=self.ax, marker='o', linestyle='-', linewidth=2)
                self.ax.set_title(f"Top 5 {group_by}s by {metric} ({freq_choice})")
                self.ax.legend(title=group_col, bbox_to_anchor=(1.01, 1), loc='upper left', fontsize=8)

            self.ax.grid(True, linestyle='--', alpha=0.7)
            if metric == "Total Revenue":
                self.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: f"₹{x:,.0f}"))
            self.fig.tight_layout()
            self.canvas.draw()
        except Exception as e:
            print(f"Plotting error: {e}")
            self.ax.text(0.5, 0.5, "Insufficient data for trend.", ha='center', va='center')
            self.canvas.draw()

    def add_record(self):
        self.open_record_form()

    def edit_selected_record(self):
        items = self.table.selectedItems()
        if not items: return
        idx = items[0].data(Qt.UserRole)
        self.open_record_form(idx)

    def open_record_form(self, index=None):
        from PySide6.QtWidgets import QDialog
        dlg = QDialog(self)
        dlg.setWindowTitle("Record Details")
        dlg.resize(400, 600)
        layout = QVBoxLayout(dlg)
        form = QFormLayout()
        
        widgets = {}
        for col in COLUMNS:
            if col == "Lapped Days": continue
            if col in DATE_COLS:
                w = QDateEdit()
                w.setCalendarPopup(True)
                if index is not None:
                    dt = pd.to_datetime(self.df.at[index, col])
                    if pd.notnull(dt): w.setDate(QDate(dt.year, dt.month, dt.day))
                    else: w.setDate(QDate.currentDate())
                else:
                    w.setDate(QDate.currentDate())
            else:
                w = QLineEdit()
                if index is not None:
                    val = self.df.at[index, col]
                    if col in ["e-Way Bill No.", "HSN/SAC", "Sl No"] and pd.notnull(val):
                        try: val = str(int(float(val)))
                        except: pass
                    w.setText(str(val) if pd.notnull(val) else "")
            form.addRow(f"{col}:", w)
            widgets[col] = w
            
        layout.addLayout(form)
        
        save_btn = QPushButton("💾 Save Record")
        save_btn.clicked.connect(lambda: self.save_record(dlg, widgets, index))
        layout.addWidget(save_btn)
        dlg.exec()

    def save_record(self, dlg, widgets, index):
        try:
            new_data = {}
            for col, w in widgets.items():
                if isinstance(w, QDateEdit):
                    new_data[col] = w.date().toPython()
                else:
                    val = w.text().strip()
                    if col in NUMERIC_COLS:
                        new_data[col] = float(val.replace(',', '')) if val else 0
                    else:
                        new_data[col] = val
            
            if index is None:
                self.df = pd.concat([self.df, pd.DataFrame([new_data])], ignore_index=True)
            else:
                for col, val in new_data.items():
                    if self.df[col].dtype != 'object' and isinstance(val, str):
                        self.df[col] = self.df[col].astype(object)
                    self.df.at[index, col] = val
            
            self.calculate_lapped_days()
            self.df.to_excel(FILE_PATH, index=False)
            self.refresh_table()
            dlg.accept()
            QMessageBox.information(self, "Success", "Record saved.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Save failed: {e}")

    def delete_record(self):
        items = self.table.selectedItems()
        if not items: return
        if QMessageBox.question(self, "Delete", "Are you sure?") == QMessageBox.Yes:
            idx = items[0].data(Qt.UserRole)
            self.df = self.df.drop(idx).reset_index(drop=True)
            self.df.to_excel(FILE_PATH, index=False)
            self.refresh_table()

    def export_excel(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Excel", "", "Excel Files (*.xlsx)")
        if path:
            self.filtered_df.to_excel(path, index=False)
            QMessageBox.information(self, "Success", "Export complete.")

    def export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export PDF", "", "PDF Files (*.pdf)")
        if not path: return
        try:
            doc = SimpleDocTemplate(path, pagesize=landscape(A4))
            styles = getSampleStyleSheet()
            elements = []
            
            title = Paragraph("<b>Timely Delivery Report</b>", styles['Title'])
            elements.append(title); elements.append(Spacer(1, 10))
            
            export_cols = ["Buyer (Bill to)", "Description of Goods", "Quantity", "Per", "Order Date", "Despatched Date", "Delivery Date", "Lapped Days"]
            pdf_data = [export_cols]
            for _, row in self.filtered_df.iterrows():
                pdf_data.append([self.format_value(c, row[c]) for c in export_cols])
            
            table = Table(pdf_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.dodgerblue),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('FONTSIZE', (0,0), (-1,-1), 8),
            ]))
            elements.append(table)
            doc.build(elements)
            QMessageBox.information(self, "Success", "PDF generated.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"PDF Export failed: {e}")