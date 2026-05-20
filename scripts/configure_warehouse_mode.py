import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


COMPANY = "3pl"
COMPANY_ABBR = "3"


def ensure_doc(doctype, name=None, **values):
    if name and frappe.db.exists(doctype, name):
        doc = frappe.get_doc(doctype, name)
        changed = False
        for key, value in values.items():
            if getattr(doc, key, None) != value:
                setattr(doc, key, value)
                changed = True
        if changed:
            doc.save(ignore_permissions=True)
        return doc

    doc = frappe.new_doc(doctype)
    if name:
        doc.name = name
    for key, value in values.items():
        setattr(doc, key, value)
    doc.insert(ignore_permissions=True)
    return doc


def ensure_warehouse(warehouse_name, parent=None, is_group=0):
    full_name = f"{warehouse_name} - {COMPANY_ABBR}"
    if frappe.db.exists("Warehouse", full_name):
        doc = frappe.get_doc("Warehouse", full_name)
        changed = False
        expected = {
            "warehouse_name": warehouse_name,
            "company": COMPANY,
            "parent_warehouse": parent,
            "is_group": is_group,
        }
        for key, value in expected.items():
            if getattr(doc, key, None) != value:
                setattr(doc, key, value)
                changed = True
        if changed:
            doc.save(ignore_permissions=True)
        return doc

    doc = frappe.get_doc(
        {
            "doctype": "Warehouse",
            "warehouse_name": warehouse_name,
            "company": COMPANY,
            "parent_warehouse": parent,
            "is_group": is_group,
        }
    )
    doc.insert(ignore_permissions=True)
    return doc


def configure_workspaces():
    visible = {"Home", "Stock", "Users"}
    for name in frappe.get_all("Workspace", pluck="name"):
        is_hidden = 0 if name in visible else 1
        frappe.db.set_value("Workspace", name, "is_hidden", is_hidden, update_modified=True)


def configure_module_profile():
    blocked_modules = [
        "Accounts",
        "Assets",
        "Buying",
        "CRM",
        "ERPNext Integrations",
        "Integrations",
        "Manufacturing",
        "Projects",
        "Quality Management",
        "Selling",
        "Support",
        "Website",
    ]

    try:
        old_in_install = getattr(frappe.flags, "in_install", False)
        frappe.flags.in_install = True
        if frappe.db.exists("Module Profile", "Warehouse Only"):
            profile = frappe.get_doc("Module Profile", "Warehouse Only")
            profile.set("block_modules", [])
        else:
            profile = frappe.new_doc("Module Profile")
            profile.module_profile_name = "Warehouse Only"

        for module in blocked_modules:
            profile.append("block_modules", {"module": module})

        profile.save(ignore_permissions=True)
    except frappe.DocumentLockedError:
        frappe.log_error("Warehouse Only module profile is locked; skipping profile update")
    finally:
        frappe.flags.in_install = old_in_install

    for role_name in ("3PL Warehouse User", "3PL Warehouse Manager"):
        if not frappe.db.exists("Role", role_name):
            frappe.get_doc({"doctype": "Role", "role_name": role_name}).insert(ignore_permissions=True)


def configure_warehouses():
    root = f"All Warehouses - {COMPANY_ABBR}"
    ensure_warehouse("Receiving Area", root, is_group=1)
    ensure_warehouse("Temporary Receiving", f"Receiving Area - {COMPANY_ABBR}")
    ensure_warehouse("Inspection and Comparison", f"Receiving Area - {COMPANY_ABBR}")

    ensure_warehouse("Storage Locations", root, is_group=1)
    ensure_warehouse("Aisle A", f"Storage Locations - {COMPANY_ABBR}")
    ensure_warehouse("Aisle B", f"Storage Locations - {COMPANY_ABBR}")
    ensure_warehouse("Overflow", f"Storage Locations - {COMPANY_ABBR}")

    ensure_warehouse("Packing", root)
    ensure_warehouse("Shipping", root)


def configure_stock_entry_types():
    entry_types = {
        "3PL Inbound Receipt": "Material Receipt",
        "3PL Comparison": "Material Transfer",
        "3PL Put Away": "Material Transfer",
        "3PL Internal Movement": "Material Transfer",
        "3PL Packing": "Material Transfer",
        "3PL Shipping": "Material Issue",
    }

    for name, purpose in entry_types.items():
        if frappe.db.exists("Stock Entry Type", name):
            frappe.db.set_value("Stock Entry Type", name, "purpose", purpose)
            continue

        frappe.get_doc(
            {
                "doctype": "Stock Entry Type",
                "name": name,
                "purpose": purpose,
                "is_standard": 0,
            }
        ).insert(ignore_permissions=True)


