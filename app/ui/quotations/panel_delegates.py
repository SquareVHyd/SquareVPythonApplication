from PySide6.QtWidgets import QStyledItemDelegate, QComboBox
from PySide6.QtCore import Qt, QEvent, QTimer

class ComboBoxDelegate(QStyledItemDelegate):
    """
    A custom item delegate that provides a QComboBox editor for specific table columns.
    """
    def __init__(self, parent=None, items=None):
        super().__init__(parent)
        self._items = items if items is not None else []

    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.addItems(self._items)
        # Automatically open the dropdown list when the editor is created
        QTimer.singleShot(0, editor.showPopup)
        editor.installEventFilter(self) # Needed for handling Enter key in QComboBox
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        if value in self._items:
            editor.setCurrentText(value)
        else:
            editor.setCurrentIndex(0) # Default to first item or empty

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def eventFilter(self, editor, event):
        # This is to ensure that pressing Enter in the QComboBox commits the data
        # and allows navigation to the next cell, similar to QLineEdit behavior.
        if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.commitData.emit(editor)
            self.closeEditor.emit(editor, QStyledItemDelegate.NoHint)
            return True
        return super().eventFilter(editor, event)