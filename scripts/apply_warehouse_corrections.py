import frappe
from frappe.utils import get_time, getdate

from project_config import COMPANY


def append_item(entry, correction, qty):
    row = {
        "item_code": correction.item_code,
        "qty": abs(qty),
        "uom": correction.uom or frappe.db.get_value("Item", correction.item_code, "stock_uom") or "Nos",
        "conversion_factor": 1,
        "allow_zero_valuation_rate": 1,
        "container_code": correction.container_code,
    }
    if qty > 0:
        row["t_warehouse"] = correction.warehouse
    else:
        row["s_warehouse"] = correction.warehouse
    entry.append("items", row)


def make_stock_entry(correction):
    qty_delta = correction.qty_delta or 0
    if qty_delta == 0:
        correction.stock_posting_status = "Not Required"
        correction.stock_posting_error = ""
        correction.save(ignore_permissions=True)
        return None

    purpose = "Material Receipt" if qty_delta > 0 else "Material Issue"
    stock_entry_type = "3PL Quantity Gain" if qty_delta > 0 else "3PL Quantity Loss"
    entry = frappe.get_doc(
        {
            "doctype": "Stock Entry",
            "company": COMPANY,
            "purpose": purpose,
            "stock_entry_type": stock_entry_type,
            "posting_date": getdate(correction.operation_datetime),
            "posting_time": get_time(correction.operation_datetime),
            "client": correction.client,
            "warehouse_flow": "Warehouse Correction",
            "scanned_location": correction.warehouse,
            "container_code": correction.container_code,
            "warehouse_correction": correction.name,
            "remarks": f"3PL warehouse correction {correction.name}: {correction.correction_type}.",
        }
    )
    append_item(entry, correction, qty_delta)
    entry.insert(ignore_permissions=True)
    entry.submit()
    return entry


def mark_needs_review(correction, exc):
    correction.stock_posting_status = "Needs Review"
    correction.stock_posting_error = str(exc)[:1000]
    correction.save(ignore_permissions=True)


def apply_correction_stock_posting(correction):
    if correction.stock_entry and frappe.db.exists("Stock Entry", correction.stock_entry):
        correction.stock_posting_status = "Posted"
        correction.stock_posting_error = ""
        correction.save(ignore_permissions=True)
        return correction.stock_entry

    if correction.status != "Applied":
        return None
    if correction.stock_posting_status == "Needs Review":
        return None
    if not correction.warehouse:
        mark_needs_review(correction, "Correction has no warehouse/location for stock posting.")
        return None

    try:
        entry = make_stock_entry(correction)
    except Exception as exc:
        frappe.db.rollback()
        if frappe.db.exists("Three PL Warehouse Correction", correction.name):
            correction.reload()
            mark_needs_review(correction, exc)
        frappe.db.commit()
        return None

    if entry:
        correction.stock_entry = entry.name
        correction.stock_posting_status = "Posted"
        correction.stock_posting_error = ""
        correction.save(ignore_permissions=True)
    return entry.name if entry else None


def apply_warehouse_corrections():
    posted = []
    skipped = []
    for correction_name in frappe.get_all(
        "Three PL Warehouse Correction",
        filters={"status": "Applied", "stock_posting_status": ("not in", ["Posted", "Needs Review", "Not Required"])},
        pluck="name",
    ):
        correction = frappe.get_doc("Three PL Warehouse Correction", correction_name)
        entry_name = apply_correction_stock_posting(correction)
        if entry_name:
            posted.append(entry_name)
            frappe.db.commit()
        else:
            skipped.append(correction_name)
    return posted, skipped


def main():
    posted, skipped = apply_warehouse_corrections()
    frappe.db.commit()
    print(f"Posted warehouse correction Stock Entries: {len(posted)}")
    print(f"Skipped warehouse correction stock postings: {len(skipped)}")


if __name__ == "__main__":
    main()
