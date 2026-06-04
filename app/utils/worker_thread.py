"""
Worker Thread - Handles long-running operations without freezing UI
"""

from PySide6.QtCore import QThread, Signal


class Worker(QThread):
    """Worker thread for running blocking operations."""
    
    finished = Signal()
    error = Signal(str)
    result = Signal(object)
    
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.finished.connect(self.deleteLater)
    
    def run(self):
        """Execute the function in the worker thread."""
        try:
            result = self.func(*self.args, **self.kwargs)
            self.result.emit(result)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()
