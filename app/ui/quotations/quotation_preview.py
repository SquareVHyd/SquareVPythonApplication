from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame,
    QPushButton, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QSizePolicy, QDialog, QFormLayout, QComboBox, QLineEdit
)
from PySide6.QtCore import Qt
import pyodbc
from datetime import datetime
from app.ui.searchable_table import SearchableTable, NumericTableWidgetItem
from app.services.quotation_service import QuotationService
from app.ui.quotations.quotation_form import QuotationForm
from app.ui.quotations.panels.panel_form import PanelForm
from app.ui.quotations.modules.panel_module_form import PanelModuleForm
from app.ui.quotations.modules.panel_module_page import INGOG_LIST, POLE_LIST, KA_LIST, RELEASE_LIST, PROTECTION_LIST
from app.ui.quotations.module_items.module_item_form import ModuleItemForm
from app.ui.quotations.module_items.select_module_items_dialog import SelectModuleItemsDialog
from app.ui.quotations.ctc_constants import (
    GST_OPTIONS, FREIGHT_OPTIONS, PAYMENT_OPTIONS, WARRANTY_OPTIONS,
    VALIDITY_OPTIONS, PACKING_OPTIONS, INSPECTION_OPTIONS, DELIVERY_OPTIONS
)

def format_indian_currency(value):
    try:
        val = float(value)
    except (ValueError, TypeError):
        return str(value)
    
    is_negative = val < 0
    val = abs(val)
    
    val_str = f"{val:.2f}"
    
    if "." in val_str:
        integer_part, decimal_part = val_str.split(".")
    else:
        integer_part, decimal_part = val_str, "00"
        
    if len(integer_part) > 3:
        last_three = integer_part[-3:]
        other_digits = integer_part[:-3]
        
        groups = []
        while len(other_digits) > 0:
            groups.append(other_digits[-2:])
            other_digits = other_digits[:-2]
            
        groups.reverse()
        formatted_integer = ",".join(groups) + "," + last_three
    else:
        formatted_integer = integer_part
        
    result = formatted_integer + "." + decimal_part
    return "-" + result if is_negative else result

from PySide6.QtCore import QObject, QEvent
class ClickFilter(QObject):
    def __init__(self, callback, parent=None):
        super().__init__(parent)
        self.callback = callback
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.LeftButton:
            self.callback()
            return True
        return super().eventFilter(obj, event)

