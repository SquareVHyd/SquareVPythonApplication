from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus import Table


def generate_quotation_pdf(data, filename):
    doc = SimpleDocTemplate(filename)

    table = Table(data)

    doc.build([table])