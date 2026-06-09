import frappe
from frappe.utils import now


ACTIVE_CONTAINER_STATUSES = {"Received", "In Verification", "Ready for Putaway", "Stored", "Picking", "Picked", "Packed"}
SNAPSHOT_STATUS_BY_CONTAINER_STATUS = {
    "Received": "Receiving",
    "In Verification": "Receiving",
    "Ready for Putaway": "Receiving",
    "Stored": "Available",
    "Picking": "Allocated",
    "Picked": "Allocated",
    "Packed": "Allocated",
}


def snapshot_name(customer, item_code, container_code):
    return frappe.db.get_value(
        "Three PL Inventory Snapshot",
        {"customer": customer, "item_code": item_code, "container_code": container_code},
        "name",
    )


def sync_snapshot(container, item_row):
    existing = snapshot_name(container.client, item_row.item_code, container.name)
    doc = frappe.get_doc("Three PL Inventory Snapshot", existing) if existing else frappe.new_doc("Three PL Inventory Snapshot")
    item_name = frappe.db.get_value("Item", item_row.item_code, "item_name") or item_row.item_code

    doc.customer = container.client
    doc.item_code = item_row.item_code
    doc.client_sku = item_row.client_sku
    doc.item_name = item_name
    doc.qty = item_row.qty
    doc.uom = item_row.uom
    doc.warehouse = container.current_warehouse
    doc.container_code = container.name
    doc.status = SNAPSHOT_STATUS_BY_CONTAINER_STATUS.get(container.status, "Available")
    doc.last_updated = now()
    doc.notes = f"Synced from active container {container.name}."
    doc.save(ignore_permissions=True)
    return doc.name


def delete_stale_snapshots(active_keys):
    deleted = []
    for row in frappe.get_all("Three PL Inventory Snapshot", fields=["name", "customer", "item_code", "container_code"]):
        key = (row.customer, row.item_code, row.container_code)
        if row.container_code and key not in active_keys:
            frappe.delete_doc("Three PL Inventory Snapshot", row.name, ignore_permissions=True, force=True)
            deleted.append(row.name)
    return deleted


def sync_inventory_snapshots():
    active_keys = set()
    synced = []
    for container_name in frappe.get_all("Three PL Container", filters={"status": ("in", sorted(ACTIVE_CONTAINER_STATUSES))}, pluck="name"):
        container = frappe.get_doc("Three PL Container", container_name)
        if not container.current_warehouse:
            continue
        for item_row in container.items:
            active_keys.add((container.client, item_row.item_code, container.name))
            synced.append(sync_snapshot(container, item_row))
    deleted = delete_stale_snapshots(active_keys)
    return synced, deleted


def main():
    synced, deleted = sync_inventory_snapshots()
    frappe.db.commit()
    print(f"Synced inventory snapshots: {len(synced)}")
    print(f"Deleted stale inventory snapshots: {len(deleted)}")


if __name__ == "__main__":
    main()
