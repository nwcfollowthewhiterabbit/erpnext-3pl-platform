import frappe
from frappe.utils import nowdate


CLIENTS = [
    "Demo Client Alpha",
    "Demo Client Beta",
]

ITEMS = [
    {
        "item_code": "SKU-ALPHA-001",
        "item_name": "Demo Alpha Widget",
        "barcode": "300000000001",
    },
    {
        "item_code": "SKU-ALPHA-002",
        "item_name": "Demo Alpha Cable",
        "barcode": "300000000002",
    },
    {
        "item_code": "SKU-BETA-001",
        "item_name": "Demo Beta Accessory",
        "barcode": "300000000003",
    },
]


def ensure_master_data():
    if not frappe.db.exists("Customer Group", "Commercial"):
        frappe.get_doc(
            {
                "doctype": "Customer Group",
                "customer_group_name": "Commercial",
                "is_group": 0,
            }
        ).insert(ignore_permissions=True)

    if not frappe.db.exists("Territory", "Ukraine"):
        frappe.get_doc(
            {
                "doctype": "Territory",
                "territory_name": "Ukraine",
                "is_group": 0,
            }
        ).insert(ignore_permissions=True)

    if not frappe.db.exists("Item Group", "Products"):
        frappe.get_doc(
            {
                "doctype": "Item Group",
                "item_group_name": "Products",
                "is_group": 0,
            }
        ).insert(ignore_permissions=True)

    if not frappe.db.exists("UOM", "Nos"):
        frappe.get_doc({"doctype": "UOM", "uom_name": "Nos"}).insert(ignore_permissions=True)


def ensure_customer(customer_name):
    if frappe.db.exists("Customer", customer_name):
        return frappe.get_doc("Customer", customer_name)

    return frappe.get_doc(
        {
            "doctype": "Customer",
            "customer_name": customer_name,
            "customer_type": "Company",
            "customer_group": "Commercial",
            "territory": "Ukraine",
        }
    ).insert(ignore_permissions=True)


def ensure_item(item_code, item_name, barcode):
    if frappe.db.exists("Item", item_code):
        item = frappe.get_doc("Item", item_code)
    else:
        item = frappe.get_doc(
            {
                "doctype": "Item",
                "item_code": item_code,
                "item_name": item_name,
                "item_group": "Products",
                "stock_uom": "Nos",
                "is_stock_item": 1,
            }
        )

    if not any(row.barcode == barcode for row in item.get("barcodes", [])):
        item.append("barcodes", {"barcode": barcode})

    item.save(ignore_permissions=True)
    return item


def ensure_inbound_notice():
    external_reference = "ASN-ALPHA-001"
    existing = frappe.db.get_value(
        "Inbound Shipment Notice",
        {"external_reference": external_reference, "customer": "Demo Client Alpha"},
        "name",
    )
    if existing:
        return frappe.get_doc("Inbound Shipment Notice", existing)

    notice = frappe.get_doc(
        {
            "doctype": "Inbound Shipment Notice",
            "customer": "Demo Client Alpha",
            "external_reference": external_reference,
            "notice_date": nowdate(),
            "expected_arrival_date": nowdate(),
            "temporary_warehouse": "Temporary Receiving - 3",
            "status": "Draft",
            "items": [
                {
                    "item_code": "SKU-ALPHA-001",
                    "item_name": "Demo Alpha Widget",
                    "expected_qty": 10,
                    "uom": "Nos",
                },
                {
                    "item_code": "SKU-ALPHA-002",
                    "item_name": "Demo Alpha Cable",
                    "expected_qty": 25,
                    "uom": "Nos",
                },
            ],
            "notes": "Demo client notification for receiving and comparison flow.",
        }
    )
    notice.insert(ignore_permissions=True)
    return notice


def ensure_stock_entry(notice_name):
    name = "DEMO-RECEIVING-ALPHA-001"
    if frappe.db.exists("Stock Entry", name):
        return frappe.get_doc("Stock Entry", name)

    entry = frappe.get_doc(
        {
            "doctype": "Stock Entry",
            "name": name,
            "stock_entry_type": "3PL Inbound Receipt",
            "purpose": "Material Receipt",
            "company": "3pl",
            "posting_date": nowdate(),
            "client": "Demo Client Alpha",
            "inbound_shipment_notice": notice_name,
            "warehouse_flow": "Inbound Receipt",
            "scanned_location": "Temporary Receiving - 3",
            "items": [
                {
                    "item_code": "SKU-ALPHA-001",
                    "qty": 10,
                    "t_warehouse": "Temporary Receiving - 3",
                    "uom": "Nos",
                    "stock_uom": "Nos",
                    "conversion_factor": 1,
                    "basic_rate": 1,
                    "scanned_location": "Temporary Receiving - 3",
                },
                {
                    "item_code": "SKU-ALPHA-002",
                    "qty": 24,
                    "t_warehouse": "Temporary Receiving - 3",
                    "uom": "Nos",
                    "stock_uom": "Nos",
                    "conversion_factor": 1,
                    "basic_rate": 1,
                    "scanned_location": "Temporary Receiving - 3",
                },
            ],
        }
    )
    entry.insert(ignore_permissions=True)
    return entry


def main():
    ensure_master_data()

    for customer_name in CLIENTS:
        ensure_customer(customer_name)

    for item in ITEMS:
        ensure_item(**item)

    notice = ensure_inbound_notice()
    ensure_stock_entry(notice.name)

    frappe.db.commit()
    frappe.clear_cache()
