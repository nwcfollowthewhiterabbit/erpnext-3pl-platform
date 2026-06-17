from frappe.model.document import Document


class ThreePLClientInstruction(Document):
    def before_validate(self):
        from erpnext_3pl.client_desk import prepare_client_instruction

        prepare_client_instruction(self)
