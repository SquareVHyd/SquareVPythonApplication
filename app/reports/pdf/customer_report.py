from app.reports.pdf.report_base import ReportBase


class CustomerReport(ReportBase):
    def generate(self):
        self.build(
            "Customer Report",
            "Customer report generated successfully"
        )