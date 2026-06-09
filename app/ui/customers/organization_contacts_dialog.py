from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QAbstractItemView, QPushButton, QHeaderView, QMessageBox,
    QSplitter, QWidget, QMenu, QLineEdit
)
from PySide6.QtCore import Qt, QPoint, QTimer
from PySide6.QtGui import QAction, QShortcut, QKeySequence

from app.services.customer_service import CustomerService
from app.ui.searchable_table import SearchableTable, NumericTableWidgetItem
from app.ui.master.generic_crud_dialog import GenericCrudDialog
from app.utils.worker_thread import Worker

class OrganizationContactsDialog(QDialog):
    def __init__(self, organization_name, parent=None):
        super().__init__(parent)
        self.organization_name = organization_name
        self.service = CustomerService()
        self._worker = None
        self._fp_worker = None
        self._contacts_cache = []
        self._current_google_id = None
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._perform_contact_search)

        self.setWindowTitle("Organization Contacts")
        self.setMinimumSize(800, 500)
        self.setup_ui()
        self._load_contacts_async()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        self.splitter = QSplitter(Qt.Horizontal)

        # Left Side: Contacts Table Container
        contacts_container = QWidget()
        contacts_layout = QVBoxLayout(contacts_container)
        
        # Header for Contacts
        contacts_header = QHBoxLayout()
        contacts_header.addWidget(QLabel(f"<b>{self.organization_name}</b>"))
        contacts_header.addStretch()

        self.contact_search = QLineEdit()
        self.contact_search.setPlaceholderText("Search contacts...")
        self.contact_search.setFixedWidth(180)
        self.contact_search.textChanged.connect(self._debounce_contact_search)

        self.btn_refresh = QPushButton("🔄")
        self.btn_refresh.setToolTip("Refresh (Ctrl+R)")
        self.btn_refresh.clicked.connect(self._load_contacts_async)

        self.btn_add_contact = QPushButton("➕ Add")
        self.btn_add_contact.setToolTip("Add Contact (Ctrl+N)")
        self.btn_add_contact.clicked.connect(self._add_contact)
        self.btn_edit_contact = QPushButton("✏️ Edit")
        self.btn_edit_contact.setToolTip("Edit Contact (Ctrl+E)")
        self.btn_edit_contact.clicked.connect(self._edit_contact)
        self.btn_del_contact = QPushButton("🗑️")
        self.btn_del_contact.setToolTip("Delete Contact (Delete)")
        self.btn_del_contact.clicked.connect(self._delete_contact)

        contacts_header.addWidget(self.contact_search)
        contacts_header.addWidget(self.btn_refresh)
        contacts_header.addWidget(self.btn_add_contact)
        contacts_header.addWidget(self.btn_edit_contact)
        contacts_header.addWidget(self.btn_del_contact)
        contacts_layout.addLayout(contacts_header)

        self.table = SearchableTable()
        self.table.setStyleSheet("QTableView { selection-background-color: #93c5fd; selection-color: #000000; } QHeaderView::section { background-color: #fce4ec; border: 1px solid #e2e8f0; }")
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Google ID",
            "First Name",
            "Middle Name",
            "Last Name",
            "Phone",
            "Email"
        ])
        self.table.hideColumn(0)  # Hide Google ID
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Enable Context Menu
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        
        contacts_layout.addWidget(self.table)
        self.contact_status = QLabel("Contacts: 0")
        contacts_layout.addWidget(self.contact_status)

        # Right Side: Followup Panel
        self.followup_panel = QWidget()
        self.followup_panel.hide() # Hidden by default
        fp_layout = QVBoxLayout(self.followup_panel)
        
        fp_header = QHBoxLayout()
        self.fp_title = QLabel("Followups")
        self.fp_title.setStyleSheet("font-weight: bold;")
        
        self.btn_add_fp = QPushButton("➕")
        self.btn_add_fp.setToolTip("Add Followup")
        self.btn_add_fp.clicked.connect(self._add_followup)
        self.btn_edit_fp = QPushButton("✏️")
        self.btn_edit_fp.setToolTip("Edit Followup")
        self.btn_edit_fp.clicked.connect(self._edit_followup)
        self.btn_del_fp = QPushButton("🗑️")
        self.btn_del_fp.setToolTip("Delete Followup")
        self.btn_del_fp.clicked.connect(self._delete_followup)

        close_fp_btn = QPushButton("❌")
        close_fp_btn.setFixedWidth(30)
        close_fp_btn.clicked.connect(self.followup_panel.hide)

        fp_header.addWidget(self.fp_title)
        fp_header.addStretch()
        fp_header.addWidget(self.btn_add_fp)
        fp_header.addWidget(self.btn_edit_fp)
        fp_header.addWidget(self.btn_del_fp)
        fp_header.addWidget(close_fp_btn)
        fp_layout.addLayout(fp_header)

        self.followup_table = SearchableTable()
        self.followup_table.setStyleSheet("QTableView { selection-background-color: #93c5fd; selection-color: #000000; } QHeaderView::section { background-color: #fce4ec; border: 1px solid #e2e8f0; }")
        self.followup_table.setColumnCount(6)
        self.followup_table.setHorizontalHeaderLabels([
            "Date", "Mode", "Discussed", "Next Date", "Status", "ID"
        ])
        self.followup_table.hideColumn(5)
        fp_layout.addWidget(self.followup_table)
        
        self.fp_status = QLabel("Rows: 0")
        fp_layout.addWidget(self.fp_status)

        # Add to Splitter
        self.splitter.addWidget(contacts_container)
        self.splitter.addWidget(self.followup_panel)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(self.splitter)

        button_layout = QHBoxLayout()
        close_button = QPushButton("✖️ Close")
        close_button.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        main_layout.addLayout(button_layout)

        # Shortcuts
        QShortcut(QKeySequence("Ctrl+N"), self, activated=lambda: self._on_shortcut_add())
        QShortcut(QKeySequence("Ctrl+E"), self, activated=lambda: self._on_shortcut_edit())
        QShortcut(QKeySequence("Delete"), self, activated=lambda: self._on_shortcut_delete())
        QShortcut(QKeySequence("Ctrl+R"), self, activated=self._load_contacts_async)
        QShortcut(QKeySequence.Find, self, activated=lambda: self.contact_search.setFocus())

    def _show_context_menu(self, pos: QPoint):
        """Handles right-click on individual contacts to show followup history."""
        item = self.table.itemAt(pos)
        if not item:
            return

        row = item.row()
        # Column 0 is the hidden Google ID
        google_id = self.table.item(row, 0).text()
        # Construct name for the title: First Name (1) and Last Name (3)
        first_name = self.table.item(row, 1).text()
        last_name = self.table.item(row, 3).text()
        contact_name = f"{first_name} {last_name}".strip()

        menu = QMenu(self)
        view_action = QAction(f"View Followups for {contact_name}", self)
        view_action.triggered.connect(lambda: self._load_followups(google_id, contact_name))
        menu.addAction(view_action)
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _load_followups(self, google_id, name):
        """Opens the side panel and fetches followup data for the specific contact."""
        self._current_google_id = google_id # Store for context
        self.fp_title.setText(f"Followups: {name}")
        self.followup_panel.show()
        
        if self._fp_worker and self._fp_worker.isRunning():
            return

        self._fp_worker = Worker(self.service.get_google_contact_followups, google_id)
        self._fp_worker.result.connect(self._on_followups_loaded)
        self._fp_worker.error.connect(self._on_error)
        self._fp_worker.start()

    def _on_followups_loaded(self, data):
        """Renders followup data into the side panel table."""
        self.followup_table.setRowCount(len(data))
        for r, row in enumerate(data):
            # SQL Query returns: OrgName(0), Date(1), Mode(2), Discussed(3), NextDate(4), Status(5), ID(6)
            for c in range(1, 7):
                val = str(row[c]) if row[c] is not None else ""
                item = NumericTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.followup_table.setItem(r, c - 1, item)
        self.followup_table.resizeColumnsToContents()
        self.fp_status.setText(f"Rows: {len(data)}")
        self._fp_worker = None

    def _load_contacts_async(self):
        if self._worker and self._worker.isRunning():
            return

        self._worker = Worker(self.service.get_contacts_for_organization, self.organization_name)
        self._worker.result.connect(self._on_contacts_loaded)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_contacts_loaded(self, contacts):
        self._contacts_cache = list(contacts)
        self._render_contacts(self._contacts_cache)
        self._worker = None

    def _render_contacts(self, rows):
        self.table.blockSignals(True)
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c in range(len(row)):
                val = str(row[c]) if row[c] is not None else ""
                item = NumericTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(r, c, item)
        self.table.setSortingEnabled(True)
        self.table.blockSignals(False)
        self.table.resizeColumnsToContents()
        self.contact_status.setText(f"Contacts: {len(rows)}")

    def _debounce_contact_search(self):
        self._search_timer.start(300)

    def _perform_contact_search(self):
        keyword = self.contact_search.text().lower().strip()
        if not keyword:
            self._render_contacts(self._contacts_cache)
            return

        filtered = [
            row for row in self._contacts_cache
            if any(keyword in str(cell).lower() for cell in row if cell)
        ]
        self._render_contacts(filtered)

    def _delete_contact(self):
        selected = self.table.selectedItems()
        if not selected: return
        row = selected[0].row()
        google_id = self.table.item(row, 0).text()
        name = f"{self.table.item(row, 1).text()} {self.table.item(row, 3).text()}"

        if QMessageBox.question(self, "Delete Contact", f"Delete {name}?") == QMessageBox.Yes:
            try:
                self.service.delete_contact(google_id)
                self._load_contacts_async()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _delete_followup(self):
        selected = self.followup_table.selectedItems()
        if not selected: return
        row = selected[0].row()
        followup_id = self.followup_table.item(row, 5).text()

        if QMessageBox.question(self, "Delete", "Delete this followup entry?") == QMessageBox.Yes:
            try:
                self.service.delete_followup(followup_id)
                if hasattr(self, '_current_google_id'):
                    name = self.fp_title.text().replace("Followups: ", "")
                    self._load_followups(self._current_google_id, name)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _add_contact(self):
        cols = ["Google ID", "First Name", "Middle Name", "Last Name", "Phone", "Email"]
        dialog = GenericCrudDialog(cols, parent=self)
        if dialog.exec() == QDialog.Accepted:
            raw = dialog.get_data()
            data = {
                "google_id": raw["Google ID"],
                "first_name": raw["First Name"],
                "middle_name": raw["Middle Name"],
                "last_name": raw["Last Name"],
                "org_name": self.organization_name,
                "phone": raw["Phone"],
                "email": raw["Email"]
            }
            try:
                self.service.create_contact(data)
                self._load_contacts_async()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _edit_contact(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected: return
        row = selected[0].row()
        
        initial = {
            "Google ID": self.table.item(row, 0).text(),
            "First Name": self.table.item(row, 1).text(),
            "Middle Name": self.table.item(row, 2).text(),
            "Last Name": self.table.item(row, 3).text(),
            "Phone": self.table.item(row, 4).text(),
            "Email": self.table.item(row, 5).text()
        }
        cols = ["First Name", "Middle Name", "Last Name", "Phone", "Email"]
        dialog = GenericCrudDialog(cols, initial_data=initial, parent=self)
        if dialog.exec() == QDialog.Accepted:
            raw = dialog.get_data()
            data = {
                "first_name": raw["First Name"],
                "middle_name": raw["Middle Name"],
                "last_name": raw["Last Name"],
                "phone": raw["Phone"],
                "email": raw["Email"]
            }
            try:
                self.service.update_contact(initial["Google ID"], data)
                self._load_contacts_async()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _add_followup(self):
        if not self._current_google_id:
            QMessageBox.warning(self, "Warning", "Please select a contact first.")
            return
        cols = ["Date", "Mode", "Discussed", "Next Date", "Status"]
        dialog = GenericCrudDialog(cols, parent=self)
        if dialog.exec() == QDialog.Accepted:
            raw = dialog.get_data()
            data = {
                "google_id": self._current_google_id,
                "date": raw["Date"],
                "mode": raw["Mode"],
                "discussed": raw["Discussed"],
                "next_date": raw["Next Date"],
                "status": raw["Status"]
            }
            try:
                self.service.create_followup(data)
                name = self.fp_title.text().replace("Followups: ", "")
                self._load_followups(self._current_google_id, name)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _edit_followup(self):
        selected = self.followup_table.selectionModel().selectedRows()
        if not selected: return
        row = selected[0].row()
        
        initial = {
            "Date": self.followup_table.item(row, 0).text(),
            "Mode": self.followup_table.item(row, 1).text(),
            "Discussed": self.followup_table.item(row, 2).text(),
            "Next Date": self.followup_table.item(row, 3).text(),
            "Status": self.followup_table.item(row, 4).text(),
            "ID": self.followup_table.item(row, 5).text()
        }
        cols = ["Date", "Mode", "Discussed", "Next Date", "Status"]
        dialog = GenericCrudDialog(cols, initial_data=initial, parent=self)
        if dialog.exec() == QDialog.Accepted:
            raw = dialog.get_data()
            data = {
                "date": raw["Date"],
                "mode": raw["Mode"],
                "discussed": raw["Discussed"],
                "next_date": raw["Next Date"],
                "status": raw["Status"]
            }
            try:
                self.service.update_followup(initial["ID"], data)
                name = self.fp_title.text().replace("Followups: ", "")
                self._load_followups(self._current_google_id, name)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _on_shortcut_add(self):
        if self.followup_table.hasFocus():
            self._add_followup()
        else:
            self._add_contact()

    def _on_shortcut_edit(self):
        if self.followup_table.hasFocus():
            self._edit_followup()
        else:
            self._edit_contact()

    def _on_shortcut_delete(self):
        if self.followup_table.hasFocus():
            self._delete_followup()
        else:
            self._delete_contact()

    def _on_error(self, err):
        QMessageBox.critical(self, "Database Error", f"Failed to load contacts: {err}")
        self._worker = None