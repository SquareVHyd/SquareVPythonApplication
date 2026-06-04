from app.repositories.module_type_repository import ModuleTypeRepository


class ModuleTypeService:
    def __init__(self):
        self.repository = ModuleTypeRepository()

    def get_all_module_types(self):
        return self.repository.get_all_module_types()

    def get_module_type(self, module_type_id):
        return self.repository.get_module_type(module_type_id)

    def create_module_type(self, module_type, module_make_id, mod_swg_id):
        return self.repository.create_module_type(module_type, module_make_id, mod_swg_id)

    def update_module_type(self, module_type_id, module_type, module_make_id, mod_swg_id):
        return self.repository.update_module_type(module_type_id, module_type, module_make_id, mod_swg_id)

    def delete_module_type(self, module_type_id):
        return self.repository.delete_module_type(module_type_id)

    def get_all_module_makes(self):
        return self.repository.get_all_module_makes()

    def get_all_swgs(self):
        return self.repository.get_all_swgs()

    def create_module_make(self, module_make):
        return self.repository.create_module_make(module_make)
