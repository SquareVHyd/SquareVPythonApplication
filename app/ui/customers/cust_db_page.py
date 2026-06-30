from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QLabel, QAbstractItemView, QMessageBox,
    QStatusBar, QDialog, QFormLayout, QDialogButtonBox,
    QComboBox, QTextEdit, QSplitter, QHeaderView, QMenu
)
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QShortcut, QKeySequence, QAction

from app.services.cust_db_service import CustDbService
from app.ui.searchable_table import SearchableTable, NumericTableWidgetItem
from app.utils.worker_thread import Worker
from app.ui.customers.cust_followup_dialog import CustFollowupDialog


# ===========================================================================
# Form Dialog – Customer (Add / Edit)
# ===========================================================================
class CustDbFormDialog(QDialog):
    """Dialog for adding or editing a tblCustomers record."""

    def __init__(self, states: list, initial_data: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Customer Details")
        self.setMinimumWidth(480)
        self._states = states  # list of (ID, StateName)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(10)

        self.field_name    = QLineEdit(); self.field_name.setPlaceholderText("Required")
        self.field_mail    = QLineEdit()
        self.field_phone   = QLineEdit()
        self.field_address = QLineEdit()
        self.field_city    = QLineEdit()

        self.combo_state = QComboBox()
        self.combo_state.addItem("-- Select State --", None)
        for sid, sname in states:
            self.combo_state.addItem(sname, sid)

        self.field_pin        = QLineEdit()
        self.field_gstn       = QLineEdit()
        self.field_notes      = QTextEdit(); self.field_notes.setFixedHeight(72)
        self.field_attachments = QLineEdit()

        form.addRow("Customer Name *", self.field_name)
        form.addRow("Email",           self.field_mail)
        form.addRow("Phone",           self.field_phone)
        form.addRow("Address",         self.field_address)
        form.addRow("City",            self.field_city)
        form.addRow("State",           self.combo_state)
        form.addRow("PIN",             self.field_pin)
        form.addRow("GSTN Code",       self.field_gstn)
        form.addRow("Notes",           self.field_notes)
        form.addRow("Attachments",     self.field_attachments)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if initial_data:
            self._populate(initial_data)

    def _populate(self, data: dict):
        self.field_name.setText(data.get("CustomerName") or "")
        self.field_mail.setText(data.get("Mail") or "")
        self.field_phone.setText(data.get("CustomerPhone") or "")
        self.field_address.setText(data.get("CustomerAddress") or "")
        self.field_city.setText(data.get("CustomerCity") or "")
        self.field_pin.setText(str(data.get("CustomerPIN") or ""))
        self.field_gstn.setText(data.get("CustomerGSTNCode") or "")
        self.field_notes.setPlainText(data.get("CustomerNotes") or "")
        self.field_attachments.setText(data.get("Attachments") or "")
        state_id = data.get("CustomerStateID")
        if state_id is not None:
            for i in range(self.combo_state.count()):
                if self.combo_state.itemData(i) == state_id:
                    self.combo_state.setCurrentIndex(i)
                    break

    def _validate_and_accept(self):
        if not self.field_name.text().strip():
            QMessageBox.warning(self, "Validation", "Customer Name is required.")
            self.field_name.setFocus()
            return
        self.accept()

    def get_data(self) -> dict:
        pin_text = self.field_pin.text().strip()
        pin_val  = int(pin_text) if pin_text.isdigit() else None
        return {
            "customer_name":    self.field_name.text().strip(),
            "mail":             self.field_mail.text().strip() or None,
            "customer_phone":   self.field_phone.text().strip() or None,
            "customer_address": self.field_address.text().strip() or None,
            "customer_city":    self.field_city.text().strip() or None,
            "customer_state_id":self.combo_state.currentData(),
            "customer_pin":     pin_val,
            "customer_gstn_code":self.field_gstn.text().strip() or None,
            "customer_notes":   self.field_notes.toPlainText().strip() or None,
            "attachments":      self.field_attachments.text().strip() or None,
        }


# ===========================================================================
# Form Dialog – Customer Contact (Add / Edit)
# ===========================================================================
class ContactFormDialog(QDialog):
    """Dialog for adding or editing a tblCustomerContacts record."""

    def __init__(self, initial_data: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Customer Contact")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        form   = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(10)

        self.field_name        = QLineEdit(); self.field_name.setPlaceholderText("Required")
        self.field_title       = QLineEdit()
        self.field_designation = QLineEdit()
        self.field_mobile1     = QLineEdit()
        self.field_mobile2     = QLineEdit()

        form.addRow("Contact Name *",  self.field_name)
        form.addRow("Title",           self.field_title)
        form.addRow("Designation",     self.field_designation)
        form.addRow("Mobile 1",        self.field_mobile1)
        form.addRow("Mobile 2",        self.field_mobile2)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if initial_data:
            self._populate(initial_data)

    def _populate(self, data: dict):
        self.field_name.setText(data.get("CustomerContactName") or "")
        self.field_title.setText(data.get("CustomerContactTitle") or "")
        self.field_designation.setText(data.get("CustomerContactDesignation") or "")
        self.field_mobile1.setText(data.get("CustomerMobile1") or "")
        self.field_mobile2.setText(data.get("CustomerMobile2") or "")

    def _validate_and_accept(self):
        if not self.field_name.text().strip():
            QMessageBox.warning(self, "Validation", "Contact Name is required.")
            self.field_name.setFocus()
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "contact_name":        self.field_name.text().strip(),
            "contact_title":       self.field_title.text().strip() or None,
            "contact_designation": self.field_designation.text().strip() or None,
            "mobile1":             self.field_mobile1.text().strip() or None,
            "mobile2":             self.field_mobile2.text().strip() or None,
        }


# ===========================================================================
# Main Customers DB Page
# ===========================================================================
class CustDbPage(QWidget):
    """
    Page that displays and manages customers from public."tblCustomers".
    Right-click a customer row → 'View Contacts' → opens a side panel
    showing contacts from public."tblCustomerContacts".
    """

    # ------------------------------------------------------------------
    # Column indices for the CUSTOMERS table (SELECT order from repository)
    # ------------------------------------------------------------------
    COL_ID          = 0
    COL_NAME        = 1
    COL_MAIL        = 2
    COL_PHONE       = 3
    COL_ADDRESS     = 4
    COL_CITY        = 5
    COL_STATE_NAME  = 6
    COL_STATE_ID    = 7   # hidden
    COL_PIN         = 8
    COL_GSTN        = 9
    COL_NOTES       = 10
    COL_ATTACHMENTS = 11  # hidden
    COL_DATE        = 12

    CUST_HEADERS = [
        "ID", "Customer Name", "Email", "Phone",
        "Address", "City", "State", "State ID",
        "PIN", "GSTN Code", "Notes", "Attachments", "Date of Entry"
    ]

    # ------------------------------------------------------------------
    # Column indices for the CONTACTS panel
    # ------------------------------------------------------------------
    CC_COL_ID          = 0   # hidden
    CC_COL_CUST_ID     = 1   # hidden
    CC_COL_NAME        = 2
    CC_COL_TITLE       = 3
    CC_COL_DESIGNATION = 4
    CC_COL_MOBILE1     = 5
    CC_COL_MOBILE2     = 6

    CONTACT_HEADERS = [
        "ID", "CustomerID",
        "Contact Name", "Title", "Designation", "Mobile 1", "Mobile 2"
    ]

    def __init__(self):
        super().__init__()
        self.service             = CustDbService()
        self._cache              = []
        self._contacts_cache     = []
        self._states             = []
        self._current_cust_id    = None
        self._current_cust_name  = ""
        self._search_timer       = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._perform_search)
        self._worker             = None
        self._contact_worker     = None

        self._apply_styles()
        self.setup_ui()
        self._load_states_then_refresh()

    # ------------------------------------------------------------------
    # Styling
    # ------------------------------------------------------------------
    def _apply_styles(self):
        self.setStyleSheet("""
            QPushButton {
                background-color: #e0f2fe;
                color: #0c4a6e;
                border: 1px solid #bae6fd;
                padding: 6px 14px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover   { background-color: #bae6fd; }
            QPushButton:pressed { background-color: #7dd3fc; }
            QPushButton:disabled { background-color: transparent; color: #94a3b8; border: none; }
        """)

    # ------------------------------------------------------------------
    # UI Setup
    # ------------------------------------------------------------------
    def setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(4)

        # ---- Toolbar (Add / Edit / Delete / Refresh / Search) --------
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(4, 4, 4, 0)

        lbl = QLabel("Customers DB")
        lbl.setStyleSheet("font-size: 17px; font-weight: bold; padding: 2px 0;")

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search Name, Email, Phone, City, GSTN…")
        self.search_box.setMinimumWidth(240)
        self.search_box.textChanged.connect(self._debounce_search)

        self.btn_refresh = QPushButton("🔄 Refresh")
        self.btn_add     = QPushButton("➕ Add")
        self.btn_edit    = QPushButton("✏️ Edit")
        self.btn_delete  = QPushButton("🗑️ Delete")

        self.btn_refresh.clicked.connect(self.refresh_table)
        self.btn_add.clicked.connect(self._add_customer)
        self.btn_edit.clicked.connect(self._edit_customer)
        self.btn_delete.clicked.connect(self._delete_customer)

        toolbar.addWidget(lbl)
        toolbar.addStretch()
        toolbar.addWidget(self.search_box)
        toolbar.addWidget(self.btn_refresh)
        toolbar.addWidget(self.btn_add)
        toolbar.addWidget(self.btn_edit)
        toolbar.addWidget(self.btn_delete)
        root.addLayout(toolbar)

        # ---- Horizontal splitter: Customers | Contacts panel ---------
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(2)
        self.splitter.setStyleSheet("QSplitter::handle { background-color: #e2e8f0; }")

        # -- Left: Customers table
        self.cust_table = SearchableTable()
        self.cust_table.setStyleSheet(
            "QTableView { selection-background-color: #93c5fd; selection-color: #000000; } "
            "QHeaderView::section { background-color: #fce4ec; border: 1px solid #e2e8f0; }"
        )
        self.cust_table.setColumnCount(len(self.CUST_HEADERS))
        self.cust_table.setHorizontalHeaderLabels(self.CUST_HEADERS)
        self.cust_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.cust_table.setSortingEnabled(True)
        self.cust_table.hideColumn(self.COL_ID)
        self.cust_table.hideColumn(self.COL_STATE_ID)
        self.cust_table.hideColumn(self.COL_ATTACHMENTS)
        self.cust_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.cust_table.customContextMenuRequested.connect(self._show_context_menu)

        self.splitter.addWidget(self.cust_table)

        # -- Right: Contacts panel (hidden by default)
        self.contacts_panel = QWidget()
        self.contacts_panel.hide()
        cp_layout = QVBoxLayout(self.contacts_panel)
        cp_layout.setContentsMargins(4, 4, 4, 4)
        cp_layout.setSpacing(4)

        # Contacts panel header
        cp_header = QHBoxLayout()
        self.contacts_title = QLabel("Contacts")
        self.contacts_title.setStyleSheet("font-weight: bold; font-size: 14px;")

        self.btn_add_contact    = QPushButton("➕")
        self.btn_add_contact.setToolTip("Add Contact (Ctrl+N)")
        self.btn_edit_contact   = QPushButton("✏️")
        self.btn_edit_contact.setToolTip("Edit Contact (Ctrl+E)")
        self.btn_del_contact    = QPushButton("🗑️")
        self.btn_del_contact.setToolTip("Delete Contact (Del)")
        self.btn_followup       = QPushButton("📋 Follow Up")
        self.btn_followup.setToolTip("View / manage follow-ups for selected contact")
        self.btn_close_contacts = QPushButton("❌")
        self.btn_close_contacts.setToolTip("Close panel")
        self.btn_close_contacts.setFixedWidth(32)

        self.btn_add_contact.clicked.connect(self._add_contact)
        self.btn_edit_contact.clicked.connect(self._edit_contact)
        self.btn_del_contact.clicked.connect(self._delete_contact)
        self.btn_followup.clicked.connect(self._open_followup)
        self.btn_close_contacts.clicked.connect(self.contacts_panel.hide)

        cp_header.addWidget(self.contacts_title)
        cp_header.addStretch()
        cp_header.addWidget(self.btn_followup)
        cp_header.addWidget(self.btn_add_contact)
        cp_header.addWidget(self.btn_edit_contact)
        cp_header.addWidget(self.btn_del_contact)
        cp_header.addWidget(self.btn_close_contacts)
        cp_layout.addLayout(cp_header)

        # Contacts table
        self.contacts_table = SearchableTable()
        self.contacts_table.setStyleSheet(
            "QTableView { selection-background-color: #93c5fd; selection-color: #000000; } "
            "QHeaderView::section { background-color: #e0f7fa; border: 1px solid #e2e8f0; }"
        )
        self.contacts_table.setColumnCount(len(self.CONTACT_HEADERS))
        self.contacts_table.setHorizontalHeaderLabels(self.CONTACT_HEADERS)
        self.contacts_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.contacts_table.setSortingEnabled(True)
        self.contacts_table.hideColumn(self.CC_COL_ID)
        self.contacts_table.hideColumn(self.CC_COL_CUST_ID)
        self.contacts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        cp_layout.addWidget(self.contacts_table)

        self.contacts_status = QLabel("Contacts: 0")
        self.contacts_status.setStyleSheet("color: #64748b; font-size: 12px;")
        cp_layout.addWidget(self.contacts_status)

        self.splitter.addWidget(self.contacts_panel)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 2)
        root.addWidget(self.splitter, stretch=1)

        # ---- Status bar ----------------------------------------------
        self.status_bar = QStatusBar()
        root.addWidget(self.status_bar)

        # ---- Keyboard shortcuts -------------------------------------
        QShortcut(QKeySequence("Ctrl+R"), self, activated=self.refresh_table)
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self._add_customer)
        QShortcut(QKeySequence("Ctrl+E"), self, activated=self._edit_customer)
        QShortcut(QKeySequence.Delete,    self, activated=self._delete_customer)
        QShortcut(QKeySequence.Find,      self, activated=lambda: self.search_box.setFocus())

    # ------------------------------------------------------------------
    # Context Menu (right-click on customer row)
    # ------------------------------------------------------------------
    def _show_context_menu(self, pos: QPoint):
        item = self.cust_table.itemAt(pos)
        if not item:
            return
        row = item.row()
        cust_id_item = self.cust_table.item(row, self.COL_ID)
        name_item    = self.cust_table.item(row, self.COL_NAME)
        if not cust_id_item or not name_item:
            return

        cust_id   = int(cust_id_item.text())
        cust_name = name_item.text()

        menu = QMenu(self)
        view_action = QAction(f"👥 View Contacts for {cust_name}", self)
        view_action.triggered.connect(lambda: self._load_contacts(cust_id, cust_name))
        menu.addAction(view_action)
        menu.exec(self.cust_table.viewport().mapToGlobal(pos))

    # ------------------------------------------------------------------
    # Contacts Panel
    # ------------------------------------------------------------------
    def _load_contacts(self, customer_id: int, customer_name: str):
        """Show the contacts side panel and load contacts for the given customer."""
        self._current_cust_id   = customer_id
        self._current_cust_name = customer_name
        self.contacts_title.setText(f"Contacts – {customer_name}")
        self.contacts_panel.show()

        if self._contact_worker and self._contact_worker.isRunning():
            return
        self._contact_worker = Worker(self.service.get_contacts_by_customer, customer_id)
        self._contact_worker.result.connect(self._on_contacts_loaded)
        self._contact_worker.error.connect(self._on_contacts_error)
        self._contact_worker.start()

    def _on_contacts_loaded(self, rows):
        self._contacts_cache = list(rows)
        self._render_contacts(self._contacts_cache)
        self._contact_worker = None

    def _on_contacts_error(self, err):
        QMessageBox.critical(self, "Error", f"Failed to load contacts:\n{err}")
        self._contact_worker = None

    def _render_contacts(self, rows):
        self.contacts_table.setSortingEnabled(False)
        self.contacts_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c in range(len(self.CONTACT_HEADERS)):
                val  = str(row[c]) if row[c] is not None else ""
                item = NumericTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.contacts_table.setItem(r, c, item)
        self.contacts_table.setSortingEnabled(True)
        self.contacts_status.setText(f"Contacts: {len(rows)}")

    # ------------------------------------------------------------------
    # Contact CRUD helpers
    # ------------------------------------------------------------------
    def _selected_contact_row(self):
        rows = self.contacts_table.selectionModel().selectedRows()
        return rows[0].row() if rows else -1

    def _contact_row_to_dict(self, row: int) -> dict:
        def cell(col):
            it = self.contacts_table.item(row, col)
            return it.text() if it else ""
        return {
            "ID":                        cell(self.CC_COL_ID),
            "CustomerContactName":       cell(self.CC_COL_NAME),
            "CustomerContactTitle":      cell(self.CC_COL_TITLE),
            "CustomerContactDesignation":cell(self.CC_COL_DESIGNATION),
            "CustomerMobile1":           cell(self.CC_COL_MOBILE1),
            "CustomerMobile2":           cell(self.CC_COL_MOBILE2),
        }

    def _add_contact(self):
        if not self._current_cust_id:
            QMessageBox.warning(self, "Warning", "Please select a customer first (right-click → View Contacts).")
            return
        dlg = ContactFormDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            data["customer_id"] = self._current_cust_id
            try:
                self.service.create_contact(data)
                self._load_contacts(self._current_cust_id, self._current_cust_name)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _edit_contact(self):
        row = self._selected_contact_row()
        if row == -1:
            QMessageBox.information(self, "Edit", "Please select a contact to edit.")
            return
        initial    = self._contact_row_to_dict(row)
        contact_id = self.contacts_table.item(row, self.CC_COL_ID).text()
        dlg = ContactFormDialog(initial_data=initial, parent=self)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            try:
                self.service.update_contact(int(contact_id), data)
                self._load_contacts(self._current_cust_id, self._current_cust_name)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _delete_contact(self):
        row = self._selected_contact_row()
        if row == -1:
            QMessageBox.information(self, "Delete", "Please select a contact to delete.")
            return
        name       = self.contacts_table.item(row, self.CC_COL_NAME).text()
        contact_id = self.contacts_table.item(row, self.CC_COL_ID).text()
        reply = QMessageBox.question(
            self, "Delete Contact",
            f"Delete contact:\n\n  {name}\n\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                self.service.delete_contact(int(contact_id))
                self._load_contacts(self._current_cust_id, self._current_cust_name)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _open_followup(self):
        """Opens the Follow-up dialog for the selected contact."""
        row = self._selected_contact_row()
        if row == -1:
            QMessageBox.information(
                self, "Follow Up",
                "Please select a contact from the panel to view follow-ups."
            )
            return
        contact_id   = int(self.contacts_table.item(row, self.CC_COL_ID).text())
        contact_name = self.contacts_table.item(row, self.CC_COL_NAME).text()
        dlg = CustFollowupDialog(contact_id, contact_name, parent=self)
        dlg.exec()

    # ------------------------------------------------------------------
    # Data Loading
    # ------------------------------------------------------------------
    def _load_states_then_refresh(self):
        try:
            self._states = self.service.get_all_states()
        except Exception as e:
            self._states = []
            QMessageBox.warning(self, "Warning", f"Could not load states list:\n{e}")
        self.refresh_table()

    def refresh_table(self):
        if self._worker and self._worker.isRunning():
            return
        self.status_bar.showMessage("Loading customers from DB…")
        self.btn_refresh.setEnabled(False)
        self._worker = Worker(self.service.get_all_customers)
        self._worker.result.connect(self._on_data_loaded)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_data_loaded(self, rows):
        self._cache = list(rows)
        self._render(self._cache)
        self.status_bar.showMessage(f"Loaded {len(rows)} customer(s)", 5000)
        self.btn_refresh.setEnabled(True)
        self._worker = None

    def _on_error(self, err):
        QMessageBox.critical(self, "Database Error", f"Failed to load customers:\n{err}")
        self.status_bar.clearMessage()
        self.btn_refresh.setEnabled(True)
        self._worker = None

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def _render(self, rows):
        self.cust_table.setSortingEnabled(False)
        self.cust_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c in range(len(self.CUST_HEADERS)):
                val  = str(row[c]) if row[c] is not None else ""
                item = NumericTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.cust_table.setItem(r, c, item)
        self.cust_table.setSortingEnabled(True)
        self.cust_table.resizeColumnsToContents()

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------
    def _debounce_search(self):
        self._search_timer.start(300)

    def _perform_search(self):
        keyword = self.search_box.text().lower().strip()
        if not keyword:
            self._render(self._cache)
            return
        visible_cols = [
            self.COL_NAME, self.COL_MAIL, self.COL_PHONE,
            self.COL_ADDRESS, self.COL_CITY, self.COL_STATE_NAME,
            self.COL_PIN, self.COL_GSTN, self.COL_NOTES
        ]
        filtered = [
            row for row in self._cache
            if any(keyword in str(row[c]).lower() for c in visible_cols if row[c])
        ]
        self._render(filtered)

    # ------------------------------------------------------------------
    # Customer CRUD
    # ------------------------------------------------------------------
    def _selected_row(self):
        rows = self.cust_table.selectionModel().selectedRows()
        return rows[0].row() if rows else -1

    def _row_to_initial_data(self, row: int) -> dict:
        def cell(col):
            it = self.cust_table.item(row, col)
            return it.text() if it else ""

        state_id_text = cell(self.COL_STATE_ID)
        state_id = int(state_id_text) if state_id_text.isdigit() else None
        return {
            "ID":              cell(self.COL_ID),
            "CustomerName":    cell(self.COL_NAME),
            "Mail":            cell(self.COL_MAIL),
            "CustomerPhone":   cell(self.COL_PHONE),
            "CustomerAddress": cell(self.COL_ADDRESS),
            "CustomerCity":    cell(self.COL_CITY),
            "CustomerStateID": state_id,
            "CustomerPIN":     cell(self.COL_PIN),
            "CustomerGSTNCode":cell(self.COL_GSTN),
            "CustomerNotes":   cell(self.COL_NOTES),
            "Attachments":     cell(self.COL_ATTACHMENTS),
        }

    def _add_customer(self):
        dlg = CustDbFormDialog(self._states, parent=self)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            try:
                self.service.create_customer(data)
                self.refresh_table()
                self.status_bar.showMessage("Customer added successfully.", 4000)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _edit_customer(self):
        row = self._selected_row()
        if row == -1:
            QMessageBox.information(self, "Edit", "Please select a customer to edit.")
            return
        initial     = self._row_to_initial_data(row)
        customer_id = self.cust_table.item(row, self.COL_ID).text()
        dlg = CustDbFormDialog(self._states, initial_data=initial, parent=self)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            try:
                self.service.update_customer(int(customer_id), data)
                self.refresh_table()
                self.status_bar.showMessage("Customer updated successfully.", 4000)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _delete_customer(self):
        row = self._selected_row()
        if row == -1:
            QMessageBox.information(self, "Delete", "Please select a customer to delete.")
            return
        name        = self.cust_table.item(row, self.COL_NAME).text()
        customer_id = self.cust_table.item(row, self.COL_ID).text()
        reply = QMessageBox.question(
            self, "Delete Customer",
            f"Are you sure you want to delete:\n\n  {name}\n\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                self.service.delete_customer(int(customer_id))
                self.contacts_panel.hide()
                self.refresh_table()
                self.status_bar.showMessage(f"Deleted customer: {name}", 4000)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
