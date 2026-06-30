"""
price_revision_page.py
----------------------
Read-only price revision history page for tblPriceRevision.
- Left: table showing all revisions (PriceListID, Description, Model, Price, Date)
- Right: embedded matplotlib trend chart for the selected item (slides open on row select)
- No CRUD operations – view only.
"""
import os
os.environ.setdefault("MPLBACKEND", "QtAgg")

import matplotlib
matplotlib.use("QtAgg")

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QAbstractItemView, QStatusBar,
    QSplitter, QHeaderView, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QShortcut, QKeySequence

from app.services.price_list_service import PriceListService
from app.ui.searchable_table import SearchableTable, NumericTableWidgetItem
from app.utils.worker_thread import Worker


# ============================================================================
# Embedded trend chart
# ============================================================================
class PriceTrendChart(QWidget):
    """Embeddable matplotlib canvas that plots price over time for one item."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._fig = Figure(figsize=(5, 4), tight_layout=True)
        self._ax  = self._fig.add_subplot(111)
        self._canvas = FigureCanvas(self._fig)
        self._canvas.setMinimumWidth(320)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Title row
        self._title_lbl = QLabel("Select a row to see the price trend")
        self._title_lbl.setStyleSheet(
            "font-weight: bold; font-size: 13px; color: #0c4a6e; padding: 4px 0;"
        )
        self._title_lbl.setAlignment(Qt.AlignCenter)

        layout.addWidget(self._title_lbl)
        layout.addWidget(self._canvas, stretch=1)

        self._draw_empty()

    def _draw_empty(self):
        self._ax.clear()
        self._ax.set_facecolor("#f8fafc")
        self._fig.patch.set_facecolor("#f8fafc")
        self._ax.text(
            0.5, 0.5, "No data to display",
            ha="center", va="center", fontsize=12, color="#94a3b8",
            transform=self._ax.transAxes
        )
        self._ax.axis("off")
        self._canvas.draw()

    def plot(self, description: str, model: str, rows: list):
        """
        rows: list of (PriceListID, ListPrice, UpdatedAt)  – oldest first
        """
        self._ax.clear()
        self._fig.patch.set_facecolor("#ffffff")

        if not rows:
            self._draw_empty()
            self._title_lbl.setText(f"{description}  [{model}]  — No history")
            return

        dates  = [r[2] for r in rows]   # UpdatedAt (datetime)
        prices = [float(r[1]) for r in rows]  # ListPrice

        # --- Plot ---
        self._ax.plot(
            dates, prices,
            marker="o", markersize=5,
            linestyle="-", linewidth=1.8,
            color="#3b82f6",
            markerfacecolor="#0c4a6e"
        )
        self._ax.fill_between(dates, prices, alpha=0.08, color="#3b82f6")

        # Annotate points where price changes
        prev_price = None
        for d, p in zip(dates, prices):
            if p != prev_price:
                pct_text = ""
                if prev_price is not None and prev_price != 0:
                    pct_change = ((p - prev_price) / prev_price) * 100
                    sign = "+" if pct_change > 0 else ""
                    pct_text = f" ({sign}{pct_change:.1f}%)"
                
                annotation_text = f"₹{p:,.2f}{pct_text}"
                
                self._ax.annotate(
                    annotation_text,
                    xy=(d, p),
                    xytext=(0, 6), textcoords="offset points",
                    ha="center", va="bottom",
                    fontsize=8, color="#0c4a6e", fontweight="bold"
                )
                prev_price = p

        # Format x-axis dates
        self._ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
        self._ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        self._fig.autofmt_xdate(rotation=35, ha="right")

        # Labels
        self._ax.set_ylabel("List Price (₹)", fontsize=9, color="#475569")
        self._ax.set_xlabel("Date", fontsize=9, color="#475569")
        self._ax.grid(True, linestyle="--", alpha=0.4, color="#cbd5e1")
        self._ax.set_facecolor("#f8fafc")
        self._ax.tick_params(axis="both", labelsize=8, colors="#475569")
        for spine in self._ax.spines.values():
            spine.set_edgecolor("#e2e8f0")

        self._canvas.draw()
        self._title_lbl.setText(f"📈  {description}  [{model}]")


# ============================================================================
# Revision Page
# ============================================================================
class PriceRevisionPage(QWidget):
    """
    Read-only page showing all records from tblPriceRevision.
    Selecting a row opens an embedded price-trend chart in the right panel.
    """

    COL_ID    = 0   # PriceListID (hidden)
    COL_DESC  = 1   # ItemDescription
    COL_MODEL = 2   # Model
    COL_PRICE = 3   # ListPrice
    COL_DATE  = 4   # UpdatedAt

    HEADERS = ["ID", "Description", "Model", "List Price", "Updated At"]

    def __init__(self):
        super().__init__()
        self.service       = PriceListService()
        self._cache        = []          # all revision rows
        self._trend_cache  = {}          # {price_list_id: [rows]}
        self._worker       = None
        self._trend_worker = None
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._perform_search)
        self._last_selected_id = None
        self._view_mode = "all"

        self._apply_styles()
        self._setup_ui()
        self.refresh_table()

    # ------------------------------------------------------------------
    # Styling
    # ------------------------------------------------------------------
    def _apply_styles(self):
        self.setStyleSheet("""
            QPushButton {
                background-color: #e0f2fe; color: #0c4a6e;
                border: 1px solid #bae6fd; padding: 6px 14px;
                border-radius: 4px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover   { background-color: #bae6fd; }
            QPushButton:pressed { background-color: #7dd3fc; }
            QPushButton:disabled { background-color: transparent; color: #94a3b8; border: none; }
        """)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(4)

        # ── Toolbar ───────────────────────────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(6, 6, 6, 0)

        title_lbl = QLabel("Price Revision History")
        title_lbl.setStyleSheet("font-size: 17px; font-weight: bold;")

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search description, model…")
        self.search_box.setMinimumWidth(220)
        self.search_box.textChanged.connect(self._debounce_search)

        self.btn_all_items = QPushButton("📋 All Items")
        self.btn_all_items.clicked.connect(self.load_all_items)
        
        self.btn_updated_items = QPushButton("⭐ Updated Items")
        self.btn_updated_items.setToolTip("Show only items with multiple revisions")
        self.btn_updated_items.clicked.connect(self.load_updated_items)

        self.btn_refresh = QPushButton("🔄 Refresh")
        self.btn_refresh.clicked.connect(self.refresh_table)

        toolbar.addWidget(title_lbl)
        toolbar.addStretch()
        toolbar.addWidget(self.btn_all_items)
        toolbar.addWidget(self.btn_updated_items)
        toolbar.addWidget(self.search_box)
        toolbar.addWidget(self.btn_refresh)
        root.addLayout(toolbar)

        # ── Splitter: table | trend chart ────────────────────────────
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(2)
        self.splitter.setStyleSheet("QSplitter::handle { background-color: #e2e8f0; }")

        # -- Left: revision table
        self.table = SearchableTable()
        self.table.setStyleSheet(
            "QTableView { selection-background-color: #93c5fd; selection-color: #000000; } "
            "QHeaderView::section { background-color: #fce4ec; border: 1px solid #e2e8f0; "
            "padding: 4px; font-weight: bold; }"
        )
        self.table.setColumnCount(len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSortingEnabled(True)
        self.table.hideColumn(self.COL_ID)

        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(self.COL_DESC,  QHeaderView.Stretch)
        hdr.setSectionResizeMode(self.COL_MODEL, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(self.COL_PRICE, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(self.COL_DATE,  QHeaderView.ResizeToContents)

        self.table.selectionModel().selectionChanged.connect(self._on_row_selected)
        self.splitter.addWidget(self.table)

        # -- Right: trend chart panel
        chart_container = QFrame()
        chart_container.setObjectName("chartPanel")
        chart_container.setStyleSheet(
            "#chartPanel { background: #ffffff; border-left: 1px solid #e2e8f0; }"
        )
        chart_layout = QVBoxLayout(chart_container)
        chart_layout.setContentsMargins(6, 6, 6, 6)

        self.trend_chart = PriceTrendChart()
        chart_layout.addWidget(self.trend_chart)

        self.splitter.addWidget(chart_container)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 2)
        root.addWidget(self.splitter, stretch=1)

        # ── Status bar ───────────────────────────────────────────────
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(
            "QStatusBar { background-color: #f8fafc; color: #475569; "
            "border-top: 1px solid #e2e8f0; font-size: 11px; }"
        )
        root.addWidget(self.status_bar)

        # Shortcuts
        QShortcut(QKeySequence("Ctrl+R"), self, activated=self.refresh_table)
        QShortcut(QKeySequence.Find,      self, activated=lambda: self.search_box.setFocus())

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------
    def load_all_items(self):
        self._view_mode = "all"
        self.refresh_table()

    def load_updated_items(self):
        self._view_mode = "updated"
        self.refresh_table()

    def refresh_table(self):
        if self._worker and self._worker.isRunning():
            return
            
        mode_text = "Updated items" if self._view_mode == "updated" else "All items"
        self.status_bar.showMessage(f"Loading {mode_text.lower()} revision history…")
        
        self.btn_refresh.setEnabled(False)
        self.btn_all_items.setEnabled(False)
        self.btn_updated_items.setEnabled(False)
        
        self._trend_cache.clear()
        
        if self._view_mode == "updated":
            self._worker = Worker(self.service.get_updated_items_revisions)
        else:
            self._worker = Worker(self.service.get_all_price_revisions)
            
        self._worker.result.connect(self._on_loaded)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_loaded(self, rows):
        self._cache = list(rows)
        self._render(self._cache)
        self.status_bar.showMessage(f"Loaded {len(rows)} revision record(s)", 5000)
        self.btn_refresh.setEnabled(True)
        self.btn_all_items.setEnabled(True)
        self.btn_updated_items.setEnabled(True)
        self._worker = None

    def _on_error(self, err):
        QMessageBox.critical(self, "Database Error", f"Failed to load revision history:\n{err}")
        self.status_bar.clearMessage()
        self.btn_refresh.setEnabled(True)
        self.btn_all_items.setEnabled(True)
        self.btn_updated_items.setEnabled(True)
        self._worker = None

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def _render(self, rows):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                if hasattr(val, "strftime"):          # datetime
                    text = val.strftime("%d-%m-%Y %H:%M")
                elif c == self.COL_PRICE and val is not None:
                    text = f"{float(val):,.2f}"
                else:
                    text = str(val) if val is not None else ""
                item = NumericTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(r, c, item)
        self.table.setSortingEnabled(True)

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
        filtered = [
            row for row in self._cache
            if keyword in str(row[self.COL_DESC] or "").lower()
            or keyword in str(row[self.COL_MODEL] or "").lower()
        ]
        self._render(filtered)

    # ------------------------------------------------------------------
    # Chart – load trend for selected row
    # ------------------------------------------------------------------
    def _on_row_selected(self, selected, deselected):
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return
        row = indexes[0].row()
        price_list_id = self.table.item(row, self.COL_ID)
        if not price_list_id:
            return
        pid       = int(price_list_id.text())
        desc_item = self.table.item(row, self.COL_DESC)
        mod_item  = self.table.item(row, self.COL_MODEL)
        desc  = desc_item.text() if desc_item else ""
        model = mod_item.text()  if mod_item  else ""

        if pid == self._last_selected_id:
            return   # same item selected again, chart already shown
        self._last_selected_id = pid

        # Use cached data if available
        if pid in self._trend_cache:
            self.trend_chart.plot(desc, model, self._trend_cache[pid])
            return

        # Load asynchronously
        self.status_bar.showMessage(f"Loading trend for: {desc}…")
        if self._trend_worker and self._trend_worker.isRunning():
            return  # don't stack workers

        self._trend_worker = Worker(self.service.get_price_revisions, pid)
        self._trend_worker.result.connect(
            lambda rows, d=desc, m=model, p=pid: self._on_trend_loaded(rows, d, m, p)
        )
        self._trend_worker.error.connect(self._on_trend_error)
        self._trend_worker.start()

    def _on_trend_loaded(self, rows, description, model, price_list_id):
        self._trend_cache[price_list_id] = list(rows)
        self.trend_chart.plot(description, model, self._trend_cache[price_list_id])
        self.status_bar.showMessage(
            f"{len(rows)} revision point(s) for {description}", 4000
        )
        self._trend_worker = None

    def _on_trend_error(self, err):
        QMessageBox.warning(self, "Chart Error", f"Could not load trend data:\n{err}")
        self._trend_worker = None
