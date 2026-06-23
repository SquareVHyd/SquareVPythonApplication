from PySide6.QtWidgets import QStyledItemDelegate, QComboBox, QSpinBox, QDoubleSpinBox
from PySide6.QtCore import Qt, QEvent, QTimer

class ComboBoxDelegate(QStyledItemDelegate):
    """
    A custom item delegate that provides a QComboBox editor for specific table columns.
    """
    def __init__(self, parent=None, items=None, editable=False):
        super().__init__(parent)
        self._items = items if items is not None else []
        self._editable = editable

    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.setEditable(self._editable)
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
        val = editor.currentText().strip()
        # Update the underlying shared list if a new value is typed
        if self._editable and val and val not in self._items:
            self._items.append(val)
        model.setData(index, val, Qt.EditRole)

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

class SpinBoxDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, min_val=1, max_val=999999):
        super().__init__(parent)
        self.min_val = min_val
        self.max_val = max_val

    def createEditor(self, parent, option, index):
        editor = QSpinBox(parent)
        editor.setFrame(False)
        editor.setMinimum(self.min_val)
        editor.setMaximum(self.max_val)
        return editor

    def setEditorData(self, editor, index):
        val = index.model().data(index, Qt.EditRole)
        try: editor.setValue(int(float(str(val).strip() or self.min_val)))
        except: editor.setValue(self.min_val)

    def setModelData(self, editor, model, index):
        model.setData(index, str(editor.value()), Qt.EditRole)

class DoubleSpinBoxDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, min_val=1.0, max_val=9999999.0, decimals=2):
        super().__init__(parent)
        self.min_val = min_val
        self.max_val = max_val
        self.decimals = decimals

    def createEditor(self, parent, option, index):
        editor = QDoubleSpinBox(parent)
        editor.setFrame(False)
        editor.setMinimum(self.min_val)
        editor.setMaximum(self.max_val)
        editor.setDecimals(self.decimals)
        return editor

    def setEditorData(self, editor, index):
        val = index.model().data(index, Qt.EditRole)
        clean = str(val).replace('₹', '').replace(',', '').replace('%', '').strip()
        try: editor.setValue(float(clean or self.min_val))
        except: editor.setValue(self.min_val)

    def setModelData(self, editor, model, index):
        model.setData(index, str(round(editor.value(), self.decimals)), Qt.EditRole)