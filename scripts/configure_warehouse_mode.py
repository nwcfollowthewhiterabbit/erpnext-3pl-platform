import json

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


COMPANY = "3pl"
COMPANY_ABBR = "3"
COUNTRY = "Lithuania"
CURRENCY = "EUR"
LANGUAGE = "en"
TIME_ZONE = "Europe/Vilnius"


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
    for name in frappe.get_all("Workspace", pluck="name"):
        frappe.db.set_value("Workspace", name, "is_hidden", 1, update_modified=True)

    workspaces = [
        {
            "name": "3PL Warehouse",
            "label": "3PL Warehouse",
            "title": "3PL Warehouse",
            "module": "Stock",
            "indicator_color": "green",
            "content": [
                {"id": "3pl_header", "type": "header", "data": {"text": '<span class="h4"><b>3PL Warehouse</b></span>', "col": 12}},
                {"id": "3pl_receiving", "type": "shortcut", "data": {"shortcut_name": "Receiving Notices", "col": 3}},
                {"id": "3pl_stock_entries", "type": "shortcut", "data": {"shortcut_name": "Stock Entries", "col": 3}},
                {"id": "3pl_pick_lists", "type": "shortcut", "data": {"shortcut_name": "Pick Lists", "col": 3}},
                {"id": "3pl_asn_report", "type": "shortcut", "data": {"shortcut_name": "ASN vs Received", "col": 3}},
                {"id": "3pl_spacer", "type": "spacer", "data": {"col": 12}},
                {"id": "3pl_reports_header", "type": "header", "data": {"text": '<span class="h4"><b>Reports and Masters</b></span>', "col": 12}},
                {"id": "3pl_items", "type": "shortcut", "data": {"shortcut_name": "Items", "col": 3}},
                {"id": "3pl_warehouses", "type": "shortcut", "data": {"shortcut_name": "Warehouses", "col": 3}},
                {"id": "3pl_stock_balance", "type": "shortcut", "data": {"shortcut_name": "Stock Balance", "col": 3}},
                {"id": "3pl_stock_ledger", "type": "shortcut", "data": {"shortcut_name": "Stock Ledger", "col": 3}},
            ],
            "shortcuts": [
                {"type": "DocType", "link_to": "Inbound Shipment Notice", "doc_view": "List", "label": "Receiving Notices"},
                {"type": "DocType", "link_to": "Stock Entry", "doc_view": "List", "label": "Stock Entries"},
                {"type": "DocType", "link_to": "Pick List", "doc_view": "List", "label": "Pick Lists"},
                {"type": "Report", "link_to": "3PL ASN vs Received", "label": "ASN vs Received", "report_ref_doctype": "Inbound Shipment Notice"},
                {"type": "DocType", "link_to": "Item", "doc_view": "List", "label": "Items"},
                {"type": "DocType", "link_to": "Warehouse", "doc_view": "Tree", "label": "Warehouses"},
                {"type": "Report", "link_to": "Stock Balance", "label": "Stock Balance", "report_ref_doctype": "Stock Ledger Entry"},
                {"type": "Report", "link_to": "Stock Ledger", "label": "Stock Ledger", "report_ref_doctype": "Stock Ledger Entry"},
            ],
            "links": [
                {"type": "Link", "label": "Receiving Notices", "link_type": "DocType", "link_to": "Inbound Shipment Notice"},
                {"type": "Link", "label": "Stock Entries", "link_type": "DocType", "link_to": "Stock Entry"},
                {"type": "Link", "label": "Pick Lists", "link_type": "DocType", "link_to": "Pick List"},
                {"type": "Link", "label": "Items", "link_type": "DocType", "link_to": "Item"},
                {"type": "Link", "label": "Warehouses", "link_type": "DocType", "link_to": "Warehouse"},
            ],
        },
        {
            "name": "Stock Reference",
            "label": "Stock Reference",
            "title": "Stock Reference",
            "module": "Stock",
            "indicator_color": "green",
            "content": [
                {"id": "stock_ref_header", "type": "header", "data": {"text": '<span class="h4"><b>Stock Reference</b></span>', "col": 12}},
                {"id": "stock_ref_items", "type": "shortcut", "data": {"shortcut_name": "Items", "col": 3}},
                {"id": "stock_ref_warehouses", "type": "shortcut", "data": {"shortcut_name": "Warehouses", "col": 3}},
                {"id": "stock_ref_spacer", "type": "spacer", "data": {"col": 12}},
                {"id": "stock_ref_reports_header", "type": "header", "data": {"text": '<span class="h4"><b>Stock Reports</b></span>', "col": 12}},
                {"id": "stock_ref_balance", "type": "shortcut", "data": {"shortcut_name": "Stock Balance", "col": 3}},
                {"id": "stock_ref_ledger", "type": "shortcut", "data": {"shortcut_name": "Stock Ledger", "col": 3}},
                {"id": "stock_ref_asn", "type": "shortcut", "data": {"shortcut_name": "ASN vs Received", "col": 3}},
            ],
            "shortcuts": [
                {"type": "DocType", "link_to": "Item", "doc_view": "List", "label": "Items"},
                {"type": "DocType", "link_to": "Warehouse", "doc_view": "Tree", "label": "Warehouses"},
                {"type": "Report", "link_to": "Stock Balance", "label": "Stock Balance", "report_ref_doctype": "Stock Ledger Entry"},
                {"type": "Report", "link_to": "Stock Ledger", "label": "Stock Ledger", "report_ref_doctype": "Stock Ledger Entry"},
                {"type": "Report", "link_to": "3PL ASN vs Received", "label": "ASN vs Received", "report_ref_doctype": "Inbound Shipment Notice"},
            ],
            "links": [
                {"type": "Link", "label": "Items", "link_type": "DocType", "link_to": "Item"},
                {"type": "Link", "label": "Warehouses", "link_type": "DocType", "link_to": "Warehouse"},
            ],
        },
    ]

    for workspace_data in workspaces:
        if frappe.db.exists("Workspace", workspace_data["name"]):
            doc = frappe.get_doc("Workspace", workspace_data["name"])
            doc.set("shortcuts", [])
            doc.set("links", [])
        else:
            doc = frappe.new_doc("Workspace")
            doc.name = workspace_data["name"]

        for field in ("label", "title", "module", "indicator_color"):
            setattr(doc, field, workspace_data[field])
        doc.public = 1
        doc.is_hidden = 0
        doc.content = json.dumps(workspace_data["content"])

        for shortcut in workspace_data["shortcuts"]:
            doc.append("shortcuts", shortcut)
        for link in workspace_data["links"]:
            doc.append("links", link)

        doc.save(ignore_permissions=True)


