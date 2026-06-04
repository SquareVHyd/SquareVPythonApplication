import re

from PySide6.QtWidgets import QTableWidget, QAbstractItemView, QTableWidgetItem, QHeaderView
from PySide6.QtGui import QFontMetrics
from PySide6.QtCore import Qt


class NumericTableWidgetItem(QTableWidgetItem):
    _numeric_re = re.compile(r"^-?\d+(?:\.\d+)?$")

    def __init__(self, value=""):
        text = "" if value is None else str(value)
        super().__init__(text)

    def __lt__(self, other):
        if isinstance(other, QTableWidgetItem):
            self_value = self._numeric_value(self.text())
            other_value = self._numeric_value(other.text())
            if self_value is not None and other_value is not None:
                return self_value < other_value
            if self_value is not None and other_value is None:
                return True
            if self_value is None and other_value is not None:
                return False
            return self.text() < other.text()
        return False

    @classmethod
    def _numeric_value(cls, text):
        if text is None:
            return None
        text = str(text).strip()
        if text == "":
            return None
        if cls._numeric_re.fullmatch(text):
            return float(text) if "." in text else int(text)
        return None


class SearchableTable(QTableWidget):
    def __init__(self):
        super().__init__()

        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setSectionsMovable(True)
        header.setStretchLastSection(True)
        header.setDefaultSectionSize(120)
        header.setMinimumSectionSize(80)
        header.setHighlightSections(False)

        self.setSortingEnabled(True)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setShowGrid(True)
        self.setStyleSheet(
            "QTableWidget { gridline-color: #e1e1e1; border: 1px solid #d9d9d9; }"
            "QHeaderView::section { background-color: #f7f7f7; padding: 6px; border: 1px solid #d9d9d9; }"
        )

    def fix_column_widths(self):
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)

        fm = QFontMetrics(self.font())
        for col in range(self.columnCount()):
            content_width = self.sizeHintForColumn(col)
            header_item = self.horizontalHeaderItem(col)
            header_width = fm.horizontalAdvance(header_item.text()) + 24 if header_item else 0
            width = max(content_width, header_width, 80)
            self.setColumnWidth(col, width)

    def get_table_data(self):
        headers = []
        for col in range(self.columnCount()):
            header = self.horizontalHeaderItem(col)
            headers.append(header.text() if header else "")

        rows = []
        for row in range(self.rowCount()):
            row_values = []
            for col in range(self.columnCount()):
                item = self.item(row, col)
                row_values.append(item.text() if item else "")
            rows.append(row_values)

        return headers, rows

    def to_html(self, title="Table Export"):
        headers, rows = self.get_table_data()
        html = [
            "<html><head><meta charset='utf-8'><style>",
            "table { border-collapse: collapse; width: 100%; }",
            "th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }",
            "th { background-color: #f4f4f4; }",
            "</style></head><body>",
            f"<h2>{title}</h2>",
            "<table>",
            "<thead><tr>",
        ]

        for header in headers:
            html.append(f"<th>{header}</th>")
        html.append("</tr></thead><tbody>")

        for row in rows:
            html.append("<tr>")
            for cell in row:
                html.append(f"<td>{cell}</td>")
            html.append("</tr>")

        html.append("</tbody></table></body></html>")
        return "".join(html)