def configure_custom_doctypes():
    if not frappe.db.exists("DocType", "Inbound Shipment Notice Item"):
        child = frappe.get_doc(
            {
                "doctype": "DocType",
                "name": "Inbound Shipment Notice Item",
                "module": "Stock",
                "custom": 1,
                "istable": 1,
                "editable_grid": 1,
                "fields": [
                    {"fieldname": "item_code", "label": "Item", "fieldtype": "Link", "options": "Item", "reqd": 1, "in_list_view": 1},
                    {"fieldname": "item_name", "label": "Item Name", "fieldtype": "Data", "in_list_view": 1},
                    {"fieldname": "expected_qty", "label": "Expected Qty", "fieldtype": "Float", "reqd": 1, "in_list_view": 1},
                    {"fieldname": "uom", "label": "UOM", "fieldtype": "Link", "options": "UOM", "in_list_view": 1},
                    {"fieldname": "received_qty", "label": "Received Qty", "fieldtype": "Float", "in_list_view": 1},
                    {"fieldname": "variance_qty", "label": "Variance Qty", "fieldtype": "Float", "read_only": 1},
                    {"fieldname": "notes", "label": "Notes", "fieldtype": "Small Text"},
                ],
            }
        )
        child.name = "Inbound Shipment Notice Item"
        child.insert(ignore_permissions=True)

    if not frappe.db.exists("DocType", "Inbound Shipment Notice"):
        parent = frappe.get_doc(
            {
                "doctype": "DocType",
                "name": "Inbound Shipment Notice",
                "module": "Stock",
                "custom": 1,
                "is_submittable": 1,
                "track_changes": 1,
                "title_field": "external_reference",
                "fields": [
                    {"fieldname": "customer", "label": "Client", "fieldtype": "Link", "options": "Customer", "reqd": 1, "in_standard_filter": 1},
                    {"fieldname": "external_reference", "label": "Client Notice Ref", "fieldtype": "Data", "reqd": 1, "in_list_view": 1},
                    {"fieldname": "notice_date", "label": "Notice Date", "fieldtype": "Date", "default": "Today", "in_list_view": 1},
                    {"fieldname": "expected_arrival_date", "label": "Expected Arrival Date", "fieldtype": "Date", "in_list_view": 1},
                    {"fieldname": "temporary_warehouse", "label": "Temporary Warehouse", "fieldtype": "Link", "options": "Warehouse", "default": f"Temporary Receiving - {COMPANY_ABBR}"},
                    {"fieldname": "status", "label": "Status", "fieldtype": "Select", "options": "Draft\nPartially Received\nReceived\nClosed", "default": "Draft", "in_list_view": 1},
                    {"fieldname": "items_section", "label": "Expected Products", "fieldtype": "Section Break"},
                    {"fieldname": "items", "label": "Items", "fieldtype": "Table", "options": "Inbound Shipment Notice Item"},
                    {"fieldname": "notes", "label": "Notes", "fieldtype": "Small Text"},
                ],
                "permissions": [
                    {"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "cancel": 1, "amend": 1, "report": 1, "export": 1},
                    {"role": "Stock Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "cancel": 1, "amend": 1, "report": 1, "export": 1},
                    {"role": "Stock User", "read": 1, "write": 1, "create": 1, "submit": 1, "report": 1, "export": 1},
                    {"role": "3PL Warehouse Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "cancel": 1, "amend": 1, "report": 1, "export": 1},
                    {"role": "3PL Warehouse User", "read": 1, "write": 1, "create": 1, "submit": 1, "report": 1},
                ],
            }
        )
        parent.name = "Inbound Shipment Notice"
        parent.insert(ignore_permissions=True)


def configure_custom_fields():
    fields = {
        "Stock Entry": [
            {
                "fieldname": "client_section",
                "label": "3PL Client Tracking",
                "fieldtype": "Section Break",
                "insert_after": "stock_entry_type",
                "collapsible": 1,
            },
            {
                "fieldname": "client",
                "label": "Client",
                "fieldtype": "Link",
                "options": "Customer",
                "insert_after": "client_section",
                "in_standard_filter": 1,
            },
            {
                "fieldname": "inbound_shipment_notice",
                "label": "Inbound Shipment Notice",
                "fieldtype": "Link",
                "options": "Inbound Shipment Notice",
                "insert_after": "client",
                "depends_on": "eval:doc.client",
            },
            {
                "fieldname": "warehouse_flow",
                "label": "Warehouse Flow",
                "fieldtype": "Select",
                "options": "\nInbound Receipt\nComparison\nPut Away\nInternal Movement\nPicking Support\nPacking\nShipping",
                "insert_after": "inbound_shipment_notice",
                "in_standard_filter": 1,
            },
            {
                "fieldname": "scanned_location",
                "label": "Scanned Location",
                "fieldtype": "Link",
                "options": "Warehouse",
                "insert_after": "warehouse_flow",
                "description": "Use this to record the warehouse/location barcode scanned before scanning products.",
            },
        ],
        "Stock Entry Detail": [
            {
                "fieldname": "scanned_location",
                "label": "Scanned Location",
                "fieldtype": "Link",
                "options": "Warehouse",
                "insert_after": "barcode",
                "in_list_view": 1,
                "description": "Location scanned for this product row.",
            }
        ],
        "Pick List": [
            {
                "fieldname": "client_section",
                "label": "3PL Client Tracking",
                "fieldtype": "Section Break",
                "insert_after": "purpose",
                "collapsible": 1,
            },
            {
                "fieldname": "client",
                "label": "Client",
                "fieldtype": "Link",
                "options": "Customer",
                "insert_after": "client_section",
                "in_standard_filter": 1,
            },
            {
                "fieldname": "shipment_reference",
                "label": "Shipment Reference",
                "fieldtype": "Data",
                "insert_after": "client",
            },
        ],
        "Pick List Item": [
            {
                "fieldname": "scanned_location",
                "label": "Scanned Location",
                "fieldtype": "Link",
                "options": "Warehouse",
                "insert_after": "warehouse",
                "in_list_view": 1,
            }
        ],
    }
    create_custom_fields(fields, update=True)


def configure_defaults():
    settings = frappe.get_single("Stock Settings")
    settings.item_naming_by = "Item Code"
    settings.save(ignore_permissions=True)

    frappe.db.set_default("company", COMPANY)
    frappe.db.set_default("currency", "UAH")
    frappe.db.set_default("country", "Ukraine")


def main():
    configure_workspaces()
    configure_module_profile()
    configure_warehouses()
    configure_stock_entry_types()
    configure_custom_doctypes()
    configure_custom_fields()
    configure_defaults()
    frappe.db.commit()
    frappe.clear_cache()


main()
