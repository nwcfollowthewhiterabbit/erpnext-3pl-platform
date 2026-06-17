from frappe import _
import frappe
from frappe.utils import flt, now_datetime

from erpnext_3pl.warehouse.container_moves import apply_move
from erpnext_3pl.warehouse.container_repacks import apply_repack
from erpnext_3pl.warehouse.warehouse_corrections import apply_correction_stock_posting


WAREHOUSE_ROLES = {"3PL Warehouse User", "3PL Warehouse Manager", "System Manager"}
BLOCKED_CONTAINER_STATUSES = {"Shipped", "Closed", "Replaced"}


def require_warehouse_role():
    if not set(frappe.get_roles()).intersection(WAREHOUSE_ROLES):
        frappe.throw(_("This operation is only available to warehouse users."), frappe.PermissionError)


def get_open_container(container_code):
    if not container_code:
        frappe.throw(_("Container / HU is required."))
    container = frappe.get_doc("Three PL Container", container_code)
    if container.status in BLOCKED_CONTAINER_STATUSES:
        frappe.throw(_("Container {0} cannot be changed from status {1}.").format(container.name, container.status))
    return container


def get_item_client_sku(item_code):
    if not item_code:
        frappe.throw(_("Item / SKU is required."))
    client_sku = frappe.db.get_value("Item", item_code, "client_sku")
    if client_sku is None:
        frappe.throw(_("Item {0} was not found.").format(item_code))
    return client_sku


def find_container_item(container, item_code, uom):
    for row in container.items:
        if row.item_code == item_code and (row.uom or uom) == uom:
            return row
    return None


def set_document_status(doc, status):
    doc.status = status
    doc.save(ignore_permissions=True)


def update_container_count(container, item_code, qty, uom, condition, notes):
    row = find_container_item(container, item_code, uom)
    expected_qty = row.qty if row else 0
    client_sku = get_item_client_sku(item_code)

    if row:
        row.qty = qty
        row.condition_status = condition
        row.notes = notes or row.notes
    else:
        container.append(
            "items",
            {
                "item_code": item_code,
                "client_sku": client_sku,
                "qty": qty,
                "uom": uom,
                "condition_status": condition,
                "notes": notes or "Added by scanner operation.",
            },
        )

    if condition != "OK":
        container.status = "In Verification"
    container.last_moved_at = now_datetime()
    container.save(ignore_permissions=True)
    return expected_qty, client_sku


def create_adjustment_movement(container, reference_doctype, reference_name, notes, operation_time):
    movement = frappe.get_doc(
        {
            "doctype": "Three PL Container Movement",
            "movement_datetime": operation_time,
            "container_code": container.name,
            "client": container.client,
            "movement_type": "Adjusted",
            "from_warehouse": container.current_warehouse,
            "to_warehouse": container.current_warehouse,
            "reference_doctype": reference_doctype,
            "reference_name": reference_name,
            "notes": notes,
        }
    )
    movement.insert(ignore_permissions=True)
    return movement


def create_correction(container, item_code, uom, expected_qty, actual_qty, condition, correction_type, notes, operation_time, source_doctype=None, source_name=None):
    correction = frappe.get_doc(
        {
            "doctype": "Three PL Warehouse Correction",
            "operation_reference": f"CORR-{container.name}-{item_code}-{frappe.generate_hash(length=8)}",
            "operation_datetime": operation_time,
            "status": "Draft",
            "correction_type": correction_type,
            "client": container.client,
            "container_code": container.name,
            "warehouse": container.current_warehouse,
            "item_code": item_code,
            "client_sku": get_item_client_sku(item_code),
            "uom": uom,
            "expected_qty": expected_qty,
            "actual_qty": actual_qty,
            "qty_delta": actual_qty - expected_qty,
            "condition_status": condition,
            "source_doctype": source_doctype,
            "source_name": source_name,
            "notes": notes,
        }
    )
    correction.insert(ignore_permissions=True)
    return correction


@frappe.whitelist()
def apply_container_move(container_code, target_location, notes=None):
    require_warehouse_role()
    container = get_open_container((container_code or "").strip())
    target_location = (target_location or "").strip()
    if not target_location:
        frappe.throw(_("Target Location is required."))

    operation_time = now_datetime()
    move = frappe.get_doc(
        {
            "doctype": "Three PL Container Move",
            "operation_reference": f"MOVE-{container.name}-{frappe.generate_hash(length=8)}",
            "operation_datetime": operation_time,
            "status": "Draft",
            "container_code": container.name,
            "client": container.client,
            "from_warehouse": container.current_warehouse,
            "to_warehouse": target_location,
            "notes": notes or "Created from scanner-first container move page.",
        }
    )
    move.insert(ignore_permissions=True)
    movement = apply_move(move)
    frappe.db.commit()
    return {"move": move.name, "movement": movement.name, "container": container.name}


