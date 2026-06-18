import re

with open(r'f:\python_project\sqv_180062026\SquareVPythonApplication\app\ui\quotations\quotation_page.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update imports
content = content.replace(
    "QDialog, QHeaderView",
    "QDialog, QHeaderView, QSplitter, QScrollArea, QGroupBox, QFormLayout"
)

# 2. Modify setup_ui
setup_ui_old = """        layout.addWidget(self.table)

        self.status_bar = QStatusBar()
        layout.addWidget(self.status_bar)"""

setup_ui_new = """        self.splitter = QSplitter(Qt.Vertical)
        
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.addWidget(self.table)
        self.splitter.addWidget(top_widget)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.details_container = QWidget()
        self.details_layout = QVBoxLayout(self.details_container)
        self.details_layout.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(self.details_container)
        self.splitter.addWidget(self.scroll_area)
        
        self.splitter.setSizes([400, 300])
        layout.addWidget(self.splitter)

        self.status_bar = QStatusBar()
        layout.addWidget(self.status_bar)"""

content = content.replace(setup_ui_old, setup_ui_new)

# 3. Modify _on_selection_changed
on_selection_changed_old = """    def _on_selection_changed(self):
        \"\"\"Enables the Panels button only when a single quotation is selected.\"\"\"
        selected = self.table.selectionModel().selectedRows()
        if hasattr(self.parent_quotation_details_page, 'update_panels_button_state'):
            self.parent_quotation_details_page.update_panels_button_state(len(selected) == 1)"""

on_selection_changed_new = """    def _clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self._clear_layout(child.layout())

    def _toggle_container(self, checked, container, btn):
        container.setVisible(checked)
        btn.setText("▼" if checked else "▶")

    def _on_selection_changed(self):
        \"\"\"Enables the Panels button and updates the detail views.\"\"\"
        selected = self.table.selectionModel().selectedRows()
        if hasattr(self.parent_quotation_details_page, 'update_panels_button_state'):
            self.parent_quotation_details_page.update_panels_button_state(len(selected) == 1)
            
        self._clear_layout(self.details_layout)
        if len(selected) == 1:
            row = selected[0].row()
            quote_id = int(self.table.item(row, 0).text())
            customer_id = int(self.table.item(row, 1).text())
            self._add_customer_details(customer_id)
            self._add_quotation_ctc_form(quote_id)
            self._add_common_specs_form(quote_id)"""

content = content.replace(on_selection_changed_old, on_selection_changed_new)

# 4. Add methods before CustomerViewDialog
methods_to_add = """    def _add_customer_details(self, customer_id):
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
        
        table = SearchableTable()
        try:
            import pyodbc
            conn = pyodbc.connect('DSN=PostgreSQL35W;')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM public."tblCustomers" WHERE "ID" = ?', (customer_id,))
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            conn.close()

            table.setColumnCount(len(columns))
            table.setHorizontalHeaderLabels(columns)
            table.setRowCount(len(rows))

            for r, row in enumerate(rows):
                for c, val in enumerate(row):
                    text = str(val) if val is not None else ""
                    item = NumericTableWidgetItem(text)
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    table.setItem(r, c, item)

            table.resizeColumnsToContents()
            total_height = table.horizontalHeader().height() + 52
            if len(rows) > 0:
                total_height += table.rowHeight(0) * len(rows)
            table.setFixedHeight(min(total_height, 150))
            
            container_layout.addWidget(table)
            self.details_layout.addWidget(group)
        except Exception as e:
            container_layout.addWidget(QLabel(f"Failed to load customer details: {e}"))
            self.details_layout.addWidget(group)

    def _add_quotation_ctc_form(self, quote_id):
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
            self.service.save_quote_ctc(QuoteID=quote_id)
            rows = self.service.get_quote_ctc_list(quote_id)
            if rows:
                data = rows[0]
                ctc_id = data[0]
                
                gst_input = QLineEdit(str(data[2]) if data[2] is not None else "")
                freight_input = QLineEdit(str(data[3]) if data[3] is not None else "")
                payment_input = QLineEdit(str(data[4]) if data[4] is not None else "")
                warranty_input = QLineEdit(str(data[5]) if data[5] is not None else "")
                validity_input = QLineEdit(str(data[6]) if data[6] is not None else "")
                packing_input = QLineEdit(str(data[7]) if data[7] is not None else "")
                inspection_input = QLineEdit(str(data[8]) if data[8] is not None else "")
                delivery_input = QLineEdit(str(data[9]) if data[9] is not None else "")
                bank_input = QLineEdit(str(data[10]) if data[10] is not None else "")
                notes_input = QLineEdit(str(data[11]) if data[11] is not None else "")
                
                container_layout.addRow("GST / Taxes:", gst_input)
                container_layout.addRow("Freight & Insurance:", freight_input)
                container_layout.addRow("Payment:", payment_input)
                container_layout.addRow("Warranty:", warranty_input)
                container_layout.addRow("Validity:", validity_input)
                container_layout.addRow("Packing:", packing_input)
                container_layout.addRow("Inspection:", inspection_input)
                container_layout.addRow("Delivery:", delivery_input)
                container_layout.addRow("Bank Details:", bank_input)
                container_layout.addRow("Notes:", notes_input)
                
                save_btn = QPushButton("💾 Save CTC")
                save_btn.clicked.connect(lambda: self._save_ctc_form(
                    ctc_id, gst_input, freight_input, payment_input, warranty_input, 
                    validity_input, packing_input, inspection_input, delivery_input, 
                    bank_input, notes_input
                ))
                container_layout.addRow("", save_btn)
                
            self.details_layout.addWidget(group)
        except Exception as e:
            container_layout.addRow(QLabel(f"Failed to load CTC: {e}"))
            self.details_layout.addWidget(group)

    def _save_ctc_form(self, ctc_id, gst_input, freight_input, payment_input, warranty_input, validity_input, packing_input, inspection_input, delivery_input, bank_input, notes_input):
        try:
            self.service.update_quote_ctc_field(ctc_id, "GSTTax", gst_input.text())
            self.service.update_quote_ctc_field(ctc_id, "FreightAndInsurance", freight_input.text())
            self.service.update_quote_ctc_field(ctc_id, "Payment", payment_input.text())
            self.service.update_quote_ctc_field(ctc_id, "Warranty", warranty_input.text())
            self.service.update_quote_ctc_field(ctc_id, "Validity", validity_input.text())
            self.service.update_quote_ctc_field(ctc_id, "Packing", packing_input.text())
            self.service.update_quote_ctc_field(ctc_id, "Inspection", inspection_input.text())
            self.service.update_quote_ctc_field(ctc_id, "Delivery", delivery_input.text())
            self.service.update_quote_ctc_field(ctc_id, "BankDetails", bank_input.text())
            self.service.update_quote_ctc_field(ctc_id, "Notes", notes_input.text())
            QMessageBox.information(self, "Success", "CTC saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save CTC: {e}")

    def _add_common_specs_form(self, quote_id):
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
            self.service.save_common_specs(quote_id)
            rows = self.service.get_common_specs_list(quote_id)
            if rows:
                data = rows[0]
                spec_id = data[0]
                
                spec_labels = [
                    "Voltage", "Phase", "Frequency", "System Earthing", "Short Circuit Level", "Ambient Temperature",
                    "Degree of Protection", "Form of Separation", "Standard", "Panel Base Frame",
                    "Cable Entry", "Color Shade", "Busbar System", "Earth Busbar"
                ]
                
                inputs = []
                for i, label in enumerate(spec_labels):
                    val_index = i + 2
                    val = str(data[val_index]) if val_index < len(data) and data[val_index] is not None else ""
                    inp = QLineEdit(val)
                    container_layout.addRow(label + ":", inp)
                    inputs.append(inp)
                
                save_btn = QPushButton("💾 Save Common Specs")
                save_btn.clicked.connect(lambda _, sid=spec_id, inps=inputs, lbls=spec_labels: self._save_common_specs_form(sid, inps, lbls))
                container_layout.addRow("", save_btn)
                
            self.details_layout.addWidget(group)
        except Exception as e:
            container_layout.addRow(QLabel(f"Failed to load Common Specs: {e}"))
            self.details_layout.addWidget(group)

    def _save_common_specs_form(self, spec_id, inputs, spec_labels):
        try:
            db_columns = [
                "Voltage", "Phase", "Frequency", "SystemEarthing", "ShortCircuitLevel", "AmbientTemperature",
                "DegreeOfProtection", "FormOfSeparation", "Standard", "PanelBaseFrame",
                "CableEntry", "ColorShade", "BusbarSystem", "EarthBusbar"
            ]
            for i, col in enumerate(db_columns):
                self.service.update_common_specs_field(spec_id, col, inputs[i].text())
            QMessageBox.information(self, "Success", "Common Specs saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save Common Specs: {e}")

"""

content = content.replace("class CustomerViewDialog(QDialog):", methods_to_add + "\nclass CustomerViewDialog(QDialog):")

with open(r'f:\python_project\sqv_180062026\SquareVPythonApplication\app\ui\quotations\quotation_page.py', 'w', encoding='utf-8') as f:
    f.write(content)
