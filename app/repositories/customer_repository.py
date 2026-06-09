from sqlalchemy import text
from app.config.database import get_session

class CustomerRepository:
    def __init__(self):
        pass

    def get_google_contacts_summary(self):
        """Fetches unique organizations from google_contacts table."""
        query = text("""
            SELECT DISTINCT ON ("Organization Name")
                   "Organization Name",
                   COALESCE("E-mail 1 - Value", '') AS Email,
                   COALESCE("Phone 1 - Value", '') AS Phone
            FROM public.google_contacts
            WHERE "Organization Name" IS NOT NULL
              AND TRIM("Organization Name") <> ''
            ORDER BY "Organization Name"
        """)
        
        with get_session() as session:
            result = session.execute(query)
            return result.fetchall()

    def get_contacts_by_organization_name(self, organization_name):
        """
        Fetches detailed contact information for a given organization name
        from the google_contacts table.
        """
        query = text("""
            SELECT 
                "Google ID",
                "First Name", 
                "Middle Name", 
                "Last Name",
                COALESCE(
                    NULLIF(TRIM("Phone 1 - Value"), ''), 
                    NULLIF(TRIM("Phone 2 - Value"), ''), 
                    NULLIF(TRIM("Phone 3 - Value"), '')
                ) AS Phone,
                COALESCE(
                    NULLIF(TRIM("E-mail 1 - Value"), ''), 
                    NULLIF(TRIM("E-mail 2 - Value"), ''), 
                    NULLIF(TRIM("E-mail 3 - Value"), '')
                ) AS Email
            FROM public.google_contacts
            WHERE "Organization Name" = :organization_name
            ORDER BY "First Name", "Last Name"
        """)

        with get_session() as session:
            result = session.execute(query, {"organization_name": organization_name})
            return result.fetchall()

    def create_google_contact(self, data):
        """Creates a new contact record."""
        query = text("""
            INSERT INTO public.google_contacts (
                "Google ID", "First Name", "Middle Name", "Last Name", 
                "Organization Name", "Phone 1 - Value", "E-mail 1 - Value"
            ) VALUES (
                :google_id, :first_name, :middle_name, :last_name, 
                :org_name, :phone, :email
            )
        """)
        with get_session() as session:
            session.execute(query, data)
            session.commit()

    def update_google_contact(self, google_id, data):
        """Updates an existing contact record."""
        query = text("""
            UPDATE public.google_contacts SET
                "First Name" = :first_name,
                "Middle Name" = :middle_name,
                "Last Name" = :last_name,
                "Phone 1 - Value" = :phone,
                "E-mail 1 - Value" = :email
            WHERE "Google ID" = :google_id
        """)
        data["google_id"] = google_id
        with get_session() as session:
            session.execute(query, data)
            session.commit()

    def get_followups_by_google_id(self, google_id):
        """Fetches followup history for a specific Google Contact."""
        query = text("""
            SELECT
                gc."Organization Name",
                f."DateOfFollowup",
                f."ModeOfContact",
                f."WhatDiscussed",
                f."NextFollowupDate",
                f."Status",
                f."ID"
            FROM public.google_contacts gc
            JOIN public."tblGoogleContactFollowup" f
                ON gc."Google ID" = f."GoogleID"
            WHERE gc."Google ID" = :google_id
            ORDER BY f."DateOfFollowup" DESC
        """)
        
        with get_session() as session:
            result = session.execute(query, {"google_id": google_id})
            return result.fetchall()

    def create_google_followup(self, data):
        """Creates a new followup record."""
        query = text("""
            INSERT INTO public."tblGoogleContactFollowup" (
                "GoogleID", "DateOfFollowup", "ModeOfContact", 
                "WhatDiscussed", "NextFollowupDate", "Status"
            ) VALUES (
                :google_id, :date, :mode, :discussed, :next_date, :status
            )
        """)
        with get_session() as session:
            session.execute(query, data)
            session.commit()

    def update_google_followup(self, followup_id, data):
        """Updates an existing followup record."""
        query = text("""
            UPDATE public."tblGoogleContactFollowup" SET
                "DateOfFollowup" = :date,
                "ModeOfContact" = :mode,
                "WhatDiscussed" = :discussed,
                "NextFollowupDate" = :next_date,
                "Status" = :status
            WHERE "ID" = :id
        """)
        data["id"] = followup_id
        with get_session() as session:
            session.execute(query, data)
            session.commit()

    def delete_google_contact(self, google_id):
        """Deletes a contact from google_contacts."""
        query = text('DELETE FROM public.google_contacts WHERE "Google ID" = :google_id')
        with get_session() as session:
            session.execute(query, {"google_id": google_id})
            session.commit()

    def delete_google_followup(self, followup_id):
        """Deletes a followup record."""
        query = text('DELETE FROM public."tblGoogleContactFollowup" WHERE "ID" = :id')
        with get_session() as session:
            session.execute(query, {"id": followup_id})
            session.commit()