from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QLabel,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
    QAbstractItemView,
    QFileDialog,
    QTextEdit,
    QMenu,
)


from PySide6.QtCore import Qt
from app.ui.customers.customer_contacts_dialog import (
    CustomerContactsDialog
)
from PySide6.QtGui import QShortcut, QKeySequence, QTextDocument, QPageSize
from PySide6.QtPrintSupport import QPrinter, QPrintPreviewDialog

from PySide6.QtCore import Qt, QTimer

from app.services.customer_service import CustomerService
from app.services.excel_service import ExcelService
from app.services.state_service import StateService
from app.ui.customers.customer_form import CustomerForm
from app.ui.searchable_table import NumericTableWidgetItem, SearchableTable
from app.utils.worker_thread import Worker
from app.config.ui_state import UIStateManager


class CustomerPage(QWidget):
    def __init__(self):
        super().__init__()

        self.service = CustomerService()
        self.state_service = StateService()
        self._customer_cache = []
        self._state_cache = {}
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._perform_search)
        self._worker = None

        self.setup_ui()
        self._restore_state()
        # Load data asynchronously on startup
        self._load_customers_async()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)

        header_layout = QHBoxLayout()
        title = QLabel("Customers")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search customers...")
        self.search_box.returnPressed.connect(self._perform_search)
        self.search_box.textChanged.connect(self._debounce_search)

        self.search_shortcut = QShortcut(QKeySequence.Find, self)
        self.search_shortcut.activated.connect(self.focus_search)

        self.refresh_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        self.refresh_shortcut.activated.connect(self.refresh_table)
        self.add_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        self.add_shortcut.activated.connect(self.add_customer)
        self.edit_shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        self.edit_shortcut.activated.connect(self.edit_customer)
        self.delete_shortcut = QShortcut(QKeySequence.Delete, self)
        self.delete_shortcut.activated.connect(self.delete_customer)
        self.save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        self.save_shortcut.activated.connect(self.save_table_as_excel)
        self.print_shortcut = QShortcut(QKeySequence("Ctrl+P"), self)
        self.print_shortcut.activated.connect(self.save_table_as_pdf)
        self.select_row_shortcut = QShortcut(QKeySequence("Ctrl+Space"), self)
        self.select_row_shortcut.activated.connect(self.select_current_row)
        self.select_col_shortcut = QShortcut(QKeySequence("Ctrl+L"), self)
        self.select_col_shortcut.activated.connect(self.select_current_column)
        self.move_row_down_shortcut = QShortcut(QKeySequence("Ctrl+Down"), self)
        self.move_row_down_shortcut.activated.connect(lambda: self.move_selection(1, 0))
        self.move_row_up_shortcut = QShortcut(QKeySequence("Ctrl+Up"), self)
        self.move_row_up_shortcut.activated.connect(lambda: self.move_selection(-1, 0))
        self.move_col_right_shortcut = QShortcut(QKeySequence("Ctrl+Right"), self)
        self.move_col_right_shortcut.activated.connect(lambda: self.move_selection(0, 1))
        self.move_col_left_shortcut = QShortcut(QKeySequence("Ctrl+Left"), self)
        self.move_col_left_shortcut.activated.connect(lambda: self.move_selection(0, -1))
        self.help_shortcut = QShortcut(QKeySequence("F1"), self)
        self.help_shortcut.activated.connect(self.show_shortcuts)
        self.help_shortcut2 = QShortcut(QKeySequence("Ctrl+H"), self)
        self.help_shortcut2.activated.connect(self.show_shortcuts)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_table)

        self.add_btn = QPushButton("Add")
        self.add_btn.clicked.connect(self.add_customer)

        self.edit_btn = QPushButton("Edit")
        self.edit_btn.clicked.connect(self.edit_customer)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_customer)

        self.save_as_btn = QPushButton("Save As")
        save_menu = QMenu(self.save_as_btn)
        save_menu.addAction("Excel", self.save_table_as_excel)
        save_menu.addAction("PDF", self.save_table_as_pdf)
        self.save_as_btn.setMenu(save_menu)

        # Quotations button removed

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.search_box)
        header_layout.addWidget(self.refresh_btn)
        header_layout.addWidget(self.add_btn)
        header_layout.addWidget(self.edit_btn)
        header_layout.addWidget(self.delete_btn)
        header_layout.addWidget(self.save_as_btn)

        self.layout.addLayout(header_layout)

        self.table = SearchableTable()
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(True)
        self.table.setGridStyle(Qt.SolidLine)
        self.table.setStyleSheet("""
            QTableWidget { gridline-color: #e2e8f0; }
            QHeaderView::section { background-color: #f8fafc; padding: 6px; font-weight: bold; border: 1px solid #e2e8f0; }
        """)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(
            self.open_customer_context_menu
        )
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID",
            "Name",
            "Mail",
            "Phone",
            "City",
            "State"
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSortingEnabled(True)
        # Enable movable columns and rows
        self.table.horizontalHeader().setSectionsMovable(True)
        self.table.verticalHeader().setSectionsMovable(True)
        self.table.verticalHeader().setVisible(True) # Set visible to allow dragging

        self.layout.addWidget(self.table)

    def load_customers(self):
        """Load customers (called after add/edit/delete operations)."""
        self._load_customers_async()

    def _reload_customers(self):
        customers, _ = self.service.get_all_customers()
        self._customer_cache = list(customers)
        
        # Batch load all states upfront to avoid individual lookups
        unique_state_ids = set(row[6] for row in self._customer_cache if row[6])
        self._state_cache = {}
        for state_id in unique_state_ids:
            state = self.state_service.get_state(state_id)
            name = str(state[2] or "") if state else ""
            self._state_cache[state_id] = name
        
        self._render_customers(self._customer_cache)

    def _render_customers(self, rows):
        # Disable sorting and signals during update for performance
        self.table.setSortingEnabled(False)
        self.table.blockSignals(True)
        
        try:
            self.table.setRowCount(len(rows))
            
            for index, row in enumerate(rows):
                customer_state = self._get_state_name(row[6]) if row[6] else ""
                
                values = [
                    row[0],
                    row[1],
                    row[2],
                    row[3],
                    row[5],
                    customer_state,
                ]
                
                for column, value in enumerate(values):
                    self.table.setItem(index, column, NumericTableWidgetItem(value or ""))
        finally:
            # Re-enable signals and sorting
            self.table.blockSignals(False)
            self.table.setSortingEnabled(True)

    def _get_state_name(self, state_id):
        if state_id in self._state_cache:
            return self._state_cache[state_id]

        state = self.state_service.get_state(state_id)
        name = str(state[2] or "") if state else ""
        self._state_cache[state_id] = name
        return name

    def _debounce_search(self):
        """Debounce search input to avoid excessive re-rendering (300ms delay)."""
        self._search_timer.stop()
        self._search_timer.start(300)
    
    def _perform_search(self):
        """Execute the actual search operation."""
        keyword = self.search_box.text().strip().lower()
        if not keyword:
            self._render_customers(self._customer_cache)
            return

        rows = []
        for row in self._customer_cache:
            state_name = self._get_state_name(row[6]) if row[6] else ""
            search_text = " ".join([
                str(row[0] or ""),
                str(row[1] or ""),
                str(row[2] or ""),
                str(row[3] or ""),
                str(row[5] or ""),
                state_name,
            ]).lower()
            if keyword in search_text:
                rows.append(row)

        self._render_customers(rows)
    
    def search_customers(self):
        """Alias for backward compatibility."""
        self._perform_search()

    def _load_customers_async(self):
        """Load customers asynchronously in background thread."""
        if self._worker is not None:
            return  # Already loading
        
        self._worker = Worker(self._load_customers_sync)
        self._worker.result.connect(self._on_customers_loaded)
        self._worker.error.connect(self._on_load_error)
        self._worker.start()
    
    def _load_customers_sync(self):
        """Synchronous customer loading (runs in worker thread)."""
        customers, _ = self.service.get_all_customers()
        return list(customers)
    
    def _on_customers_loaded(self, customers):
        """Handle loaded customers result."""
        self._customer_cache = customers
        
        # Batch load all states upfront
        unique_state_ids = set(row[6] for row in self._customer_cache if row[6])
        self._state_cache = {}
        for state_id in unique_state_ids:
            state = self.state_service.get_state(state_id)
            name = str(state[2] or "") if state else ""
            self._state_cache[state_id] = name
        
        self._render_customers(self._customer_cache)
        self._restore_state()
        self._worker = None
    
    def _on_load_error(self, error_msg):
        """Handle load error."""
        QMessageBox.critical(self, "Load Error", f"Failed to load customers: {error_msg}")
        self._worker = None
    
    def _restore_state(self):
        """Restore customer page state from saved settings."""
        state = UIStateManager.get_customer_page_state()
        if state.get("search_text"):
            self.search_box.blockSignals(True)
            self.search_box.setText(state["search_text"])
            self.search_box.blockSignals(False)
            self._perform_search()

        if state.get("header_state"):
            self.table.horizontalHeader().restoreState(state["header_state"])

        if state.get("v_header_state"):
            self.table.verticalHeader().restoreState(state["v_header_state"])

    
    def _save_state(self):
        """Save customer page state to persistent storage."""
        if not hasattr(UIStateManager, 'save_customer_page_state'):
            return
            
        header_state = self.table.horizontalHeader().saveState()
        v_header_state = self.table.verticalHeader().saveState()
        scroll_pos = self.table.verticalScrollBar().value()
        search_text = self.search_box.text()
        
        UIStateManager.save_customer_page_state({
            "header_state": header_state,
            "v_header_state": v_header_state,
            "scroll_position": scroll_pos,
            "search_text": search_text
        })

    def get_selected_customer(self):
        selected = self.table.selectedItems()
        if not selected:
            return None

        row = selected[0].row()
        customer_id = int(self.table.item(row, 0).text())
        return self.service.get_customer(customer_id)

    def focus_search(self):
        self.search_box.setFocus()

    def move_selection(self, row_delta=0, col_delta=0):
        if self.table.rowCount() == 0 or self.table.columnCount() == 0:
            return

        current = self.table.currentItem()
        row = current.row() if current else 0
        col = current.column() if current else 0

        row = max(0, min(self.table.rowCount() - 1, row + row_delta))
        col = max(0, min(self.table.columnCount() - 1, col + col_delta))

        self.table.setCurrentCell(row, col)
        self.table.scrollToItem(self.table.currentItem())

    def select_current_row(self):
        if self.table.rowCount() == 0:
            return

        current = self.table.currentItem() or self.table.item(0, 0)
        if current:
            self.table.selectRow(current.row())
            self.table.setCurrentCell(current.row(), current.column())

    def select_current_column(self):
        if self.table.columnCount() == 0:
            return

        current = self.table.currentItem() or self.table.item(0, 0)
        if current:
            self.table.selectColumn(current.column())
            self.table.setCurrentCell(current.row(), current.column())

    def show_shortcuts(self):
        shortcuts = (
            "Keyboard Shortcuts:\n"
            "F1 / Ctrl+H - Open shortcuts help\n"
            "Ctrl+F - Focus search box\n"
            "Ctrl+R - Refresh customer list\n"
            "Ctrl+N - Add customer\n"
            "Ctrl+E - Edit selected customer\n"
            "Delete - Delete selected customer\n"
            "Ctrl+S - Export customers to Excel\n"
            "Ctrl+P - Export customers to PDF\n"
            "Ctrl+Down / Ctrl+Up - Move row selection\n"
            "Ctrl+Right / Ctrl+Left - Move column selection\n"
            "Ctrl+Space - Select current row\n"
            "Ctrl+L - Select current column\n"
        )
        QMessageBox.information(self, "Keyboard Shortcuts", shortcuts)

    def refresh_table(self):
        self._save_state()  # Save current state before refresh
        
        self.search_box.blockSignals(True)
        self.search_box.clear()
        self.search_box.blockSignals(False)
        
        # Cancel any pending search operation
        self._search_timer.stop()

        # Load customers asynchronously
        self._load_customers_async()
        self.table.clearSelection()
        self.table.scrollToTop()

    def reset_search(self):
        self.refresh_table()

    # Quotations/print functionality removed; PDF export remains via Save As -> PDF

    def save_table_as_excel(self):
        headers, rows = self.table.get_table_data()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Customers Table as Excel",
            "",
            "Excel Files (*.xlsx)",
        )
        if not file_path:
            return
        if not file_path.lower().endswith(".xlsx"):
            file_path += ".xlsx"

        try:
            ExcelService().export(headers, rows, file_path)
            QMessageBox.information(self, "Saved", f"Customers table saved to:\n{file_path}")
        except Exception as exc:
            QMessageBox.critical(self, "Save Error", f"Unable to save Excel file: {exc}")

    def save_table_as_pdf(self):
        html = self.table.to_html("Customers Table")
        self.preview_and_save_pdf(html, "Save Customers Table as PDF")

    def build_customer_request_letter(self, values):
        from datetime import datetime
        today = datetime.now().strftime("%d/%m/%Y")
        return (
            "MATERIALS REQUEST LETTER\n"
            "=====================================================\n\n"
            "Date: " + today + "\n\n"
            "TO: Supply Chain Management\n"
            "FROM: Customer Service Department\n\n"
            "RE: Customer Materials Request\n\n"
            f"Customer ID: {values['ID']}\n"
            f"Customer Name: {values['Name']}\n"
            f"Email: {values['Mail']}\n"
            f"Phone: {values['Phone']}\n"
            f"City: {values['City']}\n"
            f"State: {values['State']}\n\n"
            "DESCRIPTION:\n"
            "Please process and deliver the following items for the above mentioned customer:"
            "\n\n"
            "1. \n"
            "2. \n"
            "3. \n\n"
            "TERMS:\n"
            "- Please confirm receipt of this request within 24 hours\n"
            "- Estimated delivery date: [Specify Date]\n"
            "- Contact person: [Name & Extension]\n\n"
            "This request is prioritized and requires immediate attention.\n\n"
            "Authorized By: Enterprise ERP System\n"
            "Department: Customer Service\n"
            "Date of Request: "+today+"\n\n"
            "---\n"
            "Enterprise ERP System\n"
            "All rights reserved © 2026"
        )

    def edit_request_letter(self, letter_text):
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Request Letter")
        dialog.setMinimumSize(700, 520)

        layout = QVBoxLayout(dialog)
        editor = QTextEdit(dialog)
        editor.setPlainText(letter_text)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        layout.addWidget(editor)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.Accepted:
            return editor.toPlainText()
        return None

    def build_print_html(self, title, body, values):
        from datetime import datetime

        today = datetime.now().strftime("%d %B %Y")
        formatted_body = body.replace("\n", "<br>")

        return f"""
        <html>
        <head>
            <meta charset="UTF-8">

            <style>

                @page {{
                    margin: 22mm 18mm 20mm 18mm;
                }}

                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    background-color: #eef2f7;
                    margin: 0;
                    padding: 25px;
                    color: #2d3748;
                }}

                .page {{
                    background: #ffffff;
                    border-radius: 14px;
                    overflow: hidden;
                    box-shadow: 0 6px 20px rgba(0,0,0,0.12);
                    border: 1px solid #dbe3ec;
                }}

                .header {{
                    background: linear-gradient(
                        135deg,
                        #0f172a 0%,
                        #1e3a8a 50%,
                        #2563eb 100%
                    );
                    color: white;
                    padding: 35px 45px;
                }}

                .header-top {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}

                .company-details h1 {{
                    margin: 0;
                    font-size: 30px;
                    font-weight: 700;
                    letter-spacing: 1px;
                }}

                .company-details p {{
                    margin-top: 8px;
                    font-size: 14px;
                    opacity: 0.9;
                }}

                .document-badge {{
                    background: rgba(255,255,255,0.15);
                    border: 1px solid rgba(255,255,255,0.3);
                    padding: 10px 18px;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: 600;
                    letter-spacing: 1px;
                }}

                .content {{
                    padding: 40px 45px;
                }}

                .date {{
                    text-align: right;
                    color: #64748b;
                    font-size: 13px;
                    margin-bottom: 25px;
                    font-weight: 500;
                }}

                .section-title {{
                    font-size: 17px;
                    font-weight: 700;
                    color: #1e3a8a;
                    margin-bottom: 15px;
                    border-bottom: 2px solid #dbeafe;
                    padding-bottom: 8px;
                }}

                .customer-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 35px;
                    border-radius: 10px;
                    overflow: hidden;
                    border: 1px solid #dbe3ec;
                }}

                .customer-table tr:nth-child(even) {{
                    background-color: #f8fafc;
                }}

                .customer-table td {{
                    padding: 14px 16px;
                    border-bottom: 1px solid #e2e8f0;
                    font-size: 14px;
                }}

                .customer-table .label {{
                    width: 30%;
                    background-color: #eff6ff;
                    color: #1e3a8a;
                    font-weight: 700;
                }}

                .customer-table .value {{
                    color: #334155;
                }}

                .letter-section {{
                    margin-top: 10px;
                }}

                .letter-body {{
                    background: #fcfcfd;
                    border: 1px solid #e5e7eb;
                    border-left: 5px solid #2563eb;
                    border-radius: 10px;
                    padding: 28px;
                    font-size: 14px;
                    line-height: 1.8;
                    color: #374151;
                    text-align: justify;
                    white-space: pre-wrap;
                }}

                .signature-area {{
                    margin-top: 60px;
                }}

                .signature-container {{
                    display: flex;
                    justify-content: space-between;
                    gap: 40px;
                }}

                .signature-box {{
                    width: 45%;
                }}

                .signature-line {{
                    margin-top: 65px;
                    border-top: 2px solid #334155;
                    padding-top: 10px;
                    font-size: 13px;
                    font-weight: 600;
                    color: #475569;
                }}

                .footer {{
                    margin-top: 50px;
                    border-top: 1px solid #cbd5e1;
                    padding-top: 18px;
                    text-align: center;
                    color: #64748b;
                    font-size: 11px;
                }}

                .footer p {{
                    margin: 5px 0;
                }}

            </style>

        </head>

        <body>

            <div class="page">

                <div class="header">

                    <div class="header-top">

                        <div class="company-details">
                            <h1>{title}</h1>
                            <p>Enterprise ERP Management System</p>
                        </div>

                        <div class="document-badge">
                            OFFICIAL DOCUMENT
                        </div>

                    </div>

                </div>

                <div class="content">

                    <div class="date">
                        Generated Date : {today}
                    </div>

                    <div class="section-title">
                        Customer Information
                    </div>

                    <table class="customer-table">

                        <tr>
                            <td class="label">Customer ID</td>
                            <td class="value">{values.get('ID', '')}</td>
                        </tr>

                        <tr>
                            <td class="label">Customer Name</td>
                            <td class="value">{values.get('Name', '')}</td>
                        </tr>

                        <tr>
                            <td class="label">Email Address</td>
                            <td class="value">{values.get('Mail', '')}</td>
                        </tr>

                        <tr>
                            <td class="label">Phone Number</td>
                            <td class="value">{values.get('Phone', '')}</td>
                        </tr>

                        <tr>
                            <td class="label">City</td>
                            <td class="value">{values.get('City', '')}</td>
                        </tr>

                        <tr>
                            <td class="label">State</td>
                            <td class="value">{values.get('State', '')}</td>
                        </tr>

                    </table>

                    <div class="letter-section">

                        <div class="section-title">
                            Request Letter
                        </div>

                        <div class="letter-body">
                            {formatted_body}
                        </div>

                    </div>

                    <div class="signature-area">

                        <div class="signature-container">

                            <div class="signature-box">
                                <div class="signature-line">
                                    Prepared By<br>
                                    Customer Service Department
                                </div>
                            </div>

                            <div class="signature-box">
                                <div class="signature-line">
                                    Approved By<br>
                                    Operations Management
                                </div>
                            </div>

                        </div>

                    </div>

                    <div class="footer">
                        <p>This document was generated automatically by Enterprise ERP System</p>
                        <p>Confidential • Internal Business Communication</p>
                        <p>© 2026 Enterprise ERP Solutions. All Rights Reserved.</p>
                    </div>

                </div>

            </div>

        </body>
        </html>
        """

    def preview_and_save_pdf(self, html, save_title):
        try:
            document = QTextDocument()
            document.setHtml(html)

            # 1. Setup the high-resolution engine for CSS rendering
            printer = QPrinter(QPrinter.HighResolution)
            printer.setPageSize(QPageSize(QPageSize.A4))
            printer.setOrientation(QPrinter.Landscape)
            printer.setPageMargins(12, 12, 12, 12, QPrinter.Millimeter)

            # Fix layout clipping: Tell the HTML engine to scale perfectly to the printer paper boundaries
            document.setPageSize(printer.pageRect(QPrinter.DevicePixel).size())

            # 2. Open the Preview Dialog window displaying the correct HTML/CSS formatting
            preview = QPrintPreviewDialog(printer, self)
            preview.setWindowTitle("PDF Preview - Customer Request")
            preview.paintRequested.connect(lambda p: document.print_(p))
            result = preview.exec()
            
            # If the user closes or cancels the preview, stop execution here
            if result != QDialog.Accepted:
                return

            # 3. Direct System Save Operation (Skip standard hardware print queues)
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                save_title, 
                "", 
                "PDF Files (*.pdf)"
            )
            if not file_path:
                QMessageBox.information(self, "Save Cancelled", "PDF save was cancelled.")
                return
                
            if not file_path.lower().endswith(".pdf"):
                file_path += ".pdf"

            # 4. Generate a clean system printer context dedicated entirely to saving the PDF binary
            export_printer = QPrinter(QPrinter.HighResolution)
            export_printer.setPageSize(QPageSize(QPageSize.A4))
            export_printer.setOrientation(QPrinter.Landscape)
            export_printer.setPageMargins(12, 12, 12, 12, QPrinter.Millimeter)
            
            # Enforce direct file output parameters instead of routing to standard hardware
            export_printer.setOutputFormat(QPrinter.PdfFormat)
            export_printer.setOutputFileName(file_path)
            
            # Write the formatted document directly to your storage disk
            document.print_(export_printer)
            
            QMessageBox.information(
                self, 
                "PDF Exported Successfully", 
                f"PDF has been safely saved to:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while generating PDF:\n{str(e)}")

            
    def add_customer(self):
        dialog = CustomerForm(self)
        if dialog.exec() == QDialog.Accepted:
            self.load_customers()

    def edit_customer(self):
        customer = self.get_selected_customer()
        if not customer:
            QMessageBox.warning(self, "Select customer", "Please select a customer to edit")
            return

        dialog = CustomerForm(self, customer=customer)
        if dialog.exec() == QDialog.Accepted:
            self.load_customers()
    def open_customer_context_menu(self, position):

        item = self.table.itemAt(position)

        if not item:
            return

        # only when clicking ID column
        if item.column() != 0:
            return

        menu = QMenu(self)

        view_contacts_action = menu.addAction(
            "View Customer Contacts"
        )

        action = menu.exec(
            self.table.viewport().mapToGlobal(position)
        )

        if action == view_contacts_action:

            customer_id = int(item.text())

            dialog = CustomerContactsDialog(
                customer_id,
                self
            )

            dialog.exec()
    def delete_customer(self):
        customer = self.get_selected_customer()
        if not customer:
            QMessageBox.warning(self, "Select customer", "Please select a customer to delete")
            return

        confirm = QMessageBox.question(
            self,
            "Delete customer",
            "Are you sure you want to delete this customer?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if confirm == QMessageBox.Yes:
            self.service.delete_customer(customer[0])
            self.load_customers()
