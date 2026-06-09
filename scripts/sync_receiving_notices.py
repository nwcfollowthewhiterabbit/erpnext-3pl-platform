import frappe


def qty_key(item_code, uom):
    return (item_code, uom or "")


def add_qty(target, key, qty):
    target[key] = target.get(key, 0) + (qty or 0)


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


def set_notice_item_quantities(notice, actual_by_key):
    for row in notice.items:
        key = qty_key(row.item_code, row.uom)
        expected_qty = row.expected_qty or 0
        received_qty = actual_by_key.get(key, 0)
        row.received_qty = received_qty
        row.variance_qty = received_qty - expected_qty


def manual_discrepancies(notice):
    return [row.as_dict() for row in notice.discrepancies if not row.auto_generated]


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


def sync_notice(notice_name):
    notice = frappe.get_doc("Inbound Shipment Notice", notice_name)
    stock_entry_names = submitted_receipt_entries(notice.name)
    expected_by_key, _rows_by_key = expected_totals(notice)
    actual_by_key, source_by_key = actual_totals(stock_entry_names)

    set_notice_item_quantities(notice, actual_by_key)
    manual_rows = manual_discrepancies(notice)
    notice.set("discrepancies", [])
    for row in manual_rows:
        notice.append("discrepancies", row)
    append_auto_discrepancies(notice, expected_by_key, actual_by_key, source_by_key)
    set_notice_status(notice, expected_by_key, actual_by_key)
    notice.save(ignore_permissions=True)
    return notice.name


def sync_receiving_notices():
    synced = []
    for notice_name in frappe.get_all("Inbound Shipment Notice", pluck="name"):
        if submitted_receipt_entries(notice_name):
            synced.append(sync_notice(notice_name))
    return synced


def main():
    synced = sync_receiving_notices()
    frappe.db.commit()
    print(f"Synced receiving notices: {len(synced)}")
    for notice_name in synced:
        print(notice_name)


if __name__ == "__main__":
    main()
