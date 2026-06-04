from PySide6.QtWidgets import QWidget
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QLineEdit
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QTableWidgetItem

from app.ui.searchable_table import SearchableTable


class BaseCrudPage(QWidget):
    def __init__(self, service, title):
        super().__init__()

        self.service = service

        self.layout = QVBoxLayout(self)

        self.top_bar = QHBoxLayout()

        self.title = QLabel(title)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search...")

        self.refresh_btn = QPushButton("Refresh")
        self.add_btn = QPushButton("Add")
        self.edit_btn = QPushButton("Edit")
        self.delete_btn = QPushButton("Delete")
        self.export_btn = QPushButton("Excel")

        self.top_bar.addWidget(self.title)
        self.top_bar.addWidget(self.search_box)
        self.top_bar.addWidget(self.refresh_btn)
        self.top_bar.addWidget(self.add_btn)
        self.top_bar.addWidget(self.edit_btn)
        self.top_bar.addWidget(self.delete_btn)
        self.top_bar.addWidget(self.export_btn)

        self.layout.addLayout(self.top_bar)

        self.table = SearchableTabl