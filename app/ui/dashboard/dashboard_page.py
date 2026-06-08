import os
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QGridLayout
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QPixmap


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

        header_layout = QHBoxLayout(header)

        # Logo
        logo_label = QLabel()
        logo_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "Images",
            "SQV_Header.png"
        )
        if os.path.exists(logo_path):
            logo_label.setPixmap(QPixmap(logo_path).scaledToHeight(80, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignCenter)

        # Text Content Container
        text_layout = QVBoxLayout()

        company_name = QLabel("SQUARE V ENGINEERING ENTERPRISES")
        company_name.setObjectName("companyName")
        company_name.setAlignment(Qt.AlignCenter)

        website = QLabel('Website: <a href="https://squarevengineering.com/" style="color: #dbe9ff;">https://squarevengineering.com/</a>')
        website.setObjectName("headerDetail")
        website.setAlignment(Qt.AlignCenter)
        website.setOpenExternalLinks(True)

        
        address = QLabel("Survey No:298/P, Road No 14, Pipe Line Road, Phase-I, IDA, Jeedimetla, Hyderabad - 500055, Telangana")
        address.setObjectName("headerDetail")
        address.setAlignment(Qt.AlignCenter)
        address.setWordWrap(True)

        gst_no = QLabel("GST Number: 36AFKFS1080B1Z7")
        gst_no.setObjectName("headerDetail")
        gst_no.setAlignment(Qt.AlignCenter)

        text_layout.addWidget(company_name)
        text_layout.addWidget(website)
        text_layout.addWidget(address)
        text_layout.addWidget(gst_no)

        header_layout.addWidget(logo_label)
        header_layout.addStretch() # Add stretch before text_layout to push it right
        header_layout.addLayout(text_layout)
        header_layout.addStretch() # Add stretch after text_layout to center it

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
            color: #ff0000;
            font-size: 24px;
            font-weight: bold;
        }

        
        #headerDetail {
            background: transparent;
            color: #dbe9ff;
            font-size: 11px;
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