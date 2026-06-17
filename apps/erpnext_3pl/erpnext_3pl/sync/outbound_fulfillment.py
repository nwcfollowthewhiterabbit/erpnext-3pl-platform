import frappe
from frappe.utils import now


FLOW_STATUS = {
    "Packing": ("Packed", "Packed"),
    "Shipping": ("Shipped", "Shipped"),
}


def request_from_entry(entry):
    if entry.shipment_request:
        return entry.shipment_request
    if entry.shipment_reference:
        return frappe.db.get_value(
            "Three PL Shipment Request",
            {"customer": entry.client, "external_reference": entry.shipment_reference},
            "name",
        )
    return None


def entry_containers(entry):
    containers = {entry.container_code} if entry.container_code else set()
    containers.update(row.container_code for row in entry.items if row.container_code)
    return sorted(container for container in containers if container)


def movement_exists(container_name, movement_type, entry_name):
    return frappe.db.exists(
        "Three PL Container Movement",
        {
            "container_code": container_name,
            "movement_type": movement_type,
            "reference_doctype": "Stock Entry",
            "reference_name": entry_name,
        },
    )


def movement_locations(entry):
    from_warehouse = None
    to_warehouse = None
    for row in entry.items:
        from_warehouse = from_warehouse or row.s_warehouse
        to_warehouse = to_warehouse or row.t_warehouse
    return from_warehouse, to_warehouse


def create_movement(entry, container, movement_type):
    from_warehouse, to_warehouse = movement_locations(entry)
    movement = frappe.new_doc("Three PL Container Movement")
    movement.movement_datetime = now()
    movement.container_code = container.name
    movement.client = container.client
    movement.movement_type = movement_type
    movement.from_warehouse = from_warehouse
    movement.to_warehouse = to_warehouse
    movement.reference_doctype = "Stock Entry"
    movement.reference_name = entry.name
    movement.notes = f"Synced from {entry.stock_entry_type or entry.name} for shipment {entry.shipment_reference or entry.shipment_request}."
    movement.save(ignore_permissions=True)
    return movement


def sync_container(entry, container_name, container_status, movement_type):
    container = frappe.get_doc("Three PL Container", container_name)
    if entry.client and container.client != entry.client:
        raise RuntimeError(f"Container {container.name} belongs to {container.client}, not {entry.client}")

    if not movement_exists(container.name, movement_type, entry.name):
        create_movement(entry, container, movement_type)

    _from_warehouse, to_warehouse = movement_locations(entry)
    if to_warehouse:
        container.current_warehouse = to_warehouse
    container.status = container_status
    container.last_moved_at = now()
    container.save(ignore_permissions=True)


def sync_entry(entry_name):
    entry = frappe.get_doc("Stock Entry", entry_name)
    if entry.docstatus != 1 or entry.warehouse_flow not in FLOW_STATUS:
        return None

    request_name = request_from_entry(entry)
    if not request_name:
        return None

    request_status, container_status = FLOW_STATUS[entry.warehouse_flow]
    for container_name in entry_containers(entry):
        sync_container(entry, container_name, container_status, request_status)

    request = frappe.get_doc("Three PL Shipment Request", request_name)
    request.status = request_status
    request.save(ignore_permissions=True)
    return request.name


def sync_outbound_fulfillment():
    synced = []
    for entry_name in frappe.get_all(
        "Stock Entry",
        filters={
            "docstatus": 1,
            "warehouse_flow": ("in", sorted(FLOW_STATUS)),
        },
        pluck="name",
    ):
        request_name = sync_entry(entry_name)
        if request_name:
            synced.append(request_name)
    return sorted(set(synced))


def main():
    synced = sync_outbound_fulfillment()
    frappe.db.commit()
    print(f"Synced outbound fulfillment requests: {len(synced)}")
    for request_name in synced:
        print(request_name)


if __name__ == "__main__":
    main()
