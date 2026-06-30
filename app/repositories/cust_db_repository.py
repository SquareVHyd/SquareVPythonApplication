from sqlalchemy import text
from app.config.database import get_session


class CustDbRepository:
    """Repository for CRUD operations on public."tblCustomers" and public."tblCustomerContacts"."""

    # =====================================================================
    # tblCustomers
    # =====================================================================

    def get_all_customers(self):
        """Fetches all customers joined with tblState for state name display."""
        query = text("""
            SELECT
                c."ID",
                c."CustomerName",
                c."Mail",
                c."CustomerPhone",
                c."CustomerAddress",
                c."CustomerCity",
                COALESCE(s."StateName", '') AS "StateName",
                c."CustomerStateID",
                c."CustomerPIN",
                c."CustomerGSTNCode",
                c."CustomerNotes",
                c."Attachments",
                c."SysDateOfEntry"
            FROM public."tblCustomers" c
            LEFT JOIN public."tblState" s ON c."CustomerStateID" = s."ID"
            ORDER BY c."CustomerName"
        """)
        with get_session() as session:
            result = session.execute(query)
            return result.fetchall()

    def get_customer_by_id(self, customer_id):
        """Fetches a single customer by ID."""
        query = text("""
            SELECT
                c."ID",
                c."CustomerName",
                c."Mail",
                c."CustomerPhone",
                c."CustomerAddress",
                c."CustomerCity",
                COALESCE(s."StateName", '') AS "StateName",
                c."CustomerStateID",
                c."CustomerPIN",
                c."CustomerGSTNCode",
                c."CustomerNotes",
                c."Attachments",
                c."SysDateOfEntry"
            FROM public."tblCustomers" c
            LEFT JOIN public."tblState" s ON c."CustomerStateID" = s."ID"
            WHERE c."ID" = :customer_id
        """)
        with get_session() as session:
            result = session.execute(query, {"customer_id": customer_id})
            return result.fetchone()

    def create_customer(self, data: dict):
        """Inserts a new customer record. Returns the new ID."""
        query = text("""
            INSERT INTO public."tblCustomers" (
                "CustomerName", "Mail", "CustomerPhone",
                "CustomerAddress", "CustomerCity", "CustomerStateID",
                "CustomerPIN", "CustomerGSTNCode", "CustomerNotes", "Attachments"
            ) VALUES (
                :customer_name, :mail, :customer_phone,
                :customer_address, :customer_city, :customer_state_id,
                :customer_pin, :customer_gstn_code, :customer_notes, :attachments
            ) RETURNING "ID"
        """)
        with get_session() as session:
            result = session.execute(query, data)
            session.commit()
            return result.scalar()

    def update_customer(self, customer_id, data: dict):
        """Updates an existing customer record."""
        query = text("""
            UPDATE public."tblCustomers" SET
                "CustomerName"    = :customer_name,
                "Mail"            = :mail,
                "CustomerPhone"   = :customer_phone,
                "CustomerAddress" = :customer_address,
                "CustomerCity"    = :customer_city,
                "CustomerStateID" = :customer_state_id,
                "CustomerPIN"     = :customer_pin,
                "CustomerGSTNCode"= :customer_gstn_code,
                "CustomerNotes"   = :customer_notes,
                "Attachments"     = :attachments
            WHERE "ID" = :customer_id
        """)
        data["customer_id"] = customer_id
        with get_session() as session:
            session.execute(query, data)
            session.commit()

    def delete_customer(self, customer_id):
        """Deletes a customer record by ID."""
        query = text('DELETE FROM public."tblCustomers" WHERE "ID" = :customer_id')
        with get_session() as session:
            session.execute(query, {"customer_id": customer_id})
            session.commit()

    def get_all_states(self):
        """Returns list of (ID, StateName) tuples for the State dropdown."""
        query = text('SELECT "ID", "StateName" FROM public."tblState" ORDER BY "StateName"')
        with get_session() as session:
            result = session.execute(query)
            return result.fetchall()

    # =====================================================================
    # tblCustomerContacts
    # =====================================================================

    def get_contacts_by_customer(self, customer_id):
        """Returns all contacts for a given CustomerID."""
        query = text("""
            SELECT
                "ID",
                "CustomerID",
                "CustomerContactName",
                "CustomerContactTitle",
                "CustomerContactDesignation",
                "CustomerMobile1",
                "CustomerMobile2"
            FROM public."tblCustomerContacts"
            WHERE "CustomerID" = :customer_id
            ORDER BY "CustomerContactName"
        """)
        with get_session() as session:
            result = session.execute(query, {"customer_id": customer_id})
            return result.fetchall()

    def create_contact(self, data: dict):
        """Inserts a new contact record. Returns the new ID."""
        query = text("""
            INSERT INTO public."tblCustomerContacts" (
                "CustomerID", "CustomerContactName", "CustomerContactTitle",
                "CustomerContactDesignation", "CustomerMobile1", "CustomerMobile2"
            ) VALUES (
                :customer_id, :contact_name, :contact_title,
                :contact_designation, :mobile1, :mobile2
            ) RETURNING "ID"
        """)
        with get_session() as session:
            result = session.execute(query, data)
            session.commit()
            return result.scalar()

    def update_contact(self, contact_id, data: dict):
        """Updates an existing contact record."""
        query = text("""
            UPDATE public."tblCustomerContacts" SET
                "CustomerContactName"        = :contact_name,
                "CustomerContactTitle"       = :contact_title,
                "CustomerContactDesignation" = :contact_designation,
                "CustomerMobile1"            = :mobile1,
                "CustomerMobile2"            = :mobile2
            WHERE "ID" = :contact_id
        """)
        data["contact_id"] = contact_id
        with get_session() as session:
            session.execute(query, data)
            session.commit()

    def delete_contact(self, contact_id):
        """Deletes a contact record by ID."""
        query = text('DELETE FROM public."tblCustomerContacts" WHERE "ID" = :contact_id')
        with get_session() as session:
            session.execute(query, {"contact_id": contact_id})
            session.commit()

    # =====================================================================
    # tblCustomerFollowup
    # =====================================================================

    def get_followups_by_contact(self, contact_id):
        """Returns all follow-up records for a given ContactID, newest first."""
        query = text("""
            SELECT
                "ID",
                "ContactID",
                "DateOfFollowup",
                "ModeOfContact",
                "WhatDiscussed",
                "SysDateOfEntry"
            FROM public."tblCustomerFollowup"
            WHERE "ContactID" = :contact_id
            ORDER BY "DateOfFollowup" DESC
        """)
        with get_session() as session:
            result = session.execute(query, {"contact_id": contact_id})
            return result.fetchall()

    def create_followup(self, data: dict):
        """Inserts a new follow-up record. Returns the new ID."""
        query = text("""
            INSERT INTO public."tblCustomerFollowup" (
                "ContactID", "DateOfFollowup", "ModeOfContact", "WhatDiscussed"
            ) VALUES (
                :contact_id, :date_of_followup, :mode_of_contact, :what_discussed
            ) RETURNING "ID"
        """)
        with get_session() as session:
            result = session.execute(query, data)
            session.commit()
            return result.scalar()

    def update_followup(self, followup_id, data: dict):
        """Updates an existing follow-up record."""
        query = text("""
            UPDATE public."tblCustomerFollowup" SET
                "DateOfFollowup"  = :date_of_followup,
                "ModeOfContact"   = :mode_of_contact,
                "WhatDiscussed"   = :what_discussed
            WHERE "ID" = :followup_id
        """)
        data["followup_id"] = followup_id
        with get_session() as session:
            session.execute(query, data)
            session.commit()

    def delete_followup(self, followup_id):
        """Deletes a follow-up record by ID."""
        query = text('DELETE FROM public."tblCustomerFollowup" WHERE "ID" = :followup_id')
        with get_session() as session:
            session.execute(query, {"followup_id": followup_id})
            session.commit()
