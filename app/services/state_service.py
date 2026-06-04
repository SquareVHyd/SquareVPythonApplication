from app.repositories.state_repository import StateRepository


class StateService:
    def __init__(self):
        self.repository = StateRepository()

    def get_all_states(self):
        return self.repository.get_states()

    def get_state(self, state_id):
        return self.repository.get_state_by_id(state_id)

    def search(self, keyword):
        return self.repository.search_states(keyword)

    def create(self, state_code, state_name):
        return self.repository.create_state(state_code, state_name)

    def update(self, state_id, state_code, state_name):
        return self.repository.update_state(state_id, state_code, state_name)

    def delete(self, state_id):
        return self.repository.delete_state(state_id)
