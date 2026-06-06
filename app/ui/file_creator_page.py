import os
import shutil
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, 
    QLabel, QGroupBox, QRadioButton, QFileDialog, QMessageBox,
    QFormLayout
)

class FileCreatorPage(QWidget):
    """PySide6 implementation of the Folder Replicator / File Creator tool."""
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        group = QGroupBox("Folder Replicator / File Creator")
        form = QFormLayout(group)
        
        # Source Folder Input
        src_layout = QHBoxLayout()
        self.ent_source = QLineEdit()
        self.btn_browse_src = QPushButton("📁 Browse")
        self.btn_browse_src.clicked.connect(self.browse_source)
        src_layout.addWidget(self.ent_source)
        src_layout.addWidget(self.btn_browse_src)
        form.addRow("Source Folder:", src_layout)
        
        # Destination Folder Input
        dst_layout = QHBoxLayout()
        self.ent_dest = QLineEdit()
        self.btn_browse_dst = QPushButton("📁 Browse")
        self.btn_browse_dst.clicked.connect(self.browse_dest)
        dst_layout.addWidget(self.ent_dest)
        dst_layout.addWidget(self.btn_browse_dst)
        form.addRow("Destination Folder:", dst_layout)
        
        # Copying Options
        self.radio_struct = QRadioButton("Structure Only")
        self.radio_full = QRadioButton("Structure + Files")
        self.radio_struct.setChecked(True)
        form.addRow("Copy Option:", self.radio_struct)
        form.addRow("", self.radio_full)
        
        layout.addWidget(group)
        
        # Execution Button
        self.btn_execute = QPushButton("⚡ Execute Copy")
        self.btn_execute.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        self.btn_execute.clicked.connect(self.execute_copy)
        layout.addWidget(self.btn_execute)
        
        layout.addStretch()

    def browse_source(self):
        path = QFileDialog.getExistingDirectory(self, "Select Source Folder")
        if path:
            self.ent_source.setText(path)

    def browse_dest(self):
        path = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if path:
            self.ent_dest.setText(path)

    def execute_copy(self):
        src = self.ent_source.text()
        dst = self.ent_dest.text()
        option = "Structure Only" if self.radio_struct.isChecked() else "Structure + Files"

        if not src or not dst:
            QMessageBox.warning(self, "Missing Input", "Please select both source and destination folders.")
            return

        confirm = QMessageBox.question(self, "Confirmation", 
                                     f"Are you sure you want to copy using option '{option}'?",
                                     QMessageBox.Yes | QMessageBox.No)
        
        if confirm == QMessageBox.Yes:
            try:
                if self.radio_struct.isChecked():
                    # Replicate only structure
                    for root, dirs, files in os.walk(src):
                        rel_path = os.path.relpath(root, src)
                        os.makedirs(os.path.join(dst, rel_path), exist_ok=True)
                else:
                    # Full copy
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                QMessageBox.information(self, "Success", "Folders recreated successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Something went wrong:\n{e}")