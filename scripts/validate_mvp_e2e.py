import frappe
from frappe.utils import now_datetime, nowdate

from project_config import CLIENT_PORTAL_CUSTOMER, CLIENT_PORTAL_USER, COMPANY, WAREHOUSE_MANAGER_USER


PREFIX = "MVP-E2E"
CLIENT_SKU = f"{PREFIX}-SKU"
PRODUCT_NAME = "MVP E2E Product"
ITEM_CODE = None
NOTICE_REF = f"{PREFIX}-IN"
SHIPMENT_REF = f"{PREFIX}-OUT"
CONTAINER_CODE = f"{PREFIX}-BOX"
TEMP_WAREHOUSE = "Temporary Receiving - 3"
STORAGE_WAREHOUSE = "Aisle B - 3"
PACKING_WAREHOUSE = "Packing - 3"


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def cancel_and_delete(doctype, name):
    if not name or not frappe.db.exists(doctype, name):
        return
    doc = frappe.get_doc(doctype, name)
    if getattr(doc, "docstatus", 0) == 1:
        doc.cancel()
    frappe.delete_doc(doctype, name, ignore_permissions=True, force=True)


def cleanup():
    frappe.set_user("Administrator")

    for stock_entry_name in frappe.get_all(
        "Stock Entry",
        filters=[
            ["Stock Entry", "remarks", "like", f"{PREFIX}%"],
        ],
        pluck="name",
        order_by="creation desc",
    ):
        cancel_and_delete("Stock Entry", stock_entry_name)

    request_names = frappe.get_all("Three PL Shipment Request", filters={"external_reference": SHIPMENT_REF}, pluck="name")
    for pick_name in frappe.get_all("Pick List", filters={"shipment_request": ("in", request_names or [""])}, pluck="name"):
        cancel_and_delete("Pick List", pick_name)
    for request_name in request_names:
        cancel_and_delete("Three PL Shipment Request", request_name)

    for movement_name in frappe.get_all("Three PL Container Movement", filters={"container_code": CONTAINER_CODE}, pluck="name"):
        cancel_and_delete("Three PL Container Movement", movement_name)
    for move_name in frappe.get_all("Three PL Container Move", filters={"container_code": CONTAINER_CODE}, pluck="name"):
        cancel_and_delete("Three PL Container Move", move_name)
    for stocktake_name in frappe.get_all("Three PL Stocktake", filters={"container_code": CONTAINER_CODE}, pluck="name"):
        cancel_and_delete("Three PL Stocktake", stocktake_name)
    for correction_name in frappe.get_all("Three PL Warehouse Correction", filters={"container_code": CONTAINER_CODE}, pluck="name"):
        cancel_and_delete("Three PL Warehouse Correction", correction_name)
    for snapshot_name in frappe.get_all("Three PL Inventory Snapshot", filters={"container_code": CONTAINER_CODE}, pluck="name"):
        cancel_and_delete("Three PL Inventory Snapshot", snapshot_name)
    for balance_name in frappe.get_all("Three PL Inventory Balance Snapshot", filters={"client_sku": CLIENT_SKU}, pluck="name"):
        cancel_and_delete("Three PL Inventory Balance Snapshot", balance_name)

    cancel_and_delete("Three PL Container", CONTAINER_CODE)

    for notice_name in frappe.get_all("Inbound Shipment Notice", filters={"external_reference": NOTICE_REF}, pluck="name"):
        cancel_and_delete("Inbound Shipment Notice", notice_name)

    for product_name in frappe.get_all("Three PL Client Product", filters={"client_sku": CLIENT_SKU}, pluck="name"):
        for log_name in frappe.get_all("Three PL Client Product Change Log", filters={"product": product_name}, pluck="name"):
            cancel_and_delete("Three PL Client Product Change Log", log_name)
        cancel_and_delete("Three PL Client Product", product_name)

    for item_name in frappe.get_all("Item", filters={"client_sku": CLIENT_SKU}, pluck="name"):
        cancel_and_delete("Item", item_name)

    frappe.db.commit()


def append_stock_item(entry, item_code, qty, source=None, target=None):
    row = {
        "item_code": item_code,
        "qty": qty,
        "uom": "Nos",
        "stock_uom": "Nos",
        "conversion_factor": 1,
        "basic_rate": 1,
        "container_code": CONTAINER_CODE,
        "scanned_location": source or target,
    }
    if source:
        row["s_warehouse"] = source
    if target:
        row["t_warehouse"] = target
    entry.append("items", row)


