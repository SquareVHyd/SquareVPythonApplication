import os
import tempfile
import fitz  # PyMuPDF
from docx2pdf import convert

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSplitter, 
    QTreeView, QFileSystemModel, QLabel, QTextEdit, QScrollArea,
    QFileDialog, QMessageBox, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage

DEFAULT_START_FOLDER = r"G:\My Drive\SVEE2\01 CompanyDocs\10 ZED"

class FileViewerPage(QWidget):
    """PySide6 implementation of the File Explorer & Previewer tool."""
    def __init__(self):
        super().__init__()
        self.current_folder = ""
        self.current_selected_file = "" 
        self.setup_ui()
        self.load_initial_folder(DEFAULT_START_FOLDER)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10) 
        
        # --- Top Toolbar ---
        toolbar_layout = QHBoxLayout()
        
        self.btn_select_folder = QPushButton("📁 Select Folder")
        self.btn_select_folder.clicked.connect(self.select_folder)
        
        self.btn_open_explorer = QPushButton("📂 Open Folder in Explorer")
        self.btn_open_explorer.clicked.connect(self.open_in_explorer)
        self.btn_open_explorer.setEnabled(False)

        self.btn_open_file = QPushButton("📄 Open Selected File")
        self.btn_open_file.clicked.connect(self.open_selected_file)
        self.btn_open_file.setEnabled(False)
        
        self.btn_export_pdf = QPushButton("📄 Save as PDF...")
        self.btn_export_pdf.clicked.connect(self.export_to_pdf_dialog)
        self.btn_export_pdf.setEnabled(False)
        self.btn_export_pdf.setStyleSheet("font-weight: bold; color: #107c41;") 
        
        self.lbl_current_path = QLabel("No folder selected.")
        self.lbl_current_path.setStyleSheet("color: gray;")
        
        toolbar_layout.addWidget(self.btn_select_folder)
        toolbar_layout.addWidget(self.btn_open_explorer)
        toolbar_layout.addWidget(self.btn_open_file)
        toolbar_layout.addWidget(self.btn_export_pdf)
        toolbar_layout.addWidget(self.lbl_current_path)
        toolbar_layout.addStretch() 
        
        main_layout.addLayout(toolbar_layout)
        
        # --- Adjustable Splitter ---
        self.splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.splitter, 1) 
        
        # 1. Left Side: File Tree
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath("")
        
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.file_model)
        self.tree_view.clicked.connect(self.on_file_clicked)
        self.tree_view.setColumnHidden(1, True)
        self.tree_view.setColumnHidden(2, True)
        self.tree_view.setColumnHidden(3, True)
        
        self.splitter.addWidget(self.tree_view)
        
        # 2. Right Side: Preview Pane
        self.preview_container = QWidget()
        self.preview_layout = QVBoxLayout(self.preview_container)
        self.preview_layout.setContentsMargins(0, 0, 0, 0)
        
        # --- Viewer Widgets ---
        self.text_viewer = QTextEdit()
        self.text_viewer.setReadOnly(True)
        self.text_viewer.hide()
        
        self.pdf_scroll_area = QScrollArea()
        self.pdf_scroll_area.setWidgetResizable(True)
        self.pdf_content_widget = QWidget()
        self.pdf_content_layout = QVBoxLayout(self.pdf_content_widget)
        self.pdf_scroll_area.setWidget(self.pdf_content_widget)
        self.pdf_scroll_area.hide()
        
        self.image_viewer = QLabel()
        self.image_viewer.setAlignment(Qt.AlignCenter)
        self.image_viewer.hide()
        
        self.lbl_status = QLabel("Select a file to preview.")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        
        self.preview_layout.addWidget(self.text_viewer)
        self.preview_layout.addWidget(self.pdf_scroll_area)
        self.preview_layout.addWidget(self.image_viewer)
        self.preview_layout.addWidget(self.lbl_status)
        
        self.splitter.addWidget(self.preview_container)
        self.splitter.setSizes([380, 820])

    def load_initial_folder(self, folder_path):
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            self.current_folder = folder_path
            self.lbl_current_path.setText(f"Path: {folder_path}")
            self.btn_open_explorer.setEnabled(True)
            self.tree_view.setRootIndex(self.file_model.index(folder_path))
        else:
            self.lbl_current_path.setText(f"Default path not found. Please click 'Select Folder'.")

    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if folder_path:
            self.load_initial_folder(folder_path)

    def open_in_explorer(self):
        if self.current_folder and os.path.exists(self.current_folder):
            os.startfile(self.current_folder)

    def open_selected_file(self):
        if self.current_selected_file and os.path.exists(self.current_selected_file):
            try:
                os.startfile(self.current_selected_file)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not open file:\n{str(e)}")

    def on_file_clicked(self, index):
        file_path = self.file_model.filePath(index)
        if os.path.isdir(file_path):
            self.current_selected_file = ""
            self.btn_open_file.setEnabled(False)
            self.btn_export_pdf.setEnabled(False)
            return  
        self.current_selected_file = file_path
        self.btn_open_file.setEnabled(True)
        ext = os.path.splitext(file_path)[1].lower()
        self.btn_export_pdf.setEnabled(ext in ['.docx', '.doc'])
        self.preview_file(file_path)

    def reset_preview(self):
        self.text_viewer.hide(); self.pdf_scroll_area.hide(); self.image_viewer.hide()
        self.image_viewer.clear(); self.lbl_status.show(); self.lbl_status.setText("Loading preview...")
        for i in reversed(range(self.pdf_content_layout.count())):
            widget = self.pdf_content_layout.itemAt(i).widget()
            if widget: widget.setParent(None)
        QApplication.processEvents()

    def preview_file(self, file_path):
        self.reset_preview()
        ext = os.path.splitext(file_path)[1].lower()
        try:
            if ext == '.pdf': self.show_pdf(file_path)
            elif ext in ['.docx', '.doc']: self.show_docx_as_pdf_preview(file_path)
            elif ext in ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp']: self.show_image(file_path)
            else: self.show_text(file_path)
        except Exception as e: self.lbl_status.setText(f"Error loading preview:\n{str(e)}")

    def show_docx_as_pdf_preview(self, file_path):
        self.lbl_status.setText("Rendering Word Document layout... Please wait.")
        QApplication.processEvents()
        temp_pdf = os.path.join(tempfile.gettempdir(), "temp_preview_document.pdf")
        try:
            convert(file_path, temp_pdf); self.show_pdf(temp_pdf)
        except Exception as e:
            self.lbl_status.setText(f"Preview conversion failed.\nEnsure MS Word is installed.\nError: {str(e)}")

    def export_to_pdf_dialog(self):
        if not self.current_selected_file: return
        input_filename = os.path.basename(self.current_selected_file)
        default_path = os.path.join(os.path.dirname(self.current_selected_file), os.path.splitext(input_filename)[0] + ".pdf")
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Converted PDF As", default_path, "PDF Files (*.pdf)")
        if save_path:
            self.lbl_status.show(); self.lbl_status.setText(f"Converting document to PDF...\nSaving to: {save_path}")
            QApplication.processEvents()
            try:
                convert(self.current_selected_file, save_path)
                QMessageBox.information(self, "Success", f"File converted successfully!\nSaved to:\n{save_path}")
                self.lbl_status.setText("Conversion complete.")
            except Exception as e:
                QMessageBox.critical(self, "Conversion Failed", f"An error occurred during conversion:\n{str(e)}")
                self.lbl_status.setText("Conversion failed.")

    def show_image(self, file_path):
        try:
            pixmap = QPixmap(file_path)
            if pixmap.isNull(): self.lbl_status.setText("Could not load image."); return
            scaled_pixmap = pixmap.scaled(self.preview_container.width() - 20, self.preview_container.height() - 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_viewer.setPixmap(scaled_pixmap); self.lbl_status.hide(); self.image_viewer.show()
        except Exception as e: self.lbl_status.setText(f"Failed to load image:\n{str(e)}")

    def show_text(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f: content = f.read(50000) 
            self.text_viewer.setPlainText(content); self.lbl_status.hide(); self.text_viewer.show()
        except UnicodeDecodeError: self.lbl_status.setText("Binary file or complex format.\nPreview not available.")

    def show_pdf(self, file_path):
        try:
            doc = fitz.open(file_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num); pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
                img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
                label = QLabel(); label.setPixmap(QPixmap.fromImage(img)); label.setAlignment(Qt.AlignCenter)
                self.pdf_content_layout.addWidget(label)
            self.lbl_status.hide(); self.pdf_scroll_area.show()
        except Exception as e: self.lbl_status.setText(f"Failed to read PDF:\n{str(e)}")