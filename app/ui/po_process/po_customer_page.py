from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QAbstractItemView,
    QScrollArea, QFrame
)
from PySide6.QtCore import Qt
from app.services.po_customer_service import POCustomerService
from app.ui.po_process.po_customer_form import POCustomerForm
from app.ui.po_process.select_quote_items_dialog import SelectQuoteItemsDialog
from app.ui.po_process.po_item_form import POItemForm

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

class POCustomerPage(QWidget):
    def __init__(self, parent_process_page):
        super().__init__()
        self.parent_process_page = parent_process_page
        self.service = POCustomerService()
        self.quote_id = None
        self.project_name = ""
        self.po_expanded_states = {}
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)

        # Header Section
        header = QHBoxLayout()
        self.title_label = QLabel("PO Customers")
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
        self.title_label.setText(f"PO Customers - Quote {quote_id} ({project_name})")
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

        self._clear_layout(self.content_layout)

        pos = self.service.get_pos_by_quote(self.quote_id)

        # Calculate Grand Total for all POs
        grand_total = 0.0
        for po in pos:
            po_id = po["ID"]
            items = self.service.get_items_by_po(po_id)
            for item in items:
                grand_total += float(item["Amount"] or 0)

        # Actions Row
        action_header = QHBoxLayout()
        po_title = QLabel(f"Purchase Orders ({len(pos)})")
        po_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #0f172a; margin-top: 10px;")
        
        grand_total_lbl = QLabel(f"<b>Total POs Value =</b> ₹{format_indian_currency(grand_total)}")
        grand_total_lbl.setStyleSheet("font-size: 18px; color: #b91c1c; font-weight: bold; margin-top: 10px; margin-left: 20px;")
        
        btn_collapse_pos = QPushButton("Collapse All POs")
        btn_collapse_pos.setCheckable(True)
        btn_collapse_pos.setStyleSheet("background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 4px; padding: 4px; font-weight: bold; margin-top: 10px;")
        
        add_po_btn = QPushButton("➕ Add PO")
        add_po_btn.clicked.connect(self.add_po)
        add_po_btn.setStyleSheet("margin-top: 10px;")
        
        action_header.addWidget(po_title)
        action_header.addWidget(grand_total_lbl)
        action_header.addStretch()
        action_header.addWidget(btn_collapse_pos)
        action_header.addWidget(add_po_btn)
        self.content_layout.addLayout(action_header)

        self.po_toggles = []
        for po in pos:
            t, c = self._add_po_widget(po)
            if t and c:
                self.po_toggles.append((t, c, po["ID"]))

        def toggle_all_pos(checked):
            btn_collapse_pos.setText("Expand All POs" if checked else "Collapse All POs")
            for t, c, po_id in self.po_toggles:
                t.setChecked(not checked)
                self._on_po_toggled(not checked, po_id, c, t)

        btn_collapse_pos.clicked.connect(toggle_all_pos)
        
        if not self.po_expanded_states:
            btn_collapse_pos.setChecked(True)
            toggle_all_pos(True)

        self.content_layout.addStretch()

    def _add_po_widget(self, po):
        po_id = po["ID"]
        po_no = po["PO_No"]
        po_date = po["PO_Date"]
        
        items = self.service.get_items_by_po(po_id)
        po_total = sum(float(item["Amount"] or 0) for item in items)

        po_frame = QFrame()
        po_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        po_frame.setStyleSheet("QFrame { background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; margin-top: 10px; }")
        layout = QVBoxLayout(po_frame)

        # PO Header
        header = QHBoxLayout()

        toggle_btn = QPushButton()
        toggle_btn.setFixedSize(24, 24)
        toggle_btn.setCheckable(True)
        
        is_expanded = self.po_expanded_states.get(po_id, False)
        toggle_btn.setChecked(is_expanded)
        toggle_btn.setText("▼" if is_expanded else "▶")
        toggle_btn.setStyleSheet("font-weight: bold; border: none; background: transparent; color: #1e293b;")

        p_info = QLabel(f"<b>PO Number:</b> {po_no} | <b>Date:</b> {po_date}")
        p_info.setStyleSheet("border: none; font-size: 14px; color: #1e293b;")
        
        total_lbl = QLabel(f"<b>PO Total Amount =</b> ₹{format_indian_currency(po_total)}")
        total_lbl.setStyleSheet("border: none; font-size: 14px; color: #2563eb; font-weight: bold; margin-left: 15px;")

        edit_btn = QPushButton("✏️")
        edit_btn.setToolTip("Edit PO")
        edit_btn.clicked.connect(lambda: self.edit_po(po))
        
        del_btn = QPushButton("🗑️")
        del_btn.setToolTip("Delete PO")
        del_btn.clicked.connect(lambda: self.delete_po(po_id, po_no))
        
        add_item_btn = QPushButton("➕ Item")
        add_item_btn.setFixedWidth(70)
        add_item_btn.clicked.connect(lambda: self.add_item(po_id))
        
        add_from_quote_btn = QPushButton("📂 Add From Quote")
        add_from_quote_btn.setFixedWidth(120)
        add_from_quote_btn.clicked.connect(lambda: self.add_from_quote(po_id))

        header.addWidget(toggle_btn)
        header.addWidget(p_info)
        header.addWidget(total_lbl)
        header.addStretch()
        header.addWidget(add_from_quote_btn)
        header.addWidget(add_item_btn)
        header.addWidget(edit_btn)
        header.addWidget(del_btn)
        layout.addLayout(header)

        # Container for PO Items (collapsible)
        items_container = QWidget()
        items_layout = QVBoxLayout(items_container)
        items_container.setContentsMargins(0, 0, 0, 0)
        
        items_container.setVisible(is_expanded)
        toggle_btn.clicked.connect(lambda checked, p=po_id, c=items_container, btn=toggle_btn: self._on_po_toggled(checked, p, c, btn))
        layout.addWidget(items_container)

        # Items Table
        if items:
            table = QTableWidget(len(items), 7)
            table.setHorizontalHeaderLabels(["ID", "Description", "Qty", "Price", "Amount", "Warranty", "Actions"])
            table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch) # Description
            table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents) # Qty
            table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents) # Price
            table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents) # Amount
            table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents) # Warranty
            table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents) # Actions

            table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            table.setEditTriggers(QTableWidget.NoEditTriggers)
            
            for r, item in enumerate(items):
                table.setItem(r, 0, QTableWidgetItem(str(item["ID"])))
                table.setItem(r, 1, QTableWidgetItem(item["Description"]))
                table.setItem(r, 2, QTableWidgetItem(str(item["Qty"])))
                table.setItem(r, 3, QTableWidgetItem(f"₹{format_indian_currency(item['Price'])}"))
                table.setItem(r, 4, QTableWidgetItem(f"₹{format_indian_currency(item['Amount'])}"))
                table.setItem(r, 5, QTableWidgetItem(str(item["Warranty"])))

                # Row Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(2, 2, 2, 2)
                actions_layout.setSpacing(4)
                
                i_edit = QPushButton("✏️"); i_edit.setFixedSize(20, 20)
                i_edit.clicked.connect(lambda _, it=item: self.edit_item(it))
                
                i_del = QPushButton("🗑️"); i_del.setFixedSize(20, 20)
                i_del.clicked.connect(lambda _, it=item: self.delete_item(it))
                
                actions_layout.addWidget(i_edit)
                actions_layout.addWidget(i_del)
                table.setCellWidget(r, 6, actions_widget)
            
            table.resizeRowsToContents()
            total_height = table.horizontalHeader().height() + table.verticalHeader().length() + 52
            table.setFixedHeight(total_height)
            
            items_layout.addWidget(table)
        else:
            items_layout.addWidget(QLabel("No items configured for this PO."))

        self.content_layout.addWidget(po_frame)
        return toggle_btn, items_container

    def _toggle_container(self, checked, container, button):
        container.setVisible(checked)
        button.setText("▼" if checked else "▶")

    def _on_po_toggled(self, checked, po_id, container, button):
        self.po_expanded_states[po_id] = checked
        self._toggle_container(checked, container, button)

    # --- PO Operations ---
    def add_po(self):
        if not self.quote_id:
            return
        dialog = POCustomerForm(parent=self)
        if dialog.exec():
            data = dialog.get_data()
            try:
                self.service.create_po(self.quote_id, data["po_no"], data["po_date"])
                self.refresh_view()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create PO: {e}")

    def edit_po(self, po):
        po_id = po["ID"]
        dialog = POCustomerForm(po_data=po, parent=self)
        if dialog.exec():
            data = dialog.get_data()
            try:
                self.service.update_po(po_id, data["po_no"], data["po_date"])
                self.refresh_view()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update PO: {e}")

    def delete_po(self, po_id, po_no):
        reply = QMessageBox.question(self, "Confirm Delete", f"Are you sure you want to delete PO '{po_no}' and all its items?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                self.service.delete_po(po_id)
                self.refresh_view()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete PO: {e}")

    # --- PO Items Operations ---
    def add_from_quote(self, po_id):
        dialog = SelectQuoteItemsDialog(self.quote_id, parent=self)
        if dialog.exec():
            selected_items = dialog.get_selected_items()
            for item in selected_items:
                try:
                    self.service.create_po_item(
                        po_id, 
                        item["Description"], 
                        item["Qty"], 
                        item["Price"], 
                        item["Warranty"]
                    )
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to add item: {e}")
            self.refresh_view()

    def add_item(self, po_id):
        dialog = POItemForm(parent=self)
        if dialog.exec():
            data = dialog.get_data()
            try:
                self.service.create_po_item(
                    po_id,
                    data["description"],
                    data["qty"],
                    data["price"],
                    data["warranty"]
                )
                self.refresh_view()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add item: {e}")

    def edit_item(self, item):
        item_id = item["ID"]
        dialog = POItemForm(item_data=item, parent=self)
        if dialog.exec():
            data = dialog.get_data()
            try:
                self.service.update_po_item(
                    item_id,
                    data["description"],
                    data["qty"],
                    data["price"],
                    data["warranty"]
                )
                self.refresh_view()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update item: {e}")

    def delete_item(self, item):
        item_id = item["ID"]
        desc = item["Description"]
        reply = QMessageBox.question(self, "Confirm Delete", f"Are you sure you want to delete '{desc}'?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                self.service.delete_po_item(item_id)
                self.refresh_view()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete item: {e}")
