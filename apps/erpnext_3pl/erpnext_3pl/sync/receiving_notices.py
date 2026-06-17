import json

import frappe


def qty_key(item_code, uom):
    return (item_code, uom or "")


def add_qty(target, key, qty):
    target[key] = target.get(key, 0) + (qty or 0)


def structured_portal_items(description):
    if not description:
        return []
    try:
        payload = json.loads(description)
    except (TypeError, ValueError):
        return []
    if not isinstance(payload, dict) or payload.get("source") != "client_product_picker":
        return []
    return payload.get("items") if isinstance(payload.get("items"), list) else []


def ensure_structured_notice_items(notice):
    if notice.docstatus == 1:
        return False
    items = structured_portal_items(notice.portal_items_description)
    if not items:
        return False

    notice.set("items", [])
    for item in items:
        item_code = item.get("item_code")
        if not item_code:
            continue
        qty = item.get("expected_qty") or item.get("qty") or 0
        notice.append(
            "items",
            {
                "item_code": item_code,
                "client_sku": item.get("client_sku") or frappe.db.get_value("Item", item_code, "client_sku"),
                "item_name": item.get("item_name") or frappe.db.get_value("Item", item_code, "item_name"),
                "expected_qty": qty,
                "uom": item.get("uom") or frappe.db.get_value("Item", item_code, "stock_uom") or "Nos",
                "notes": item.get("notes"),
            },
        )
    return True


def scrub_invalid_stock_entry_links(notice):
    changed = False
    for row in notice.discrepancies:
        if row.source_stock_entry and not frappe.db.exists("Stock Entry", row.source_stock_entry):
            row.source_stock_entry = None
            changed = True
    return changed


def submitted_receipt_entries(notice_name):
    return frappe.get_all(
        "Stock Entry",
        filters={
            "docstatus": 1,
            "warehouse_flow": "Inbound Receipt",
            "inbound_shipment_notice": notice_name,
        },
        pluck="name",
    )


def expected_totals(notice):
    totals = {}
    rows_by_key = {}
    for row in notice.items:
        key = qty_key(row.item_code, row.uom)
        add_qty(totals, key, row.expected_qty)
        rows_by_key.setdefault(key, []).append(row)
    return totals, rows_by_key


def actual_totals(stock_entry_names):
    totals = {}
    source_by_key = {}
    for entry_name in stock_entry_names:
        entry = frappe.get_doc("Stock Entry", entry_name)
        for row in entry.items:
            key = qty_key(row.item_code, row.uom or row.stock_uom)
            add_qty(totals, key, row.qty)
            source_by_key.setdefault(key, entry.name)
    return totals, source_by_key


def manual_actual_totals(notice):
    totals = {}
    for row in notice.items:
        key = qty_key(row.item_code, row.uom)
        add_qty(totals, key, row.received_qty)
    return totals


def set_notice_item_quantities(notice, actual_by_key):
    for row in notice.items:
        key = qty_key(row.item_code, row.uom)
        expected_qty = row.expected_qty or 0
        received_qty = actual_by_key.get(key, 0)
        row.received_qty = received_qty
        row.variance_qty = received_qty - expected_qty


def manual_discrepancies(notice):
    rows = []
    for row in notice.discrepancies:
        if row.auto_generated:
            continue
        data = row.as_dict()
        source_stock_entry = data.get("source_stock_entry")
        if source_stock_entry and not frappe.db.exists("Stock Entry", source_stock_entry):
            data["source_stock_entry"] = None
        rows.append(data)
    return rows


def append_auto_discrepancies(notice, expected_by_key, actual_by_key, source_by_key):
    all_keys = set(expected_by_key) | set(actual_by_key)
    for key in sorted(all_keys):
        item_code, uom = key
        expected_qty = expected_by_key.get(key, 0)
        actual_qty = actual_by_key.get(key, 0)
        variance_qty = actual_qty - expected_qty
        if variance_qty == 0:
            continue

        if expected_qty == 0:
            discrepancy_type = "Unexpected Product"
        elif actual_qty == 0:
            discrepancy_type = "Missing Product"
        else:
            discrepancy_type = "Quantity Difference"

        notice.append(
            "discrepancies",
            {
                "discrepancy_type": discrepancy_type,
                "item_code": item_code,
                "expected_qty": expected_qty,
                "actual_qty": actual_qty,
                "variance_qty": variance_qty,
                "status": "Open",
                "auto_generated": 1,
                "source_stock_entry": source_by_key.get(key),
                "notes": "Generated from submitted inbound Stock Entry quantities.",
            },
        )


def unresolved_discrepancies(notice):
    return [row for row in notice.discrepancies if row.status != "Resolved"]


def set_notice_status(notice, expected_by_key, actual_by_key):
    total_expected = sum(expected_by_key.values())
    total_actual = sum(actual_by_key.values())
    if not total_actual:
        notice.status = "Draft"
        return
    if unresolved_discrepancies(notice):
        notice.status = "Discrepancy Review"
        return
    if total_actual < total_expected:
        notice.status = "Partially Received"
        return
    notice.status = "Received"


def sync_notice_doc(notice, save=False):
    scrub_invalid_stock_entry_links(notice)
    ensure_structured_notice_items(notice)
    stock_entry_names = submitted_receipt_entries(notice.name)
    expected_by_key, _rows_by_key = expected_totals(notice)
    if stock_entry_names:
        actual_by_key, source_by_key = actual_totals(stock_entry_names)
    else:
        actual_by_key = manual_actual_totals(notice)
        source_by_key = {}

    set_notice_item_quantities(notice, actual_by_key)
    manual_rows = manual_discrepancies(notice)
    notice.set("discrepancies", [])
    for row in manual_rows:
        notice.append("discrepancies", row)
    append_auto_discrepancies(notice, expected_by_key, actual_by_key, source_by_key)
    set_notice_status(notice, expected_by_key, actual_by_key)
    if save:
        notice.save(ignore_permissions=True)
    return notice.name


def sync_notice(notice_name):
    notice = frappe.get_doc("Inbound Shipment Notice", notice_name)
    return sync_notice_doc(notice, save=True)


def sync_receiving_notices():
    synced = []
    for notice_name in frappe.get_all("Inbound Shipment Notice", pluck="name"):
        notice = frappe.get_doc("Inbound Shipment Notice", notice_name)
        changed_links = scrub_invalid_stock_entry_links(notice)
        changed_items = ensure_structured_notice_items(notice)
        if changed_links or changed_items:
            notice.save(ignore_permissions=True)
            synced.append(notice.name)
        if submitted_receipt_entries(notice_name):
            synced.append(sync_notice(notice_name))
    return sorted(set(synced))


def main():
    synced = sync_receiving_notices()
    frappe.db.commit()
    print(f"Synced receiving notices: {len(synced)}")
    for notice_name in synced:
        print(notice_name)


if __name__ == "__main__":
    main()
