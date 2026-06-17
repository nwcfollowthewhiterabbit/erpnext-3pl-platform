import frappe


def sync_client_product(doc, method=None):
    if frappe.flags.get("three_pl_client_product_sync"):
        return
    frappe.flags.three_pl_client_product_sync = True
    try:
        from erpnext_3pl.sync.client_products import sync_product

        sync_product(doc.name)
    finally:
        frappe.flags.three_pl_client_product_sync = False


def sync_product_import(doc, method=None):
    if frappe.flags.get("three_pl_product_import_sync"):
        return
    frappe.flags.three_pl_product_import_sync = True
    try:
        from erpnext_3pl.sync.client_products import process_product_import

        if doc.status == "Pending":
            process_product_import(doc.name)
    finally:
        frappe.flags.three_pl_product_import_sync = False


def sync_client_instruction_status(doc, method=None):
    if not doc.receiving_notice:
        return
    frappe.db.set_value(
        "Inbound Shipment Notice",
        doc.receiving_notice,
        "client_instruction_status",
        "Instruction Received",
        update_modified=True,
    )


def sync_container_inventory(doc, method=None):
    if frappe.flags.get("three_pl_container_inventory_sync"):
        return
    frappe.flags.three_pl_container_inventory_sync = True
    try:
        from erpnext_3pl.sync.inventory_snapshots import sync_snapshot

        active_statuses = {"Received", "In Verification", "Ready for Putaway", "Stored", "Picking", "Picked", "Packed"}
        active_keys = set()
        if doc.status in active_statuses and doc.current_warehouse:
            for item_row in doc.items:
                active_keys.add((doc.client, item_row.item_code, doc.name))
                sync_snapshot(doc, item_row)

        for snapshot_name in frappe.get_all("Three PL Inventory Snapshot", filters={"container_code": doc.name}, pluck="name"):
            snapshot = frappe.get_doc("Three PL Inventory Snapshot", snapshot_name)
            if (snapshot.customer, snapshot.item_code, snapshot.container_code) not in active_keys:
                frappe.delete_doc("Three PL Inventory Snapshot", snapshot.name, ignore_permissions=True, force=True)
    finally:
        frappe.flags.three_pl_container_inventory_sync = False


def sync_receiving_notice_discrepancies(doc, method=None):
    if frappe.flags.get("three_pl_receiving_notice_sync"):
        return
    frappe.flags.three_pl_receiving_notice_sync = True
    try:
        from erpnext_3pl.sync.receiving_notices import sync_notice_doc

        sync_notice_doc(doc)
    finally:
        frappe.flags.three_pl_receiving_notice_sync = False


def sync_shipment_request_pick_list(doc, method=None):
    if frappe.flags.get("three_pl_shipment_request_pick_list_sync"):
        return
    frappe.flags.three_pl_shipment_request_pick_list_sync = True
    try:
        from erpnext_3pl.sync.shipment_requests import sync_request

        sync_request(doc.name)
    finally:
        frappe.flags.three_pl_shipment_request_pick_list_sync = False


def sync_pick_list_picked(doc, method=None):
    if frappe.flags.get("three_pl_pick_list_picked_sync"):
        return
    frappe.flags.three_pl_pick_list_picked_sync = True
    try:
        from erpnext_3pl.sync.picking_confirmations import sync_pick_list

        if doc.shipment_request:
            sync_pick_list(doc.name)
    finally:
        frappe.flags.three_pl_pick_list_picked_sync = False


def sync_stock_entry_flow(doc, method=None):
    if frappe.flags.get("three_pl_stock_entry_flow_sync"):
        return
    frappe.flags.three_pl_stock_entry_flow_sync = True
    try:
        if doc.warehouse_flow == "Inbound Receipt":
            from erpnext_3pl.sync.receiving_notices import sync_notice

            if doc.inbound_shipment_notice:
                sync_notice(doc.inbound_shipment_notice)
        if doc.warehouse_flow in {"Packing", "Shipping"}:
            from erpnext_3pl.sync.outbound_fulfillment import sync_entry

            sync_entry(doc.name)
    finally:
        frappe.flags.three_pl_stock_entry_flow_sync = False
