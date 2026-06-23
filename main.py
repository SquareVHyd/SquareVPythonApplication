import sys

from PySide6.QtWidgets import QApplication

from app.ui.auth.login_window import LoginWindow
from app.ui.main_window import MainWindow


def main():

    app = QApplication(sys.argv)

    # window = LoginWindow()
    window = MainWindow()

    window.showMaximized()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()