def submit_stock_entry(entry_type, purpose, flow, item_code, qty, source=None, target=None, **extra):
    entry = frappe.new_doc("Stock Entry")
    entry.stock_entry_type = entry_type
    entry.purpose = purpose
    entry.company = COMPANY
    entry.posting_date = nowdate()
    entry.client = CLIENT_PORTAL_CUSTOMER
    entry.warehouse_flow = flow
    entry.container_code = CONTAINER_CODE
    entry.scanned_location = source or target
    entry.remarks = f"{PREFIX} {flow}"
    for field, value in extra.items():
        if entry.meta.has_field(field):
            setattr(entry, field, value)
    append_stock_item(entry, item_code, qty, source=source, target=target)
    entry.insert(ignore_permissions=True)
    entry.submit()
    frappe.db.commit()
    return entry


def create_client_product():
    product_sync = __import__("sync_client_products")

    frappe.set_user(CLIENT_PORTAL_USER)
    product = frappe.get_doc(
        {
            "doctype": "Three PL Client Product",
            "customer": CLIENT_PORTAL_CUSTOMER,
            "client_sku": CLIENT_SKU,
            "product_name": PRODUCT_NAME,
            "product_description": "Temporary product created by MVP golden path validation.",
            "uom": "Nos",
            "barcode": f"{PREFIX}-BARCODE",
            "status": "Active",
            "notes": f"{PREFIX} product validation row.",
        }
    )
    product.insert()
    require(product.owner == CLIENT_PORTAL_USER, "Client product was not created by portal user")

    frappe.set_user("Administrator")
    item_code = product_sync.sync_product(product.name)
    product.reload()
    item = frappe.get_doc("Item", item_code)
    require(product.sync_status == "Synced", "Client product did not sync")
    require(item.owner_client == CLIENT_PORTAL_CUSTOMER, "Synced item has wrong owner_client")
    require(item.client_sku == CLIENT_SKU, "Synced item has wrong client_sku")
    require(frappe.db.exists("Three PL Client Product Change Log", {"product": product.name, "action": "Created"}), "Product create log is missing")
    return item_code


def create_receiving_notice(item_code):
    payload = frappe.as_json(
        {
            "version": 1,
            "source": "client_product_picker",
            "mode": "receiving",
            "items": [
                {
                    "item_code": item_code,
                    "client_sku": CLIENT_SKU,
                    "item_name": PRODUCT_NAME,
                    "uom": "Nos",
                    "expected_qty": 3,
                    "qty": 3,
                    "notes": "MVP E2E receiving row.",
                }
            ],
        }
    )
    frappe.set_user(CLIENT_PORTAL_USER)
    notice = frappe.get_doc(
        {
            "doctype": "Inbound Shipment Notice",
            "customer": CLIENT_PORTAL_CUSTOMER,
            "external_reference": NOTICE_REF,
            "expected_arrival_date": nowdate(),
            "temporary_warehouse": TEMP_WAREHOUSE,
            "portal_source": 1,
            "portal_items_description": payload,
        }
    )
    notice.insert()
    require(notice.owner == CLIENT_PORTAL_USER, "Receiving Notice was not created by portal user")
    return notice.name


def receive_goods(notice_name, item_code):
    receiving_sync = __import__("sync_receiving_notices")

    frappe.set_user(WAREHOUSE_MANAGER_USER)
    container = frappe.get_doc(
        {
            "doctype": "Three PL Container",
            "container_code": CONTAINER_CODE,
            "barcode": CONTAINER_CODE,
            "container_type": "Box",
            "client": CLIENT_PORTAL_CUSTOMER,
            "current_warehouse": TEMP_WAREHOUSE,
            "status": "Expected",
        }
    )
    container.insert()

    submit_stock_entry(
        "3PL Inbound Receipt",
        "Material Receipt",
        "Inbound Receipt",
        item_code,
        3,
        target=TEMP_WAREHOUSE,
        inbound_shipment_notice=notice_name,
    )

    frappe.set_user("Administrator")
    receiving_sync.sync_notice(notice_name)
    notice = frappe.get_doc("Inbound Shipment Notice", notice_name)
    require(len(notice.items) == 1, "Receiving Notice structured items were not expanded")
    require(notice.items[0].received_qty == 3, "Receiving Notice received_qty is wrong")
    require(notice.items[0].variance_qty == 0, "Receiving Notice variance should be zero")
    require(notice.status == "Received", f"Receiving Notice status is wrong: {notice.status}")

    container = frappe.get_doc("Three PL Container", CONTAINER_CODE)
    container.status = "Ready for Putaway"
    container.set(
        "items",
        [
            {
                "item_code": item_code,
                "client_sku": CLIENT_SKU,
                "qty": 3,
                "uom": "Nos",
                "condition_status": "OK",
            }
        ],
    )
    container.save(ignore_permissions=True)
    return container.name


