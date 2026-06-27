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

    def get_po_list(self):
        """Fetches all POs with basic customer details for dropdowns."""
        query = text("""
            SELECT po."ID", po."PO_No", po."PO_Date", q."CustomerName"
            FROM public."po_Customer" po
            LEFT JOIN public."tbl_QuoteMain" qm ON po."Quotation_ID" = qm."ID"
            LEFT JOIN public."tblCustomers" q ON qm."CustomerId" = q."ID"
            ORDER BY po."ID" DESC
        """)
        with get_session() as session:
            try:
                result = session.execute(query)
                return [dict(row._mapping) for row in result.fetchall()]
            except Exception as e:
                print(f"Error fetching PO list: {e}")
                return []

    def get_pos_for_quotation(self, quote_id):
        """Fetches POs related to a specific quotation."""
        query = text("""
            SELECT po."ID", po."PO_No", po."PO_Date", q."CustomerName"
            FROM public."po_Customer" po
            LEFT JOIN public."tbl_QuoteMain" qm ON po."Quotation_ID" = qm."ID"
            LEFT JOIN public."tblCustomers" q ON qm."CustomerId" = q."ID"
            WHERE po."Quotation_ID" = :quote_id
            ORDER BY po."ID" DESC
        """)
        with get_session() as session:
            try:
                result = session.execute(query, {"quote_id": quote_id})
                return [dict(row._mapping) for row in result.fetchall()]
            except Exception as e:
                print(f"Error fetching PO list for quote: {e}")
                return []

    def get_panels_for_po(self, po_id):
        """Fetches panel names associated with the quotation linked to the given PO."""
        query = text("""
            SELECT p."PanelName"
            FROM public."tbl_Panels" p
            JOIN public."po_Customer" po ON p."QuoteID" = po."Quotation_ID"
            WHERE po."ID" = :po_id
        """)
        with get_session() as session:
            try:
                result = session.execute(query, {"po_id": po_id})
                return [row[0] for row in result.fetchall()]
            except Exception as e:
                print(f"Error fetching panels for PO: {e}")
                return []

    def get_all_moms(self, quote_id=None):
        """Fetches all MOMs joined with PO and Quote details. Optionally filter by quotation."""
        base_query = """
            SELECT
                mom."ID",
                po."PO_No",
                po."PO_Date",
                c."CustomerName" AS "Customer_Name",
                mom."Customer_Representative",
                mom."SQV_Representatives",
                mom."Panel_Name",
                mom."Remarks",
                mom."General_Remark",
                mom."Date_Dispatch",
                mom."PO_ID"
            FROM public."Minutes_of_Meeting" mom
            JOIN public."po_Customer" po ON mom."PO_ID" = po."ID"
            LEFT JOIN public."tbl_QuoteMain" qm ON po."Quotation_ID" = qm."ID"
            LEFT JOIN public."tblCustomers" c ON qm."CustomerId" = c."ID"
        """
        if quote_id:
            base_query += " WHERE po.\"Quotation_ID\" = :quote_id"
        base_query += " ORDER BY mom.\"ID\" DESC"
        
        query = text(base_query)
        with get_session() as session:
            try:
                params = {"quote_id": quote_id} if quote_id else {}
                result = session.execute(query, params)
                return [dict(row._mapping) for row in result.fetchall()]
            except Exception as e:
                print(f"Error fetching MOMs: {e}")
                return []

    def create_mom(self, data):
        """Inserts a new MOM record."""
        query = text("""
            INSERT INTO public."Minutes_of_Meeting" 
            ("PO_ID", "Date_Dispatch", "Customer_Representative", "SQV_Representatives", "Panel_Name", "Remarks", "General_Remark")
            VALUES 
            (:po_id, :date_dispatch, :cust_rep, :sqv_rep, :panel_name, :remarks, :gen_remark)
        """)
        with get_session() as session:
            try:
                session.execute(query, {
                    "po_id": data.get("po_id"),
                    "date_dispatch": data.get("date_dispatch"),
                    "cust_rep": data.get("cust_rep"),
                    "sqv_rep": data.get("sqv_rep"),
                    "panel_name": data.get("panel_name"),
                    "remarks": data.get("remarks"),
                    "gen_remark": data.get("gen_remark")
                })
                session.commit()
                return True
            except Exception as e:
                print(f"Error creating MOM: {e}")
                session.rollback()
                return False

    def update_mom(self, mom_id, data):
        """Updates an existing MOM record."""
        query = text("""
            UPDATE public."Minutes_of_Meeting"
            SET "PO_ID" = :po_id,
                "Date_Dispatch" = :date_dispatch,
                "Customer_Representative" = :cust_rep,
                "SQV_Representatives" = :sqv_rep,
                "Panel_Name" = :panel_name,
                "Remarks" = :remarks,
                "General_Remark" = :gen_remark
            WHERE "ID" = :mom_id
        """)
        with get_session() as session:
            try:
                session.execute(query, {
                    "mom_id": mom_id,
                    "po_id": data.get("po_id"),
                    "date_dispatch": data.get("date_dispatch"),
                    "cust_rep": data.get("cust_rep"),
                    "sqv_rep": data.get("sqv_rep"),
                    "panel_name": data.get("panel_name"),
                    "remarks": data.get("remarks"),
                    "gen_remark": data.get("gen_remark")
                })
                session.commit()
                return True
            except Exception as e:
                print(f"Error updating MOM: {e}")
                session.rollback()
                return False

    def delete_mom(self, mom_id):
        """Deletes an MOM record."""
        query = text("""
            DELETE FROM public."Minutes_of_Meeting"
            WHERE "ID" = :mom_id
        """)
        with get_session() as session:
            try:
                session.execute(query, {"mom_id": mom_id})
                session.commit()
                return True
            except Exception as e:
                print(f"Error deleting MOM: {e}")
                session.rollback()
                return False

    def get_all_complaints(self, quote_id=None):
        """Fetches all complaints joined with PO details. Optionally filter by quotation."""
        base_query = """
            SELECT
                comp."ID",
                comp."PO_ID",
                comp."Complaint_Date",
                comp."Panel_Name",
                comp."Site",
                comp."Customer_Name",
                comp."Complaint_Type",
                comp."Complaint_Description",
                comp."Warranty",
                comp."Attended_By",
                comp."Feedback",
                comp."Charged_Amount",
                comp."status",
                po."PO_No",
                po."PO_Date"
            FROM public."Complaint" comp
            JOIN public."po_Customer" po ON comp."PO_ID" = po."ID"
        """
        if quote_id:
            base_query += " WHERE po.\"Quotation_ID\" = :quote_id"
        base_query += " ORDER BY comp.\"ID\" DESC"
        
        query = text(base_query)
        with get_session() as session:
            try:
                params = {"quote_id": quote_id} if quote_id else {}
                result = session.execute(query, params)
                return [dict(row._mapping) for row in result.fetchall()]
            except Exception as e:
                print(f"Error fetching complaints: {e}")
                return []

    def create_complaint(self, data):
        """Inserts a new Complaint record."""
        query = text("""
            INSERT INTO public."Complaint" 
            ("PO_ID", "Complaint_Date", "Panel_Name", "Site", "Customer_Name", "Complaint_Type", "Complaint_Description", "Warranty", "Attended_By", "Feedback", "Charged_Amount", "status")
            VALUES 
            (:po_id, :comp_date, :panel_name, :site, :cust_name, :comp_type, :comp_desc, :warranty, :attended_by, :feedback, :charged_amount, :status)
        """)
        with get_session() as session:
            try:
                session.execute(query, {
                    "po_id": data.get("po_id"),
                    "comp_date": data.get("comp_date"),
                    "panel_name": data.get("panel_name"),
                    "site": data.get("site"),
                    "cust_name": data.get("cust_name"),
                    "comp_type": data.get("comp_type"),
                    "comp_desc": data.get("comp_desc"),
                    "warranty": data.get("warranty", ""),
                    "attended_by": data.get("attended_by"),
                    "feedback": data.get("feedback"),
                    "charged_amount": data.get("charged_amount", 0.0),
                    "status": data.get("status", "pending")
                })
                session.commit()
                return True
            except Exception as e:
                print(f"Error creating complaint: {e}")
                session.rollback()
                return False

    def update_complaint(self, comp_id, data):
        """Updates an existing Complaint record."""
        query = text("""
            UPDATE public."Complaint"
            SET "PO_ID" = :po_id,
                "Complaint_Date" = :comp_date,
                "Panel_Name" = :panel_name,
                "Site" = :site,
                "Customer_Name" = :cust_name,
                "Complaint_Type" = :comp_type,
                "Complaint_Description" = :comp_desc,
                "Warranty" = :warranty,
                "Attended_By" = :attended_by,
                "Feedback" = :feedback,
                "Charged_Amount" = :charged_amount,
                "status" = :status
            WHERE "ID" = :comp_id
        """)
        with get_session() as session:
            try:
                session.execute(query, {
                    "comp_id": comp_id,
                    "po_id": data.get("po_id"),
                    "comp_date": data.get("comp_date"),
                    "panel_name": data.get("panel_name"),
                    "site": data.get("site"),
                    "cust_name": data.get("cust_name"),
                    "comp_type": data.get("comp_type"),
                    "comp_desc": data.get("comp_desc"),
                    "warranty": data.get("warranty", ""),
                    "attended_by": data.get("attended_by"),
                    "feedback": data.get("feedback"),
                    "charged_amount": data.get("charged_amount", 0.0),
                    "status": data.get("status", "pending")
                })
                session.commit()
                return True
            except Exception as e:
                print(f"Error updating complaint: {e}")
                session.rollback()
                return False

    def delete_complaint(self, comp_id):
        """Deletes a Complaint record."""
        query = text("""
            DELETE FROM public."Complaint"
            WHERE "ID" = :comp_id
        """)
        with get_session() as session:
            try:
                session.execute(query, {"comp_id": comp_id})
                session.commit()
                return True
            except Exception as e:
                print(f"Error deleting complaint: {e}")
                session.rollback()
                return False

    def get_quotation_project_names(self):
        """Fetches a list of unique CustomerName - ProjectName from quotations."""
        query = text("""
            SELECT DISTINCT c."CustomerName" || ' - ' || q."QuoteProjectName" AS project_info
            FROM public."tbl_QuoteMain" q
            LEFT JOIN public."tblCustomers" c ON q."CustomerId" = c."ID"
            WHERE c."CustomerName" IS NOT NULL AND q."QuoteProjectName" IS NOT NULL
            ORDER BY project_info
        """)
        with get_session() as session:
            try:
                result = session.execute(query)
                return [row[0] for row in result.fetchall() if row[0]]
            except Exception as e:
                print(f"Error fetching project names: {e}")
                return []

    def get_all_contract_bills(self):
        query = text("""
            SELECT "Bill_No", "Bill_Date", "Contractor_Name", "Type_Of_Job", "Amount", "Project_Name", "PO_ID", "PO_No"
            FROM public."Contract_Bills"
            ORDER BY "Bill_No" ASC
        """)
        with get_session() as session:
            try:
                result = session.execute(query)
                return [dict(zip(result.keys(), row)) for row in result.fetchall()]
            except Exception as e:
                print(f"Error fetching contract bills: {e}")
                return []

    def add_contract_bill(self, data):
        query = text("""
            INSERT INTO public."Contract_Bills" 
            ("Bill_Date", "Contractor_Name", "Type_Of_Job", "Amount", "Project_Name", "PO_ID", "PO_No")
            VALUES (:bill_date, :contractor, :job_type, :amount, :project_name, :po_id, :po_no)
            RETURNING "Bill_No"
        """)
        with get_session() as session:
            try:
                result = session.execute(query, data)
                session.commit()
                return result.scalar()
            except Exception as e:
                print(f"Error adding contract bill: {e}")
                session.rollback()
                return None

    def update_contract_bill(self, bill_no, data):
        query = text("""
            UPDATE public."Contract_Bills"
            SET "Bill_Date" = :bill_date,
                "Contractor_Name" = :contractor,
                "Type_Of_Job" = :job_type,
                "Amount" = :amount,
                "Project_Name" = :project_name,
                "PO_ID" = :po_id,
                "PO_No" = :po_no
            WHERE "Bill_No" = :bill_no
        """)
        data["bill_no"] = bill_no
        with get_session() as session:
            try:
                session.execute(query, data)
                session.commit()
                return True
            except Exception as e:
                print(f"Error updating contract bill: {e}")
                session.rollback()
                return False

    def delete_contract_bill(self, bill_no):
        query = text("""
            DELETE FROM public."Contract_Bills"
            WHERE "Bill_No" = :bill_no
        """)
        with get_session() as session:
            try:
                session.execute(query, {"bill_no": bill_no})
                session.commit()
                return True
            except Exception as e:
                print(f"Error deleting contract bill: {e}")
                session.rollback()
                return False
