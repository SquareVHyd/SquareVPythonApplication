from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QLabel, QScrollArea, QWidget
from PySide6.QtCore import Qt
from app.services.quotation_service import QuotationService

class PanelModulePreviewDialog(QDialog):
    """
    A dialog to display a consolidated view of all panels and their modules
    for a given quotation.
    """
    def __init__(self, quote_id, project_name, parent=None):
        super().__init__(parent)
        self.quote_id = quote_id
        self.project_name = project_name
        self.service = QuotationService()
        self.setWindowTitle(f"Preview: Panels & Modules for {project_name} (Quote ID: {quote_id})")
        self.resize(800, 600)
        self.setup_ui()
        self.load_preview_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        title_label = QLabel(f"Consolidated View for Quote: <b>{self.project_name}</b> (ID: {self.quote_id})")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        self.preview_text_edit = QTextEdit()
        self.preview_text_edit.setReadOnly(True)
        self.preview_text_edit.setFontPointSize(10)
        main_layout.addWidget(self.preview_text_edit)

    def load_preview_data(self):
        preview_content = []
        
        # Fetch all panels for the current quotation
        panels = self.service.get_panels_by_quote(self.quote_id)
        
        if not panels:
            preview_content.append("<i>No panels found for this quotation.</i>")
            self.preview_text_edit.setHtml("".join(preview_content))
            return

        for panel in panels:
            panel_id = panel[0]
            panel_name = panel[4] # "PanelName" column
            panel_category = panel[2] # "PanelCategory" column
            panel_serial = panel[3] # "PanelSerial" column
            
            preview_content.append(f"<h3 style='color:#0056b3;'>Panel: {panel_name} (ID: {panel_id})</h3>")
            preview_content.append(f"<ul>")
            preview_content.append(f"<li><b>Category:</b> {panel_category}</li>")
            preview_content.append(f"<li><b>Serial:</b> {panel_serial}</li>")
            preview_content.append(f"<li><b>Quantity:</b> {panel[5]}</li>")
            preview_content.append(f"<li><b>Dimensions (LxHxD):</b> {panel[6]}x{panel[7]}x{panel[8]} mm</li>")
            preview_content.append(f"</ul>")
            
            # Fetch modules for this specific panel
            modules = self.service.get_panel_modules_by_panel_id(panel_id)
            
            if modules:
                preview_content.append(f"<h4 style='color:#007bff;'>Modules for Panel {panel_name}:</h4>")
                preview_content.append("<table border='1' style='width:100%; border-collapse: collapse;'>")
                preview_content.append("<tr style='background-color:#e9ecef;'>")
                preview_content.append("<th>In/Out</th><th>Qty</th><th>Module Type</th><th>Pole</th><th>KA</th><th>Remark</th>")
                preview_content.append("</tr>")
                for module in modules:
                    # Columns: ID, PanelID, IngOg, PanelModQty, ModuleTypeID, Pnl_Module_Type, ModPole, ModKa, Release, Protection, Remark
                    ing_og = module[2]
                    qty = module[3]
                    module_type = module[5] # Pnl_Module_Type
                    pole = module[6]
                    ka = module[7]
                    remark = module[10]
                    preview_content.append("<tr>")
                    preview_content.append(f"<td>{ing_og}</td><td>{qty}</td><td>{module_type}</td><td>{pole}</td><td>{ka}</td><td>{remark}</td>")
                    preview_content.append("</tr>")
                preview_content.append("</table>")
            else:
                preview_content.append(f"<p><i>No modules found for Panel {panel_name}.</i></p>")
            
            preview_content.append("<hr style='border-top: 1px dashed #ccc;'>") # Separator between panels

        self.preview_text_edit.setHtml("".join(preview_content))