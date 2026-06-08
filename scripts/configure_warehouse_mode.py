import json

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from project_config import CLIENT_PORTAL_FORMS, CLIENT_PORTAL_HOME, COMPANY, COMPANY_ABBR, COUNTRY, CURRENCY, LANGUAGE, PLACEHOLDER_EMAIL, TIME_ZONE


def ensure_child_field(doc, field):
    sync_keys = {
        "label",
        "fieldtype",
        "options",
        "reqd",
        "read_only",
        "default",
        "insert_after",
        "in_list_view",
        "in_standard_filter",
        "unique",
        "collapsible",
        "depends_on",
        "description",
    }
    existing = next((row for row in doc.fields if row.fieldname == field["fieldname"]), None)
    if existing:
        changed = False
        for key in sync_keys & field.keys():
            if getattr(existing, key, None) != field[key]:
                setattr(existing, key, field[key])
                changed = True
        return changed

    doc.append("fields", field)
    return True


def ensure_doctype_fields(doctype, fields):
    doc = frappe.get_doc("DocType", doctype)
    changed = False
    for field in fields:
        changed = ensure_child_field(doc, field) or changed
    if changed:
        doc.save(ignore_permissions=True)


def ensure_doctype_permission(doc, permission):
    sync_keys = {
        "read",
        "write",
        "create",
        "delete",
        "submit",
        "cancel",
        "amend",
        "report",
        "export",
        "import",
        "share",
        "print",
        "email",
    }
    permlevel = permission.get("permlevel", 0)
    existing = next((row for row in doc.permissions if row.role == permission["role"] and row.permlevel == permlevel), None)
    if existing:
        changed = False
        for key in sync_keys & permission.keys():
            if getattr(existing, key, 0) != permission[key]:
                setattr(existing, key, permission[key])
                changed = True
        return changed

    doc.append("permissions", {"permlevel": permlevel, **permission})
    return True