def configure_company():
    if not frappe.db.exists("Warehouse Type", "Transit"):
        frappe.get_doc({"doctype": "Warehouse Type", "name": "Transit"}).insert(ignore_permissions=True)

    if frappe.db.exists("Company", COMPANY):
        company = frappe.get_doc("Company", COMPANY)
        if company.default_currency != CURRENCY:
            for account in frappe.get_all("Account", filters={"company": COMPANY}, pluck="name"):
                frappe.db.set_value("Account", account, "account_currency", CURRENCY, update_modified=False)

        changed = False
        expected = {
            "company_name": COMPANY,
            "abbr": COMPANY_ABBR,
            "default_currency": CURRENCY,
            "country": COUNTRY,
        }
        for key, value in expected.items():
            if getattr(company, key, None) != value:
                setattr(company, key, value)
                changed = True
        if changed:
            company.save(ignore_permissions=True)
    else:
        frappe.get_doc(
            {
                "doctype": "Company",
                "company_name": COMPANY,
                "abbr": COMPANY_ABBR,
                "default_currency": CURRENCY,
                "country": COUNTRY,
            }
        ).insert(ignore_permissions=True)

    root = f"All Warehouses - {COMPANY_ABBR}"
    if not frappe.db.exists("Warehouse", root):
        frappe.get_doc(
            {
                "doctype": "Warehouse",
                "warehouse_name": "All Warehouses",
                "company": COMPANY,
                "is_group": 1,
                "parent_warehouse": None,
            }
        ).insert(ignore_permissions=True)


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

    for role_name in ("Stock User", "Stock Manager", "3PL Warehouse User", "3PL Warehouse Manager"):
        if frappe.db.exists("Role", role_name):
            frappe.db.set_value("Role", role_name, "home_page", "app/3pl-warehouse")

    frappe.db.set_default("desktop:home_page", "workspace")


def configure_desk_permissions():
    from frappe.permissions import add_permission

    for role_name in ("3PL Warehouse User", "3PL Warehouse Manager"):
        existing = frappe.db.exists(
            "Custom DocPerm",
            {
                "parent": "Page",
                "role": role_name,
                "permlevel": 0,
                "if_owner": 0,
                "read": 1,
            },
        )
        if not existing:
            add_permission("Page", role_name, 0, "read")


def mark_setup_complete():
    if frappe.db.table_exists("Installed Application"):
        for app_name in ("frappe", "erpnext"):
            if frappe.db.exists("Installed Application", {"app_name": app_name}):
                frappe.db.set_value("Installed Application", {"app_name": app_name}, "is_setup_complete", 1)

    if frappe.db.exists("DocType", "System Settings"):
        frappe.db.set_single_value("System Settings", "setup_complete", frappe.is_setup_complete())


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


def configure_reports():
    query = """
select
    isn.name as "Notice:Link/Inbound Shipment Notice:150",
    isn.external_reference as "Client Notice Ref:Data:150",
    isn.customer as "Client:Link/Customer:170",
    item.item_code as "Item:Link/Item:150",
    item.expected_qty as "Expected Qty:Float:110",
    item.received_qty as "Received Qty:Float:110",
    item.variance_qty as "Variance Qty:Float:110",
    isn.status as "Status:Data:120"
from `tabInbound Shipment Notice` isn
inner join `tabInbound Shipment Notice Item` item on item.parent = isn.name
order by isn.creation desc, item.idx asc
""".strip()

    if frappe.db.exists("Report", "3PL ASN vs Received"):
        report = frappe.get_doc("Report", "3PL ASN vs Received")
    else:
        report = frappe.new_doc("Report")
        report.report_name = "3PL ASN vs Received"

    report.ref_doctype = "Inbound Shipment Notice"
    report.report_type = "Query Report"
    report.is_standard = "No"
    report.module = "Stock"
    report.query = query
    report.save(ignore_permissions=True)


def configure_defaults():
    settings = frappe.get_single("Stock Settings")
    settings.item_naming_by = "Item Code"
    settings.save(ignore_permissions=True)

    system_settings = frappe.get_single("System Settings")
    system_settings.country = COUNTRY
    system_settings.currency = CURRENCY
    system_settings.language = LANGUAGE
    system_settings.time_zone = TIME_ZONE
    system_settings.save(ignore_permissions=True)

    frappe.db.set_default("company", COMPANY)
    frappe.db.set_default("currency", CURRENCY)
    frappe.db.set_default("country", COUNTRY)


def main():
    configure_company()
    configure_module_profile()
    configure_desk_permissions()
    configure_warehouses()
    configure_stock_entry_types()
    configure_custom_doctypes()
    configure_custom_fields()
    configure_reports()
    configure_workspaces()
    configure_defaults()
    mark_setup_complete()
    frappe.db.commit()
    frappe.clear_cache()


main()
