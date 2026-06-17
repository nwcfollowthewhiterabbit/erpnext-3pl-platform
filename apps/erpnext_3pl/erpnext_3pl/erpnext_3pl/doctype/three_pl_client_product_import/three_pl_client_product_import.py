from frappe.model.document import Document


class ThreePLClientProductImport(Document):
    def before_validate(self):
        from erpnext_3pl.client_desk import prepare_client_product_import

        prepare_client_product_import(self)
