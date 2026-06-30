"""
cust_followup_dialog.py
-----------------------
A standalone QDialog that shows and manages follow-up records from
public."tblCustomerFollowup" for a specific tblCustomerContacts row.

Open it like:
    dlg = CustFollowupDialog(contact_id, contact_name, parent=self)
    dlg.exec()          # modal
    # or
    dlg.show()          # modeless
"""
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QAbstractItemView, QMessageBox, QStatusBar,
    QFormLayout, QDialogButtonBox, QTextEdit, QComboBox,
    QHeaderView, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QDate, QTimer
from PySide6.QtGui import QShortcut, QKeySequence, QFont

# PySide6 date-edit widget
from PySide6.QtWidgets import QDateEdit

from app.services.cust_db_service import CustDbService
from app.ui.searchable_table import SearchableTable, NumericTableWidgetItem
from app.utils.worker_thread import Worker


# ============================================================================
# Follow-up Form Dialog (Add / Edit)
# ============================================================================
class FollowupFormDialog(QDialog):
    """Small dialog to add or edit a single follow-up entry."""

    MODE_OPTIONS = [
        "Phone Call",
        "Email",
        "In-Person Visit",
        "Video Call",
        "WhatsApp",
        "Other",
    ]

    def __init__(self, initial_data: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Follow-up Entry")
        self.setMinimumWidth(440)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(10)

        # Date of followup
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd-MM-yyyy")
        self.date_edit.setDate(QDate.currentDate())

        # Mode of contact
        self.combo_mode = QComboBox()
        for m in self.MODE_OPTIONS:
            self.combo_mode.addItem(m)

        # What discussed
        self.field_discussed = QTextEdit()
        self.field_discussed.setPlaceholderText("Enter discussion summary…")
        self.field_discussed.setFixedHeight(100)

        form.addRow("Date of Follow-up *", self.date_edit)
        form.addRow("Mode of Contact",      self.combo_mode)
        form.addRow("What Discussed",       self.field_discussed)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if initial_data:
            self._populate(initial_data)

    def _populate(self, data: dict):
        # Date
        date_val = data.get("DateOfFollowup")
        if date_val:
            if hasattr(date_val, "date"):           # datetime object
                date_val = date_val.date()
            if hasattr(date_val, "year"):            # date object
                self.date_edit.setDate(QDate(date_val.year, date_val.month, date_val.day))
            else:                                    # string fallback
                qd = QDate.fromString(str(date_val)[:10], "yyyy-MM-dd")
                if qd.isValid():
                    self.date_edit.setDate(qd)

        # Mode
        mode = data.get("ModeOfContact") or ""
        idx  = self.combo_mode.findText(mode, Qt.MatchFixedString)
        if idx >= 0:
            self.combo_mode.setCurrentIndex(idx)
        else:
            # Add custom value if it doesn't match the preset list
            self.combo_mode.addItem(mode)
            self.combo_mode.setCurrentText(mode)

        # Discussed
        self.field_discussed.setPlainText(data.get("WhatDiscussed") or "")

    def _validate_and_accept(self):
        if not self.date_edit.date().isValid():
            QMessageBox.warning(self, "Validation", "A valid date is required.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "date_of_followup": self.date_edit.date().toString("yyyy-MM-dd"),
            "mode_of_contact":  self.combo_mode.currentText().strip() or None,
            "what_discussed":   self.field_discussed.toPlainText().strip() or None,
        }


# ============================================================================
# Main Follow-up Dialog Window
# ============================================================================
class CustFollowupDialog(QDialog):
    """
    Modal dialog that shows all follow-up records for a single customer contact
    and provides full CRUD (Add / Edit / Delete).

    Usage:
        dlg = CustFollowupDialog(contact_id=42, contact_name="John Doe", parent=self)
        dlg.exec()
    """

    # Column indices matching the SELECT order in repository
    COL_ID         = 0   # hidden
    COL_CONTACT_ID = 1   # hidden
    COL_DATE       = 2
    COL_MODE       = 3
    COL_DISCUSSED  = 4
    COL_SYS_DATE   = 5

    HEADERS = ["ID", "ContactID", "Date", "Mode", "What Discussed", "Recorded On"]

    def __init__(self, contact_id: int, contact_name: str, parent=None):
        super().__init__(parent)
        self.contact_id   = contact_id
        self.contact_name = contact_name
        self.service      = CustDbService()
        self._cache       = []
        self._worker      = None

        self.setWindowTitle(f"Follow-ups — {contact_name}")
        self.setMinimumSize(820, 480)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self._setup_ui()
        self.refresh_table()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 8)
        root.setSpacing(8)

        # ── Header bar ────────────────────────────────────────────────
        header = QHBoxLayout()

        icon_lbl = QLabel("📋")
        icon_lbl.setFont(QFont("Segoe UI Emoji", 20))

        info_block = QVBoxLayout()
        title_lbl = QLabel(f"Follow-ups")
        title_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #0c4a6e;")
        sub_lbl   = QLabel(f"Contact: {self.contact_name}")
        sub_lbl.setStyleSheet("font-size: 13px; color: #64748b;")
        info_block.addWidget(title_lbl)
        info_block.addWidget(sub_lbl)
        info_block.setSpacing(0)

        header.addWidget(icon_lbl)
        header.addSpacing(8)
        header.addLayout(info_block)
        header.addStretch()

        # Action buttons
        btn_style = """
            QPushButton {
                background-color: #e0f2fe; color: #0c4a6e;
                border: 1px solid #bae6fd; padding: 6px 16px;
                border-radius: 4px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover   { background-color: #bae6fd; }
            QPushButton:pressed { background-color: #7dd3fc; }
            QPushButton:disabled { background-color: transparent; color: #94a3b8; border: none; }
        """

        self.btn_refresh = QPushButton("🔄 Refresh")
        self.btn_add     = QPushButton("➕ Add")
        self.btn_edit    = QPushButton("✏️ Edit")
        self.btn_delete  = QPushButton("🗑️ Delete")
        self.btn_close   = QPushButton("✖️ Close")

        for btn in (self.btn_refresh, self.btn_add, self.btn_edit,
                    self.btn_delete, self.btn_close):
            btn.setStyleSheet(btn_style)

        self.btn_refresh.clicked.connect(self.refresh_table)
        self.btn_add.clicked.connect(self._add_followup)
        self.btn_edit.clicked.connect(self._edit_followup)
        self.btn_delete.clicked.connect(self._delete_followup)
        self.btn_close.clicked.connect(self.accept)

        header.addWidget(self.btn_refresh)
        header.addWidget(self.btn_add)
        header.addWidget(self.btn_edit)
        header.addWidget(self.btn_delete)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #e2e8f0;")

        root.addLayout(header)
        root.addWidget(sep)

        # ── Table ─────────────────────────────────────────────────────
        self.table = SearchableTable()
        self.table.setStyleSheet(
            "QTableView { selection-background-color: #93c5fd; selection-color: #000000; } "
            "QHeaderView::section { background-color: #e0f7fa; border: 1px solid #e2e8f0; "
            "padding: 4px; font-weight: bold; }"
        )
        self.table.setColumnCount(len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSortingEnabled(True)
        self.table.hideColumn(self.COL_ID)
        self.table.hideColumn(self.COL_CONTACT_ID)

        # Stretch "What Discussed" column; others auto-size
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(self.COL_DATE,      QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(self.COL_MODE,      QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(self.COL_DISCUSSED, QHeaderView.Stretch)
        hdr.setSectionResizeMode(self.COL_SYS_DATE,  QHeaderView.ResizeToContents)

        # Double-click to edit
        self.table.doubleClicked.connect(self._edit_followup)

        root.addWidget(self.table, stretch=1)

        # ── Status bar + Close button row ────────────────────────────
        footer = QHBoxLayout()
        self.status_bar = QStatusBar()
        self.status_bar.setSizeGripEnabled(False)
        footer.addWidget(self.status_bar, stretch=1)
        footer.addWidget(self.btn_close)
        root.addLayout(footer)

        # Keyboard shortcuts
        QShortcut(QKeySequence("Ctrl+R"), self, activated=self.refresh_table)
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self._add_followup)
        QShortcut(QKeySequence("Ctrl+E"), self, activated=self._edit_followup)
        QShortcut(QKeySequence.Delete,    self, activated=self._delete_followup)
        QShortcut(QKeySequence("Escape"), self, activated=self.accept)

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------
    def refresh_table(self):
        if self._worker and self._worker.isRunning():
            return
        self.status_bar.showMessage("Loading follow-ups…")
        self.btn_refresh.setEnabled(False)
        self._worker = Worker(self.service.get_followups_by_contact, self.contact_id)
        self._worker.result.connect(self._on_loaded)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_loaded(self, rows):
        self._cache = list(rows)
        self._render(self._cache)
        count = len(rows)
        self.status_bar.showMessage(
            f"{count} follow-up{'s' if count != 1 else ''} found", 5000
        )
        self.btn_refresh.setEnabled(True)
        self._worker = None

    def _on_error(self, err):
        QMessageBox.critical(self, "Error", f"Failed to load follow-ups:\n{err}")
        self.status_bar.clearMessage()
        self.btn_refresh.setEnabled(True)
        self._worker = None

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def _render(self, rows):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                # Format datetime objects nicely
                if hasattr(val, "strftime"):
                    text = val.strftime("%d-%m-%Y %H:%M") if hasattr(val, "hour") else val.strftime("%d-%m-%Y")
                else:
                    text = str(val) if val is not None else ""
                item = NumericTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(r, c, item)
        self.table.setSortingEnabled(True)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _selected_row(self) -> int:
        rows = self.table.selectionModel().selectedRows()
        return rows[0].row() if rows else -1

    def _row_to_initial_data(self, row: int) -> dict:
        def cell(col):
            it = self.table.item(row, col)
            return it.text() if it else ""

        # Pull raw datetime from cache for the date field
        raw_row   = self._cache[row] if row < len(self._cache) else None
        date_raw  = raw_row[self.COL_DATE] if raw_row else None

        return {
            "ID":              cell(self.COL_ID),
            "DateOfFollowup":  date_raw,
            "ModeOfContact":   cell(self.COL_MODE),
            "WhatDiscussed":   cell(self.COL_DISCUSSED),
        }

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    def _add_followup(self):
        dlg = FollowupFormDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            data["contact_id"] = self.contact_id
            try:
                self.service.create_followup(data)
                self.refresh_table()
                self.status_bar.showMessage("Follow-up added.", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _edit_followup(self):
        row = self._selected_row()
        if row == -1:
            QMessageBox.information(self, "Edit", "Please select a follow-up entry to edit.")
            return
        initial     = self._row_to_initial_data(row)
        followup_id = self.table.item(row, self.COL_ID).text()

        dlg = FollowupFormDialog(initial_data=initial, parent=self)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            try:
                self.service.update_followup(int(followup_id), data)
                self.refresh_table()
                self.status_bar.showMessage("Follow-up updated.", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _delete_followup(self):
        row = self._selected_row()
        if row == -1:
            QMessageBox.information(self, "Delete", "Please select a follow-up entry to delete.")
            return

        date_text   = self.table.item(row, self.COL_DATE).text()
        followup_id = self.table.item(row, self.COL_ID).text()

        reply = QMessageBox.question(
            self, "Delete Follow-up",
            f"Delete the follow-up entry on:\n\n  {date_text}\n\n"
            "This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                self.service.delete_followup(int(followup_id))
                self.refresh_table()
                self.status_bar.showMessage("Follow-up deleted.", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
