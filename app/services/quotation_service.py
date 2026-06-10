import pyodbc
from datetime import datetime

class QuotationService:
    def __init__(self):
        self.dsn = "PostgreSQL35W"

    def get_db_connection(self):
        try:
            return pyodbc.connect(f"DSN={self.dsn};")
        except Exception as e:
            print(f"Connection Error: {e}")
            return None

    def get_all_quotations(self):
        """Fetches quotations with joined customer and contact names."""
        conn = self.get_db_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            # Resolving IDs to names as requested
            query = """
                SELECT 
                    q."ID",
                    q."CustomerId", 
                    c."CustomerName", 
                    q."DateOfRequest", q."Date_Quote", q."QuoteRereceNo",
                    q."QuoteSubject", q."QuoteProjectName",
                    cc."CustomerContactName",
                    q."PreparedBy", q."QuoteStatus"
                FROM public."tbl_QuoteMain" q
                LEFT JOIN public."tblCustomers" c ON q."CustomerId" = c."ID"
                LEFT JOIN public."tblCustomerContacts" cc ON q."CustomerContactID" = cc."ID"
                ORDER BY q."ID" DESC
            """
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            print(f"Query Error: {e}")
            return []
        finally:
            conn.close()