from datetime import datetime
from sqlalchemy import text
from app.config.database import get_session

class POProcessService:
    def __init__(self):
        pass

    def get_all_quotations(self):
        """Fetches the latest quotation for each family with joined customer and contact names."""
        query = text("""
                SELECT 
                    q."ID",
                    q."CustomerId", 
                    c."CustomerName", 
                    q."DateOfRequest", q."Date_Quote", q."QuoteRereceNo",
                    q."QuoteSubject", q."QuoteProjectName",
                    cc."CustomerContactName",
                    q."PreparedBy", q."QuoteStatus",
                    q."BaseQuoteID", q."RevisionNo"
                FROM public."tbl_QuoteMain" q
                LEFT JOIN public."tblCustomers" c ON q."CustomerId" = c."ID"
                LEFT JOIN public."tblCustomerContacts" cc ON q."CustomerContactID" = cc."ID"
                WHERE q."RevisionNo" = (
                    SELECT COALESCE(MAX("RevisionNo"), 0)
                    FROM public."tbl_QuoteMain" q2 
                    WHERE COALESCE(q2."BaseQuoteID", q2."ID") = COALESCE(q."BaseQuoteID", q."ID")
                )
                ORDER BY q."ID" DESC
        """)
        with get_session() as session:
            try:
                result = session.execute(query)
                # Convert to list of tuples for thread safety and predictable indexing in the UI
                return [tuple(row) for row in result.fetchall()]
            except Exception as e:
                print(f"Error fetching quotations in PO Process: {e}")
                return []

    def get_quotation_by_id(self, quote_id):
        """Fetches a single quotation record by its ID, including customer and contact names."""
        query = text("""
                SELECT 
                    q."ID", q."CustomerId", c."CustomerName", q."DateOfRequest", q."Date_Quote", 
                    q."QuoteRereceNo", q."QuoteSubject", q."QuoteProjectName",
                    cc."CustomerContactName", q."PreparedBy", q."QuoteStatus",
                    q."BaseQuoteID", q."RevisionNo"
                FROM public."tbl_QuoteMain" q
                LEFT JOIN public."tblCustomers" c ON q."CustomerId" = c."ID"
                LEFT JOIN public."tblCustomerContacts" cc ON q."CustomerContactID" = cc."ID"
                WHERE q."ID" = :quote_id
        """)
        with get_session() as session:
            try:
                result = session.execute(query, {"quote_id": quote_id})
                row = result.fetchone()
                return dict(row._mapping) if row else None
            except Exception as e:
                print(f"Error fetching quotation by ID in PO Process: {e}")
                return None
