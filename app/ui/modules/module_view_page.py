from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLineEdit, QLabel, QAbstractItemView, QMessageBox, QMenu, QInputDialog
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QShortcut, QKeySequence

from app.services.module_service import ModuleService
from app.services.module_type_service import ModuleTypeService
from app.ui.searchable_table import SearchableTable, NumericTableWidgetItem
from app.ui.modules.module_type_form import ModuleTypeForm
from app.config.ui_state import UIStateManager
from app.utils.worker_thread import Worker

class ModuleViewPage(QWidget):
    def __init__(self):
        super().__init__()
        self.service = ModuleService()
        self.type_service = ModuleTypeService()
        self._cache = []
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._perform_search)
        self._worker = None

        self.setup_ui()
        self._load_async()
        self._restore_state()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        header = QHBoxLayout()

        title = QLabel("Modules Overview")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search Module Type / Make / SWG...")
        self.search_box.textChanged.connect(self._debounce_search)

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setToolTip("Refresh modules list (Ctrl+R)")
        self.refresh_btn.clicked.connect(self.refresh_table)

        self.add_btn = QPushButton("➕ Add")
        self.add_btn.setToolTip("Add new module type (Ctrl+N)")
        self.add_btn.clicked.connect(self._add_module_type)

        self.edit_btn = QPushButton("✏️ Edit")
        self.edit_btn.setToolTip("Edit selected module type (Ctrl+E)")
        self.edit_btn.clicked.connect(self._edit_module_type)

        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.setToolTip("Delete selected module type (Delete)")
        self.delete_btn.clicked.connect(self._delete_module_type)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.search_box)
        header.addWidget(self.refresh_btn)
        header.addWidget(self.add_btn)
        header.addWidget(self.edit_btn)
        header.addWidget(self.delete_btn)
        layout.addLayout(header)

        # Row for individual filters and Clear All button
        filter_row = QHBoxLayout()
        self.type_filter = QLineEdit()
        self.type_filter.setPlaceholderText("Filter Module Type...")
        self.type_filter.textChanged.connect(self._debounce_search)

        self.make_filter = QLineEdit()
        self.make_filter.setPlaceholderText("Filter Make...")
        self.make_filter.textChanged.connect(self._debounce_search)

        self.clear_filters_btn = QPushButton("🧹 Clear All Filters")
        self.clear_filters_btn.clicked.connect(self.clear_all_filters)

        filter_row.addStretch()
        filter_row.addWidget(QLabel("Narrow by:"))
        filter_row.addWidget(self.type_filter)
        filter_row.addWidget(self.make_filter)
        filter_row.addWidget(self.clear_filters_btn)
        layout.addLayout(filter_row)

        self.table = SearchableTable()
        self.table.setColumnCount(4) # Changed from 5 to 4
        self.table.setHorizontalHeaderLabels([
            "ID",
            "Module Type",
            "Module Make",
            "SWG",
        ])
        self.table.hideColumn(0) # Hide ModuleTypeID
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._on_context_menu)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.itemDoubleClicked.connect(self._on_double_click)
        self.table.setSortingEnabled(True)
        
        # Enable movable columns and rows
        self.table.horizontalHeader().setSectionsMovable(True)
        self.table.verticalHeader().setSectionsMovable(True)

        self.table.verticalHeader().setVisible(True)
        
        layout.addWidget(self.table)

        QShortcut(QKeySequence("Ctrl+R"), self, activated=self.refresh_table)
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self._add_module_type)
        QShortcut(QKeySequence("Ctrl+E"), self, activated=self._edit_module_type)
        QShortcut(QKeySequence.Delete, self, activated=self._delete_module_type)
        QShortcut(QKeySequence.Find, self, activated=lambda: self.search_box.setFocus())

    def _on_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item or item.column() != 1: # Column 1 is Module Type
            return

        row = item.row()
        module_type_id_item = self.table.item(row, 0) # ModuleTypeID is now at index 0
        if not module_type_id_item: return
        
        module_type_id = int(module_type_id_item.text())
        module_type_name = self.table.item(row, 1).text()

        menu = QMenu(self)
        open_action = menu.addAction(f"Open Module Details: {module_type_name}")
        edit_action = menu.addAction("Edit Module Type")
        delete_action = menu.addAction("Delete Module Type")
        
        action = menu.exec(self.table.viewport().mapToGlobal(pos))

        if action == open_action:
            self._open_module_manager(module_type_id)
        elif action == edit_action:
            self._edit_module_type()
        elif action == delete_action:
            self._delete_module_type()

    def _on_double_click(self, item):
        row = item.row()
        module_type_id = int(self.table.item(row, 0).text())
        self._open_module_manager(module_type_id)

    def _open_module_manager(self, module_type_id):
        from app.ui.modules.module_items_dialog import ModuleItemsDialog
        dialog = ModuleItemsDialog(module_type_id, self)
        dialog.exec()
        self.refresh_table()

    def _add_module_type(self):
        makes = self.type_service.get_all_module_makes()
        swgs = self.type_service.get_all_swgs()
        
        form = ModuleTypeForm(self, makes=makes, swgs=swgs)
        if form.exec():
            data = form.get_data()
            try:
                self.type_service.create_module_type(
                    data["ModuleType"], 
                    data["ModuleMakeID"], 
                    data["ModSwgID"]
                )
                self.refresh_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not create module type: {e}")

    def _edit_module_type(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Selection Required", "Please select a module type to edit.")
            return
        
        row = selected[0].row()
        module_type_id = int(self.table.item(row, 0).text())
        
        # Fetch full data to populate the form
        raw_data = self.type_service.get_module_type(module_type_id)
        initial_data = dict(raw_data._mapping) if raw_data else None
        makes = self.type_service.get_all_module_makes()
        swgs = self.type_service.get_all_swgs()

        form = ModuleTypeForm(self, makes=makes, swgs=swgs, initial_data=initial_data)
        if form.exec():
            data = form.get_data()
            try:
                self.type_service.update_module_type(
                    module_type_id,
                    data["ModuleType"],
                    data["ModuleMakeID"],
                    data["ModSwgID"]
                )
                self.refresh_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not update module type: {e}")

    def _delete_module_type(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Selection Required", "Please select module types to delete.")
            return

        if QMessageBox.question(self, "Confirm Delete", f"Are you sure you want to delete {len(selected)} module type(s)?") == QMessageBox.Yes:
            try:
                for index in selected:
                    module_type_id = int(self.table.item(index.row(), 0).text())
                    self.type_service.delete_module_type(module_type_id)
                
                QMessageBox.information(self, "Deleted", "Module type(s) deleted successfully.")
                self.refresh_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _load_async(self):
        if self._worker: return
        self._worker = Worker(self.service.get_all_modules)
        self._worker.result.connect(self._loaded)
        self._worker.error.connect(self._on_load_error)
        self._worker.start()

    def _loaded(self, rows):
        self._cache = list(rows)
        self._render(self._cache)
        self._worker = None

    def _on_load_error(self, err):
        QMessageBox.critical(self, "Database Error", f"Could not load modules: {err}")
        self._worker = None

    def _render(self, rows):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            # row indexes based on new query: 0:ModuleTypeID, 1:ModuleType, 2:ModuleMake, 3:SWG
            for t_col in range(len(row)): # Iterate through all columns returned by the new query
                self.table.setItem(
                    r, t_col,
                    NumericTableWidgetItem(str(row[t_col] if row[t_col] is not None else ""))
                )
        self.table.setSortingEnabled(True)
        self.table.resizeColumnsToContents()
        self._restore_state()

    def _save_state(self):
        """Save header state to UIStateManager."""
        header_state = self.table.horizontalHeader().saveState()
        v_header_state = self.table.verticalHeader().saveState()
        if hasattr(UIStateManager, 'save_modules_page_state'):
            UIStateManager.save_modules_page_state({
                "header_state": header_state,
                "v_header_state": v_header_state
            })

    def _restore_state(self):
        """Restore header state from UIStateManager."""
        if hasattr(UIStateManager, 'get_modules_page_state'):
            state = UIStateManager.get_modules_page_state()
            if state:
                if state.get("header_state"):
                    self.table.horizontalHeader().restoreState(state["header_state"])
                if state.get("v_header_state"):
                    self.table.verticalHeader().restoreState(state["v_header_state"])

    def _debounce_search(self):
        self._search_timer.start(300)

    def _perform_search(self):
        keyword = self.search_box.text().lower()
        type_key = self.type_filter.text().lower()
        make_key = self.make_filter.text().lower()

        if not any([keyword, type_key, make_key]):
            self._render(self._cache)
            return

        filtered = []
        for row in self._cache:
            # Check general keyword
            match_general = True
            if keyword:
                search_content = f"{row[1] or ''} {row[2] or ''} {row[3] or ''}".lower()
                match_general = keyword in search_content

            # Check individual filters (AND logic)
            match_type = not type_key or type_key in str(row[1] or "").lower()
            match_make = not make_key or make_key in str(row[2] or "").lower()

            if match_general and match_type and match_make:
                filtered.append(row)
        self._render(filtered)

    def clear_all_filters(self):
        self.search_box.clear()
        self.type_filter.clear()
        self.make_filter.clear()

    def refresh_table(self):
        self.clear_all_filters()
        self._load_async()