@frappe.whitelist()
def apply_warehouse_correction(container_code, item_code, actual_qty, correction_type="Quantity Count", condition="OK", uom="Nos", notes=None):
    require_warehouse_role()
    container = get_open_container((container_code or "").strip())
    item_code = (item_code or "").strip()
    uom = (uom or "Nos").strip()
    actual_qty = flt(actual_qty)
    if actual_qty < 0:
        frappe.throw(_("Actual Qty must be non-negative."))

    operation_time = now_datetime()
    expected_qty, _client_sku = update_container_count(container, item_code, actual_qty, uom, condition, notes)
    correction = create_correction(
        container,
        item_code,
        uom,
        expected_qty,
        actual_qty,
        condition,
        correction_type,
        notes or "Created from scanner-first warehouse correction page.",
        operation_time,
    )
    movement = create_adjustment_movement(
        container,
        "Three PL Warehouse Correction",
        correction.name,
        f"{correction_type}: delta {correction.qty_delta}. {notes or ''}".strip(),
        operation_time,
    )
    correction.movement = movement.name
    set_document_status(correction, "Applied")
    entry_name = apply_correction_stock_posting(correction)
    frappe.db.commit()
    correction.reload()
    return {
        "correction": correction.name,
        "movement": movement.name,
        "stock_entry": entry_name,
        "stock_posting_status": correction.stock_posting_status,
    }


def ensure_stocktake_session(reference, container, notes, operation_time):
    if not reference:
        return None

    existing = frappe.db.get_value("Three PL Stocktake Session", {"session_reference": reference}, ["name", "status"], as_dict=True)
    if existing:
        if existing.status in {"Completed", "Cancelled"}:
            frappe.throw(_("Stocktake session is not open: {0}.").format(existing.status))
        return existing.name

    session = frappe.get_doc(
        {
            "doctype": "Three PL Stocktake Session",
            "session_reference": reference,
            "status": "Open",
            "client": container.client,
            "warehouse": container.current_warehouse,
            "started_at": operation_time,
            "notes": notes or "",
        }
    )
    session.insert(ignore_permissions=True)
    set_document_status(session, "In Progress")
    return session.name


@frappe.whitelist()
def apply_stocktake(container_code, item_code, counted_qty, session_reference=None, session_notes=None, condition="OK", uom="Nos", notes=None):
    require_warehouse_role()
    container = get_open_container((container_code or "").strip())
    item_code = (item_code or "").strip()
    uom = (uom or "Nos").strip()
    counted_qty = flt(counted_qty)
    if counted_qty < 0:
        frappe.throw(_("Counted Qty must be non-negative."))

    operation_time = now_datetime()
    session_name = ensure_stocktake_session((session_reference or "").strip(), container, session_notes, operation_time)
    expected_qty, client_sku = update_container_count(container, item_code, counted_qty, uom, condition, notes)
    qty_delta = counted_qty - expected_qty
    needs_correction = qty_delta != 0 or condition != "OK"

    stocktake = frappe.get_doc(
        {
            "doctype": "Three PL Stocktake",
            "operation_reference": f"STOCKTAKE-{container.name}-{item_code}-{frappe.generate_hash(length=8)}",
            "operation_datetime": operation_time,
            "status": "Draft",
            "stocktake_session": session_name,
            "client": container.client,
            "warehouse": container.current_warehouse,
            "container_code": container.name,
            "item_code": item_code,
            "client_sku": client_sku,
            "uom": uom,
            "expected_qty": expected_qty,
            "counted_qty": counted_qty,
            "qty_delta": qty_delta,
            "condition_status": condition,
            "notes": notes or "Created from scanner-first stocktake page.",
        }
    )
    stocktake.insert(ignore_permissions=True)

    correction_name = None
    movement_name = None
    stock_entry = None
    stock_posting_status = None
    if needs_correction:
        correction = create_correction(
            container,
            item_code,
            uom,
            expected_qty,
            counted_qty,
            condition,
            "Quantity Count",
            notes or "Created from scanner-first stocktake page.",
            operation_time,
            source_doctype="Three PL Stocktake",
            source_name=stocktake.name,
        )
        movement = create_adjustment_movement(
            container,
            "Three PL Stocktake",
            stocktake.name,
            f"Stocktake delta {qty_delta}. {notes or ''}".strip(),
            operation_time,
        )
        correction.movement = movement.name
        set_document_status(correction, "Applied")
        stocktake.correction = correction.name
        stocktake.movement = movement.name
        set_document_status(stocktake, "Applied")
        stock_entry = apply_correction_stock_posting(correction)
        correction.reload()
        correction_name = correction.name
        movement_name = movement.name
        stock_posting_status = correction.stock_posting_status
    else:
        set_document_status(stocktake, "No Difference")

    frappe.db.commit()
    return {
        "stocktake": stocktake.name,
        "session": session_name,
        "correction": correction_name,
        "movement": movement_name,
        "stock_entry": stock_entry,
        "stock_posting_status": stock_posting_status,
    }


