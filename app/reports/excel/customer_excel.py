from openpyxl import Workbook


def export_customers(data, filename):
    wb = Workbook()
    ws = wb.active

    ws.append(["ID", "Customer", "Phone"])

    for row in data:
        ws.append(row)

    wb.save(filename)