from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QFormLayout, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt
from app.services.quotation_service import QuotationService

class QuotationPreviewDialog(QDialog):
    def __init__(self, quote_id, parent=None):
        super().__init__(parent)
        self.quote_id = quote_id
        self.service = QuotationService()
        self.setWindowTitle(f"Quotation Preview - ID: {quote_id}")
        self.resize(1000, 800)
        self.setup_ui()
        self.load_quotation_preview()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Main Quotation Details Section
        self.quote_details_group = QGroupBox("Quotation Details")
        self.quote_details_layout = QFormLayout(self.quote_details_group)
        self.lbl_quote_subject = QLabel(); self.quote_details_layout.addRow("Subject:", self.lbl_quote_subject)
        self.lbl_quote_project = QLabel(); self.quote_details_layout.addRow("Project Name:", self.lbl_quote_project)
        self.lbl_customer_name = QLabel(); self.quote_details_layout.addRow("Customer:", self.lbl_customer_name)
        self.lbl_ref_no = QLabel(); self.quote_details_layout.addRow("Reference No:", self.lbl_ref_no)
        self.lbl_quote_date = QLabel(); self.quote_details_layout.addRow("Quote Date:", self.lbl_quote_date)
        main_layout.addWidget(self.quote_details_group)

        # Scrollable Area for Panels
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)

        # Close Button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        main_layout.addWidget(close_btn, alignment=Qt.AlignRight)

    def load_quotation_preview(self):
        # Clear previous content
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Load main quotation details
        quote_data = self.service.get_quotation_by_id(self.quote_id)
        if quote_data:
            self.setWindowTitle(f"Quotation Preview - {quote_data.get('QuoteSubject', 'N/A')}")
            self.lbl_quote_subject.setText(quote_data.get("QuoteSubject", "N/A"))
            self.lbl_quote_project.setText(quote_data.get("QuoteProjectName", "N/A"))
            self.lbl_customer_name.setText(quote_data.get("CustomerName", "N/A"))
            self.lbl_ref_no.setText(quote_data.get("QuoteRereceNo", "N/A"))
            self.lbl_quote_date.setText(str(quote_data.get("Date_Quote", "N/A")))
        else:
            QMessageBox.warning(self, "Error", "Could not load main quotation details.")
            return

        # Load panels
        panels = self.service.get_panels_by_quote(self.quote_id)
        if not panels:
            self.scroll_layout.addWidget(QLabel("No panels found for this quotation."))
            return

        for panel_row in panels:
            panel_id, _, _, _, panel_name, panel_qty, _, _, _, _, _, _, _, _ = panel_row

            panel_group = QGroupBox(f"Panel: {panel_name} (Qty: {panel_qty})")
            panel_layout = QVBoxLayout(panel_group)

            # Load modules for this panel
            modules = self.service.get_panel_modules_by_panel_id(panel_id)
            if not modules:
                panel_layout.addWidget(QLabel("No modules found for this panel."))
            else:
                for module_row in modules:
                    pm_id, _, _, _, ing_og, panel_mod_qty, module_type_id, module_type_name, _, _, _, _, _ = module_row

                    module_group = QGroupBox(f"Module: {module_type_name} (Ing/Og: {ing_og}, Qty: {panel_mod_qty})")
                    module_layout = QVBoxLayout(module_group)

                    # Load items for this module instance
                    items = self.service.get_module_items_by_panel_module_id(pm_id)
                    if not items:
                        module_layout.addWidget(QLabel("No items found for this module."))
                    else:
                        items_table = QTableWidget()
                        items_table.setColumnCount(4)
                        items_table.setHorizontalHeaderLabels(["Description", "BOM", "LP", "Discount"])
                        items_table.setRowCount(len(items))
                        items_table.setEditTriggers(QTableWidget.NoEditTriggers)
                        items_table.setSelectionBehavior(QTableWidget.SelectRows)
                        items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch) # Stretch description

                        for r, item_data in enumerate(items):
                            # Safely extract indices as the service now returns more columns
                            desc = item_data[1]
                            bom = item_data[2]
                            lp = item_data[3]
                            disc = item_data[4]
                            
                            items_table.setItem(r, 0, QTableWidgetItem(str(desc)))
                            items_table.setItem(r, 1, QTableWidgetItem(str(bom)))
                            items_table.setItem(r, 2, QTableWidgetItem(f"{lp:,.2f}"))
                            items_table.setItem(r, 3, QTableWidgetItem(f"{disc*100:.2f}%"))
                        items_table.resizeColumnsToContents()
                        module_layout.addWidget(items_table)
                    panel_layout.addWidget(module_group)
            self.scroll_layout.addWidget(panel_group)