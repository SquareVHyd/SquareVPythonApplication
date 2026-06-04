from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QFrame,
    QApplication,
)

from PySide6.QtCore import Qt

from app.services.auth_service import AuthService
from app.ui.main_window import MainWindow
from app.ui.auth.register_window import RegisterWindow


class LoginWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.auth_service = AuthService()

        self.setup_ui()

    def setup_ui(self):

        self.setWindowTitle("Enterprise ERP Login")

        self.resize(450, 400)

        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                font-size: 14px;
            }

            QFrame {
                background: white;
                border-radius: 10px;
            }

            QLabel {
                color: #333333;
            }

            QLineEdit {
                padding: 10px;
                border: 1px solid #cccccc;
                border-radius: 5px;
                background: white;
            }

            QPushButton {
                background-color: #1976d2;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #1565c0;
            }

            #registerBtn {
                background-color: #757575;
            }

            #registerBtn:hover {
                background-color: #616161;
            }
        """)

        main_layout = QVBoxLayout(self)

        main_layout.setAlignment(Qt.AlignCenter)

        frame = QFrame()

        frame.setFixedWidth(350)

        frame_layout = QVBoxLayout(frame)

        frame_layout.setSpacing(15)

        title = QLabel("Enterprise ERP")

        title.setAlignment(Qt.AlignCenter)

        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
        """)

        subtitle = QLabel("Login to Continue")

        subtitle.setAlignment(Qt.AlignCenter)

        subtitle.setStyleSheet("""
            color: gray;
            font-size: 14px;
        """)

        self.username_input = QLineEdit()

        self.username_input.setPlaceholderText("Username")

        self.password_input = QLineEdit()

        self.password_input.setPlaceholderText("Password")

        self.password_input.setEchoMode(QLineEdit.Password)

        # Buttons layout
        button_layout = QHBoxLayout()

        self.login_button = QPushButton("LOGIN")

        self.login_button.clicked.connect(self.login)

        self.register_button = QPushButton("NEW USER?")

        self.register_button.setObjectName("registerBtn")

        self.register_button.clicked.connect(self.open_register)

        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.register_button)

        frame_layout.addWidget(title)
        frame_layout.addWidget(subtitle)
        frame_layout.addWidget(QLabel(""))
        frame_layout.addWidget(QLabel("Username:"))
        frame_layout.addWidget(self.username_input)
        frame_layout.addWidget(QLabel("Password:"))
        frame_layout.addWidget(self.password_input)
        frame_layout.addWidget(QLabel(""))
        frame_layout.addLayout(button_layout)

        main_layout.addWidget(frame)

    def login(self):

        username = self.username_input.text().strip()

        password = self.password_input.text().strip()

        if not username:
            QMessageBox.warning(
                self,
                "Validation",
                "Username required"
            )
            return

        if not password:
            QMessageBox.warning(
                self,
                "Validation",
                "Password required"
            )
            return

        valid = self.auth_service.login(
            username,
            password
        )

        if valid:

            self.main_window = MainWindow()

            self.main_window.show()

            self.close()

        else:

            QMessageBox.critical(
                self,
                "Login Failed",
                "Invalid username or password"
            )

            self.password_input.clear()

    def open_register(self):
        """Open the registration window."""
        self.register_window = RegisterWindow(self)
        self.register_window.show()