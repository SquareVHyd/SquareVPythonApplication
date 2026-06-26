import math
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QLabel,
    QMessageBox,
    QDialog,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QCheckBox,
    QHeaderView,
    QComboBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QBrush

from app.services.generic_spec_service import GenericSpecService
from app.ui.generic_spec.generic_spec_dialogs import GenericSpecForm
from app.ui.searchable_table import NumericTableWidgetItem
from app.utils.worker_thread import Worker

class GenericSpecPage(QWidget):
    def __init__(self):
        super().__init__()
        self.service = GenericSpecService()

        # Selection state tracking (persisted by ID)
        self.selected_price_list_ids = set()
        
        # Cache for search optimization
        self.generic_cache = []
        self.price_cache = []
        self.price_filtered_rows = []
        
        # Pagination state
        self.current_page = 1
        self.page_size = 100
        self.total_pages = 1
        self.total_filtered = 0

        # Worker thread trackers
        self._init_worker = None
        self._generic_worker = None
        self._price_worker = None
        self._action_worker = None
        
        # Debounce timers
        self.generic_search_timer = QTimer()
        self.generic_search_timer.setSingleShot(True)
        self.generic_search_timer.timeout.connect(self._perform_generic_search)

        self.price_search_timer = QTimer()
        self.price_search_timer.setSingleShot(True)
        self.price_search_timer.timeout.connect(self._perform_price_search)

        self.destroyed.connect(self.cleanup_workers)

        self.setup_ui()
        
        # Initialize the database schema and load data asynchronously
        self.init_db_and_load()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Title / Top bar
        title_label = QLabel("Generic Specification Mapping")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #0f172a;")
        title_label.setFixedHeight(30)
        main_layout.addWidget(title_label)

        # Splitter for left and right grids
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(2)
        self.splitter.setStyleSheet("QSplitter::handle { background-color: #cbd5e1; }")

        # --- LEFT PANEL: Generic Spec Items ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        left_header = QLabel("Generic Specification Items (Master)")
        left_header.setStyleSheet("font-weight: bold; color: #1e293b; font-size: 13px;")
        left_layout.addWidget(left_header)

        # Left controls
        left_ctrls = QHBoxLayout()
        self.generic_search = QLineEdit()
        self.generic_search.setPlaceholderText("Search generic description...")
        self.generic_search.textChanged.connect(self._debounce_generic_search)
        
        self.generic_clear_btn = QPushButton("🧹")
        self.generic_clear_btn.setToolTip("Clear Search")
        self.generic_clear_btn.setFixedWidth(30)
        self.generic_clear_btn.clicked.connect(self.clear_generic_search)

        self.add_generic_btn = QPushButton("➕ Add")
        self.add_generic_btn.setToolTip("Add new generic item")
        self.add_generic_btn.clicked.connect(self.add_generic_item)

        self.edit_generic_btn = QPushButton("✏️ Edit")
        self.edit_generic_btn.setToolTip("Edit selected generic description")
        self.edit_generic_btn.clicked.connect(self.edit_generic_item)

        self.delete_generic_btn = QPushButton("🗑️ Delete")
        self.delete_generic_btn.setToolTip("Delete selected generic item")
        self.delete_generic_btn.clicked.connect(self.delete_generic_item)

        left_ctrls.addWidget(self.generic_search)
        left_ctrls.addWidget(self.generic_clear_btn)
        left_ctrls.addWidget(self.add_generic_btn)
        left_ctrls.addWidget(self.edit_generic_btn)
        left_ctrls.addWidget(self.delete_generic_btn)
        left_layout.addLayout(left_ctrls)

        # Left grid
        self.generic_table = QTableWidget()
        self.generic_table.setStyleSheet("QTableView { selection-background-color: #93c5fd; selection-color: #000000; } QHeaderView::section { background-color: #fce4ec; border: 1px solid #e2e8f0; font-weight: bold; }")
        self.generic_table.setColumnCount(3)
        self.generic_table.setHorizontalHeaderLabels(["ID", "ItemDescription", "Remark/Makes"])
        self.generic_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.generic_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.generic_table.setSortingEnabled(True)
        self.generic_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.generic_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.generic_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Interactive)
        self.generic_table.horizontalHeader().setSectionsMovable(True)
        self.generic_table.horizontalHeader().setStretchLastSection(True)
        self.generic_table.horizontalHeader().setMinimumHeight(30)
        self.generic_table.itemSelectionChanged.connect(self.on_generic_selection_changed)
        self.generic_table.itemChanged.connect(self.handle_generic_item_changed)
        left_layout.addWidget(self.generic_table)

        self.splitter.addWidget(left_widget)

        # --- RIGHT PANEL: Price List Items ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)

        right_header = QLabel("Price List Items (Detail)")
        right_header.setStyleSheet("font-weight: bold; color: #1e293b; font-size: 13px;")
        right_layout.addWidget(right_header)

        # Right controls row 1
        right_ctrls_1 = QHBoxLayout()
        self.price_search = QLineEdit()
        self.price_search.setPlaceholderText("Search price items (Desc, Model, ID, Cat, Make, Generic ID)...")
        self.price_search.textChanged.connect(self._debounce_price_search)

        self.price_clear_btn = QPushButton("🧹 Clear")
        self.price_clear_btn.clicked.connect(self.clear_price_search)

        self.filter_linked_cb = QCheckBox("Show only items for selected generic")
        self.filter_linked_cb.setStyleSheet("font-weight: 500;")
        self.filter_linked_cb.stateChanged.connect(self.filter_linked_state_changed)

        right_ctrls_1.addWidget(self.price_search)
        right_ctrls_1.addWidget(self.price_clear_btn)
        right_ctrls_1.addWidget(self.filter_linked_cb)
        right_layout.addLayout(right_ctrls_1)

        # Right controls row 2 (Filters)
        right_ctrls_2 = QHBoxLayout()
        
        self.category_filter_combo = QComboBox()
        self.category_filter_combo.addItem("All Categories")
        self.category_filter_combo.currentTextChanged.connect(self.price_filter_changed)
        
        self.make_filter_combo = QComboBox()
        self.make_filter_combo.addItem("All Makes")
        self.make_filter_combo.currentTextChanged.connect(self.price_filter_changed)
        
        # Style controls to look clean and premium
        self.category_filter_combo.setMinimumWidth(150)
        self.make_filter_combo.setMinimumWidth(150)
        
        lbl_cat = QLabel("Category:")
        lbl_cat.setStyleSheet("font-weight: 500; color: #475569;")
        lbl_make = QLabel("Make:")
        lbl_make.setStyleSheet("font-weight: 500; color: #475569;")
        
        right_ctrls_2.addWidget(lbl_cat)
        right_ctrls_2.addWidget(self.category_filter_combo)
        right_ctrls_2.addWidget(lbl_make)
        right_ctrls_2.addWidget(self.make_filter_combo)
        right_ctrls_2.addStretch()
        right_layout.addLayout(right_ctrls_2)

        # Selection stats label
        self.price_stats = QLabel("Initializing...")
        self.price_stats.setStyleSheet("color: #475569; font-size: 11px; font-weight: bold;")
        right_layout.addWidget(self.price_stats)

        # Right grid
        self.price_table = QTableWidget()
        self.price_table.setStyleSheet("QTableView { selection-background-color: #93c5fd; selection-color: #000000; } QHeaderView::section { background-color: #fce4ec; border: 1px solid #e2e8f0; font-weight: bold; }")
        
        # Columns: Select(0), ID(1), Description(2), Model(3), Category(4), Make(5), List Price(6), Discount %(7), Net Price(8), Used Qty(9), Total Amount(10), GenericSpecItemID(11)
        self.price_table.setColumnCount(12)
        self.price_table.setHorizontalHeaderLabels([
            "☑",
            "ID",
            "ItemDescription",
            "Model",
            "Category",
            "Make",
            "List Price",
            "Discount %",
            "Net Price",
            "Used Qty",
            "Total Amount",
            "GenericSpecItemID"
        ])
        self.price_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.price_table.setSortingEnabled(True)
        self.price_table.itemChanged.connect(self.handle_price_checkbox_changed)
        
        # Set resize modes for all columns to allow manual resizing and moving
        for i in range(12):
            self.price_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.Interactive)
        self.price_table.horizontalHeader().setSectionsMovable(True)
        self.price_table.horizontalHeader().setStretchLastSection(True)
        self.price_table.horizontalHeader().setMinimumHeight(30)
        
        # Do not hide columns List Price(6), Discount %(7), Net Price(8), Used Qty(9), Total Amount(10)
        # They are now fully visible per user request
        
        right_layout.addWidget(self.price_table)

        # Pagination controls layout
        pagination_layout = QHBoxLayout()
        self.prev_page_btn = QPushButton("◀ Previous")
        self.prev_page_btn.clicked.connect(self.prev_page)
        self.prev_page_btn.setEnabled(False)
        
        self.page_info_label = QLabel("Page 1 of 1")
        self.page_info_label.setStyleSheet("font-weight: bold; color: #475569;")
        self.page_info_label.setAlignment(Qt.AlignCenter)
        
        self.next_page_btn = QPushButton("Next ▶")
        self.next_page_btn.clicked.connect(self.next_page)
        self.next_page_btn.setEnabled(False)
        
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["50", "100", "200", "500"])
        self.page_size_combo.setCurrentText("100")
        self.page_size_combo.currentTextChanged.connect(self.page_size_changed)
        
        pagination_layout.addWidget(self.prev_page_btn)
        pagination_layout.addStretch()
        pagination_layout.addWidget(self.page_info_label)
        pagination_layout.addStretch()
        pagination_layout.addWidget(self.next_page_btn)
        pagination_layout.addWidget(QLabel("Page Size:"))
        pagination_layout.addWidget(self.page_size_combo)
        
        right_layout.addLayout(pagination_layout)

        self.splitter.addWidget(right_widget)

        # Set initial splitter proportions (approx 35% left, 65% right)
        self.splitter.setSizes([350, 650])
        main_layout.addWidget(self.splitter, 1)

        # --- BOTTOM ACTION TOOLBAR ---
        bottom_toolbar = QHBoxLayout()
        
        self.bulk_add_generic_btn = QPushButton("🏷️ Add Generic Item from Selection")
        self.bulk_add_generic_btn.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 8px 16px; border-radius: 4px;")
        self.bulk_add_generic_btn.clicked.connect(self.add_generic_from_selected_price_items)

        self.assign_generic_btn = QPushButton("🔗 Assign Selected to Generic Item")
        self.assign_generic_btn.setStyleSheet("background-color: #2563eb; color: white; font-weight: bold; padding: 8px 16px; border-radius: 4px;")
        self.assign_generic_btn.clicked.connect(self.assign_generic_to_selected_price_items)

        self.remove_mapping_btn = QPushButton("🔓 Remove Mapping")
        self.remove_mapping_btn.setStyleSheet("background-color: #dc2626; color: white; font-weight: bold; padding: 8px 16px; border-radius: 4px;")
        self.remove_mapping_btn.clicked.connect(self.remove_mapping_from_selected_price_items)

        self.select_all_price_btn = QPushButton("Select All Visible")
        self.select_all_price_btn.clicked.connect(self.select_all_visible_price_items)

        self.clear_price_sel_btn = QPushButton("Clear Selection")
        self.clear_price_sel_btn.clicked.connect(self.clear_price_selection)

        bottom_toolbar.addWidget(self.bulk_add_generic_btn)
        bottom_toolbar.addWidget(self.assign_generic_btn)
        bottom_toolbar.addWidget(self.remove_mapping_btn)
        bottom_toolbar.addStretch()
        bottom_toolbar.addWidget(self.select_all_price_btn)
        bottom_toolbar.addWidget(self.clear_price_sel_btn)
        main_layout.addLayout(bottom_toolbar)

    # --- DB SCHEMA INITIALIZATION ---
    def init_db_and_load(self):
        """Asynchronously runs database setup to avoid blocking MainWindow thread."""
        if self._init_worker and self._init_worker.isRunning():
            return
            
        self.price_stats.setText("Initializing database schema...")
        self._init_worker = Worker(self.service.repository.initialize_tables)
        self._init_worker.result.connect(self._on_db_initialized)
        self._init_worker.error.connect(self._on_db_init_error)
        self._init_worker.start()

    def _on_db_initialized(self, result):
        self._init_worker = None
        self.refresh_all()

    def _on_db_init_error(self, err):
        print(f"Database setup error: {err}")
        self._init_worker = None
        # Try loading anyway
        self.refresh_all()

    # --- ACTION METHODS ---
    def get_selected_generic_id(self):
        """Returns the ID of the selected generic item, or None."""
        selected_indexes = self.generic_table.selectionModel().selectedRows()
        if not selected_indexes:
            return None
        row = selected_indexes[0].row()
        id_item = self.generic_table.item(row, 0)
        return int(id_item.text()) if id_item else None

    def get_selected_generic_desc(self):
        """Returns the description of the selected generic item, or None."""
        selected_indexes = self.generic_table.selectionModel().selectedRows()
        if not selected_indexes:
            return None
        row = selected_indexes[0].row()
        desc_item = self.generic_table.item(row, 1)
        return desc_item.text() if desc_item else None

    def get_selected_generic_remark(self):
        """Returns the Remark/Makes of the selected generic item, or None."""
        selected_indexes = self.generic_table.selectionModel().selectedRows()
        if not selected_indexes:
            return None
        row = selected_indexes[0].row()
        remark_item = self.generic_table.item(row, 2)
        return remark_item.text() if remark_item else None

    def add_generic_item(self):
        """Opens form to add a new generic spec item."""
        dialog = GenericSpecForm(self, mode="Add")
        if dialog.exec() == QDialog.Accepted:
            desc = dialog.get_description()
            remark = dialog.get_remark_makes()
            
            # Use background action thread to insert
            self.price_stats.setText(f"Creating generic item: {desc}...")
            self.run_background_action(
                lambda: self.service.create_generic_item(desc, remark),
                lambda new_id: self._on_generic_created(new_id, desc),
                self._on_action_error
            )

    def _on_generic_created(self, new_id, desc):
        QMessageBox.information(self, "Success", f"Generic Item '{desc}' created successfully.")
        self.refresh_generic_table()
        # Select the newly created item
        QTimer.singleShot(100, lambda: self.select_generic_by_id(new_id))

    def edit_generic_item(self):
        """Opens form to edit selected generic spec item."""
        generic_id = self.get_selected_generic_id()
        if not generic_id:
            QMessageBox.warning(self, "Selection Required", "Please select a Generic Item to edit.")
            return
        
        desc = self.get_selected_generic_desc()
        remark = self.get_selected_generic_remark()
        dialog = GenericSpecForm(self, item_description=desc, remark_makes=remark, mode="Edit")
        if dialog.exec() == QDialog.Accepted:
            new_desc = dialog.get_description()
            new_remark = dialog.get_remark_makes()
            
            self.price_stats.setText(f"Updating generic item...")
            self.run_background_action(
                lambda: self.service.update_generic_item(generic_id, new_desc, new_remark),
                lambda _: self._on_generic_updated(generic_id),
                self._on_action_error
            )

    def _on_generic_updated(self, generic_id):
        QMessageBox.information(self, "Success", "Generic Item description updated.")
        self.refresh_generic_table()
        QTimer.singleShot(100, lambda: self.select_generic_by_id(generic_id))

    def delete_generic_item(self):
        """Deletes selected generic item, checking links in a background thread."""
        generic_id = self.get_selected_generic_id()
        if not generic_id:
            QMessageBox.warning(self, "Selection Required", "Please select a Generic Item to delete.")
            return
        
        desc = self.get_selected_generic_desc()
        
        # Check linked items count in background
        self.price_stats.setText("Checking item linkages...")
        self.run_background_action(
            lambda: self.service.count_linked_price_items(generic_id),
            lambda count: self._confirm_delete_generic(generic_id, desc, count),
            self._on_action_error
        )

    def _confirm_delete_generic(self, generic_id, desc, count):
        self.price_stats.setText("Ready")
        if count > 0:
            msg = (
                f"Warning: The Generic Item '{desc}' is currently mapped to {count} price list records.\n\n"
                "Deleting it will unassign (set mapping to NULL) all these price list records.\n\n"
                "Are you sure you want to proceed?"
            )
            choice = QMessageBox.warning(
                self,
                "Confirm Deletion with Links",
                msg,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
        else:
            msg = f"Are you sure you want to delete the Generic Item '{desc}'?"
            choice = QMessageBox.question(
                self,
                "Confirm Deletion",
                msg,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

        if choice == QMessageBox.Yes:
            self.price_stats.setText("Deleting generic item...")
            self.run_background_action(
                lambda: self.service.delete_generic_item(generic_id),
                lambda _: self._on_generic_deleted(),
                self._on_action_error
            )

    def _on_generic_deleted(self):
        QMessageBox.information(self, "Success", "Generic Item deleted successfully.")
        self.refresh_all()

    def add_generic_from_selected_price_items(self):
        """Feature 1: Creates new Generic Item, then maps selected price list rows to it in background."""
        if not self.selected_price_list_ids:
            QMessageBox.warning(self, "Selection Required", "Please select one or more Price List records using the checkboxes.")
            return

        default_desc = ""
        selected_makes = set()
        for row in self.price_cache:
            if row[0] in self.selected_price_list_ids:
                if not default_desc:
                    default_desc = row[1]
                if row[4]:
                    selected_makes.add(str(row[4]).strip())

        default_makes = " / ".join(sorted(list(selected_makes)))

        dialog = GenericSpecForm(self, item_description=default_desc, remark_makes=default_makes, mode="Create Mapping From Selection")
        if dialog.exec() == QDialog.Accepted:
            desc = dialog.get_description()
            remark = dialog.get_remark_makes()
            pids = list(self.selected_price_list_ids)
            
            self.price_stats.setText("Creating item and mapping records...")
            
            def job():
                new_id = self.service.create_generic_item(desc, remark)
                self.service.assign_generic_item_to_price_items(new_id, pids)
                return new_id

            self.run_background_action(
                job,
                lambda new_id: self._on_bulk_mapped(new_id, desc, len(pids)),
                self._on_action_error
            )

    def _on_bulk_mapped(self, new_id, desc, count):
        QMessageBox.information(
            self,
            "Success",
            f"Created generic item '{desc}' (ID: {new_id}) and mapped it to {count} price items."
        )
        self.selected_price_list_ids.clear()
        self.refresh_all()
        QTimer.singleShot(100, lambda: self.select_generic_by_id(new_id))

    def assign_generic_to_selected_price_items(self):
        """Feature 2: Map selected Generic Item to selected Price List rows in background."""
        generic_id = self.get_selected_generic_id()
        if not generic_id:
            QMessageBox.warning(self, "Selection Required", "Please select a Generic Item from the left grid first.")
            return

        if not self.selected_price_list_ids:
            QMessageBox.warning(self, "Selection Required", "Please select one or more Price List records using checkboxes.")
            return

        desc = self.get_selected_generic_desc()
        confirm = QMessageBox.question(
            self,
            "Confirm Assignment",
            f"Are you sure you want to assign the Generic Item '{desc}' (ID: {generic_id}) to the {len(self.selected_price_list_ids)} selected Price List items?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            pids = list(self.selected_price_list_ids)
            self.price_stats.setText("Assigning generic mapping...")
            
            # Merge makes: get existing makes + selected makes
            existing_remark = self.get_selected_generic_remark() or ""
            selected_makes = set()
            if existing_remark:
                for part in existing_remark.split("/"):
                    if part.strip():
                        selected_makes.add(part.strip())
            
            for row in self.price_cache:
                if row[0] in self.selected_price_list_ids:
                    if row[4]:
                        selected_makes.add(str(row[4]).strip())
            
            merged_makes = " / ".join(sorted(list(selected_makes)))
            
            def job():
                self.service.update_generic_item(generic_id, desc, merged_makes)
                self.service.assign_generic_item_to_price_items(generic_id, pids)
                
            self.run_background_action(
                job,
                lambda _: self._on_assignment_done(generic_id),
                self._on_action_error
            )

    def _on_assignment_done(self, generic_id):
        QMessageBox.information(self, "Success", "Mapping updated successfully.")
        self.selected_price_list_ids.clear()
        self.refresh_all()
        QTimer.singleShot(100, lambda: self.select_generic_by_id(generic_id))

    def remove_mapping_from_selected_price_items(self):
        """Feature 4: Remove mapping (set GenericSpecItemID to NULL) for checked price list rows in background."""
        if not self.selected_price_list_ids:
            QMessageBox.warning(self, "Selection Required", "Please select one or more Price List records using checkboxes.")
            return

        confirm = QMessageBox.question(
            self,
            "Confirm Unassignment",
            f"Are you sure you want to remove mapping from the {len(self.selected_price_list_ids)} selected Price List items?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            pids = list(self.selected_price_list_ids)
            self.price_stats.setText("Removing mappings...")
            self.run_background_action(
                lambda: self.service.remove_generic_item_mapping(pids),
                lambda _: self._on_unmapping_done(),
                self._on_action_error
            )

    def _on_unmapping_done(self):
        QMessageBox.information(self, "Success", "Mapping removed successfully.")
        self.selected_price_list_ids.clear()
        self.refresh_all()

    # --- INLINE EDITING FOR LEFT GRID ---
    def handle_generic_item_changed(self, item):
        """Inline editing handler for Generic Spec Item description or Remark/Makes."""
        if item.column() not in (1, 2):
            return

        row = item.row()
        id_item = self.generic_table.item(row, 0)
        if not id_item:
            return

        generic_id = int(id_item.text())
        desc_item = self.generic_table.item(row, 1)
        remark_item = self.generic_table.item(row, 2)
        
        new_desc = desc_item.text().strip() if desc_item else ""
        new_remark = remark_item.text().strip() if remark_item else ""

        if not new_desc:
            QMessageBox.warning(self, "Validation Error", "Description cannot be empty.")
            self.refresh_generic_table()
            return

        # Perform inline update in background thread
        self.price_stats.setText("Updating generic item...")
        self.run_background_action(
            lambda: self.service.update_generic_item(generic_id, new_desc, new_remark),
            lambda _: self._on_inline_generic_updated(generic_id, new_desc, new_remark),
            lambda err: self._on_inline_generic_error(err)
        )

    def _on_inline_generic_updated(self, generic_id, new_desc, new_remark):
        self.price_stats.setText("Ready")
        # Update cache
        for i, cache_row in enumerate(self.generic_cache):
            if cache_row[0] == generic_id:
                self.generic_cache[i] = (generic_id, new_desc, new_remark)
                break

    def _on_inline_generic_error(self, err):
        if "UniqueViolation" in str(err) or "unique constraint" in str(err).lower():
            QMessageBox.warning(self, "Duplicate Error", "Another Generic Item with this description already exists.")
        else:
            QMessageBox.critical(self, "Database Error", f"Could not update Generic Item: {err}")
        self.refresh_generic_table()

    # --- BACKGROUND WORKER HELPER ---
    def run_background_action(self, target_fn, success_callback, error_callback):
        if self._action_worker and self._action_worker.isRunning():
            return
            
        self._action_worker = Worker(target_fn)
        
        def on_success(result):
            self._action_worker = None
            success_callback(result)
            
        def on_error(err):
            self._action_worker = None
            error_callback(err)
            
        self._action_worker.result.connect(on_success)
        self._action_worker.error.connect(on_error)
        self._action_worker.start()

    def closeEvent(self, event):
        """Clean up background workers when widget closes."""
        self.cleanup_workers()
        super().closeEvent(event)

    def cleanup_workers(self):
        """Disconnect and wait for all running background threads on widget destruction."""
        for worker_attr in ['_init_worker', '_generic_worker', '_price_worker', '_action_worker']:
            worker = getattr(self, worker_attr, None)
            if worker and worker.isRunning():
                try:
                    worker.result.disconnect()
                except (RuntimeError, TypeError):
                    pass
                try:
                    worker.error.disconnect()
                except (RuntimeError, TypeError):
                    pass
                worker.quit()
                worker.wait()

    def _on_action_error(self, err):
        self.price_stats.setText("Ready")
        if "UniqueViolation" in str(err) or "unique constraint" in str(err).lower():
            QMessageBox.warning(self, "Duplicate Error", "Operation failed: A duplicate entry constraint was violated.")
        else:
            QMessageBox.critical(self, "Database Error", f"Operation failed: {err}")
        self._action_worker = None
        self.refresh_all()

    # --- DATA FETCHING & RENDERING (ASYNCHRONOUS) ---
    def refresh_all(self):
        """Reloads both datasets asynchronously."""
        self.refresh_generic_table()
        self.refresh_price_table()

    def refresh_generic_table(self):
        """Loads and renders the left generic specification items grid asynchronously."""
        if self._generic_worker and self._generic_worker.isRunning():
            return

        self._generic_worker = Worker(self.service.get_all_generic_items)
        self._generic_worker.result.connect(self._on_generic_loaded)
        self._generic_worker.error.connect(self._on_generic_load_error)
        self._generic_worker.start()

    def _on_generic_loaded(self, result):
        rows, _ = result
        self.generic_cache = list(rows)
        self._render_generic_grid(self.generic_cache)
        self._generic_worker = None

    def _on_generic_load_error(self, err):
        QMessageBox.critical(self, "Database Error", f"Could not load Generic Items: {err}")
        self._generic_worker = None

    def refresh_price_table(self):
        """Loads and renders the right price list grid asynchronously."""
        if self._price_worker and self._price_worker.isRunning():
            return

        self.price_stats.setText("Loading Price List records from database...")
        self._price_worker = Worker(self.service.get_price_list_items)
        self._price_worker.result.connect(self._on_price_loaded)
        self._price_worker.error.connect(self._on_price_load_error)
        self._price_worker.start()

    def _on_price_loaded(self, result):
        rows, _ = result
        self.price_cache = list(rows)
        
        self.populate_filter_combos()
        
        # Reset pagination current page to 1
        self.current_page = 1
        self._perform_price_search()
        self._price_worker = None

    def populate_filter_combos(self):
        self.category_filter_combo.blockSignals(True)
        self.make_filter_combo.blockSignals(True)
        
        current_cat = self.category_filter_combo.currentText()
        current_make = self.make_filter_combo.currentText()
        
        self.category_filter_combo.clear()
        self.make_filter_combo.clear()
        
        self.category_filter_combo.addItem("All Categories")
        self.make_filter_combo.addItem("All Makes")
        
        categories = set()
        makes = set()
        for row in self.price_cache:
            if row[3]:
                categories.add(str(row[3]).strip())
            if row[4]:
                makes.add(str(row[4]).strip())
                
        self.category_filter_combo.addItems(sorted(list(categories)))
        self.make_filter_combo.addItems(sorted(list(makes)))
        
        idx_cat = self.category_filter_combo.findText(current_cat)
        if idx_cat >= 0:
            self.category_filter_combo.setCurrentIndex(idx_cat)
        else:
            self.category_filter_combo.setCurrentIndex(0)
            
        idx_make = self.make_filter_combo.findText(current_make)
        if idx_make >= 0:
            self.make_filter_combo.setCurrentIndex(idx_make)
        else:
            self.make_filter_combo.setCurrentIndex(0)
            
        self.category_filter_combo.blockSignals(False)
        self.make_filter_combo.blockSignals(False)

    def _on_price_load_error(self, err):
        QMessageBox.critical(self, "Database Error", f"Could not load Price List: {err}")
        self._price_worker = None

    def _render_generic_grid(self, rows):
        self.generic_table.blockSignals(True)
        self.generic_table.setSortingEnabled(False)
        self.generic_table.setRowCount(len(rows))

        for r, row in enumerate(rows):
            # ID
            id_item = NumericTableWidgetItem(str(row[0]))
            id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
            self.generic_table.setItem(r, 0, id_item)

            # Description (Editable)
            desc_item = QTableWidgetItem(str(row[1]))
            desc_item.setFlags(desc_item.flags() | Qt.ItemIsEditable)
            self.generic_table.setItem(r, 1, desc_item)

            # Remark/Makes (Editable)
            remark_item = QTableWidgetItem(str(row[2] or ""))
            remark_item.setFlags(remark_item.flags() | Qt.ItemIsEditable)
            self.generic_table.setItem(r, 2, remark_item)

        self.generic_table.blockSignals(False)
        self.generic_table.setSortingEnabled(True)

    def _render_price_grid(self, rows):
        self.price_table.blockSignals(True)
        self.price_table.setSortingEnabled(False)
        self.price_table.setRowCount(len(rows))

        selected_generic_id = self.get_selected_generic_id()

        for r, row in enumerate(rows):
            price_id = row[0]
            mapped_generic_id = row[12]

            # 0. Checkbox Item
            cb_item = QTableWidgetItem()
            cb_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            if price_id in self.selected_price_list_ids:
                cb_item.setCheckState(Qt.Checked)
            else:
                cb_item.setCheckState(Qt.Unchecked)
            self.price_table.setItem(r, 0, cb_item)

            # 1. ID
            id_item = NumericTableWidgetItem(str(row[0]))
            id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
            self.price_table.setItem(r, 1, id_item)

            # 2. ItemDescription
            desc_item = QTableWidgetItem(str(row[1] or ""))
            desc_item.setFlags(desc_item.flags() & ~Qt.ItemIsEditable)
            self.price_table.setItem(r, 2, desc_item)

            # 3. Model
            model_item = QTableWidgetItem(str(row[2] or ""))
            model_item.setFlags(model_item.flags() & ~Qt.ItemIsEditable)
            self.price_table.setItem(r, 3, model_item)

            # 4. Category
            cat_item = QTableWidgetItem(str(row[3] or ""))
            cat_item.setFlags(cat_item.flags() & ~Qt.ItemIsEditable)
            self.price_table.setItem(r, 4, cat_item)

            # 5. Make
            make_item = QTableWidgetItem(str(row[4] or ""))
            make_item.setFlags(make_item.flags() & ~Qt.ItemIsEditable)
            self.price_table.setItem(r, 5, make_item)

            # 6. ListPrice
            lp_val = f"{float(row[5]):,.2f}" if row[5] is not None else ""
            lp_item = NumericTableWidgetItem(lp_val)
            lp_item.setFlags(lp_item.flags() & ~Qt.ItemIsEditable)
            self.price_table.setItem(r, 6, lp_item)

            # 7. DiscountPercent
            dp_val = f"{(float(row[6]) * 100):.2f}" if row[6] is not None else ""
            dp_item = NumericTableWidgetItem(dp_val)
            dp_item.setFlags(dp_item.flags() & ~Qt.ItemIsEditable)
            self.price_table.setItem(r, 7, dp_item)

            # 8. NetPrice
            np_val = f"{float(row[7]):,.2f}" if row[7] is not None else ""
            np_item = NumericTableWidgetItem(np_val)
            np_item.setFlags(np_item.flags() & ~Qt.ItemIsEditable)
            self.price_table.setItem(r, 8, np_item)

            # 9. UsedQty
            qty_val = f"{int(row[8])}" if row[8] is not None else ""
            qty_item = NumericTableWidgetItem(qty_val)
            qty_item.setFlags(qty_item.flags() & ~Qt.ItemIsEditable)
            self.price_table.setItem(r, 9, qty_item)

            # 10. TotalAmount
            tot_val = f"{float(row[9]):,.2f}" if row[9] is not None else ""
            tot_item = NumericTableWidgetItem(tot_val)
            tot_item.setFlags(tot_item.flags() & ~Qt.ItemIsEditable)
            self.price_table.setItem(r, 10, tot_item)

            # 11. GenericSpecItemID
            spec_item = NumericTableWidgetItem(str(row[12]) if row[12] is not None else "")
            spec_item.setFlags(spec_item.flags() & ~Qt.ItemIsEditable)
            self.price_table.setItem(r, 11, spec_item)

            # Soft highlight mapped rows
            if selected_generic_id is not None and mapped_generic_id == selected_generic_id:
                bg_color = QColor("#dcfce7")
                brush = QBrush(bg_color)
                for col in range(self.price_table.columnCount()):
                    item_at_col = self.price_table.item(r, col)
                    if item_at_col:
                        item_at_col.setBackground(brush)

        for col in range(9, 11):
            self.price_table.hideColumn(col)

        self.price_table.blockSignals(False)
        self.price_table.setSortingEnabled(True)
        self.update_stats_label()

    def select_generic_by_id(self, generic_id):
        """Helper to programmatically select a generic item in the left grid by ID."""
        self.generic_table.blockSignals(True)
        found = False
        for r in range(self.generic_table.rowCount()):
            id_item = self.generic_table.item(r, 0)
            if id_item and int(id_item.text()) == generic_id:
                self.generic_table.selectRow(r)
                found = True
                break
        self.generic_table.blockSignals(False)
        if found:
            self.on_generic_selection_changed()

    def select_all_visible_price_items(self):
        """Checks all visible checkboxes in the right price grid on the current page."""
        self.price_table.blockSignals(True)
        for r in range(self.price_table.rowCount()):
            cb_item = self.price_table.item(r, 0)
            id_item = self.price_table.item(r, 1)
            if cb_item and id_item:
                cb_item.setCheckState(Qt.Checked)
                self.selected_price_list_ids.add(int(id_item.text()))
        self.price_table.blockSignals(False)
        self.update_stats_label()

    def clear_price_selection(self):
        """Unchecks all checkboxes and resets selected tracker set."""
        self.selected_price_list_ids.clear()
        self.price_table.blockSignals(True)
        for r in range(self.price_table.rowCount()):
            cb_item = self.price_table.item(r, 0)
            if cb_item:
                cb_item.setCheckState(Qt.Unchecked)
        self.price_table.blockSignals(False)
        self.update_stats_label()

    def update_stats_label(self):
        selected_count = len(self.selected_price_list_ids)
        self.price_stats.setText(f"Showing {len(self.price_filtered_rows)} records (Filtered) | Selected: {selected_count} records")

    # --- SELECTION & CHECKBOX EVENTS ---
    def on_generic_selection_changed(self):
        """Called when user clicks/selects a Generic Spec Item on the left."""
        self.current_page = 1
        self._perform_price_search()

    def handle_price_checkbox_changed(self, item):
        """Tracks checked/unchecked price list IDs across searching."""
        if item.column() != 0:
            return
        row = item.row()
        id_item = self.price_table.item(row, 1)
        if id_item:
            price_id = int(id_item.text())
            if item.checkState() == Qt.Checked:
                self.selected_price_list_ids.add(price_id)
            else:
                self.selected_price_list_ids.discard(price_id)
            self.update_stats_label()

    # --- SEARCH & FILTER LOGIC ---
    def _debounce_generic_search(self):
        self.generic_search_timer.start(300)

    def _debounce_price_search(self):
        self.current_page = 1
        self.price_search_timer.start(300)

    def clear_generic_search(self):
        self.generic_search.clear()

    def clear_price_search(self):
        self.price_search.clear()
        self.category_filter_combo.setCurrentIndex(0)
        self.make_filter_combo.setCurrentIndex(0)

    def filter_linked_state_changed(self, state):
        self.current_page = 1
        self._perform_price_search()

    def price_filter_changed(self, text):
        self.current_page = 1
        self._perform_price_search()

    def _perform_generic_search(self):
        keyword = self.generic_search.text().strip().lower()
        if not keyword:
            self._render_generic_grid(self.generic_cache)
            return

        filtered = []
        for row in self.generic_cache:
            if (keyword in str(row[0]).lower() or 
                keyword in str(row[1]).lower() or 
                (row[2] and keyword in str(row[2]).lower())):
                filtered.append(row)
        self._render_generic_grid(filtered)

    def _perform_price_search(self):
        """Filters right price table based on keyword, category/make dropdowns, and selected Generic Spec link."""
        keyword = self.price_search.text().strip().lower()
        selected_generic_id = self.get_selected_generic_id()
        only_linked = self.filter_linked_cb.isChecked()
        
        selected_cat = self.category_filter_combo.currentText()
        selected_make = self.make_filter_combo.currentText()

        self.price_filtered_rows = []
        for row in self.price_cache:
            mapped_generic_id = row[12]
            cat_val = str(row[3] or "").strip()
            make_val = str(row[4] or "").strip()

            # Linkage filter
            if only_linked:
                if selected_generic_id is None:
                    continue
                if mapped_generic_id != selected_generic_id:
                    continue

            # Category filter dropdown
            if selected_cat != "All Categories" and cat_val != selected_cat:
                continue

            # Make filter dropdown
            if selected_make != "All Makes" and make_val != selected_make:
                continue

            # Text search filter
            if keyword:
                matches = (
                    keyword in str(row[0]).lower() or             # ID
                    keyword in str(row[1] or "").lower() or       # ItemDescription
                    keyword in str(row[2] or "").lower() or       # Model
                    keyword in str(row[3] or "").lower() or       # Category
                    keyword in str(row[4] or "").lower() or       # Make
                    keyword in str(row[12] or "").lower()         # GenericSpecItemID
                )
                if not matches:
                    continue

            self.price_filtered_rows.append(row)

        # Pagination calculations
        self.total_filtered = len(self.price_filtered_rows)
        self.total_pages = max(1, math.ceil(self.total_filtered / self.page_size))
        
        if self.current_page > self.total_pages:
            self.current_page = self.total_pages
        if self.current_page < 1:
            self.current_page = 1

        self.render_current_price_page()

    def render_current_price_page(self):
        """Slices the filtered rows for the current page and updates grids and buttons."""
        start_idx = (self.current_page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        page_rows = self.price_filtered_rows[start_idx:end_idx]

        self._render_price_grid(page_rows)

        # Update pagination elements
        self.page_info_label.setText(f"Page {self.current_page} of {self.total_pages}")
        self.prev_page_btn.setEnabled(self.current_page > 1)
        self.next_page_btn.setEnabled(self.current_page < self.total_pages)

    # --- PAGINATION NAVIGATION EVENTS ---
    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.render_current_price_page()

    def next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.render_current_price_page()

    def page_size_changed(self, size_str):
        try:
            self.page_size = int(size_str)
            self.current_page = 1
            self._perform_price_search()
        except ValueError:
            pass
