from app.repositories.cust_db_repository import CustDbRepository


class CustDbService:
    """Service layer for tblCustomers and tblCustomerContacts CRUD operations."""

    def __init__(self):
        self.repo = CustDbRepository()

    # ------------------------------------------------------------------ #
    # tblCustomers
    # ------------------------------------------------------------------ #

    def get_all_customers(self):
        """Returns all customer rows (joined with tblState)."""
        return self.repo.get_all_customers()

    def get_customer_by_id(self, customer_id):
        """Returns a single customer row by ID."""
        return self.repo.get_customer_by_id(customer_id)

    def create_customer(self, data: dict):
        """
        Validates and creates a new customer.
        Expects keys: customer_name, mail, customer_phone, customer_address,
                      customer_city, customer_state_id, customer_pin,
                      customer_gstn_code, customer_notes, attachments
        """
        if not data.get("customer_name", "").strip():
            raise ValueError("Customer Name is required.")
        return self.repo.create_customer(data)

    def update_customer(self, customer_id, data: dict):
        """Validates and updates an existing customer."""
        if not data.get("customer_name", "").strip():
            raise ValueError("Customer Name is required.")
        self.repo.update_customer(customer_id, data)

    def delete_customer(self, customer_id):
        """Deletes a customer by ID."""
        self.repo.delete_customer(customer_id)

    def get_all_states(self):
        """Returns all state records for dropdown population."""
        return self.repo.get_all_states()

    # ------------------------------------------------------------------ #
    # tblCustomerContacts
    # ------------------------------------------------------------------ #

    def get_contacts_by_customer(self, customer_id):
        """Returns all contacts linked to the given customer ID."""
        return self.repo.get_contacts_by_customer(customer_id)

    def create_contact(self, data: dict):
        """
        Validates and creates a new customer contact.
        Expects keys: customer_id, contact_name, contact_title,
                      contact_designation, mobile1, mobile2
        """
        if not data.get("contact_name", "").strip():
            raise ValueError("Contact Name is required.")
        return self.repo.create_contact(data)

    def update_contact(self, contact_id, data: dict):
        """Validates and updates a contact record."""
        if not data.get("contact_name", "").strip():
            raise ValueError("Contact Name is required.")
        self.repo.update_contact(contact_id, data)

    def delete_contact(self, contact_id):
        """Deletes a contact by ID."""
        self.repo.delete_contact(contact_id)

    # ------------------------------------------------------------------ #
    # tblCustomerFollowup
    # ------------------------------------------------------------------ #

    def get_followups_by_contact(self, contact_id):
        """Returns all follow-up records for a given contact (newest first)."""
        return self.repo.get_followups_by_contact(contact_id)

    def create_followup(self, data: dict):
        """
        Validates and creates a new follow-up record.
        Expects keys: contact_id, date_of_followup (str/date),
                      mode_of_contact, what_discussed
        """
        if not data.get("date_of_followup"):
            raise ValueError("Date of Follow-up is required.")
        return self.repo.create_followup(data)

    def update_followup(self, followup_id, data: dict):
        """Validates and updates an existing follow-up record."""
        if not data.get("date_of_followup"):
            raise ValueError("Date of Follow-up is required.")
        self.repo.update_followup(followup_id, data)

    def delete_followup(self, followup_id):
        """Deletes a follow-up record by ID."""
        self.repo.delete_followup(followup_id)
