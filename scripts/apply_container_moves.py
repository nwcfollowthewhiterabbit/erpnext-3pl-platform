import frappe
from frappe.utils import now


def create_movement_for_move(move):
    movement = frappe.new_doc("Three PL Container Movement")
    movement.movement_datetime = move.operation_datetime or now()
    movement.container_code = move.container_code
    movement.client = move.client
    movement.movement_type = "Moved"
    movement.from_warehouse = move.from_warehouse
    movement.to_warehouse = move.to_warehouse
    movement.reference_doctype = "Three PL Container Move"
    movement.reference_name = move.name
    movement.notes = f"Applied from container move {move.operation_reference or move.name}."
    movement.save(ignore_permissions=True)
    return movement


def apply_move(move):
    container = frappe.get_doc("Three PL Container", move.container_code)

    if container.client != move.client:
        raise RuntimeError(f"Container {move.container_code} belongs to {container.client}, not {move.client}")
    if container.current_warehouse != move.from_warehouse:
        raise RuntimeError(
            f"Container {move.container_code} is at {container.current_warehouse}, not {move.from_warehouse}"
        )
    if move.from_warehouse == move.to_warehouse:
        raise RuntimeError(f"Container move {move.name} has identical source and target locations")

    movement = create_movement_for_move(move)

    container.current_warehouse = move.to_warehouse
    container.last_moved_at = movement.movement_datetime
    if container.status not in {"Shipped", "Closed", "Replaced"}:
        container.status = "Stored"
    container.save(ignore_permissions=True)

    move.status = "Applied"
    move.movement = movement.name
    move.save(ignore_permissions=True)
    return movement


def apply_pending_moves():
    applied = []
    for move_name in frappe.get_all("Three PL Container Move", filters={"status": "Draft"}, pluck="name"):
        move = frappe.get_doc("Three PL Container Move", move_name)
        applied.append(apply_move(move).name)
    return applied


def main():
    applied = apply_pending_moves()
    frappe.db.commit()
    print(f"Applied container moves: {len(applied)}")
    for movement_name in applied:
        print(movement_name)


if __name__ == "__main__":
    main()
