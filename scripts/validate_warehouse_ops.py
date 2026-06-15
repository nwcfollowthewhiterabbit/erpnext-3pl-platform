import frappe
from frappe.desk.query_report import run as run_query_report
from frappe.utils import now_datetime, nowdate

from project_config import CLIENT_PORTAL_CUSTOMER, COMPANY, WAREHOUSE_MANAGER_USER
from validate_site import (
    REQUIRED_REPORTS,
    require,
    validate_outbound_fulfillment,
    validate_partial_repack,
    validate_picking_confirmation,
    validate_putaway_operation,
    validate_stocktake,
    validate_warehouse_correction,
    validate_warehouse_correction_stock_posting,
)


def cancel_and_delete(doctype, name):
    if not name or not frappe.db.exists(doctype, name):
        return
    doc = frappe.get_doc(doctype, name)
    if getattr(doc, "docstatus", 0) == 1:
        doc.cancel()
    frappe.delete_doc(doctype, name, ignore_permissions=True, force=True)


def cleanup_by_container(container_names):
    frappe.set_user("Administrator")
    for entry_name in frappe.get_all(
        "Stock Entry",
        filters=[["Stock Entry", "remarks", "like", "WAREHOUSE-OPS-%"]],
        pluck="name",
        order_by="creation desc",
    ):
        cancel_and_delete("Stock Entry", entry_name)
    for correction_name in frappe.get_all("Three PL Warehouse Correction", filters={"container_code": ("in", container_names)}, pluck="name"):
        linked_entries = frappe.get_all("Stock Entry", filters={"warehouse_correction": correction_name}, pluck="name", order_by="creation desc")
        for entry_name in linked_entries:
            cancel_and_delete("Stock Entry", entry_name)
    for doctype in ("Three PL Container Movement", "Three PL Container Move", "Three PL Warehouse Correction"):
        for name in frappe.get_all(doctype, filters={"container_code": ("in", container_names)}, pluck="name"):
            cancel_and_delete(doctype, name)
    for repack_name in frappe.get_all("Three PL Container Repack", filters={"operation_reference": ("like", "WAREHOUSE-OPS-%")}, pluck="name"):
        cancel_and_delete("Three PL Container Repack", repack_name)
    for container_name in container_names:
        cancel_and_delete("Three PL Container", container_name)
    frappe.db.commit()


def seed_container(container_name, warehouse, qty=5, item_code="SKU-ALPHA-001"):
    doc = frappe.get_doc(
        {
            "doctype": "Three PL Container",
            "container_code": container_name,
            "barcode": container_name,
            "container_type": "Box",
            "client": CLIENT_PORTAL_CUSTOMER,
            "current_warehouse": warehouse,
            "status": "Stored",
            "items": [
                {
                    "item_code": item_code,
                    "client_sku": frappe.db.get_value("Item", item_code, "client_sku") or "ALPHA-001",
                    "qty": qty,
                    "uom": "Nos",
                    "condition_status": "OK",
                }
            ],
        }
    )
    doc.insert(ignore_permissions=True)
    return doc


def validate_container_move():
    processor = __import__("apply_container_moves")
    containers = ["WAREHOUSE-OPS-MOVE-BOX"]
    cleanup_by_container(containers)

    seed_container("WAREHOUSE-OPS-MOVE-BOX", "Aisle A - 3", qty=2)

    frappe.set_user(WAREHOUSE_MANAGER_USER)
    move = frappe.get_doc(
        {
            "doctype": "Three PL Container Move",
            "operation_reference": "WAREHOUSE-OPS-MOVE",
            "operation_datetime": now_datetime(),
            "status": "Draft",
            "container_code": "WAREHOUSE-OPS-MOVE-BOX",
            "client": CLIENT_PORTAL_CUSTOMER,
            "from_warehouse": "Aisle A - 3",
            "to_warehouse": "Aisle B - 3",
            "notes": "Warehouse ops validation move.",
        }
    )
    move.insert()

    frappe.set_user("Administrator")
    movement = processor.apply_move(move)
    container = frappe.get_doc("Three PL Container", "WAREHOUSE-OPS-MOVE-BOX")
    move.reload()
    require(container.current_warehouse == "Aisle B - 3", "Container move did not update current warehouse")
    require(container.status == "Stored", "Container move did not leave container stored")
    require(move.status == "Applied", "Container move was not applied")
    require(move.movement == movement.name, "Container move is not linked to movement")

    cleanup_by_container(containers)


