from app.config.database import get_session
from sqlalchemy import text

class SldAnalyzerService:
    def get_all_quotations(self):
        """Fetches all quotations for selection."""
        query = text("""
                SELECT q."ID", q."QuoteRereceNo", q."QuoteProjectName",
                       c."CustomerName"
                FROM public."tbl_QuoteMain" q
                LEFT JOIN public."tblCustomers" c ON q."CustomerId" = c."ID"
                ORDER BY q."ID" DESC
        """)
        with get_session() as session:
            try:
                result = session.execute(query)
                return [tuple(row) for row in result.fetchall()]
            except Exception as e:
                print(f"Error fetching quotations: {e}")
                return []

    def get_panels_for_quotation(self, quote_id):
        """Fetches panels with their physical dimensions for SLD generation."""
        query = text("""
                SELECT "ID", "PanelName", "PanelQty",
                       "LengthXmm", "HeightYmm", "DepthZmm", "StandRequired"
                FROM public."tbl_Panels" 
                WHERE "QuoteID" = :quote_id 
                ORDER BY "ID"
        """)
        with get_session() as session:
            try:
                result = session.execute(query, {"quote_id": quote_id})
                return [tuple(row) for row in result.fetchall()]
            except Exception as e:
                print(f"Error fetching panels for SLD: {e}")
                return []

    def get_panel_modules(self, panel_id):
        """Fetches modules for a given panel."""
        query = text("""
                SELECT pm."IngOg" as "DriveDescription", pm."PanelModQty", pm."IngOg", pm."Protection"
                FROM public."tbl_PanelModules" pm
                WHERE pm."PanelID" = :panel_id
                ORDER BY pm."ID"
        """)
        with get_session() as session:
            try:
                result = session.execute(query, {"panel_id": panel_id})
                return [tuple(row) for row in result.fetchall()]
            except Exception as e:
                print(f"Error fetching modules for panel: {e}")
                return []
