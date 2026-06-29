from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLineEdit, QLabel, QMessageBox, QMenu, QAbstractItemView, 
                             QFrame, QApplication, QDialog, QSplitter, QGroupBox, QGridLayout, QFileDialog, QStatusBar)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QShortcut, QKeySequence
from app.services.busbar_service import BusbarService
from app.services.excel_service import ExcelService
from app.ui.searchable_table import NumericTableWidgetItem, SearchableTable
from app.ui.busbar.busbar_form import BusbarForm
from app.ui.busbar.metal_manager import MetalManagerDialog
from app.ui.busbar.sleeve_manager import SleeveManagerDialog
from app.config.ui_state import UIStateManager
from app.utils.worker_thread import Worker

class BusbarPage(QWidget):
    def __init__(self):
        super().__init__()
        self.service = BusbarService()
        self._cache = []
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._perform_search)
        self._worker = None
        
        self.setup_ui()
        self.refresh_table()
        self._restore_state()

    def setup_ui(self):
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
        self.setStyleSheet(self.styleSheet() + btn_style + "#sidebar { background-color: #f0f2f5; } #appTitle { font-size: 20px; font-weight: bold; margin-bottom: 16px; }")
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Sidebar setup matching quotation details UI
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("sidebar")
        sidebar_frame.setFixedWidth(240)
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(20, 20, 20, 20)
        sidebar_layout.setSpacing(12)

        sidebar_title = QLabel("Busbar Menu")
        sidebar_title.setObjectName("appTitle")
        sidebar_title.setAlignment(Qt.AlignCenter)

        self.summary_btn = QPushButton("📊 Busbar Summary")
        self.summary_btn.clicked.connect(self.show_summary_view)

        self.metal_btn = QPushButton("🏭 Metal Properties")
        self.metal_btn.clicked.connect(self.open_metal_manager)

        self.sleeve_btn = QPushButton("📏 Sleeve Sizes")
        self.sleeve_btn.clicked.connect(self.open_sleeve_manager)

        sidebar_layout.addWidget(sidebar_title)
        sidebar_layout.addWidget(self.summary_btn)
        sidebar_layout.addWidget(self.metal_btn)
        sidebar_layout.addWidget(self.sleeve_btn)
        sidebar_layout.addStretch()

        self.main_layout.addWidget(sidebar_frame)

        # Main content area
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)

        self.splitter = QSplitter(Qt.Horizontal)

        # LEFT CONTAINER (Main Table)
        self.left_widget = QWidget()
        self.left_layout = QVBoxLayout(self.left_widget)
        self.left_layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        header_layout = QHBoxLayout()
        title = QLabel("Busbar Materials Entry")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search materials...")
        self.search_box.textChanged.connect(self._debounce_search)

        self.add_btn = QPushButton("➕ Add")
        self.add_btn.setToolTip("(Ctrl+N)")
        self.edit_btn = QPushButton("✏️ Edit")
        self.edit_btn.setToolTip("(Ctrl+E)")
        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.setToolTip("(Delete)")
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
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setToolTip("(Ctrl+R)")

        
        self.add_btn.clicked.connect(self.add_busbar)
        self.edit_btn.clicked.connect(self.edit_busbar)
        self.delete_btn.clicked.connect(self.delete_busbar)
        self.refresh_btn.clicked.connect(self.refresh_table)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.search_box)
        header_layout.addWidget(self.refresh_btn)
        header_layout.addWidget(self.add_btn)
        header_layout.addWidget(self.edit_btn)
        header_layout.addWidget(self.delete_btn)
        self.left_layout.addLayout(header_layout)

        # Filter Row
        filter_row = QHBoxLayout()
        self.run_filter = QLineEdit()
        self.run_filter.setPlaceholderText("Filter Run...")
        self.run_filter.textChanged.connect(self._debounce_search)

        self.width_filter = QLineEdit()
        self.width_filter.setPlaceholderText("Filter Width...")
        self.width_filter.textChanged.connect(self._debounce_search)

        self.thick_filter = QLineEdit()
        self.thick_filter.setPlaceholderText("Filter Thick...")
        self.thick_filter.textChanged.connect(self._debounce_search)

        self.clear_filters_btn = QPushButton("🧹 Clear")
        self.clear_filters_btn.setFixedWidth(80)
        self.clear_filters_btn.clicked.connect(self.clear_all_filters)

        filter_row.addWidget(QLabel("Column Filters: "))
        filter_row.addWidget(self.run_filter)
        filter_row.addWidget(self.width_filter)
        filter_row.addWidget(self.thick_filter)
        filter_row.addWidget(self.clear_filters_btn)
        filter_row.addStretch()
        self.left_layout.addLayout(filter_row)

        # Table
        self.table = SearchableTable()
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels([
            "ID", "Run Length", "Width", "Thick", "Metal", 
            "Density", "Cost/Kg", "Sleeve Width", "Special Rate", 
            "Normal Rate", "MetalID", "SlevID"
        ])
        self.table.hideColumn(0)
        self.table.hideColumn(10)
        self.table.hideColumn(11)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        self.table.setStyleSheet("QTableView { selection-background-color: #93c5fd; selection-color: #000000; } QHeaderView::section { background-color: #fce4ec; border: 1px solid #e2e8f0; }")
        # Enable movable columns and rows
        self.table.horizontalHeader().setSectionsMovable(True)
        self.table.verticalHeader().setSectionsMovable(True)

        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.open_context_menu)
        self.left_layout.addWidget(self.table)

        # RIGHT CONTAINER (Summary View)
        self.right_widget = QFrame()
        self.right_widget.setFrameShape(QFrame.StyledPanel)
        self.right_layout = QVBoxLayout(self.right_widget)
        self.setup_summary_view()
        self.right_widget.hide() # Hidden by default

        self.splitter.addWidget(self.left_widget)
        self.splitter.addWidget(self.right_widget)
        self.splitter.setStretchFactor(0, 2)
        self.splitter.setStretchFactor(1, 1)
        
        self.content_layout.addWidget(self.splitter)

        # Footer Status Bar for selection statistics
        self.status_bar = QStatusBar()
        self.status_bar.setSizeGripEnabled(False)
        self.status_bar.setStyleSheet("QStatusBar { background-color: #f8fafc; color: #475569; border-top: 1px solid #e2e8f0; max-height: 25px; }")
        self.content_layout.addWidget(self.status_bar)

        self.main_layout.addWidget(content_widget, 1)

        self.table.itemSelectionChanged.connect(self._update_status_bar_stats)

        # Shortcuts
        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(self.add_busbar)
        QShortcut(QKeySequence("Ctrl+E"), self).activated.connect(self.edit_busbar)
        QShortcut(QKeySequence("Ctrl+R"), self).activated.connect(self.refresh_table)
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(self.search_box.setFocus)
        QShortcut(QKeySequence(Qt.Key_Delete), self).activated.connect(self.delete_busbar)

    def _update_status_bar_stats(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            self.status_bar.clearMessage()
            return

        count = len(selected_rows)
        msg = f"Count: {count}"
        self.status_bar.showMessage(msg)

    def setup_summary_view(self):
        # Header with Title and Close button
        title_bar = QHBoxLayout()
        title = QLabel("Busbar Summary Analysis (vw)")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #1e293b;")

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(20, 20)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton { border: none; background: transparent; font-size: 14px; color: #94a3b8; }
            QPushButton:hover { color: #ef4444; }
        """)
        close_btn.clicked.connect(lambda: self.right_widget.hide())

        title_bar.addWidget(title)
        title_bar.addStretch()
        title_bar.addWidget(close_btn)
        self.right_layout.addLayout(title_bar)

        # Filter Blocks
        filter_group = QGroupBox("Report Filters")
        filter_grid = QGridLayout(filter_group)
        
        self.f_metal = QLineEdit(); self.f_metal.setPlaceholderText("Metal")
        self.f_run = QLineEdit(); self.f_run.setPlaceholderText("Run")
        self.f_width = QLineEdit(); self.f_width.setPlaceholderText("Width")
        self.f_thick = QLineEdit(); self.f_thick.setPlaceholderText("Thick")
        self.f_amp_min = QLineEdit(); self.f_amp_min.setPlaceholderText("Amps Min")
        self.f_amp_max = QLineEdit(); self.f_amp_max.setPlaceholderText("Amps Max")

        filter_grid.addWidget(QLabel("Metal:"), 0, 0); filter_grid.addWidget(self.f_metal, 0, 1)
        filter_grid.addWidget(QLabel("Run:"), 0, 2); filter_grid.addWidget(self.f_run, 0, 3)
        filter_grid.addWidget(QLabel("Width:"), 1, 0); filter_grid.addWidget(self.f_width, 1, 1)
        filter_grid.addWidget(QLabel("Thick:"), 1, 2); filter_grid.addWidget(self.f_thick, 1, 3)
        filter_grid.addWidget(QLabel("Amp Range:"), 2, 0); filter_grid.addWidget(self.f_amp_min, 2, 1); filter_grid.addWidget(self.f_amp_max, 2, 3)

        self.right_layout.addWidget(filter_group)

        # Action Buttons
        btn_layout = QHBoxLayout()
        apply_btn = QPushButton("🔍 Apply Filter"); apply_btn.clicked.connect(self.apply_summary_filters); apply_btn.setStyleSheet("background-color: #D2B48C;")
        clear_btn = QPushButton("🧹 Clear Filter"); clear_btn.clicked.connect(self.clear_summary_filters); clear_btn.setStyleSheet("background-color: #D2B48C;")
        refresh_v_btn = QPushButton("🔄 Refresh View"); refresh_v_btn.clicked.connect(self.apply_summary_filters); refresh_v_btn.setStyleSheet("background-color: #D2B48C;")
        export_btn = QPushButton("📊 Export Excel"); export_btn.clicked.connect(self.export_summary_excel); export_btn.setStyleSheet("background-color: #D2B48C;")
        
        btn_layout.addWidget(apply_btn); btn_layout.addWidget(clear_btn); btn_layout.addWidget(refresh_v_btn); btn_layout.addWidget(export_btn)
        self.right_layout.addLayout(btn_layout)

        self.summary_table = SearchableTable()
        self.summary_table.setStyleSheet("QTableView { selection-background-color: #93c5fd; selection-color: #000000; } QHeaderView::section { background-color: #fce4ec; border: 1px solid #e2e8f0; }")
        self.summary_table.setColumnCount(13)
        self.summary_table.setHorizontalHeaderLabels([
            "Size", "CalAmps", "Metal Kg/m", "Rs/Meter", "Run", "BBSize", 
            "Metal", "Width", "Thick", "CDen", "Cost/Kg", "Sleeve Rs", "Final Cost"
        ])
        self.right_layout.addWidget(self.summary_table)

    def apply_summary_filters(self):
        filters = {
            'run': self.f_run.text().strip(),
            'metal': self.f_metal.text().strip(),
            'width': self.f_width.text().strip(),
            'thick': self.f_thick.text().strip(),
            'min_amps': self.f_amp_min.text().strip(),
            'max_amps': self.f_amp_max.text().strip()
        }
        filters = {k: v for k, v in filters.items() if v}
        data = self.service.get_summary_view(filters)
        self._render_summary(data)

    def clear_summary_filters(self):
        for widget in [self.f_run, self.f_metal, self.f_width, self.f_thick, self.f_amp_min, self.f_amp_max]:
            widget.clear()
        self.apply_summary_filters()

    def _render_summary(self, rows):
        self.summary_table.setSortingEnabled(False)
        self.summary_table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, val in enumerate(row[1:]):  # Skip 'ID' column
                self.summary_table.setItem(i, j, NumericTableWidgetItem(str(val or "")))
        self.summary_table.setSortingEnabled(True)
        self.summary_table.fix_column_widths()

    def export_summary_excel(self):
        # Export full summary view without filters as requested
        data = self.service.get_summary_view(filters=None)
        export_data = [row[1:] for row in data]  # Skip 'ID' column
        headers = ["Size", "CalAmps", "MetalKgPerMeter", "RsUnitMeter", "Run", "BBSize", "Metal", "Width", "Thick", "Current Density", "Unit Cost", "Sleeve Rs", "Final Cost"]
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Full Summary Report", "", "Excel Files (*.xlsx)")
        if file_path:
            ExcelService().export(headers, export_data, file_path)
            QMessageBox.information(self, "Export", "Summary report exported successfully.")

    def refresh_table(self):
        self.clear_all_filters()
        if self._worker and self._worker.isRunning():
            return
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self._worker = Worker(self.service.get_all_busbars)
        self._worker.result.connect(self._on_data_loaded)
        self._worker.start()

    def clear_all_filters(self):
        """Resets all search fields which triggers re-render via textChanged signals."""
        self.search_box.clear()
        self.run_filter.clear()
        self.width_filter.clear()
        self.thick_filter.clear()

    def _on_data_loaded(self, data):
        self._cache = list(data)
        self._render(self._cache)
        QApplication.restoreOverrideCursor()
        self._worker = None

    def _render(self, rows):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                item = NumericTableWidgetItem(str(val or ""))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(i, j, item)
        self.table.setSortingEnabled(True)
        self._restore_state()

    def _save_state(self):
        """Save header state to UIStateManager."""
        header_state = self.table.horizontalHeader().saveState()
        v_header_state = self.table.verticalHeader().saveState()
        if hasattr(UIStateManager, 'save_busbar_page_state'):
            UIStateManager.save_busbar_page_state({
                "header_state": header_state, 
                "v_header_state": v_header_state
            })

    def _restore_state(self):
        """Restore header state from UIStateManager."""
        if hasattr(UIStateManager, 'get_busbar_page_state'):
            state = UIStateManager.get_busbar_page_state()
            if state:
                if state.get("header_state"):
                    self.table.horizontalHeader().restoreState(state["header_state"])
                if state.get("v_header_state"):
                    self.table.verticalHeader().restoreState(state["v_header_state"])

    def _debounce_search(self):
        self._search_timer.stop()
        self._search_timer.start(300)

    def _perform_search(self):
        general_kw = self.search_box.text().lower()
        run_kw = self.run_filter.text().lower()
        width_kw = self.width_filter.text().lower()
        thick_kw = self.thick_filter.text().lower()

        if not any([general_kw, run_kw, width_kw, thick_kw]):
            self._render(self._cache)
            return

        filtered = []
        for row in self._cache:
            # General keyword match across visible data columns (0-9)
            match_general = True
            if general_kw:
                search_content = " ".join(map(str, row[:10])).lower()
                match_general = general_kw in search_content
            
            # Specific field matches (AND logic)
            # row indices: 1=Run, 2=Width, 3=Thick
            match_run = not run_kw or run_kw in str(row[1] or "").lower()
            match_width = not width_kw or width_kw in str(row[2] or "").lower()
            match_thick = not thick_kw or thick_kw in str(row[3] or "").lower()

            if match_general and match_run and match_width and match_thick:
                filtered.append(row)

        self._render(filtered)

    def open_context_menu(self, pos):
        index = self.table.indexAt(pos)
        if not index.isValid(): return
        
        row = index.row()
        bb_id = int(self.table.item(row, 0).text())

        menu = QMenu(self)
        menu.addSection("Analysis")
        view_summary_action = menu.addAction("View Busbar Summary Table")
        menu.addSeparator()
        menu.addSection("Actions")
        menu.addAction("Edit Busbar", self.edit_busbar)
        menu.addAction("Delete Busbar", self.delete_busbar)
        menu.addSeparator()
        menu.addSection("Relations")
        menu.addAction("Metal Properties Manager", self.open_metal_manager)
        menu.addAction("Sleeve Sizes Manager", self.open_sleeve_manager)

        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        if action == view_summary_action:
            self.right_widget.show()
            self.apply_summary_filters()

    def add_busbar(self):
        dialog = BusbarForm(self)
        if dialog.exec() == QDialog.Accepted:
            self.service.create_busbar(dialog.get_data())
            self.refresh_table()

    def edit_busbar(self):
        sel = self.table.selectedItems()
        if not sel: return
        bb_id = int(self.table.item(sel[0].row(), 0).text())
        item_data = self.service.get_busbar(bb_id)
        
        dialog = BusbarForm(self, item_data)
        if dialog.exec() == QDialog.Accepted:
            self.service.update_busbar(bb_id, dialog.get_data())
            self.refresh_table()

    def delete_busbar(self):
        sel = self.table.selectedItems()
        if not sel: return
        bb_id = int(self.table.item(sel[0].row(), 0).text())
        if QMessageBox.question(self, "Delete", "Delete selected busbar entry?") == QMessageBox.Yes:
            self.service.delete_busbar(bb_id)
            self.refresh_table()

    def show_summary_view(self):
        self.right_widget.show()
        self.apply_summary_filters()

    def open_metal_manager(self):
        dialog = MetalManagerDialog(self)
        dialog.exec()
        self.refresh_table()

    def open_sleeve_manager(self):
        dialog = SleeveManagerDialog(self)
        dialog.exec()
        self.refresh_table()