def validate_full_repack():
    processor = __import__("apply_container_repacks")
    containers = ["WAREHOUSE-OPS-REPACK-SRC-1", "WAREHOUSE-OPS-REPACK-SRC-2", "WAREHOUSE-OPS-REPACK-TARGET"]
    cleanup_by_container(containers)

    seed_container("WAREHOUSE-OPS-REPACK-SRC-1", "Aisle A - 3", qty=2)
    seed_container("WAREHOUSE-OPS-REPACK-SRC-2", "Aisle B - 3", qty=3)
    frappe.get_doc(
        {
            "doctype": "Three PL Container",
            "container_code": "WAREHOUSE-OPS-REPACK-TARGET",
            "barcode": "WAREHOUSE-OPS-REPACK-TARGET",
            "container_type": "Box",
            "client": CLIENT_PORTAL_CUSTOMER,
            "current_warehouse": "Aisle B - 3",
            "status": "Stored",
        }
    ).insert(ignore_permissions=True)

    repack = frappe.get_doc(
        {
            "doctype": "Three PL Container Repack",
            "operation_reference": "WAREHOUSE-OPS-FULL-REPACK",
            "operation_datetime": now_datetime(),
            "status": "Draft",
            "repack_mode": "Full Consolidation",
            "client": CLIENT_PORTAL_CUSTOMER,
            "target_container": "WAREHOUSE-OPS-REPACK-TARGET",
            "target_location": "Aisle B - 3",
            "source_containers": [
                {"source_container": "WAREHOUSE-OPS-REPACK-SRC-1", "source_location": "Aisle A - 3"},
                {"source_container": "WAREHOUSE-OPS-REPACK-SRC-2", "source_location": "Aisle B - 3"},
            ],
            "items": [
                {
                    "item_code": "SKU-ALPHA-001",
                    "client_sku": "ALPHA-001",
                    "qty": 5,
                    "uom": "Nos",
                    "condition_status": "OK",
                }
            ],
            "notes": "Warehouse ops validation full consolidation.",
        }
    )
    repack.insert(ignore_permissions=True)

    movement = processor.apply_repack(repack)
    target = frappe.get_doc("Three PL Container", "WAREHOUSE-OPS-REPACK-TARGET")
    source_1 = frappe.get_doc("Three PL Container", "WAREHOUSE-OPS-REPACK-SRC-1")
    source_2 = frappe.get_doc("Three PL Container", "WAREHOUSE-OPS-REPACK-SRC-2")
    repack.reload()
    require(repack.status == "Applied", "Full repack was not applied")
    require(repack.movement == movement.name, "Full repack is not linked to movement")
    require(target.items[0].qty == 5, "Full repack target quantity is wrong")
    require(source_1.status == "Replaced" and source_2.status == "Replaced", "Full repack sources were not replaced")
    require(source_1.replaced_by == target.name and source_2.replaced_by == target.name, "Full repack sources are not linked to target")

    cleanup_by_container(containers)


def validate_repack_needs_review():
    processor = __import__("apply_container_repacks")
    containers = ["WAREHOUSE-OPS-REPACK-BAD-SRC", "WAREHOUSE-OPS-REPACK-BAD-TARGET"]
    cleanup_by_container(containers)

    seed_container("WAREHOUSE-OPS-REPACK-BAD-SRC", "Aisle A - 3", qty=1)
    frappe.get_doc(
        {
            "doctype": "Three PL Container",
            "container_code": "WAREHOUSE-OPS-REPACK-BAD-TARGET",
            "barcode": "WAREHOUSE-OPS-REPACK-BAD-TARGET",
            "container_type": "Box",
            "client": CLIENT_PORTAL_CUSTOMER,
            "current_warehouse": "Aisle B - 3",
            "status": "Stored",
        }
    ).insert(ignore_permissions=True)
    repack = frappe.get_doc(
        {
            "doctype": "Three PL Container Repack",
            "operation_reference": "WAREHOUSE-OPS-BAD-REPACK",
            "operation_datetime": now_datetime(),
            "status": "Draft",
            "repack_mode": "Partial Split",
            "client": CLIENT_PORTAL_CUSTOMER,
            "target_container": "WAREHOUSE-OPS-REPACK-BAD-TARGET",
            "target_location": "Aisle B - 3",
            "source_containers": [{"source_container": "WAREHOUSE-OPS-REPACK-BAD-SRC", "source_location": "Aisle A - 3"}],
            "items": [
                {
                    "item_code": "SKU-ALPHA-001",
                    "client_sku": "ALPHA-001",
                    "qty": 2,
                    "uom": "Nos",
                    "condition_status": "OK",
                }
            ],
        }
    )
    repack.insert(ignore_permissions=True)
    _applied, skipped = processor.apply_pending_repacks()
    repack.reload()
    require(skipped and repack.status == "Needs Review", "Invalid repack was not moved to Needs Review")
    require("exceeds source" in (repack.notes or ""), "Invalid repack does not explain the quantity issue")

    cleanup_by_container(containers)


