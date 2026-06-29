import pyodbc
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLineEdit, QLabel, QAbstractItemView, QMessageBox, QMenu, QStatusBar, QApplication,
    QDialog, QHeaderView, QSplitter, QScrollArea, QGroupBox, QFormLayout, QComboBox
)
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QShortcut, QKeySequence, QAction

from app.services.quotation_service import QuotationService
from app.ui.quotations.quotation_form import QuotationForm
from app.ui.quotations.quotation_ctc_dialog import QuotationCTCDialog
from app.ui.quotations.module_items.module_items_viewer_dialog import ModuleItemsViewerDialog
from app.ui.quotations.quotation_preview_dialog import QuotationPreviewDialog
from app.ui.quotations.reports.test_reports_page import TestReportsPage
from app.ui.searchable_table import SearchableTable, NumericTableWidgetItem
from app.utils.worker_thread import Worker


class QuotationPage(QWidget):
    def __init__(self, parent_quotation_details_page=None):
        super().__init__()
        self.service = QuotationService()
        self._cache = []
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._perform_search)
        self._worker = None
        self.parent_quotation_details_page = parent_quotation_details_page # Store reference to QuotationDetailsPage
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
        title = QLabel("Quotations Management")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search by Customer, Project, or Ref No...")
        self.search_box.textChanged.connect(self._debounce_search)

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh_table)
        
        self.items_btn = QPushButton("📦 Items")
        self.items_btn.clicked.connect(self._show_items_viewer)

        self.add_btn = QPushButton("➕ Add")
        self.add_btn.setToolTip("(Ctrl+N)")
        self.add_btn.clicked.connect(self.add_quotation)

        self.edit_btn = QPushButton("✏️ Edit")
        self.edit_btn.setToolTip("(Ctrl+E)")
        self.edit_btn.clicked.connect(self.edit_quotation)

        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #fee2e2;
                        color: #991b1b;
                        border: 1px solid #fecaca;
                        padding: 6px 12px;
                        border-radius: 4px;
                        font-weight: bold;
                        font-size: 13px;
                    }
                    QPushButton:hover { background-color: #fecaca; }
                    QPushButton:pressed { background-color: #fca5a5; }
                    QPushButton:disabled { background-color: transparent; color: #94a3b8; border: none; }
                """)
        self.delete_btn.setToolTip("(Delete)")
        self.delete_btn.clicked.connect(self.delete_quotation)
        
        self.copy_btn = QPushButton("📋 Copy")
        self.copy_btn.clicked.connect(self.copy_quotation)
        
        self.paste_btn = QPushButton("📋 Paste")
        self.paste_btn.clicked.connect(self.paste_quotation)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.search_box)
        header.addWidget(self.refresh_btn)
        header.addWidget(self.items_btn)
        header.addWidget(self.add_btn)
        header.addWidget(self.edit_btn)
        header.addWidget(self.delete_btn)
        header.addWidget(self.copy_btn)
        header.addWidget(self.paste_btn)
        layout.addLayout(header)

        # Table
        self.table = SearchableTable()
        self.table.setStyleSheet("QTableView { selection-background-color: #93c5fd; selection-color: #000000; }") # Keep existing style
        self.table.setColumnCount(14)
        self.table.setHorizontalHeaderLabels([
            "ID", "Customer ID", "Customer", "Req. Date", "Quote Date", "Ref No", 
            "Subject", "Project", "Revision", "Contact", "Prepared By", "Status", "BaseQuoteID", "RevisionNo"
        ])
        self.table.hideColumn(0) # Hide Quote ID
        self.table.hideColumn(1) # Hide Customer ID
        self.table.hideColumn(12) # Hide BaseQuoteID
        self.table.hideColumn(13) # Hide RevisionNo
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSortingEnabled(True)
        
        # Right-click context menu
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        
        # Track selection to enable/disable Panels button
        self.table.itemSelectionChanged.connect(self._on_selection_changed)

        # Double click to edit entire quotation
        self.table.itemDoubleClicked.connect(self.edit_quotation)
        
        layout.addWidget(self.table)

        self.status_bar = QStatusBar()
        layout.addWidget(self.status_bar)

        QShortcut(QKeySequence("Ctrl+R"), self, activated=self.refresh_table)
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self.add_quotation)
        QShortcut(QKeySequence("Ctrl+E"), self, activated=self.edit_quotation)
        QShortcut(QKeySequence("Delete"), self, activated=self.delete_quotation)
        QShortcut(QKeySequence("Ctrl+F"), self, activated=lambda: self.search_box.setFocus())

    def _on_selection_changed(self):
        """Enables the Panels button and updates the detail views."""
        selected = self.table.selectionModel().selectedRows()
        is_single_selection = len(selected) == 1
        if hasattr(self.parent_quotation_details_page, 'update_panels_button_state'):
            self.parent_quotation_details_page.update_panels_button_state(is_single_selection)
            
        if is_single_selection:
            row = selected[0].row()
            quote_id = int(self.table.item(row, 0).text())
            base_quote_id = int(self.table.item(row, 12).text()) if self.table.item(row, 12) and self.table.item(row, 12).text() else quote_id
            
            # Populate sidebar combo
            if hasattr(self.parent_quotation_details_page, 'populate_revisions'):
                self.parent_quotation_details_page.populate_revisions(base_quote_id, quote_id)

    def _on_table_revision_changed(self, row, combo):
        quote_id = combo.currentData()
        quote_data = self.service.get_quotation_by_id(quote_id)
        if not quote_data: return
        
        self.table.blockSignals(True)
        self.table.item(row, 0).setText(str(quote_data["ID"]))
        
        def _fmt_date(d):
            return d.strftime('%Y-%m-%d') if d else ""
        
        if self.table.item(row, 3): self.table.item(row, 3).setText(_fmt_date(quote_data.get("DateOfRequest")))
        if self.table.item(row, 4): self.table.item(row, 4).setText(_fmt_date(quote_data.get("Date_Quote")))
        if self.table.item(row, 5): self.table.item(row, 5).setText(str(quote_data.get("QuoteRereceNo", "")))
        if self.table.item(row, 6): self.table.item(row, 6).setText(str(quote_data.get("QuoteSubject", "")))
        if self.table.item(row, 7): self.table.item(row, 7).setText(str(quote_data.get("QuoteProjectName", "")))
        if self.table.item(row, 11): self.table.item(row, 11).setText(str(quote_data.get("QuoteStatus", "")))
        if self.table.item(row, 13): self.table.item(row, 13).setText(str(quote_data.get("RevisionNo", "")))
        
        self.table.blockSignals(False)
        
        # Sync with sidebar if this row is selected
        selected = self.table.selectionModel().selectedRows()
        if len(selected) == 1 and selected[0].row() == row:
            if hasattr(self.parent_quotation_details_page, 'revision_combo'):
                cb = self.parent_quotation_details_page.revision_combo
                cb.blockSignals(True)
                for i in range(cb.count()):
                    if cb.itemData(i) == quote_id:
                        cb.setCurrentIndex(i)
                        break
                cb.blockSignals(False)
                self.parent_quotation_details_page._on_revision_selected(cb.currentIndex())

    def update_selected_row_with_quote(self, quote_id):
        """Updates the selected row with the data of the specified quotation revision."""
        selected = self.table.selectionModel().selectedRows()
        if len(selected) == 1:
            row = selected[0].row()
            quote_data = self.service.get_quotation_by_id(quote_id)
            if quote_data:
                self.table.blockSignals(True)
                self.table.item(row, 0).setText(str(quote_data["ID"]))
                
                def _fmt_date(d):
                    return d.strftime('%Y-%m-%d') if d else ""
                
                if self.table.item(row, 3): self.table.item(row, 3).setText(_fmt_date(quote_data.get("DateOfRequest")))
                if self.table.item(row, 4): self.table.item(row, 4).setText(_fmt_date(quote_data.get("Date_Quote")))
                if self.table.item(row, 5): self.table.item(row, 5).setText(str(quote_data.get("QuoteRereceNo", "")))
                if self.table.item(row, 6): self.table.item(row, 6).setText(str(quote_data.get("QuoteSubject", "")))
                if self.table.item(row, 7): self.table.item(row, 7).setText(str(quote_data.get("QuoteProjectName", "")))
                if self.table.item(row, 11): self.table.item(row, 11).setText(str(quote_data.get("QuoteStatus", "")))
                if self.table.item(row, 13): self.table.item(row, 13).setText(str(quote_data.get("RevisionNo", "")))
                
                combo = self.table.cellWidget(row, 8)
                if combo:
                    combo.blockSignals(True)
                    for i in range(combo.count()):
                        if combo.itemData(i) == quote_id:
                            combo.setCurrentIndex(i)
                            break
                    combo.blockSignals(False)
                self.table.blockSignals(False)

    def add_quotation(self):
        """Opens the form to add a new quotation."""
        dialog = QuotationForm(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                self.service.create_quotation(**data)
                QMessageBox.information(self, "Success", "Quotation created successfully.")
                self.refresh_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create quotation: {e}")

    def edit_quotation(self):
        """Opens the form to edit the selected quotation."""
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Selection Required", "Please select a quotation to edit.")
            return
        
        row = selected[0].row()
        # Build data dictionary from table row
        quot_id = int(self.table.item(row, 0).text())
        current_data = {
            "id": quot_id,
            "customer_id": int(self.table.item(row, 1).text()),
            "req_date": self.table.item(row, 3).text(),
            "quote_date": self.table.item(row, 4).text(),
            "ref_no": self.table.item(row, 5).text(),
            "subject": self.table.item(row, 6).text(),
            "project": self.table.item(row, 7).text(),
            "contact": self.table.item(row, 9).text(),
            "prepared_by": self.table.item(row, 10).text(),
            "status": self.table.item(row, 11).text(),
        }

        dialog = QuotationForm(self, quotation_data=current_data)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                self.service.update_quotation(quot_id, **data)
                QMessageBox.information(self, "Success", "Quotation updated successfully.")
                self.refresh_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update quotation: {e}")

    def delete_quotation(self):
        """Deletes the selected quotation(s)."""
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Selection Required", "Please select quotation(s) to delete.")
            return

        if QMessageBox.question(self, "Confirm Delete", 
                               f"Are you sure you want to delete {len(selected)} quotation(s)?",
                               QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            try:
                for index in selected:
                    quot_id = int(self.table.item(index.row(), 0).text())
                    self.service.delete_quotation(quot_id)
                QMessageBox.information(self, "Deleted", "Quotation(s) removed successfully.")
                self.refresh_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete: {e}")

    def copy_quotation(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Selection Required", "Please select a quotation to copy.")
            return
        row = selected[0].row()
        quote_id = int(self.table.item(row, 0).text())
        project_name = self.table.item(row, 7).text()
        
        self.service.clipboard["type"] = "quotation"
        self.service.clipboard["id"] = quote_id
        self.service.clipboard["name"] = project_name
        QMessageBox.information(self, "Copied", f"Quotation '{project_name}' copied to clipboard.")

    def paste_quotation(self):
        if self.service.clipboard.get("type") != "quotation" or not self.service.clipboard.get("id"):
            QMessageBox.warning(self, "Clipboard Empty", "No quotation in clipboard to paste.")
            return
            
        try:
            self.service.copy_quotation(self.service.clipboard["id"])
            QMessageBox.information(self, "Pasted", "Quotation pasted successfully.")
            self.refresh_table()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to paste quotation: {e}")

    def show_panels(self):
        """Opens the Panel Manager for the selected quotation."""
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return
            
        row = selected[0].row()
        quote_id = int(self.table.item(row, 0).text())
        project_name = self.table.item(row, 7).text()
        
        if hasattr(self.parent_quotation_details_page, 'open_panel_view'):
            self.parent_quotation_details_page.open_panel_view(quote_id, project_name)

    def _show_items_viewer(self):
        """Opens the Module Items Viewer for the selected quotation."""
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Selection Required", "Please select a quotation to view its items.")
            return
        row = selected[0].row()
        quote_id = int(self.table.item(row, 0).text())
        # Call the show_items method of the parent QuotationDetailsPage/Window
        self.parent_quotation_details_page.show_items()

    def refresh_table(self):
        if self._worker: return
        self.status_bar.showMessage("Fetching quotations...")
        self._worker = Worker(self.service.get_all_quotations)
        self._worker.result.connect(self._on_data_loaded)
        self._worker.start()

    def _on_data_loaded(self, rows):
        self._cache = list(rows)
        self._render(self._cache)
        self.status_bar.showMessage(f"Loaded {len(rows)} quotations", 5000)
        self._worker = None

    def _render(self, rows):
        self.table.blockSignals(True)
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        
        grouped_revisions = self.service.get_all_revisions_grouped()
        
        for r, row in enumerate(rows):
            id_val = row[0]
            base_quote_id = row[11] if row[11] else id_val
            
            mappings = [
                (0, row[0]), (1, row[1]), (2, row[2]), (3, row[3]), (4, row[4]), 
                (5, row[5]), (6, row[6]), (7, row[7]), (9, row[8]), (10, row[9]), 
                (11, row[10]), (12, row[11]), (13, row[12])
            ]
            for col_idx, val in mappings:
                val_str = str(val) if val is not None else ""
                item = NumericTableWidgetItem(val_str)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(r, col_idx, item)
                
            # Create Revision Combo Box in col 8
            combo = QComboBox()
            revisions = grouped_revisions.get(base_quote_id, [])
            active_idx = 0
            for i, rev in enumerate(revisions):
                text = f"Rev {rev.get('RevisionNo', 0)} ({rev.get('QuoteRereceNo', '')})"
                combo.addItem(text, rev.get("ID"))
                if rev.get("ID") == id_val:
                    active_idx = i
            combo.setCurrentIndex(active_idx)
            combo.currentIndexChanged.connect(lambda idx, c=combo, tr_row=r: self._on_table_revision_changed(tr_row, c))
            
            self.table.setCellWidget(r, 8, combo)

        self.table.setSortingEnabled(True)
        self.table.blockSignals(False)
        self.table.resizeColumnsToContents()

    def _debounce_search(self):
        self._search_timer.start(300)

    def _perform_search(self):
        keyword = self.search_box.text().lower().strip()
        if not keyword:
            self._render(self._cache)
            return
        filtered = [row for row in self._cache if any(keyword in str(cell).lower() for cell in row)]
        self._render(filtered)

    def _show_context_menu(self, pos: QPoint):
        item = self.table.itemAt(pos)
        if not item: return
        
        row = item.row()
        quote_id = int(self.table.item(row, 0).text())
        project_name = self.table.item(row, 7).text()
        ref_id = self.table.item(row, 5).text()
        customer_id = self.table.item(row, 1).text()
        customer_name = self.table.item(row, 2).text()
        
        menu = QMenu(self)
        
        process_action = QAction(f"📑 Quotation Process: {ref_id}", self)
        process_action.triggered.connect(lambda: self._open_quotation_process(row))
        menu.addAction(process_action)
        
        items_action = QAction(f"📦 View Module Items: {project_name}", self)
        items_action.triggered.connect(lambda: self.parent_quotation_details_page.show_items())
        menu.addAction(items_action)

        rev_action = QAction(f"🔄 View Revisions: {project_name}", self)
        rev_action.triggered.connect(self._open_revisions)
        menu.addAction(rev_action)
        
        add_rev_action = QAction(f"➕ Create New Revision", self)
        add_rev_action.triggered.connect(lambda: self._create_revision_from_menu(quote_id))
        menu.addAction(add_rev_action)

        preview_action = QAction(f"👁️ Preview Quotation: {project_name}", self)
        preview_action.triggered.connect(lambda: self._open_quotation_preview(quote_id))
        menu.addAction(preview_action)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _create_revision_from_menu(self, quote_id):
        try:
            # We fetch base quote ID directly here since we have it in the table
            selected = self.table.selectionModel().selectedRows()
            if not selected: return
            row = selected[0].row()
            base_quote_id = int(self.table.item(row, 12).text()) if self.table.item(row, 12) and self.table.item(row, 12).text() else quote_id
            
            new_quote_id = self.service.create_revision(quote_id)
            QMessageBox.information(self, "Success", "Revision created successfully.")
            
            # Refresh table to show new revision
            self.refresh_table()
            
            # Update main window combobox and switch context
            if hasattr(self.parent_quotation_details_page, 'populate_revisions'):
                self.parent_quotation_details_page.populate_revisions(base_quote_id, new_quote_id)
                self.parent_quotation_details_page.show_revision()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create revision: {e}")

    def _open_common_specs(self):
        if self.parent_quotation_details_page:
            self.parent_quotation_details_page.show_common_specs()

    def _open_revisions(self):
        if self.parent_quotation_details_page:
            self.parent_quotation_details_page.show_revision()

    def _open_quotation_process(self, row):
        if self.parent_quotation_details_page:
            self.table.selectRow(row)
            self.parent_quotation_details_page.show_preview()

    def _open_ctc_dialog(self, quote_id, project_name):
        dialog = QuotationCTCDialog(quote_id, project_name, self)
        dialog.exec()

    def _open_quotation_preview(self, quote_id):
        """Opens the quotation preview dialog."""
        dialog = QuotationPreviewDialog(quote_id, self)
        dialog.exec()
