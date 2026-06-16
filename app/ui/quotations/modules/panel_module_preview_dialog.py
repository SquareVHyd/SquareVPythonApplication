from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QLabel, QScrollArea, QWidget
from PySide6.QtCore import Qt
from app.services.quotation_service import QuotationService

class PanelModulePreviewDialog(QDialog):
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
        panels = self.service.get_panels_by_quote(self.quote_id)
        if not panels:
            self.preview_text_edit.setHtml("<i>No panels found for this quotation.</i>")
            return
        for panel in panels:
            panel_id, panel_name, panel_category, panel_serial = panel[0], panel[4], panel[2], panel[3]
            preview_content.append(f"<h3 style='color:#0056b3;'>Panel: {panel_name} (ID: {panel_id})</h3>")
            preview_content.append(f"<ul><li><b>Category:</b> {panel_category}</li><li><b>Serial:</b> {panel_serial}</li><li><b>Quantity:</b> {panel[5]}</li><li><b>Dimensions:</b> {panel[6]}x{panel[7]}x{panel[8]} mm</li></ul>")
            modules = self.service.get_panel_modules_by_panel_id(panel_id)
            if modules:
                preview_content.append(f"<h4 style='color:#007bff;'>Modules for Panel {panel_name}:</h4>")
                preview_content.append("<table border='1' style='width:100%; border-collapse: collapse;'><tr style='background-color:#e9ecef;'>")
                preview_content.append("<th>In/Out</th><th>Qty</th><th>Module Type</th><th>Pole</th><th>KA</th><th>Remark</th></tr>")
                for module in modules:
                    ing_og, qty, module_type, pole, ka, remark = module[4], module[5], module[7], module[8], module[9], module[12]
                    preview_content.append(f"<tr><td>{ing_og}</td><td>{qty}</td><td>{module_type}</td><td>{pole}</td><td>{ka}</td><td>{remark}</td></tr>")
                preview_content.append("</table>")
            else:
                preview_content.append(f"<p><i>No modules found for Panel {panel_name}.</i></p>")
            preview_content.append("<hr style='border-top: 1px dashed #ccc;'>")
        self.preview_text_edit.setHtml("".join(preview_content))