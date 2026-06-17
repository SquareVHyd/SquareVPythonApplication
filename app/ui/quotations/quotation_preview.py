from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame,
    QPushButton, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QSizePolicy, QDialog
)
from PySide6.QtCore import Qt
from app.services.quotation_service import QuotationService
from app.ui.quotations.quotation_form import QuotationForm
from app.ui.quotations.panel_form import PanelForm
from app.ui.quotations.modules.panel_module_form import PanelModuleForm
from app.ui.quotations.module_items.module_item_form import ModuleItemForm
from app.ui.quotations.module_items.select_module_items_dialog import SelectModuleItemsDialog

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
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        
        # Header Section
        header = QHBoxLayout()
        self.title_label = QLabel("Quotation Preview & Management")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #1e293b;")
        
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

    def refresh_view(self):
        if not self.quote_id:
            return

        # Clear existing layout
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # 1. Quotation Details Section
        quote_data = self.service.get_quotation_by_id(self.quote_id)
        if quote_data:
            self.title_label.setText(f"Preview: {quote_data.get('QuoteProjectName', 'N/A')}")
            self._add_quotation_header(quote_data)

        # 2. Panels Section
        panels = self.service.get_panels_by_quote(self.quote_id)
        
        # Calculate Grand Total for the entire quotation
        grand_total = 0.0
        for p_row in panels:
            pid, _, _, _, _, qty, _, _, _, _, _, _, _, _ = p_row
            p_qty = float(qty or 0)
            p_modules = self.service.get_panel_modules_by_panel_id(pid)
            p_panel_total = 0.0
            for m_row in p_modules:
                m_qty = m_row[5]
                mt_id = m_row[6]
                m_items = self.service.get_module_items_by_module_type_id(mt_id)
                total_items_amount = sum(float(item[7] or 0) for item in m_items)
                p_panel_total += float(m_qty or 0) * total_items_amount
            grand_total += p_panel_total * p_qty

        panel_section_header = QHBoxLayout()
        panel_title = QLabel(f"Panels ({len(panels)})")
        panel_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #334155; margin-top: 10px;")
        grand_total_lbl = QLabel(f"<b>Total Quotation Price =</b> ₹{grand_total:,.2f}")
        grand_total_lbl.setStyleSheet("font-size: 16px; color: #dc2626; font-weight: bold; margin-top: 10px; margin-left: 20px;")
        add_panel_btn = QPushButton("➕ Add Panel")
        add_panel_btn.clicked.connect(self._add_panel)
        panel_section_header.addWidget(panel_title)
        panel_section_header.addWidget(grand_total_lbl)
        panel_section_header.addStretch()
        panel_section_header.addWidget(add_panel_btn)
        self.content_layout.addLayout(panel_section_header)

        for p_row in panels:
            self._add_panel_widget(p_row)

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
        edit_btn.setFixedWidth(120)
        edit_btn.clicked.connect(lambda: self._edit_quotation(data))
        btn_layout.addWidget(lbl)
        btn_layout.addStretch()
        btn_layout.addWidget(edit_btn)
        
        layout.addLayout(btn_layout)
        self.content_layout.addWidget(group)

    def _add_panel_widget(self, p_row):
        pid, qid, cat, ser, name, qty, l, h, d, w, ka, er, st, bm = p_row
        
        # Calculate Panel Total (Sum of all contained module totals)
        panel_qty = float(qty or 0)
        modules = self.service.get_panel_modules_by_panel_id(pid)
        panel_total = 0.0
        for m_row in modules:
            m_qty = m_row[5]
            mt_id = m_row[6]
            m_items = self.service.get_module_items_by_module_type_id(mt_id)
            total_items_amount = sum(float(item[7] or 0) for item in m_items)
            panel_total += float(m_qty or 0) * total_items_amount
        total_panel_cost = panel_total * panel_qty

        panel_frame = QFrame()
        panel_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        panel_frame.setStyleSheet("QFrame { background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; }")
        layout = QVBoxLayout(panel_frame)

        # Panel Header
        header = QHBoxLayout()

        # Toggle Button
        toggle_btn = QPushButton("▼")
        toggle_btn.setFixedSize(24, 24)
        toggle_btn.setCheckable(True)
        toggle_btn.setChecked(True)
        toggle_btn.setStyleSheet("font-weight: bold; border: none; background: transparent; color: #1e293b;")

        p_info = QLabel(f"<b>Panel:</b> {name} ({cat}) | <b>Qty:</b> {qty} | <b>Dim:</b> {l}x{h}x{d}")
        p_info.setStyleSheet("border: none; font-size: 13px;")
        
        # Panel Cost Label
        total_panel_lbl = QLabel(f"<b>Qty =</b> {panel_qty} | <b>Unit Panel Cost =</b> ₹{panel_total:,.2f} | <b>Total Panel Cost =</b> ₹{total_panel_cost:,.2f}")
        total_panel_lbl.setStyleSheet("border: none; color: #1d4ed8; font-weight: bold; margin-left: 15px;")

        edit_btn = QPushButton("✏️")
        edit_btn.setToolTip("Edit Panel")
        edit_btn.clicked.connect(lambda: self._edit_panel(p_row))
        
        del_btn = QPushButton("🗑️")
        del_btn.setToolTip("Delete Panel")
        del_btn.clicked.connect(lambda: self._delete_panel(pid))
        
        add_mod_btn = QPushButton("📦 Add Module")
        add_mod_btn.setFixedWidth(100)
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
        
        toggle_btn.clicked.connect(lambda checked: self._toggle_container(checked, modules_container, toggle_btn))
        layout.addWidget(modules_container)

        # Modules Section
        for m_row in modules:
            self._add_module_widget(modules_layout, m_row)

        self.content_layout.addWidget(panel_frame)

    def _add_module_widget(self, parent_layout, m_row):
        # Unpack based on QuotationService.get_panel_modules_by_panel_id order
        # ID, PanelID, PanelName, PanelQty, IngOg, PanelModQty, ModuleTypeID, Pnl_Module_Type, Pole, Ka, Release, Protection, Remark
        pm_id, pid, p_name, p_qty, ing_og, m_qty, mt_id, mt_name, pole, ka, rel, prot, rem = m_row
        
        # Fetch items first to calculate total module cost
        items = self.service.get_module_items_by_module_type_id(mt_id)
        total_items_amount = sum(float(item[7] or 0) for item in items)
        module_total = float(m_qty or 0) * total_items_amount

        mod_group = QGroupBox()
        mod_group.setStyleSheet("QGroupBox { border: 1px solid #94a3b8; margin-top: 15px; padding-top: 10px; font-weight: normal; }")
        layout = QVBoxLayout(mod_group)

        # Module Header with Edit/Delete
        mod_header = QHBoxLayout()

        # Toggle Button
        toggle_btn = QPushButton("▼")
        toggle_btn.setFixedSize(24, 24)
        toggle_btn.setCheckable(True)
        toggle_btn.setChecked(True)
        toggle_btn.setStyleSheet("font-weight: bold; border: none; background: transparent; color: #334155;")

        mod_lbl = QLabel(f"<b>Module:</b> {mt_name} | <b>Ing/Og:</b> {ing_og} | <b>P/kA:</b> {pole}/{ka}")
        mod_lbl.setStyleSheet("border: none;")
        
        # Total Module Cost Label
        total_mod_lbl = QLabel(f"<b>Qty =</b> {m_qty} | <b>Unit Module Cost =</b> ₹{total_items_amount:,.2f} | <b>Module Total =</b> ₹{module_total:,.2f}")
        total_mod_lbl.setStyleSheet("border: none; color: #059669; font-weight: bold; margin-left: 15px;")

        m_edit_btn = QPushButton("✏️")
        m_edit_btn.setFixedSize(24, 24)
        m_edit_btn.clicked.connect(lambda: self._edit_module(m_row))
        
        m_del_btn = QPushButton("🗑️")
        m_del_btn.setFixedSize(24, 24)
        m_del_btn.clicked.connect(lambda: self._delete_module(pm_id))
        m_add_item_btn = QPushButton("➕ Item")
        m_add_item_btn.setFixedSize(60, 24)
        m_add_item_btn.clicked.connect(lambda: self._add_item(mt_id, m_qty)) # Pass m_qty here

        m_add_from_mod_btn = QPushButton("📂 From Library") # New button
        m_add_from_mod_btn.setFixedSize(100, 24)
        m_add_from_mod_btn.clicked.connect(lambda: self._add_from_module(mt_id)) # Pass mt_id here

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
                # SQL indices: 0:ID, 1:Desc, 2:BOM, 3:LP, 4:Disc, 5:Selection, 6:Make, 7:Amount
                table.setItem(r, 0, QTableWidgetItem(str(item[1])))
                table.setItem(r, 1, QTableWidgetItem(str(item[6] or "")))
                table.setItem(r, 2, QTableWidgetItem(str(item[2])))
                table.setItem(r, 3, QTableWidgetItem(f"{item[3]:,.2f}"))
                table.setItem(r, 4, QTableWidgetItem(f"{item[4]*100:.1f}%"))
                table.setItem(r, 5, QTableWidgetItem(f"{item[7]:,.2f}"))

                # Row Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(2, 2, 2, 2)
                actions_layout.setSpacing(4)
                
                i_edit = QPushButton("✏️"); i_edit.setFixedSize(20, 20)
                i_edit.clicked.connect(lambda _, it=item, mid=mt_id: self._edit_item(mid, it))
                
                i_del = QPushButton("🗑️"); i_del.setFixedSize(20, 20)
                i_del.clicked.connect(lambda _, it=item, mid=mt_id: self._delete_item(mid, it))
                
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

    def _add_module(self, panel_id):
        dialog = PanelModuleForm(self.quote_id, panel_id=panel_id, parent=self)
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
        dialog = PanelModuleForm(self.quote_id, panel_id=panel_id, pm_data=current_data, parent=self)
        if dialog.exec():
            self.service.update_panel_module(pm_id, **dialog.get_data())
            self.refresh_view()

    def _delete_module(self, pm_id):
        if QMessageBox.question(self, "Confirm", "Delete this module entry?") == QMessageBox.Yes:
            self.service.delete_panel_module(pm_id)
            self.refresh_view()

    def _add_item(self, mt_id, panel_mod_qty):
        # The ModuleItemForm expects module_type_id as the first argument
        dialog = ModuleItemForm(mt_id, module_item_data={"bom": panel_mod_qty, "selection": "Selected"}, parent=self)
        if dialog.exec():
            d = dialog.get_data()
            self.service.create_module_item(
                d["module_type_id"],
                d["drive_description"],
                d["bom"],
                d["lp"],
                d["discount"],
                d["selection"]
            )
            self.refresh_view()

    def _edit_item(self, mt_id, item_row):
        # item_row: (ID, DriveDescription, BOM, LP, Disc, Selection)
        old_desc = item_row[1]
        current_data = {
            "module_type_id": mt_id, # This is the ID for tbl_PnlModuleType
            "drive_description": item_row[1],
            "bom": float(item_row[2] or 0),
            "lp": float(item_row[3] or 0),
            "discount": float(item_row[4] or 0),
            "selection": item_row[5]
        }
        # ModuleItemForm expects module_type_id as the first argument
        dialog = ModuleItemForm(mt_id, module_item_data=current_data, parent=self)
        if dialog.exec():
            d = dialog.get_data()
            self.service.update_module_item(
                mt_id, old_desc,  # Old PK components
                d["module_type_id"], d["drive_description"], d["bom"], d["lp"], d["discount"], d["selection"] # New Data components
            )
            self.refresh_view()

    def _delete_item(self, mt_id, item_row):
        desc = item_row[1]
        if QMessageBox.question(self, "Confirm", f"Remove item '{desc}' from this module type?") == QMessageBox.Yes:
            self.service.delete_module_item(mt_id, desc)
            self.refresh_view()

    def _add_from_module(self, mt_id):
        dialog = SelectModuleItemsDialog(target_mt_id=mt_id, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_view()
