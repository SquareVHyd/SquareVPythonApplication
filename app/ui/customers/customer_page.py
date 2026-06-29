from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLineEdit, QLabel, QAbstractItemView, QMessageBox, QStatusBar
)
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QShortcut, QKeySequence, QAction
from PySide6.QtWidgets import QMenu

from app.services.customer_service import CustomerService
from app.ui.searchable_table import SearchableTable, NumericTableWidgetItem
from app.utils.worker_thread import Worker
from app.ui.customers.organization_contacts_dialog import OrganizationContactsDialog

class CustomerPage(QWidget):
    def __init__(self):
        super().__init__()
        self.service = CustomerService()
        self._cache = []
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._perform_search)
        self._worker = None

        self.setup_ui()
        self.refresh_table()

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
        title = QLabel("Customers (Google Contacts)")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search Organization, Email or Phone...")
        self.search_box.textChanged.connect(self._debounce_search)

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh_table)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.search_box)
        header.addWidget(self.refresh_btn)
        layout.addLayout(header)

        # Table
        self.table = SearchableTable()
        self.table.setStyleSheet("QTableView { selection-background-color: #93c5fd; selection-color: #000000; } QHeaderView::section { background-color: #fce4ec; border: 1px solid #e2e8f0; }")
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([
            "Organization Name",
            # "ID", # Assuming ID is not displayed but might be useful for internal lookup
            "Email",
            "Phone"
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

        # Status Bar
        self.status_bar = QStatusBar()
        layout.addWidget(self.status_bar)

        # Shortcuts
        QShortcut(QKeySequence("Ctrl+R"), self, activated=self.refresh_table)
        QShortcut(QKeySequence.Find, self, activated=lambda: self.search_box.setFocus())

        # Enable custom context menu for the table
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

    def _show_context_menu(self, pos: QPoint):
        # Get the item at the clicked position
        item = self.table.itemAt(pos)
        if item is None:
            return

        # Get the row of the clicked item
        row = item.row()
        organization_name_item = self.table.item(row, 0) # Assuming "Organization Name" is the first column (index 0)
        if organization_name_item is None:
            return

        organization_name = organization_name_item.text()

        context_menu = QMenu(self)
        view_contacts_action = QAction("View Contacts", self)
        view_contacts_action.triggered.connect(lambda: self._view_organization_contacts(organization_name))
        context_menu.addAction(view_contacts_action)

        context_menu.exec(self.table.mapToGlobal(pos))

    def refresh_table(self):
        """Load data asynchronously to keep UI responsive."""
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
                val = str(row[c]) if row[c] is not None else ""
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