import pyodbc
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLineEdit, QLabel, QAbstractItemView, QMessageBox, QMenu, QStatusBar, QApplication,
    QDialog, QHeaderView, QSplitter, QScrollArea, QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QShortcut, QKeySequence, QAction

from app.services.quotation_service import QuotationService
from app.ui.quotations.quotation_form import QuotationForm
from app.ui.quotations.quotation_ctc_dialog import QuotationCTCDialog
from app.ui.quotations.module_items.module_items_viewer_dialog import ModuleItemsViewerDialog
from app.ui.quotations.quotation_preview_dialog import QuotationPreviewDialog
from app.ui.searchable_table import SearchableTable, NumericTableWidgetItem
from app.utils.worker_thread import Worker


class QuotationPage(QWidget):
    def __init__(self, parent_quotation_details_page=None):
        super().__init__()
        self.service = QuotationService()
        self._cache = []
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._perform_search)
        self._worker = None
        self.parent_quotation_details_page = parent_quotation_details_page # Store reference to QuotationDetailsPage
        self.setup_ui()
        self.refresh_table()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("Quotations Management")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search by Customer, Project, or Ref No...")
        self.search_box.textChanged.connect(self._debounce_search)

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh_table)
        
        self.items_btn = QPushButton("📦 Items")
        self.items_btn.clicked.connect(self._show_items_viewer)

        self.add_btn = QPushButton("➕ Add")
        self.add_btn.setToolTip("(Ctrl+N)")
        self.add_btn.clicked.connect(self.add_quotation)

        self.edit_btn = QPushButton("✏️ Edit")
        self.edit_btn.setToolTip("(Ctrl+E)")
        self.edit_btn.clicked.connect(self.edit_quotation)

        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.setToolTip("(Delete)")
        self.delete_btn.clicked.connect(self.delete_quotation)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.search_box)
        header.addWidget(self.refresh_btn)
        header.addWidget(self.items_btn)
        header.addWidget(self.add_btn)
        header.addWidget(self.edit_btn)
        header.addWidget(self.delete_btn)
        layout.addLayout(header)

        # Table
        self.table = SearchableTable()
        self.table.setStyleSheet("QTableView { selection-background-color: #93c5fd; selection-color: #000000; }") # Keep existing style
        self.table.setColumnCount(11) # Increased by 1 for CustomerId
        self.table.setHorizontalHeaderLabels([
            "ID", "Customer ID", "Customer", "Req. Date", "Quote Date", "Ref No", 
            "Subject", "Project", "Contact", "Prepared By", "Status"
        ])
        self.table.hideColumn(0) # Hide Quote ID
        self.table.hideColumn(1) # Hide Customer ID
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSortingEnabled(True)
        
        # Right-click context menu
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        
        # Track selection to enable/disable Panels button
        self.table.itemSelectionChanged.connect(self._on_selection_changed)

        # Double click to edit
        self.table.itemDoubleClicked.connect(self.edit_quotation)
        
        self.splitter = QSplitter(Qt.Vertical)
        
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
        layout.addWidget(self.status_bar)

        QShortcut(QKeySequence("Ctrl+R"), self, activated=self.refresh_table)
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self.add_quotation)
        QShortcut(QKeySequence("Ctrl+E"), self, activated=self.edit_quotation)
        QShortcut(QKeySequence("Delete"), self, activated=self.delete_quotation)
        QShortcut(QKeySequence("Ctrl+F"), self, activated=lambda: self.search_box.setFocus())

    def _clear_layout(self, layout):
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
        """Enables the Panels button and updates the detail views."""
        selected = self.table.selectionModel().selectedRows()
        if hasattr(self.parent_quotation_details_page, 'update_panels_button_state'):
            self.parent_quotation_details_page.update_panels_button_state(len(selected) == 1)
            
        self._clear_layout(self.details_layout)
        if len(selected) == 1:
            from PySide6.QtWidgets import QPushButton
            btn_collapse_all = QPushButton("Collapse All Forms")
            btn_collapse_all.setCheckable(True)
            btn_collapse_all.setStyleSheet("background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 4px; padding: 4px; font-weight: bold; margin-bottom: 5px;")
            self.details_layout.addWidget(btn_collapse_all)

            row = selected[0].row()
            quote_id = int(self.table.item(row, 0).text())
            customer_id = int(self.table.item(row, 1).text())
            t1, c1 = self._add_customer_details(customer_id)
            t2, c2 = self._add_quotation_ctc_form(quote_id)
            t3, c3 = self._add_common_specs_form(quote_id)

            def toggle_all(checked):
                btn_collapse_all.setText("Expand All Forms" if checked else "Collapse All Forms")
                for t, c in [(t1, c1), (t2, c2), (t3, c3)]:
                    if t and c:
                        t.setChecked(not checked)
                        self._toggle_container(not checked, c, t)

            btn_collapse_all.clicked.connect(toggle_all)

    def add_quotation(self):
        """Opens the form to add a new quotation."""
        dialog = QuotationForm(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                self.service.create_quotation(**data)
                QMessageBox.information(self, "Success", "Quotation created successfully.")
                self.refresh_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create quotation: {e}")

    def edit_quotation(self):
        """Opens the form to edit the selected quotation."""
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Selection Required", "Please select a quotation to edit.")
            return
        
        row = selected[0].row()
        # Build data dictionary from table row
        quot_id = int(self.table.item(row, 0).text())
        current_data = {
            "id": quot_id,
            "customer_id": int(self.table.item(row, 1).text()),
            "req_date": self.table.item(row, 3).text(),
            "quote_date": self.table.item(row, 4).text(),
            "ref_no": self.table.item(row, 5).text(),
            "subject": self.table.item(row, 6).text(),
            "project": self.table.item(row, 7).text(),
            "contact": self.table.item(row, 8).text(),
            "prepared_by": self.table.item(row, 9).text(),
            "status": self.table.item(row, 10).text(),
        }

        dialog = QuotationForm(self, quotation_data=current_data)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                self.service.update_quotation(quot_id, **data)
                QMessageBox.information(self, "Success", "Quotation updated successfully.")
                self.refresh_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update quotation: {e}")

    def delete_quotation(self):
        """Deletes the selected quotation(s)."""
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Selection Required", "Please select quotation(s) to delete.")
            return

        if QMessageBox.question(self, "Confirm Delete", 
                               f"Are you sure you want to delete {len(selected)} quotation(s)?",
                               QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            try:
                for index in selected:
                    quot_id = int(self.table.item(index.row(), 0).text())
                    self.service.delete_quotation(quot_id)
                QMessageBox.information(self, "Deleted", "Quotation(s) removed successfully.")
                self.refresh_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete: {e}")

    def show_panels(self):
        """Opens the Panel Manager for the selected quotation."""
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return
            
        row = selected[0].row()
        quote_id = int(self.table.item(row, 0).text())
        project_name = self.table.item(row, 7).text()
        
        if hasattr(self.parent_quotation_details_page, 'open_panel_view'):
            self.parent_quotation_details_page.open_panel_view(quote_id, project_name)

    def _show_items_viewer(self):
        """Opens the Module Items Viewer for the selected quotation."""
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Selection Required", "Please select a quotation to view its items.")
            return
        row = selected[0].row()
        quote_id = int(self.table.item(row, 0).text())
        # Call the show_items method of the parent QuotationDetailsPage/Window
        self.parent_quotation_details_page.show_items()

    def refresh_table(self):
        if self._worker: return
        self.status_bar.showMessage("Fetching quotations...")
        self._worker = Worker(self.service.get_all_quotations)
        self._worker.result.connect(self._on_data_loaded)
        self._worker.start()

    def _on_data_loaded(self, rows):
        self._cache = list(rows)
        self._render(self._cache)
        self.status_bar.showMessage(f"Loaded {len(rows)} quotations", 5000)
        self._worker = None

    def _render(self, rows):
        self.table.blockSignals(True)
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c in range(len(row)):
                val = str(row[c]) if row[c] is not None else ""
                item = NumericTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(r, c, item)
        self.table.setSortingEnabled(True)
        self.table.blockSignals(False)
        self.table.resizeColumnsToContents()

    def _debounce_search(self):
        self._search_timer.start(300)

    def _perform_search(self):
        keyword = self.search_box.text().lower().strip()
        if not keyword:
            self._render(self._cache)
            return
        filtered = [row for row in self._cache if any(keyword in str(cell).lower() for cell in row)]
        self._render(filtered)

    def _show_context_menu(self, pos: QPoint):
        item = self.table.itemAt(pos)
        if not item: return
        
        row = item.row()
        quote_id = int(self.table.item(row, 0).text())
        project_name = self.table.item(row, 7).text()
        customer_id = self.table.item(row, 1).text()
        customer_name = self.table.item(row, 2).text()
        
        menu = QMenu(self)
        items_action = QAction(f"📦 View Module Items: {project_name}", self)
        items_action.triggered.connect(lambda: self.parent_quotation_details_page.show_items())
        menu.addAction(items_action)

        rev_action = QAction(f"🔄 Revisions: {project_name}", self)
        rev_action.triggered.connect(self._open_revisions)
        menu.addAction(rev_action)

        preview_action = QAction(f"👁️ Preview Quotation: {project_name}", self)
        preview_action.triggered.connect(lambda: self._open_quotation_preview(quote_id))
        menu.addAction(preview_action)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _open_common_specs(self):
        if self.parent_quotation_details_page:
            self.parent_quotation_details_page.show_common_specs()

    def _open_revisions(self):
        if self.parent_quotation_details_page:
            self.parent_quotation_details_page.show_revision()

    def _open_ctc_dialog(self, quote_id, project_name):
        dialog = QuotationCTCDialog(quote_id, project_name, self)
        dialog.exec()

    def _open_quotation_preview(self, quote_id):
        """Opens the quotation preview dialog."""
        dialog = QuotationPreviewDialog(quote_id, self)
        dialog.exec()

    def _view_customer_details(self, customer_id):
        dialog = CustomerViewDialog(customer_id, self)
        dialog.exec()

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
            return toggle_btn, container
        except Exception as e:
            container_layout.addWidget(QLabel(f"Failed to load customer details: {e}"))
            self.details_layout.addWidget(group)
            return None, None

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
            return toggle_btn, container
        except Exception as e:
            container_layout.addRow(QLabel(f"Failed to load CTC: {e}"))
            self.details_layout.addWidget(group)
            return None, None

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
            return toggle_btn, container
        except Exception as e:
            container_layout.addRow(QLabel(f"Failed to load Common Specs: {e}"))
            self.details_layout.addWidget(group)
            return None, None

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


class CustomerViewDialog(QDialog):
    def __init__(self, target_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Customer Record Viewer")
        self.resize(1100, 700)
        self.dsn = "PostgreSQL35W"
        
        layout = QVBoxLayout(self)
        self.table = SearchableTable()
        layout.addWidget(self.table)
        
        self.load_data(target_id)

    def load_data(self, target_id):
        try:
            conn = pyodbc.connect(f"DSN={self.dsn};")
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM public."tblCustomers" ORDER BY "ID"')
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            conn.close()

            self.table.setColumnCount(len(columns))
            self.table.setHorizontalHeaderLabels(columns)
            self.table.setRowCount(len(rows))

            target_item = None
            for r, row in enumerate(rows):
                for c, val in enumerate(row):
                    text = str(val) if val is not None else ""
                    item = NumericTableWidgetItem(text)
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.table.setItem(r, c, item)
                    if c == 0 and str(val) == str(target_id):
                        target_item = item

            self.table.resizeColumnsToContents()
            if target_item:
                self.table.scrollToItem(target_item, QAbstractItemView.PositionAtCenter)
                self.table.selectRow(target_item.row())
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load customer details: {e}")
