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


def validate_partial_split_quantities(repack, source_container):
    source_totals = sum_container_items([source_container])
    target_totals = sum_repack_items(repack)
    for key, qty in target_totals.items():
        if qty <= 0:
            raise RuntimeError(f"Container repack {repack.name} has non-positive split qty for {key}: {qty}")
        if source_totals.get(key, 0) < qty:
            raise RuntimeError(
                f"Container repack {repack.name} split quantity exceeds source for {key}: source={source_totals.get(key, 0)}, split={qty}"
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


def row_key_values(row):
    return (row.item_code, row.uom, row.condition_status or "OK")


def append_or_increment_item(container, row, qty):
    for target_row in container.items:
        if row_key_values(target_row) == row_key_values(row):
            target_row.qty = (target_row.qty or 0) + qty
            return
    container.append(
        "items",
        {
            "item_code": row.item_code,
            "client_sku": row.client_sku,
            "qty": qty,
            "uom": row.uom,
            "condition_status": row.condition_status,
            "notes": row.notes,
        },
    )


def subtract_item_qty(container, split_row):
    remaining_to_split = split_row.qty or 0
    kept_rows = []
    for source_row in container.items:
        if row_key_values(source_row) != row_key_values(split_row):
            kept_rows.append(source_row.as_dict())
            continue
        available_qty = source_row.qty or 0
        split_qty = min(available_qty, remaining_to_split)
        remaining_qty = available_qty - split_qty
        remaining_to_split -= split_qty
        if remaining_qty > 0:
            updated = source_row.as_dict()
            updated["qty"] = remaining_qty
            kept_rows.append(updated)
    if remaining_to_split > 0:
        raise RuntimeError(f"Source container {container.name} does not have enough {split_row.item_code} to split")
    container.set("items", [])
    for kept_row in kept_rows:
        container.append("items", kept_row)


def apply_partial_split(repack, source_container, target, movement):
    target.barcode = target.barcode or repack.target_container
    target.container_type = target.container_type or "Box"
    target.client = repack.client
    target.current_warehouse = repack.target_location
    target.status = "Stored"
    target.last_moved_at = movement.movement_datetime
    target.notes = f"Created or updated by partial split {repack.operation_reference or repack.name}."

    for row in repack.items:
        subtract_item_qty(source_container, row)
        append_or_increment_item(target, row, row.qty)

    source_container.status = "Stored" if source_container.items else "Empty"
    source_container.last_moved_at = movement.movement_datetime
    source_container.save(ignore_permissions=True)
    target.save(ignore_permissions=True)


def apply_full_consolidation(repack, source_containers, target, movement):
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
    repack_mode = repack.repack_mode or "Full Consolidation"
    if repack_mode == "Partial Split":
        if len(source_containers) != 1:
            raise RuntimeError(f"Partial split repack {repack.name} must have exactly one source container")
        validate_partial_split_quantities(repack, source_containers[0])
    else:
        validate_repack_quantities(repack, source_containers)

    if frappe.db.exists("Three PL Container", repack.target_container):
        target = frappe.get_doc("Three PL Container", repack.target_container)
    else:
        target = frappe.new_doc("Three PL Container")
        target.container_code = repack.target_container

    if target.name not in {None, repack.target_container} and target.client and target.client != repack.client:
        raise RuntimeError(f"Target container {target.name} belongs to {target.client}, not {repack.client}")

    movement = create_movement_for_repack(repack)
    if repack_mode == "Partial Split":
        apply_partial_split(repack, source_containers[0], target, movement)
    else:
        apply_full_consolidation(repack, source_containers, target, movement)

    repack.status = "Applied"
    repack.movement = movement.name
    repack.save(ignore_permissions=True)
    return movement


def apply_pending_repacks():
    applied = []
    skipped = []
    for repack_name in frappe.get_all("Three PL Container Repack", filters={"status": "Draft"}, pluck="name"):
        repack = frappe.get_doc("Three PL Container Repack", repack_name)
        try:
            applied.append(apply_repack(repack).name)
        except Exception as exc:
            repack.status = "Needs Review"
            message = f"Automatic repack apply failed: {exc}"
            repack.notes = f"{repack.notes}\n{message}".strip() if repack.notes else message
            repack.save(ignore_permissions=True)
            skipped.append((repack.name, message))
    return applied, skipped


def main():
    applied, skipped = apply_pending_repacks()
    frappe.db.commit()
    print(f"Applied container repacks: {len(applied)}")
    for movement_name in applied:
        print(movement_name)
    print(f"Skipped container repacks needing review: {len(skipped)}")
    for repack_name, message in skipped:
        print(f"{repack_name}: {message}")


if __name__ == "__main__":
    main()
