from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus import Paragraph
from reportlab.platypus import Spacer
from reportlab.lib.styles import getSampleStyleSheet


class ReportBase:
    def __init__(self, filename):
        self.filename = filename
        self.styles = getSampleStyleSheet()

    def build(self, title, text_content):
        document = SimpleDocTemplate(self.filename)

        elements = []

        elements.append(
            Paragraph(title, self.styles["Title"])
        )

        elements.append(Spacer(1, 20))

        elements.append(
            Paragraph(text_content, self.styles["BodyText"])
        )

        document.build(elements)