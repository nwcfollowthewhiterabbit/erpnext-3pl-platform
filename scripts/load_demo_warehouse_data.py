import frappe
from frappe.utils import now, nowdate

from project_config import CLIENT_PORTAL_USER, COUNTRY, DEMO_CLIENTS, DEMO_ITEMS


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


def set_owner_after_save(doc, owner):
    if not doc.is_new() and doc.owner != owner:
        frappe.db.set_value(doc.doctype, doc.name, "owner", owner, update_modified=False)
        doc.owner = owner


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
    notice.owner = CLIENT_PORTAL_USER
    notice.insert(ignore_permissions=True)
    return notice


def ensure_beta_inbound_notice():
    external_reference = "ASN-BETA-001"
    existing = frappe.db.get_value(
        "Inbound Shipment Notice",
        {"external_reference": external_reference, "customer": "Demo Client Beta"},
        "name",
    )
    if existing:
        notice = frappe.get_doc("Inbound Shipment Notice", existing)
        notice.set("items", [])
    else:
        notice = frappe.new_doc("Inbound Shipment Notice")

    notice.customer = "Demo Client Beta"
    notice.external_reference = external_reference
    notice.notice_date = nowdate()
    notice.expected_arrival_date = nowdate()
    notice.temporary_warehouse = "Temporary Receiving - 3"
    notice.status = "Draft"
    notice.notes = "Demo data used to validate that Alpha client cannot read Beta receiving notices."
    notice.append(
        "items",
        {
            "item_code": "SKU-BETA-001",
            "client_sku": "BETA-001",
            "item_name": "Demo Beta Accessory",
            "expected_qty": 7,
            "uom": "Nos",
            "received_qty": 0,
            "variance_qty": -7,
            "condition_status": "OK",
        },
    )
    notice.save(ignore_permissions=True)
    return notice


def ensure_alpha_portal_notice(external_reference, expected_arrival_date, status, items, notes, instruction_status=None):
    existing = frappe.db.get_value(
        "Inbound Shipment Notice",
        {"external_reference": external_reference, "customer": "Demo Client Alpha"},
        "name",
    )
    notice = frappe.get_doc("Inbound Shipment Notice", existing) if existing else frappe.new_doc("Inbound Shipment Notice")

    notice.customer = "Demo Client Alpha"
    notice.external_reference = external_reference
    notice.notice_date = nowdate()
    notice.expected_arrival_date = expected_arrival_date
    notice.temporary_warehouse = "Temporary Receiving - 3"
    notice.status = status
    notice.notes = notes
    if instruction_status and meta_has_field("Inbound Shipment Notice", "client_instruction_status"):
        notice.client_instruction_status = instruction_status

    notice.set("items", [])
    for item in items:
        notice.append("items", item)

    if notice.is_new():
        notice.owner = CLIENT_PORTAL_USER
    notice.save(ignore_permissions=True)
    set_owner_after_save(notice, CLIENT_PORTAL_USER)
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
        set_owner_after_save(notice, CLIENT_PORTAL_USER)


def ensure_container(notice_name):
    name = "BOX-ALPHA-001"
    if frappe.db.exists("Three PL Container", name):
        container = frappe.get_doc("Three PL Container", name)
        container.set("items", [])
    else:
        container = frappe.new_doc("Three PL Container")
        container.container_code = name

    container.barcode = "BOX300000000001"
    if container.meta.has_field("container_type"):
        container.container_type = "Box"
    container.client = "Demo Client Alpha"
    container.current_warehouse = "Temporary Receiving - 3"
    container.inbound_shipment_notice = notice_name
    container.status = "In Verification"
    if container.meta.has_field("last_moved_at"):
        container.last_moved_at = now()
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


