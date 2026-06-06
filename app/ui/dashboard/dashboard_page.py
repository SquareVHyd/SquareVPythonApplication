from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QGridLayout
)
from PySide6.QtCore import Qt, QDate


class DashboardPage(QWidget):

    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # ==================================================
        # HEADER
        # ==================================================

        header = QFrame()
        header.setObjectName("header")

        header_layout = QVBoxLayout(header)

        company_name = QLabel("SQUARE V ENGINEERING ENTERPRISES")
        company_name.setObjectName("companyName")
        company_name.setAlignment(Qt.AlignCenter)

        tagline = QLabel("Race For Quality Has No Finish Line")
        tagline.setObjectName("tagline")
        tagline.setAlignment(Qt.AlignCenter)

        header_layout.addWidget(company_name)
        header_layout.addWidget(tagline)

        # ==================================================
        # WELCOME CARD
        # ==================================================

        welcome_card = QFrame()
        welcome_card.setObjectName("card")

        welcome_layout = QVBoxLayout(welcome_card)

        welcome_title = QLabel("Welcome to Square V Engineering ERP")
        welcome_title.setObjectName("sectionTitle")
        welcome_title.setAlignment(Qt.AlignCenter)

        welcome_msg = QLabel(
            "Manage customers, price lists, modules, "
            "busbar materials and reports from a single platform."
        )
        welcome_msg.setWordWrap(True)
        welcome_msg.setAlignment(Qt.AlignCenter)

        welcome_layout.addWidget(welcome_title)
        welcome_layout.addWidget(welcome_msg)

        # ==================================================
        # INFORMATION GRID
        # ==================================================

        info_frame = QFrame()
        info_layout = QGridLayout(info_frame)

        info_layout.addWidget(
            self.create_info_card(
                "Company",
                "Square V Engineering"
            ),
            0, 0
        )

        info_layout.addWidget(
            self.create_info_card(
                "Industry",
                "Electrical Panels & Automation"
            ),
            0, 1
        )

        info_layout.addWidget(
            self.create_info_card(
                "ERP Version",
                "v1.0"
            ),
            1, 0
        )

        info_layout.addWidget(
            self.create_info_card(
                "Date",
                QDate.currentDate().toString("dd-MM-yyyy")
            ),
            1, 1
        )

        info_layout.addWidget(
            self.create_info_card(
                "Address",
                "Survey No:298/P, Road No 14, Pipe Line Road, Phase-I, IDA, Jeedimetla, Hyderabad - 500055, Telangana"
            ),
            2, 0
        )

        info_layout.addWidget(
            self.create_info_card(
                "GST Number",
                "36AFKFS1080B1Z7"
            ),
            2, 1
        )

        # ==================================================
        # ABOUT SECTION
        # ==================================================

        about_card = QFrame()
        about_card.setObjectName("card")

        about_layout = QVBoxLayout(about_card)

        about_title = QLabel("About Company")
        about_title.setObjectName("sectionTitle")

        about_text = QLabel(
            "Square V Engineering Enterprises specializes in "
            "Electrical Control Panels, PCC, MCC, APFC, PLC, "
            "VFD Panels and Industrial Automation Solutions."
        )

        about_text.setWordWrap(True)

        about_layout.addWidget(about_title)
        about_layout.addWidget(about_text)

        # ==================================================
        # ADD TO MAIN LAYOUT
        # ==================================================

        main_layout.addWidget(header)
        main_layout.addWidget(welcome_card)
        main_layout.addWidget(info_frame)
        main_layout.addWidget(about_card)
        main_layout.addStretch()

        # ==================================================
        # STYLES
        # ==================================================

        self.setStyleSheet("""
        QWidget {
            background-color: #f5f7fa;
            color: #222222;
        }

        QLabel {
            background: transparent;
            color: #222222;
        }

        #header {
            background-color: #003366;
            border-radius: 10px;
            padding: 15px;

        }

        #card {
            background-color: white;
            border: 1px solid #d9d9d9;
            border-radius: 10px;
            padding: 10px;
        }

        #companyName {
            background: transparent;
            color: white;
            font-size: 24px;
            font-weight: bold;
        }

        #tagline {
            background: transparent;
            color: #dbe9ff;
            font-size: 13px;
            font-weight: 500;
        }

        #sectionTitle {
            background: transparent;
            color: #003366;
            font-size: 16px;
            font-weight: bold;
        }
        """)

    def create_info_card(self, title, value):

        card = QFrame()
        card.setObjectName("card")

        layout = QVBoxLayout(card)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(
            "font-weight:bold;color:#003366;"
        )

        lbl_value = QLabel(value)
        lbl_value.setWordWrap(True)

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_value)

        return card