def putaway(container_name, item_code):
    frappe.set_user(WAREHOUSE_MANAGER_USER)
    container = frappe.get_doc("Three PL Container", container_name)
    operation_time = now_datetime()
    move = frappe.get_doc(
        {
            "doctype": "Three PL Container Move",
            "operation_reference": f"{PREFIX}-PUTAWAY",
            "operation_datetime": operation_time,
            "status": "Draft",
            "container_code": container.name,
            "client": container.client,
            "from_warehouse": container.current_warehouse,
            "to_warehouse": STORAGE_WAREHOUSE,
            "notes": "MVP E2E putaway.",
        }
    )
    move.insert()
    movement = frappe.get_doc(
        {
            "doctype": "Three PL Container Movement",
            "movement_datetime": operation_time,
            "container_code": container.name,
            "client": container.client,
            "movement_type": "Putaway",
            "from_warehouse": container.current_warehouse,
            "to_warehouse": STORAGE_WAREHOUSE,
            "reference_doctype": "Three PL Container Move",
            "reference_name": move.name,
            "notes": "MVP E2E putaway movement.",
        }
    )
    movement.insert()
    container.current_warehouse = STORAGE_WAREHOUSE
    container.status = "Stored"
    container.last_moved_at = operation_time
    container.save()
    move.status = "Applied"
    move.movement = movement.name
    move.save()

    submit_stock_entry(
        "3PL Put Away",
        "Material Transfer",
        "Put Away",
        item_code,
        3,
        source=TEMP_WAREHOUSE,
        target=STORAGE_WAREHOUSE,
    )

    frappe.set_user("Administrator")
    container.reload()
    require(container.current_warehouse == STORAGE_WAREHOUSE, "Container was not moved to storage")
    require(container.status == "Stored", "Container is not stored after putaway")
    require(move.status == "Applied", "Putaway move was not applied")


def stocktake(container_name, item_code):
    frappe.set_user(WAREHOUSE_MANAGER_USER)
    operation_time = now_datetime()
    session = frappe.get_doc(
        {
            "doctype": "Three PL Stocktake Session",
            "session_reference": f"{PREFIX}-STOCKTAKE-SESSION",
            "status": "In Progress",
            "client": CLIENT_PORTAL_CUSTOMER,
            "warehouse": STORAGE_WAREHOUSE,
            "started_at": operation_time,
            "notes": "MVP E2E stocktake session.",
        }
    )
    session.insert()
    stocktake = frappe.get_doc(
        {
            "doctype": "Three PL Stocktake",
            "operation_reference": f"{PREFIX}-STOCKTAKE",
            "operation_datetime": operation_time,
            "status": "No Difference",
            "stocktake_session": session.name,
            "client": CLIENT_PORTAL_CUSTOMER,
            "warehouse": STORAGE_WAREHOUSE,
            "container_code": container_name,
            "item_code": item_code,
            "client_sku": CLIENT_SKU,
            "uom": "Nos",
            "expected_qty": 3,
            "counted_qty": 3,
            "qty_delta": 0,
            "condition_status": "OK",
            "notes": "MVP E2E no-difference stocktake.",
        }
    )
    stocktake.insert()
    session.status = "Completed"
    session.completed_at = operation_time
    session.save()
    frappe.set_user("Administrator")
    stocktake.reload()
    session.reload()
    require(stocktake.status == "No Difference", "Stocktake status is wrong")
    require(session.status == "Completed", "Stocktake session was not completed")


def create_shipment_request(item_code):
    inventory_sync = __import__("sync_inventory_snapshots")
    shipment_sync = __import__("sync_shipment_requests")

    frappe.set_user("Administrator")
    inventory_sync.sync_inventory_snapshots()

    payload = frappe.as_json(
        {
            "version": 1,
            "source": "client_product_picker",
            "mode": "shipment",
            "items": [
                {
                    "item_code": item_code,
                    "client_sku": CLIENT_SKU,
                    "item_name": PRODUCT_NAME,
                    "uom": "Nos",
                    "qty": 2,
                    "notes": "MVP E2E outbound row.",
                }
            ],
        }
    )
    frappe.set_user(CLIENT_PORTAL_USER)
    request = frappe.get_doc(
        {
            "doctype": "Three PL Shipment Request",
            "customer": CLIENT_PORTAL_CUSTOMER,
            "external_reference": SHIPMENT_REF,
            "requested_ship_date": nowdate(),
            "destination_name": "MVP E2E Consignee",
            "destination_address": "MVP E2E destination address",
            "portal_source": 1,
            "portal_items_description": payload,
        }
    )
    request.insert()
    require(request.owner == CLIENT_PORTAL_USER, "Shipment Request was not created by portal user")

    frappe.set_user("Administrator")
    pick_list_name = shipment_sync.sync_request(request.name)
    require(pick_list_name, "Shipment Request did not create Pick List")
    request.reload()
    pick_list = frappe.get_doc("Pick List", pick_list_name)
    require(request.status == "Picking", f"Shipment Request status is wrong after allocation: {request.status}")
    require(pick_list.client == CLIENT_PORTAL_CUSTOMER, "Pick List has wrong client")
    require(any(row.container_code == CONTAINER_CODE and row.item_code == item_code and row.qty == 2 for row in pick_list.locations), "Pick List did not allocate the E2E container")
    container = frappe.get_doc("Three PL Container", CONTAINER_CODE)
    require(container.status == "Picking", f"Container status is wrong after allocation: {container.status}")
    return request.name, pick_list.name


