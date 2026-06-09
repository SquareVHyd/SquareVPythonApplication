from app.repositories.customer_repository import CustomerRepository

class CustomerService:
    def __init__(self):
        self.repo = CustomerRepository()

    def get_customers(self):
        """Returns the processed list of customers from Google Contacts."""
        return self.repo.get_google_contacts_summary()

    def get_contacts_for_organization(self, organization_name):
        """Returns detailed contacts for a specific organization."""
        return self.repo.get_contacts_by_organization_name(organization_name)

    def get_google_contact_followups(self, google_id):
        """Returns followup history for a specific Google Contact ID."""
        return self.repo.get_followups_by_google_id(google_id)

    def create_contact(self, data):
        """Creates a new Google contact."""
        return self.repo.create_google_contact(data)

    def update_contact(self, google_id, data):
        """Updates a Google contact."""
        return self.repo.update_google_contact(google_id, data)

    def delete_contact(self, google_id):
        """Deletes a contact."""
        return self.repo.delete_google_contact(google_id)

    def create_followup(self, data):
        """Creates a new followup."""
        return self.repo.create_google_followup(data)

    def update_followup(self, followup_id, data):
        """Updates a followup."""
        return self.repo.update_google_followup(followup_id, data)

    def delete_followup(self, followup_id):
        """Deletes a followup entry."""
        return self.repo.delete_google_followup(followup_id)