def ensure_custom_doctype(spec):
    name = spec["name"]
    if frappe.db.exists("DocType", name):
        doc = frappe.get_doc("DocType", name)
        changed = False
        for key, value in spec.items():
            if key in {"doctype", "fields", "permissions"}:
                continue
            if getattr(doc, key, None) != value:
                setattr(doc, key, value)
                changed = True
        for field in spec.get("fields", []):
            changed = ensure_child_field(doc, field) or changed
        for permission in spec.get("permissions", []):
            changed = ensure_doctype_permission(doc, permission) or changed
        if changed:
            doc.save(ignore_permissions=True)
        return doc

    doc = frappe.get_doc({"doctype": "DocType", **spec})
    doc.name = name
    doc.insert(ignore_permissions=True)
    return doc


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

    guard_block_name = "3PL Warehouse Desk Guard"
    guard_script = """
(function () {
  function isWarehouseRole() {
    var roles = (window.frappe && frappe.user_roles) || [];
    return roles.indexOf("3PL Warehouse User") !== -1 || roles.indexOf("3PL Warehouse Manager") !== -1;
  }

  function isWarehouseWorkspace() {
    return window.location.pathname.indexOf("/desk/3pl-warehouse") === 0
      || window.location.pathname.indexOf("/app/3pl-warehouse") === 0
      || (window.frappe && frappe.get_route && frappe.get_route().join("/").indexOf("3pl-warehouse") !== -1);
  }

  function patchDeskHomeLink() {
    if (!isWarehouseRole() || !isWarehouseWorkspace()) return;

    var block = root_element && root_element.closest ? root_element.closest(".ce-block") : null;
    if (block) block.style.display = "none";

    document.querySelectorAll('a[href="/desk"]').forEach(function (link) {
      link.setAttribute("href", "/desk/3pl-warehouse");
      link.addEventListener("click", function (event) {
        event.preventDefault();
        event.stopPropagation();
        if (window.frappe && frappe.set_route) {
          frappe.set_route("3pl-warehouse");
        } else {
          window.location.href = "/desk/3pl-warehouse";
        }
      }, true);
    });
  }

  patchDeskHomeLink();
  setTimeout(patchDeskHomeLink, 250);
  setTimeout(patchDeskHomeLink, 1000);
}());
"""

    if frappe.db.exists("Custom HTML Block", guard_block_name):
        guard_block = frappe.get_doc("Custom HTML Block", guard_block_name)
    else:
        guard_block = frappe.new_doc("Custom HTML Block")
        guard_block.name = guard_block_name

    guard_block.html = '<div class="three-pl-desk-guard"></div>'
    guard_block.script = guard_script
    guard_block.style = ".three-pl-desk-guard { display: none !important; }"
    guard_block.private = 0
    guard_block.set("roles", [])
    for role_name in ("3PL Warehouse User", "3PL Warehouse Manager"):
        guard_block.append("roles", {"role": role_name})
    guard_block.save(ignore_permissions=True)

    workspaces = [
        {
            "name": "3PL Warehouse",
            "label": "3PL Warehouse",
            "title": "3PL Warehouse",
            "module": "Stock",
            "indicator_color": "green",
            "hide_custom": 1,
            "content": [
                {"id": "3pl_desk_guard", "type": "custom_block", "data": {"custom_block_name": guard_block_name, "col": 12}},
                {"id": "3pl_header", "type": "header", "data": {"text": '<span class="h4"><b>3PL Warehouse</b></span>', "col": 12}},
                {"id": "3pl_inbound_card", "type": "card", "data": {"card_name": "Inbound Work", "col": 4}},
                {"id": "3pl_outbound_card", "type": "card", "data": {"card_name": "Outbound Work", "col": 4}},
                {"id": "3pl_reports_card", "type": "card", "data": {"card_name": "Reports", "col": 4}},
            ],
            "custom_blocks": [
                {"custom_block_name": guard_block_name, "label": "3PL Warehouse Desk Guard"},
            ],
            "shortcuts": [
                {"type": "DocType", "link_to": "Inbound Shipment Notice", "doc_view": "List", "label": "Receiving Notices"},
                {"type": "DocType", "link_to": "Three PL Container", "doc_view": "List", "label": "Containers"},
                {"type": "DocType", "link_to": "Three PL Container Move", "doc_view": "List", "label": "Container Moves"},
                {"type": "DocType", "link_to": "Three PL Container Repack", "doc_view": "List", "label": "Container Repacks"},
                {"type": "DocType", "link_to": "Stock Entry", "doc_view": "List", "label": "Stock Entries"},
                {"type": "DocType", "link_to": "Pick List", "doc_view": "List", "label": "Pick Lists"},
                {"type": "DocType", "link_to": "Three PL Shipment Request", "doc_view": "List", "label": "Shipment Requests"},
                {"type": "Report", "link_to": "3PL ASN vs Received", "label": "ASN vs Received", "report_ref_doctype": "Inbound Shipment Notice"},
                {"type": "Report", "link_to": "3PL Receiving Discrepancies", "label": "Receiving Discrepancies", "report_ref_doctype": "Inbound Shipment Notice"},
                {"type": "Report", "link_to": "3PL Containers", "label": "Containers Report", "report_ref_doctype": "Three PL Container"},
                {"type": "Report", "link_to": "3PL Container Moves", "label": "Container Moves Report", "report_ref_doctype": "Three PL Container Move"},
                {"type": "Report", "link_to": "3PL Container Repacks", "label": "Container Repacks Report", "report_ref_doctype": "Three PL Container Repack"},
                {"type": "Report", "link_to": "3PL Container Movements", "label": "Container Movements", "report_ref_doctype": "Three PL Container Movement"},
                {"type": "Report", "link_to": "3PL Client Inventory", "label": "Client Inventory", "report_ref_doctype": "Three PL Inventory Snapshot"},
                {"type": "Report", "link_to": "3PL Client Inventory Summary", "label": "Inventory Summary", "report_ref_doctype": "Three PL Inventory Snapshot"},
                {"type": "DocType", "link_to": "Three PL Client Instruction", "doc_view": "List", "label": "Client Instructions"},
                {"type": "DocType", "link_to": "Item", "doc_view": "List", "label": "Items"},
                {"type": "DocType", "link_to": "Warehouse", "doc_view": "Tree", "label": "Warehouses"},
                {"type": "Report", "link_to": "Stock Balance", "label": "Stock Balance", "report_ref_doctype": "Stock Ledger Entry"},
                {"type": "Report", "link_to": "Stock Ledger", "label": "Stock Ledger", "report_ref_doctype": "Stock Ledger Entry"},
            ],
            "links": [
                {"type": "Card Break", "label": "Inbound Work"},
                {"type": "Link", "label": "Receiving Notices", "link_type": "DocType", "link_to": "Inbound Shipment Notice"},
                {"type": "Link", "label": "Container Moves", "link_type": "DocType", "link_to": "Three PL Container Move"},
                {"type": "Link", "label": "Container Repacks", "link_type": "DocType", "link_to": "Three PL Container Repack"},
                {"type": "Link", "label": "Stock Entries", "link_type": "DocType", "link_to": "Stock Entry"},
                {"type": "Link", "label": "ASN vs Received", "link_type": "Report", "link_to": "3PL ASN vs Received", "is_query_report": 1},
                {"type": "Link", "label": "Receiving Discrepancies", "link_type": "Report", "link_to": "3PL Receiving Discrepancies", "is_query_report": 1},
                {"type": "Card Break", "label": "Outbound Work"},
                {"type": "Link", "label": "Shipment Requests", "link_type": "DocType", "link_to": "Three PL Shipment Request"},
                {"type": "Link", "label": "Pick Lists", "link_type": "DocType", "link_to": "Pick List"},
                {"type": "Card Break", "label": "Reports"},
                {"type": "Link", "label": "ASN vs Received", "link_type": "Report", "link_to": "3PL ASN vs Received", "is_query_report": 1},
                {"type": "Link", "label": "Receiving Discrepancies", "link_type": "Report", "link_to": "3PL Receiving Discrepancies", "is_query_report": 1},
                {"type": "Link", "label": "Containers Report", "link_type": "Report", "link_to": "3PL Containers", "is_query_report": 1},
                {"type": "Link", "label": "Container Moves Report", "link_type": "Report", "link_to": "3PL Container Moves", "is_query_report": 1},
                {"type": "Link", "label": "Container Repacks Report", "link_type": "Report", "link_to": "3PL Container Repacks", "is_query_report": 1},
                {"type": "Link", "label": "Container Movements", "link_type": "Report", "link_to": "3PL Container Movements", "is_query_report": 1},
                {"type": "Link", "label": "Inventory Summary", "link_type": "Report", "link_to": "3PL Client Inventory Summary", "is_query_report": 1},
                {"type": "Link", "label": "Stock Balance", "link_type": "Report", "link_to": "Stock Balance", "is_query_report": 1},
                {"type": "Link", "label": "Stock Ledger", "link_type": "Report", "link_to": "Stock Ledger", "is_query_report": 1},
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
            doc.set("custom_blocks", [])
        else:
            doc = frappe.new_doc("Workspace")
            doc.name = workspace_data["name"]

        for field in ("label", "title", "module", "indicator_color"):
            setattr(doc, field, workspace_data[field])
        doc.hide_custom = workspace_data.get("hide_custom", 0)
        doc.public = 1
        doc.is_hidden = 0
        doc.content = json.dumps(workspace_data["content"])

        for shortcut in workspace_data["shortcuts"]:
            doc.append("shortcuts", shortcut)
        for link in workspace_data["links"]:
            doc.append("links", link)
        for custom_block in workspace_data.get("custom_blocks", []):
            doc.append("custom_blocks", custom_block)

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

    for role_name in ("3PL Client", "Customer"):
        if not frappe.db.exists("Role", role_name):
            continue

        role = frappe.get_doc("Role", role_name)
        changed = False
        if role.meta.has_field("desk_access") and role.desk_access:
            role.desk_access = 0
            changed = True
        if role.home_page != CLIENT_PORTAL_HOME:
            role.home_page = CLIENT_PORTAL_HOME
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
    child_doctype_specs = [
        {
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
        },
        {
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
        },
        {
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
        },
        {
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
        },
        {
            "name": "Three PL Repack Source",
            "module": "Stock",
            "custom": 1,
            "istable": 1,
            "editable_grid": 1,
            "fields": [
                {"fieldname": "source_container", "label": "Source Container", "fieldtype": "Link", "options": "Three PL Container", "reqd": 1, "in_list_view": 1},
                {"fieldname": "source_location", "label": "Source Location", "fieldtype": "Link", "options": "Warehouse", "in_list_view": 1},
                {"fieldname": "notes", "label": "Notes", "fieldtype": "Small Text"},
            ],
        },
        {
            "name": "Three PL Repack Item",
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
        },
    ]
    for spec in child_doctype_specs:
        ensure_custom_doctype(spec)

    warehouse_permissions = [
        {"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1},
        {"role": "Stock Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1},
        {"role": "3PL Warehouse Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1},
        {"role": "3PL Warehouse User", "read": 1, "write": 1, "create": 1, "report": 1},
    ]
    manager_permissions = warehouse_permissions[:3]

    parent_doctype_specs = [
        {
            "name": "Three PL Container",
            "module": "Stock",
            "custom": 1,
            "track_changes": 1,
            "title_field": "container_code",
            "autoname": "field:container_code",
            "fields": [
                {"fieldname": "container_code", "label": "Container / Box Code", "fieldtype": "Data", "reqd": 1, "unique": 1, "in_list_view": 1},
                {"fieldname": "barcode", "label": "Barcode / Label", "fieldtype": "Data", "in_list_view": 1},
                {"fieldname": "container_type", "label": "Container Type", "fieldtype": "Select", "options": "Box\nCarton\nPallet\nTote\nOther", "default": "Box", "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "client", "label": "Client", "fieldtype": "Link", "options": "Customer", "reqd": 1, "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "current_warehouse", "label": "Current Location", "fieldtype": "Link", "options": "Warehouse", "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "status", "label": "Status", "fieldtype": "Select", "options": "Expected\nReceived\nIn Verification\nReady for Putaway\nStored\nPicking\nPicked\nPacked\nShipped\nEmpty\nClosed\nReplaced", "default": "Expected", "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "last_moved_at", "label": "Last Moved At", "fieldtype": "Datetime", "read_only": 1, "in_list_view": 1},
                {"fieldname": "container_links_section", "label": "Container Relations", "fieldtype": "Section Break"},
                {"fieldname": "parent_container", "label": "Parent Container", "fieldtype": "Link", "options": "Three PL Container", "description": "Used when a box is placed inside a larger handling unit such as a pallet."},
                {"fieldname": "replaced_by", "label": "Replaced By", "fieldtype": "Link", "options": "Three PL Container", "description": "Used when this container was emptied, consolidated, or replaced by another container."},
                {"fieldname": "items_section", "label": "Contents", "fieldtype": "Section Break"},
                {"fieldname": "items", "label": "Items", "fieldtype": "Table", "options": "Three PL Container Item"},
                {"fieldname": "notes", "label": "Notes", "fieldtype": "Small Text"},
            ],
            "permissions": warehouse_permissions
            + [
                {"role": "Stock User", "read": 1, "write": 1, "create": 1, "report": 1},
            ],
        },
        {
            "name": "Inbound Shipment Notice",
            "module": "Stock",
            "custom": 1,
            "is_submittable": 1,
            "track_changes": 1,
            "title_field": "external_reference",
            "fields": [
                {"fieldname": "customer", "label": "Client", "fieldtype": "Link", "options": "Customer", "reqd": 1, "in_standard_filter": 1},
                {"fieldname": "external_reference", "label": "Client Notice Ref", "fieldtype": "Data", "reqd": 1, "in_list_view": 1},
                {"fieldname": "portal_source", "label": "Portal Source", "fieldtype": "Check", "insert_after": "external_reference"},
                {"fieldname": "notice_date", "label": "Notice Date", "fieldtype": "Date", "default": "Today", "in_list_view": 1},
                {"fieldname": "expected_arrival_date", "label": "Expected Arrival Date", "fieldtype": "Date", "in_list_view": 1},
                {"fieldname": "temporary_warehouse", "label": "Temporary Warehouse", "fieldtype": "Link", "options": "Warehouse", "default": f"Temporary Receiving - {COMPANY_ABBR}"},
                {"fieldname": "status", "label": "Status", "fieldtype": "Select", "options": "Draft\nPartially Received\nReceived\nClosed", "default": "Draft", "in_list_view": 1},
                {"fieldname": "client_instruction_status", "label": "Client Instruction Status", "fieldtype": "Select", "options": "\nNot Required\nWaiting for Client\nInstruction Received", "default": "Not Required", "insert_after": "status", "in_standard_filter": 1},
                {"fieldname": "portal_items_description", "label": "Portal Products and Quantities", "fieldtype": "Small Text", "insert_after": "client_instruction_status"},
                {"fieldname": "items_section", "label": "Expected Products", "fieldtype": "Section Break"},
                {"fieldname": "items", "label": "Items", "fieldtype": "Table", "options": "Inbound Shipment Notice Item"},
                {"fieldname": "discrepancy_section", "label": "Discrepancies", "fieldtype": "Section Break", "insert_after": "items"},
                {"fieldname": "discrepancies", "label": "Discrepancies", "fieldtype": "Table", "options": "Inbound Shipment Discrepancy", "insert_after": "discrepancy_section"},
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
        },
        {
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
            "permissions": manager_permissions
            + [
                {"role": "3PL Warehouse User", "read": 1, "report": 1},
                {"role": "3PL Client", "read": 1},
            ],
        },
        {
            "name": "Three PL Container Movement",
            "module": "Stock",
            "custom": 1,
            "track_changes": 1,
            "title_field": "container_code",
            "autoname": "naming_series:",
            "fields": [
                {"fieldname": "naming_series", "label": "Series", "fieldtype": "Select", "options": "HU-MOV-.YYYY.-.#####", "default": "HU-MOV-.YYYY.-.#####", "reqd": 1},
                {"fieldname": "movement_datetime", "label": "Movement Time", "fieldtype": "Datetime", "default": "Now", "reqd": 1, "in_list_view": 1},
                {"fieldname": "container_code", "label": "Container / Handling Unit", "fieldtype": "Link", "options": "Three PL Container", "reqd": 1, "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "client", "label": "Client", "fieldtype": "Link", "options": "Customer", "reqd": 1, "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "movement_type", "label": "Movement Type", "fieldtype": "Select", "options": "Expected\nReceived\nMoved\nPutaway\nPicked\nPacked\nShipped\nRepacked\nAdjusted", "reqd": 1, "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "location_section", "label": "Location", "fieldtype": "Section Break"},
                {"fieldname": "from_warehouse", "label": "From Location", "fieldtype": "Link", "options": "Warehouse", "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "to_warehouse", "label": "To Location", "fieldtype": "Link", "options": "Warehouse", "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "container_section", "label": "Container Relation", "fieldtype": "Section Break"},
                {"fieldname": "from_container", "label": "From Container", "fieldtype": "Link", "options": "Three PL Container"},
                {"fieldname": "to_container", "label": "To Container", "fieldtype": "Link", "options": "Three PL Container"},
                {"fieldname": "reference_section", "label": "Reference", "fieldtype": "Section Break"},
                {"fieldname": "reference_doctype", "label": "Reference DocType", "fieldtype": "Link", "options": "DocType"},
                {"fieldname": "reference_name", "label": "Reference Name", "fieldtype": "Dynamic Link", "options": "reference_doctype"},
                {"fieldname": "notes", "label": "Notes", "fieldtype": "Small Text"},
            ],
            "permissions": warehouse_permissions
            + [
                {"role": "Stock User", "read": 1, "write": 1, "create": 1, "report": 1},
            ],
        },
        {
            "name": "Three PL Container Move",
            "module": "Stock",
            "custom": 1,
            "track_changes": 1,
            "title_field": "operation_reference",
            "autoname": "naming_series:",
            "fields": [
                {"fieldname": "naming_series", "label": "Series", "fieldtype": "Select", "options": "HU-MOVE-.YYYY.-.#####", "default": "HU-MOVE-.YYYY.-.#####", "reqd": 1},
                {"fieldname": "operation_reference", "label": "Operation Reference", "fieldtype": "Data", "reqd": 1, "unique": 1, "in_list_view": 1},
                {"fieldname": "operation_datetime", "label": "Operation Time", "fieldtype": "Datetime", "default": "Now", "reqd": 1, "in_list_view": 1},
                {"fieldname": "status", "label": "Status", "fieldtype": "Select", "options": "Draft\nApplied\nCancelled", "default": "Draft", "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "container_code", "label": "Container / Handling Unit", "fieldtype": "Link", "options": "Three PL Container", "reqd": 1, "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "client", "label": "Client", "fieldtype": "Link", "options": "Customer", "reqd": 1, "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "from_warehouse", "label": "From Location", "fieldtype": "Link", "options": "Warehouse", "reqd": 1, "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "to_warehouse", "label": "To Location", "fieldtype": "Link", "options": "Warehouse", "reqd": 1, "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "reference_section", "label": "References", "fieldtype": "Section Break"},
                {"fieldname": "stock_entry", "label": "Stock Entry", "fieldtype": "Link", "options": "Stock Entry"},
                {"fieldname": "movement", "label": "Movement Record", "fieldtype": "Link", "options": "Three PL Container Movement", "read_only": 1},
                {"fieldname": "notes", "label": "Notes", "fieldtype": "Small Text"},
            ],
            "permissions": warehouse_permissions
            + [
                {"role": "Stock User", "read": 1, "write": 1, "create": 1, "report": 1},
            ],
        },
        {
            "name": "Three PL Container Repack",
            "module": "Stock",
            "custom": 1,
            "track_changes": 1,
            "title_field": "operation_reference",
            "autoname": "naming_series:",
            "fields": [
                {"fieldname": "naming_series", "label": "Series", "fieldtype": "Select", "options": "HU-REPACK-.YYYY.-.#####", "default": "HU-REPACK-.YYYY.-.#####", "reqd": 1},
                {"fieldname": "operation_reference", "label": "Operation Reference", "fieldtype": "Data", "reqd": 1, "unique": 1, "in_list_view": 1},
                {"fieldname": "operation_datetime", "label": "Operation Time", "fieldtype": "Datetime", "default": "Now", "reqd": 1, "in_list_view": 1},
                {"fieldname": "status", "label": "Status", "fieldtype": "Select", "options": "Draft\nNeeds Review\nApplied\nCancelled", "default": "Draft", "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "client", "label": "Client", "fieldtype": "Link", "options": "Customer", "reqd": 1, "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "target_container", "label": "Target Container", "fieldtype": "Link", "options": "Three PL Container", "reqd": 1, "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "target_location", "label": "Target Location", "fieldtype": "Link", "options": "Warehouse", "reqd": 1, "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "movement", "label": "Movement Record", "fieldtype": "Link", "options": "Three PL Container Movement", "read_only": 1},
                {"fieldname": "sources_section", "label": "Source Containers", "fieldtype": "Section Break"},
                {"fieldname": "source_containers", "label": "Source Containers", "fieldtype": "Table", "options": "Three PL Repack Source"},
                {"fieldname": "items_section", "label": "Resulting Contents", "fieldtype": "Section Break"},
                {"fieldname": "items", "label": "Items", "fieldtype": "Table", "options": "Three PL Repack Item"},
                {"fieldname": "notes", "label": "Notes", "fieldtype": "Small Text"},
            ],
            "permissions": warehouse_permissions
            + [
                {"role": "Stock User", "read": 1, "write": 1, "create": 1, "report": 1},
            ],
        },
        {
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
                {"fieldname": "portal_items_description", "label": "Portal Products and Quantities", "fieldtype": "Small Text", "insert_after": "portal_source"},
                {"fieldname": "items_section", "label": "Requested Products", "fieldtype": "Section Break"},
                {"fieldname": "items", "label": "Items", "fieldtype": "Table", "options": "Three PL Shipment Request Item"},
                {"fieldname": "notes", "label": "Notes", "fieldtype": "Small Text"},
            ],
            "permissions": warehouse_permissions
            + [
                {"role": "3PL Client", "read": 1, "write": 1, "create": 1},
            ],
        },
        {
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
            "permissions": warehouse_permissions
            + [
                {"role": "3PL Client", "read": 1, "write": 1, "create": 1},
            ],
        },
    ]
    for spec in parent_doctype_specs:
        ensure_custom_doctype(spec)

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
        "Inbound Shipment Notice Item": {"read": 1, "write": 1, "create": 1},
        "Inbound Shipment Discrepancy": {"read": 1},
        "Customer": {"read": 1},
        "Item": {"read": 1},
        "UOM": {"read": 1},
        "Warehouse": {"read": 1},
        "Web Form": {"read": 1},
        "Three PL Container": {"read": 1},
        "Three PL Container Item": {"read": 1},
        "Three PL Container Move": {"read": 1},
        "Three PL Container Movement": {"read": 1},
        "Three PL Container Repack": {"read": 1},
        "Three PL Repack Source": {"read": 1},
        "Three PL Repack Item": {"read": 1},
        "Three PL Inventory Snapshot": {"read": 1},
        "Three PL Shipment Request": {"read": 1, "write": 1, "create": 1},
        "Three PL Shipment Request Item": {"read": 1, "write": 1, "create": 1},
        "Three PL Client Instruction": {"read": 1, "write": 1, "create": 1},
    }
    for doctype, permissions in client_permissions.items():
        ensure_docperm(doctype, "3PL Client", **permissions)

    # Frappe treats Custom DocPerm rows as an override for a DocType. Whenever
    # client portal read/create access creates a Custom DocPerm row, preserve the
    # warehouse and system roles in Custom DocPerm too; otherwise Desk/API access
    # for those roles can disappear even though the standard DocPerm still exists.
    custom_override_permissions = {
        "Inbound Shipment Notice": [
            {"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "cancel": 1, "amend": 1, "report": 1, "export": 1},
            {"role": "Stock Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "cancel": 1, "amend": 1, "report": 1, "export": 1},
            {"role": "Stock User", "read": 1, "write": 1, "create": 1, "submit": 1, "report": 1, "export": 1},
            {"role": "3PL Warehouse Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "cancel": 1, "amend": 1, "report": 1, "export": 1},
            {"role": "3PL Warehouse User", "read": 1, "write": 1, "create": 1, "submit": 1, "report": 1},
        ],
        "Inbound Shipment Notice Item": warehouse_permissions
        + [
            {"role": "Stock User", "read": 1, "write": 1, "create": 1, "report": 1},
        ],
        "Inbound Shipment Discrepancy": warehouse_permissions
        + [
            {"role": "Stock User", "read": 1, "write": 1, "create": 1, "report": 1},
        ],
        "Three PL Container": warehouse_permissions
        + [
            {"role": "Stock User", "read": 1, "write": 1, "create": 1, "report": 1},
        ],
        "Three PL Container Item": warehouse_permissions
        + [
            {"role": "Stock User", "read": 1, "write": 1, "create": 1, "report": 1},
        ],
        "Three PL Container Move": warehouse_permissions
        + [
            {"role": "Stock User", "read": 1, "write": 1, "create": 1, "report": 1},
        ],
        "Three PL Container Movement": warehouse_permissions
        + [
            {"role": "Stock User", "read": 1, "write": 1, "create": 1, "report": 1},
        ],
        "Three PL Container Repack": warehouse_permissions
        + [
            {"role": "Stock User", "read": 1, "write": 1, "create": 1, "report": 1},
        ],
        "Three PL Repack Source": warehouse_permissions
        + [
            {"role": "Stock User", "read": 1, "write": 1, "create": 1, "report": 1},
        ],
        "Three PL Repack Item": warehouse_permissions
        + [
            {"role": "Stock User", "read": 1, "write": 1, "create": 1, "report": 1},
        ],
        "Three PL Inventory Snapshot": [
            {"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1},
            {"role": "Stock Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1},
            {"role": "Stock User", "read": 1, "report": 1, "export": 1},
            {"role": "3PL Warehouse Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1},
            {"role": "3PL Warehouse User", "read": 1, "report": 1},
        ],
        "Three PL Shipment Request": warehouse_permissions,
        "Three PL Shipment Request Item": warehouse_permissions,
        "Three PL Client Instruction": warehouse_permissions,
        "Customer": [
            {"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1},
            {"role": "Stock Manager", "read": 1, "report": 1, "export": 1},
            {"role": "Stock User", "read": 1, "report": 1},
            {"role": "3PL Warehouse Manager", "read": 1, "report": 1, "export": 1},
            {"role": "3PL Warehouse User", "read": 1, "report": 1},
        ],
        "Item": [
            {"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1},
            {"role": "Stock Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1},
            {"role": "Stock User", "read": 1, "report": 1},
            {"role": "3PL Warehouse Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1},
            {"role": "3PL Warehouse User", "read": 1, "report": 1},
        ],
        "UOM": [
            {"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1},
            {"role": "Stock Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1},
            {"role": "Stock User", "read": 1, "report": 1},
            {"role": "3PL Warehouse Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1},
            {"role": "3PL Warehouse User", "read": 1, "report": 1},
        ],
        "Warehouse": [
            {"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1},
            {"role": "Stock Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1},
            {"role": "Stock User", "read": 1, "report": 1},
            {"role": "3PL Warehouse Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1},
            {"role": "3PL Warehouse User", "read": 1, "report": 1},
        ],
        "Web Form": [
            {"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "export": 1},
            {"role": "3PL Warehouse Manager", "read": 1, "report": 1},
            {"role": "3PL Warehouse User", "read": 1, "report": 1},
        ],
    }
    for doctype, role_permissions in custom_override_permissions.items():
        for permission in role_permissions:
            permission = permission.copy()
            role = permission.pop("role")
            ensure_docperm(doctype, role, **permission)


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


def ensure_doctype_property(doctype, property_name, value, property_type):
    filters = {"doc_type": doctype, "property": property_name, "field_name": None}
    if frappe.db.exists("Property Setter", filters):
        setter = frappe.get_doc("Property Setter", filters)
    else:
        setter = frappe.new_doc("Property Setter")
        setter.doc_type = doctype
        setter.doctype_or_field = "DocType"
        setter.property = property_name
        setter.property_type = property_type

    if setter.value != str(value) or setter.property_type != property_type:
        setter.value = str(value)
        setter.property_type = property_type
        setter.save(ignore_permissions=True)


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
    portal_nav = build_client_portal_nav()
    for form in CLIENT_PORTAL_FORMS:
        configure_portal_web_form(
            form_name=form["form_name"],
            route=form["route"],
            doc_type=form["doc_type"],
            list_title=form["list_title"],
            button_label=form["button_label"],
            introduction_text=f"{portal_nav}{form['introduction_text']}",
            success_title=form["success_title"],
            success_message=form["success_message"],
            fields=form["fields"],
            allow_edit=form.get("allow_edit", 1),
            allow_multiple=form.get("allow_multiple", 1),
        )

    configure_portal_menu()
    configure_client_portal_website_script()


def build_client_portal_nav():
    links = []
    for form in CLIENT_PORTAL_FORMS:
        label = frappe.utils.escape_html(form["menu_title"])
        links.append(f'<a class="btn btn-sm btn-default" href="/{portal_list_route(form["route"])}">{label}</a>')
    return f'<div class="mb-4 d-flex flex-wrap gap-2">{" ".join(links)}</div>'


def portal_list_route(route):
    return route if route.endswith("/list") else f"{route}/list"


def configure_client_portal_website_script():
    nav_html = build_client_portal_nav().replace("'", "\\'")
    script = f"""
(function () {{
  function isClientPortal() {{
    return window.location.pathname.indexOf('/client/') === 0;
  }}

  function tuneClientPortalBoot() {{
    if (!isClientPortal()) return;

    if (window.frappe && frappe.boot && frappe.boot.apps_data) {{
      frappe.boot.apps_data.is_desk_apps = 0;
      frappe.boot.apps_data.default_path = '/{CLIENT_PORTAL_HOME}';
    }}

    if (window.frappe && frappe.has_permission && !frappe.has_permission.__client_portal_patched) {{
      frappe.has_permission = function (doctype, docname, perm_type, callback) {{
        if (callback) callback({{message: {{has_permission: false}}}});
      }};
      frappe.has_permission.__client_portal_patched = true;
    }}
  }}

  function installClientPortalNav() {{
    if (!isClientPortal()) return;

    var brand = document.querySelector('.navbar-brand');
    if (brand) {{
      brand.setAttribute('href', '/{CLIENT_PORTAL_HOME}');
      var label = brand.querySelector('span');
      if (label) label.textContent = 'Client Portal';
    }}

    var deskLink = document.querySelector('.switch-to-desk');
    if (deskLink) deskLink.remove();

    if (!document.querySelector('[data-client-portal-nav]')) {{
      var nav = document.createElement('div');
      nav.setAttribute('data-client-portal-nav', '1');
      nav.innerHTML = '{nav_html}';
      var target = document.querySelector('.web-list-actions') || document.querySelector('.web-form-container') || document.querySelector('.page_content');
      if (target && target.parentNode) {{
        target.parentNode.insertBefore(nav, target);
      }}
    }}
  }}

  function removeDeskPermissionNoise() {{
    if (!isClientPortal()) return;
    document.querySelectorAll('.modal').forEach(function (modal) {{
      if (/Not permitted|No permission/i.test(modal.textContent || '')) {{
        modal.remove();
      }}
    }});
    document.querySelectorAll('.modal-backdrop').forEach(function (backdrop) {{
      backdrop.remove();
    }});
    document.body.classList.remove('modal-open');
    document.body.style.removeProperty('overflow');
    document.body.style.removeProperty('padding-right');
  }}

  function escapeHtml(value) {{
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }}

  function renderClientPortalList() {{
    if (!isClientPortal() || window.location.pathname.indexOf('/list') === -1) return;
    if (!window.frappe || !frappe.web_form_doc || !frappe.web_form_doc.is_list) return;

    var target = document.querySelector('.web-list-table');
    if (!target || target.getAttribute('data-client-list-rendered') === '1') return;

    var columns = (frappe.web_form_doc.list_columns || []).slice(0, 6);
    if (!columns.length) return;

    var payload = new URLSearchParams();
    payload.set('doctype', frappe.web_form_doc.doc_type);
    payload.set('limit_start', '0');
    payload.set('limit', '20');
    payload.set('web_form_name', frappe.web_form_doc.name);

    fetch('/api/method/frappe.www.list.get_list_data', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
      body: payload.toString()
    }})
      .then(function (response) {{ return response.json(); }})
      .then(function (response) {{
        var rows = response && response.message ? response.message : [];
        target.setAttribute('data-client-list-rendered', '1');

        if (!rows.length) {{
          target.innerHTML = '<div class="text-muted small py-3">No records yet.</div>';
          return;
        }}

        var head = columns.map(function (column) {{
          return '<th>' + escapeHtml(column.label || column.fieldname) + '</th>';
        }}).join('');
        var body = rows.map(function (row) {{
          var cells = columns.map(function (column) {{
            return '<td>' + escapeHtml(row[column.fieldname]) + '</td>';
          }}).join('');
          return '<tr>' + cells + '</tr>';
        }}).join('');

        target.innerHTML = '<table class="table table-sm table-bordered mb-0"><thead><tr>' + head + '</tr></thead><tbody>' + body + '</tbody></table>';
      }});
  }}

  if (window.frappe && frappe.ready) {{
    tuneClientPortalBoot();
    frappe.ready(function () {{
      tuneClientPortalBoot();
      installClientPortalNav();
      renderClientPortalList();
      removeDeskPermissionNoise();
      setTimeout(renderClientPortalList, 250);
      setTimeout(removeDeskPermissionNoise, 250);
      setTimeout(renderClientPortalList, 1000);
      setTimeout(removeDeskPermissionNoise, 1000);
    }});
  }} else {{
    document.addEventListener('DOMContentLoaded', function () {{
      tuneClientPortalBoot();
      installClientPortalNav();
      renderClientPortalList();
      removeDeskPermissionNoise();
    }});
  }}
}})();
""".strip()

    settings = frappe.get_single("Website Script")
    if settings.javascript != script:
        settings.javascript = script
        settings.save(ignore_permissions=True)


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
    form.apply_document_permissions = 0
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
    form.success_url = f"/{portal_list_route(route)}"
    form.hide_navbar = 1
    form.hide_footer = 1

    for field in fields:
        form.append("web_form_fields", field)

    form.save(ignore_permissions=True)


def configure_portal_menu():
    portal_settings = frappe.get_single("Portal Settings")
    for form in CLIENT_PORTAL_FORMS:
        item = None
        for row in portal_settings.menu:
            if row.title == form["menu_title"] or row.route in {form["route"], portal_list_route(form["route"])}:
                item = row
                break
        if item is None:
            item = portal_settings.append("menu", {})

        item.title = form["menu_title"]
        item.enabled = 1
        item.route = portal_list_route(form["route"])
        item.reference_doctype = form["doc_type"]
        item.role = "3PL Client"
        item.target = ""

    portal_settings.default_role = "3PL Client"
    portal_settings.default_portal_home = CLIENT_PORTAL_HOME
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
    c.container_type as "Type:Data:100",
    c.status as "Status:Data:140",
    c.current_warehouse as "Current Location:Link/Warehouse:180",
    c.parent_container as "Parent Container:Link/Three PL Container:150",
    c.replaced_by as "Replaced By:Link/Three PL Container:150",
    c.last_moved_at as "Last Moved At:Datetime:150",
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
        "3PL Container Movements": {
            "ref_doctype": "Three PL Container Movement",
            "query": """
select
    m.name as "Movement:Link/Three PL Container Movement:160",
    m.movement_datetime as "Movement Time:Datetime:160",
    m.container_code as "Container / HU:Link/Three PL Container:150",
    m.client as "Client:Link/Customer:170",
    m.movement_type as "Type:Data:110",
    m.from_warehouse as "From Location:Link/Warehouse:180",
    m.to_warehouse as "To Location:Link/Warehouse:180",
    m.from_container as "From Container:Link/Three PL Container:150",
    m.to_container as "To Container:Link/Three PL Container:150",
    m.reference_doctype as "Reference Type:Data:140",
    m.reference_name as "Reference:Dynamic Link/reference_doctype:170",
    m.notes as "Notes:Small Text:240"
from `tabThree PL Container Movement` m
order by m.movement_datetime desc, m.creation desc
""".strip(),
        },
        "3PL Container Moves": {
            "ref_doctype": "Three PL Container Move",
            "query": """
select
    cm.name as "Move:Link/Three PL Container Move:160",
    cm.operation_reference as "Operation Ref:Data:150",
    cm.operation_datetime as "Operation Time:Datetime:160",
    cm.status as "Status:Data:100",
    cm.container_code as "Container / HU:Link/Three PL Container:150",
    cm.client as "Client:Link/Customer:170",
    cm.from_warehouse as "From Location:Link/Warehouse:180",
    cm.to_warehouse as "To Location:Link/Warehouse:180",
    cm.stock_entry as "Stock Entry:Link/Stock Entry:150",
    cm.movement as "Movement:Link/Three PL Container Movement:160",
    cm.notes as "Notes:Small Text:240"
from `tabThree PL Container Move` cm
order by cm.operation_datetime desc, cm.creation desc
""".strip(),
        },
        "3PL Container Repacks": {
            "ref_doctype": "Three PL Container Repack",
            "query": """
select
    r.name as "Repack:Link/Three PL Container Repack:170",
    r.operation_reference as "Operation Ref:Data:150",
    r.operation_datetime as "Operation Time:Datetime:160",
    r.status as "Status:Data:100",
    r.client as "Client:Link/Customer:170",
    r.target_container as "Target Container:Link/Three PL Container:150",
    r.target_location as "Target Location:Link/Warehouse:180",
    src.source_container as "Source Container:Link/Three PL Container:150",
    src.source_location as "Source Location:Link/Warehouse:180",
    item.item_code as "Item:Link/Item:150",
    item.client_sku as "Client SKU:Data:120",
    item.qty as "Qty:Float:90",
    item.uom as "UOM:Link/UOM:80",
    r.movement as "Movement:Link/Three PL Container Movement:160",
    r.notes as "Notes:Small Text:240"
from `tabThree PL Container Repack` r
left join `tabThree PL Repack Source` src on src.parent = r.name
left join `tabThree PL Repack Item` item on item.parent = r.name
order by r.operation_datetime desc, r.creation desc, src.idx asc, item.idx asc
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
        "3PL Client Inventory Summary": {
            "ref_doctype": "Three PL Inventory Snapshot",
            "query": """
select
    inv.customer as "Client:Link/Customer:170",
    inv.item_code as "Item:Link/Item:150",
    inv.client_sku as "Client SKU:Data:120",
    inv.item_name as "Item Name:Data:180",
    sum(inv.qty) as "Total Qty:Float:110",
    inv.uom as "UOM:Link/UOM:80",
    inv.status as "Status:Data:120",
    group_concat(distinct inv.warehouse order by inv.warehouse separator ', ') as "Locations:Data:240",
    group_concat(distinct inv.container_code order by inv.container_code separator ', ') as "Containers:Data:260",
    max(inv.last_updated) as "Last Updated:Datetime:160"
from `tabThree PL Inventory Snapshot` inv
group by inv.customer, inv.item_code, inv.client_sku, inv.item_name, inv.uom, inv.status
order by inv.customer asc, inv.item_code asc, inv.status asc
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


def configure_scanner_pages():
    html = """
<section class="container py-4" style="max-width: 760px;">
  <h1 class="h3 mb-3">Container Move</h1>
  <div class="mb-3">
    <label class="form-label" for="container-code">Container / HU</label>
    <input class="form-control" id="container-code" autocomplete="off" autofocus>
  </div>
  <div class="mb-3">
    <label class="form-label" for="target-location">Target Location</label>
    <input class="form-control" id="target-location" autocomplete="off">
  </div>
  <div class="d-flex gap-2 align-items-center">
    <button class="btn btn-primary" id="create-move" type="button">Create Move</button>
    <span class="text-muted small" id="move-status"></span>
  </div>
</section>
""".strip()
    script = """
(function () {
  function byId(id) { return document.getElementById(id); }
  function setStatus(message, isError) {
    var target = byId('move-status');
    if (!target) return;
    target.textContent = message || '';
    target.className = isError ? 'text-danger small' : 'text-muted small';
  }
  function getCsrfToken() {
    if (frappe.csrf_token && frappe.csrf_token !== 'None') {
      return Promise.resolve(frappe.csrf_token);
    }
    if (window.__threePlCsrfTokenPromise) {
      return window.__threePlCsrfTokenPromise;
    }
    window.__threePlCsrfTokenPromise = fetch('/app', { credentials: 'same-origin' })
      .then(function (response) { return response.text(); })
      .then(function (html) {
        var match = html.match(/frappe\\.csrf_token\\s*=\\s*"([^"]+)"/);
        if (!match || !match[1] || match[1] === 'None') {
          throw new Error('Could not initialize session token. Please refresh and try again.');
        }
        frappe.csrf_token = match[1];
        return match[1];
      });
    return window.__threePlCsrfTokenPromise;
  }
  function parseServerMessage(payload) {
    if (!payload) return null;
    if (payload._server_messages) {
      try {
        var messages = JSON.parse(payload._server_messages);
        if (messages.length) {
          var first = JSON.parse(messages[0]);
          if (first.message) return first.message.replace(/<[^>]*>/g, '');
        }
      } catch (error) {
        return payload._error_message || payload.exception || null;
      }
    }
    return payload._error_message || payload.exception || null;
  }
  function api(method, args) {
    return getCsrfToken().then(function (csrfToken) {
      var body = new URLSearchParams();
      Object.keys(args || {}).forEach(function (key) {
        var value = args[key];
        body.set(key, typeof value === 'string' ? value : JSON.stringify(value));
      });
      return fetch('/api/method/' + method, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-Frappe-CSRF-Token': csrfToken
        },
        body: body
      }).then(function (response) {
        return response.text().then(function (text) {
          var payload = text ? JSON.parse(text) : {};
          if (!response.ok) {
            throw new Error(parseServerMessage(payload) || ('Request failed: ' + response.status));
          }
          return payload;
        });
      });
    });
  }
  function getValue(doctype, filters, fieldname) {
    return api('frappe.client.get_value', { doctype: doctype, filters: filters, fieldname: fieldname });
  }
  function insertMove(doc) {
    return api('frappe.client.insert', { doc: doc });
  }
  function insertDoc(doc) {
    return api('frappe.client.insert', { doc: doc });
  }
  function setValue(doctype, name, fieldname, value) {
    return api('frappe.client.set_value', { doctype: doctype, name: name, fieldname: fieldname, value: value });
  }
  function setValues(doctype, name, values) {
    return Object.keys(values).reduce(function (promise, fieldname) {
      return promise.then(function () {
        return setValue(doctype, name, fieldname, values[fieldname]);
      });
    }, Promise.resolve());
  }
  function hasWarehouseRole() {
    var roles = (frappe.user_roles || []);
    return roles.indexOf('3PL Warehouse User') !== -1 || roles.indexOf('3PL Warehouse Manager') !== -1 || roles.indexOf('System Manager') !== -1;
  }
  function requireWarehouseRole() {
    if (frappe.user_roles && !hasWarehouseRole()) {
      setStatus('This scanner page is only available to warehouse users.', true);
      var button = byId('create-move');
      if (button) button.disabled = true;
      return false;
    }
    return true;
  }
  function applyMove(moveDoc) {
    var movementTime = frappe.datetime.now_datetime();
    return insertDoc({
      doctype: 'Three PL Container Movement',
      movement_datetime: movementTime,
      container_code: moveDoc.container_code,
      client: moveDoc.client,
      movement_type: 'Moved',
      from_warehouse: moveDoc.from_warehouse,
      to_warehouse: moveDoc.to_warehouse,
      reference_doctype: 'Three PL Container Move',
      reference_name: moveDoc.name,
      notes: 'Applied immediately from scanner-first container move page.'
    }).then(function (movementResponse) {
      var movement = movementResponse.message;
      return setValues('Three PL Container', moveDoc.container_code, {
        current_warehouse: moveDoc.to_warehouse,
        status: 'Stored',
        last_moved_at: movementTime
      }).then(function () {
        return setValues('Three PL Container Move', moveDoc.name, {
          status: 'Applied',
          movement: movement.name
        }).then(function () {
          return movement;
        });
      });
    });
  }
  function createMove() {
    if (frappe.session && frappe.session.user === 'Guest') {
      window.location.href = '/login?redirect-to=' + encodeURIComponent('/warehouse/container-move');
      return;
    }
    if (!requireWarehouseRole()) return;
    var containerCode = (byId('container-code').value || '').trim();
    var targetLocation = (byId('target-location').value || '').trim();
    if (!containerCode || !targetLocation) {
      setStatus('Scan container and target location first.', true);
      return;
    }
    setStatus('Creating and applying move...', false);
    getValue('Three PL Container', { name: containerCode }, ['client', 'current_warehouse']).then(function (containerResponse) {
      var container = containerResponse.message;
      if (!container || !container.client) throw new Error('Container not found.');
      if (container.current_warehouse === targetLocation) throw new Error('Target location is the current location.');
      return getValue('Warehouse', { name: targetLocation }, 'name').then(function (warehouseResponse) {
        if (!warehouseResponse.message || !warehouseResponse.message.name) throw new Error('Target location not found.');
        var reference = 'MOVE-' + containerCode + '-' + Date.now();
        return insertMove({
          doctype: 'Three PL Container Move',
          operation_reference: reference,
          operation_datetime: frappe.datetime.now_datetime(),
          status: 'Draft',
          container_code: containerCode,
          client: container.client,
          from_warehouse: container.current_warehouse,
          to_warehouse: targetLocation,
          notes: 'Created from scanner-first container move page.'
        });
      });
    }).then(function (insertResponse) {
      var move = insertResponse.message;
      return applyMove(move).then(function (movement) {
        return { move: move, movement: movement };
      });
    }).then(function (result) {
      setStatus('Move applied: ' + result.move.name + ' / ' + result.movement.name + '.', false);
      byId('container-code').value = '';
      byId('target-location').value = '';
      byId('container-code').focus();
    }).catch(function (error) {
      setStatus(error.message || 'Could not create move.', true);
    });
  }
  frappe.ready(function () {
    if (frappe.session && frappe.session.user === 'Guest') {
      window.location.href = '/login?redirect-to=' + encodeURIComponent('/warehouse/container-move');
      return;
    }
    requireWarehouseRole();
    var button = byId('create-move');
    if (button) button.addEventListener('click', createMove);
    ['container-code', 'target-location'].forEach(function (id) {
      var input = byId(id);
      if (input) input.addEventListener('keydown', function (event) {
        if (event.key === 'Enter') {
          event.preventDefault();
          if (id === 'container-code') byId('target-location').focus();
          else createMove();
        }
      });
    });
  });
})();
""".strip()

    existing_page = frappe.db.get_value("Web Page", {"route": "warehouse/container-move"}, "name")
    if existing_page:
        page = frappe.get_doc("Web Page", existing_page)
    else:
        page = frappe.new_doc("Web Page")
        page.name = "warehouse/container-move"

    page.title = "Container Move"
    page.route = "warehouse/container-move"
    page.published = 1
    if page.meta.has_field("login_required"):
        page.login_required = 1
    page.content_type = "HTML"
    page.main_section = html
    if page.meta.has_field("main_section_html"):
        page.main_section_html = html
    page.javascript = script
    page.insert_code = 0
    page.show_sidebar = 0
    page.save(ignore_permissions=True)


def configure_defaults():
    ensure_doctype_property("Warehouse", "allow_rename", 0, "Check")

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
    configure_scanner_pages()
    configure_defaults()
    configure_email_placeholder()
    mark_setup_complete()
    frappe.db.commit()
    frappe.clear_cache()


main()
