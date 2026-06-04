from app.repositories.module_repository import ModuleRepository


class ModuleService:
    def __init__(self):
        self.repository = ModuleRepository()

    def get_all_modules(self):
        return self.repository.get_all_modules()

    def get_items_by_module_type(self, module_type_id):
        return self.repository.get_items_by_module_type(module_type_id)

    def get_module(self, module_id):
        return self.repository.get_module(module_id)

    def create_module(self, module_type_id, item_id, qty, seqno):
        return self.repository.create_module(module_type_id, item_id, qty, seqno)

    def update_module(self, module_id, module_type_id, item_id, qty, seqno):
        return self.repository.update_module(module_id, module_type_id, item_id, qty, seqno)

    def delete_module(self, module_id):
        return self.repository.delete_module(module_id)
