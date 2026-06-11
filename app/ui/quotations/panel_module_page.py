from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLineEdit, QLabel, QAbstractItemView, QMessageBox, QStatusBar, QDialog, QComboBox
)
from PySide6.QtCore import Qt, QTimer
from app.services.quotation_service import QuotationService
from app.ui.searchable_table import SearchableTable, NumericTableWidgetItem
from app.utils.worker_thread import Worker
from app.ui.quotations.panel_module_form import PanelModuleForm
from app.ui.quotations.panel_module_preview_dialog import PanelModulePreviewDialog

class PanelModulePage(QWidget):
    def __init__(self, parent_window=None):
        super().__init__()
        self.main_window = parent_window
        self.quote_id = None
        self.service = QuotationService()
        self._cache = []
        self._panels_lookup = [] # To store (panel_id, panel_name) for dropdown
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._perform_search)
        self._worker = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        
        self.back_btn = QPushButton("⬅️ Back to Quotations List") # Parent is QuotationDetailsPage
        self.back_btn.clicked.connect(lambda: self.main_window.show_quotations())
        
        self.title_label = QLabel("Quotation Panel Modules")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")

        # Panel selection for adding new modules
        self.panel_selection_combo = QComboBox()
        self.panel_selection_combo.setPlaceholderText("Select Panel for New Module")
        self.panel_selection_combo.setMinimumWidth(200)

        self.preview_btn = QPushButton("👁️ Preview All Panels")
        self.preview_btn.clicked.connect(self._show_all_panels_preview)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search modules...")
        self.search_box.textChanged.connect(self._debounce_search)

        self.add_btn = QPushButton("➕ Add Module")
        self.add_btn.clicked.connect(self.add_module)
        
        self.edit_btn = QPushButton("✏️ Edit")
        self.edit_btn.clicked.connect(self.edit_module)
        
        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.clicked.connect(self.delete_module)

        header.addWidget(self.back_btn)
        header.addWidget(self.title_label)
        header.addWidget(self.panel_selection_combo)
        header.addWidget(self.preview_btn)
        header.addStretch()
        header.addWidget(self.search_box)
        header.addWidget(self.add_btn)
        header.addWidget(self.edit_btn)
        header.addWidget(self.delete_btn)
        layout.addLayout(header)

        self.table = SearchableTable()
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels([
            "ID", "PanelID", "Panel Name", "In/Out", "Qty", 
            "TypeID", "Module Type", "Pole", "KA", "Release", "Protection", "Remark"
        ])
        self.table.hideColumn(0)
        self.table.hideColumn(1)
        self.table.hideColumn(5)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.itemDoubleClicked.connect(self.edit_module)
        layout.addWidget(self.table)
        
        self.status_bar = QStatusBar()
        layout.addWidget(self.status_bar)

    def load_quotation(self, quote_id, project_name):
        self.quote_id = quote_id
        self.project_name = project_name # Store project name for preview dialog
        self.title_label.setText(f"Modules: {project_name} (ID: {quote_id})")
        self._load_panels_for_dropdown()
        self.refresh_table()

    def clear_page(self):
        """Clears the page content when no quotation is selected."""
        self.quote_id = None
        self.project_name = ""
        self.title_label.setText("Quotation Panel Modules")
        self.panel_selection_combo.clear()
        self.table.setRowCount(0)
        self._cache = []
        self.status_bar.clearMessage()

    def _load_panels_for_dropdown(self):
        self._panels_lookup = self.service.get_panels_by_quote(self.quote_id)
        self.panel_selection_combo.clear()
        self.panel_selection_combo.addItem("Select Panel...", None) # Default empty item
        for panel in self._panels_lookup:
            self.panel_selection_combo.addItem(f"{panel[4]} (ID: {panel[0]})", panel[0]) # PanelName (ID: PanelID)

    def refresh_table(self):
        if self._worker or self.quote_id is None: return
        self.status_bar.showMessage("Loading panel modules...")
        self._worker = Worker(self.service.get_all_modules_by_quote, self.quote_id)
        self._worker.result.connect(self._on_data_loaded)
        self._worker.start()

    def _on_data_loaded(self, rows):
        self._cache = list(rows)
        self._render(self._cache)
        self.status_bar.showMessage(f"Found {len(rows)} modules", 5000)
        self._worker = None

    def _render(self, rows):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                item = NumericTableWidgetItem(str(val) if val is not None else "")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(r, c, item)
        self.table.setSortingEnabled(True)
        self.table.resizeColumnsToContents()

    def _debounce_search(self): self._search_timer.start(300)
    def _perform_search(self):
        kw = self.search_box.text().lower().strip()
        self._render([r for r in self._cache if any(kw in str(c).lower() for c in r)] if kw else self._cache)

    def add_module(self):
        selected_panel_id = self.panel_selection_combo.currentData()
        if selected_panel_id is None:
            QMessageBox.warning(self, "Selection Required", "Please select a target panel from the dropdown to add a module.")
            return

        dialog = PanelModuleForm(self.quote_id, panel_id=selected_panel_id, parent=self)
        if dialog.exec() == QDialog.Accepted:
            try:
                self.service.create_panel_module(**dialog.get_data())
                QMessageBox.information(self, "Success", "Panel module added successfully.")
                self.refresh_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add panel module: {e}")


    def edit_module(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected: return
        row = selected[0].row()
        pm_id = int(self.table.item(row, 0).text())
        keys = ["id", "panel_id", "panel_name", "ing_og", "qty", "type_id", "type_name", "pole", "ka", "release", "protection", "remark"]
        data = {keys[i]: self.table.item(row, i).text() for i in range(len(keys))}
        dialog = PanelModuleForm(self.quote_id, pm_data=data, panel_id=int(data["panel_id"]), parent=self)
        if dialog.exec() == QDialog.Accepted:
            try:
                self.service.update_panel_module(pm_id, **dialog.get_data())
                QMessageBox.information(self, "Success", "Panel module updated successfully.")
                self.refresh_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update panel module: {e}")


    def delete_module(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected: return
        if QMessageBox.question(self, "Confirm", "Delete selected module(s)?") == QMessageBox.Yes:
            for idx in selected: self.service.delete_panel_module(int(self.table.item(idx.row(), 0).text()))
            self.refresh_table()

    def _show_all_panels_preview(self):
        if self.quote_id is None:
            QMessageBox.warning(self, "No Quotation Selected", "Please select a quotation first to preview its panels and modules.")
            return
        
        preview_dialog = PanelModulePreviewDialog(self.quote_id, self.project_name, self)
        preview_dialog.exec()