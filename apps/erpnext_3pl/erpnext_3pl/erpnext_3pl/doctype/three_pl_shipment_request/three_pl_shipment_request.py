from frappe.model.document import Document


class ThreePLShipmentRequest(Document):
    def before_validate(self):
        from erpnext_3pl.client_desk import prepare_shipment_request

        prepare_shipment_request(self)
