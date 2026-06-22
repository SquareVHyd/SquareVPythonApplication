import pyodbc
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLineEdit, QLabel, QAbstractItemView, QMessageBox, QMenu, QStatusBar, QApplication,
    QDialog, QHeaderView, QSplitter, QScrollArea, QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QShortcut, QKeySequence, QAction

from app.services.quotation_service import QuotationService
from app.ui.quotations.quotation_form import QuotationForm
from app.ui.quotations.quotation_ctc_dialog import QuotationCTCDialog
from app.ui.quotations.module_items.module_items_viewer_dialog import ModuleItemsViewerDialog
from app.ui.quotations.quotation_preview_dialog import QuotationPreviewDialog
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
        self.table.setColumnCount(14) # Increased by 1 for CustomerId and 3 for Metal Costs
        self.table.setHorizontalHeaderLabels([
            "ID", "Customer ID", "Customer", "Req. Date", "Quote Date", "Ref No", 
            "Subject", "Project", "Contact", "Prepared By", "Status",
            "Steel Cost", "Alum Cost", "Copper Cost"
        ])
        self.table.hideColumn(0) # Hide Quote ID
        self.table.hideColumn(1) # Hide Customer ID
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSortingEnabled(True)
        
        # Right-click context menu
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        
        # Track selection to enable/disable Panels button
        self.table.itemSelectionChanged.connect(self._on_selection_changed)

        # Double click to edit entire quotation
        self.table.itemDoubleClicked.connect(self.edit_quotation)
        
        # Inline edit handler for metal costs
        self.table.itemChanged.connect(self._on_item_changed)
        
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
        if hasattr(self.parent_quotation_details_page, 'update_panels_button_state'):
            self.parent_quotation_details_page.update_panels_button_state(len(selected) == 1)

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
            "contact": self.table.item(row, 8).text(),
            "prepared_by": self.table.item(row, 9).text(),
            "status": self.table.item(row, 10).text(),
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
        for r, row in enumerate(rows):
            for c in range(len(row)):
                val = str(row[c]) if row[c] is not None else ""
                item = NumericTableWidgetItem(val)
                if c in (11, 12, 13):
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                    item.setBackground(Qt.yellow)  # Highlight editable cells slightly
                else:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(r, c, item)
        self.table.setSortingEnabled(True)
        self.table.blockSignals(False)
        self.table.resizeColumnsToContents()

    def _on_item_changed(self, item):
        col = item.column()
        if col not in (11, 12, 13): return
        
        row = item.row()
        quote_id_item = self.table.item(row, 0)
        if not quote_id_item: return
        
        try:
            quote_id = int(quote_id_item.text())
            new_val = float(item.text().strip())
        except ValueError:
            return  # invalid input, ignore or could revert
            
        metal_col_map = {11: "Steel", 12: "Aluminium", 13: "Copper"}
        metal_name = metal_col_map[col]
        
        try:
            self.service.update_metal_cost_in_quote(quote_id, metal_name, new_val)
            # Update cache so search doesn't revert it
            for r in self._cache:
                if str(r[0]) == str(quote_id):
                    # tuples are immutable, convert to list, update, convert back
                    r_list = list(r)
                    r_list[col] = new_val
                    # need to replace in cache
                    idx = self._cache.index(r)
                    self._cache[idx] = tuple(r_list)
                    break
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save {metal_name} cost: {e}")

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
        customer_id = self.table.item(row, 1).text()
        customer_name = self.table.item(row, 2).text()
        
        menu = QMenu(self)
        
        process_action = QAction(f"📑 Quotation Process: {project_name}", self)
        process_action.triggered.connect(lambda: self._open_quotation_process(row))
        menu.addAction(process_action)
        
        items_action = QAction(f"📦 View Module Items: {project_name}", self)
        items_action.triggered.connect(lambda: self.parent_quotation_details_page.show_items())
        menu.addAction(items_action)

        rev_action = QAction(f"🔄 Revisions: {project_name}", self)
        rev_action.triggered.connect(self._open_revisions)
        menu.addAction(rev_action)

        preview_action = QAction(f"👁️ Preview Quotation: {project_name}", self)
        preview_action.triggered.connect(lambda: self._open_quotation_preview(quote_id))
        menu.addAction(preview_action)

        menu.exec(self.table.viewport().mapToGlobal(pos))

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