def submit_stock_receipt_for_correction(container_name, item_code, qty, warehouse):
    entry = frappe.get_doc(
        {
            "doctype": "Stock Entry",
            "stock_entry_type": "3PL Quantity Gain",
            "purpose": "Material Receipt",
            "company": COMPANY,
            "posting_date": nowdate(),
            "client": CLIENT_PORTAL_CUSTOMER,
            "warehouse_flow": "Warehouse Correction",
            "scanned_location": warehouse,
            "container_code": container_name,
            "remarks": f"WAREHOUSE-OPS seed stock for correction {container_name}",
            "items": [
                {
                    "item_code": item_code,
                    "qty": qty,
                    "t_warehouse": warehouse,
                    "uom": "Nos",
                    "stock_uom": "Nos",
                    "conversion_factor": 1,
                    "basic_rate": 1,
                    "container_code": container_name,
                }
            ],
        }
    )
    entry.insert(ignore_permissions=True)
    entry.submit()
    return entry


def validate_correction_loss_and_noop():
    processor = __import__("apply_warehouse_corrections")
    containers = ["WAREHOUSE-OPS-CORR-LOSS", "WAREHOUSE-OPS-CORR-NOOP"]
    cleanup_by_container(containers)
    seed_container("WAREHOUSE-OPS-CORR-LOSS", "Aisle B - 3", qty=3)
    seed_container("WAREHOUSE-OPS-CORR-NOOP", "Aisle B - 3", qty=3)
    submit_stock_receipt_for_correction("WAREHOUSE-OPS-CORR-LOSS", "SKU-ALPHA-001", 3, "Aisle B - 3")

    loss = frappe.get_doc(
        {
            "doctype": "Three PL Warehouse Correction",
            "operation_reference": "WAREHOUSE-OPS-CORR-LOSS",
            "operation_datetime": now_datetime(),
            "status": "Applied",
            "correction_type": "Quantity Count",
            "client": CLIENT_PORTAL_CUSTOMER,
            "container_code": "WAREHOUSE-OPS-CORR-LOSS",
            "warehouse": "Aisle B - 3",
            "item_code": "SKU-ALPHA-001",
            "client_sku": "ALPHA-001",
            "uom": "Nos",
            "expected_qty": 3,
            "actual_qty": 2,
            "qty_delta": -1,
            "condition_status": "OK",
        }
    )
    loss.insert(ignore_permissions=True)
    loss_entry = processor.apply_correction_stock_posting(loss)
    loss.reload()
    require(loss_entry, "Correction loss did not create Stock Entry")
    require(loss.stock_posting_status == "Posted", "Correction loss was not posted")
    entry = frappe.get_doc("Stock Entry", loss_entry)
    require(entry.stock_entry_type == "3PL Quantity Loss", "Correction loss used wrong Stock Entry Type")
    require(entry.items[0].s_warehouse == "Aisle B - 3", "Correction loss used wrong source warehouse")

    noop = frappe.get_doc(
        {
            "doctype": "Three PL Warehouse Correction",
            "operation_reference": "WAREHOUSE-OPS-CORR-NOOP",
            "operation_datetime": now_datetime(),
            "status": "Applied",
            "correction_type": "Quantity Count",
            "client": CLIENT_PORTAL_CUSTOMER,
            "container_code": "WAREHOUSE-OPS-CORR-NOOP",
            "warehouse": "Aisle B - 3",
            "item_code": "SKU-ALPHA-001",
            "client_sku": "ALPHA-001",
            "uom": "Nos",
            "expected_qty": 3,
            "actual_qty": 3,
            "qty_delta": 0,
            "condition_status": "OK",
        }
    )
    noop.insert(ignore_permissions=True)
    noop_entry = processor.apply_correction_stock_posting(noop)
    noop.reload()
    require(not noop_entry, "No-op correction should not create Stock Entry")
    require(noop.stock_posting_status == "Not Required", "No-op correction should be Not Required")

    cleanup_by_container(containers)


def validate_warehouse_role_access():
    frappe.set_user(WAREHOUSE_MANAGER_USER)
    for doctype in (
        "Three PL Container",
        "Three PL Container Move",
        "Three PL Container Repack",
        "Three PL Warehouse Correction",
        "Three PL Stocktake",
        "Three PL Stocktake Session",
        "Pick List",
        "Stock Entry",
    ):
        require(frappe.has_permission(doctype, "read"), f"Warehouse manager cannot read {doctype}")


def validate_warehouse_manager_reports():
    frappe.set_user(WAREHOUSE_MANAGER_USER)
    for report_name in REQUIRED_REPORTS:
        try:
            run_query_report(report_name, filters={})
        except Exception as exc:
            raise AssertionError(f"Warehouse manager cannot run report {report_name}: {exc}") from exc


def main():
    validate_warehouse_role_access()
    validate_warehouse_manager_reports()
    validate_container_move()
    validate_putaway_operation()
    validate_full_repack()
    validate_partial_repack()
    validate_repack_needs_review()
    validate_warehouse_correction()
    validate_warehouse_correction_stock_posting()
    validate_correction_loss_and_noop()
    validate_stocktake()
    validate_picking_confirmation()
    validate_outbound_fulfillment()
    frappe.db.commit()
    print("Warehouse operations validation passed")


if __name__ == "__main__":
    main()
