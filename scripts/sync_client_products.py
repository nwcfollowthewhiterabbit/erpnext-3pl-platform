import json
import re

import frappe
from frappe.utils import now


SYNC_FIELDS = ["customer", "client_sku", "product_name", "product_description", "uom", "barcode", "product_image", "status"]


def clean_code(value):
    cleaned = re.sub(r"[^A-Z0-9]+", "-", str(value or "").upper()).strip("-")
    return cleaned or "ITEM"


def customer_prefix(customer):
    words = [word for word in re.split(r"[^A-Za-z0-9]+", customer or "") if word.lower() not in {"demo", "client", "customer"}]
    return clean_code(words[-1] if words else customer)[:12]


def product_snapshot(product):
    return {field: product.get(field) for field in SYNC_FIELDS}


def json_dumps(data):
    return json.dumps(data or {}, sort_keys=True, ensure_ascii=False, indent=2)


def find_existing_item(product):
    if product.item_code and frappe.db.exists("Item", product.item_code):
        return product.item_code

    return frappe.db.get_value(
        "Item",
        {
            "owner_client": product.customer,
            "client_sku": product.client_sku,
        },
        "name",
    )


def generated_item_code(product):
    base = f"{customer_prefix(product.customer)}-{clean_code(product.client_sku)}"
    existing = frappe.db.get_value(
        "Item",
        {
            "owner_client": product.customer,
            "client_sku": product.client_sku,
        },
        "name",
    )
    if existing:
        return existing

    if not frappe.db.exists("Item", base):
        return base

    counter = 2
    while frappe.db.exists("Item", f"{base}-{counter}"):
        counter += 1
    return f"{base}-{counter}"


def set_if_field(doc, fieldname, value):
    if doc.meta.has_field(fieldname):
        setattr(doc, fieldname, value)


def ensure_barcode(item, barcode):
    if not barcode:
        return
    if not any(row.barcode == barcode for row in item.get("barcodes", [])):
        item.append("barcodes", {"barcode": barcode})


def change_action(old_snapshot, new_snapshot):
    if not old_snapshot:
        return "Deactivated" if new_snapshot.get("status") == "Inactive" else "Created"
    if old_snapshot.get("status") != "Inactive" and new_snapshot.get("status") == "Inactive":
        return "Deactivated"
    return "Updated"


def insert_log(product, action, old_snapshot, new_snapshot, notes=None):
    log = frappe.new_doc("Three PL Client Product Change Log")
    log.product = product.name
    log.customer = product.customer
    log.item_code = product.item_code
    log.action = action
    log.changed_by = product.modified_by or product.owner
    log.change_datetime = product.modified or now()
    log.old_values = json_dumps(old_snapshot)
    log.new_values = json_dumps(new_snapshot)
    log.notes = notes
    log.insert(ignore_permissions=True)
    return log.name


def sync_product(product_name):
    product = frappe.get_doc("Three PL Client Product", product_name)
    snapshot = product_snapshot(product)
    old_snapshot = json.loads(product.last_synced_snapshot or "{}")

    try:
        item_code = find_existing_item(product) or generated_item_code(product)
        item = frappe.get_doc("Item", item_code) if frappe.db.exists("Item", item_code) else frappe.new_doc("Item")

        if item.is_new():
            item.item_code = item_code
            item.item_group = "Products"
            item.is_stock_item = 1

        item.item_name = product.product_name
        item.description = product.product_description or product.product_name
        item.item_group = item.item_group or "Products"
        item.stock_uom = product.uom or "Nos"
        item.disabled = 1 if product.status == "Inactive" else 0
        set_if_field(item, "owner_client", product.customer)
        set_if_field(item, "client_sku", product.client_sku)
        set_if_field(item, "client_product_name", product.product_name)
        set_if_field(item, "image", product.product_image)
        ensure_barcode(item, product.barcode)
        item.save(ignore_permissions=True)

        product.item_code = item.name
        product.sync_status = "Synced"
        product.sync_error = ""
        product.last_synced_at = now()
        product.last_synced_snapshot = json_dumps(snapshot)
        product.save(ignore_permissions=True)

        if old_snapshot != snapshot:
            insert_log(product, change_action(old_snapshot, snapshot), old_snapshot, snapshot, "Product card synchronized to ERPNext Item.")
        else:
            insert_log(product, "Synced", old_snapshot, snapshot, "Product card re-synchronized without client field changes.")

        return item.name
    except Exception as exc:
        product.sync_status = "Failed"
        product.sync_error = str(exc)
        product.save(ignore_permissions=True)
        insert_log(product, "Sync Failed", old_snapshot, snapshot, str(exc))
        raise


def sync_client_products():
    synced = []
    failed = []
    for product_name in frappe.get_all("Three PL Client Product", pluck="name"):
        product = frappe.get_doc("Three PL Client Product", product_name)
        current_snapshot = product_snapshot(product)
        previous_snapshot = json.loads(product.last_synced_snapshot or "{}")
        if product.sync_status == "Synced" and current_snapshot == previous_snapshot:
            continue
        try:
            synced.append(sync_product(product_name))
            frappe.db.commit()
        except Exception as exc:
            failed.append((product_name, str(exc)))
            frappe.db.commit()
    return synced, failed


def main():
    synced, failed = sync_client_products()
    frappe.db.commit()
    print(f"Synced client products: {len(synced)}")
    for item_code in synced:
        print(item_code)
    print(f"Failed client product syncs: {len(failed)}")
    for product_name, error in failed:
        print(f"{product_name}: {error}")


if __name__ == "__main__":
    main()
