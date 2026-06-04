import json

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


COMPANY = "3pl"
COMPANY_ABBR = "3"
COUNTRY = "Lithuania"
CURRENCY = "EUR"
LANGUAGE = "en"
TIME_ZONE = "Europe/Vilnius"
PLACEHOLDER_EMAIL = "noreply@example.invalid"


def ensure_child_field(doc, field):
    if not any(row.fieldname == field["fieldname"] for row in doc.fields):
        doc.append("fields", field)
        return True
    return False


def ensure_doctype_fields(doctype, fields):
    doc = frappe.get_doc("DocType", doctype)
    changed = False
    for field in fields:
        changed = ensure_child_field(doc, field) or changed
    if changed:
        doc.save(ignore_permissions=True)


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
                {"id": "3pl_containers", "type": "shortcut", "data": {"shortcut_name": "Containers", "col": 3}},
                {"id": "3pl_stock_entries", "type": "shortcut", "data": {"shortcut_name": "Stock Entries", "col": 3}},
                {"id": "3pl_pick_lists", "type": "shortcut", "data": {"shortcut_name": "Pick Lists", "col": 3}},
                {"id": "3pl_shipment_requests", "type": "shortcut", "data": {"shortcut_name": "Shipment Requests", "col": 3}},
                {"id": "3pl_asn_report", "type": "shortcut", "data": {"shortcut_name": "ASN vs Received", "col": 3}},
                {"id": "3pl_discrepancies", "type": "shortcut", "data": {"shortcut_name": "Receiving Discrepancies", "col": 3}},
                {"id": "3pl_client_inventory", "type": "shortcut", "data": {"shortcut_name": "Client Inventory", "col": 3}},
                {"id": "3pl_client_instructions", "type": "shortcut", "data": {"shortcut_name": "Client Instructions", "col": 3}},
                {"id": "3pl_spacer", "type": "spacer", "data": {"col": 12}},
                {"id": "3pl_reports_header", "type": "header", "data": {"text": '<span class="h4"><b>Reports and Masters</b></span>', "col": 12}},
                {"id": "3pl_items", "type": "shortcut", "data": {"shortcut_name": "Items", "col": 3}},
                {"id": "3pl_warehouses", "type": "shortcut", "data": {"shortcut_name": "Warehouses", "col": 3}},
                {"id": "3pl_stock_balance", "type": "shortcut", "data": {"shortcut_name": "Stock Balance", "col": 3}},
                {"id": "3pl_stock_ledger", "type": "shortcut", "data": {"shortcut_name": "Stock Ledger", "col": 3}},
            ],
            "shortcuts": [
                {"type": "DocType", "link_to": "Inbound Shipment Notice", "doc_view": "List", "label": "Receiving Notices"},
                {"type": "DocType", "link_to": "Three PL Container", "doc_view": "List", "label": "Containers"},
                {"type": "DocType", "link_to": "Stock Entry", "doc_view": "List", "label": "Stock Entries"},
                {"type": "DocType", "link_to": "Pick List", "doc_view": "List", "label": "Pick Lists"},
                {"type": "DocType", "link_to": "Three PL Shipment Request", "doc_view": "List", "label": "Shipment Requests"},
                {"type": "Report", "link_to": "3PL ASN vs Received", "label": "ASN vs Received", "report_ref_doctype": "Inbound Shipment Notice"},
                {"type": "Report", "link_to": "3PL Receiving Discrepancies", "label": "Receiving Discrepancies", "report_ref_doctype": "Inbound Shipment Notice"},
                {"type": "Report", "link_to": "3PL Containers", "label": "Containers Report", "report_ref_doctype": "Three PL Container"},
                {"type": "Report", "link_to": "3PL Client Inventory", "label": "Client Inventory", "report_ref_doctype": "Three PL Inventory Snapshot"},
                {"type": "DocType", "link_to": "Three PL Client Instruction", "doc_view": "List", "label": "Client Instructions"},
                {"type": "DocType", "link_to": "Item", "doc_view": "List", "label": "Items"},
                {"type": "DocType", "link_to": "Warehouse", "doc_view": "Tree", "label": "Warehouses"},
                {"type": "Report", "link_to": "Stock Balance", "label": "Stock Balance", "report_ref_doctype": "Stock Ledger Entry"},
                {"type": "Report", "link_to": "Stock Ledger", "label": "Stock Ledger", "report_ref_doctype": "Stock Ledger Entry"},
            ],
            "links": [
                {"type": "Link", "label": "Receiving Notices", "link_type": "DocType", "link_to": "Inbound Shipment Notice"},
                {"type": "Link", "label": "Containers", "link_type": "DocType", "link_to": "Three PL Container"},
                {"type": "Link", "label": "Stock Entries", "link_type": "DocType", "link_to": "Stock Entry"},
                {"type": "Link", "label": "Pick Lists", "link_type": "DocType", "link_to": "Pick List"},
                {"type": "Link", "label": "Shipment Requests", "link_type": "DocType", "link_to": "Three PL Shipment Request"},
                {"type": "Link", "label": "Client Instructions", "link_type": "DocType", "link_to": "Three PL Client Instruction"},
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

    for role_name in ("3PL Warehouse User", "3PL Warehouse Manager", "3PL Client"):
        if not frappe.db.exists("Role", role_name):
            frappe.get_doc({"doctype": "Role", "role_name": role_name}).insert(ignore_permissions=True)

    if frappe.db.exists("Role", "3PL Client"):
        role = frappe.get_doc("Role", "3PL Client")
        changed = False
        if role.meta.has_field("desk_access") and role.desk_access:
            role.desk_access = 0
            changed = True
        if role.home_page != "client/receiving-notice":
            role.home_page = "client/receiving-notice"
            changed = True
        if changed:
            role.save(ignore_permissions=True)

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
                    {"fieldname": "client_sku", "label": "Client SKU", "fieldtype": "Data", "in_list_view": 1},
                    {"fieldname": "item_name", "label": "Item Name", "fieldtype": "Data", "in_list_view": 1},
                    {"fieldname": "expected_qty", "label": "Expected Qty", "fieldtype": "Float", "reqd": 1, "in_list_view": 1},
                    {"fieldname": "uom", "label": "UOM", "fieldtype": "Link", "options": "UOM", "in_list_view": 1},
                    {"fieldname": "received_qty", "label": "Received Qty", "fieldtype": "Float", "in_list_view": 1},
                    {"fieldname": "variance_qty", "label": "Variance Qty", "fieldtype": "Float", "read_only": 1},
                    {"fieldname": "condition_status", "label": "Condition", "fieldtype": "Select", "options": "\nOK\nDamaged\nQuality Issue\nHold", "in_list_view": 1},
                    {"fieldname": "notes", "label": "Notes", "fieldtype": "Small Text"},
                ],
            }
        )
        child.name = "Inbound Shipment Notice Item"
        child.insert(ignore_permissions=True)
    else:
        ensure_doctype_fields(
            "Inbound Shipment Notice Item",
            [
                {"fieldname": "client_sku", "label": "Client SKU", "fieldtype": "Data", "insert_after": "item_code", "in_list_view": 1},
                {"fieldname": "condition_status", "label": "Condition", "fieldtype": "Select", "options": "\nOK\nDamaged\nQuality Issue\nHold", "insert_after": "variance_qty", "in_list_view": 1},
            ],
        )

    if not frappe.db.exists("DocType", "Inbound Shipment Discrepancy"):
        discrepancy = frappe.get_doc(
            {
                "doctype": "DocType",
                "name": "Inbound Shipment Discrepancy",
                "module": "Stock",
                "custom": 1,
                "istable": 1,
                "editable_grid": 1,
                "fields": [
                    {"fieldname": "discrepancy_type", "label": "Type", "fieldtype": "Select", "options": "Missing Product\nUnexpected Product\nQuantity Difference\nDamaged Product\nQuality Issue", "reqd": 1, "in_list_view": 1},
                    {"fieldname": "item_code", "label": "Item", "fieldtype": "Link", "options": "Item", "in_list_view": 1},
                    {"fieldname": "client_sku", "label": "Client SKU", "fieldtype": "Data", "in_list_view": 1},
                    {"fieldname": "expected_qty", "label": "Expected Qty", "fieldtype": "Float", "in_list_view": 1},
                    {"fieldname": "actual_qty", "label": "Actual Qty", "fieldtype": "Float", "in_list_view": 1},
                    {"fieldname": "variance_qty", "label": "Variance Qty", "fieldtype": "Float", "in_list_view": 1},
                    {"fieldname": "status", "label": "Status", "fieldtype": "Select", "options": "Open\nClient Notified\nInstruction Received\nResolved", "default": "Open", "in_list_view": 1},
                    {"fieldname": "notes", "label": "Notes", "fieldtype": "Small Text"},
                ],
            }
        )
        discrepancy.name = "Inbound Shipment Discrepancy"
        discrepancy.insert(ignore_permissions=True)

    if not frappe.db.exists("DocType", "Three PL Shipment Request Item"):
        shipment_item = frappe.get_doc(
            {
                "doctype": "DocType",
                "name": "Three PL Shipment Request Item",
                "module": "Stock",
                "custom": 1,
                "istable": 1,
                "editable_grid": 1,
                "fields": [
                    {"fieldname": "item_code", "label": "Item", "fieldtype": "Link", "options": "Item", "reqd": 1, "in_list_view": 1},
                    {"fieldname": "client_sku", "label": "Client SKU", "fieldtype": "Data", "in_list_view": 1},
                    {"fieldname": "qty", "label": "Qty", "fieldtype": "Float", "reqd": 1, "in_list_view": 1},
                    {"fieldname": "uom", "label": "UOM", "fieldtype": "Link", "options": "UOM", "in_list_view": 1},
                    {"fieldname": "notes", "label": "Notes", "fieldtype": "Small Text"},
                ],
            }
        )
        shipment_item.name = "Three PL Shipment Request Item"
        shipment_item.insert(ignore_permissions=True)

    if not frappe.db.exists("DocType", "Three PL Container Item"):
        container_item = frappe.get_doc(
            {
                "doctype": "DocType",
                "name": "Three PL Container Item",
                "module": "Stock",
                "custom": 1,
                "istable": 1,
                "editable_grid": 1,
                "fields": [
                    {"fieldname": "item_code", "label": "Item", "fieldtype": "Link", "options": "Item", "reqd": 1, "in_list_view": 1},
                    {"fieldname": "client_sku", "label": "Client SKU", "fieldtype": "Data", "in_list_view": 1},
                    {"fieldname": "qty", "label": "Qty", "fieldtype": "Float", "reqd": 1, "in_list_view": 1},
                    {"fieldname": "uom", "label": "UOM", "fieldtype": "Link", "options": "UOM", "in_list_view": 1},
                    {"fieldname": "condition_status", "label": "Condition", "fieldtype": "Select", "options": "\nOK\nDamaged\nQuality Issue\nHold", "default": "OK", "in_list_view": 1},
                    {"fieldname": "notes", "label": "Notes", "fieldtype": "Small Text"},
                ],
            }
        )
        container_item.name = "Three PL Container Item"
        container_item.insert(ignore_permissions=True)
    else:
        ensure_doctype_fields(
            "Three PL Container Item",
            [
                {"fieldname": "client_sku", "label": "Client SKU", "fieldtype": "Data", "insert_after": "item_code", "in_list_view": 1},
                {"fieldname": "condition_status", "label": "Condition", "fieldtype": "Select", "options": "\nOK\nDamaged\nQuality Issue\nHold", "default": "OK", "insert_after": "uom", "in_list_view": 1},
            ],
        )

    if not frappe.db.exists("DocType", "Three PL Container"):
        container = frappe.get_doc(
            {
                "doctype": "DocType",
                "name": "Three PL Container",
                "module": "Stock",
                "custom": 1,
                "track_changes": 1,
                "title_field": "container_code",
                "autoname": "field:container_code",
                "fields": [
                    {"fieldname": "container_code", "label": "Container / Box Code", "fieldtype": "Data", "reqd": 1, "unique": 1, "in_list_view": 1},
                    {"fieldname": "barcode", "label": "Barcode / Label", "fieldtype": "Data", "in_list_view": 1},
                    {"fieldname": "client", "label": "Client", "fieldtype": "Link", "options": "Customer", "reqd": 1, "in_standard_filter": 1, "in_list_view": 1},
                    {"fieldname": "current_warehouse", "label": "Current Location", "fieldtype": "Link", "options": "Warehouse", "in_standard_filter": 1, "in_list_view": 1},
                    {"fieldname": "status", "label": "Status", "fieldtype": "Select", "options": "Expected\nReceived\nIn Verification\nReady for Putaway\nStored\nPicked\nShipped\nClosed", "default": "Expected", "in_list_view": 1},
                    {"fieldname": "items_section", "label": "Contents", "fieldtype": "Section Break"},
                    {"fieldname": "items", "label": "Items", "fieldtype": "Table", "options": "Three PL Container Item"},
                    {"fieldname": "notes", "label": "Notes", "fieldtype": "Small Text"},
                ],
                "permissions": [
                    {"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1},
                    {"role": "Stock Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1},
                    {"role": "Stock User", "read": 1, "write": 1, "create": 1, "report": 1},
                    {"role": "3PL Warehouse Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1},
                    {"role": "3PL Warehouse User", "read": 1, "write": 1, "create": 1, "report": 1},
                ],
            }
        )
        container.name = "Three PL Container"
        container.insert(ignore_permissions=True)

    if not frappe.db.exists("DocType", "Three PL Inventory Snapshot"):
        inventory = frappe.get_doc(
            {
                "doctype": "DocType",
                "name": "Three PL Inventory Snapshot",
                "module": "Stock",
                "custom": 1,
                "track_changes": 1,
                "title_field": "item_code",
                "autoname": "format:{customer}-.{item_code}-.{container_code}",
                "fields": [
                    {"fieldname": "customer", "label": "Client", "fieldtype": "Link", "options": "Customer", "reqd": 1, "in_standard_filter": 1, "in_list_view": 1},
                    {"fieldname": "item_code", "label": "Item", "fieldtype": "Link", "options": "Item", "reqd": 1, "in_standard_filter": 1, "in_list_view": 1},
                    {"fieldname": "client_sku", "label": "Client SKU", "fieldtype": "Data", "in_list_view": 1},
                    {"fieldname": "item_name", "label": "Item Name", "fieldtype": "Data", "in_list_view": 1},
                    {"fieldname": "qty", "label": "Qty", "fieldtype": "Float", "in_list_view": 1},
                    {"fieldname": "uom", "label": "UOM", "fieldtype": "Link", "options": "UOM", "in_list_view": 1},
                    {"fieldname": "warehouse", "label": "Location", "fieldtype": "Link", "options": "Warehouse", "in_standard_filter": 1, "in_list_view": 1},
                    {"fieldname": "container_code", "label": "Container / Box", "fieldtype": "Link", "options": "Three PL Container", "in_standard_filter": 1, "in_list_view": 1},
                    {"fieldname": "status", "label": "Status", "fieldtype": "Select", "options": "Available\nReceiving\nHold\nAllocated\nShipped", "default": "Available", "in_list_view": 1},
                    {"fieldname": "last_updated", "label": "Last Updated", "fieldtype": "Datetime", "read_only": 1},
                    {"fieldname": "notes", "label": "Notes", "fieldtype": "Small Text"},
                ],
                "permissions": [
                    {"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1},
                    {"role": "Stock Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1},
                    {"role": "3PL Warehouse Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1},
                    {"role": "3PL Warehouse User", "read": 1, "report": 1},
                    {"role": "3PL Client", "read": 1},
                ],
            }
        )
        inventory.name = "Three PL Inventory Snapshot"
        inventory.insert(ignore_permissions=True)

    if not frappe.db.exists("DocType", "Three PL Shipment Request"):
        shipment = frappe.get_doc(
            {
                "doctype": "DocType",
                "name": "Three PL Shipment Request",
                "module": "Stock",
                "custom": 1,
                "track_changes": 1,
                "title_field": "external_reference",
                "fields": [
                    {"fieldname": "customer", "label": "Client", "fieldtype": "Link", "options": "Customer", "reqd": 1, "in_standard_filter": 1, "in_list_view": 1},
                    {"fieldname": "external_reference", "label": "Client Shipment Ref", "fieldtype": "Data", "reqd": 1, "in_list_view": 1},
                    {"fieldname": "requested_ship_date", "label": "Requested Ship Date", "fieldtype": "Date", "in_list_view": 1},
                    {"fieldname": "status", "label": "Status", "fieldtype": "Select", "options": "Draft\nSubmitted\nAccepted\nPicking\nPacked\nShipped\nClosed\nCancelled", "default": "Submitted", "in_standard_filter": 1, "in_list_view": 1},
                    {"fieldname": "destination_name", "label": "Destination Name", "fieldtype": "Data"},
                    {"fieldname": "destination_address", "label": "Destination Address", "fieldtype": "Small Text"},
                    {"fieldname": "portal_source", "label": "Portal Source", "fieldtype": "Check", "default": 0},
                    {"fieldname": "items_section", "label": "Requested Products", "fieldtype": "Section Break"},
                    {"fieldname": "items", "label": "Items", "fieldtype": "Table", "options": "Three PL Shipment Request Item"},
                    {"fieldname": "notes", "label": "Notes", "fieldtype": "Small Text"},
                ],
                "permissions": [
                    {"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1},
                    {"role": "Stock Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1},
                    {"role": "3PL Warehouse Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1},
                    {"role": "3PL Warehouse User", "read": 1, "write": 1, "create": 1, "report": 1},
                    {"role": "3PL Client", "read": 1, "write": 1, "create": 1},
                ],
            }
        )
        shipment.name = "Three PL Shipment Request"
        shipment.insert(ignore_permissions=True)

    if not frappe.db.exists("DocType", "Three PL Client Instruction"):
        instruction = frappe.get_doc(
            {
                "doctype": "DocType",
                "name": "Three PL Client Instruction",
                "module": "Stock",
                "custom": 1,
                "track_changes": 1,
                "title_field": "receiving_notice",
                "fields": [
                    {"fieldname": "customer", "label": "Client", "fieldtype": "Link", "options": "Customer", "reqd": 1, "in_standard_filter": 1, "in_list_view": 1},
                    {"fieldname": "receiving_notice", "label": "Receiving Notice", "fieldtype": "Link", "options": "Inbound Shipment Notice", "reqd": 1, "in_standard_filter": 1, "in_list_view": 1},
                    {"fieldname": "item_code", "label": "Item", "fieldtype": "Link", "options": "Item", "in_list_view": 1},
                    {"fieldname": "client_sku", "label": "Client SKU", "fieldtype": "Data", "in_list_view": 1},
                    {"fieldname": "instruction_type", "label": "Instruction Type", "fieldtype": "Select", "options": "Accept Difference\nReturn Goods\nHold For Review\nDispose Damaged Goods\nOther", "default": "Hold For Review", "in_list_view": 1},
                    {"fieldname": "status", "label": "Status", "fieldtype": "Select", "options": "Submitted\nReviewed\nApplied\nClosed", "default": "Submitted", "in_standard_filter": 1, "in_list_view": 1},
                    {"fieldname": "portal_source", "label": "Portal Source", "fieldtype": "Check", "default": 0},
                    {"fieldname": "instruction_text", "label": "Instruction", "fieldtype": "Small Text", "reqd": 1},
                ],
                "permissions": [
                    {"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1},
                    {"role": "Stock Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1},
                    {"role": "3PL Warehouse Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1},
                    {"role": "3PL Warehouse User", "read": 1, "write": 1, "create": 1, "report": 1},
                    {"role": "3PL Client", "read": 1, "write": 1, "create": 1},
                ],
            }
        )
        instruction.name = "Three PL Client Instruction"
        instruction.insert(ignore_permissions=True)

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
                    {"fieldname": "discrepancy_section", "label": "Discrepancies", "fieldtype": "Section Break"},
                    {"fieldname": "discrepancies", "label": "Discrepancies", "fieldtype": "Table", "options": "Inbound Shipment Discrepancy"},
                    {"fieldname": "notes", "label": "Notes", "fieldtype": "Small Text"},
                ],
                "permissions": [
                    {"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "cancel": 1, "amend": 1, "report": 1, "export": 1},
                    {"role": "Stock Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "cancel": 1, "amend": 1, "report": 1, "export": 1},
                    {"role": "Stock User", "read": 1, "write": 1, "create": 1, "submit": 1, "report": 1, "export": 1},
                    {"role": "3PL Warehouse Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "cancel": 1, "amend": 1, "report": 1, "export": 1},
                    {"role": "3PL Warehouse User", "read": 1, "write": 1, "create": 1, "submit": 1, "report": 1},
                    {"role": "3PL Client", "read": 1, "write": 1, "create": 1},
                ],
            }
        )
        parent.name = "Inbound Shipment Notice"
        parent.insert(ignore_permissions=True)
    else:
        ensure_doctype_fields(
            "Inbound Shipment Notice",
            [
                {"fieldname": "portal_source", "label": "Portal Source", "fieldtype": "Check", "insert_after": "external_reference"},
                {"fieldname": "client_instruction_status", "label": "Client Instruction Status", "fieldtype": "Select", "options": "\nNot Required\nWaiting for Client\nInstruction Received", "default": "Not Required", "insert_after": "status", "in_standard_filter": 1},
                {"fieldname": "discrepancy_section", "label": "Discrepancies", "fieldtype": "Section Break", "insert_after": "items"},
                {"fieldname": "discrepancies", "label": "Discrepancies", "fieldtype": "Table", "options": "Inbound Shipment Discrepancy", "insert_after": "discrepancy_section"},
            ],
        )

    ensure_doctype_fields(
        "Inbound Shipment Notice Item",
        [
            {"fieldname": "container_code", "label": "Container / Box", "fieldtype": "Link", "options": "Three PL Container", "insert_after": "variance_qty", "in_list_view": 1},
        ],
    )
    ensure_doctype_fields(
        "Inbound Shipment Discrepancy",
        [
            {"fieldname": "container_code", "label": "Container / Box", "fieldtype": "Link", "options": "Three PL Container", "insert_after": "variance_qty", "in_list_view": 1},
        ],
    )
    ensure_doctype_fields(
        "Three PL Container",
        [
            {"fieldname": "inbound_shipment_notice", "label": "Receiving Notice", "fieldtype": "Link", "options": "Inbound Shipment Notice", "insert_after": "current_warehouse", "in_standard_filter": 1},
        ],
    )

    client_permissions = {
        "Inbound Shipment Notice": {"read": 1, "write": 1, "create": 1},
        "Item": {"read": 1},
        "Three PL Container": {"read": 1},
        "Three PL Inventory Snapshot": {"read": 1},
        "Three PL Shipment Request": {"read": 1, "write": 1, "create": 1},
        "Three PL Client Instruction": {"read": 1, "write": 1, "create": 1},
    }
    for doctype, permissions in client_permissions.items():
        ensure_docperm(doctype, "3PL Client", **permissions)


def ensure_docperm(doctype, role, **permissions):
    filters = {"parent": doctype, "role": role, "permlevel": 0}
    if frappe.db.exists("Custom DocPerm", filters):
        row = frappe.get_doc("Custom DocPerm", filters)
    else:
        row = frappe.get_doc(
            {
                "doctype": "Custom DocPerm",
                "parent": doctype,
                "parenttype": "DocType",
                "parentfield": "permissions",
                "role": role,
                "permlevel": 0,
            }
        )
    changed = False
    for field, value in permissions.items():
        if getattr(row, field, 0) != value:
            setattr(row, field, value)
            changed = True
    if changed:
        if row.is_new():
            row.insert(ignore_permissions=True)
        else:
            row.save(ignore_permissions=True)


def configure_custom_fields():
    fields = {
        "Item": [
            {
                "fieldname": "three_pl_ownership_section",
                "label": "3PL Ownership",
                "fieldtype": "Section Break",
                "insert_after": "item_group",
                "collapsible": 1,
            },
            {
                "fieldname": "owner_client",
                "label": "Owner Client",
                "fieldtype": "Link",
                "options": "Customer",
                "insert_after": "three_pl_ownership_section",
                "in_standard_filter": 1,
            },
            {
                "fieldname": "client_sku",
                "label": "Client SKU",
                "fieldtype": "Data",
                "insert_after": "owner_client",
                "in_standard_filter": 1,
                "description": "Client-facing SKU. Business uniqueness is Owner Client + Client SKU.",
            },
            {
                "fieldname": "client_product_name",
                "label": "Client Product Name",
                "fieldtype": "Data",
                "insert_after": "client_sku",
            },
        ],
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
            {
                "fieldname": "container_code",
                "label": "Container / Box",
                "fieldtype": "Link",
                "options": "Three PL Container",
                "insert_after": "scanned_location",
                "description": "Container or box scanned during receiving, putaway, picking, packing, or shipping.",
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
            },
            {
                "fieldname": "container_code",
                "label": "Container / Box",
                "fieldtype": "Link",
                "options": "Three PL Container",
                "insert_after": "scanned_location",
                "in_list_view": 1,
            },
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
            {
                "fieldname": "container_code",
                "label": "Container / Box",
                "fieldtype": "Link",
                "options": "Three PL Container",
                "insert_after": "shipment_reference",
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
            },
            {
                "fieldname": "container_code",
                "label": "Container / Box",
                "fieldtype": "Link",
                "options": "Three PL Container",
                "insert_after": "scanned_location",
                "in_list_view": 1,
            },
        ],
    }
    create_custom_fields(fields, update=True)


def configure_client_portal():
    configure_portal_web_form(
        form_name="3PL Client Receiving Notice",
        route="client/receiving-notice",
        doc_type="Inbound Shipment Notice",
        list_title="Receiving Notices",
        button_label="Submit Receiving Notice",
        introduction_text="Create and review receiving notices for inbound warehouse shipments.",
        success_title="Receiving Notice Submitted",
        success_message="The warehouse team can now review the expected inbound shipment.",
        fields=[
            {"fieldname": "customer", "fieldtype": "Link", "label": "Client", "options": "Customer", "reqd": 1, "show_in_filter": 1},
            {"fieldname": "external_reference", "fieldtype": "Data", "label": "Client Notice Ref", "reqd": 1, "show_in_filter": 1},
            {"fieldname": "expected_arrival_date", "fieldtype": "Date", "label": "Expected Arrival Date", "reqd": 1},
            {"fieldname": "items", "fieldtype": "Table", "label": "Expected Products", "options": "Inbound Shipment Notice Item", "reqd": 1},
            {"fieldname": "notes", "fieldtype": "Small Text", "label": "Notes"},
        ],
    )
    configure_portal_web_form(
        form_name="3PL Client Inventory",
        route="client/inventory",
        doc_type="Three PL Inventory Snapshot",
        list_title="Inventory",
        button_label="View Inventory",
        introduction_text="Review current inventory snapshots for your products.",
        success_title="Inventory",
        success_message="",
        allow_edit=0,
        allow_multiple=0,
        fields=[
            {"fieldname": "customer", "fieldtype": "Link", "label": "Client", "options": "Customer", "read_only": 1, "show_in_filter": 1},
            {"fieldname": "item_code", "fieldtype": "Link", "label": "Item", "options": "Item", "read_only": 1, "show_in_filter": 1},
            {"fieldname": "client_sku", "fieldtype": "Data", "label": "Client SKU", "read_only": 1},
            {"fieldname": "item_name", "fieldtype": "Data", "label": "Item Name", "read_only": 1},
            {"fieldname": "qty", "fieldtype": "Float", "label": "Qty", "read_only": 1},
            {"fieldname": "uom", "fieldtype": "Link", "label": "UOM", "options": "UOM", "read_only": 1},
            {"fieldname": "warehouse", "fieldtype": "Link", "label": "Location", "options": "Warehouse", "read_only": 1},
            {"fieldname": "container_code", "fieldtype": "Link", "label": "Container / Box", "options": "Three PL Container", "read_only": 1},
            {"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Available\nReceiving\nHold\nAllocated\nShipped", "read_only": 1},
        ],
    )
    configure_portal_web_form(
        form_name="3PL Client Shipment Request",
        route="client/shipment-request",
        doc_type="Three PL Shipment Request",
        list_title="Shipment Requests",
        button_label="Submit Shipment Request",
        introduction_text="Create outbound shipment requests for products stored in the warehouse.",
        success_title="Shipment Request Submitted",
        success_message="The warehouse team can now review and start picking.",
        fields=[
            {"fieldname": "customer", "fieldtype": "Link", "label": "Client", "options": "Customer", "reqd": 1, "show_in_filter": 1},
            {"fieldname": "external_reference", "fieldtype": "Data", "label": "Client Shipment Ref", "reqd": 1, "show_in_filter": 1},
            {"fieldname": "requested_ship_date", "fieldtype": "Date", "label": "Requested Ship Date", "reqd": 1},
            {"fieldname": "destination_name", "fieldtype": "Data", "label": "Destination Name", "reqd": 1},
            {"fieldname": "destination_address", "fieldtype": "Small Text", "label": "Destination Address", "reqd": 1},
            {"fieldname": "items", "fieldtype": "Table", "label": "Products To Ship", "options": "Three PL Shipment Request Item", "reqd": 1},
            {"fieldname": "notes", "fieldtype": "Small Text", "label": "Notes"},
        ],
    )
    configure_portal_web_form(
        form_name="3PL Client Discrepancy Instruction",
        route="client/discrepancy-instruction",
        doc_type="Three PL Client Instruction",
        list_title="Discrepancy Instructions",
        button_label="Submit Instruction",
        introduction_text="Send warehouse instructions for receiving discrepancies.",
        success_title="Instruction Submitted",
        success_message="The warehouse team can now review your instruction.",
        fields=[
            {"fieldname": "customer", "fieldtype": "Link", "label": "Client", "options": "Customer", "reqd": 1, "show_in_filter": 1},
            {"fieldname": "receiving_notice", "fieldtype": "Link", "label": "Receiving Notice", "options": "Inbound Shipment Notice", "reqd": 1, "show_in_filter": 1},
            {"fieldname": "item_code", "fieldtype": "Link", "label": "Item", "options": "Item"},
            {"fieldname": "client_sku", "fieldtype": "Data", "label": "Client SKU"},
            {"fieldname": "instruction_type", "fieldtype": "Select", "label": "Instruction Type", "options": "Accept Difference\nReturn Goods\nHold For Review\nDispose Damaged Goods\nOther", "reqd": 1},
            {"fieldname": "instruction_text", "fieldtype": "Small Text", "label": "Instruction", "reqd": 1},
        ],
    )

    configure_portal_menu()


def configure_portal_web_form(
    form_name,
    route,
    doc_type,
    list_title,
    button_label,
    introduction_text,
    success_title,
    success_message,
    fields,
    allow_edit=1,
    allow_multiple=1,
):
    existing_form = frappe.db.get_value("Web Form", {"route": route}, "name") or frappe.db.get_value("Web Form", {"title": form_name}, "name")
    if existing_form:
        form = frappe.get_doc("Web Form", existing_form)
        form.set("web_form_fields", [])
    else:
        form = frappe.new_doc("Web Form")
        form.title = form_name

    form.route = route
    form.doc_type = doc_type
    form.module = "Stock"
    form.published = 1
    form.login_required = 1
    form.anonymous = 0
    form.apply_document_permissions = 1
    form.allow_edit = allow_edit
    form.allow_multiple = allow_multiple
    form.allow_delete = 0
    form.allow_print = 1
    form.show_list = 1
    form.list_title = list_title
    form.button_label = button_label
    form.introduction_text = introduction_text
    form.success_title = success_title
    form.success_message = success_message
    form.success_url = f"/{route}"

    for field in fields:
        form.append("web_form_fields", field)

    form.save(ignore_permissions=True)


def configure_portal_menu():
    menu_title = "Receiving Notices"
    portal_settings = frappe.get_single("Portal Settings")
    menu_items = [
        ("Receiving Notices", "client/receiving-notice", "Inbound Shipment Notice"),
        ("Inventory", "client/inventory", "Three PL Inventory Snapshot"),
        ("Shipment Requests", "client/shipment-request", "Three PL Shipment Request"),
        ("Discrepancy Instructions", "client/discrepancy-instruction", "Three PL Client Instruction"),
    ]
    for title, route, reference_doctype in menu_items:
        item = None
        for row in portal_settings.menu:
            if row.title == title or row.route == route:
                item = row
                break
        if item is None:
            item = portal_settings.append("menu", {})

        item.title = title
        item.enabled = 1
        item.route = route
        item.reference_doctype = reference_doctype
        item.role = "3PL Client"
        item.target = ""

    portal_settings.default_role = "3PL Client"
    portal_settings.default_portal_home = "client/receiving-notice"
    portal_settings.save(ignore_permissions=True)


def configure_reports():
    reports = {
        "3PL ASN vs Received": {
            "ref_doctype": "Inbound Shipment Notice",
            "query": """
select
    isn.name as "Notice:Link/Inbound Shipment Notice:150",
    isn.external_reference as "Client Notice Ref:Data:150",
    isn.customer as "Client:Link/Customer:170",
    item.item_code as "Item:Link/Item:150",
    item.client_sku as "Client SKU:Data:120",
    item.expected_qty as "Expected Qty:Float:110",
    item.received_qty as "Received Qty:Float:110",
    item.variance_qty as "Variance Qty:Float:110",
    item.container_code as "Container / Box:Link/Three PL Container:150",
    isn.status as "Status:Data:120"
from `tabInbound Shipment Notice` isn
inner join `tabInbound Shipment Notice Item` item on item.parent = isn.name
order by isn.creation desc, item.idx asc
""".strip(),
        },
        "3PL Receiving Discrepancies": {
            "ref_doctype": "Inbound Shipment Notice",
            "query": """
select
    isn.name as "Notice:Link/Inbound Shipment Notice:150",
    isn.external_reference as "Client Notice Ref:Data:150",
    isn.customer as "Client:Link/Customer:170",
    d.discrepancy_type as "Type:Data:140",
    d.status as "Status:Data:150",
    d.item_code as "Item:Link/Item:150",
    d.client_sku as "Client SKU:Data:120",
    d.expected_qty as "Expected Qty:Float:110",
    d.actual_qty as "Actual Qty:Float:110",
    d.variance_qty as "Variance Qty:Float:110",
    d.container_code as "Container / Box:Link/Three PL Container:150",
    d.notes as "Notes:Small Text:220"
from `tabInbound Shipment Notice` isn
inner join `tabInbound Shipment Discrepancy` d on d.parent = isn.name
order by isn.creation desc, d.idx asc
""".strip(),
        },
        "3PL Containers": {
            "ref_doctype": "Three PL Container",
            "query": """
select
    c.name as "Container / Box:Link/Three PL Container:150",
    c.client as "Client:Link/Customer:170",
    c.status as "Status:Data:140",
    c.current_warehouse as "Current Location:Link/Warehouse:180",
    c.inbound_shipment_notice as "Receiving Notice:Link/Inbound Shipment Notice:170",
    ci.item_code as "Item:Link/Item:150",
    ci.client_sku as "Client SKU:Data:120",
    ci.qty as "Qty:Float:90",
    ci.uom as "UOM:Link/UOM:80",
    ci.condition_status as "Condition:Data:120"
from `tabThree PL Container` c
left join `tabThree PL Container Item` ci on ci.parent = c.name
order by c.creation desc, ci.idx asc
""".strip(),
        },
        "3PL Shipment Requests": {
            "ref_doctype": "Three PL Shipment Request",
            "query": """
select
    sr.name as "Shipment Request:Link/Three PL Shipment Request:170",
    sr.external_reference as "Client Shipment Ref:Data:160",
    sr.customer as "Client:Link/Customer:170",
    sr.status as "Status:Data:120",
    sr.requested_ship_date as "Requested Ship Date:Date:130",
    sr.destination_name as "Destination:Data:180",
    item.item_code as "Item:Link/Item:150",
    item.client_sku as "Client SKU:Data:120",
    item.qty as "Qty:Float:90",
    item.uom as "UOM:Link/UOM:80"
from `tabThree PL Shipment Request` sr
left join `tabThree PL Shipment Request Item` item on item.parent = sr.name
order by sr.creation desc, item.idx asc
""".strip(),
        },
        "3PL Client Inventory": {
            "ref_doctype": "Three PL Inventory Snapshot",
            "query": """
select
    inv.customer as "Client:Link/Customer:170",
    inv.item_code as "Item:Link/Item:150",
    inv.client_sku as "Client SKU:Data:120",
    inv.item_name as "Item Name:Data:180",
    inv.qty as "Qty:Float:90",
    inv.uom as "UOM:Link/UOM:80",
    inv.warehouse as "Location:Link/Warehouse:180",
    inv.container_code as "Container / Box:Link/Three PL Container:150",
    inv.status as "Status:Data:120",
    inv.last_updated as "Last Updated:Datetime:160"
from `tabThree PL Inventory Snapshot` inv
order by inv.customer asc, inv.item_code asc
""".strip(),
        },
    }

    for report_name, report_data in reports.items():
        if frappe.db.exists("Report", report_name):
            report = frappe.get_doc("Report", report_name)
        else:
            report = frappe.new_doc("Report")
            report.report_name = report_name

        report.ref_doctype = report_data["ref_doctype"]
        report.report_type = "Query Report"
        report.is_standard = "No"
        report.module = "Stock"
        report.query = report_data["query"]
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


def configure_email_placeholder():
    account_name = "Placeholder Outgoing Email"

    for name in frappe.get_all("Email Account", filters={"default_outgoing": 1}, pluck="name"):
        if name != account_name:
            frappe.db.set_value("Email Account", name, "default_outgoing", 0)

    if frappe.db.exists("Email Account", account_name):
        account = frappe.get_doc("Email Account", account_name)
    else:
        account = frappe.new_doc("Email Account")
        account.email_account_name = account_name
        account.email_id = PLACEHOLDER_EMAIL

    account.enable_incoming = 0
    account.enable_outgoing = 1
    account.default_outgoing = 1
    account.always_use_account_email_id_as_sender = 1
    account.always_use_account_name_as_sender_name = 1
    account.no_smtp_authentication = 1
    account.smtp_server = "smtp.placeholder.invalid"
    account.smtp_port = "25"
    account.use_tls = 0
    account.use_ssl_for_outgoing = 0
    account.service = ""
    account.save(ignore_permissions=True)


def main():
    configure_company()
    configure_module_profile()
    configure_desk_permissions()
    configure_warehouses()
    configure_stock_entry_types()
    configure_custom_doctypes()
    configure_custom_fields()
    configure_client_portal()
    configure_reports()
    configure_workspaces()
    configure_defaults()
    configure_email_placeholder()
    mark_setup_complete()
    frappe.db.commit()
    frappe.clear_cache()


main()
