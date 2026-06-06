from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QLabel,
    QMessageBox,
    QDialog,
    QAbstractItemView
)

from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtCore import Qt, QTimer

from app.services.price_list_service import PriceListService
from app.ui.pricelist.pricelist_form import PriceListForm
from app.ui.searchable_table import (
    SearchableTable,
    NumericTableWidgetItem
)
from app.utils.worker_thread import Worker
from app.config.ui_state import UIStateManager


class PriceListPage(QWidget):

    def __init__(self):

        super().__init__()

        self.service = PriceListService()

        self._cache = []
        self._search_timer = QTimer()

        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(
            self._perform_search
        )

        self._worker = None

        self.setup_ui()

        self._load_async()
        self._restore_state()

    def setup_ui(self):

        layout = QVBoxLayout(self)

        header = QHBoxLayout()

        title = QLabel("Price List")

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(
            "General Search (Description, Model, Category, Make)..."
        )

        self.search_box.textChanged.connect(
            self._debounce_search
        )

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.add_btn = QPushButton("➕ Add")
        self.edit_btn = QPushButton("✏️ Edit")
        self.delete_btn = QPushButton("🗑️ Delete")

        self.refresh_btn.clicked.connect(
            self.refresh_table
        )

        self.add_btn.clicked.connect(
            self.add_item
        )

        self.edit_btn.clicked.connect(
            self.edit_item
        )

        self.delete_btn.clicked.connect(
            self.delete_item
        )

        # Row for individual filters and Clear All button
        filter_row = QHBoxLayout()
        self.model_filter = QLineEdit()
        self.model_filter.setPlaceholderText("Filter Model...")
        self.model_filter.textChanged.connect(self._debounce_search)

        self.category_filter = QLineEdit()
        self.category_filter.setPlaceholderText("Filter Category...")
        self.category_filter.textChanged.connect(self._debounce_search)

        self.make_filter = QLineEdit()
        self.make_filter.setPlaceholderText("Filter Make...")
        self.make_filter.textChanged.connect(self._debounce_search)

        self.clear_filters_btn = QPushButton("Clear All Filters")
        self.clear_filters_btn.clicked.connect(self.clear_all_filters)

        filter_row.addStretch()
        filter_row.addWidget(QLabel("Narrow by:"))
        filter_row.addWidget(self.model_filter)
        filter_row.addWidget(self.category_filter)
        filter_row.addWidget(self.make_filter)
        filter_row.addWidget(self.clear_filters_btn)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.search_box)
        header.addWidget(self.refresh_btn)
        header.addWidget(self.add_btn)
        header.addWidget(self.edit_btn)
        header.addWidget(self.delete_btn)

        layout.addLayout(header)
        layout.addLayout(filter_row)

        self.table = SearchableTable()

        self.table.setColumnCount(12)

        self.table.setHorizontalHeaderLabels([
            "ID",
            "Description",
            "Model",
            "Category",
            "Make",
            "List Price",
            "Discount %",
            "Net Price",
            "Used Qty",
            "Total Amount",
            "CategoryID",
            "MakeID"
        ])
        self.table.hideColumn(0)
        self.table.hideColumn(10)
        self.table.hideColumn(11)

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        
        # Enable movable columns and rows
        self.table.horizontalHeader().setSectionsMovable(True)
        self.table.verticalHeader().setSectionsMovable(True)

        self.table.setSortingEnabled(True)

        layout.addWidget(self.table)

        QShortcut(
            QKeySequence("Ctrl+N"),
            self,
            activated=self.add_item
        )

        QShortcut(
            QKeySequence("Ctrl+E"),
            self,
            activated=self.edit_item
        )

        QShortcut(
            QKeySequence("Delete"),
            self,
            activated=self.delete_item
        )

        QShortcut(
            QKeySequence("Ctrl+R"),
            self,
            activated=self.refresh_table
        )

        QShortcut(
            QKeySequence.Find,
            self,
            activated=self.focus_search
        )

    def focus_search(self):
        self.search_box.setFocus()

    def _load_async(self):

        self._worker = Worker(
            self.service.get_all_price_items
        )

        self._worker.result.connect(
            self._loaded
        )

        self._worker.start()

    def _loaded(self, result):

        rows, _ = result

        self._cache = list(rows)

        self._render(self._cache)

    def _render(self, rows):

        self.table.setSortingEnabled(False)

        self.table.setRowCount(len(rows))

        for r, row in enumerate(rows):
            for c in range(len(row)):
                self.table.setItem(
                    r,
                    c,
                    NumericTableWidgetItem(
                        str(row[c] or "")
                    )
                )

        self.table.setSortingEnabled(True)
        self.table.resizeColumnsToContents()
        self._restore_state()

    def _save_state(self):
        """Save header state to UIStateManager."""
        header_state = self.table.horizontalHeader().saveState()
        v_header_state = self.table.verticalHeader().saveState()
        if hasattr(UIStateManager, 'save_pricelist_page_state'):
            UIStateManager.save_pricelist_page_state({
                "header_state": header_state,
                "v_header_state": v_header_state
            })

    def _restore_state(self):
        """Restore header state from UIStateManager."""
        if hasattr(UIStateManager, 'get_pricelist_page_state'):
            state = UIStateManager.get_pricelist_page_state()
            if state:
                if state.get("header_state"):
                    self.table.horizontalHeader().restoreState(state["header_state"])
                if state.get("v_header_state"):
                    self.table.verticalHeader().restoreState(state["v_header_state"])

    def _debounce_search(self):

        self._search_timer.start(300)

    def _perform_search(self):

        keyword = self.search_box.text().lower()
        model_key = self.model_filter.text().lower()
        category_key = self.category_filter.text().lower()
        make_key = self.make_filter.text().lower()

        if not any([keyword, model_key, category_key, make_key]):
            self._render(self._cache)
            return

        filtered = []
        for row in self._cache:
            # Check general keyword
            match_general = True
            if keyword:
                search_content = " ".join([
                    str(row[1] or ""),
                    str(row[2] or ""),
                    str(row[3] or ""),
                    str(row[4] or "")
                ]).lower()
                match_general = keyword in search_content

            # Check individual filters (AND logic)
            match_model = not model_key or model_key in str(row[2] or "").lower()
            match_category = not category_key or category_key in str(row[3] or "").lower()
            match_make = not make_key or make_key in str(row[4] or "").lower()

            if match_general and match_model and match_category and match_make:
                filtered.append(row)

        self._render(filtered)

    def clear_all_filters(self):
        """Resets all search fields which triggers re-render via textChanged signals."""
        self.search_box.clear()
        self.model_filter.clear()
        self.category_filter.clear()
        self.make_filter.clear()

    def get_selected_item(self):

        selected = self.table.selectedItems()

        if not selected:

            return None

        row = selected[0].row()

        item_id = int(
            self.table.item(row, 0).text()
        )

        return self.service.get_price_item(item_id)

    def add_item(self):

        dialog = PriceListForm(self)

        if dialog.exec() == QDialog.Accepted:

            data = dialog.get_data()
            self.service.create_price_item(
                **data
            )

            self.refresh_table()

    def edit_item(self):

        item = self.get_selected_item()

        if not item:

            return

        dialog = PriceListForm(
            self,
            item=item
        )

        if dialog.exec() == QDialog.Accepted:

            data = dialog.get_data()
            self.service.update_price_item(
                item[0],
                **data
            )

            self.refresh_table()

    def delete_item(self):

        item = self.get_selected_item()

        if not item:

            return

        if QMessageBox.question(
            self,
            "Delete",
            "Delete selected item?"
        ) == QMessageBox.Yes:

            self.service.delete_price_item(
                item[0]
            )

            self.refresh_table()

    def refresh_table(self):

        self.clear_all_filters()

        self._load_async()