def pick_pack_ship(request_name, pick_list_name, item_code):
    picking_sync = __import__("sync_picking_confirmations")
    fulfillment_sync = __import__("sync_outbound_fulfillment")

    frappe.set_user(WAREHOUSE_MANAGER_USER)
    pick_list = frappe.get_doc("Pick List", pick_list_name)
    for row in pick_list.locations:
        if row.container_code == CONTAINER_CODE:
            row.picked_qty = row.stock_qty or row.qty
    pick_list.save()

    frappe.set_user("Administrator")
    picked = picking_sync.sync_pick_list(pick_list.name)
    require(CONTAINER_CODE in picked, "Picking confirmation did not pick container")
    container = frappe.get_doc("Three PL Container", CONTAINER_CODE)
    require(container.status == "Picked", f"Container status is wrong after picking: {container.status}")

    packing = submit_stock_entry(
        "3PL Packing",
        "Material Transfer",
        "Packing",
        item_code,
        2,
        source=STORAGE_WAREHOUSE,
        target=PACKING_WAREHOUSE,
        shipment_request=request_name,
        shipment_reference=SHIPMENT_REF,
    )
    fulfillment_sync.sync_entry(packing.name)
    request = frappe.get_doc("Three PL Shipment Request", request_name)
    container.reload()
    require(request.status == "Packed", f"Shipment Request status is wrong after packing: {request.status}")
    require(container.status == "Packed", f"Container status is wrong after packing: {container.status}")

    shipping = submit_stock_entry(
        "3PL Shipping",
        "Material Issue",
        "Shipping",
        item_code,
        2,
        source=PACKING_WAREHOUSE,
        shipment_request=request_name,
        shipment_reference=SHIPMENT_REF,
    )
    fulfillment_sync.sync_entry(shipping.name)
    request.reload()
    container.reload()
    require(request.status == "Shipped", f"Shipment Request status is wrong after shipping: {request.status}")
    require(container.status == "Shipped", f"Container status is wrong after shipping: {container.status}")


def validate_client_visibility(item_code):
    inventory_balance_sync = __import__("sync_inventory_balance_snapshots")

    frappe.set_user("Administrator")
    inventory_balance_sync.sync_inventory_balance_snapshots()

    frappe.set_user(CLIENT_PORTAL_USER)
    product_name = frappe.db.get_value("Three PL Client Product", {"customer": CLIENT_PORTAL_CUSTOMER, "client_sku": CLIENT_SKU}, "name")
    require(product_name, "Client cannot find own E2E product")
    product = frappe.get_doc("Three PL Client Product", product_name)
    require(frappe.has_permission("Three PL Client Product", "read", doc=product), "Client has no read permission for own product")
    request_name = frappe.db.get_value("Three PL Shipment Request", {"customer": CLIENT_PORTAL_CUSTOMER, "external_reference": SHIPMENT_REF}, "name")
    require(request_name, "Client cannot find own E2E shipment request")
    request = frappe.get_doc("Three PL Shipment Request", request_name)
    require(request.status == "Shipped", "Client-visible shipment is not shipped")


def main():
    cleanup()
    try:
        item_code = create_client_product()
        notice_name = create_receiving_notice(item_code)
        container_name = receive_goods(notice_name, item_code)
        putaway(container_name, item_code)
        stocktake(container_name, item_code)
        request_name, pick_list_name = create_shipment_request(item_code)
        pick_pack_ship(request_name, pick_list_name, item_code)
        validate_client_visibility(item_code)
        print("MVP E2E validation passed")
        print(f"Product SKU: {CLIENT_SKU}")
        print(f"Item: {item_code}")
        print(f"Receiving Notice: {NOTICE_REF}")
        print(f"Shipment Request: {SHIPMENT_REF}")
    finally:
        cleanup()


if __name__ == "__main__":
    main()
