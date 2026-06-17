from frappe.model.document import Document


class ThreePLClientProduct(Document):
    def before_validate(self):
        from erpnext_3pl.client_desk import prepare_client_product

        prepare_client_product(self)