def ensure_alpha_storage_container():
    name = "BOX-ALPHA-002"
    if frappe.db.exists("Three PL Container", name):
        container = frappe.get_doc("Three PL Container", name)
        container.set("items", [])
    else:
        container = frappe.new_doc("Three PL Container")
        container.container_code = name

    container.barcode = "BOX300000000002"
    if container.meta.has_field("container_type"):
        container.container_type = "Box"
    container.client = "Demo Client Alpha"
    container.current_warehouse = "Aisle A - 3"
    container.status = "Stored"
    if container.meta.has_field("last_moved_at"):
        container.last_moved_at = now()
    container.notes = "Demo storage box used by Alpha client inventory snapshots."
    container.append(
        "items",
        {
            "item_code": "SKU-ALPHA-003",
            "client_sku": "ALPHA-003",
            "qty": 18,
            "uom": "Nos",
            "condition_status": "OK",
        },
    )
    container.save(ignore_permissions=True)
    return container


def ensure_container_movement(container_code, movement_type, to_warehouse, from_warehouse=None, reference_doctype=None, reference_name=None, notes=None):
    existing = frappe.db.get_value(
        "Three PL Container Movement",
        {
            "container_code": container_code,
            "movement_type": movement_type,
            "from_warehouse": from_warehouse,
            "to_warehouse": to_warehouse,
            "reference_doctype": reference_doctype,
            "reference_name": reference_name,
        },
        "name",
    )
    movement = frappe.get_doc("Three PL Container Movement", existing) if existing else frappe.new_doc("Three PL Container Movement")
    container = frappe.get_doc("Three PL Container", container_code)

    movement.movement_datetime = now()
    movement.container_code = container_code
    movement.client = container.client
    movement.movement_type = movement_type
    movement.from_warehouse = from_warehouse
    movement.to_warehouse = to_warehouse
    movement.reference_doctype = reference_doctype
    movement.reference_name = reference_name
    movement.notes = notes
    movement.save(ignore_permissions=True)
    return movement


def ensure_demo_container_movements(notice_name):
    ensure_container_movement(
        "BOX-ALPHA-001",
        "Received",
        "Temporary Receiving - 3",
        reference_doctype="Inbound Shipment Notice",
        reference_name=notice_name,
        notes="Demo movement: container received into temporary receiving for verification.",
    )
    ensure_container_movement(
        "BOX-ALPHA-002",
        "Putaway",
        "Aisle A - 3",
        from_warehouse="Temporary Receiving - 3",
        notes="Demo movement: container moved from receiving into storage.",
    )


def ensure_container_move_operation():
    operation_reference = "MOVE-ALPHA-001"
    existing = frappe.db.get_value("Three PL Container Move", {"operation_reference": operation_reference}, "name")
    move = frappe.get_doc("Three PL Container Move", existing) if existing else frappe.new_doc("Three PL Container Move")

    move.operation_reference = operation_reference
    if move.is_new() or not move.operation_datetime:
        move.operation_datetime = now()
    if move.status != "Applied":
        move.status = "Draft"
    move.container_code = "BOX-ALPHA-002"
    move.client = "Demo Client Alpha"
    move.from_warehouse = "Temporary Receiving - 3"
    move.to_warehouse = "Aisle A - 3"
    move.notes = "Demo container move operation. The versioned move processor applies Draft moves, updates the container, and creates movement history."
    move.save(ignore_permissions=True)

    if move.status == "Draft":
        container = frappe.get_doc("Three PL Container", "BOX-ALPHA-002")
        container.current_warehouse = move.from_warehouse
        container.status = "Ready for Putaway"
        container.save(ignore_permissions=True)

    return move


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


