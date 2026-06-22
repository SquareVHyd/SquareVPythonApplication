from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt
from app.ui.searchable_table import SearchableTable, NumericTableWidgetItem
from app.services.quotation_service import QuotationService

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
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        
        # Header Section
        header = QHBoxLayout()
        self.title_label = QLabel("Cost Summary")
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #0f172a;")
        
        self.refresh_btn = QPushButton("🔄 Recalculate")
        self.refresh_btn.clicked.connect(self.refresh_view)
        
        header.addWidget(self.title_label)
        header.addStretch()
        header.addWidget(self.refresh_btn)
        self.layout.addLayout(header)

        # Unit Costs Display
        self.costs_frame = QFrame()
        self.costs_frame.setStyleSheet("QFrame { background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 6px; }")
        costs_layout = QHBoxLayout(self.costs_frame)
        costs_layout.setContentsMargins(15, 10, 15, 10)
        
        self.lbl_al_cost = QLabel("Unit Al Cost: ₹0.00")
        self.lbl_cu_cost = QLabel("Unit Copper Cost: ₹0.00")
        self.lbl_st_cost = QLabel("Unit Steel Cost: ₹0.00")
        
        style = "font-size: 14px; font-weight: bold; color: #1e293b; border: none; background: transparent;"
        self.lbl_al_cost.setStyleSheet(style)
        self.lbl_cu_cost.setStyleSheet(style)
        self.lbl_st_cost.setStyleSheet(style)
        
        def sep():
            s = QLabel(" | ")
            s.setStyleSheet("color: #94a3b8; border: none; background: transparent;")
            return s
            
        costs_layout.addStretch()
        costs_layout.addWidget(self.lbl_al_cost)
        costs_layout.addWidget(sep())
        costs_layout.addWidget(self.lbl_cu_cost)
        costs_layout.addWidget(sep())
        costs_layout.addWidget(self.lbl_st_cost)
        costs_layout.addStretch()
        
        self.layout.addWidget(self.costs_frame)

        # Table Section
        self.table = SearchableTable()
        self.table.setStyleSheet("QTableView { selection-background-color: #93c5fd; selection-color: #000000; }")
        self.table.setColumnCount(17)
        self.table.setHorizontalHeaderLabels([
            "Panel Name", "Pnl Qty", "Process Price", "Steel Cost", "Busbar Cost",
            "Painting cost", "Gasket cost", "Electrical cost", "Hardware cost", 
            "Labour cost", "Packing cost", "Landed cost/per panel", "Total landed cost",
            "Other cost", "Overhead cost", "Profit", "Final offer cost"
        ])
        
        # We will control editability per-item, not globally NoEditTriggers
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        
        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(QHeaderView.Interactive)
        self.table.itemChanged.connect(self._on_item_changed)
        
        self.layout.addWidget(self.table)

    def load_quotation(self, quote_id, project_name):
        self.quote_id = quote_id
        self.project_name = project_name
        self.title_label.setText(f"Cost Summary: {project_name}")
        self.refresh_view()

    def refresh_view(self):
        if not self.quote_id:
            return
            
        # 1. Update Unit Costs Header
        al_cost = self.service.get_metal_cost_from_quote(self.quote_id, "aluminium")
        cu_cost = self.service.get_metal_cost_from_quote(self.quote_id, "copper")
        st_cost = self.service.get_metal_cost_from_quote(self.quote_id, "steel")
        
        self.lbl_al_cost.setText(f"Unit Al Cost: {format_currency(al_cost)}")
        self.lbl_cu_cost.setText(f"Unit Copper Cost: {format_currency(cu_cost)}")
        self.lbl_st_cost.setText(f"Unit Steel Cost: {format_currency(st_cost)}")
        
        # 2. Populate Table
        panels = self.service.get_panels_by_quote(self.quote_id)
        self.table.setRowCount(len(panels))
        self.table.blockSignals(True)
        
        for r, p_row in enumerate(panels):
            pid = p_row[0]
            name = p_row[4]
            try:
                qty = int(p_row[5] or 1)
            except ValueError:
                qty = 1
                
            unit_process = self.service.calculate_panel_process_cost(pid)
            unit_steel = self.service.calculate_panel_steel_cost(pid, self.quote_id)
            unit_busbar = self.service.calculate_panel_busbar_cost(pid, self.quote_id)
            
            total_process = unit_process * qty
            total_steel = unit_steel * qty
            total_busbar = unit_busbar * qty
            
            total_line_cost = total_process + total_steel + total_busbar
            
            self.table.setItem(r, 0, self._create_item(name, False))
            self.table.setItem(r, 1, self._create_item(qty, False))
            self.table.setItem(r, 2, self._create_item(f"{unit_process:.2f}", False))
            self.table.setItem(r, 3, self._create_item(f"{unit_steel:.2f}", False))
            self.table.setItem(r, 4, self._create_item(f"{unit_busbar:.2f}", False))
            
            # Initial zeroes for editable costs
            
            l, h, d = self.service.get_panel_dimensions(pid)
            area_mm2 = (2 * (l * h + l * d + d * h)) * 1.05
            area_sqft = area_mm2 / 92903.04
            painting_cost = area_sqft * 17.0
            
            self.table.setItem(r, 5, self._create_item(f"{painting_cost:.2f}", True))
            
            for c in range(6, 11): # Gasket to Packing
                self.table.setItem(r, c, self._create_item("0.00", True))
                
            self.table.setItem(r, 11, self._create_item("0.00", False)) # Landed
            self.table.setItem(r, 12, self._create_item("0.00", False)) # Total Landed
            
            for c in range(13, 16): # Other, Overhead, Profit
                self.table.setItem(r, c, self._create_item("0.00", True))
                
            self.table.setItem(r, 16, self._create_item("0.00", False, True)) # Final Offer
            
            # trigger calculation
            self._recalc_row(r)
            
        self.table.blockSignals(False)
        self.table.resizeColumnsToContents()

    def _create_item(self, text, editable, bold_red=False):
        item = NumericTableWidgetItem(str(text))
        if editable:
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            item.setBackground(Qt.yellow) # visual cue
        else:
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            if bold_red:
                from PySide6.QtGui import QFont, QBrush, QColor
                font = QFont()
                font.setBold(True)
                item.setFont(font)
                item.setForeground(QBrush(QColor("#b91c1c")))
        return item

    def _on_item_changed(self, item):
        self._recalc_row(item.row())
        
    def _recalc_row(self, r):
        self.table.blockSignals(True)
        try:
            def get_val(c):
                it = self.table.item(r, c)
                if not it: return 0.0
                try: return float(it.text() or 0)
                except ValueError: return 0.0
            
            qty = get_val(1)
            process = get_val(2)
            steel = get_val(3)
            busbar = get_val(4)
            
            painting = get_val(5)
            gasket = get_val(6)
            electrical = get_val(7)
            hardware = get_val(8)
            labour = get_val(9)
            packing = get_val(10)
            
            # Landed cost/per panel
            landed_per_panel = process + steel + busbar + painting + gasket + electrical + hardware + labour + packing
            if self.table.item(r, 11):
                self.table.item(r, 11).setText(f"{landed_per_panel:.2f}")
            
            # Total landed cost
            total_landed = landed_per_panel * qty
            if self.table.item(r, 12):
                self.table.item(r, 12).setText(f"{total_landed:.2f}")
            
            other = get_val(13)
            overhead = get_val(14)
            profit = get_val(15)
            
            # Final offer cost
            final_offer = total_landed + other + overhead + profit
            if self.table.item(r, 16):
                self.table.item(r, 16).setText(f"{final_offer:.2f}")
            
        finally:
            self.table.blockSignals(False)
