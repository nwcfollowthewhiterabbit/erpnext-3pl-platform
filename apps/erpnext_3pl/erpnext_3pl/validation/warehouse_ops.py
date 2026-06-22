import frappe
from frappe.desk.query_report import run as run_query_report
from frappe.utils import now_datetime, nowdate

from erpnext_3pl.config.project_config import CLIENT_DESK_CUSTOMER, COMPANY, WAREHOUSE_MANAGER_USER
from erpnext_3pl.validation.site import (
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
    for correction_name in frappe.get_all("Three PL Warehouse Correction", filters={"container_code": ("in", container_names)}, pluck="name"):
        linked_entries = frappe.get_all("Stock Entry", filters={"warehouse_correction": correction_name}, pluck="name", order_by="creation desc")
        for entry_name in linked_entries:
            cancel_and_delete("Stock Entry", entry_name)
    for entry_name in frappe.get_all(
        "Stock Entry",
        filters=[["Stock Entry", "remarks", "like", "WAREHOUSE-OPS%"]],
        pluck="name",
        order_by="creation desc",
    ):
        cancel_and_delete("Stock Entry", entry_name)
    for movement_name in frappe.get_all("Three PL Container Movement", filters={"container_code": ("in", container_names)}, pluck="name"):
        cancel_and_delete("Three PL Container Movement", movement_name)
    for stocktake_name in frappe.get_all("Three PL Stocktake", filters={"container_code": ("in", container_names)}, pluck="name"):
        cancel_and_delete("Three PL Stocktake", stocktake_name)
    for session_name in frappe.get_all("Three PL Stocktake Session", filters={"session_reference": ("like", "WAREHOUSE-OPS-%")}, pluck="name"):
        cancel_and_delete("Three PL Stocktake Session", session_name)
    for doctype in ("Three PL Container Move", "Three PL Warehouse Correction"):
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
            "client": CLIENT_DESK_CUSTOMER,
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
    from erpnext_3pl.warehouse import container_moves as processor

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
            "client": CLIENT_DESK_CUSTOMER,
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
    from erpnext_3pl.warehouse import container_repacks as processor

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
            "client": CLIENT_DESK_CUSTOMER,
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
            "client": CLIENT_DESK_CUSTOMER,
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
    from erpnext_3pl.warehouse import container_repacks as processor

    containers = ["WAREHOUSE-OPS-REPACK-BAD-SRC", "WAREHOUSE-OPS-REPACK-BAD-TARGET"]
    cleanup_by_container(containers)

    seed_container("WAREHOUSE-OPS-REPACK-BAD-SRC", "Aisle A - 3", qty=1)
    frappe.get_doc(
        {
            "doctype": "Three PL Container",
            "container_code": "WAREHOUSE-OPS-REPACK-BAD-TARGET",
            "barcode": "WAREHOUSE-OPS-REPACK-BAD-TARGET",
            "container_type": "Box",
            "client": CLIENT_DESK_CUSTOMER,
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
            "client": CLIENT_DESK_CUSTOMER,
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
            "client": CLIENT_DESK_CUSTOMER,
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
    from erpnext_3pl.warehouse import warehouse_corrections as processor

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
            "status": "Draft",
            "correction_type": "Quantity Count",
            "client": CLIENT_DESK_CUSTOMER,
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
    loss.status = "Applied"
    loss.save(ignore_permissions=True)
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
            "status": "Draft",
            "correction_type": "Quantity Count",
            "client": CLIENT_DESK_CUSTOMER,
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
    noop.status = "Applied"
    noop.save(ignore_permissions=True)
    noop_entry = processor.apply_correction_stock_posting(noop)
    noop.reload()
    require(not noop_entry, "No-op correction should not create Stock Entry")
    require(noop.stock_posting_status == "Not Required", "No-op correction should be Not Required")

    cleanup_by_container(containers)


def validate_scanner_api_operations():
    from erpnext_3pl.api import warehouse_ops

    containers = [
        "WAREHOUSE-OPS-API-RECV",
        "WAREHOUSE-OPS-API-MOVE",
        "WAREHOUSE-OPS-API-CORR",
        "WAREHOUSE-OPS-API-STOCK",
        "WAREHOUSE-OPS-API-REPACK-SRC",
        "WAREHOUSE-OPS-API-REPACK-TGT",
    ]
    cleanup_by_container(containers)
    for notice_name in frappe.get_all("Inbound Shipment Notice", filters={"external_reference": "WAREHOUSE-OPS-API-RECV"}, pluck="name"):
        cancel_and_delete("Inbound Shipment Notice", notice_name)
    frappe.set_user("Administrator")
    seed_container("WAREHOUSE-OPS-API-MOVE", "Aisle A - 3", qty=2)
    seed_container("WAREHOUSE-OPS-API-CORR", "Aisle B - 3", qty=2)
    seed_container("WAREHOUSE-OPS-API-STOCK", "Aisle B - 3", qty=5)
    seed_container("WAREHOUSE-OPS-API-REPACK-SRC", "Aisle A - 3", qty=6)

    notice = frappe.get_doc(
        {
            "doctype": "Inbound Shipment Notice",
            "customer": CLIENT_DESK_CUSTOMER,
            "external_reference": "WAREHOUSE-OPS-API-RECV",
            "notice_date": nowdate(),
            "temporary_warehouse": "Temporary Receiving - 3",
            "status": "Draft",
            "items": [
                {
                    "item_code": "SKU-ALPHA-001",
                    "client_sku": frappe.db.get_value("Item", "SKU-ALPHA-001", "client_sku") or "ALPHA-001",
                    "expected_qty": 4,
                }
            ],
        }
    )
    notice.insert(ignore_permissions=True)

    frappe.set_user(WAREHOUSE_MANAGER_USER)
    receiving_result = warehouse_ops.apply_receiving_scan(
        "WAREHOUSE-OPS-API-RECV",
        "WAREHOUSE-OPS-API-RECV",
        "SKU-ALPHA-001",
        4,
        "Temporary Receiving - 3",
        notes="WAREHOUSE-OPS scanner API receiving.",
    )
    received_notice = frappe.get_doc("Inbound Shipment Notice", receiving_result["notice"])
    received_container = frappe.get_doc("Three PL Container", receiving_result["container"])
    received_entry = frappe.get_doc("Stock Entry", receiving_result["stock_entry"])
    require(receiving_result["movement"], "Scanner API receiving did not create movement history")
    require(received_entry.docstatus == 1, "Scanner API receiving did not submit Stock Entry")
    require(received_entry.inbound_shipment_notice == received_notice.name, "Scanner API receiving Stock Entry is not linked to notice")
    require(received_entry.container_code == received_container.name, "Scanner API receiving Stock Entry is not linked to container")
    require(received_container.current_warehouse == "Temporary Receiving - 3", "Scanner API receiving did not set container location")
    require(received_container.items[0].qty == 4, "Scanner API receiving did not update container qty")
    require(received_notice.items[0].received_qty == 4, "Scanner API receiving did not update notice received qty")
    require(received_notice.items[0].variance_qty == 0, "Scanner API receiving did not normalize notice variance")
    require(received_notice.items[0].uom == "Nos", "Scanner API receiving did not normalize empty notice UOM")
    require(
        not any(row.discrepancy_type in {"Missing Product", "Unexpected Product"} for row in received_notice.discrepancies),
        "Scanner API receiving created false missing/unexpected discrepancies",
    )
    require(received_notice.items[0].container_code == received_container.name, "Scanner API receiving did not annotate notice container")
    require(received_notice.status == "Received", "Scanner API receiving did not mark notice received")

    move_result = warehouse_ops.apply_container_move("WAREHOUSE-OPS-API-MOVE", "Aisle B - 3")
    moved_container = frappe.get_doc("Three PL Container", "WAREHOUSE-OPS-API-MOVE")
    require(move_result["move"], "Scanner API did not create container move")
    require(move_result["movement"], "Scanner API did not create move history")
    require(moved_container.current_warehouse == "Aisle B - 3", "Scanner API move did not update location")

    correction_result = warehouse_ops.apply_warehouse_correction(
        "WAREHOUSE-OPS-API-CORR",
        "SKU-ALPHA-001",
        3,
        notes="WAREHOUSE-OPS scanner API correction.",
    )
    corrected_container = frappe.get_doc("Three PL Container", "WAREHOUSE-OPS-API-CORR")
    correction = frappe.get_doc("Three PL Warehouse Correction", correction_result["correction"])
    require(corrected_container.items[0].qty == 3, "Scanner API correction did not update container qty")
    require(correction.status == "Applied", "Scanner API correction did not apply document")
    require(correction.stock_posting_status == "Posted", "Scanner API correction did not post stock entry")
    require(correction.stock_entry, "Scanner API correction is not linked to Stock Entry")

    same_result = warehouse_ops.apply_stocktake(
        "WAREHOUSE-OPS-API-STOCK",
        "SKU-ALPHA-001",
        5,
        session_reference="WAREHOUSE-OPS-API-STOCK-SAME",
        notes="WAREHOUSE-OPS scanner API no-difference stocktake.",
    )
    same_stocktake = frappe.get_doc("Three PL Stocktake", same_result["stocktake"])
    require(same_stocktake.status == "No Difference", "Scanner API no-difference stocktake has wrong status")
    warehouse_ops.complete_stocktake_session("WAREHOUSE-OPS-API-STOCK-SAME")
    same_session = frappe.get_doc("Three PL Stocktake Session", same_result["session"])
    require(same_session.status == "Completed", "Scanner API stocktake session did not complete")

    delta_result = warehouse_ops.apply_stocktake(
        "WAREHOUSE-OPS-API-STOCK",
        "SKU-ALPHA-001",
        6,
        session_reference="WAREHOUSE-OPS-API-STOCK-DELTA",
        notes="WAREHOUSE-OPS scanner API delta stocktake.",
    )
    delta_stocktake = frappe.get_doc("Three PL Stocktake", delta_result["stocktake"])
    delta_correction = frappe.get_doc("Three PL Warehouse Correction", delta_result["correction"])
    require(delta_stocktake.status == "Applied", "Scanner API delta stocktake was not applied")
    require(delta_stocktake.correction == delta_correction.name, "Scanner API delta stocktake is not linked to correction")
    require(delta_correction.stock_posting_status == "Posted", "Scanner API stocktake correction did not post stock entry")

    repack_result = warehouse_ops.apply_container_repack(
        "Partial Split",
        ["WAREHOUSE-OPS-API-REPACK-SRC"],
        "WAREHOUSE-OPS-API-REPACK-TGT",
        "Aisle B - 3",
        item_code="SKU-ALPHA-001",
        qty=2,
        notes="WAREHOUSE-OPS scanner API partial split.",
    )
    source = frappe.get_doc("Three PL Container", "WAREHOUSE-OPS-API-REPACK-SRC")
    target = frappe.get_doc("Three PL Container", "WAREHOUSE-OPS-API-REPACK-TGT")
    require(repack_result["repack"], "Scanner API did not create repack document")
    require(source.items[0].qty == 4, "Scanner API partial split did not subtract source qty")
    require(target.items[0].qty == 2, "Scanner API partial split did not add target qty")

    cleanup_by_container(containers)
    cancel_and_delete("Inbound Shipment Notice", notice.name)


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
    validate_scanner_api_operations()
    validate_stocktake()
    validate_picking_confirmation()
    validate_outbound_fulfillment()
    frappe.db.commit()
    print("Warehouse operations validation passed")


if __name__ == "__main__":
    main()
