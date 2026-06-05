import frappe
from frappe.utils import now


def item_qty_key(row):
    return (row.item_code, row.uom, row.condition_status or "OK")


def sum_container_items(containers):
    totals = {}
    for container in containers:
        for row in container.items:
            key = item_qty_key(row)
            totals[key] = totals.get(key, 0) + row.qty
    return totals


def sum_repack_items(repack):
    totals = {}
    for row in repack.items:
        key = item_qty_key(row)
        totals[key] = totals.get(key, 0) + row.qty
    return totals


def validate_repack_quantities(repack, source_containers):
    source_totals = sum_container_items(source_containers)
    target_totals = sum_repack_items(repack)
    if source_totals != target_totals:
        raise RuntimeError(
            f"Container repack {repack.name} quantity mismatch: source={source_totals}, target={target_totals}"
        )


def create_movement_for_repack(repack):
    source_names = [row.source_container for row in repack.source_containers]
    movement = frappe.new_doc("Three PL Container Movement")
    movement.movement_datetime = repack.operation_datetime or now()
    movement.container_code = repack.target_container
    movement.client = repack.client
    movement.movement_type = "Repacked"
    movement.to_warehouse = repack.target_location
    movement.from_container = source_names[0] if source_names else None
    movement.to_container = repack.target_container
    movement.reference_doctype = "Three PL Container Repack"
    movement.reference_name = repack.name
    movement.notes = f"Applied from container repack {repack.operation_reference or repack.name}."
    movement.save(ignore_permissions=True)
    return movement


def apply_repack(repack):
    if not repack.source_containers:
        raise RuntimeError(f"Container repack {repack.name} has no source containers")
    if not repack.items:
        raise RuntimeError(f"Container repack {repack.name} has no resulting items")

    source_containers = [frappe.get_doc("Three PL Container", row.source_container) for row in repack.source_containers]
    for container in source_containers:
        if container.client != repack.client:
            raise RuntimeError(f"Source container {container.name} belongs to {container.client}, not {repack.client}")
        if container.status in {"Shipped", "Closed", "Replaced"}:
            raise RuntimeError(f"Source container {container.name} cannot be repacked from status {container.status}")
    validate_repack_quantities(repack, source_containers)

    if frappe.db.exists("Three PL Container", repack.target_container):
        target = frappe.get_doc("Three PL Container", repack.target_container)
    else:
        target = frappe.new_doc("Three PL Container")
        target.container_code = repack.target_container

    if target.name not in {None, repack.target_container} and target.client and target.client != repack.client:
        raise RuntimeError(f"Target container {target.name} belongs to {target.client}, not {repack.client}")

    movement = create_movement_for_repack(repack)

    target.barcode = target.barcode or repack.target_container
    target.container_type = target.container_type or "Box"
    target.client = repack.client
    target.current_warehouse = repack.target_location
    target.status = "Stored"
    target.last_moved_at = movement.movement_datetime
    target.notes = f"Created or updated by repack {repack.operation_reference or repack.name}."
    target.set("items", [])
    for row in repack.items:
        target.append(
            "items",
            {
                "item_code": row.item_code,
                "client_sku": row.client_sku,
                "qty": row.qty,
                "uom": row.uom,
                "condition_status": row.condition_status,
                "notes": row.notes,
            },
        )
    target.save(ignore_permissions=True)

    for container in source_containers:
        container.status = "Replaced"
        container.replaced_by = target.name
        container.last_moved_at = movement.movement_datetime
        container.save(ignore_permissions=True)

    repack.status = "Applied"
    repack.movement = movement.name
    repack.save(ignore_permissions=True)
    return movement


def apply_pending_repacks():
    applied = []
    for repack_name in frappe.get_all("Three PL Container Repack", filters={"status": "Draft"}, pluck="name"):
        repack = frappe.get_doc("Three PL Container Repack", repack_name)
        applied.append(apply_repack(repack).name)
    return applied


def main():
    applied = apply_pending_repacks()
    frappe.db.commit()
    print(f"Applied container repacks: {len(applied)}")
    for movement_name in applied:
        print(movement_name)


main()
