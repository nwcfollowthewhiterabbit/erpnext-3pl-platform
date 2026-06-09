import csv
import sys
from pathlib import Path

import frappe


def as_bool(value):
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def require(value, message):
    if not value:
        raise RuntimeError(message)
    return value


def ensure_warehouse(row):
    warehouse_name = require(row.get("warehouse_name"), "warehouse_name is required").strip()
    parent_warehouse = require(row.get("parent_warehouse"), f"parent_warehouse is required for {warehouse_name}").strip()
    is_group = 1 if as_bool(row.get("is_group")) else 0
    description = (row.get("description") or "").strip()

    company = frappe.db.get_value("Warehouse", parent_warehouse, "company")
    require(company, f"Parent warehouse does not exist or has no company: {parent_warehouse}")

    if frappe.db.exists("Warehouse", {"warehouse_name": warehouse_name, "parent_warehouse": parent_warehouse}):
        warehouse_name_full = frappe.db.get_value(
            "Warehouse",
            {"warehouse_name": warehouse_name, "parent_warehouse": parent_warehouse},
            "name",
        )
        warehouse = frappe.get_doc("Warehouse", warehouse_name_full)
    else:
        warehouse = frappe.new_doc("Warehouse")
        warehouse.warehouse_name = warehouse_name
        warehouse.parent_warehouse = parent_warehouse
        warehouse.company = company

    warehouse.is_group = is_group
    if description and warehouse.meta.has_field("warehouse_description"):
        warehouse.warehouse_description = description
    warehouse.save(ignore_permissions=True)
    return warehouse.name


def main():
    csv_path = Path(sys.argv[4] if len(sys.argv) > 4 else "/tmp/warehouse-locations.csv")
    if not csv_path.exists():
        raise RuntimeError(f"CSV file not found: {csv_path}")

    created_or_updated = []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if not any(row.values()):
                continue
            created_or_updated.append(ensure_warehouse(row))

    frappe.db.commit()
    print(f"Imported warehouse locations: {len(created_or_updated)}")
    for name in created_or_updated:
        print(name)


if __name__ == "__main__":
    main()
