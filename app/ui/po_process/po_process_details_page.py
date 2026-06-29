from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QFrame, QPushButton, 
    QLabel, QStackedWidget, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QButtonGroup
)
from app.ui.components.menu_button import MenuButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QShortcut, QKeySequence

from app.services.po_process_service import POProcessService
from app.ui.quotations.reports.test_reports_page import TestReportsPage
from app.ui.quotations.reports.po_generator_page import PoGeneratorPage
from app.ui.sld_analyzer.sld_page import SldPage
from app.ui.po_process.po_customer_page import POCustomerPage
from app.ui.po_process.minutes_of_meeting_page import MinutesOfMeetingPage
from app.ui.po_process.complaints_page import ComplaintsPage
from app.ui.po_process.contract_bills_page import ContractBillsPage

class POProcessQuotationPage(QWidget):
    """Simplified quotation table specifically for selecting a quote in PO Process."""
    def __init__(self, parent_process_page):
        super().__init__()
        self.parent_process_page = parent_process_page
        self.service = POProcessService()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        btn_style = """
            QPushButton {
                background-color: #e0f2fe;
                color: #0c4a6e;
                border: 1px solid #bae6fd;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #bae6fd; }
            QPushButton:pressed { background-color: #7dd3fc; }
            QPushButton:disabled { background-color: transparent; color: #94a3b8; border: none; }
            QComboBox {
                background-color: white;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 5px 12px;
                font-size: 13px;
                color: #0f172a;
            }
            QComboBox::drop-down {
                border-left: 1px solid #cbd5e1;
                width: 24px;
            }
        """
        self.setStyleSheet(self.styleSheet() + btn_style)

        
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

        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        self.quotations_btn = MenuButton("📄 Quotations List")
        self.quotations_btn.clicked.connect(self.show_quotations)

        self.test_reports_btn = MenuButton("📄 Test Reports")
        self.test_reports_btn.clicked.connect(self.show_test_reports)
        self.test_reports_btn.setEnabled(False)

        self.po_sales_person_btn = MenuButton("📄 Supplier_POs")
        self.po_sales_person_btn.clicked.connect(self.show_po_sales_person)
        self.po_sales_person_btn.setEnabled(False)

        self.sld_analyzer_btn = MenuButton("📏 SLD Analyzer")
        self.sld_analyzer_btn.clicked.connect(self.show_sld_analyzer)
        self.sld_analyzer_btn.setToolTip("View General Arrangement diagrams for this quotation")
        self.sld_analyzer_btn.setEnabled(False)

        self.po_customers_btn = MenuButton("📄 PO_Customers")
        self.po_customers_btn.clicked.connect(self.show_po_customers)
        self.po_customers_btn.setEnabled(False)

        self.min_of_meeting_btn = MenuButton("📄 Minutes of Meeting")
        self.min_of_meeting_btn.clicked.connect(self.show_minutes_of_meeting)
        self.min_of_meeting_btn.setEnabled(False)

        self.complaints_btn = MenuButton("📄 Complaints")
        self.complaints_btn.clicked.connect(self.show_complaints)
        self.complaints_btn.setEnabled(False)

        self.contract_bills_btn = MenuButton("🧾 Contract Bills")
        self.contract_bills_btn.clicked.connect(self.show_contract_bills)
        self.contract_bills_btn.setEnabled(False)
        
        self.btn_group.addButton(self.quotations_btn)
        self.btn_group.addButton(self.test_reports_btn)
        self.btn_group.addButton(self.po_sales_person_btn)
        self.btn_group.addButton(self.sld_analyzer_btn)
        self.btn_group.addButton(self.po_customers_btn)
        self.btn_group.addButton(self.min_of_meeting_btn)
        self.btn_group.addButton(self.complaints_btn)
        self.btn_group.addButton(self.contract_bills_btn)

        sidebar_layout.addWidget(title)
        sidebar_layout.addWidget(self.quotations_btn)
        sidebar_layout.addWidget(self.test_reports_btn)
        sidebar_layout.addWidget(self.po_sales_person_btn)
        sidebar_layout.addWidget(self.sld_analyzer_btn)
        sidebar_layout.addWidget(self.po_customers_btn)
        sidebar_layout.addWidget(self.min_of_meeting_btn)
        sidebar_layout.addWidget(self.complaints_btn)
        sidebar_layout.addWidget(self.contract_bills_btn)
        sidebar_layout.addStretch()

        self.close_btn = MenuButton("↩️ Back to ERP")
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
        self.min_of_meeting_page = MinutesOfMeetingPage(self)
        self.complaints_page = ComplaintsPage(self)
        self.contract_bills_page = ContractBillsPage(self)

        self.pages.addWidget(self.welcome_page)
        self.pages.addWidget(self.quotation_page)
        self.pages.addWidget(self.test_reports_page)
        self.pages.addWidget(self.po_generator_page)
        self.pages.addWidget(self.sld_page)
        self.pages.addWidget(self.po_customer_page)
        self.pages.addWidget(self.min_of_meeting_page)
        self.pages.addWidget(self.complaints_page)
        self.pages.addWidget(self.contract_bills_page)

        self.splitter.addWidget(sidebar_frame)
        self.splitter.addWidget(self.pages)
        self.splitter.setStretchFactor(1, 1)

        self.layout.addWidget(self.splitter)

        self.setStyleSheet(
            "#sidebar { background-color: #f8fafc; } "
            "#appTitle { font-size: 20px; font-weight: bold; margin-bottom: 16px; padding-left: 10px; }"
            "QHeaderView::section { background-color: #fce4ec; border: 1px solid #e2e8f0; padding: 4px; font-weight: bold; }"
        )

        self.esc_shortcut = QShortcut(QKeySequence("Esc"), self)
        self.esc_shortcut.activated.connect(self._back_to_erp)
        
        self.show_quotations()

    def _back_to_erp(self):
        if self.parent_main_window:
            self.parent_main_window.show_dashboard()

    def update_button_state(self, enabled):
        self.test_reports_btn.setEnabled(enabled)
        self.po_sales_person_btn.setEnabled(enabled)
        self.sld_analyzer_btn.setEnabled(enabled)
        self.po_customers_btn.setEnabled(enabled)
        self.min_of_meeting_btn.setEnabled(enabled)
        self.complaints_btn.setEnabled(enabled)
        self.contract_bills_btn.setEnabled(enabled)

    def show_quotations(self):
        self.pages.setCurrentWidget(self.quotation_page)
        self.quotations_btn.setChecked(True)

    def show_test_reports(self):
        selected = self.quotation_page.table.selectionModel().selectedRows()
        if selected:
            row = selected[0].row()
            quote_id = int(self.quotation_page.table.item(row, 0).text())
            project_name = self.quotation_page.table.item(row, 7).text()
            self.test_reports_page.load_quotation(quote_id, project_name)
            self.pages.setCurrentWidget(self.test_reports_page)
            self.test_reports_btn.setChecked(True)
        else:
            QMessageBox.warning(self, "Selection Required", "Please select a quotation first.")

    def show_po_sales_person(self):
        selected = self.quotation_page.table.selectionModel().selectedRows()
        if selected:
            row = selected[0].row()
            quote_id = int(self.quotation_page.table.item(row, 0).text())
            self.po_generator_page.load_quotation(quote_id)
            self.pages.setCurrentWidget(self.po_generator_page)
            self.po_sales_person_btn.setChecked(True)
        else:
            QMessageBox.warning(self, "Selection Required", "Please select a quotation first.")

    def show_sld_analyzer(self):
        selected = self.quotation_page.table.selectionModel().selectedRows()
        if selected:
            row = selected[0].row()
            quote_id = int(self.quotation_page.table.item(row, 0).text())
            self.sld_page.load_quotation(quote_id)
            self.pages.setCurrentWidget(self.sld_page)
            self.sld_analyzer_btn.setChecked(True)
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
            self.po_customers_btn.setChecked(True)
        else:
            QMessageBox.warning(self, "Selection Required", "Please select a quotation first.")

    def show_minutes_of_meeting(self):
        selected = self.quotation_page.table.selectionModel().selectedRows()
        if selected:
            row = selected[0].row()
            quote_id = int(self.quotation_page.table.item(row, 0).text())
            self.min_of_meeting_page.load_quotation(quote_id)
            self.pages.setCurrentWidget(self.min_of_meeting_page)
            self.min_of_meeting_btn.setChecked(True)
        else:
            QMessageBox.warning(self, "Selection Required", "Please select a quotation first.")

    def show_complaints(self):
        selected = self.quotation_page.table.selectionModel().selectedRows()
        if selected:
            row = selected[0].row()
            quote_id = int(self.quotation_page.table.item(row, 0).text())
            self.complaints_page.load_quotation(quote_id)
            self.pages.setCurrentWidget(self.complaints_page)
            self.complaints_btn.setChecked(True)
        else:
            QMessageBox.warning(self, "Selection Required", "Please select a quotation first.")

    def show_contract_bills(self):
        selected = self.quotation_page.table.selectionModel().selectedRows()
        if selected:
            row = selected[0].row()
            quote_id = int(self.quotation_page.table.item(row, 0).text())
            project_name = self.quotation_page.table.item(row, 7).text()
            self.contract_bills_page.load_quotation(quote_id, project_name)
            self.pages.setCurrentWidget(self.contract_bills_page)
            self.contract_bills_btn.setChecked(True)
        else:
            QMessageBox.warning(self, "Selection Required", "Please select a quotation first.")