def ensure_inventory_snapshots():
    snapshots = [
        {
            "customer": "Demo Client Alpha",
            "item_code": "SKU-ALPHA-001",
            "client_sku": "ALPHA-001",
            "item_name": "Demo Alpha Widget",
            "qty": 10,
            "uom": "Nos",
            "warehouse": "Temporary Receiving - 3",
            "container_code": "BOX-ALPHA-001",
            "status": "Receiving",
            "notes": "Demo inventory snapshot from receiving container.",
        },
        {
            "customer": "Demo Client Alpha",
            "item_code": "SKU-ALPHA-002",
            "client_sku": "ALPHA-002",
            "item_name": "Demo Alpha Cable",
            "qty": 24,
            "uom": "Nos",
            "warehouse": "Temporary Receiving - 3",
            "container_code": "BOX-ALPHA-001",
            "status": "Receiving",
            "notes": "Demo inventory snapshot with one missing unit versus ASN.",
        },
        {
            "customer": "Demo Client Alpha",
            "item_code": "SKU-ALPHA-003",
            "client_sku": "ALPHA-003",
            "item_name": "Demo Alpha Adapter",
            "qty": 18,
            "uom": "Nos",
            "warehouse": "Aisle A - 3",
            "container_code": "BOX-ALPHA-002",
            "status": "Available",
            "notes": "Demo stock already put away into storage.",
        },
        {
            "customer": "Demo Client Beta",
            "item_code": "SKU-BETA-001",
            "client_sku": "BETA-001",
            "item_name": "Demo Beta Accessory",
            "qty": 7,
            "uom": "Nos",
            "warehouse": "Aisle B - 3",
            "container_code": None,
            "status": "Available",
            "notes": "Demo data used to validate that Alpha client cannot read Beta inventory.",
        },
    ]

    for snapshot in snapshots:
        existing = frappe.db.get_value(
            "Three PL Inventory Snapshot",
            {
                "customer": snapshot["customer"],
                "item_code": snapshot["item_code"],
                "container_code": snapshot["container_code"],
            },
            "name",
        )
        if existing:
            doc = frappe.get_doc("Three PL Inventory Snapshot", existing)
        else:
            doc = frappe.new_doc("Three PL Inventory Snapshot")

        for key, value in snapshot.items():
            setattr(doc, key, value)
        should_set_client_owner = snapshot["customer"] == "Demo Client Alpha"
        if should_set_client_owner and doc.is_new():
            doc.owner = CLIENT_PORTAL_USER
        doc.last_updated = now()
        doc.save(ignore_permissions=True)
        if should_set_client_owner:
            set_owner_after_save(doc, CLIENT_PORTAL_USER)


def ensure_shipment_request():
    external_reference = "SHIP-ALPHA-001"
    existing = frappe.db.get_value(
        "Three PL Shipment Request",
        {"customer": "Demo Client Alpha", "external_reference": external_reference},
        "name",
    )
    if existing:
        request = frappe.get_doc("Three PL Shipment Request", existing)
        request.set("items", [])
    else:
        request = frappe.new_doc("Three PL Shipment Request")

    request.customer = "Demo Client Alpha"
    request.external_reference = external_reference
    request.requested_ship_date = nowdate()
    request.status = "Submitted"
    request.destination_name = "Demo Consignee"
    request.destination_address = "Demo Street 1, Vilnius, Lithuania"
    request.portal_source = 1
    if request.is_new():
        request.owner = CLIENT_PORTAL_USER
    request.notes = "Demo outbound request created for client portal testing."
    request.append(
        "items",
        {
            "item_code": "SKU-ALPHA-001",
            "client_sku": "ALPHA-001",
            "qty": 1,
            "uom": "Nos",
        },
    )
    request.save(ignore_permissions=True)
    set_owner_after_save(request, CLIENT_PORTAL_USER)
    return request


def ensure_alpha_shipment_request(external_reference, requested_ship_date, status, destination_name, destination_address, items, notes):
    existing = frappe.db.get_value(
        "Three PL Shipment Request",
        {"customer": "Demo Client Alpha", "external_reference": external_reference},
        "name",
    )
    request = frappe.get_doc("Three PL Shipment Request", existing) if existing else frappe.new_doc("Three PL Shipment Request")

    request.customer = "Demo Client Alpha"
    request.external_reference = external_reference
    request.requested_ship_date = requested_ship_date
    request.status = status
    request.destination_name = destination_name
    request.destination_address = destination_address
    request.portal_source = 1
    request.notes = notes
    request.set("items", [])
    for item in items:
        request.append("items", item)

    if request.is_new():
        request.owner = CLIENT_PORTAL_USER
    request.save(ignore_permissions=True)
    set_owner_after_save(request, CLIENT_PORTAL_USER)
    return request


