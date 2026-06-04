import frappe
from frappe.utils import nowdate


CLIENTS = [
    "Demo Client Alpha",
    "Demo Client Beta",
]
COUNTRY = "Lithuania"

ITEMS = [
    {
        "item_code": "SKU-ALPHA-001",
        "item_name": "Demo Alpha Widget",
        "client": "Demo Client Alpha",
        "client_sku": "ALPHA-001",
        "client_product_name": "Alpha Widget",
        "barcode": "300000000001",
    },
    {
        "item_code": "SKU-ALPHA-002",
        "item_name": "Demo Alpha Cable",
        "client": "Demo Client Alpha",
        "client_sku": "ALPHA-002",
        "client_product_name": "Alpha Cable",
        "barcode": "300000000002",
    },
    {
        "item_code": "SKU-BETA-001",
        "item_name": "Demo Beta Accessory",
        "client": "Demo Client Beta",
        "client_sku": "BETA-001",
        "client_product_name": "Beta Accessory",
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

    if not frappe.db.exists("Territory", COUNTRY):
        frappe.get_doc(
            {
                "doctype": "Territory",
                "territory_name": COUNTRY,
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
        customer = frappe.get_doc("Customer", customer_name)
        changed = False
        expected = {
            "customer_group": "Commercial",
            "territory": COUNTRY,
        }
        for key, value in expected.items():
            if getattr(customer, key, None) != value:
                setattr(customer, key, value)
                changed = True
        if changed:
            customer.save(ignore_permissions=True)
        return customer

    return frappe.get_doc(
        {
            "doctype": "Customer",
            "customer_name": customer_name,
            "customer_type": "Company",
            "customer_group": "Commercial",
            "territory": COUNTRY,
        }
    ).insert(ignore_permissions=True)


def meta_has_field(doctype, fieldname):
    return frappe.get_meta(doctype).has_field(fieldname)


def set_if_field(doc, fieldname, value):
    if doc.meta.has_field(fieldname) and getattr(doc, fieldname, None) != value:
        setattr(doc, fieldname, value)


def ensure_item(item_code, item_name, client, client_sku, client_product_name, barcode):
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

    item.item_name = item_name
    item.item_group = "Products"
    item.stock_uom = "Nos"
    set_if_field(item, "owner_client", client)
    set_if_field(item, "client_sku", client_sku)
    set_if_field(item, "client_product_name", client_product_name)

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
        notice = frappe.get_doc("Inbound Shipment Notice", existing)
        sync_notice_details(notice)
        return notice

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
                    "client_sku": "ALPHA-001",
                    "item_name": "Demo Alpha Widget",
                    "expected_qty": 10,
                    "uom": "Nos",
                    "received_qty": 10,
                    "variance_qty": 0,
                    "condition_status": "OK",
                },
                {
                    "item_code": "SKU-ALPHA-002",
                    "client_sku": "ALPHA-002",
                    "item_name": "Demo Alpha Cable",
                    "expected_qty": 25,
                    "uom": "Nos",
                    "received_qty": 24,
                    "variance_qty": -1,
                    "condition_status": "OK",
                },
            ],
            "notes": "Demo client notification for receiving and comparison flow.",
        }
    )
    if meta_has_field("Inbound Shipment Notice", "client_instruction_status"):
        notice.client_instruction_status = "Waiting for Client"
    sync_notice_details(notice)
    notice.insert(ignore_permissions=True)
    return notice


def sync_notice_details(notice):
    if meta_has_field("Inbound Shipment Notice", "client_instruction_status"):
        notice.client_instruction_status = "Waiting for Client"

    container_exists = frappe.db.exists("Three PL Container", "BOX-ALPHA-001")
    expected_rows = {
        "SKU-ALPHA-001": {"client_sku": "ALPHA-001", "received_qty": 10, "variance_qty": 0, "condition_status": "OK"},
        "SKU-ALPHA-002": {"client_sku": "ALPHA-002", "received_qty": 24, "variance_qty": -1, "condition_status": "OK"},
    }
    if container_exists:
        expected_rows["SKU-ALPHA-001"]["container_code"] = "BOX-ALPHA-001"
        expected_rows["SKU-ALPHA-002"]["container_code"] = "BOX-ALPHA-001"

    for row in notice.get("items", []):
        values = expected_rows.get(row.item_code)
        if not values:
            continue
        for fieldname, value in values.items():
            if row.meta.has_field(fieldname):
                setattr(row, fieldname, value)

    if meta_has_field("Inbound Shipment Notice", "discrepancies"):
        discrepancy = {
            "discrepancy_type": "Quantity Difference",
            "item_code": "SKU-ALPHA-002",
            "client_sku": "ALPHA-002",
            "expected_qty": 25,
            "actual_qty": 24,
            "variance_qty": -1,
            "status": "Open",
            "notes": "Demo case: one item is missing from the received box.",
        }
        if container_exists:
            discrepancy["container_code"] = "BOX-ALPHA-001"

        notice.set("discrepancies", [])
        notice.append("discrepancies", discrepancy)

    if not notice.is_new():
        notice.save(ignore_permissions=True)


def ensure_container(notice_name):
    name = "BOX-ALPHA-001"
    if frappe.db.exists("Three PL Container", name):
        container = frappe.get_doc("Three PL Container", name)
        container.set("items", [])
    else:
        container = frappe.new_doc("Three PL Container")
        container.container_code = name

    container.barcode = "BOX300000000001"
    container.client = "Demo Client Alpha"
    container.current_warehouse = "Temporary Receiving - 3"
    container.inbound_shipment_notice = notice_name
    container.status = "In Verification"
    container.notes = "Demo receiving box used to test containerized receiving and discrepancy review."
    container.append(
        "items",
        {
            "item_code": "SKU-ALPHA-001",
            "client_sku": "ALPHA-001",
            "qty": 10,
            "uom": "Nos",
            "condition_status": "OK",
        },
    )
    container.append(
        "items",
        {
            "item_code": "SKU-ALPHA-002",
            "client_sku": "ALPHA-002",
            "qty": 24,
            "uom": "Nos",
            "condition_status": "OK",
            "notes": "Expected quantity is 25 on the Receiving Notice.",
        },
    )
    container.save(ignore_permissions=True)
    return container


def ensure_stock_entry(notice_name):
    name = "DEMO-RECEIVING-ALPHA-001"
    if frappe.db.exists("Stock Entry", name):
        entry = frappe.get_doc("Stock Entry", name)
        set_if_field(entry, "container_code", "BOX-ALPHA-001")
        for row in entry.items:
            if row.meta.has_field("container_code"):
                row.container_code = "BOX-ALPHA-001"
        entry.save(ignore_permissions=True)
        return entry

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
            "container_code": "BOX-ALPHA-001",
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
                    "container_code": "BOX-ALPHA-001",
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
                    "container_code": "BOX-ALPHA-001",
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
    ensure_container(notice.name)
    notice = frappe.get_doc("Inbound Shipment Notice", notice.name)
    sync_notice_details(notice)
    ensure_stock_entry(notice.name)

    frappe.db.commit()
    frappe.clear_cache()
