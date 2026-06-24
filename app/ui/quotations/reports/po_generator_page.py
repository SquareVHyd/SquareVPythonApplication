import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QTextEdit, QFileDialog, QMessageBox, QSplitter, QDialog, QTextBrowser,
    QListWidget, QListWidgetItem, QFormLayout, QFrame, QGridLayout, QAbstractItemView, QSizePolicy
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QTextDocument, QPageSize
from PySide6.QtPrintSupport import QPrinter
from sqlalchemy import text
from app.config.database import get_session
from app.ui.searchable_table import SearchableTable

class MakeSelectionDialog(QDialog):
    def __init__(self, makes, selected_makes, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Makes")
        self.setMinimumWidth(300)
        self.setMinimumHeight(400)
        layout = QVBoxLayout(self)
        
        from PySide6.QtWidgets import QScrollArea, QCheckBox, QWidget, QLabel
        from PySide6.QtCore import Qt
        
        class CheckBoxRow(QWidget):
            def __init__(self, text, is_checked):
                super().__init__()
                self.text_val = text
                layout = QHBoxLayout(self)
                layout.setContentsMargins(10, 12, 10, 12)
                
                self.checkbox = QCheckBox(text)
                self.checkbox.setChecked(is_checked)
                self.checkbox.setStyleSheet("font-size: 14px; color: #1e293b;")
                # Make checkbox ignore clicks so the row handles it entirely
                self.checkbox.setAttribute(Qt.WA_TransparentForMouseEvents)
                
                layout.addWidget(self.checkbox)
                layout.addStretch()
                
                self.setCursor(Qt.PointingHandCursor)
                self.setStyleSheet("""
                    CheckBoxRow {
                        border-bottom: 1px solid #cbd5e1;
                        background-color: white;
                    }
                    CheckBoxRow:hover {
                        background-color: #f8fafc;
                    }
                """)
                
            def mouseReleaseEvent(self, event):
                if event.button() == Qt.LeftButton:
                    self.checkbox.setChecked(not self.checkbox.isChecked())
                    
            def is_checked(self):
                return self.checkbox.isChecked()
                
            def set_checked(self, state):
                self.checkbox.setChecked(state)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: 1px solid #cbd5e1; border-radius: 4px; }")
        
        self.scroll_widget = QWidget()
        self.scroll_widget.setStyleSheet("background-color: white;")
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setSpacing(0)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        
        self.rows = []
        for make in makes:
            row = CheckBoxRow(make, make in selected_makes)
            self.scroll_layout.addWidget(row)
            self.rows.append(row)
            
        self.scroll_layout.addStretch()
        self.scroll_area.setWidget(self.scroll_widget)
        layout.addWidget(self.scroll_area)
        
        btn_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("Select All")
        select_all_btn.setAutoDefault(False)
        select_all_btn.clicked.connect(self.select_all)
        btn_layout.addWidget(select_all_btn)
        
        clear_all_btn = QPushButton("Clear All")
        clear_all_btn.setAutoDefault(False)
        clear_all_btn.clicked.connect(self.clear_all)
        btn_layout.addWidget(clear_all_btn)
        
        btn_layout.addStretch()
        
        ok_btn = QPushButton("OK")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
        
    def select_all(self):
        for row in self.rows:
            row.set_checked(True)
            
    def clear_all(self):
        for row in self.rows:
            row.set_checked(False)
        
    def get_selected_makes(self):
        selected = []
        for row in self.rows:
            if row.is_checked():
                selected.append(row.text_val)
        return selected

class POPreviewDialog(QDialog):
    def __init__(self, html_content, parent=None):
        super().__init__(parent)
        self.html_content = html_content
        self.setWindowTitle("PO Preview")
        self.resize(900, 800)
        
        layout = QVBoxLayout(self)
        
        # Browser to render HTML
        self.browser = QTextBrowser()
        self.browser.setHtml(self.html_content)
        layout.addWidget(self.browser)
        
        # Bottom controls
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("📄 Save as PDF")
        save_btn.setStyleSheet("background-color: #2563eb; color: white; font-weight: bold; padding: 6px 16px; border-radius: 4px;")
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)

