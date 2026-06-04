from openpyxl import Workbook


class ExcelService:
    def export(self, headers, rows, filename):
        workbook = Workbook()
        worksheet = workbook.active

        worksheet.append(headers)

        for row in rows:
            worksheet.append(list(row))

        workbook.save(filename)