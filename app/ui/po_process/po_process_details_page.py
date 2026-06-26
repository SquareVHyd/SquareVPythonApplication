from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QFrame, QPushButton, 
    QLabel, QStackedWidget, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QShortcut, QKeySequence

from app.services.po_process_service import POProcessService
from app.ui.quotations.reports.test_reports_page import TestReportsPage
from app.ui.quotations.reports.po_generator_page import PoGeneratorPage
from app.ui.sld_analyzer.sld_page import SldPage
from app.ui.po_process.po_customer_page import POCustomerPage

class POProcessQuotationPage(QWidget):
    """Simplified quotation table specifically for selecting a quote in PO Process."""
    def __init__(self, parent_process_page):
        super().__init__()
        self.parent_process_page = parent_process_page
        self.service = POProcessService()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("Select Quotation for PO Process")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #0f172a;")
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_data)
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(refresh_btn)
        layout.addLayout(header)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "Customer ID", "Customer Name", "Date of Request", 
            "Date Quote", "Reference No", "Subject", "Project Name", "Rev No"
        ])
        
        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(QHeaderView.Interactive)
        header_view.setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # When selection changes, update the sidebar buttons in parent
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        
        layout.addWidget(self.table)
        self.load_data()

    def load_data(self):
        self.table.setRowCount(0)
        quotes = self.service.get_all_quotations()
        
        self.table.setRowCount(len(quotes))
        for row_idx, row_data in enumerate(quotes):
            # indices mapping based on get_all_quotations query:
            # 0:ID, 1:CustomerId, 2:CustomerName, 3:DateOfRequest, 4:Date_Quote, 
            # 5:QuoteRereceNo, 6:QuoteSubject, 7:QuoteProjectName, 8:CustomerContactName,
            # 9:PreparedBy, 10:QuoteStatus, 11:BaseQuoteID, 12:RevisionNo
            cols = [
                str(row_data[0] or ""),
                str(row_data[1] or ""),
                str(row_data[2] or ""),
                str(row_data[3] or ""),
                str(row_data[4] or ""),
                str(row_data[5] or ""),
                str(row_data[6] or ""),
                str(row_data[7] or ""),
                str(row_data[12] or "0"),
            ]
            for col_idx, text in enumerate(cols):
                item = QTableWidgetItem(text)
                self.table.setItem(row_idx, col_idx, item)
        self.table.resizeColumnsToContents()

    def on_selection_changed(self):
        has_selection = len(self.table.selectionModel().selectedRows()) > 0
        self.parent_process_page.update_button_state(has_selection)


class POProcessDetailsPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.parent_main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.splitter = QSplitter(Qt.Horizontal)

        # Sidebar
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("sidebar")
        sidebar_frame.setMinimumWidth(220)
        sidebar_frame.setMaximumWidth(280)
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(15, 20, 15, 20)
        sidebar_layout.setSpacing(10)

        title = QLabel("PO Process")
        title.setObjectName("appTitle")

        self.quotations_btn = QPushButton("📄 Quotations List")
        self.quotations_btn.clicked.connect(self.show_quotations)

        self.test_reports_btn = QPushButton("📄 Test Reports")
        self.test_reports_btn.clicked.connect(self.show_test_reports)
        self.test_reports_btn.setEnabled(False)

        self.po_sales_person_btn = QPushButton("📄 Supplier_POs")
        self.po_sales_person_btn.clicked.connect(self.show_po_sales_person)
        self.po_sales_person_btn.setEnabled(False)

        self.sld_analyzer_btn = QPushButton("📏 SLD Analyzer")
        self.sld_analyzer_btn.clicked.connect(self.show_sld_analyzer)
        self.sld_analyzer_btn.setToolTip("View General Arrangement diagrams for this quotation")
        self.sld_analyzer_btn.setEnabled(False)

        self.po_customers_btn = QPushButton("📄 PO_Customers")
        self.po_customers_btn.clicked.connect(self.show_po_customers)
        self.po_customers_btn.setEnabled(False)

        sidebar_layout.addWidget(title)
        sidebar_layout.addWidget(self.quotations_btn)
        sidebar_layout.addWidget(self.test_reports_btn)
        sidebar_layout.addWidget(self.po_sales_person_btn)
        sidebar_layout.addWidget(self.sld_analyzer_btn)
        sidebar_layout.addWidget(self.po_customers_btn)
        sidebar_layout.addStretch()

        self.close_btn = QPushButton("↩️ Back to ERP")
        self.close_btn.clicked.connect(self._back_to_erp)
        sidebar_layout.addWidget(self.close_btn)

        # Pages
        self.pages = QStackedWidget()

        self.welcome_page = QLabel("Select a quotation to generate PO or Test Reports.")
        self.welcome_page.setAlignment(Qt.AlignCenter)
        self.welcome_page.setStyleSheet("font-size: 16px; color: #64748b;")

        self.quotation_page = POProcessQuotationPage(self)
        self.test_reports_page = TestReportsPage(self)
        self.po_generator_page = PoGeneratorPage(self)
        self.sld_page = SldPage(self)
        self.po_customer_page = POCustomerPage(self)

        self.pages.addWidget(self.welcome_page)
        self.pages.addWidget(self.quotation_page)
        self.pages.addWidget(self.test_reports_page)
        self.pages.addWidget(self.po_generator_page)
        self.pages.addWidget(self.sld_page)
        self.pages.addWidget(self.po_customer_page)

        self.splitter.addWidget(sidebar_frame)
        self.splitter.addWidget(self.pages)
        self.splitter.setStretchFactor(1, 1)

        self.layout.addWidget(self.splitter)

        self.setStyleSheet(
            "#sidebar { background-color: #f0f2f5; } "
            "#appTitle { font-size: 20px; font-weight: bold; margin-bottom: 16px; }"
            "QHeaderView::section { background-color: #fce4ec; border: 1px solid #e2e8f0; padding: 4px; font-weight: bold; }"
        )

        self.esc_shortcut = QShortcut(QKeySequence("Esc"), self)
        self.esc_shortcut.activated.connect(self._back_to_erp)

    def _back_to_erp(self):
        if self.parent_main_window:
            self.parent_main_window.show_dashboard()

    def update_button_state(self, enabled):
        self.test_reports_btn.setEnabled(enabled)
        self.po_sales_person_btn.setEnabled(enabled)
        self.sld_analyzer_btn.setEnabled(enabled)
        self.po_customers_btn.setEnabled(enabled)

    def show_quotations(self):
        self.pages.setCurrentWidget(self.quotation_page)

    def show_test_reports(self):
        selected = self.quotation_page.table.selectionModel().selectedRows()
        if selected:
            row = selected[0].row()
            quote_id = int(self.quotation_page.table.item(row, 0).text())
            project_name = self.quotation_page.table.item(row, 7).text()
            self.test_reports_page.load_quotation(quote_id, project_name)
            self.pages.setCurrentWidget(self.test_reports_page)
        else:
            QMessageBox.warning(self, "Selection Required", "Please select a quotation first.")

    def show_po_sales_person(self):
        selected = self.quotation_page.table.selectionModel().selectedRows()
        if selected:
            row = selected[0].row()
            quote_id = int(self.quotation_page.table.item(row, 0).text())
            self.po_generator_page.load_quotation(quote_id)
            self.pages.setCurrentWidget(self.po_generator_page)
        else:
            QMessageBox.warning(self, "Selection Required", "Please select a quotation first.")

    def show_sld_analyzer(self):
        selected = self.quotation_page.table.selectionModel().selectedRows()
        if selected:
            row = selected[0].row()
            quote_id = int(self.quotation_page.table.item(row, 0).text())
            self.sld_page.load_quotation(quote_id)
            self.pages.setCurrentWidget(self.sld_page)
        else:
            QMessageBox.warning(self, "Selection Required", "Please select a quotation first.")

    def show_po_customers(self):
        selected = self.quotation_page.table.selectionModel().selectedRows()
        if selected:
            row = selected[0].row()
            quote_id = int(self.quotation_page.table.item(row, 0).text())
            project_name = self.quotation_page.table.item(row, 7).text()
            self.po_customer_page.load_quotation(quote_id, project_name)
            self.pages.setCurrentWidget(self.po_customer_page)
        else:
            QMessageBox.warning(self, "Selection Required", "Please select a quotation first.")
