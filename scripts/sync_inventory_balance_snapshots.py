import hashlib
import json

import frappe
from frappe.utils import now, nowdate


def snapshot_key(row, snapshot_date):
    return {
        "snapshot_date": snapshot_date,
        "source_snapshot": row.name,
    }


def sync_balance_snapshot(row, snapshot_date, captured_at):
    key = snapshot_key(row, snapshot_date)
    existing = frappe.db.get_value("Three PL Inventory Balance Snapshot", key, "name")
    doc = frappe.get_doc("Three PL Inventory Balance Snapshot", existing) if existing else frappe.new_doc("Three PL Inventory Balance Snapshot")
    if not existing:
        digest = hashlib.sha1(json.dumps(key, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:12]
        doc.name = f"INV-BAL-{snapshot_date}-{digest}"
        doc.flags.name_set = True

    doc.snapshot_date = snapshot_date
    doc.customer = row.customer
    doc.item_code = row.item_code
    doc.client_sku = row.client_sku
    doc.item_name = row.item_name
    doc.qty = row.qty
    doc.uom = row.uom
    doc.warehouse = row.warehouse
    doc.container_code = row.container_code
    doc.status = row.status
    doc.source_snapshot = row.name
    doc.captured_at = captured_at
    doc.notes = f"Daily balance copied from current inventory snapshot {row.name}."
    doc.save(ignore_permissions=True)
    return doc.name


def sync_inventory_balance_snapshots():
    snapshot_date = nowdate()
    captured_at = now()
    synced = []
    for stale_name in frappe.get_all("Three PL Inventory Balance Snapshot", filters={"snapshot_date": snapshot_date}, pluck="name"):
        frappe.delete_doc("Three PL Inventory Balance Snapshot", stale_name, ignore_permissions=True, force=True)

    for row in frappe.get_all(
        "Three PL Inventory Snapshot",
        fields=[
            "name",
            "customer",
            "item_code",
            "client_sku",
            "item_name",
            "qty",
            "uom",
            "warehouse",
            "container_code",
            "status",
        ],
        order_by="customer asc, item_code asc, container_code asc",
    ):
        synced.append(sync_balance_snapshot(row, snapshot_date, captured_at))
    return synced


def main():
    synced = sync_inventory_balance_snapshots()
    frappe.db.commit()
    print(f"Synced inventory balance snapshots: {len(synced)}")


if __name__ == "__main__":
    main()