class QuotationPreviewPage(QWidget):
    """
    A hierarchical 'one-stop' view for managing a Quotation, its Panels, 
    Modules, and Items with full CRUD capabilities.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = QuotationService()
        self.quote_id = None
        self.project_name = ""
        self.panel_expanded_states = {}
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
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
        
        # Header Section
        header = QHBoxLayout()
        self.title_label = QLabel("Quotation Preview & Management")
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #0f172a;")
        
        self.refresh_btn = QPushButton("🔄 Refresh View")
        self.refresh_btn.clicked.connect(self.refresh_view)
        
        header.addWidget(self.title_label)
        header.addStretch()
        header.addWidget(self.refresh_btn)
        self.layout.addLayout(header)

        # Main Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.container = QWidget()
        self.content_layout = QVBoxLayout(self.container)
        self.content_layout.setSpacing(20)
        self.scroll.setWidget(self.container)
        self.layout.addWidget(self.scroll)

    def load_quotation(self, quote_id, project_name):
        self.quote_id = quote_id
        self.project_name = project_name
        self.refresh_view()

    def _clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self._clear_layout(child.layout())

    def refresh_view(self):
        if not self.quote_id:
            return

        # Clear existing layout
        self._clear_layout(self.content_layout)

        # 1. Quotation Details Section
        quote_data = self.service.get_quotation_by_id(self.quote_id)
        if quote_data:
            self.title_label.setText(f"Preview: {quote_data.get('QuoteRereceNo', 'N/A')} - {quote_data.get('QuoteProjectName', '')}")
            self._add_quotation_header(quote_data)

            from PySide6.QtWidgets import QPushButton
            btn_collapse_all = QPushButton("Collapse All Forms")
            btn_collapse_all.setCheckable(True)
            btn_collapse_all.setStyleSheet("background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 4px; padding: 4px; font-weight: bold; margin-bottom: 5px;")
            self.content_layout.addWidget(btn_collapse_all)
            
            customer_id = quote_data.get('CustomerId')
            t1, c1 = self._add_customer_details(customer_id) if customer_id else (None, None)
            t2, c2 = self._add_quotation_ctc_form()
            t3, c3 = self._add_common_specs_form()
            t4, c4 = self._add_revision_table()

            def toggle_all(checked):
                btn_collapse_all.setText("▶ Expand All Forms" if checked else "▼ Collapse All Forms")
                for t, c in [(t1, c1), (t2, c2), (t3, c3), (t4, c4)]:
                    if t and c:
                        t.setChecked(not checked)
                        self._toggle_container(not checked, c, t)

            btn_collapse_all.clicked.connect(toggle_all)
            
            # Collapse by default
            btn_collapse_all.setChecked(True)
            toggle_all(True)

        # 2. Panels Section
        panels = self.service.get_panels_by_quote(self.quote_id)
        
        # Calculate Grand Total for the entire quotation
        grand_total = 0.0
        for p_row in panels:
            pid, _, _, _, _, qty, _, _, _, _, _, _, _, _, _, _, _ = p_row
            p_qty = float(qty or 0)
            p_modules = self.service.get_panel_modules_by_panel_id(pid)
            p_panel_total = 0.0
            for m_row in p_modules:
                m_qty = m_row[5]
                pm_id = m_row[0]
                m_items = self.service.get_module_items_by_panel_module_id(pm_id)
                total_items_amount = sum(float(item[6] or 0) for item in m_items)
                p_panel_total += float(m_qty or 0) * total_items_amount
            grand_total += p_panel_total * p_qty

        panel_section_header = QHBoxLayout()
        panel_title = QLabel(f"Panels ({len(panels)})")
        panel_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #0f172a; margin-top: 10px;")
        grand_total_lbl = QLabel(f"<b>Total Quotation Price =</b> ₹{format_indian_currency(grand_total)}")
        grand_total_lbl.setStyleSheet("font-size: 18px; color: #b91c1c; font-weight: bold; margin-top: 10px; margin-left: 20px;")
        
        btn_collapse_panels = QPushButton("▼ Collapse All Panels")
        btn_collapse_panels.setCheckable(True)
        btn_collapse_panels.setStyleSheet("background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 4px; padding: 4px; font-weight: bold; margin-top: 10px;")
        
        add_panel_btn = QPushButton("➕ Add Panel")
        add_panel_btn.clicked.connect(self._add_panel)
        add_panel_btn.setStyleSheet("margin-top: 10px;")
        
        panel_section_header.addWidget(panel_title)
        panel_section_header.addWidget(grand_total_lbl)
        panel_section_header.addStretch()
        panel_section_header.addWidget(btn_collapse_panels)
        panel_section_header.addWidget(add_panel_btn)
        self.content_layout.addLayout(panel_section_header)

        self.panel_toggles = []
        for p_row in panels:
            t, c = self._add_panel_widget(p_row)
            if t and c:
                self.panel_toggles.append((t, c, p_row[0]))

        def toggle_all_panels(checked):
            btn_collapse_panels.setText("▶ Expand All Panels" if checked else "▼ Collapse All Panels")
            for t, c, pid in self.panel_toggles:
                t.setChecked(not checked)
                self._on_panel_toggled(not checked, pid, c, t)

        btn_collapse_panels.clicked.connect(toggle_all_panels)
        
        # If it's the very first load, we might want to collapse all. But we respect stored states.
        # Check if any panel has a state stored, if not, default to collapse all.
        if not self.panel_expanded_states:
            btn_collapse_panels.setChecked(True)
            toggle_all_panels(True)

        self.content_layout.addStretch()

    def _add_quotation_header(self, data):
        group = QGroupBox("Quotation Info")
        group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #cbd5e1; border-radius: 8px; margin-top: 10px; padding: 10px; }")
        layout = QVBoxLayout(group)
        
        info_text = (
            f"<b>Subject:</b> {data.get('QuoteSubject')} | "
            f"<b>Customer:</b> {data.get('CustomerName')} | "
            f"<b>Ref:</b> {data.get('QuoteRereceNo')} | "
            f"<b>Date:</b> {data.get('Date_Quote')}"
        )
        lbl = QLabel(info_text)
        
        btn_layout = QHBoxLayout()
        edit_btn = QPushButton("✏️ Edit Quotation")
        # edit_btn.setFixedWidth(120)
        edit_btn.clicked.connect(lambda: self._edit_quotation(data))
        btn_layout.addWidget(lbl)
        btn_layout.addStretch()
        btn_layout.addWidget(edit_btn)
        
        layout.addLayout(btn_layout)
        self.content_layout.addWidget(group)

    def _add_panel_widget(self, p_row):
        pid, qid, cat, ser, name, qty, l, h, d, w, ka, er, st, bm, profit, other_cost, overhead_cost = p_row
        
        # Calculate Panel Total (Sum of all contained module totals)
        panel_qty = float(qty or 0)
        modules = self.service.get_panel_modules_by_panel_id(pid)
        panel_total = 0.0
        for m_row in modules:
            m_qty = m_row[5]
            pm_id = m_row[0]
            m_items = self.service.get_module_items_by_panel_module_id(pm_id)
            total_items_amount = sum(float(item[6] or 0) for item in m_items)
            panel_total += float(m_qty or 0) * total_items_amount
        total_panel_cost = panel_total * panel_qty

        panel_frame = QFrame()
        panel_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        panel_frame.setStyleSheet("QFrame { background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; }")
        layout = QVBoxLayout(panel_frame)

        # Panel Header
        header = QHBoxLayout()

        # Toggle Button
        toggle_btn = QPushButton()
        # toggle_btn.setFixedSize(24, 24)
        toggle_btn.setCheckable(True)
        
        # Restore toggle state, default to collapsed (False)
        is_expanded = self.panel_expanded_states.get(pid, False)
        toggle_btn.setChecked(is_expanded)
        toggle_btn.setText("▼" if is_expanded else "▶")
        toggle_btn.setStyleSheet("font-weight: bold; border: none; background: transparent; color: #1e293b;")

        p_info = QLabel(f"<b>Panel:</b> {name} ({cat}) | <b>Qty:</b> {qty} | <b>Dim:</b> {l}x{h}x{d}")
        p_info.setStyleSheet("border: none; font-size: 14px; color: #1e293b;")
        p_info.setCursor(Qt.PointingHandCursor)
        p_info._filter = ClickFilter(toggle_btn.click, p_info)
        p_info.installEventFilter(p_info._filter)
        
        # Panel Cost Label
        total_panel_lbl = QLabel(f"<b>Qty =</b> {panel_qty} | <b>Unit Panel Cost =</b> ₹{format_indian_currency(panel_total)} | <b>Total Panel Cost =</b> ₹{format_indian_currency(total_panel_cost)}")
        total_panel_lbl.setStyleSheet("border: none; font-size: 14px; color: #2563eb; font-weight: bold; margin-left: 15px;")
        total_panel_lbl.setCursor(Qt.PointingHandCursor)
        total_panel_lbl._filter = ClickFilter(toggle_btn.click, total_panel_lbl)
        total_panel_lbl.installEventFilter(total_panel_lbl._filter)

        edit_btn = QPushButton("✏️")
        edit_btn.setToolTip("Edit Panel")
        edit_btn.clicked.connect(lambda: self._edit_panel(p_row))
        
        del_btn = QPushButton("🗑️")
        del_btn.setToolTip("Delete Panel")
        del_btn.clicked.connect(lambda: self._delete_panel(pid))
        
        add_mod_btn = QPushButton("📦 Add Module")
        # add_mod_btn.setFixedWidth(100)
        add_mod_btn.clicked.connect(lambda: self._add_module(pid))

        header.addWidget(toggle_btn)
        header.addWidget(p_info)
        header.addWidget(total_panel_lbl)
        header.addStretch()
        header.addWidget(edit_btn)
        header.addWidget(del_btn)
        header.addWidget(add_mod_btn)
        layout.addLayout(header)

        # Container for modules (collapsible)
        modules_container = QWidget()
        modules_layout = QVBoxLayout(modules_container)
        modules_container.setContentsMargins(0, 0, 0, 0)
        
        # Set initial visibility
        modules_container.setVisible(is_expanded)
        
        toggle_btn.clicked.connect(lambda checked, p=pid, c=modules_container, btn=toggle_btn: self._on_panel_toggled(checked, p, c, btn))
        layout.addWidget(modules_container)

        # Modules Section
        for m_row in modules:
            self._add_module_widget(modules_layout, m_row)

        self.content_layout.addWidget(panel_frame)
        return toggle_btn, modules_container

    def _add_module_widget(self, parent_layout, m_row):
        # Unpack based on QuotationService.get_panel_modules_by_panel_id order
        # ID, PanelID, PanelName, PanelQty, IngOg, PanelModQty, ModuleTypeID, Pnl_Module_Type, Pole, Ka, Release, Protection, Remark
        pm_id, pid, p_name, p_qty, ing_og, m_qty, mt_id, mt_name, pole, ka, rel, prot, rem = m_row
        
        # Fetch items first to calculate total module cost
        items = self.service.get_module_items_by_panel_module_id(pm_id)
        total_items_amount = sum(float(item[6] or 0) for item in items)
        module_total = float(m_qty or 0) * total_items_amount

        mod_group = QGroupBox()
        mod_group.setStyleSheet("QGroupBox { border: 1px solid #94a3b8; margin-top: 15px; padding-top: 10px; font-weight: normal; }")
        layout = QVBoxLayout(mod_group)

        # Module Header with Edit/Delete
        mod_header = QHBoxLayout()

        # Toggle Button
        toggle_btn = QPushButton("▼")
        # toggle_btn.setFixedSize(24, 24)
        toggle_btn.setCheckable(True)
        toggle_btn.setChecked(True)
        toggle_btn.setStyleSheet("font-weight: bold; border: none; background: transparent; color: #334155; padding: 4px;")

        mod_lbl = QLabel(f"<b>Module:</b> {mt_name} | <b>Ing/Og:</b> {ing_og} | <b>P/kA:</b> {pole}/{ka}")
        mod_lbl.setStyleSheet("border: none; font-size: 13px; color: #334155;")
        mod_lbl.setCursor(Qt.PointingHandCursor)
        mod_lbl._filter = ClickFilter(toggle_btn.click, mod_lbl)
        mod_lbl.installEventFilter(mod_lbl._filter)
        
        # Total Module Cost Label
        total_mod_lbl = QLabel(f"<b>Qty =</b> {m_qty} | <b>Unit Module Cost =</b> ₹{format_indian_currency(total_items_amount)} | <b>Module Total =</b> ₹{format_indian_currency(module_total)}")
        total_mod_lbl.setStyleSheet("border: none; font-size: 13px; color: #059669; font-weight: bold; margin-left: 15px;")
        total_mod_lbl.setCursor(Qt.PointingHandCursor)
        total_mod_lbl._filter = ClickFilter(toggle_btn.click, total_mod_lbl)
        total_mod_lbl.installEventFilter(total_mod_lbl._filter)

        m_edit_btn = QPushButton("✏️")
        # m_edit_btn.setFixedSize(24, 24)
        m_edit_btn.clicked.connect(lambda: self._edit_module(m_row))
        
        m_del_btn = QPushButton("🗑️")
        # m_del_btn.setFixedSize(24, 24)
        m_del_btn.clicked.connect(lambda: self._delete_module(pm_id))
        m_add_item_btn = QPushButton("➕ Item")
        # m_add_item_btn.setFixedSize(60, 24)
        m_add_item_btn.clicked.connect(lambda: self._add_item(pm_id, m_qty)) # Pass m_qty here

        m_add_from_mod_btn = QPushButton("📂 From Library") # New button
        # m_add_from_mod_btn.setFixedSize(100, 24)
        m_add_from_mod_btn.clicked.connect(lambda: self._add_from_module(pm_id)) # Pass pm_id here

        mod_header.addWidget(toggle_btn)
        mod_header.addWidget(mod_lbl)
        mod_header.addWidget(total_mod_lbl)
        mod_header.addStretch()
        mod_header.addWidget(m_add_item_btn)
        mod_header.addWidget(m_add_from_mod_btn) # Add new button
        mod_header.addWidget(m_edit_btn)
        mod_header.addWidget(m_del_btn)
        layout.addLayout(mod_header)

        # Content container (collapsible)
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_container.setContentsMargins(0, 0, 0, 0)
        
        toggle_btn.clicked.connect(lambda checked: self._toggle_container(checked, content_container, toggle_btn))
        layout.addWidget(content_container)

        # Items Table
        if items:
            table = QTableWidget(len(items), 7)
            table.setHorizontalHeaderLabels(["Description", "Make", "BOM", "LP", "Disc", "Amount", "Actions"])
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch) # Description stretches
            table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents) # Make
            table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents) # BOM
            table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents) # LP
            table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents) # Disc
            table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents) # Amount
            table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents) # Actions

            # UI Update: Disable internal scrolling and set fixed height to show all items
            table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            table.setEditTriggers(QTableWidget.NoEditTriggers)
            
            for r, item in enumerate(items):
                # SQL indices: 0:ID, 1:Desc, 2:BOM, 3:LP, 4:Disc, 5:Make, 6:Amount
                table.setItem(r, 0, QTableWidgetItem(str(item[1])))
                table.setItem(r, 1, QTableWidgetItem(str(item[5] or "")))
                table.setItem(r, 2, QTableWidgetItem(str(item[2])))
                table.setItem(r, 3, QTableWidgetItem(f"{format_indian_currency(item[3])}"))
                table.setItem(r, 4, QTableWidgetItem(f"{item[4]*100:.1f}%"))
                table.setItem(r, 5, QTableWidgetItem(f"{format_indian_currency(item[6])}"))

                # Row Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(2, 2, 2, 2)
                actions_layout.setSpacing(4)
                
                mini_btn_style = "QPushButton { padding: 4px; font-size: 12px; background: transparent; border: none; } QPushButton:hover { background: #e2e8f0; border-radius: 2px; }"
                i_edit = QPushButton("✏️"); # i_edit.setFixedSize(20, 20)
                i_edit.setStyleSheet(mini_btn_style)
                i_edit.clicked.connect(lambda _, it=item, pmid=pm_id: self._edit_item(pmid, it))
                
                i_del = QPushButton("🗑️"); # i_del.setFixedSize(20, 20)
                i_del.setStyleSheet("QPushButton { padding: 4px; font-size: 12px; background: #fee2e2; border: 1px solid #fecaca; border-radius: 2px; } QPushButton:hover { background: #fecaca; }")
                i_del.clicked.connect(lambda _, it=item, pmid=pm_id: self._delete_item(pmid, it))
                
                actions_layout.addWidget(i_edit)
                actions_layout.addWidget(i_del)
                table.setCellWidget(r, 6, actions_widget)
            
            # Dynamically adjust table height to show all rows without internal scrolling
            table.resizeRowsToContents()
            total_height = table.horizontalHeader().height() + table.verticalHeader().length() + 52
            table.setFixedHeight(total_height)
            
            content_layout.addWidget(table)
        else:
            content_layout.addWidget(QLabel("No items configured for this module."))

        parent_layout.addWidget(mod_group)

    def _toggle_container(self, checked, container, button):
        """Toggles visibility of a container and updates the button arrow."""
        container.setVisible(checked)
        button.setText("▼" if checked else "▶")

    def _on_panel_toggled(self, checked, pid, container, button):
        self.panel_expanded_states[pid] = checked
        self._toggle_container(checked, container, button)

    # --- CRUD Actions Leveraging Existing Logic ---

    def _edit_quotation(self, data):
        # Map database keys (from get_quotation_by_id) to QuotationForm expected keys
        current_data = {
            "id": data["ID"],
            "customer_id": data["CustomerId"],
            "req_date": str(data["DateOfRequest"]),
            "quote_date": str(data["Date_Quote"]),
            "ref_no": data["QuoteRereceNo"],
            "subject": data["QuoteSubject"],
            "project": data["QuoteProjectName"],
            "contact": data.get("CustomerContactName", ""),
            "prepared_by": data.get("PreparedBy", ""),
            "status": data.get("QuoteStatus", "Draft"),
        }
        dialog = QuotationForm(self, quotation_data=current_data)
        if dialog.exec():
            self.service.update_quotation(self.quote_id, **dialog.get_data())
            self.refresh_view()

    def _add_panel(self):
        dialog = PanelForm(self.quote_id, parent=self)
        if dialog.exec():
            self.service.create_panel(**dialog.get_data())
            self.refresh_view()

    def _edit_panel(self, p_row):
        cols = ["id", "quote_id", "category", "serial", "name", "qty", "length", "height", "depth", "waste", "ka_rating", "earth_runs", "stand", "busbar"]
        current_data = {cols[i]: str(p_row[i]) for i in range(len(cols))}
        dialog = PanelForm(self.quote_id, panel_data=current_data, parent=self)
        if dialog.exec():
            self.service.update_panel(p_row[0], **dialog.get_data())
            self.refresh_view()

    def _delete_panel(self, panel_id):
        if QMessageBox.question(self, "Confirm", "Delete this panel and all its modules?") == QMessageBox.Yes:
            self.service.delete_panel(panel_id)
            self.refresh_view()

    def _get_dropdown_data(self):
        return {"ingog": INGOG_LIST, "pole": POLE_LIST, "ka": KA_LIST, "release": RELEASE_LIST, "protection": PROTECTION_LIST}

    def _add_module(self, panel_id):
        dialog = PanelModuleForm(self.quote_id, panel_id=panel_id, parent=self, dropdown_lists=self._get_dropdown_data())
        if dialog.exec():
            data = dialog.get_data()
            self.service.create_panel_module(**data)
            self.refresh_view()

    def _edit_module(self, m_row):
        # Map tuple to PanelModuleForm expected keys
        # Order: ID, PanelID, PanelName, PanelQty, IngOg, PanelModQty, ModuleTypeID, Pnl_Module_Type, Pole, Ka, Release, Protection, Remark
        pm_id = m_row[0]
        panel_id = m_row[1]
        current_data = {
            "id": pm_id,
            "panel_id": panel_id,
            "ing_og": m_row[4],
            "qty": m_row[5],
            "type_id": m_row[6],
            "pole": m_row[8],
            "ka": m_row[9],
            "release": m_row[10],
            "protection": m_row[11],
            "remark": m_row[12]
        }
        dialog = PanelModuleForm(self.quote_id, panel_id=panel_id, pm_data=current_data, parent=self, dropdown_lists=self._get_dropdown_data())
        if dialog.exec():
            self.service.update_panel_module(pm_id, **dialog.get_data())
            self.refresh_view()

    def _delete_module(self, pm_id):
        if QMessageBox.question(self, "Confirm", "Delete this module entry?") == QMessageBox.Yes:
            self.service.delete_panel_module(pm_id)
            self.refresh_view()

    def _add_item(self, pm_id, panel_mod_qty):
        # The ModuleItemForm expects module_type_id as the first argument (now treating it as pm_id)
        dialog = ModuleItemForm(pm_id, module_item_data={"bom": panel_mod_qty}, parent=self)
        if dialog.exec():
            d = dialog.get_data()
            self.service.create_module_item(
                d["module_type_id"], # This contains the pm_id now
                d["drive_description"],
                d["bom"],
                d["lp"],
                d["discount"]
            )
            self.refresh_view()

    def _edit_item(self, pm_id, item_row):
        # item_row: (ID, DriveDescription, BOM, LP, Disc)
        old_desc = item_row[1]
        current_data = {
            "module_type_id": pm_id, # This is the ID for tbl_PanelModules
            "drive_description": item_row[1],
            "bom": float(item_row[2] or 0),
            "lp": float(item_row[3] or 0),
            "discount": float(item_row[4] or 0)
        }
        # ModuleItemForm expects module_type_id as the first argument (now acting as pm_id)
        dialog = ModuleItemForm(pm_id, module_item_data=current_data, parent=self)
        if dialog.exec():
            d = dialog.get_data()
            self.service.update_module_item(
                pm_id, old_desc,  # Old PK components
                d["module_type_id"], d["drive_description"], d["bom"], d["lp"], d["discount"] # New Data components
            )
            self.refresh_view()

    def _delete_item(self, pm_id, item_row):
        desc = item_row[1]
        if QMessageBox.question(self, "Confirm", f"Remove item '{desc}' from this module type?") == QMessageBox.Yes:
            self.service.delete_module_item(pm_id, desc)
            self.refresh_view()

    def _add_from_module(self, pm_id):
        dialog = SelectModuleItemsDialog(target_pm_id=pm_id, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_view()

    def _add_customer_details(self, customer_id):
        group = QGroupBox()
        group.setStyleSheet("QGroupBox { border: 1px solid #cbd5e1; border-radius: 8px; margin-top: 10px; padding: 10px; }")
        layout = QVBoxLayout(group)
        
        header = QHBoxLayout()
        toggle_btn = QPushButton("▼")
        toggle_btn.setFixedSize(24, 24)
        toggle_btn.setCheckable(True)
        toggle_btn.setChecked(True)
        toggle_btn.setStyleSheet("font-weight: bold; border: none; background: transparent; color: #1e293b;")
        
        title_lbl = QLabel("<b>Customer Details</b>")
        title_lbl.setStyleSheet("border: none; font-size: 14px;")
        
        header.addWidget(toggle_btn)
        header.addWidget(title_lbl)
        header.addStretch()
        layout.addLayout(header)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container.setContentsMargins(0, 0, 0, 0)
        toggle_btn.clicked.connect(lambda checked: self._toggle_container(checked, container, toggle_btn))
        layout.addWidget(container)
        
        table = QTableWidget()
        try:
            from app.config.database import get_session
            from sqlalchemy import text
            with get_session() as session:
                result = session.execute(text('SELECT * FROM public."tblCustomers" WHERE "ID" = :id'), {"id": customer_id})
                columns = list(result.keys())
                rows = result.fetchall()

            table.setColumnCount(2)
            table.setHorizontalHeaderLabels(["Field", "Value"])
            table.setRowCount(len(columns))

            if len(rows) > 0:
                row_data = rows[0]
                for r, col_name in enumerate(columns):
                    item_key = QTableWidgetItem(str(col_name))
                    item_key.setFlags(item_key.flags() & ~Qt.ItemIsEditable)
                    
                    val = row_data[r]
                    text_val = str(val) if val is not None else ""
                    item_val = QTableWidgetItem(text_val)
                    item_val.setFlags(item_val.flags() & ~Qt.ItemIsEditable)
                    
                    table.setItem(r, 0, item_key)
                    table.setItem(r, 1, item_val)

            table.verticalHeader().hide()
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            table.setSelectionBehavior(QTableWidget.SelectRows)
            table.setAlternatingRowColors(True)
            table.setStyleSheet(
                "QTableWidget { gridline-color: #e1e1e1; border: 1px solid #d9d9d9; }"
                "QHeaderView::section { background-color: #f7f7f7; padding: 6px; border: 1px solid #d9d9d9; font-weight: bold; }"
                "QTableView { selection-background-color: #93c5fd; selection-color: #000000; }"
            )

            total_height = table.horizontalHeader().height() + 2
            if len(columns) > 0:
                total_height += table.rowHeight(0) * len(columns)
            table.setFixedHeight(min(total_height, 250))
            
            container_layout.addWidget(table)
            self.content_layout.addWidget(group)
            return toggle_btn, container
        except Exception as e:
            container_layout.addWidget(QLabel(f"Failed to load customer details: {e}"))
            self.content_layout.addWidget(group)
            return None, None

    def _add_quotation_ctc_form(self):
        group = QGroupBox()
        group.setStyleSheet("QGroupBox { border: 1px solid #cbd5e1; border-radius: 8px; margin-top: 10px; padding: 10px; }")
        layout = QVBoxLayout(group)
        
        header = QHBoxLayout()
        toggle_btn = QPushButton("▼")
        toggle_btn.setFixedSize(24, 24)
        toggle_btn.setCheckable(True)
        toggle_btn.setChecked(True)
        toggle_btn.setStyleSheet("font-weight: bold; border: none; background: transparent; color: #1e293b;")
        
        title_lbl = QLabel("<b>Quotation CTC</b>")
        title_lbl.setStyleSheet("border: none; font-size: 14px;")
        
        header.addWidget(toggle_btn)
        header.addWidget(title_lbl)
        header.addStretch()
        layout.addLayout(header)

        container = QWidget()
        container_layout = QFormLayout(container)
        container.setContentsMargins(0, 0, 0, 0)
        toggle_btn.clicked.connect(lambda checked: self._toggle_container(checked, container, toggle_btn))
        layout.addWidget(container)
        
        try:
            self.service.save_quote_ctc(QuoteID=self.quote_id)
            rows = self.service.get_quote_ctc_list(self.quote_id)
            if rows:
                data = rows[0]
                self.ctc_id = data[0]
                
                def create_combo(options, current_val):
                    combo = QComboBox()
                    combo.setEditable(True)
                    combo.addItems(options)
                    if current_val:
                        combo.setCurrentText(str(current_val))
                    else:
                        combo.setCurrentIndex(0)
                    return combo

                self.ctc_gst_input = create_combo(GST_OPTIONS, data[2])
                self.ctc_freight_input = create_combo(FREIGHT_OPTIONS, data[3])
                self.ctc_payment_input = create_combo(PAYMENT_OPTIONS, data[4])
                self.ctc_warranty_input = create_combo(WARRANTY_OPTIONS, data[5])
                self.ctc_validity_input = create_combo(VALIDITY_OPTIONS, data[6])
                self.ctc_packing_input = create_combo(PACKING_OPTIONS, data[7])
                self.ctc_inspection_input = create_combo(INSPECTION_OPTIONS, data[8])
                self.ctc_delivery_input = create_combo(DELIVERY_OPTIONS, data[9])
                
                self.ctc_bank_input = QLineEdit(str(data[10]) if data[10] is not None else "")
                self.ctc_notes_input = QLineEdit(str(data[11]) if data[11] is not None else "")
                
                container_layout.addRow("GST / Taxes:", self.ctc_gst_input)
                container_layout.addRow("Freight & Insurance:", self.ctc_freight_input)
                container_layout.addRow("Payment:", self.ctc_payment_input)
                container_layout.addRow("Warranty:", self.ctc_warranty_input)
                container_layout.addRow("Validity:", self.ctc_validity_input)
                container_layout.addRow("Packing:", self.ctc_packing_input)
                container_layout.addRow("Inspection:", self.ctc_inspection_input)
                container_layout.addRow("Delivery:", self.ctc_delivery_input)
                container_layout.addRow("Bank Details:", self.ctc_bank_input)
                container_layout.addRow("Notes:", self.ctc_notes_input)
                
                save_btn = QPushButton("💾 Save CTC")
                save_btn.clicked.connect(self._save_ctc_form)
                container_layout.addRow("", save_btn)
                
            self.content_layout.addWidget(group)
            return toggle_btn, container
        except Exception as e:
            container_layout.addRow(QLabel(f"Failed to load CTC: {e}"))
            self.content_layout.addWidget(group)
            return None, None

    def _save_ctc_form(self):
        try:
            self.service.update_quote_ctc_field(self.ctc_id, "GSTTax", self.ctc_gst_input.currentText())
            self.service.update_quote_ctc_field(self.ctc_id, "FreightAndInsurance", self.ctc_freight_input.currentText())
            self.service.update_quote_ctc_field(self.ctc_id, "Payment", self.ctc_payment_input.currentText())
            self.service.update_quote_ctc_field(self.ctc_id, "Warranty", self.ctc_warranty_input.currentText())
            self.service.update_quote_ctc_field(self.ctc_id, "Validity", self.ctc_validity_input.currentText())
            self.service.update_quote_ctc_field(self.ctc_id, "Packing", self.ctc_packing_input.currentText())
            self.service.update_quote_ctc_field(self.ctc_id, "Inspection", self.ctc_inspection_input.currentText())
            self.service.update_quote_ctc_field(self.ctc_id, "Delivery", self.ctc_delivery_input.currentText())
            self.service.update_quote_ctc_field(self.ctc_id, "BankDetails", self.ctc_bank_input.text())
            self.service.update_quote_ctc_field(self.ctc_id, "Notes", self.ctc_notes_input.text())
            QMessageBox.information(self, "Success", "CTC saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save CTC: {e}")

    def _add_common_specs_form(self):
        group = QGroupBox()
        group.setStyleSheet("QGroupBox { border: 1px solid #cbd5e1; border-radius: 8px; margin-top: 10px; padding: 10px; }")
        layout = QVBoxLayout(group)
        
        header = QHBoxLayout()
        toggle_btn = QPushButton("▼")
        toggle_btn.setFixedSize(24, 24)
        toggle_btn.setCheckable(True)
        toggle_btn.setChecked(True)
        toggle_btn.setStyleSheet("font-weight: bold; border: none; background: transparent; color: #1e293b;")
        
        title_lbl = QLabel("<b>Common Specifications</b>")
        title_lbl.setStyleSheet("border: none; font-size: 14px;")
        
        header.addWidget(toggle_btn)
        header.addWidget(title_lbl)
        header.addStretch()
        layout.addLayout(header)

        container = QWidget()
        container_layout = QFormLayout(container)
        container.setContentsMargins(0, 0, 0, 0)
        toggle_btn.clicked.connect(lambda checked: self._toggle_container(checked, container, toggle_btn))
        layout.addWidget(container)
        
        try:
            self.service.save_common_specs(self.quote_id) # Ensure record exists
            rows = self.service.get_common_specs_list(self.quote_id)
            if rows:
                data = rows[0]
                self.spec_id = data[0]
                
                steel_values = [
                    "2.0 mm(+/- 10%) Thick CRCA Sheet steel",
                    "1.6 mm(+/- 10%) Thick CRCA Sheet steel",
                    "3.0 mm(+/- 10%) Thick CRCA Sheet steel"
                ]

                self.frames_input = QComboBox(); self.frames_input.setEditable(True); self.frames_input.addItems(steel_values)
                self.partitions_input = QComboBox(); self.partitions_input.setEditable(True); self.partitions_input.addItems(steel_values)
                self.doors_input = QComboBox(); self.doors_input.setEditable(True); self.doors_input.addItems(steel_values)
                self.gland_plates_input = QComboBox(); self.gland_plates_input.setEditable(True); self.gland_plates_input.addItems(steel_values)
                self.system_input = QLineEdit()
                self.control_supply_input = QComboBox(); self.control_supply_input.setEditable(True)
                self.control_supply_input.addItems(["230 Vac/50Hz Phase & Neutral", "110 Vac/50Hz Phase & Neutral"])
                self.busbar_sleeves_input = QLineEdit()
                self.busbar_supports_input = QLineEdit()
                self.busbar_metal_input = QComboBox(); self.busbar_metal_input.setEditable(True)
                self.busbar_metal_input.addItems(["Aluminium", "Copper"])
                self.cd_al_input = QLineEdit()
                self.cd_cu_input = QLineEdit()
                self.painting_color_input = QLineEdit()
                
                self.frames_input.setCurrentText(str(data[2]) if data[2] is not None else "")
                self.partitions_input.setCurrentText(str(data[3]) if data[3] is not None else "")
                self.doors_input.setCurrentText(str(data[4]) if data[4] is not None else "")
                self.gland_plates_input.setCurrentText(str(data[5]) if data[5] is not None else "")
                self.system_input.setText(str(data[6]) if data[6] is not None else "")
                self.control_supply_input.setCurrentText(str(data[7]) if data[7] is not None else "")
                self.busbar_sleeves_input.setText(str(data[8]) if data[8] is not None else "")
                self.busbar_supports_input.setText(str(data[9]) if data[9] is not None else "")
                self.busbar_metal_input.setCurrentText(str(data[10]) if data[10] is not None else "")
                self.cd_al_input.setText(str(data[11]) if data[11] is not None else "")
                self.cd_cu_input.setText(str(data[12]) if data[12] is not None else "")
                self.painting_color_input.setText(str(data[13]) if data[13] is not None else "")

                container_layout.addRow("Frames:", self.frames_input)
                container_layout.addRow("Partitions:", self.partitions_input)
                container_layout.addRow("Doors:", self.doors_input)
                container_layout.addRow("Gland Plates:", self.gland_plates_input)
                container_layout.addRow("System:", self.system_input)
                container_layout.addRow("Control Supply:", self.control_supply_input)
                container_layout.addRow("Busbar Sleeves:", self.busbar_sleeves_input)
                container_layout.addRow("Busbar Supports:", self.busbar_supports_input)
                container_layout.addRow("Busbar Metal:", self.busbar_metal_input)
                container_layout.addRow("Current Density (AL):", self.cd_al_input)
                container_layout.addRow("Current Density (CU):", self.cd_cu_input)
                container_layout.addRow("Painting Color:", self.painting_color_input)

                save_btn = QPushButton("💾 Save Common Specs")
                save_btn.clicked.connect(self._save_common_specs_form)
                container_layout.addRow("", save_btn)
                
            self.content_layout.addWidget(group)
            return toggle_btn, container
        except Exception as e:
            container_layout.addRow(QLabel(f"Failed to load Common Specs: {e}"))
            self.content_layout.addWidget(group)
            return None, None

    def _save_common_specs_form(self):
        try:
            mapping = {
                "Frames": self.frames_input.currentText(),
                "Partitions": self.partitions_input.currentText(),
                "Doors": self.doors_input.currentText(),
                "GlandPlates": self.gland_plates_input.currentText(),
                "System": self.system_input.text(),
                "ControlSupply": self.control_supply_input.currentText(),
                "BusbarSleeves": self.busbar_sleeves_input.text(),
                "BusbarSupports": self.busbar_supports_input.text(),
                "BusbarMetal": self.busbar_metal_input.currentText(),
                "CurrentDensity_AL": self.cd_al_input.text(),
                "CurrentDensity_CU": self.cd_cu_input.text(),
                "PaintingColor": self.painting_color_input.text()
            }
            for col_name, value in mapping.items():
                self.service.update_common_specs_field(self.spec_id, col_name, value)
            QMessageBox.information(self, "Success", "Common specifications saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save Common Specs: {e}")

    def _add_revision_table(self):
        """Adds a collapsible Revision History section to the Quotation Process page."""
        group = QGroupBox()
        group.setStyleSheet(
            "QGroupBox { border: 1px solid #cbd5e1; border-radius: 8px; margin-top: 10px; padding: 10px; }"
        )
        layout = QVBoxLayout(group)

        # ── header row ──────────────────────────────────────────────────────────
        header = QHBoxLayout()

        toggle_btn = QPushButton("▼")
        toggle_btn.setFixedSize(24, 24)
        toggle_btn.setCheckable(True)
        toggle_btn.setChecked(True)
        toggle_btn.setStyleSheet(
            "font-weight: bold; border: none; background: transparent; color: #1e293b;"
        )

        title_lbl = QLabel("<b>Revision History</b>")
        title_lbl.setStyleSheet("border: none; font-size: 14px;")

        add_rev_btn = QPushButton("➕ Add Revision")
        add_rev_btn.setFixedHeight(24)
        add_rev_btn.clicked.connect(self._add_revision_from_preview)

        header.addWidget(toggle_btn)
        header.addWidget(title_lbl)
        header.addStretch()
        header.addWidget(add_rev_btn)
        layout.addLayout(header)

        # ── collapsible container ────────────────────────────────────────────────
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container.setContentsMargins(0, 0, 0, 0)
        toggle_btn.clicked.connect(
            lambda checked: self._toggle_container(checked, container, toggle_btn)
        )
        layout.addWidget(container)

        # ── revision table ───────────────────────────────────────────────────────
        try:
            quote_data = self.service.get_quotation_by_id(self.quote_id)
            base_quote_id = quote_data.get("BaseQuoteID") if quote_data and quote_data.get("BaseQuoteID") else self.quote_id
                
            rows = self.service.get_revisions_for_quote(base_quote_id)

            self._revision_table = QTableWidget(len(rows), 4)
            self._revision_table.setHorizontalHeaderLabels(["ID", "Revision No", "Date", "Project"])
            self._revision_table.hideColumn(0)
            self._revision_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
            self._revision_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
            self._revision_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
            self._revision_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self._revision_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self._revision_table.setSelectionBehavior(QTableWidget.SelectRows)

            for r, row in enumerate(rows):
                id_item = QTableWidgetItem(str(row.get("ID", "")))
                
                rev_no = row.get("RevisionNo", 0)
                rev_no_item = QTableWidgetItem(str(rev_no))
                rev_no_item.setFlags(rev_no_item.flags() & ~Qt.ItemIsEditable)

                date_val = row.get("Date_Quote")
                if isinstance(date_val, datetime):
                    date_str = date_val.strftime("%d-%b-%Y")
                else:
                    date_str = str(date_val) if date_val is not None else ""
                date_item = QTableWidgetItem(date_str)
                date_item.setFlags(date_item.flags() & ~Qt.ItemIsEditable)

                desc_item = QTableWidgetItem(str(row.get("QuoteProjectName", "")))
                desc_item.setFlags(desc_item.flags() & ~Qt.ItemIsEditable)

                self._revision_table.setItem(r, 0, id_item)
                self._revision_table.setItem(r, 1, rev_no_item)
                self._revision_table.setItem(r, 2, date_item)
                self._revision_table.setItem(r, 3, desc_item)
                
                # Highlight current
                if row.get("ID") == self.quote_id:
                    for c in range(4):
                        self._revision_table.item(r, c).setBackground(Qt.yellow)

            # Fit height to content
            self._revision_table.resizeRowsToContents()
            row_count = max(len(rows), 1)
            total_height = (
                self._revision_table.horizontalHeader().height()
                + self._revision_table.rowHeight(0) * row_count
                + 10
            ) if len(rows) > 0 else (
                self._revision_table.horizontalHeader().height() + 40
            )
            self._revision_table.setFixedHeight(min(total_height, 250))

            container_layout.addWidget(self._revision_table)

        except Exception as e:
            container_layout.addWidget(QLabel(f"Failed to load revisions: {e}"))

        self.content_layout.addWidget(group)
        return toggle_btn, container

    def _add_revision_from_preview(self):
        """Creates a new revision for the current quotation and refreshes the view."""
        try:
            new_quote_id = self.service.create_revision(self.quote_id)
            
            # Switch context in main window
            if hasattr(self.main_window, 'populate_revisions'):
                quote_data = self.service.get_quotation_by_id(self.quote_id)
                base_quote_id = quote_data.get("BaseQuoteID") if quote_data else self.quote_id
                self.main_window.populate_revisions(base_quote_id, new_quote_id)
                
            self.refresh_view()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
