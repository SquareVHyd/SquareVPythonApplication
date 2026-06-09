from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QPushButton, QLabel, QScrollArea, QWidget
from PySide6.QtCore import Qt

class GenericCrudDialog(QDialog):
    """
    A generic dialog for adding or editing a database record.
    It dynamically creates QLineEdit fields based on provided column names.
    """
    def __init__(self, column_names, initial_data=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit/Add Record")
        self.setMinimumWidth(450)
        self.resize(500, 600)

        self.layout = QVBoxLayout(self)

        # Adding a Scroll Area to handle tables with many columns
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        container = QWidget()
        self.form_layout = QFormLayout(container)
        self.fields = {} # Stores QLineEdit widgets mapped by column name

        for col_name in column_names:
            line_edit = QLineEdit()
            if initial_data and col_name in initial_data:
                line_edit.setText(str(initial_data[col_name]))
            self.form_layout.addRow(f"{col_name}:", line_edit)
            self.fields[col_name] = line_edit
        
        scroll_area.setWidget(container)
        self.layout.addWidget(scroll_area)

        buttons_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("✖️ Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        self.layout.addLayout(buttons_layout)

    def get_data(self):
        """Returns a dictionary of column names to their current values from the form."""
        data = {}
        for col_name, line_edit in self.fields.items():
            data[col_name] = line_edit.text()
        return data