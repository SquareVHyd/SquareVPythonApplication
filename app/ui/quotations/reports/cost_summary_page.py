from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QHeaderView, QAbstractItemView,
    QLineEdit, QFormLayout, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QBrush, QColor
from app.ui.searchable_table import SearchableTable, NumericTableWidgetItem
from app.services.quotation_service import QuotationService

# Icon constants for the Select column
ICON_SELECTED   = "✅"
ICON_UNSELECTED = "☐"

def format_currency(value):
    try:
        val = float(value)
        return f"₹{val:,.2f}"
    except (ValueError, TypeError):
        return "₹0.00"


class CostSummaryPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = QuotationService()
        self.quote_id = None
        self.project_name = ""
        self._panel_ids = []
        self.setup_ui()

    # ------------------------------------------------------------------
    # Column indices (centralised for easy maintenance)
    # ------------------------------------------------------------------
    COL_NAME      = 0
    COL_QTY       = 1
    COL_PROCESS   = 2
    COL_STEEL     = 3
    COL_BUSBAR    = 4
    COL_PAINTING  = 5
    COL_GASKET    = 6
    COL_ELEC      = 7
    COL_HARDWARE  = 8
    COL_LABOUR    = 9
    COL_PACKING   = 10
    COL_LANDED    = 11
    COL_TOTAL_L   = 12
    COL_OTHER     = 13
    COL_OVERHEAD  = 14
    COL_PROFIT    = 15
    COL_SELECT    = 16   # ← beside Profit %
    COL_FINAL     = 17

    # ------------------------------------------------------------------
    # UI Setup
    # ------------------------------------------------------------------
    def setup_ui(self):
        self.layout = QVBoxLayout(self)

        # ── Title / Refresh ──────────────────────────────────────────
        header = QHBoxLayout()
        self.title_label = QLabel("Cost Summary")
        self.title_label.setStyleSheet(
            "font-size: 22px; font-weight: bold; color: #0f172a;"
        )
        self.refresh_btn = QPushButton("🔄 Recalculate")
        self.refresh_btn.setStyleSheet(
            "QPushButton { padding: 5px 12px; border-radius: 4px; "
            "background-color: #e2e8f0; border: 1px solid #cbd5e1; } "
            "QPushButton:hover { background-color: #cbd5e1; }"
        )
        self.refresh_btn.clicked.connect(self.refresh_view)
        header.addWidget(self.title_label)
        header.addStretch()
        header.addWidget(self.refresh_btn)
        self.layout.addLayout(header)

        # ── Unit Costs Frame (QLineEdit, no spinbox) ─────────────────
        self.costs_frame = QFrame()
        self.costs_frame.setStyleSheet(
            "QFrame { background-color: #f8fafc; border: 1px solid #cbd5e1;"
            " border-radius: 6px; }"
        )
        costs_layout = QHBoxLayout(self.costs_frame)
        costs_layout.setContentsMargins(15, 10, 15, 10)
        costs_layout.setSpacing(10)

        self.lineedits = {}
        le_style = (
            "QLineEdit { padding: 4px 8px; border: 1px solid #94a3b8; "
            "border-radius: 4px; background-color: white; min-width: 90px; }"
            "QLineEdit:focus { border: 1px solid #3b82f6; }"
        )

        def make_le():
            le = QLineEdit()
            le.setPlaceholderText("0.00")
            le.setStyleSheet(le_style)
            le.editingFinished.connect(self._on_header_costs_changed)
            return le

        form1 = QFormLayout(); form1.setSpacing(6)
        self.lineedits['aluminium'] = make_le()
        self.lineedits['copper']    = make_le()
        self.lineedits['steel']     = make_le()
        form1.addRow("Unit Al Cost (₹):",     self.lineedits['aluminium'])
        form1.addRow("Unit Copper Cost (₹):", self.lineedits['copper'])
        form1.addRow("Unit Steel Cost (₹):",  self.lineedits['steel'])

        form2 = QFormLayout(); form2.setSpacing(6)
        self.lineedits['painting']   = make_le()
        self.lineedits['gasket']     = make_le()
        self.lineedits['electrical'] = make_le()
        form2.addRow("Paint Cost/sqft (₹):",  self.lineedits['painting'])
        form2.addRow("Unit Gasket Cost (₹):", self.lineedits['gasket'])
        form2.addRow("Unit Elec Cost (₹):",   self.lineedits['electrical'])

        # ── Apply Profit section ──────────────────────────────────────
        profit_frame = QFrame()
        profit_frame.setStyleSheet(
            "QFrame { background-color: #eff6ff; border: 1px solid #bfdbfe;"
            " border-radius: 5px; }"
        )
        profit_inner = QVBoxLayout(profit_frame)
        profit_inner.setContentsMargins(10, 8, 10, 8)
        profit_inner.setSpacing(6)

        profit_title = QLabel("<b>Apply Profit %</b>")
        profit_title.setStyleSheet("font-size: 12px; color: #1e40af; border: none;")

        profit_row = QHBoxLayout()
        self.profit_input = QLineEdit()
        self.profit_input.setPlaceholderText("e.g. 10")
        self.profit_input.setStyleSheet(le_style)
        self.profit_input.setMaximumWidth(70)

        self.apply_profit_btn = QPushButton("✅ Apply Profit %")
        self.apply_profit_btn.setStyleSheet(
            "QPushButton { background-color: #2563eb; color: white; border-radius: 4px;"
            " padding: 5px 10px; font-weight: bold; border: none; } "
            "QPushButton:hover { background-color: #1d4ed8; }"
        )
        self.apply_profit_btn.clicked.connect(self._apply_profit)

        profit_row.addWidget(QLabel("Profit %:"))
        profit_row.addWidget(self.profit_input)
        profit_row.addWidget(self.apply_profit_btn)
        profit_row.addStretch()

        profit_inner.addWidget(profit_title)
        profit_inner.addLayout(profit_row)

        costs_layout.addLayout(form1)
        costs_layout.addSpacing(15)
        costs_layout.addLayout(form2)
        costs_layout.addSpacing(15)
        costs_layout.addWidget(profit_frame)
        costs_layout.addStretch()

        self.layout.addWidget(self.costs_frame)

        # ── Table (18 cols) ───────────────────────────────────────────
        self.table = SearchableTable()
        self.table.setStyleSheet(
            "QTableWidget { gridline-color: #e2e8f0; }"
            "QHeaderView::section { background-color: #f1f5f9; font-weight: bold;"
            " border: 1px solid #e2e8f0; padding: 4px; }"
        )
        self.table.setColumnCount(18)
        self.table.setHorizontalHeaderLabels([
            "Panel Name", "Qty", "Process Price", "Steel Cost", "Busbar Cost",
            "Painting", "Gasket", "Electrical", "Hardware", "Labour", "Packing",
            "Landed/Panel", "Total Landed",
            "Other Cost", "Overhead Cost", "Profit %",
            "Select",           # col 16 — beside Profit %
            "Final Offer Cost"  # col 17
        ])

        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)

        hv = self.table.horizontalHeader()
        hv.setSectionResizeMode(QHeaderView.Interactive)
        hv.setSectionResizeMode(self.COL_SELECT, QHeaderView.Fixed)
        self.table.setColumnWidth(self.COL_SELECT, 60)

        self.table.itemChanged.connect(self._on_item_changed)
        # Toggle select icon on click
        self.table.itemClicked.connect(self._on_item_clicked)

        self.layout.addWidget(self.table)

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------
    def load_quotation(self, quote_id, project_name):
        self.quote_id = quote_id
        self.project_name = project_name
        self.title_label.setText(f"Cost Summary: {project_name}")
        self.refresh_view()

    # ------------------------------------------------------------------
    # Header cost inputs changed
    # ------------------------------------------------------------------
    def _on_header_costs_changed(self):
        if not self.quote_id:
            return

        def sf(key):
            try:
                return float(self.lineedits[key].text() or 0)
            except ValueError:
                return 0.0

        new_costs = {k: sf(k) for k in self.lineedits}
        try:
            self.service.update_quote_unit_costs(self.quote_id, new_costs)
            self.refresh_view()
        except Exception as e:
            print(f"Error updating unit costs: {e}")

    # ------------------------------------------------------------------
    # Refresh / Populate table
    # ------------------------------------------------------------------
    def refresh_view(self):
        if not self.quote_id:
            return

        # 1. Unit cost header
        costs_dict = self.service.get_quote_unit_costs(self.quote_id)
        for k, le in self.lineedits.items():
            le.blockSignals(True)
            le.setText(str(costs_dict.get(k, 0.0)))
            le.blockSignals(False)

        # 2. Table rows
        panels = self.service.get_panels_by_quote(self.quote_id)
        self.table.setRowCount(len(panels))
        self.table.blockSignals(True)
        self._panel_ids = []

        for r, p_row in enumerate(panels):
            pid  = p_row[0]
            name = p_row[4]
            self._panel_ids.append(pid)

            try:
                qty = int(p_row[5] or 1)
            except ValueError:
                qty = 1

            def safe(idx):
                try:
                    return float(p_row[idx] or 0.0)
                except (IndexError, TypeError, ValueError):
                    return 0.0

            saved_profit   = safe(14)
            saved_other    = safe(15)
            saved_overhead = safe(16)

            unit_process = self.service.calculate_panel_process_cost(pid)
            unit_steel   = self.service.calculate_panel_steel_cost(pid, self.quote_id)
            unit_busbar  = self.service.calculate_panel_busbar_cost(pid, self.quote_id)

            l, h, d   = self.service.get_panel_dimensions(pid)
            area_mm2  = (2 * (l * h + l * d + d * h)) * 1.05
            area_sqft = area_mm2 / 92903.04
            painting_cost = area_sqft * costs_dict.get("painting", 20.0)

            # Col 0 — Panel Name (carries panel ID)
            name_item = self._make_cell(name, editable=False)
            name_item.setData(Qt.UserRole, pid)
            self.table.setItem(r, self.COL_NAME, name_item)

            self.table.setItem(r, self.COL_QTY,     self._make_cell(qty, editable=False))
            self.table.setItem(r, self.COL_PROCESS,  self._make_cell(f"{unit_process:.2f}", editable=False))
            self.table.setItem(r, self.COL_STEEL,    self._make_cell(f"{unit_steel:.2f}",   editable=False))
            self.table.setItem(r, self.COL_BUSBAR,   self._make_cell(f"{unit_busbar:.2f}",  editable=False))
            self.table.setItem(r, self.COL_PAINTING, self._make_cell(f"{painting_cost:.2f}", editable=True))

            for c in range(self.COL_GASKET, self.COL_PACKING + 1):
                self.table.setItem(r, c, self._make_cell("0.00", editable=True))

            self.table.setItem(r, self.COL_LANDED,   self._make_cell("0.00", editable=False))
            self.table.setItem(r, self.COL_TOTAL_L,  self._make_cell("0.00", editable=False))
            self.table.setItem(r, self.COL_OTHER,    self._make_cell(f"{saved_other:.2f}",    editable=True))
            self.table.setItem(r, self.COL_OVERHEAD, self._make_cell(f"{saved_overhead:.2f}", editable=True))
            self.table.setItem(r, self.COL_PROFIT,   self._make_cell(f"{saved_profit:.2f}",   editable=True))

            # Col 16 — Select toggle icon (in-memory only, not editable via text)
            sel_item = NumericTableWidgetItem(ICON_UNSELECTED)
            sel_item.setFlags(Qt.ItemIsEnabled)   # not editable, click handled via itemClicked
            sel_item.setTextAlignment(Qt.AlignCenter)
            sel_item.setFont(QFont("Segoe UI Emoji", 12))
            self.table.setItem(r, self.COL_SELECT, sel_item)

            self.table.setItem(r, self.COL_FINAL, self._make_cell("0.00", editable=False, bold_red=True))

            self._recalc_row(r)

        self.table.blockSignals(False)
        self.table.resizeColumnsToContents()
        self.table.setColumnWidth(self.COL_SELECT, 60)

    # ------------------------------------------------------------------
    # Cell factory — no background colour on any cell
    # ------------------------------------------------------------------
    def _make_cell(self, text, editable, bold_red=False):
        item = NumericTableWidgetItem(str(text))
        if editable:
            item.setFlags(item.flags() | Qt.ItemIsEditable)
        else:
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            if bold_red:
                font = QFont(); font.setBold(True)
                item.setFont(font)
                item.setForeground(QBrush(QColor("#b91c1c")))
        return item

    # Alias for any external callers
    def _create_item(self, text, editable, bold_red=False):
        return self._make_cell(text, editable, bold_red)

    # ------------------------------------------------------------------
    # Select column toggle on click
    # ------------------------------------------------------------------
    def _on_item_clicked(self, item):
        if item.column() != self.COL_SELECT:
            return
        current = item.text()
        item.setText(ICON_UNSELECTED if current == ICON_SELECTED else ICON_SELECTED)

    # ------------------------------------------------------------------
    # Apply Profit % dialog
    # ------------------------------------------------------------------
    def _apply_profit(self):
        try:
            profit_pct = float(self.profit_input.text() or 0)
        except ValueError:
            QMessageBox.warning(self, "Invalid Input",
                                "Please enter a valid number for profit %.")
            return

        msg = QMessageBox(self)
        msg.setWindowTitle("Apply Profit %")
        msg.setText(f"Apply <b>{profit_pct}%</b> profit to which rows?")
        btn_all      = msg.addButton("Apply to All",      QMessageBox.AcceptRole)
        btn_selected = msg.addButton("Apply to Selected", QMessageBox.ActionRole)
        msg.addButton("Cancel",                           QMessageBox.RejectRole)
        msg.exec()

        clicked = msg.clickedButton()
        if clicked == btn_all:
            rows = list(range(self.table.rowCount()))
        elif clicked == btn_selected:
            rows = [
                r for r in range(self.table.rowCount())
                if self.table.item(r, self.COL_SELECT)
                and self.table.item(r, self.COL_SELECT).text() == ICON_SELECTED
            ]
            if not rows:
                QMessageBox.information(
                    self, "No Rows Selected",
                    "Click the ☐ icon in the Select column to mark rows, then try again."
                )
                return
        else:
            return  # Cancel

        # Apply in-memory then recalc (DB save happens inside _recalc_row)
        self.table.blockSignals(True)
        for r in rows:
            item = self.table.item(r, self.COL_PROFIT)
            if item:
                item.setText(f"{profit_pct:.2f}")
        self.table.blockSignals(False)
        for r in rows:
            self._recalc_row(r)

    # ------------------------------------------------------------------
    # itemChanged signal — skip Select column
    # ------------------------------------------------------------------
    def _on_item_changed(self, item):
        if item.column() == self.COL_SELECT:
            return
        self._recalc_row(item.row())

    # ------------------------------------------------------------------
    # Row recalculation + DB persist
    # ------------------------------------------------------------------
    def _recalc_row(self, r):
        self.table.blockSignals(True)
        try:
            def gv(c):
                it = self.table.item(r, c)
                if not it: return 0.0
                try: return float(it.text() or 0)
                except ValueError: return 0.0

            qty        = gv(self.COL_QTY)
            process    = gv(self.COL_PROCESS)
            steel      = gv(self.COL_STEEL)
            busbar     = gv(self.COL_BUSBAR)
            painting   = gv(self.COL_PAINTING)
            gasket     = gv(self.COL_GASKET)
            electrical = gv(self.COL_ELEC)
            hardware   = gv(self.COL_HARDWARE)
            labour     = gv(self.COL_LABOUR)
            packing    = gv(self.COL_PACKING)

            landed_per_panel = (
                process + steel + busbar + painting +
                gasket + electrical + hardware + labour + packing
            )
            if self.table.item(r, self.COL_LANDED):
                self.table.item(r, self.COL_LANDED).setText(f"{landed_per_panel:.2f}")

            total_landed = landed_per_panel * qty
            if self.table.item(r, self.COL_TOTAL_L):
                self.table.item(r, self.COL_TOTAL_L).setText(f"{total_landed:.2f}")

            other      = gv(self.COL_OTHER)
            overhead   = gv(self.COL_OVERHEAD)
            profit_pct = gv(self.COL_PROFIT)

            profit_amount = total_landed * profit_pct / 100
            final_offer   = total_landed + other + overhead + profit_amount

            if self.table.item(r, self.COL_FINAL):
                self.table.item(r, self.COL_FINAL).setText(f"{final_offer:.2f}")

            # ── Persist to tbl_Panels ─────────────────────────────────
            name_item = self.table.item(r, self.COL_NAME)
            panel_id  = name_item.data(Qt.UserRole) if name_item else None
            if panel_id is not None:
                for method, val, label in [
                    (self.service.update_panel_other_cost,    other,      "OtherCost"),
                    (self.service.update_panel_overhead_cost, overhead,   "OverHeadCost"),
                    (self.service.update_panel_profit,        profit_pct, "Profit"),
                ]:
                    try:
                        method(panel_id, val)
                    except Exception as e:
                        print(f"[CostSummary] Failed to save {label} "
                              f"for panel {panel_id}: {e}")
        finally:
            self.table.blockSignals(False)
