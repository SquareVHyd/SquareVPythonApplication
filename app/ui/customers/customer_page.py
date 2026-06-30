from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QFrame, QSplitter,
    QPushButton, QLineEdit, QAbstractItemView,
    QMessageBox, QStatusBar, QButtonGroup
)
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QShortcut, QKeySequence, QAction
from PySide6.QtWidgets import QMenu

from app.ui.components.menu_button import MenuButton
from app.services.customer_service import CustomerService
from app.ui.searchable_table import SearchableTable, NumericTableWidgetItem
from app.utils.worker_thread import Worker
from app.ui.customers.organization_contacts_dialog import OrganizationContactsDialog
from app.ui.customers.cust_db_page import CustDbPage


class CustomerPage(QWidget):
    """
    Customer page with a sidebar menu (like QuotationDetailsPage) with two views:
      • 📇 Google Contacts  – existing google_contacts table view
      • 🗄️ Contacts DB      – tblCustomers table view (CustDbPage)
    """

    PAGE_GOOGLE  = 0
    PAGE_CUST_DB = 1

    def __init__(self):
        super().__init__()
        self.service        = CustomerService()
        self._cache         = []
        self._search_timer  = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._perform_search)
        self._worker        = None

        self._setup_ui()
        self.refresh_table()   # pre-load the Google Contacts view

    # ==================================================================
    # UI Construction
    # ==================================================================
    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        # ---- Horizontal splitter: sidebar | content ------------------
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(1)
        self.splitter.setStyleSheet("QSplitter::handle { background-color: #e2e8f0; }")

        # ── Sidebar ───────────────────────────────────────────────────
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setMinimumWidth(200)
        sidebar.setMaximumWidth(400)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(20, 20, 20, 20)
        sb_layout.setSpacing(12)

        title = QLabel("Customers")
        title.setObjectName("appTitle")
        title.setAlignment(Qt.AlignCenter)

        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        self.btn_google = MenuButton("📇 Google Contacts")
        self.btn_google.setToolTip("View customers from synced Google Contacts")
        self.btn_google.clicked.connect(lambda: self._switch_page(self.PAGE_GOOGLE))

        self.btn_custdb = MenuButton("🗄️ Contacts DB")
        self.btn_custdb.setToolTip("View & manage customers from the internal database")
        self.btn_custdb.clicked.connect(lambda: self._switch_page(self.PAGE_CUST_DB))

        self.btn_group.addButton(self.btn_google,  self.PAGE_GOOGLE)
        self.btn_group.addButton(self.btn_custdb,  self.PAGE_CUST_DB)

        sb_layout.addWidget(title)
        sb_layout.addWidget(self.btn_google)
        sb_layout.addWidget(self.btn_custdb)
        sb_layout.addStretch()

        # ── Stacked content pages ─────────────────────────────────────
        self.pages = QStackedWidget()

        # Page 0 – Google Contacts
        self.google_page = self._build_google_contacts_page()
        self.pages.addWidget(self.google_page)             # index 0

        # Page 1 – Contacts DB
        self.cust_db_page = CustDbPage()
        self.pages.addWidget(self.cust_db_page)            # index 1

        # Assemble splitter
        self.splitter.addWidget(sidebar)
        self.splitter.addWidget(self.pages)
        self.splitter.setStretchFactor(1, 1)

        root.addWidget(self.splitter)

        # Apply sidebar styling consistent with MainWindow & QuotationDetailsPage
        self.setStyleSheet(
            "#sidebar { background-color: #f8fafc; } "
            "#appTitle { font-size: 20px; font-weight: bold; margin-bottom: 16px; padding-left: 10px; } "
            "QHeaderView::section { background-color: #fce4ec; border: 1px solid #e2e8f0; padding: 4px; font-weight: bold; }"
        )

        # Default to Google Contacts, mark button checked
        self.pages.setCurrentIndex(self.PAGE_GOOGLE)
        self.btn_google.setChecked(True)

    # ==================================================================
    # Page switching
    # ==================================================================
    def _switch_page(self, index: int):
        self.pages.setCurrentIndex(index)
        # The exclusive QButtonGroup handles button state visually

    # ==================================================================
    # Google Contacts view – original logic
    # ==================================================================
    def _build_google_contacts_page(self) -> QWidget:
        """Builds and returns the original Google Contacts widget."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 4)

        # Header
        header = QHBoxLayout()
        title = QLabel("Customers (Google Contacts)")
        title.setStyleSheet("font-size: 17px; font-weight: bold;")

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search Organization, Email or Phone...")
        self.search_box.textChanged.connect(self._debounce_search)

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #e0f2fe; color: #0c4a6e;
                border: 1px solid #bae6fd; padding: 6px 12px;
                border-radius: 4px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover  { background-color: #bae6fd; }
            QPushButton:pressed { background-color: #7dd3fc; }
        """)
        self.refresh_btn.clicked.connect(self.refresh_table)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.search_box)
        header.addWidget(self.refresh_btn)
        layout.addLayout(header)

        # Table
        self.table = SearchableTable()
        self.table.setStyleSheet(
            "QTableView { selection-background-color: #93c5fd; selection-color: #000000; } "
            "QHeaderView::section { background-color: #fce4ec; border: 1px solid #e2e8f0; }"
        )
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Organization Name", "Email", "Phone"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

        # Status bar
        self.status_bar = QStatusBar()
        layout.addWidget(self.status_bar)

        # Shortcuts (scoped to this page widget)
        QShortcut(QKeySequence("Ctrl+R"), page, activated=self.refresh_table)
        QShortcut(QKeySequence.Find,      page, activated=lambda: self.search_box.setFocus())

        # Context menu
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        return page

    # ------------------------------------------------------------------
    # Google Contacts – data logic (unchanged from original)
    # ------------------------------------------------------------------
    def _show_context_menu(self, pos: QPoint):
        item = self.table.itemAt(pos)
        if item is None:
            return
        row = item.row()
        org_item = self.table.item(row, 0)
        if org_item is None:
            return
        org_name = org_item.text()

        menu = QMenu(self)
        action = QAction("View Contacts", self)
        action.triggered.connect(lambda: self._view_organization_contacts(org_name))
        menu.addAction(action)
        menu.exec(self.table.mapToGlobal(pos))

    def refresh_table(self):
        """Load Google Contacts data asynchronously."""
        if self._worker:
            return
        self.status_bar.showMessage("Loading customers...")
        self._worker = Worker(self.service.get_customers)
        self._worker.result.connect(self._on_data_loaded)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_data_loaded(self, rows):
        self._cache = list(rows)
        self._render(self._cache)
        self.status_bar.showMessage(f"Loaded {len(rows)} customers", 5000)
        self._worker = None

    def _on_error(self, err):
        QMessageBox.critical(self, "Database Error", f"Failed to load customers: {err}")
        self.status_bar.clearMessage()
        self._worker = None

    def _render(self, rows):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c in range(3):
                val  = str(row[c]) if row[c] is not None else ""
                item = NumericTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(r, c, item)
        self.table.setSortingEnabled(True)
        self.table.resizeColumnsToContents()

    def _debounce_search(self):
        self._search_timer.start(300)

    def _perform_search(self):
        keyword = self.search_box.text().lower().strip()
        if not keyword:
            self._render(self._cache)
            return
        filtered = [
            row for row in self._cache
            if any(keyword in str(cell).lower() for cell in row if cell)
        ]
        self._render(filtered)

    def _view_organization_contacts(self, organization_name: str):
        dialog = OrganizationContactsDialog(organization_name, self)
        dialog.exec()