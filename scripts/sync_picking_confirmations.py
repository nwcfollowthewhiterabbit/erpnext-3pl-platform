import frappe
from frappe.utils import now


def picked_rows(pick_list):
    return [
        row
        for row in pick_list.locations
        if row.container_code and (row.picked_qty or 0) >= (row.stock_qty or row.qty or 0) and (row.stock_qty or row.qty or 0) > 0
    ]


def movement_exists(container_name, pick_list_name):
    return frappe.db.exists(
        "Three PL Container Movement",
        {
            "container_code": container_name,
            "movement_type": "Picked",
            "reference_doctype": "Pick List",
            "reference_name": pick_list_name,
        },
    )


def create_picked_movement(container, pick_list):
    movement = frappe.new_doc("Three PL Container Movement")
    movement.movement_datetime = now()
    movement.container_code = container.name
    movement.client = container.client
    movement.movement_type = "Picked"
    movement.from_warehouse = container.current_warehouse
    movement.to_warehouse = container.current_warehouse
    movement.reference_doctype = "Pick List"
    movement.reference_name = pick_list.name
    movement.notes = f"Picked for shipment request {pick_list.shipment_reference or pick_list.shipment_request}."
    movement.save(ignore_permissions=True)
    return movement


def sync_pick_list(pick_list_name):
    pick_list = frappe.get_doc("Pick List", pick_list_name)
    synced = []
    for container_name in sorted({row.container_code for row in picked_rows(pick_list)}):
        container = frappe.get_doc("Three PL Container", container_name)
        if container.status in {"Shipped", "Closed", "Replaced"}:
            continue
        if not movement_exists(container.name, pick_list.name):
            create_picked_movement(container, pick_list)
        container.status = "Picked"
        container.last_moved_at = now()
        container.save(ignore_permissions=True)
        synced.append(container.name)
    return synced


def sync_picking_confirmations():
    synced = []
    for pick_list_name in frappe.get_all(
        "Pick List",
        filters={"shipment_request": ("is", "set"), "docstatus": ("<", 2)},
        pluck="name",
    ):
        synced.extend(sync_pick_list(pick_list_name))
    return sorted(set(synced))


def main():
    synced = sync_picking_confirmations()
    frappe.db.commit()
    print(f"Synced picking confirmations: {len(synced)}")
    for container_name in synced:
        print(container_name)


main()
