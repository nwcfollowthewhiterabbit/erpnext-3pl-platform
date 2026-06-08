import frappe
from frappe.utils import now


OPEN_REQUEST_STATUSES = {"Submitted", "Accepted", "Picking"}


def existing_pick_list(request):
    return frappe.db.get_value("Pick List", {"shipment_request": request.name}, "name") or frappe.db.get_value(
        "Pick List",
        {"client": request.customer, "shipment_reference": request.external_reference},
        "name",
    )


def available_inventory(customer, item_code):
    return frappe.get_all(
        "Three PL Inventory Snapshot",
        filters={
            "customer": customer,
            "item_code": item_code,
            "status": "Available",
            "qty": (">", 0),
        },
        fields=["warehouse", "container_code", "qty", "uom"],
        order_by="warehouse asc, container_code asc",
    )


def allocate_item(customer, item_row):
    remaining_qty = item_row.qty or 0
    allocations = []
    for snapshot in available_inventory(customer, item_row.item_code):
        if remaining_qty <= 0:
            break
        pick_qty = min(remaining_qty, snapshot.qty or 0)
        if pick_qty <= 0:
            continue
        allocations.append(
            {
                "item_code": item_row.item_code,
                "item_name": frappe.db.get_value("Item", item_row.item_code, "item_name") or item_row.item_code,
                "description": frappe.db.get_value("Item", item_row.item_code, "description") or item_row.item_code,
                "warehouse": snapshot.warehouse,
                "scanned_location": snapshot.warehouse,
                "container_code": snapshot.container_code,
                "qty": pick_qty,
                "stock_qty": pick_qty,
                "picked_qty": 0,
                "uom": item_row.uom,
                "stock_uom": item_row.uom,
                "conversion_factor": 1,
            }
        )
        remaining_qty -= pick_qty

    if remaining_qty > 0:
        raise RuntimeError(
            f"Shipment request {item_row.parent} cannot allocate {item_row.item_code}: missing {remaining_qty} {item_row.uom or ''}".strip()
        )
    return allocations


def build_allocations(request):
    if not request.items:
        raise RuntimeError(f"Shipment request {request.name} has no structured item rows")

    allocations = []
    for item_row in request.items:
        allocations.extend(allocate_item(request.customer, item_row))
    return allocations


def ensure_pick_list(request):
    pick_list_name = existing_pick_list(request)
    pick_list = frappe.get_doc("Pick List", pick_list_name) if pick_list_name else frappe.new_doc("Pick List")
    if pick_list.docstatus != 0:
        return pick_list

    allocations = build_allocations(request)
    pick_list.purpose = "Delivery"
    pick_list.pick_manually = 1
    pick_list.customer = request.customer
    pick_list.client = request.customer
    pick_list.shipment_reference = request.external_reference
    pick_list.shipment_request = request.name
    pick_list.set("locations", [])
    for row in allocations:
        pick_list.append("locations", row)
    pick_list.save(ignore_permissions=True)
    return pick_list


def create_picking_movement(container, pick_list):
    movement = frappe.new_doc("Three PL Container Movement")
    movement.movement_datetime = now()
    movement.container_code = container.name
    movement.client = container.client
    movement.movement_type = "Picking"
    movement.from_warehouse = container.current_warehouse
    movement.to_warehouse = container.current_warehouse
    movement.reference_doctype = "Pick List"
    movement.reference_name = pick_list.name
    movement.notes = f"Allocated for shipment request {pick_list.shipment_reference or pick_list.shipment_request}."
    movement.save(ignore_permissions=True)
    return movement


def mark_allocated_containers(pick_list):
    movements = []
    container_names = sorted({row.container_code for row in pick_list.locations if row.container_code})
    for container_name in container_names:
        container = frappe.get_doc("Three PL Container", container_name)
        if container.status in {"Shipped", "Closed", "Replaced"}:
            raise RuntimeError(f"Container {container.name} cannot be picked from status {container.status}")
        if not frappe.db.exists(
            "Three PL Container Movement",
            {
                "container_code": container.name,
                "movement_type": "Picking",
                "reference_doctype": "Pick List",
                "reference_name": pick_list.name,
            },
        ):
            movements.append(create_picking_movement(container, pick_list).name)
        container.status = "Picking"
        container.last_moved_at = now()
        container.save(ignore_permissions=True)
    return movements


def append_request_note(request, message):
    if message in (request.notes or ""):
        return
    request.notes = f"{request.notes}\n{message}".strip() if request.notes else message
    request.save(ignore_permissions=True)


def sync_request(request_name):
    request = frappe.get_doc("Three PL Shipment Request", request_name)
    if request.status not in OPEN_REQUEST_STATUSES:
        return None

    try:
        pick_list = ensure_pick_list(request)
        mark_allocated_containers(pick_list)
    except Exception as exc:
        append_request_note(request, f"Automatic pick allocation failed: {exc}")
        return None

    request.status = "Picking"
    request.save(ignore_permissions=True)
    return pick_list.name


def sync_shipment_requests():
    synced = []
    for request_name in frappe.get_all(
        "Three PL Shipment Request",
        filters={"status": ("in", sorted(OPEN_REQUEST_STATUSES))},
        pluck="name",
    ):
        pick_list_name = sync_request(request_name)
        if pick_list_name:
            synced.append(pick_list_name)
    return synced


def main():
    synced = sync_shipment_requests()
    frappe.db.commit()
    print(f"Synced shipment requests: {len(synced)}")
    for pick_list_name in synced:
        print(pick_list_name)


main()