def ensure_client_instruction(notice_name, item_code="SKU-ALPHA-002", client_sku="ALPHA-002", instruction_type="Accept Difference", instruction_text=None):
    existing = frappe.db.get_value(
        "Three PL Client Instruction",
        {"customer": "Demo Client Alpha", "receiving_notice": notice_name, "item_code": item_code},
        "name",
    )
    if existing:
        instruction = frappe.get_doc("Three PL Client Instruction", existing)
    else:
        instruction = frappe.new_doc("Three PL Client Instruction")

    instruction.customer = "Demo Client Alpha"
    instruction.receiving_notice = notice_name
    instruction.item_code = item_code
    instruction.client_sku = client_sku
    instruction.instruction_type = instruction_type
    instruction.status = "Submitted"
    instruction.portal_source = 1
    if instruction.is_new():
        instruction.owner = CLIENT_PORTAL_USER
    instruction.instruction_text = instruction_text or "Demo instruction: accept the one-unit shortage and continue putaway for received goods."
    instruction.save(ignore_permissions=True)
    set_owner_after_save(instruction, CLIENT_PORTAL_USER)
    return instruction


def ensure_additional_alpha_portal_data():
    second_notice = ensure_alpha_portal_notice(
        external_reference="ASN-ALPHA-002",
        expected_arrival_date=nowdate(),
        status="Partially Received",
        instruction_status="Not Required",
        notes="Demo receiving notice with products expected later today.",
        items=[
            {
                "item_code": "SKU-ALPHA-001",
                "client_sku": "ALPHA-001",
                "item_name": "Demo Alpha Widget",
                "expected_qty": 6,
                "uom": "Nos",
                "received_qty": 0,
                "variance_qty": -6,
                "condition_status": "OK",
            },
            {
                "item_code": "SKU-ALPHA-003",
                "client_sku": "ALPHA-003",
                "item_name": "Demo Alpha Adapter",
                "expected_qty": 18,
                "uom": "Nos",
                "received_qty": 18,
                "variance_qty": 0,
                "condition_status": "OK",
            },
        ],
    )
    third_notice = ensure_alpha_portal_notice(
        external_reference="ASN-ALPHA-003",
        expected_arrival_date=nowdate(),
        status="Draft",
        instruction_status="Waiting for Client",
        notes="Demo receiving notice with a damaged product case.",
        items=[
            {
                "item_code": "SKU-ALPHA-002",
                "client_sku": "ALPHA-002",
                "item_name": "Demo Alpha Cable",
                "expected_qty": 12,
                "uom": "Nos",
                "received_qty": 11,
                "variance_qty": -1,
                "condition_status": "Damaged",
            },
        ],
    )

    ensure_alpha_shipment_request(
        external_reference="SHIP-ALPHA-002",
        requested_ship_date=nowdate(),
        status="Draft",
        destination_name="Demo Retail Store",
        destination_address="Gedimino pr. 10, Vilnius, Lithuania",
        notes="Demo draft outbound request for client portal review.",
        items=[
            {
                "item_code": "SKU-ALPHA-003",
                "client_sku": "ALPHA-003",
                "qty": 3,
                "uom": "Nos",
            },
        ],
    )
    ensure_client_instruction(
        third_notice.name,
        item_code="SKU-ALPHA-002",
        client_sku="ALPHA-002",
        instruction_type="Hold For Review",
        instruction_text="Demo instruction: keep the damaged cable case on hold until client confirms replacement or disposal.",
    )
    return second_notice, third_notice


def main():
    ensure_master_data()

    for customer_name in DEMO_CLIENTS:
        ensure_customer(customer_name)

    for item in DEMO_ITEMS:
        ensure_item(**item)

    notice = ensure_inbound_notice()
    ensure_beta_inbound_notice()
    ensure_container(notice.name)
    ensure_alpha_storage_container()
    ensure_demo_container_movements(notice.name)
    ensure_container_move_operation()
    notice = frappe.get_doc("Inbound Shipment Notice", notice.name)
    sync_notice_details(notice)
    ensure_stock_entry(notice.name)
    ensure_inventory_snapshots()
    ensure_shipment_request()
    ensure_client_instruction(notice.name)
    ensure_additional_alpha_portal_data()

    frappe.db.commit()
    frappe.clear_cache()
