from app.repositories.test_report_repository import TestReportRepository


class TestReportService:
    def __init__(self):
        self.repository = TestReportRepository()

    def get_or_create_report(self, panel_id):
        """Fetch existing test report for a panel or create empty ones if not exists."""
        return self.repository.get_or_create_report(panel_id)

    def save_report(self, panel_id, inspection_data, general_data, ir_data):
        """Update test report data."""
        return self.repository.save_report(panel_id, inspection_data, general_data, ir_data)

    def get_header_details(self, quote_id):
        """Get customer and quotation details for the report header."""
        from sqlalchemy import text
        from app.config.database import get_session
        
        query = text('''
            SELECT 
                q."QuoteRereceNo" as "CustomerPONo",
                c."CustomerName",
                c."CustomerAddress" as "FullAddress",
                q."QuoteProjectName",
                q."Date_Quote"
            FROM public."tbl_QuoteMain" q
            LEFT JOIN public."tblCustomers" c ON q."CustomerId" = c."ID"
            WHERE q."ID" = :quote_id
        ''')
        with get_session() as session:
            res = session.execute(query, {"quote_id": quote_id}).fetchone()
            if not res:
                return {}
            keys = session.execute(query, {"quote_id": quote_id}).keys()
            return dict(zip(keys, res))