class PoGeneratorPage(QWidget):
    def __init__(self, parent_window=None):
        super().__init__()
        self.main_window = parent_window
        self.quote_id = None
        self.items_data = []
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # --- Top controls ---
        header = QHBoxLayout()
        self.title_label = QLabel("PO Generator")
        self.title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #0f172a;")
        header.addWidget(self.title_label)
        header.addStretch()
        
        header.addWidget(QLabel("<b>Filter by Make:</b>"))
        
        self.selected_makes = []
        self.all_makes = []
        
        self.make_btn = QPushButton("-- Select Makes --")
        self.make_btn.setMinimumWidth(200)
        self.make_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 4px 8px;
                background-color: white;
                border: 1px solid #94a3b8;
                border-radius: 3px;
                color: #0f172a;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
            }
        """)
        self.make_btn.clicked.connect(self.show_make_dialog)
        header.addWidget(self.make_btn)
        
        self.generate_btn = QPushButton("👁️ Preview & Save PDF")
        self.generate_btn.setStyleSheet("background-color: #2563eb; color: white; font-weight: bold; padding: 6px 16px; border-radius: 4px;")
        self.generate_btn.clicked.connect(self.preview_pdf)
        header.addWidget(self.generate_btn)
        
        layout.addLayout(header)
        
        header_title = QLabel("PO Header Details (Editable):")
        header_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #0f172a;")
        header_title.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        layout.addWidget(header_title)
        
        self.header_table = QTableWidget()
        self.header_table.setColumnCount(3)
        self.header_table.setRowCount(1)
        self.header_table.setHorizontalHeaderLabels(["Sender Details", "Recipient Details", "Introductory Text"])
        self.header_table.verticalHeader().setVisible(False)
        self.header_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.header_table.setFocusPolicy(Qt.NoFocus)
        self.header_table.setStyleSheet(
            "QTableWidget { gridline-color: #cbd5e1; border: 1px solid #94a3b8; background-color: white; }"
            "QHeaderView::section { background-color: #f1f5f9; padding: 6px; border: 1px solid #cbd5e1; font-weight: bold; color: #334155; text-align: center; }"
            "QTextEdit, QLineEdit { border: none; background-color: transparent; padding: 4px; }"
            "QTextEdit:focus, QLineEdit:focus { background-color: #f8fafc; }"
        )
        self.header_table.setRowHeight(0, 100)
        self.header_table.setMaximumHeight(140)
        
        # Configure column widths (evenly stretched)
        header_view = self.header_table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.Stretch)
        header_view.setSectionResizeMode(1, QHeaderView.Stretch)
        header_view.setSectionResizeMode(2, QHeaderView.Stretch)
        
        # Sender Details
        self.sender_edit = QTextEdit()
        self.sender_edit.setPlainText("National Engineering Enterprises\n#303,3rd floor, Adinath Sqare,\n5-3-404 TO 411,Hyderbasthi,\nnear Gujarati High School Lane,\nR.P Road,Secunderabad -500 003")
        self.header_table.setCellWidget(0, 0, self.sender_edit)
        
        # Recipient Details
        self.rec_edit = QTextEdit()
        self.rec_edit.setPlainText("Square V Engineering Enterprises\nGROUND FLOOR, Road No .14\nSurvey No:298(P), Pipe Line Road,\nPhase-I, IDA, Jeedimetla,\nHyderabad - 500055, Telangana, India\nEmail: info.squarev@gmail.com\nExport: IEC:AFKFS1080B ,State Code: 36\nGSTIN : 36AFKFS1080B1Z7")
        self.header_table.setCellWidget(0, 1, self.rec_edit)
        
        def wrap_top(widget):
            w = QWidget()
            l = QVBoxLayout(w)
            l.setContentsMargins(0, 0, 0, 0)
            l.addWidget(widget, 0, Qt.AlignTop)
            return w
            
        # Introductory Text
        self.intro_edit = QLineEdit()
        self.intro_edit.setText("We are please to award purchase order for supply of Terminals as per mentioned below")
        self.header_table.setCellWidget(0, 2, wrap_top(self.intro_edit))
        
        layout.addWidget(self.header_table)
        
        # Bottom Details (Date and Ref)
        bottom_details_layout = QHBoxLayout()
        bottom_details_layout.setSpacing(20)
        
        date_layout = QHBoxLayout()
        lbl_date = QLabel("Date:")
        lbl_date.setStyleSheet("border: none; font-weight: bold; color: #334155;")
        self.date_edit = QLineEdit()
        self.date_edit.setText(QDate.currentDate().toString("dd/MM/yyyy"))
        self.date_edit.setMaximumWidth(150)
        date_layout.addWidget(lbl_date)
        date_layout.addWidget(self.date_edit)
        
        ref_layout = QHBoxLayout()
        lbl_ref = QLabel("Ref No:")
        lbl_ref.setStyleSheet("border: none; font-weight: bold; color: #334155;")
        self.ref_edit = QLineEdit()
        self.ref_edit.setText("SVEE05 -2026-27")
        self.ref_edit.setMaximumWidth(200)
        ref_layout.addWidget(lbl_ref)
        ref_layout.addWidget(self.ref_edit)
        
        bottom_details_layout.addLayout(date_layout)
        bottom_details_layout.addLayout(ref_layout)
        bottom_details_layout.addStretch()
        
        layout.addLayout(bottom_details_layout)
        
        self.table = SearchableTable()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["#", "Description", "Qty", "Unit price", "Price", "Discount %", "Total"])
        self.table.itemChanged.connect(self.calculate_row_totals)
        
        # Make the table resize nicely like the steel specification table
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        
        # --- Calculation Block (Totals at bottom) ---
        calc_frame = QFrame()
        calc_frame.setStyleSheet("QFrame { background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 6px; }")
        calc_layout = QHBoxLayout(calc_frame)
        calc_layout.setContentsMargins(15, 10, 15, 10)
        
        self.lbl_subtotal = QLabel("Sub-total: ₹0.00")
        self.lbl_subtotal.setStyleSheet("border: none; background: transparent; font-weight: bold; color: #334155; font-size: 13px;")
        
        self.lbl_gst = QLabel("GST 18%: ₹0.00")
        self.lbl_gst.setStyleSheet("border: none; background: transparent; font-weight: bold; color: #334155; font-size: 13px;")
        
        self.lbl_grand_total = QLabel("Grand Total: ₹0.00")
        self.lbl_grand_total.setStyleSheet("border: none; background: transparent; font-weight: bold; color: #dc2626; font-size: 13px;")
        
        lbl_summary = QLabel("PO Total Summary:")
        lbl_summary.setStyleSheet("border: none; background: transparent; font-weight: bold; color: #0f172a; font-size: 13px;")
        calc_layout.addWidget(lbl_summary)
        calc_layout.addStretch()
        
        def sep():
            lbl = QLabel(" | ")
            lbl.setStyleSheet("border: none; background: transparent; color: #94a3b8;")
            return lbl
        
        calc_layout.addWidget(self.lbl_subtotal)
        calc_layout.addWidget(sep())
        calc_layout.addWidget(self.lbl_gst)
        calc_layout.addWidget(sep())
        calc_layout.addWidget(self.lbl_grand_total)
        
        # Add calc frame to the layout
        layout.addWidget(calc_frame)

    def load_quotation(self, quote_id):
        self.quote_id = quote_id
        self.items_data = []
        
        sql = text("""
            SELECT 
                0 as "ID",
                mi."DriveDescription",
                SUM(
                    COALESCE(p."PanelQty", 1) * 
                    COALESCE(pm."PanelModQty", 1) *
                    CASE 
                        WHEN mi."BOM" IS NOT NULL AND mi."BOM" <> 0 THEN mi."BOM" 
                        ELSE 1
                    END
                ) as "TotalBOM",
                MAX(mi."LP") as "LP",
                MAX(mi."%Discount") as "Discount",
                MAX(pl."Make") as "Make",
                MAX(pl."Model") as "Model"
            FROM public."tbl_Panels" p
            JOIN public."tbl_PanelModules" pm ON p."ID" = pm."PanelID"
            JOIN public."tbl_ModuleItems" mi ON pm."ModuleTypeID" = mi."ID"
            LEFT JOIN public."vwPriceList" pl ON mi."DriveDescription" = pl."ItemDescription"
            WHERE p."QuoteID" = :tid
            GROUP BY mi."DriveDescription"
            ORDER BY mi."DriveDescription"
        """)
        
        try:
            with get_session() as session:
                rows = session.execute(sql, {"tid": self.quote_id}).fetchall()
                # Store as list of tuples (mt_id, desc, bom, lp, disc, make, model)
                self.items_data = rows
                
            self.populate_makes()
            self.apply_filter()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load items for PO Generator: {e}")

    def populate_makes(self):
        makes = set()
        for row in self.items_data:
            make = str(row[5] or "").strip()
            if make:
                makes.add(make)
                
        self.all_makes = sorted(list(makes))
        self.selected_makes = []
        self.make_btn.setText("-- Select Makes --")

    def show_make_dialog(self):
        if not self.all_makes:
            QMessageBox.information(self, "Info", "No makes available for this quotation.")
            return
            
        dialog = MakeSelectionDialog(self.all_makes, self.selected_makes, self)
        if dialog.exec() == QDialog.Accepted:
            self.selected_makes = dialog.get_selected_makes()
            if not self.selected_makes:
                self.make_btn.setText("-- Select Makes --")
            elif len(self.selected_makes) == 1:
                self.make_btn.setText(self.selected_makes[0])
            else:
                self.make_btn.setText(f"{len(self.selected_makes)} Makes Selected")
            self.apply_filter()

    def apply_filter(self):
        self.generate_btn.setEnabled(bool(self.selected_makes))
        
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        
        if not self.selected_makes:
            self.table.blockSignals(False)
            self.lbl_subtotal.setText("Sub-total: ₹0.00")
            self.lbl_gst.setText("GST 18%: ₹0.00")
            self.lbl_grand_total.setText("Grand Total: ₹0.00")
            return
            
        filtered_items = [r for r in self.items_data if str(r[5] or "").strip() in self.selected_makes]
        
        self.table.setRowCount(len(filtered_items))
        for r, row in enumerate(filtered_items):
            mt_id, desc, bom, lp, disc, make, model = row
            
            # Formulate the description cell
            desc_text = desc
            if make: desc_text += f"\nMake: {make}"
            if model: desc_text += f"\nModel No:{model}"
            
            bom_val = float(bom or 0)
            lp_val = float(lp or 0)
            disc_val = float(disc or 0)
            price = bom_val * lp_val
            total = price * (1 - disc_val)
            
            # Col 0: #
            idx_item = QTableWidgetItem(str(r+1))
            idx_item.setFlags(idx_item.flags() & ~Qt.ItemIsEditable)
            idx_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, 0, idx_item)
            
            # Col 1: Description
            desc_item = QTableWidgetItem(desc_text)
            self.table.setItem(r, 1, desc_item)
            
            # Col 2: Qty
            qty_item = QTableWidgetItem(f"{bom_val:.0f}" if bom_val.is_integer() else f"{bom_val:.2f}")
            qty_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, 2, qty_item)
            
            # Col 3: Unit Price
            up_item = QTableWidgetItem(f"{lp_val:.2f}")
            up_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(r, 3, up_item)
            
            # Col 4: Price (Read-only initially)
            price_item = QTableWidgetItem(f"{price:,.2f}")
            price_item.setFlags(price_item.flags() & ~Qt.ItemIsEditable)
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(r, 4, price_item)
            
            # Col 5: Discount
            disc_item = QTableWidgetItem(f"{disc_val * 100:.2f}")
            disc_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, 5, disc_item)
            
            # Col 6: Total (Read-only initially)
            total_item = QTableWidgetItem(f"{total:,.2f}")
            total_item.setFlags(total_item.flags() & ~Qt.ItemIsEditable)
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(r, 6, total_item)
            
        self.table.resizeRowsToContents()
        self.table.blockSignals(False)
        self.calculate_row_totals(None)

    def calculate_row_totals(self, item):
        if item and item.column() not in (2, 3, 5):
            return
            
        self.table.blockSignals(True)
        subtotal = 0.0
        
        def safe_float(val):
            try: return float(val.replace(',', ''))
            except: return 0.0

        for r in range(self.table.rowCount()):
            qty = safe_float(self.table.item(r, 2).text())
            unit_price = safe_float(self.table.item(r, 3).text())
            disc_pct = safe_float(self.table.item(r, 5).text()) / 100.0
            
            price = qty * unit_price
            total = price * (1 - disc_pct)
            
            self.table.item(r, 4).setText(f"{price:,.2f}")
            self.table.item(r, 6).setText(f"{total:,.2f}")
            subtotal += total
            
        self.subtotal_val = subtotal
        self.gst_val = subtotal * 0.18
        self.grand_total_val = subtotal + self.gst_val
        
        self.lbl_subtotal.setText(f"Sub-total: ₹{self.subtotal_val:,.2f}")
        self.lbl_gst.setText(f"GST 18%: ₹{self.gst_val:,.2f}")
        self.lbl_grand_total.setText(f"Grand Total: ₹{self.grand_total_val:,.2f}")
        
        self.table.blockSignals(False)

    def preview_pdf(self):
        # Collect table data
        rows_html = ""
        for r in range(self.table.rowCount()):
            desc = self.table.item(r, 1).text().replace('\n', '<br>')
            qty = self.table.item(r, 2).text()
            uprice = self.table.item(r, 3).text()
            price = self.table.item(r, 4).text()
            disc = self.table.item(r, 5).text() + " %"
            total = self.table.item(r, 6).text()
            
            rows_html += f"""
            <tr>
            <td class="center">{r+1}</td>
            <td class="description">{desc}</td>
            <td class="center">{qty}</td>
            <td class="right">{uprice}</td>
            <td class="right">{price}</td>
            <td class="center">{disc}</td>
            <td class="right">{total}</td>
            </tr>
            """
            
        sender_html = self.sender_edit.toPlainText().replace('\n', '<br>')
        rec_html = self.rec_edit.toPlainText().replace('\n', '<br>')
        
        logo_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Images", "SQV_Header.png")).replace("\\", "/")
        logo_url = f"file:///{logo_path}"
        
        # We need to construct the sender block from sender_html
        sender_parts = sender_html.split('<br>')
        sender_bold = sender_parts[0] if sender_parts else ''
        sender_rest = '<br>'.join(sender_parts[1:]) if len(sender_parts) > 1 else ''

        # Construct recipient block
        rec_parts = rec_html.split('<br>')
        rec_bold = rec_parts[0] if rec_parts else ''
        rec_rest = '<br>'.join(rec_parts[1:]) if len(rec_parts) > 1 else ''
        
        subtotal_str = f"₹ {self.subtotal_val:,.2f}"
        gst_str = f"₹ {self.gst_val:,.2f}"
        grand_total_str = f"₹ {self.grand_total_val:,.2f}"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8">
        <title>Purchase Order</title>
        <style>
        body{{
            font-family: Arial, sans-serif;
            background:white;
        }}
        .page{{
            width: 100%;
            margin:auto;
            background:white;
        }}
        h1{{
            margin:0 0 20px 0;
            font-size:26pt;
            display: inline-block;
        }}
        .block{{
            line-height:1.5;
            font-size:6pt;
        }}
        .middle{{
            text-align:center;
            font-size:6pt;
        }}
        .bold{{
            font-weight:bold;
        }}
        .note{{
            margin:20px 0;
            font-size:6pt;
            font-weight:bold;
        }}
        table.items{{
            width:100%;
            background-color: black;
            font-size:6pt;
        }}
        .items th, .items td {{
            background-color: white;
        }}
        .items th{{
            padding:8px;
            text-align:center;
        }}
        .items td{{
            padding:6px;
            vertical-align:top;
        }}
        .center{{
            text-align:center;
        }}
        .right{{
            text-align:right;
            white-space:nowrap;
        }}
        .description{{
            line-height:1.5;
        }}
        .grand{{
            font-size:11pt;
            font-weight:bold;
        }}
        </style>
        </head>
        <body>
        <div class="page">
        
        <table style="margin-bottom: 20px; border: none; width: 100%;" cellspacing="0" cellpadding="0">
            <tr>
                <td style="border: none; padding-right: 15px; vertical-align: top; width: 50px;">
                    <img src="{logo_url}" height="35">
                </td>
                <td style="border: none; vertical-align: top;">
                    <h1 style="margin: 0; padding: 0;">Purchase Order</h1>
                </td>
            </tr>
        </table>
        
        <div class="header" style="width: 100%; margin-bottom: 30px;">
            <table style="width: 100%; border: none;" cellspacing="0" cellpadding="0">
                <tr>
                    <td style="width: 50%; vertical-align: top; border: none; font-size: 6pt; line-height: 1.5; padding-right: 20px;" class="block">
                        <div style="font-weight: bold; margin-bottom: 2px;">Date Issued: {self.date_edit.text()}</div>
                        <div style="font-weight: bold; margin-bottom: 10px;">Reference: {self.ref_edit.text()}</div>
                        <div class="bold" style="font-weight: bold;">{sender_bold}</div>
                        {sender_rest}
                    </td>
                    <td style="width: 50%; vertical-align: top; border: none; font-size: 6pt; line-height: 1.5; padding-left: 20px;" class="block">
                        <div class="bold" style="font-weight: bold;">{rec_bold}</div>
                        {rec_rest}
                    </td>
                </tr>
            </table>
        </div>
        
        <div class="note">
        {self.intro_edit.text()}
        </div>
        
        <table class="items" cellspacing="1" cellpadding="0">
        <thead>
        <tr>
        <th width="5%">#</th>
        <th width="43%">Description</th>
        <th width="8%">Qty</th>
        <th width="10%">Unit price</th>
        <th width="12%">Price</th>
        <th width="10%">Discount</th>
        <th width="12%">Total</th>
        </tr>
        </thead>
        <tbody>
        {rows_html}
        </tbody>
        </table>
        
        <div style="height: 15px;"></div>
        
        <table style="width: 300px; float: right; border-collapse: collapse; font-size: 6pt; font-weight: bold;">
        <tr>
            <td style="padding: 8px; border: 1px solid black;">Sub-total</td>
            <td class="right" style="padding: 8px; border: 1px solid black;">{subtotal_str}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid black;">GST 18%</td>
            <td class="right" style="padding: 8px; border: 1px solid black;">{gst_str}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid black;">Grand Total</td>
            <td class="right" style="padding: 8px; border: 1px solid black;">{grand_total_str}</td>
        </tr>
        </table>
        
        <div style="clear:both"></div>
        </div>
        </body>
        </html>
        """
        
        dialog = POPreviewDialog(html, self)
        if dialog.exec() == QDialog.Accepted:
            self.save_pdf(html)
            
    def save_pdf(self, html):
        makes_str = "_".join(self.selected_makes)
        if len(makes_str) > 30:
            makes_str = "Multiple_Makes"
        elif not makes_str:
            makes_str = "Unknown_Make"
            
        filename, _ = QFileDialog.getSaveFileName(self, "Save Purchase Order", f"PO_{makes_str}.pdf", "PDF Files (*.pdf)")
        if not filename: return
        
        if os.path.exists(filename):
            try:
                with open(filename, 'a'): pass
            except PermissionError:
                QMessageBox.critical(self, "File in Use", f"Cannot save PDF.\n\nThe file '{os.path.basename(filename)}' is likely open in another program (like Adobe Reader, Chrome, or Edge). Please close it and try saving again.")
                return
                
        try:
            printer = QPrinter(QPrinter.ScreenResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(filename)
            printer.setPageSize(QPageSize(QPageSize.A4))
            
            from PySide6.QtCore import QMarginsF
            from PySide6.QtGui import QPageLayout
            printer.setPageMargins(QMarginsF(15, 15, 15, 15), QPageLayout.Millimeter)
            
            doc = QTextDocument()
            doc.setHtml(html)
            
            # Ensure document layout uses printer dimensions
            doc.setPageSize(printer.pageRect(QPrinter.DevicePixel).size())
            
            doc.print_(printer)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save PDF file:\n{str(e)}")
