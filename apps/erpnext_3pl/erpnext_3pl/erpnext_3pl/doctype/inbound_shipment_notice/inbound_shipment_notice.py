from frappe.model.document import Document


class InboundShipmentNotice(Document):
    def before_validate(self):
        from erpnext_3pl.client_desk import prepare_inbound_notice

        prepare_inbound_notice(self)
