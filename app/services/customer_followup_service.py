from app.repositories.customer_followup_repository import (
    CustomerFollowupRepository,
)


class CustomerFollowupService:

    def __init__(self):
        self.repository = CustomerFollowupRepository()

    def get_followups_by_contact_id(self, contact_id):
        return self.repository.get_followups_by_contact_id(contact_id)

    def create_followup(
        self,
        contact_id,
        followup_date,
        what_discussed,
        mode_of_contact,
    ):
        return self.repository.create_followup(
            contact_id,
            followup_date,
            what_discussed,
            mode_of_contact,
        )

    def update_followup(
        self,
        followup_id,
        followup_date,
        what_discussed,
        mode_of_contact,
    ):
        return self.repository.update_followup(
            followup_id,
            followup_date,
            what_discussed,
            mode_of_contact,
        )

    def delete_followup(self, followup_id):
        return self.repository.delete_followup(followup_id)