@frappe.whitelist()
def complete_stocktake_session(session_reference):
    require_warehouse_role()
    session_reference = (session_reference or "").strip()
    if not session_reference:
        frappe.throw(_("Stocktake session reference is required."))
    session_name = frappe.db.get_value("Three PL Stocktake Session", {"session_reference": session_reference}, "name")
    if not session_name:
        frappe.throw(_("Stocktake session not found."))
    session = frappe.get_doc("Three PL Stocktake Session", session_name)
    session.completed_at = now_datetime()
    set_document_status(session, "Completed")
    frappe.db.commit()
    return {"session": session.name}


def source_container_item_rows(source_containers):
    totals = {}
    for container in source_containers:
        for row in container.items:
            key = (row.item_code, row.uom or "Nos", row.condition_status or "OK")
            if key not in totals:
                totals[key] = {
                    "item_code": row.item_code,
                    "client_sku": row.client_sku or get_item_client_sku(row.item_code),
                    "qty": 0,
                    "uom": row.uom or "Nos",
                    "condition_status": row.condition_status or "OK",
                    "notes": row.notes,
                }
            totals[key]["qty"] += row.qty or 0
    return list(totals.values())


@frappe.whitelist()
def apply_container_repack(repack_mode, source_containers, target_container, target_location, item_code=None, qty=None, uom="Nos", notes=None):
    require_warehouse_role()
    if isinstance(source_containers, str):
        source_containers = frappe.parse_json(source_containers)
    source_containers = [str(name).strip() for name in (source_containers or []) if str(name).strip()]
    if not source_containers:
        frappe.throw(_("At least one source container is required."))

    sources = [get_open_container(name) for name in source_containers]
    client = sources[0].client
    if any(source.client != client for source in sources):
        frappe.throw(_("All source containers must belong to the same client."))

    target_container = (target_container or "").strip()
    target_location = (target_location or "").strip()
    if not target_container or not target_location:
        frappe.throw(_("Target container and target location are required."))

    if not frappe.db.exists("Three PL Container", target_container):
        frappe.get_doc(
            {
                "doctype": "Three PL Container",
                "container_code": target_container,
                "barcode": target_container,
                "container_type": "Box",
                "client": client,
                "current_warehouse": target_location,
                "status": "Stored",
            }
        ).insert(ignore_permissions=True)

    repack_mode = repack_mode or "Full Consolidation"
    if repack_mode == "Partial Split":
        if len(sources) != 1:
            frappe.throw(_("Partial split requires exactly one source container."))
        item_code = (item_code or "").strip()
        uom = (uom or "Nos").strip()
        qty = flt(qty)
        if qty <= 0:
            frappe.throw(_("Qty To Move must be positive."))
        items = [
            {
                "item_code": item_code,
                "client_sku": get_item_client_sku(item_code),
                "qty": qty,
                "uom": uom,
                "condition_status": "OK",
                "notes": notes,
            }
        ]
    else:
        items = source_container_item_rows(sources)

    repack = frappe.get_doc(
        {
            "doctype": "Three PL Container Repack",
            "operation_reference": f"REPACK-{target_container}-{frappe.generate_hash(length=8)}",
            "operation_datetime": now_datetime(),
            "status": "Draft",
            "repack_mode": repack_mode,
            "client": client,
            "target_container": target_container,
            "target_location": target_location,
            "source_containers": [
                {"source_container": source.name, "source_location": source.current_warehouse} for source in sources
            ],
            "items": items,
            "notes": notes or "Created from scanner-first repack page.",
        }
    )
    repack.insert(ignore_permissions=True)
    movement = apply_repack(repack)
    frappe.db.commit()
    return {"repack": repack.name, "movement": movement.name, "target_container": target_container}
