from sqlalchemy import text

from app.config.database import get_session


class CustomerFollowupRepository:

    def __init__(self):
        self.session = get_session()

    def get_followups_by_contact_id(self, contact_id):

        query = text(
            '''
            SELECT
                "ID",
                "ContactID",
                "DateOfFollowup",
                "WhatDiscussed",
                "ModeOfContact",
                "SysDateOfEntry"
            FROM "tblCustomerFollowup"
            WHERE "ContactID" = :contact_id
            ORDER BY "DateOfFollowup" DESC
            '''
        )

        with get_session() as session:
            result = session.execute(
                query,
                {
                    "contact_id": contact_id
                }
            )

            return result.fetchall()

    def create_followup(
        self,
        contact_id,
        followup_date,
        what_discussed,
        mode_of_contact,
    ):

        query = text(
            '''
            INSERT INTO "tblCustomerFollowup"
            (
                "ContactID",
                "DateOfFollowup",
                "WhatDiscussed",
                "ModeOfContact"
            )
            VALUES
            (
                :contact_id,
                :followup_date,
                :what_discussed,
                :mode_of_contact
            )
            '''
        )

        with get_session() as session:
            session.execute(
                query,
                {
                    "contact_id": contact_id,
                    "followup_date": followup_date,
                    "what_discussed": what_discussed,
                    "mode_of_contact": mode_of_contact,
                }
            )

            session.commit()

    def update_followup(
        self,
        followup_id,
        followup_date,
        what_discussed,
        mode_of_contact,
    ):

        query = text(
            '''
            UPDATE "tblCustomerFollowup"
            SET
                "DateOfFollowup" = :followup_date,
                "WhatDiscussed" = :what_discussed,
                "ModeOfContact" = :mode_of_contact
            WHERE "ID" = :followup_id
            '''
        )

        with get_session() as session:
            session.execute(
                query,
                {
                    "followup_id": followup_id,
                    "followup_date": followup_date,
                    "what_discussed": what_discussed,
                    "mode_of_contact": mode_of_contact,
                }
            )

            session.commit()

    def delete_followup(self, followup_id):
        query = text(
            '''
            DELETE FROM "tblCustomerFollowup"
            WHERE "ID" = :followup_id
            '''
        )

        with get_session() as session:
            session.execute(
                query,
                {
                    "followup_id": followup_id
                }
            )

            session.commit()
