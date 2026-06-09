import json

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from project_config import CLIENT_PORTAL_CUSTOMER, CLIENT_PORTAL_FORMS, CLIENT_PORTAL_HOME, CLIENT_PORTAL_RECEIVING_REF_PREFIX, COMPANY, COMPANY_ABBR, COUNTRY, CURRENCY, LANGUAGE, PLACEHOLDER_EMAIL, TIME_ZONE


CUSTOM_DOCTYPE_MODULE = "Website"


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
        "mandatory_depends_on",
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
    if spec.get("custom"):
        spec = {**spec, "module": CUSTOM_DOCTYPE_MODULE}

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
                {"type": "DocType", "link_to": "Three PL Warehouse Correction", "doc_view": "List", "label": "Warehouse Corrections"},
                {"type": "DocType", "link_to": "Three PL Stocktake Session", "doc_view": "List", "label": "Stocktake Sessions"},
                {"type": "DocType", "link_to": "Three PL Stocktake", "doc_view": "List", "label": "Stocktakes"},
                {"type": "DocType", "link_to": "Stock Entry", "doc_view": "List", "label": "Stock Entries"},
                {"type": "Report", "link_to": "3PL Corrections Needing Review", "label": "Corrections Review", "report_ref_doctype": "Three PL Warehouse Correction"},
                {"type": "DocType", "link_to": "Pick List", "doc_view": "List", "label": "Pick Lists"},
                {"type": "DocType", "link_to": "Three PL Shipment Request", "doc_view": "List", "label": "Shipment Requests"},
                {"type": "Report", "link_to": "3PL ASN vs Received", "label": "ASN vs Received", "report_ref_doctype": "Inbound Shipment Notice"},
                {"type": "Report", "link_to": "3PL Receiving Discrepancies", "label": "Receiving Discrepancies", "report_ref_doctype": "Inbound Shipment Notice"},
                {"type": "Report", "link_to": "3PL Containers", "label": "Containers Report", "report_ref_doctype": "Three PL Container"},
                {"type": "Report", "link_to": "3PL Container Moves", "label": "Container Moves Report", "report_ref_doctype": "Three PL Container Move"},
                {"type": "Report", "link_to": "3PL Container Repacks", "label": "Container Repacks Report", "report_ref_doctype": "Three PL Container Repack"},
                {"type": "Report", "link_to": "3PL Warehouse Corrections", "label": "Warehouse Corrections Report", "report_ref_doctype": "Three PL Warehouse Correction"},
                {"type": "Report", "link_to": "3PL Stocktake Sessions", "label": "Stocktake Sessions Report", "report_ref_doctype": "Three PL Stocktake Session"},
                {"type": "Report", "link_to": "3PL Stocktakes", "label": "Stocktakes Report", "report_ref_doctype": "Three PL Stocktake"},
                {"type": "Report", "link_to": "3PL Container Movements", "label": "Container Movements", "report_ref_doctype": "Three PL Container Movement"},
                {"type": "Report", "link_to": "3PL Client Inventory", "label": "Client Inventory", "report_ref_doctype": "Three PL Inventory Snapshot"},
                {"type": "Report", "link_to": "3PL Client Inventory Summary", "label": "Inventory Summary", "report_ref_doctype": "Three PL Inventory Snapshot"},
                {"type": "Report", "link_to": "3PL Inventory Balance By Date", "label": "Inventory By Date", "report_ref_doctype": "Three PL Inventory Balance Snapshot"},
                {"type": "Report", "link_to": "3PL Warehouse Operation Turnover", "label": "Operation Turnover", "report_ref_doctype": "Three PL Container Movement"},
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
                {"type": "Link", "label": "Warehouse Corrections", "link_type": "DocType", "link_to": "Three PL Warehouse Correction"},
                {"type": "Link", "label": "Stocktake Sessions", "link_type": "DocType", "link_to": "Three PL Stocktake Session"},
                {"type": "Link", "label": "Stocktakes", "link_type": "DocType", "link_to": "Three PL Stocktake"},
                {"type": "Link", "label": "Stock Entries", "link_type": "DocType", "link_to": "Stock Entry"},
                {"type": "Link", "label": "Corrections Needing Review", "link_type": "Report", "link_to": "3PL Corrections Needing Review", "is_query_report": 1},
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
                {"type": "Link", "label": "Warehouse Corrections Report", "link_type": "Report", "link_to": "3PL Warehouse Corrections", "is_query_report": 1},
                {"type": "Link", "label": "Stocktake Sessions Report", "link_type": "Report", "link_to": "3PL Stocktake Sessions", "is_query_report": 1},
                {"type": "Link", "label": "Stocktakes Report", "link_type": "Report", "link_to": "3PL Stocktakes", "is_query_report": 1},
                {"type": "Link", "label": "Container Movements", "link_type": "Report", "link_to": "3PL Container Movements", "is_query_report": 1},
                {"type": "Link", "label": "Inventory Summary", "link_type": "Report", "link_to": "3PL Client Inventory Summary", "is_query_report": 1},
                {"type": "Link", "label": "Inventory By Date", "link_type": "Report", "link_to": "3PL Inventory Balance By Date", "is_query_report": 1},
                {"type": "Link", "label": "Operation Turnover", "link_type": "Report", "link_to": "3PL Warehouse Operation Turnover", "is_query_report": 1},
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
        "3PL Quantity Gain": "Material Receipt",
        "3PL Quantity Loss": "Material Issue",
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
                {"fieldname": "auto_generated", "label": "Auto Generated", "fieldtype": "Check", "default": 0, "in_list_view": 1},
                {"fieldname": "source_stock_entry", "label": "Source Stock Entry", "fieldtype": "Link", "options": "Stock Entry"},
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
                {"fieldname": "status", "label": "Status", "fieldtype": "Select", "options": "Draft\nIn Verification\nPartially Received\nDiscrepancy Review\nReceived\nClosed", "default": "Draft", "in_list_view": 1},
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
                {"fieldname": "movement_type", "label": "Movement Type", "fieldtype": "Select", "options": "Expected\nReceived\nMoved\nPutaway\nPicking\nPicked\nPacked\nShipped\nRepacked\nAdjusted", "reqd": 1, "in_standard_filter": 1, "in_list_view": 1},
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
            "name": "Three PL Inventory Balance Snapshot",
            "module": "Stock",
            "custom": 1,
            "track_changes": 1,
            "title_field": "item_code",
            "autoname": "prompt",
            "fields": [
                {"fieldname": "snapshot_date", "label": "Snapshot Date", "fieldtype": "Date", "reqd": 1, "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "customer", "label": "Client", "fieldtype": "Link", "options": "Customer", "reqd": 1, "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "item_code", "label": "Item", "fieldtype": "Link", "options": "Item", "reqd": 1, "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "client_sku", "label": "Client SKU", "fieldtype": "Data", "in_list_view": 1},
                {"fieldname": "item_name", "label": "Item Name", "fieldtype": "Data", "in_list_view": 1},
                {"fieldname": "qty", "label": "Qty", "fieldtype": "Float", "in_list_view": 1},
                {"fieldname": "uom", "label": "UOM", "fieldtype": "Link", "options": "UOM", "in_list_view": 1},
                {"fieldname": "warehouse", "label": "Location", "fieldtype": "Link", "options": "Warehouse", "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "container_code", "label": "Container / Box", "fieldtype": "Link", "options": "Three PL Container", "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "status", "label": "Status", "fieldtype": "Select", "options": "Available\nReceiving\nHold\nAllocated\nShipped", "default": "Available", "in_list_view": 1},
                {"fieldname": "source_snapshot", "label": "Source Current Snapshot", "fieldtype": "Link", "options": "Three PL Inventory Snapshot", "read_only": 1},
                {"fieldname": "captured_at", "label": "Captured At", "fieldtype": "Datetime", "read_only": 1},
                {"fieldname": "notes", "label": "Notes", "fieldtype": "Small Text"},
            ],
            "permissions": manager_permissions
            + [
                {"role": "3PL Warehouse User", "read": 1, "report": 1},
                {"role": "3PL Client", "read": 1},
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
                {"fieldname": "repack_mode", "label": "Repack Mode", "fieldtype": "Select", "options": "Full Consolidation\nPartial Split", "default": "Full Consolidation", "in_standard_filter": 1, "in_list_view": 1},
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
            "name": "Three PL Warehouse Correction",
            "module": "Stock",
            "custom": 1,
            "track_changes": 1,
            "title_field": "operation_reference",
            "autoname": "naming_series:",
            "fields": [
                {"fieldname": "naming_series", "label": "Series", "fieldtype": "Select", "options": "WH-CORR-.YYYY.-.#####", "default": "WH-CORR-.YYYY.-.#####", "reqd": 1},
                {"fieldname": "operation_reference", "label": "Operation Reference", "fieldtype": "Data", "reqd": 1, "unique": 1, "in_list_view": 1},
                {"fieldname": "operation_datetime", "label": "Operation Time", "fieldtype": "Datetime", "default": "Now", "reqd": 1, "in_list_view": 1},
                {"fieldname": "status", "label": "Status", "fieldtype": "Select", "options": "Draft\nApplied\nNeeds Review\nCancelled", "default": "Draft", "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "correction_type", "label": "Correction Type", "fieldtype": "Select", "options": "Quantity Count\nUnexpected Product\nDamaged Product\nQuality Issue\nHold For Review", "reqd": 1, "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "client", "label": "Client", "fieldtype": "Link", "options": "Customer", "reqd": 1, "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "container_code", "label": "Container / Handling Unit", "fieldtype": "Link", "options": "Three PL Container", "reqd": 1, "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "warehouse", "label": "Location", "fieldtype": "Link", "options": "Warehouse", "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "item_section", "label": "Item", "fieldtype": "Section Break"},
                {"fieldname": "item_code", "label": "Item", "fieldtype": "Link", "options": "Item", "reqd": 1, "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "client_sku", "label": "Client SKU", "fieldtype": "Data", "in_list_view": 1},
                {"fieldname": "uom", "label": "UOM", "fieldtype": "Link", "options": "UOM", "in_list_view": 1},
                {"fieldname": "expected_qty", "label": "Expected Qty", "fieldtype": "Float", "in_list_view": 1},
                {"fieldname": "actual_qty", "label": "Actual Qty", "fieldtype": "Float", "reqd": 1, "in_list_view": 1},
                {"fieldname": "qty_delta", "label": "Qty Delta", "fieldtype": "Float", "read_only": 1, "in_list_view": 1},
                {"fieldname": "condition_status", "label": "Condition", "fieldtype": "Select", "options": "OK\nDamaged\nQuality Issue\nHold", "default": "OK", "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "reference_section", "label": "Reference", "fieldtype": "Section Break"},
                {"fieldname": "movement", "label": "Movement Record", "fieldtype": "Link", "options": "Three PL Container Movement", "read_only": 1},
                {"fieldname": "stock_entry", "label": "Stock Entry", "fieldtype": "Link", "options": "Stock Entry", "read_only": 1},
                {"fieldname": "stock_posting_status", "label": "Stock Posting Status", "fieldtype": "Select", "options": "Pending\nPosted\nNot Required\nNeeds Review", "default": "Pending", "in_standard_filter": 1, "in_list_view": 1, "description": "Managers can reset Needs Review corrections to Pending for retry, or mark them Not Required when no ERPNext stock posting is needed."},
                {"fieldname": "stock_posting_error", "label": "Stock Posting Error", "fieldtype": "Small Text", "read_only": 1},
                {"fieldname": "review_section", "label": "Manager Review", "fieldtype": "Section Break"},
                {"fieldname": "review_decision", "label": "Review Decision", "fieldtype": "Select", "options": "\nRetry Posting\nNo Stock Posting Required\nCancelled", "read_only": 1, "in_list_view": 1},
                {"fieldname": "reviewed_by", "label": "Reviewed By", "fieldtype": "Link", "options": "User", "read_only": 1},
                {"fieldname": "reviewed_at", "label": "Reviewed At", "fieldtype": "Datetime", "read_only": 1},
                {"fieldname": "review_notes", "label": "Review Notes", "fieldtype": "Small Text"},
                {"fieldname": "source_doctype", "label": "Source DocType", "fieldtype": "Link", "options": "DocType"},
                {"fieldname": "source_name", "label": "Source Name", "fieldtype": "Dynamic Link", "options": "source_doctype"},
                {"fieldname": "notes", "label": "Notes", "fieldtype": "Small Text"},
            ],
            "permissions": warehouse_permissions
            + [
                {"role": "Stock User", "read": 1, "write": 1, "create": 1, "report": 1},
            ],
        },
        {
            "name": "Three PL Stocktake Session",
            "module": "Stock",
            "custom": 1,
            "track_changes": 1,
            "title_field": "session_reference",
            "autoname": "naming_series:",
            "fields": [
                {"fieldname": "naming_series", "label": "Series", "fieldtype": "Select", "options": "STOCKTAKE-SESSION-.YYYY.-.#####", "default": "STOCKTAKE-SESSION-.YYYY.-.#####", "reqd": 1},
                {"fieldname": "session_reference", "label": "Session Reference", "fieldtype": "Data", "reqd": 1, "unique": 1, "in_list_view": 1},
                {"fieldname": "status", "label": "Status", "fieldtype": "Select", "options": "Open\nIn Progress\nCompleted\nCancelled", "default": "Open", "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "client", "label": "Client", "fieldtype": "Link", "options": "Customer", "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "warehouse", "label": "Location Scope", "fieldtype": "Link", "options": "Warehouse", "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "started_at", "label": "Started At", "fieldtype": "Datetime", "default": "Now", "in_list_view": 1},
                {"fieldname": "completed_at", "label": "Completed At", "fieldtype": "Datetime", "read_only": 1},
                {"fieldname": "notes", "label": "Notes", "fieldtype": "Small Text"},
            ],
            "permissions": warehouse_permissions
            + [
                {"role": "Stock User", "read": 1, "write": 1, "create": 1, "report": 1},
            ],
        },
        {
            "name": "Three PL Stocktake",
            "module": "Stock",
            "custom": 1,
            "track_changes": 1,
            "title_field": "operation_reference",
            "autoname": "naming_series:",
            "fields": [
                {"fieldname": "naming_series", "label": "Series", "fieldtype": "Select", "options": "STOCKTAKE-.YYYY.-.#####", "default": "STOCKTAKE-.YYYY.-.#####", "reqd": 1},
                {"fieldname": "operation_reference", "label": "Operation Reference", "fieldtype": "Data", "reqd": 1, "unique": 1, "in_list_view": 1},
                {"fieldname": "operation_datetime", "label": "Operation Time", "fieldtype": "Datetime", "default": "Now", "reqd": 1, "in_list_view": 1},
                {"fieldname": "status", "label": "Status", "fieldtype": "Select", "options": "Draft\nApplied\nNo Difference\nNeeds Review\nCancelled", "default": "Draft", "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "stocktake_session", "label": "Stocktake Session", "fieldtype": "Link", "options": "Three PL Stocktake Session", "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "client", "label": "Client", "fieldtype": "Link", "options": "Customer", "reqd": 1, "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "warehouse", "label": "Location", "fieldtype": "Link", "options": "Warehouse", "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "container_code", "label": "Container / Handling Unit", "fieldtype": "Link", "options": "Three PL Container", "reqd": 1, "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "item_code", "label": "Item", "fieldtype": "Link", "options": "Item", "reqd": 1, "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "client_sku", "label": "Client SKU", "fieldtype": "Data", "in_list_view": 1},
                {"fieldname": "uom", "label": "UOM", "fieldtype": "Link", "options": "UOM", "in_list_view": 1},
                {"fieldname": "expected_qty", "label": "System Qty", "fieldtype": "Float", "in_list_view": 1},
                {"fieldname": "counted_qty", "label": "Counted Qty", "fieldtype": "Float", "reqd": 1, "in_list_view": 1},
                {"fieldname": "qty_delta", "label": "Qty Delta", "fieldtype": "Float", "read_only": 1, "in_list_view": 1},
                {"fieldname": "condition_status", "label": "Condition", "fieldtype": "Select", "options": "OK\nDamaged\nQuality Issue\nHold", "default": "OK", "in_standard_filter": 1, "in_list_view": 1},
                {"fieldname": "correction", "label": "Correction", "fieldtype": "Link", "options": "Three PL Warehouse Correction", "read_only": 1},
                {"fieldname": "movement", "label": "Movement Record", "fieldtype": "Link", "options": "Three PL Container Movement", "read_only": 1},
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
        "Three PL Warehouse Correction": {"read": 1},
        "Three PL Stocktake": {"read": 1},
        "Three PL Repack Source": {"read": 1},
        "Three PL Repack Item": {"read": 1},
        "Three PL Inventory Snapshot": {"read": 1},
        "Three PL Inventory Balance Snapshot": {"read": 1},
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
        "Three PL Warehouse Correction": warehouse_permissions
        + [
            {"role": "Stock User", "read": 1, "write": 1, "create": 1, "report": 1},
        ],
        "Three PL Stocktake": warehouse_permissions
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
        "Three PL Inventory Balance Snapshot": [
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
            permission.pop("doctype", None)
            permission.pop("name", None)
            permission.pop("parent", None)
            permission.pop("parentfield", None)
            permission.pop("parenttype", None)
            permission.pop("idx", None)
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
                "mandatory_depends_on": "eval:doc.warehouse_flow=='Inbound Receipt'",
            },
            {
                "fieldname": "inbound_shipment_notice",
                "label": "Inbound Shipment Notice",
                "fieldtype": "Link",
                "options": "Inbound Shipment Notice",
                "insert_after": "client",
                "depends_on": "eval:doc.client",
                "mandatory_depends_on": "eval:doc.warehouse_flow=='Inbound Receipt'",
            },
            {
                "fieldname": "shipment_request",
                "label": "Shipment Request",
                "fieldtype": "Link",
                "options": "Three PL Shipment Request",
                "insert_after": "inbound_shipment_notice",
                "depends_on": "eval:doc.client",
                "in_standard_filter": 1,
            },
            {
                "fieldname": "shipment_reference",
                "label": "Shipment Reference",
                "fieldtype": "Data",
                "insert_after": "shipment_request",
            },
            {
                "fieldname": "warehouse_flow",
                "label": "Warehouse Flow",
                "fieldtype": "Select",
                "options": "\nInbound Receipt\nComparison\nPut Away\nInternal Movement\nWarehouse Correction\nPicking Support\nPacking\nShipping",
                "insert_after": "shipment_reference",
                "in_standard_filter": 1,
            },
            {
                "fieldname": "scanned_location",
                "label": "Scanned Location",
                "fieldtype": "Link",
                "options": "Warehouse",
                "insert_after": "warehouse_flow",
                "mandatory_depends_on": "eval:doc.warehouse_flow=='Inbound Receipt'",
                "description": "Use this to record the warehouse/location barcode scanned before scanning products.",
            },
            {
                "fieldname": "container_code",
                "label": "Container / Box",
                "fieldtype": "Link",
                "options": "Three PL Container",
                "insert_after": "scanned_location",
                "mandatory_depends_on": "eval:doc.warehouse_flow=='Inbound Receipt'",
                "description": "Container or box scanned during receiving, putaway, picking, packing, or shipping.",
            },
            {
                "fieldname": "warehouse_correction",
                "label": "Warehouse Correction",
                "fieldtype": "Link",
                "options": "Three PL Warehouse Correction",
                "insert_after": "container_code",
                "depends_on": "eval:doc.warehouse_flow=='Warehouse Correction'",
                "in_standard_filter": 1,
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
                "fieldname": "shipment_request",
                "label": "Shipment Request",
                "fieldtype": "Link",
                "options": "Three PL Shipment Request",
                "insert_after": "shipment_reference",
                "in_standard_filter": 1,
            },
            {
                "fieldname": "container_code",
                "label": "Container / Box",
                "fieldtype": "Link",
                "options": "Three PL Container",
                "insert_after": "shipment_request",
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
            client_script=form.get("client_script"),
        )

    configure_client_status_pages()
    configure_portal_menu()
    configure_client_portal_website_script()


def build_client_portal_nav():
    links = []
    for form in CLIENT_PORTAL_FORMS:
        label = frappe.utils.escape_html(form["menu_title"])
        links.append(f'<a class="btn btn-sm btn-default" href="/{portal_list_route(form["route"])}">{label}</a>')
    links.append('<a class="btn btn-sm btn-default" href="/client/discrepancies">Discrepancies</a>')
    links.append('<a class="btn btn-sm btn-default" href="/client/shipment-tracking">Shipment Tracking</a>')
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

  function getWebFormValue(fieldname) {{
    if (window.frappe && frappe.web_form && frappe.web_form.get_value) {{
      return frappe.web_form.get_value(fieldname);
    }}
    var input = document.querySelector('[data-fieldname="' + fieldname + '"] input, [name="' + fieldname + '"], input[data-fieldname="' + fieldname + '"]');
    return input ? input.value : '';
  }}

  function setWebFormValue(fieldname, value) {{
    if (window.frappe && frappe.web_form && frappe.web_form.set_value) {{
      frappe.web_form.set_value(fieldname, value);
      return;
    }}
    var input = document.querySelector('[data-fieldname="' + fieldname + '"] input, [name="' + fieldname + '"], input[data-fieldname="' + fieldname + '"]');
    if (input) {{
      input.value = value;
      input.dispatchEvent(new Event('change', {{ bubbles: true }}));
    }}
  }}

  function padReferencePart(value, width) {{
    return String(value).padStart(width, '0');
  }}

  function todayReferenceStamp() {{
    var now = new Date();
    return String(now.getFullYear()) + padReferencePart(now.getMonth() + 1, 2) + padReferencePart(now.getDate(), 2);
  }}

  function nextReceivingReference(rows, basePrefix) {{
    var maxNumber = 0;
    (rows || []).forEach(function (row) {{
      var ref = row.external_reference || '';
      if (ref.indexOf(basePrefix + '-') !== 0) return;
      var parsed = parseInt(ref.slice(basePrefix.length + 1), 10);
      if (!Number.isNaN(parsed)) maxNumber = Math.max(maxNumber, parsed);
    }});
    return basePrefix + '-' + padReferencePart(maxNumber + 1, 3);
  }}

  function autoFillReceivingNoticeReference() {{
    if (window.location.pathname !== '/client/receiving-notice/new') return;
    if (getWebFormValue('external_reference')) return;

    var basePrefix = '{CLIENT_PORTAL_RECEIVING_REF_PREFIX}-' + todayReferenceStamp();
    var customer = getWebFormValue('customer') || '{CLIENT_PORTAL_CUSTOMER}';
    var payload = new URLSearchParams();
    payload.set('doctype', 'Inbound Shipment Notice');
    payload.set('filters', JSON.stringify({{
      customer: customer,
      external_reference: ['like', basePrefix + '-%']
    }}));
    payload.set('fields', JSON.stringify(['external_reference']));
    payload.set('limit_page_length', '100');
    payload.set('order_by', 'external_reference desc');

    fetch('/api/method/frappe.client.get_list', {{
      method: 'POST',
      credentials: 'same-origin',
      headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
      body: payload.toString()
    }})
      .then(function (response) {{ return response.json(); }})
      .then(function (response) {{
        if (getWebFormValue('external_reference')) return;
        setWebFormValue('external_reference', nextReceivingReference(response.message || [], basePrefix));
      }})
      .catch(function () {{
        if (!getWebFormValue('external_reference')) {{
          setWebFormValue('external_reference', basePrefix + '-001');
        }}
      }});
  }}

  if (window.frappe && frappe.ready) {{
    tuneClientPortalBoot();
    frappe.ready(function () {{
      tuneClientPortalBoot();
      installClientPortalNav();
      renderClientPortalList();
      autoFillReceivingNoticeReference();
      removeDeskPermissionNoise();
      setTimeout(renderClientPortalList, 250);
      setTimeout(autoFillReceivingNoticeReference, 250);
      setTimeout(removeDeskPermissionNoise, 250);
      setTimeout(renderClientPortalList, 1000);
      setTimeout(autoFillReceivingNoticeReference, 1000);
      setTimeout(removeDeskPermissionNoise, 1000);
    }});
  }} else {{
    document.addEventListener('DOMContentLoaded', function () {{
      tuneClientPortalBoot();
      installClientPortalNav();
      renderClientPortalList();
      autoFillReceivingNoticeReference();
      removeDeskPermissionNoise();
    }});
  }}
}})();
""".strip()

    settings = frappe.get_single("Website Script")
    if settings.javascript != script:
        settings.javascript = script
        settings.save(ignore_permissions=True)


def configure_client_status_pages():
    portal_nav = build_client_portal_nav()
    pages = [
        {
            "route": "client/discrepancies",
            "title": "Discrepancies",
            "html": f"""
<section class="container py-4">
  {portal_nav}
  <h1 class="h3 mb-3">Discrepancies</h1>
  <div class="text-muted small mb-3">Review receiving discrepancies recorded by the warehouse and submit instructions when needed.</div>
  <div class="table-responsive">
    <table class="table table-sm align-middle">
      <thead>
        <tr>
          <th>Receiving Notice</th>
          <th>Client Ref</th>
          <th>Type</th>
          <th>Item</th>
          <th>Expected</th>
          <th>Actual</th>
          <th>Variance</th>
          <th>Status</th>
          <th>Notes</th>
        </tr>
      </thead>
      <tbody id="client-discrepancy-body">
        <tr><td colspan="9" class="text-muted">Loading...</td></tr>
      </tbody>
    </table>
  </div>
  <div class="small text-muted" id="client-discrepancy-status"></div>
</section>
""".strip(),
            "javascript": f"""
(function () {{
  function byId(id) {{ return document.getElementById(id); }}
  function setStatus(message, isError) {{
    var target = byId('client-discrepancy-status');
    if (!target) return;
    target.textContent = message || '';
    target.className = isError ? 'small text-danger' : 'small text-muted';
  }}
  function escapeHtml(value) {{
    return String(value == null ? '' : value).replace(/[&<>"']/g, function (ch) {{
      return ({{'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}})[ch];
    }});
  }}
  function api(method, args) {{
    var body = new URLSearchParams();
    Object.keys(args || {{}}).forEach(function (key) {{
      var value = args[key];
      body.set(key, typeof value === 'string' ? value : JSON.stringify(value));
    }});
    return fetch('/api/method/' + method, {{
      method: 'POST',
      credentials: 'same-origin',
      headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
      body: body
    }}).then(function (response) {{
      return response.json().then(function (payload) {{
        if (!response.ok) throw new Error(payload.exception || payload._error_message || ('Request failed: ' + response.status));
        return payload;
      }});
    }});
  }}
  function loadRows() {{
    if (frappe.session && frappe.session.user === 'Guest') {{
      window.location.href = '/login?redirect-to=' + encodeURIComponent('/client/discrepancies');
      return;
    }}
    setStatus('Loading discrepancies...', false);
    api('frappe.client.get_list', {{
      doctype: 'Inbound Shipment Notice',
      filters: {{ customer: '{CLIENT_PORTAL_CUSTOMER}' }},
      fields: ['name', 'external_reference', 'status', 'client_instruction_status'],
      order_by: 'modified desc',
      limit_page_length: 50
    }}).then(function (response) {{
      var notices = response.message || [];
      return Promise.all(notices.map(function (notice) {{
        return api('frappe.client.get', {{ doctype: 'Inbound Shipment Notice', name: notice.name }}).then(function (docResponse) {{
          var doc = docResponse.message || {{}};
          return (doc.discrepancies || []).map(function (row) {{
            row.notice = doc.name;
            row.external_reference = doc.external_reference;
            row.notice_status = doc.status;
            row.client_instruction_status = doc.client_instruction_status;
            return row;
          }});
        }});
      }}));
    }}).then(function (groups) {{
      var rows = [].concat.apply([], groups || []);
      if (!rows.length) {{
        byId('client-discrepancy-body').innerHTML = '<tr><td colspan="9" class="text-muted">No discrepancies recorded.</td></tr>';
        setStatus('', false);
        return;
      }}
      byId('client-discrepancy-body').innerHTML = rows.map(function (row) {{
        return '<tr>' +
          '<td>' + escapeHtml(row.notice) + '</td>' +
          '<td>' + escapeHtml(row.external_reference) + '</td>' +
          '<td>' + escapeHtml(row.discrepancy_type) + '</td>' +
          '<td>' + escapeHtml(row.client_sku || row.item_code) + '</td>' +
          '<td>' + escapeHtml(row.expected_qty) + '</td>' +
          '<td>' + escapeHtml(row.actual_qty) + '</td>' +
          '<td>' + escapeHtml(row.variance_qty) + '</td>' +
          '<td>' + escapeHtml(row.status) + '</td>' +
          '<td class="small text-muted">' + escapeHtml(row.notes) + '</td>' +
        '</tr>';
      }}).join('');
      setStatus(rows.length + ' discrepancy row(s). Use Discrepancy Instructions to send a decision to the warehouse.', false);
    }}).catch(function (error) {{
      setStatus(error.message || 'Could not load discrepancies.', true);
    }});
  }}
  frappe.ready(loadRows);
}})();
""".strip(),
        },
        {
            "route": "client/shipment-tracking",
            "title": "Shipment Tracking",
            "html": f"""
<section class="container py-4">
  {portal_nav}
  <h1 class="h3 mb-3">Shipment Tracking</h1>
  <div class="text-muted small mb-3">Track client shipment request status from submission through warehouse processing.</div>
  <div class="table-responsive">
    <table class="table table-sm align-middle">
      <thead>
        <tr>
          <th>Request</th>
          <th>Client Ref</th>
          <th>Status</th>
          <th>Requested Ship Date</th>
          <th>Destination</th>
          <th>Items</th>
          <th>Notes</th>
        </tr>
      </thead>
      <tbody id="client-shipment-tracking-body">
        <tr><td colspan="7" class="text-muted">Loading...</td></tr>
      </tbody>
    </table>
  </div>
  <div class="small text-muted" id="client-shipment-tracking-status"></div>
</section>
""".strip(),
            "javascript": f"""
(function () {{
  function byId(id) {{ return document.getElementById(id); }}
  function setStatus(message, isError) {{
    var target = byId('client-shipment-tracking-status');
    if (!target) return;
    target.textContent = message || '';
    target.className = isError ? 'small text-danger' : 'small text-muted';
  }}
  function escapeHtml(value) {{
    return String(value == null ? '' : value).replace(/[&<>"']/g, function (ch) {{
      return ({{'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}})[ch];
    }});
  }}
  function api(method, args) {{
    var body = new URLSearchParams();
    Object.keys(args || {{}}).forEach(function (key) {{
      var value = args[key];
      body.set(key, typeof value === 'string' ? value : JSON.stringify(value));
    }});
    return fetch('/api/method/' + method, {{
      method: 'POST',
      credentials: 'same-origin',
      headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
      body: body
    }}).then(function (response) {{
      return response.json().then(function (payload) {{
        if (!response.ok) throw new Error(payload.exception || payload._error_message || ('Request failed: ' + response.status));
        return payload;
      }});
    }});
  }}
  function loadRows() {{
    if (frappe.session && frappe.session.user === 'Guest') {{
      window.location.href = '/login?redirect-to=' + encodeURIComponent('/client/shipment-tracking');
      return;
    }}
    setStatus('Loading shipment requests...', false);
    api('frappe.client.get_list', {{
      doctype: 'Three PL Shipment Request',
      filters: {{ customer: '{CLIENT_PORTAL_CUSTOMER}' }},
      fields: ['name', 'external_reference', 'status', 'requested_ship_date', 'destination_name', 'portal_items_description', 'notes'],
      order_by: 'modified desc',
      limit_page_length: 50
    }}).then(function (response) {{
      var rows = response.message || [];
      if (!rows.length) {{
        byId('client-shipment-tracking-body').innerHTML = '<tr><td colspan="7" class="text-muted">No shipment requests yet.</td></tr>';
        setStatus('', false);
        return;
      }}
      byId('client-shipment-tracking-body').innerHTML = rows.map(function (row) {{
        return '<tr>' +
          '<td>' + escapeHtml(row.name) + '</td>' +
          '<td>' + escapeHtml(row.external_reference) + '</td>' +
          '<td>' + escapeHtml(row.status) + '</td>' +
          '<td>' + escapeHtml(row.requested_ship_date) + '</td>' +
          '<td>' + escapeHtml(row.destination_name) + '</td>' +
          '<td class="small">' + escapeHtml(row.portal_items_description) + '</td>' +
          '<td class="small text-muted">' + escapeHtml(row.notes) + '</td>' +
        '</tr>';
      }}).join('');
      setStatus(rows.length + ' shipment request(s).', false);
    }}).catch(function (error) {{
      setStatus(error.message || 'Could not load shipment tracking.', true);
    }});
  }}
  frappe.ready(loadRows);
}})();
""".strip(),
        },
    ]

    for page_data in pages:
        existing_page = frappe.db.get_value("Web Page", {"route": page_data["route"]}, "name")
        if existing_page:
            page = frappe.get_doc("Web Page", existing_page)
        else:
            page = frappe.new_doc("Web Page")
            page.name = page_data["route"]
        page.title = page_data["title"]
        page.route = page_data["route"]
        page.published = 1
        if page.meta.has_field("login_required"):
            page.login_required = 1
        page.content_type = "HTML"
        page.main_section = page_data["html"]
        if page.meta.has_field("main_section_html"):
            page.main_section_html = page_data["html"]
        page.javascript = page_data["javascript"]
        page.insert_code = 0
        page.show_sidebar = 0
        page.save(ignore_permissions=True)


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
    client_script=None,
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
    form.module = "Website"
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
    if client_script:
        if form.meta.has_field("client_script"):
            form.client_script = client_script
        elif form.meta.has_field("script"):
            form.script = client_script

    for field in fields:
        form.append("web_form_fields", field)

    form.save(ignore_permissions=True)


def configure_portal_menu():
    portal_settings = frappe.get_single("Portal Settings")
    menu_items = [
        {
            "title": form["menu_title"],
            "route": portal_list_route(form["route"]),
            "reference_doctype": form["doc_type"],
        }
        for form in CLIENT_PORTAL_FORMS
    ] + [
        {"title": "Discrepancies", "route": "client/discrepancies", "reference_doctype": "Inbound Shipment Notice"},
        {"title": "Shipment Tracking", "route": "client/shipment-tracking", "reference_doctype": "Three PL Shipment Request"},
    ]
    for menu_item in menu_items:
        item = None
        for row in portal_settings.menu:
            if row.title == menu_item["title"] or row.route == menu_item["route"]:
                item = row
                break
        if item is None:
            item = portal_settings.append("menu", {})

        item.title = menu_item["title"]
        item.enabled = 1
        item.route = menu_item["route"]
        item.reference_doctype = menu_item["reference_doctype"]
        item.role = "3PL Client"
        item.target = ""

    portal_settings.default_role = "3PL Client"
    portal_settings.default_portal_home = CLIENT_PORTAL_HOME
    portal_settings.save(ignore_permissions=True)


def configure_reports():
    report_roles = [
        "System Manager",
        "Stock Manager",
        "Stock User",
        "3PL Warehouse Manager",
        "3PL Warehouse User",
    ]
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
    r.repack_mode as "Mode:Data:130",
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
        "3PL Warehouse Corrections": {
            "ref_doctype": "Three PL Warehouse Correction",
            "query": """
select
    c.name as "Correction:Link/Three PL Warehouse Correction:170",
    c.operation_reference as "Operation Ref:Data:160",
    c.operation_datetime as "Operation Time:Datetime:160",
    c.status as "Status:Data:110",
    c.correction_type as "Type:Data:150",
    c.client as "Client:Link/Customer:170",
    c.container_code as "Container / HU:Link/Three PL Container:150",
    c.warehouse as "Location:Link/Warehouse:180",
    c.item_code as "Item:Link/Item:150",
    c.client_sku as "Client SKU:Data:120",
    c.expected_qty as "Expected Qty:Float:110",
    c.actual_qty as "Actual Qty:Float:110",
    c.qty_delta as "Delta:Float:90",
    c.condition_status as "Condition:Data:120",
    c.movement as "Movement:Link/Three PL Container Movement:160",
    c.stock_posting_status as "Stock Posting:Data:130",
    c.stock_entry as "Stock Entry:Link/Stock Entry:150",
    c.stock_posting_error as "Stock Posting Error:Small Text:220",
    c.review_decision as "Review Decision:Data:170",
    c.reviewed_by as "Reviewed By:Link/User:160",
    c.reviewed_at as "Reviewed At:Datetime:160",
    c.review_notes as "Review Notes:Small Text:220",
    c.notes as "Notes:Small Text:260"
from `tabThree PL Warehouse Correction` c
order by c.operation_datetime desc, c.creation desc
""".strip(),
        },
        "3PL Corrections Needing Review": {
            "ref_doctype": "Three PL Warehouse Correction",
            "query": """
select
    c.name as "Correction:Link/Three PL Warehouse Correction:170",
    c.operation_datetime as "Operation Time:Datetime:160",
    c.correction_type as "Type:Data:150",
    c.client as "Client:Link/Customer:170",
    c.container_code as "Container / HU:Link/Three PL Container:150",
    c.warehouse as "Location:Link/Warehouse:180",
    c.item_code as "Item:Link/Item:150",
    c.client_sku as "Client SKU:Data:120",
    c.qty_delta as "Delta:Float:90",
    c.condition_status as "Condition:Data:120",
    c.stock_posting_status as "Stock Posting:Data:130",
    c.stock_posting_error as "Stock Posting Error:Small Text:320",
    c.review_notes as "Review Notes:Small Text:220",
    c.notes as "Notes:Small Text:240"
from `tabThree PL Warehouse Correction` c
where c.stock_posting_status = 'Needs Review'
order by c.modified desc
""".strip(),
        },
        "3PL Stocktakes": {
            "ref_doctype": "Three PL Stocktake",
            "query": """
select
    s.name as "Stocktake:Link/Three PL Stocktake:170",
    s.stocktake_session as "Session:Link/Three PL Stocktake Session:180",
    s.operation_reference as "Operation Ref:Data:160",
    s.operation_datetime as "Operation Time:Datetime:160",
    s.status as "Status:Data:120",
    s.client as "Client:Link/Customer:170",
    s.warehouse as "Location:Link/Warehouse:180",
    s.container_code as "Container / HU:Link/Three PL Container:150",
    s.item_code as "Item:Link/Item:150",
    s.client_sku as "Client SKU:Data:120",
    s.expected_qty as "System Qty:Float:110",
    s.counted_qty as "Counted Qty:Float:110",
    s.qty_delta as "Delta:Float:90",
    s.condition_status as "Condition:Data:120",
    s.correction as "Correction:Link/Three PL Warehouse Correction:170",
    s.movement as "Movement:Link/Three PL Container Movement:160",
    s.notes as "Notes:Small Text:260"
from `tabThree PL Stocktake` s
order by s.operation_datetime desc, s.creation desc
""".strip(),
        },
        "3PL Stocktake Sessions": {
            "ref_doctype": "Three PL Stocktake Session",
            "query": """
select
    session.name as "Session:Link/Three PL Stocktake Session:180",
    session.session_reference as "Session Ref:Data:180",
    session.status as "Status:Data:120",
    session.client as "Client:Link/Customer:170",
    session.warehouse as "Location Scope:Link/Warehouse:180",
    session.started_at as "Started At:Datetime:160",
    session.completed_at as "Completed At:Datetime:160",
    count(stocktake.name) as "Count Lines:Int:100",
    sum(case when coalesce(stocktake.qty_delta, 0) <> 0 or stocktake.condition_status <> 'OK' then 1 else 0 end) as "Variance Lines:Int:110",
    sum(case when stocktake.correction is not null and stocktake.correction != '' then 1 else 0 end) as "Corrections:Int:100",
    session.notes as "Notes:Small Text:240"
from `tabThree PL Stocktake Session` session
left join `tabThree PL Stocktake` stocktake on stocktake.stocktake_session = session.name
group by session.name, session.session_reference, session.status, session.client, session.warehouse, session.started_at, session.completed_at, session.notes
order by session.started_at desc, session.creation desc
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
        "3PL Inventory Balance By Date": {
            "ref_doctype": "Three PL Inventory Balance Snapshot",
            "query": """
select
    bal.snapshot_date as "Snapshot Date:Date:110",
    bal.customer as "Client:Link/Customer:170",
    bal.item_code as "Item:Link/Item:150",
    bal.client_sku as "Client SKU:Data:120",
    bal.item_name as "Item Name:Data:180",
    sum(bal.qty) as "Qty:Float:100",
    bal.uom as "UOM:Link/UOM:80",
    bal.status as "Status:Data:120",
    group_concat(distinct bal.warehouse order by bal.warehouse separator ', ') as "Locations:Data:260",
    group_concat(distinct bal.container_code order by bal.container_code separator ', ') as "Containers:Data:260",
    max(bal.captured_at) as "Captured At:Datetime:160"
from `tabThree PL Inventory Balance Snapshot` bal
group by bal.snapshot_date, bal.customer, bal.item_code, bal.client_sku, bal.item_name, bal.uom, bal.status
order by bal.snapshot_date desc, bal.customer asc, bal.item_code asc, bal.status asc
""".strip(),
        },
        "3PL Warehouse Operation Turnover": {
            "ref_doctype": "Three PL Container Movement",
            "query": """
select
    date(m.movement_datetime) as "Operation Date:Date:110",
    m.movement_datetime as "Operation Time:Datetime:160",
    m.client as "Client:Link/Customer:170",
    m.movement_type as "Operation Type:Data:130",
    m.container_code as "Container / HU:Link/Three PL Container:150",
    m.from_warehouse as "From Location:Link/Warehouse:180",
    m.to_warehouse as "To Location:Link/Warehouse:180",
    m.from_container as "From Container:Link/Three PL Container:150",
    m.to_container as "To Container:Link/Three PL Container:150",
    m.reference_doctype as "Reference Type:Data:140",
    m.reference_name as "Reference:Dynamic Link/reference_doctype:170",
    m.notes as "Notes:Small Text:260"
from `tabThree PL Container Movement` m
order by m.movement_datetime desc, m.creation desc
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
        report.set("roles", [])
        for role in report_roles:
            report.append("roles", {"role": role})
        report.save(ignore_permissions=True)


def configure_scanner_pages():
    receiving_html = """
<section class="container py-4" style="max-width: 820px;">
  <h1 class="h3 mb-3">Receiving Scan</h1>
  <div class="row g-3">
    <div class="col-md-6">
      <label class="form-label" for="receiving-notice">Receiving Notice / ASN</label>
      <input class="form-control" id="receiving-notice" autocomplete="off" autofocus>
    </div>
    <div class="col-md-6">
      <label class="form-label" for="receiving-container">Container / HU</label>
      <input class="form-control" id="receiving-container" autocomplete="off">
    </div>
    <div class="col-md-5">
      <label class="form-label" for="receiving-item">Item / SKU</label>
      <input class="form-control" id="receiving-item" autocomplete="off">
    </div>
    <div class="col-md-3">
      <label class="form-label" for="receiving-qty">Qty</label>
      <input class="form-control" id="receiving-qty" inputmode="decimal" autocomplete="off">
    </div>
    <div class="col-md-4">
      <label class="form-label" for="receiving-location">Receiving Location</label>
      <input class="form-control" id="receiving-location" autocomplete="off" value="Temporary Receiving - 3">
    </div>
    <div class="col-md-4">
      <label class="form-label" for="receiving-condition">Condition</label>
      <select class="form-select" id="receiving-condition">
        <option value="OK">OK</option>
        <option value="Damaged">Damaged</option>
        <option value="Quality Issue">Quality Issue</option>
        <option value="Hold">Hold</option>
      </select>
    </div>
    <div class="col-md-8">
      <label class="form-label" for="receiving-notes">Inspection Notes</label>
      <input class="form-control" id="receiving-notes" autocomplete="off">
    </div>
  </div>
  <div class="d-flex gap-2 align-items-center mt-3">
    <button class="btn btn-primary" id="submit-receiving" type="button">Submit Receipt</button>
    <span class="text-muted small" id="receiving-status"></span>
  </div>
</section>
""".strip()
    receiving_script = """
(function () {
  function byId(id) { return document.getElementById(id); }
  function setStatus(message, isError) {
    var target = byId('receiving-status');
    if (!target) return;
    target.textContent = message || '';
    target.className = isError ? 'text-danger small' : 'text-muted small';
  }
  function getCsrfToken() {
    if (frappe.csrf_token && frappe.csrf_token !== 'None') return Promise.resolve(frappe.csrf_token);
    if (window.__threePlCsrfTokenPromise) return window.__threePlCsrfTokenPromise;
    window.__threePlCsrfTokenPromise = fetch('/app', { credentials: 'same-origin' })
      .then(function (response) { return response.text(); })
      .then(function (html) {
        var match = html.match(/frappe\\.csrf_token\\s*=\\s*"([^"]+)"/);
        if (!match || !match[1] || match[1] === 'None') throw new Error('Could not initialize session token. Please refresh and try again.');
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
          if (!response.ok) throw new Error(parseServerMessage(payload) || ('Request failed: ' + response.status));
          return payload;
        });
      });
    });
  }
  function hasWarehouseRole() {
    var roles = (frappe.user_roles || []);
    return roles.indexOf('3PL Warehouse User') !== -1 || roles.indexOf('3PL Warehouse Manager') !== -1 || roles.indexOf('System Manager') !== -1;
  }
  function requireWarehouseRole() {
    if (frappe.user_roles && !hasWarehouseRole()) {
      setStatus('This scanner page is only available to warehouse users.', true);
      var button = byId('submit-receiving');
      if (button) button.disabled = true;
      return false;
    }
    return true;
  }
  function getDoc(doctype, name) {
    return api('frappe.client.get', { doctype: doctype, name: name });
  }
  function getValue(doctype, filters, fieldname) {
    return api('frappe.client.get_value', { doctype: doctype, filters: filters, fieldname: fieldname });
  }
  function insertDoc(doc) {
    return api('frappe.client.insert', { doc: doc });
  }
  function saveDoc(doc) {
    return api('frappe.client.save', { doc: doc });
  }
  function submitDoc(doc) {
    return api('frappe.client.submit', { doc: doc });
  }
  function findNotice(reference) {
    return getValue('Inbound Shipment Notice', { name: reference }, ['name', 'customer', 'external_reference']).then(function (response) {
      if (response.message && response.message.name) return getDoc('Inbound Shipment Notice', response.message.name).then(function (docResponse) { return docResponse.message; });
      return getValue('Inbound Shipment Notice', { external_reference: reference }, ['name', 'customer', 'external_reference']).then(function (byReference) {
        if (byReference.message && byReference.message.name) return getDoc('Inbound Shipment Notice', byReference.message.name).then(function (docResponse) { return docResponse.message; });
        throw new Error('Receiving Notice not found.');
      });
    });
  }
  function ensureContainer(containerCode, notice, location) {
    return getValue('Three PL Container', { name: containerCode }, 'name').then(function (response) {
      if (!response.message || !response.message.name) {
        return insertDoc({
          doctype: 'Three PL Container',
          container_code: containerCode,
          barcode: containerCode,
          container_type: 'Box',
          client: notice.customer,
          current_warehouse: location,
          status: 'Received',
          inbound_shipment_notice: notice.name,
          last_moved_at: frappe.datetime.now_datetime()
        }).then(function (insertResponse) { return insertResponse.message; });
      }
      return getDoc('Three PL Container', containerCode).then(function (containerResponse) {
        var container = containerResponse.message;
        if (container.client && container.client !== notice.customer) throw new Error('Container belongs to another client.');
        if (['Shipped', 'Closed', 'Replaced'].indexOf(container.status) !== -1) throw new Error('Container cannot receive stock from status ' + container.status + '.');
        container.client = notice.customer;
        container.current_warehouse = location;
        container.status = 'Received';
        container.inbound_shipment_notice = notice.name;
        container.last_moved_at = frappe.datetime.now_datetime();
        return saveDoc(container).then(function (saveResponse) { return saveResponse.message || container; });
      });
    });
  }
  function updateContainerItems(containerCode, itemCode, clientSku, qty, uom, condition, notes) {
    return getDoc('Three PL Container', containerCode).then(function (containerResponse) {
      var container = containerResponse.message;
      var matched = false;
      container.items = container.items || [];
      container.items.forEach(function (row) {
        if (row.item_code === itemCode && row.uom === uom && (row.condition_status || 'OK') === condition) {
          row.qty = Number(row.qty || 0) + qty;
          if (notes) row.notes = notes;
          matched = true;
        }
      });
      if (!matched) {
        container.items.push({
          item_code: itemCode,
          client_sku: clientSku,
          qty: qty,
          uom: uom,
          condition_status: condition,
          notes: notes || 'Received from scanner-first receiving page.'
        });
      }
      if (condition !== 'OK') {
        container.status = 'In Verification';
      }
      return saveDoc(container);
    });
  }
  function createAndSubmitStockEntry(notice, containerCode, itemCode, qty, uom, location) {
    return insertDoc({
      doctype: 'Stock Entry',
      stock_entry_type: '3PL Inbound Receipt',
      purpose: 'Material Receipt',
      company: '3pl',
      posting_date: frappe.datetime.get_today(),
      client: notice.customer,
      inbound_shipment_notice: notice.name,
      warehouse_flow: 'Inbound Receipt',
      scanned_location: location,
      container_code: containerCode,
      items: [{
        item_code: itemCode,
        qty: qty,
        t_warehouse: location,
        uom: uom,
        stock_uom: uom,
        conversion_factor: 1,
        basic_rate: 1,
        allow_zero_valuation_rate: 1,
        scanned_location: location,
        container_code: containerCode
      }]
    }).then(function (insertResponse) {
      return submitDoc(insertResponse.message);
    });
  }
  function syncNoticeRow(notice, itemCode, clientSku, qty, uom, containerCode, entryName, condition, notes) {
    var matched = false;
    (notice.items || []).forEach(function (row) {
      if (row.item_code === itemCode && row.uom === uom) {
        row.received_qty = Number(row.received_qty || 0) + qty;
        row.container_code = containerCode;
        row.condition_status = condition;
        matched = true;
      }
    });
    if (!matched) {
      notice.discrepancies = notice.discrepancies || [];
      notice.discrepancies.push({
        discrepancy_type: 'Unexpected Product',
        item_code: itemCode,
        client_sku: clientSku,
        expected_qty: 0,
        actual_qty: qty,
        variance_qty: qty,
        status: 'Open',
        auto_generated: 0,
        source_stock_entry: entryName,
        container_code: containerCode,
        notes: notes || 'Unexpected product received from scanner-first receiving page.'
      });
    }
    (notice.items || []).forEach(function (row) {
      row.variance_qty = Number(row.received_qty || 0) - Number(row.expected_qty || 0);
    });
    if (matched && condition !== 'OK') {
      notice.discrepancies = notice.discrepancies || [];
      notice.discrepancies.push({
        discrepancy_type: condition === 'Damaged' ? 'Damaged Product' : 'Quality Issue',
        item_code: itemCode,
        client_sku: clientSku,
        expected_qty: qty,
        actual_qty: qty,
        variance_qty: 0,
        status: 'Open',
        auto_generated: 0,
        source_stock_entry: entryName,
        container_code: containerCode,
        notes: notes || condition + ' recorded from scanner-first receiving page.'
      });
    }
    var hasVariance = (notice.items || []).some(function (row) { return Number(row.variance_qty || 0) !== 0; });
    notice.status = (hasVariance || !matched || condition !== 'OK') ? 'Discrepancy Review' : 'Received';
    return saveDoc(notice).then(function () {
      return insertDoc({
        doctype: 'Three PL Container Movement',
        movement_datetime: frappe.datetime.now_datetime(),
        container_code: containerCode,
        client: notice.customer,
        movement_type: 'Received',
        to_warehouse: byId('receiving-location').value.trim(),
        reference_doctype: 'Stock Entry',
        reference_name: entryName,
        notes: 'Created from scanner-first receiving page. Condition: ' + condition + '. ' + (notes || '')
      });
    });
  }
  function submitReceiving() {
    if (frappe.session && frappe.session.user === 'Guest') {
      window.location.href = '/login?redirect-to=' + encodeURIComponent('/warehouse/receiving');
      return;
    }
    if (!requireWarehouseRole()) return;
    var noticeReference = (byId('receiving-notice').value || '').trim();
    var containerCode = (byId('receiving-container').value || '').trim();
    var itemCode = (byId('receiving-item').value || '').trim();
    var qty = Number((byId('receiving-qty').value || '').trim());
    var location = (byId('receiving-location').value || '').trim();
    var condition = byId('receiving-condition').value || 'OK';
    var notes = (byId('receiving-notes').value || '').trim();
    if (!noticeReference || !containerCode || !itemCode || !qty || !location) {
      setStatus('Scan ASN, container, item, qty, and receiving location first.', true);
      return;
    }
    setStatus('Submitting receipt...', false);
    var notice;
    var itemUom;
    var clientSku;
    findNotice(noticeReference).then(function (foundNotice) {
      notice = foundNotice;
      var noticeRow = (notice.items || []).find(function (row) { return row.item_code === itemCode; });
      return getValue('Item', { name: itemCode }, ['name', 'stock_uom', 'client_sku', 'owner_client']).then(function (itemResponse) {
        if (!itemResponse.message || !itemResponse.message.name) throw new Error('Item not found.');
        if (itemResponse.message.owner_client && itemResponse.message.owner_client !== notice.customer) throw new Error('Item belongs to another client.');
        itemUom = noticeRow ? noticeRow.uom : (itemResponse.message.stock_uom || 'Nos');
        clientSku = noticeRow ? noticeRow.client_sku : (itemResponse.message.client_sku || '');
        return getValue('Warehouse', { name: location }, 'name');
      });
    }).then(function (warehouseResponse) {
      if (!warehouseResponse.message || !warehouseResponse.message.name) throw new Error('Receiving location not found.');
      return ensureContainer(containerCode, notice, location);
    }).then(function () {
      return createAndSubmitStockEntry(notice, containerCode, itemCode, qty, itemUom, location);
    }).then(function (entryResponse) {
      var entry = entryResponse.message;
      return updateContainerItems(containerCode, itemCode, clientSku, qty, itemUom, condition, notes).then(function () {
        return syncNoticeRow(notice, itemCode, clientSku, qty, itemUom, containerCode, entry.name, condition, notes).then(function () {
          return entry;
        });
      });
    }).then(function (entry) {
      setStatus('Receipt submitted: ' + entry.name + '.', false);
      byId('receiving-item').value = '';
      byId('receiving-qty').value = '';
      byId('receiving-notes').value = '';
      byId('receiving-condition').value = 'OK';
      byId('receiving-item').focus();
    }).catch(function (error) {
      setStatus(error.message || 'Could not submit receipt.', true);
    });
  }
  frappe.ready(function () {
    if (frappe.session && frappe.session.user === 'Guest') {
      window.location.href = '/login?redirect-to=' + encodeURIComponent('/warehouse/receiving');
      return;
    }
    requireWarehouseRole();
    var button = byId('submit-receiving');
    if (button) button.addEventListener('click', submitReceiving);
    ['receiving-notice', 'receiving-container', 'receiving-item', 'receiving-qty', 'receiving-location', 'receiving-condition', 'receiving-notes'].forEach(function (id, index, fields) {
      var input = byId(id);
      if (input) input.addEventListener('keydown', function (event) {
        if (event.key === 'Enter') {
          event.preventDefault();
          if (index < fields.length - 1) byId(fields[index + 1]).focus();
          else submitReceiving();
        }
      });
    });
  });
})();
""".strip()

    existing_receiving_page = frappe.db.get_value("Web Page", {"route": "warehouse/receiving"}, "name")
    if existing_receiving_page:
        receiving_page = frappe.get_doc("Web Page", existing_receiving_page)
    else:
        receiving_page = frappe.new_doc("Web Page")
        receiving_page.name = "warehouse/receiving"

    receiving_page.title = "Receiving Scan"
    receiving_page.route = "warehouse/receiving"
    receiving_page.published = 1
    if receiving_page.meta.has_field("login_required"):
        receiving_page.login_required = 1
    receiving_page.content_type = "HTML"
    receiving_page.main_section = receiving_html
    if receiving_page.meta.has_field("main_section_html"):
        receiving_page.main_section_html = receiving_html
    receiving_page.javascript = receiving_script
    receiving_page.insert_code = 0
    receiving_page.show_sidebar = 0
    receiving_page.save(ignore_permissions=True)

    correction_html = """
<section class="container py-4" style="max-width: 820px;">
  <h1 class="h3 mb-3">Warehouse Correction</h1>
  <div class="row g-3">
    <div class="col-md-5">
      <label class="form-label" for="correction-container">Container / HU</label>
      <input class="form-control" id="correction-container" autocomplete="off" autofocus>
    </div>
    <div class="col-md-4">
      <label class="form-label" for="correction-item">Item / SKU</label>
      <input class="form-control" id="correction-item" autocomplete="off">
    </div>
    <div class="col-md-3">
      <label class="form-label" for="correction-actual-qty">Actual Qty</label>
      <input class="form-control" id="correction-actual-qty" inputmode="decimal" autocomplete="off">
    </div>
    <div class="col-md-5">
      <label class="form-label" for="correction-type">Correction Type</label>
      <select class="form-select" id="correction-type">
        <option value="Quantity Count">Quantity Count</option>
        <option value="Unexpected Product">Unexpected Product</option>
        <option value="Damaged Product">Damaged Product</option>
        <option value="Quality Issue">Quality Issue</option>
        <option value="Hold For Review">Hold For Review</option>
      </select>
    </div>
    <div class="col-md-4">
      <label class="form-label" for="correction-condition">Condition</label>
      <select class="form-select" id="correction-condition">
        <option value="OK">OK</option>
        <option value="Damaged">Damaged</option>
        <option value="Quality Issue">Quality Issue</option>
        <option value="Hold">Hold</option>
      </select>
    </div>
    <div class="col-md-3">
      <label class="form-label" for="correction-uom">UOM</label>
      <input class="form-control" id="correction-uom" autocomplete="off" value="Nos">
    </div>
    <div class="col-12">
      <label class="form-label" for="correction-notes">Notes</label>
      <textarea class="form-control" id="correction-notes" rows="2"></textarea>
    </div>
  </div>
  <div class="d-flex gap-2 align-items-center mt-3">
    <button class="btn btn-primary" id="apply-correction" type="button">Apply Correction</button>
    <span class="text-muted small" id="correction-status"></span>
  </div>
</section>
""".strip()
    correction_script = """
(function () {
  function byId(id) { return document.getElementById(id); }
  function setStatus(message, isError) {
    var target = byId('correction-status');
    if (!target) return;
    target.textContent = message || '';
    target.className = isError ? 'text-danger small' : 'text-muted small';
  }
  function getCsrfToken() {
    if (frappe.csrf_token && frappe.csrf_token !== 'None') return Promise.resolve(frappe.csrf_token);
    if (window.__threePlCsrfTokenPromise) return window.__threePlCsrfTokenPromise;
    window.__threePlCsrfTokenPromise = fetch('/app', { credentials: 'same-origin' })
      .then(function (response) { return response.text(); })
      .then(function (html) {
        var match = html.match(/frappe\\.csrf_token\\s*=\\s*"([^"]+)"/);
        if (!match || !match[1] || match[1] === 'None') throw new Error('Could not initialize session token. Please refresh and try again.');
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
          if (!response.ok) throw new Error(parseServerMessage(payload) || ('Request failed: ' + response.status));
          return payload;
        });
      });
    });
  }
  function hasWarehouseRole() {
    var roles = (frappe.user_roles || []);
    return roles.indexOf('3PL Warehouse User') !== -1 || roles.indexOf('3PL Warehouse Manager') !== -1 || roles.indexOf('System Manager') !== -1;
  }
  function requireWarehouseRole() {
    if (frappe.user_roles && !hasWarehouseRole()) {
      setStatus('This scanner page is only available to warehouse users.', true);
      var button = byId('apply-correction');
      if (button) button.disabled = true;
      return false;
    }
    return true;
  }
  function getDoc(doctype, name) {
    return api('frappe.client.get', { doctype: doctype, name: name });
  }
  function getValue(doctype, filters, fieldname) {
    return api('frappe.client.get_value', { doctype: doctype, filters: filters, fieldname: fieldname });
  }
  function insertDoc(doc) {
    return api('frappe.client.insert', { doc: doc });
  }
  function saveDoc(doc) {
    return api('frappe.client.save', { doc: doc });
  }
  function setValue(doctype, name, fieldname, value) {
    return api('frappe.client.set_value', { doctype: doctype, name: name, fieldname: fieldname, value: value });
  }
  function setValues(doctype, name, values) {
    return Object.keys(values).reduce(function (promise, fieldname) {
      return promise.then(function () { return setValue(doctype, name, fieldname, values[fieldname]); });
    }, Promise.resolve());
  }
  function updateContainer(container, itemCode, actualQty, uom, condition, notes) {
    var expectedQty = 0;
    var matched = false;
    container.items = container.items || [];
    container.items.forEach(function (row) {
      if (row.item_code === itemCode && (row.uom || uom) === uom) {
        expectedQty = Number(row.qty || 0);
        row.qty = actualQty;
        row.condition_status = condition;
        row.notes = notes || row.notes;
        matched = true;
      }
    });
    if (!matched) {
      container.items.push({
        item_code: itemCode,
        qty: actualQty,
        uom: uom,
        condition_status: condition,
        notes: notes || 'Added by warehouse correction.'
      });
    }
    if (condition !== 'OK') {
      container.status = 'In Verification';
    }
    container.last_moved_at = frappe.datetime.now_datetime();
    return saveDoc(container).then(function () {
      return { expectedQty: expectedQty, delta: actualQty - expectedQty };
    });
  }
  function applyCorrection() {
    if (frappe.session && frappe.session.user === 'Guest') {
      window.location.href = '/login?redirect-to=' + encodeURIComponent('/warehouse/correction');
      return;
    }
    if (!requireWarehouseRole()) return;
    var containerCode = (byId('correction-container').value || '').trim();
    var itemCode = (byId('correction-item').value || '').trim();
    var actualQty = Number((byId('correction-actual-qty').value || '').trim());
    var correctionType = byId('correction-type').value;
    var condition = byId('correction-condition').value;
    var uom = (byId('correction-uom').value || '').trim() || 'Nos';
    var notes = (byId('correction-notes').value || '').trim();
    if (!containerCode || !itemCode || Number.isNaN(actualQty) || actualQty < 0) {
      setStatus('Scan container, item, and a non-negative actual quantity first.', true);
      return;
    }
    setStatus('Applying correction...', false);
    var container;
    var result;
    var correction;
    getDoc('Three PL Container', containerCode).then(function (response) {
      container = response.message;
      if (!container || !container.name) throw new Error('Container not found.');
      if (['Shipped', 'Closed', 'Replaced'].indexOf(container.status) !== -1) throw new Error('Container cannot be corrected from status ' + container.status + '.');
      return getValue('Item', { name: itemCode }, ['name', 'client_sku']);
    }).then(function (itemResponse) {
      if (!itemResponse.message || !itemResponse.message.name) throw new Error('Item not found.');
      return updateContainer(container, itemCode, actualQty, uom, condition, notes);
    }).then(function (updateResult) {
      result = updateResult;
      return insertDoc({
        doctype: 'Three PL Warehouse Correction',
        operation_reference: 'CORR-' + containerCode + '-' + itemCode + '-' + Date.now(),
        operation_datetime: frappe.datetime.now_datetime(),
        status: 'Draft',
        correction_type: correctionType,
        client: container.client,
        container_code: container.name,
        warehouse: container.current_warehouse,
        item_code: itemCode,
        uom: uom,
        expected_qty: result.expectedQty,
        actual_qty: actualQty,
        qty_delta: result.delta,
        condition_status: condition,
        notes: notes || 'Created from scanner-first warehouse correction page.'
      });
    }).then(function (correctionResponse) {
      correction = correctionResponse.message;
      return insertDoc({
        doctype: 'Three PL Container Movement',
        movement_datetime: frappe.datetime.now_datetime(),
        container_code: container.name,
        client: container.client,
        movement_type: 'Adjusted',
        from_warehouse: container.current_warehouse,
        to_warehouse: container.current_warehouse,
        reference_doctype: 'Three PL Warehouse Correction',
        reference_name: correction.name,
        notes: correctionType + ': delta ' + result.delta + '. ' + (notes || '')
      });
    }).then(function (movementResponse) {
      var movement = movementResponse.message;
      return setValues('Three PL Warehouse Correction', correction.name, {
        status: 'Applied',
        movement: movement.name
      }).then(function () {
        return movement;
      });
    }).then(function (movement) {
      setStatus('Correction applied: ' + correction.name + ' / ' + movement.name + '.', false);
      byId('correction-item').value = '';
      byId('correction-actual-qty').value = '';
      byId('correction-notes').value = '';
      byId('correction-item').focus();
    }).catch(function (error) {
      setStatus(error.message || 'Could not apply correction.', true);
    });
  }
  frappe.ready(function () {
    if (frappe.session && frappe.session.user === 'Guest') {
      window.location.href = '/login?redirect-to=' + encodeURIComponent('/warehouse/correction');
      return;
    }
    requireWarehouseRole();
    var button = byId('apply-correction');
    if (button) button.addEventListener('click', applyCorrection);
    ['correction-container', 'correction-item', 'correction-actual-qty', 'correction-uom'].forEach(function (id, index, fields) {
      var input = byId(id);
      if (input) input.addEventListener('keydown', function (event) {
        if (event.key === 'Enter') {
          event.preventDefault();
          if (index < fields.length - 1) byId(fields[index + 1]).focus();
          else applyCorrection();
        }
      });
    });
  });
})();
""".strip()

    existing_correction_page = frappe.db.get_value("Web Page", {"route": "warehouse/correction"}, "name")
    if existing_correction_page:
        correction_page = frappe.get_doc("Web Page", existing_correction_page)
    else:
        correction_page = frappe.new_doc("Web Page")
        correction_page.name = "warehouse/correction"

    correction_page.title = "Warehouse Correction"
    correction_page.route = "warehouse/correction"
    correction_page.published = 1
    if correction_page.meta.has_field("login_required"):
        correction_page.login_required = 1
    correction_page.content_type = "HTML"
    correction_page.main_section = correction_html
    if correction_page.meta.has_field("main_section_html"):
        correction_page.main_section_html = correction_html
    correction_page.javascript = correction_script
    correction_page.insert_code = 0
    correction_page.show_sidebar = 0
    correction_page.save(ignore_permissions=True)

    stocktake_html = """
<section class="container py-4" style="max-width: 820px;">
  <h1 class="h3 mb-3">Stocktake</h1>
  <div class="row g-3">
    <div class="col-md-5">
      <label class="form-label" for="stocktake-session">Session Ref</label>
      <input class="form-control" id="stocktake-session" autocomplete="off" placeholder="e.g. COUNT-AISLE-A">
    </div>
    <div class="col-md-7">
      <label class="form-label" for="stocktake-session-notes">Session Notes</label>
      <input class="form-control" id="stocktake-session-notes" autocomplete="off">
    </div>
    <div class="col-md-5">
      <label class="form-label" for="stocktake-container">Container / HU</label>
      <input class="form-control" id="stocktake-container" autocomplete="off" autofocus>
    </div>
    <div class="col-md-4">
      <label class="form-label" for="stocktake-item">Item / SKU</label>
      <input class="form-control" id="stocktake-item" autocomplete="off">
    </div>
    <div class="col-md-3">
      <label class="form-label" for="stocktake-counted-qty">Counted Qty</label>
      <input class="form-control" id="stocktake-counted-qty" inputmode="decimal" autocomplete="off">
    </div>
    <div class="col-md-4">
      <label class="form-label" for="stocktake-condition">Condition</label>
      <select class="form-select" id="stocktake-condition">
        <option value="OK">OK</option>
        <option value="Damaged">Damaged</option>
        <option value="Quality Issue">Quality Issue</option>
        <option value="Hold">Hold</option>
      </select>
    </div>
    <div class="col-md-3">
      <label class="form-label" for="stocktake-uom">UOM</label>
      <input class="form-control" id="stocktake-uom" autocomplete="off" value="Nos">
    </div>
    <div class="col-md-5">
      <label class="form-label" for="stocktake-notes">Notes</label>
      <input class="form-control" id="stocktake-notes" autocomplete="off">
    </div>
  </div>
  <div class="d-flex gap-2 align-items-center mt-3">
    <button class="btn btn-primary" id="apply-stocktake" type="button">Apply Stocktake</button>
    <button class="btn btn-outline-secondary" id="complete-stocktake-session" type="button">Complete Session</button>
    <span class="text-muted small" id="stocktake-status"></span>
  </div>
</section>
""".strip()
    stocktake_script = """
(function () {
  function byId(id) { return document.getElementById(id); }
  function setStatus(message, isError) {
    var target = byId('stocktake-status');
    if (!target) return;
    target.textContent = message || '';
    target.className = isError ? 'text-danger small' : 'text-muted small';
  }
  function getCsrfToken() {
    if (frappe.csrf_token && frappe.csrf_token !== 'None') return Promise.resolve(frappe.csrf_token);
    if (window.__threePlCsrfTokenPromise) return window.__threePlCsrfTokenPromise;
    window.__threePlCsrfTokenPromise = fetch('/app', { credentials: 'same-origin' })
      .then(function (response) { return response.text(); })
      .then(function (html) {
        var match = html.match(/frappe\\.csrf_token\\s*=\\s*"([^"]+)"/);
        if (!match || !match[1] || match[1] === 'None') throw new Error('Could not initialize session token. Please refresh and try again.');
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
          if (!response.ok) throw new Error(parseServerMessage(payload) || ('Request failed: ' + response.status));
          return payload;
        });
      });
    });
  }
  function hasWarehouseRole() {
    var roles = (frappe.user_roles || []);
    return roles.indexOf('3PL Warehouse User') !== -1 || roles.indexOf('3PL Warehouse Manager') !== -1 || roles.indexOf('System Manager') !== -1;
  }
  function requireWarehouseRole() {
    if (frappe.user_roles && !hasWarehouseRole()) {
      setStatus('This scanner page is only available to warehouse users.', true);
      var button = byId('apply-stocktake');
      if (button) button.disabled = true;
      return false;
    }
    return true;
  }
  function getDoc(doctype, name) {
    return api('frappe.client.get', { doctype: doctype, name: name });
  }
  function insertDoc(doc) {
    return api('frappe.client.insert', { doc: doc });
  }
  function getList(doctype, filters, fields, limit) {
    return api('frappe.client.get_list', {
      doctype: doctype,
      filters: filters || {},
      fields: fields || ['name'],
      limit_page_length: limit || 1
    });
  }
  function saveDoc(doc) {
    return api('frappe.client.save', { doc: doc });
  }
  function setValue(doctype, name, fieldname, value) {
    return api('frappe.client.set_value', { doctype: doctype, name: name, fieldname: fieldname, value: value });
  }
  function setValues(doctype, name, values) {
    return Object.keys(values).reduce(function (promise, fieldname) {
      return promise.then(function () { return setValue(doctype, name, fieldname, values[fieldname]); });
    }, Promise.resolve());
  }
  function ensureSession(reference, container, notes) {
    if (!reference) return Promise.resolve(null);
    return getList('Three PL Stocktake Session', { session_reference: reference }, ['name', 'status'], 1).then(function (response) {
      var rows = response.message || [];
      if (rows.length) {
        if (rows[0].status === 'Completed' || rows[0].status === 'Cancelled') {
          throw new Error('Stocktake session is not open: ' + rows[0].status + '.');
        }
        return rows[0].name;
      }
      return insertDoc({
        doctype: 'Three PL Stocktake Session',
        session_reference: reference,
        status: 'In Progress',
        client: container.client,
        warehouse: container.current_warehouse,
        started_at: frappe.datetime.now_datetime(),
        notes: notes || ''
      }).then(function (sessionResponse) {
        return sessionResponse.message.name;
      });
    });
  }
  function completeSession() {
    if (frappe.session && frappe.session.user === 'Guest') {
      window.location.href = '/login?redirect-to=' + encodeURIComponent('/warehouse/stocktake');
      return;
    }
    if (!requireWarehouseRole()) return;
    var reference = (byId('stocktake-session').value || '').trim();
    if (!reference) {
      setStatus('Enter a stocktake session reference first.', true);
      return;
    }
    setStatus('Completing session...', false);
    getList('Three PL Stocktake Session', { session_reference: reference }, ['name'], 1).then(function (response) {
      var rows = response.message || [];
      if (!rows.length) throw new Error('Stocktake session not found.');
      return setValues('Three PL Stocktake Session', rows[0].name, {
        status: 'Completed',
        completed_at: frappe.datetime.now_datetime()
      });
    }).then(function () {
      setStatus('Stocktake session completed.', false);
    }).catch(function (error) {
      setStatus(error.message || 'Could not complete stocktake session.', true);
    });
  }
  function findItemRow(container, itemCode, uom) {
    return (container.items || []).find(function (row) {
      return row.item_code === itemCode && (row.uom || uom) === uom;
    });
  }
  function updateContainer(container, itemCode, countedQty, uom, condition, notes) {
    var row = findItemRow(container, itemCode, uom);
    var expectedQty = row ? Number(row.qty || 0) : 0;
    if (row) {
      row.qty = countedQty;
      row.condition_status = condition;
      row.notes = notes || row.notes;
    } else {
      container.items = container.items || [];
      container.items.push({
        item_code: itemCode,
        qty: countedQty,
        uom: uom,
        condition_status: condition,
        notes: notes || 'Added by stocktake.'
      });
    }
    if (condition !== 'OK') container.status = 'In Verification';
    container.last_moved_at = frappe.datetime.now_datetime();
    return saveDoc(container).then(function () {
      return { expectedQty: expectedQty, delta: countedQty - expectedQty };
    });
  }
  function applyStocktake() {
    if (frappe.session && frappe.session.user === 'Guest') {
      window.location.href = '/login?redirect-to=' + encodeURIComponent('/warehouse/stocktake');
      return;
    }
    if (!requireWarehouseRole()) return;
    var containerCode = (byId('stocktake-container').value || '').trim();
    var itemCode = (byId('stocktake-item').value || '').trim();
    var countedQty = Number((byId('stocktake-counted-qty').value || '').trim());
    var condition = byId('stocktake-condition').value;
    var uom = (byId('stocktake-uom').value || '').trim() || 'Nos';
    var notes = (byId('stocktake-notes').value || '').trim();
    var sessionReference = (byId('stocktake-session').value || '').trim();
    var sessionNotes = (byId('stocktake-session-notes').value || '').trim();
    var sessionName = null;
    if (!containerCode || !itemCode || Number.isNaN(countedQty) || countedQty < 0) {
      setStatus('Scan container, item, and a non-negative counted quantity first.', true);
      return;
    }
    setStatus('Applying stocktake...', false);
    var container;
    var result;
    var stocktake;
    var correction = null;
    var movement = null;
    getDoc('Three PL Container', containerCode).then(function (response) {
      container = response.message;
      if (!container || !container.name) throw new Error('Container not found.');
      if (['Shipped', 'Closed', 'Replaced'].indexOf(container.status) !== -1) throw new Error('Container cannot be counted from status ' + container.status + '.');
      return ensureSession(sessionReference, container, sessionNotes);
    }).then(function (createdSessionName) {
      sessionName = createdSessionName;
      return updateContainer(container, itemCode, countedQty, uom, condition, notes);
    }).then(function (updateResult) {
      result = updateResult;
      var needsCorrection = result.delta !== 0 || condition !== 'OK';
      return insertDoc({
        doctype: 'Three PL Stocktake',
        operation_reference: 'STOCKTAKE-' + containerCode + '-' + itemCode + '-' + Date.now(),
        operation_datetime: frappe.datetime.now_datetime(),
        status: needsCorrection ? 'Draft' : 'No Difference',
        stocktake_session: sessionName,
        client: container.client,
        warehouse: container.current_warehouse,
        container_code: container.name,
        item_code: itemCode,
        uom: uom,
        expected_qty: result.expectedQty,
        counted_qty: countedQty,
        qty_delta: result.delta,
        condition_status: condition,
        notes: notes || 'Created from scanner-first stocktake page.'
      });
    }).then(function (stocktakeResponse) {
      stocktake = stocktakeResponse.message;
      if (result.delta === 0 && condition === 'OK') return null;
      return insertDoc({
        doctype: 'Three PL Warehouse Correction',
        operation_reference: 'CORR-STOCKTAKE-' + containerCode + '-' + itemCode + '-' + Date.now(),
        operation_datetime: frappe.datetime.now_datetime(),
        status: 'Draft',
        correction_type: 'Quantity Count',
        client: container.client,
        container_code: container.name,
        warehouse: container.current_warehouse,
        item_code: itemCode,
        uom: uom,
        expected_qty: result.expectedQty,
        actual_qty: countedQty,
        qty_delta: result.delta,
        condition_status: condition,
        source_doctype: 'Three PL Stocktake',
        source_name: stocktake.name,
        notes: notes || 'Created from scanner-first stocktake page.'
      }).then(function (correctionResponse) {
        correction = correctionResponse.message;
        return insertDoc({
          doctype: 'Three PL Container Movement',
          movement_datetime: frappe.datetime.now_datetime(),
          container_code: container.name,
          client: container.client,
          movement_type: 'Adjusted',
          from_warehouse: container.current_warehouse,
          to_warehouse: container.current_warehouse,
          reference_doctype: 'Three PL Stocktake',
          reference_name: stocktake.name,
          notes: 'Stocktake delta ' + result.delta + '. ' + (notes || '')
        });
      }).then(function (movementResponse) {
        movement = movementResponse.message;
        return setValues('Three PL Warehouse Correction', correction.name, {
          status: 'Applied',
          movement: movement.name
        });
      }).then(function () {
        return setValues('Three PL Stocktake', stocktake.name, {
          status: 'Applied',
          correction: correction.name,
          movement: movement.name
        });
      });
    }).then(function () {
      setStatus('Stocktake saved: ' + stocktake.name + (correction ? ' / ' + correction.name : ' / no difference') + '.', false);
      byId('stocktake-item').value = '';
      byId('stocktake-counted-qty').value = '';
      byId('stocktake-notes').value = '';
      byId('stocktake-item').focus();
    }).catch(function (error) {
      setStatus(error.message || 'Could not apply stocktake.', true);
    });
  }
  frappe.ready(function () {
    if (frappe.session && frappe.session.user === 'Guest') {
      window.location.href = '/login?redirect-to=' + encodeURIComponent('/warehouse/stocktake');
      return;
    }
    requireWarehouseRole();
    var button = byId('apply-stocktake');
    if (button) button.addEventListener('click', applyStocktake);
    var complete = byId('complete-stocktake-session');
    if (complete) complete.addEventListener('click', completeSession);
    ['stocktake-session', 'stocktake-container', 'stocktake-item', 'stocktake-counted-qty', 'stocktake-uom'].forEach(function (id, index, fields) {
      var input = byId(id);
      if (input) input.addEventListener('keydown', function (event) {
        if (event.key === 'Enter') {
          event.preventDefault();
          if (index < fields.length - 1) byId(fields[index + 1]).focus();
          else applyStocktake();
        }
      });
    });
  });
})();
""".strip()

    existing_stocktake_page = frappe.db.get_value("Web Page", {"route": "warehouse/stocktake"}, "name")
    if existing_stocktake_page:
        stocktake_page = frappe.get_doc("Web Page", existing_stocktake_page)
    else:
        stocktake_page = frappe.new_doc("Web Page")
        stocktake_page.name = "warehouse/stocktake"

    stocktake_page.title = "Stocktake"
    stocktake_page.route = "warehouse/stocktake"
    stocktake_page.published = 1
    if stocktake_page.meta.has_field("login_required"):
        stocktake_page.login_required = 1
    stocktake_page.content_type = "HTML"
    stocktake_page.main_section = stocktake_html
    if stocktake_page.meta.has_field("main_section_html"):
        stocktake_page.main_section_html = stocktake_html
    stocktake_page.javascript = stocktake_script
    stocktake_page.insert_code = 0
    stocktake_page.show_sidebar = 0
    stocktake_page.save(ignore_permissions=True)

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

    putaway_html = """
<section class="container py-4" style="max-width: 760px;">
  <h1 class="h3 mb-3">Putaway</h1>
  <div class="mb-3">
    <label class="form-label" for="putaway-container-code">Container / HU</label>
    <input class="form-control" id="putaway-container-code" autocomplete="off" autofocus>
  </div>
  <div class="mb-3">
    <label class="form-label" for="putaway-target-location">Storage Location</label>
    <input class="form-control" id="putaway-target-location" autocomplete="off">
  </div>
  <div class="d-flex gap-2 align-items-center">
    <button class="btn btn-primary" id="apply-putaway" type="button">Apply Putaway</button>
    <span class="text-muted small" id="putaway-status"></span>
  </div>
</section>
""".strip()
    putaway_script = """
(function () {
  var ALLOWED_SOURCE_STATUSES = ['Received', 'In Verification', 'Ready for Putaway'];

  function byId(id) { return document.getElementById(id); }
  function setStatus(message, isError) {
    var target = byId('putaway-status');
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
  function hasWarehouseRole() {
    var roles = (frappe.user_roles || []);
    return roles.indexOf('3PL Warehouse User') !== -1 || roles.indexOf('3PL Warehouse Manager') !== -1 || roles.indexOf('System Manager') !== -1;
  }
  function requireWarehouseRole() {
    if (frappe.user_roles && !hasWarehouseRole()) {
      setStatus('This scanner page is only available to warehouse users.', true);
      var button = byId('apply-putaway');
      if (button) button.disabled = true;
      return false;
    }
    return true;
  }
  function getValue(doctype, filters, fieldname) {
    return api('frappe.client.get_value', { doctype: doctype, filters: filters, fieldname: fieldname });
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
  function createMove(containerCode, container, targetLocation) {
    return insertDoc({
      doctype: 'Three PL Container Move',
      operation_reference: 'PUTAWAY-' + containerCode + '-' + Date.now(),
      operation_datetime: frappe.datetime.now_datetime(),
      status: 'Draft',
      container_code: containerCode,
      client: container.client,
      from_warehouse: container.current_warehouse,
      to_warehouse: targetLocation,
      notes: 'Created from scanner-first putaway page.'
    });
  }
  function applyMove(moveDoc) {
    var movementTime = frappe.datetime.now_datetime();
    return insertDoc({
      doctype: 'Three PL Container Movement',
      movement_datetime: movementTime,
      container_code: moveDoc.container_code,
      client: moveDoc.client,
      movement_type: 'Putaway',
      from_warehouse: moveDoc.from_warehouse,
      to_warehouse: moveDoc.to_warehouse,
      reference_doctype: 'Three PL Container Move',
      reference_name: moveDoc.name,
      notes: 'Applied immediately from scanner-first putaway page.'
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
  function applyPutaway() {
    if (frappe.session && frappe.session.user === 'Guest') {
      window.location.href = '/login?redirect-to=' + encodeURIComponent('/warehouse/putaway');
      return;
    }
    if (!requireWarehouseRole()) return;
    var containerCode = (byId('putaway-container-code').value || '').trim();
    var targetLocation = (byId('putaway-target-location').value || '').trim();
    if (!containerCode || !targetLocation) {
      setStatus('Scan container and storage location first.', true);
      return;
    }
    setStatus('Applying putaway...', false);
    getValue('Three PL Container', { name: containerCode }, ['client', 'current_warehouse', 'status']).then(function (containerResponse) {
      var container = containerResponse.message;
      if (!container || !container.client) throw new Error('Container not found.');
      if (ALLOWED_SOURCE_STATUSES.indexOf(container.status) === -1) {
        throw new Error('Container is not ready for putaway. Current status: ' + (container.status || 'unknown') + '.');
      }
      if (container.current_warehouse === targetLocation) throw new Error('Storage location is already current location.');
      return getValue('Warehouse', { name: targetLocation }, 'name').then(function (warehouseResponse) {
        if (!warehouseResponse.message || !warehouseResponse.message.name) throw new Error('Storage location not found.');
        return createMove(containerCode, container, targetLocation);
      });
    }).then(function (insertResponse) {
      var move = insertResponse.message;
      return applyMove(move).then(function (movement) {
        return { move: move, movement: movement };
      });
    }).then(function (result) {
      setStatus('Putaway applied: ' + result.move.name + ' / ' + result.movement.name + '.', false);
      byId('putaway-container-code').value = '';
      byId('putaway-target-location').value = '';
      byId('putaway-container-code').focus();
    }).catch(function (error) {
      setStatus(error.message || 'Could not apply putaway.', true);
    });
  }
  frappe.ready(function () {
    if (frappe.session && frappe.session.user === 'Guest') {
      window.location.href = '/login?redirect-to=' + encodeURIComponent('/warehouse/putaway');
      return;
    }
    requireWarehouseRole();
    var button = byId('apply-putaway');
    if (button) button.addEventListener('click', applyPutaway);
    ['putaway-container-code', 'putaway-target-location'].forEach(function (id) {
      var input = byId(id);
      if (input) input.addEventListener('keydown', function (event) {
        if (event.key === 'Enter') {
          event.preventDefault();
          if (id === 'putaway-container-code') byId('putaway-target-location').focus();
          else applyPutaway();
        }
      });
    });
  });
})();
""".strip()

    existing_putaway_page = frappe.db.get_value("Web Page", {"route": "warehouse/putaway"}, "name")
    if existing_putaway_page:
        putaway_page = frappe.get_doc("Web Page", existing_putaway_page)
    else:
        putaway_page = frappe.new_doc("Web Page")
        putaway_page.name = "warehouse/putaway"

    putaway_page.title = "Putaway"
    putaway_page.route = "warehouse/putaway"
    putaway_page.published = 1
    if putaway_page.meta.has_field("login_required"):
        putaway_page.login_required = 1
    putaway_page.content_type = "HTML"
    putaway_page.main_section = putaway_html
    if putaway_page.meta.has_field("main_section_html"):
        putaway_page.main_section_html = putaway_html
    putaway_page.javascript = putaway_script
    putaway_page.insert_code = 0
    putaway_page.show_sidebar = 0
    putaway_page.save(ignore_permissions=True)

    repack_html = """
<section class="container py-4" style="max-width: 820px;">
  <h1 class="h3 mb-3">Container Repack</h1>
  <div class="mb-3">
    <label class="form-label" for="repack-mode">Mode</label>
    <select class="form-select" id="repack-mode">
      <option value="Full Consolidation">Full Consolidation</option>
      <option value="Partial Split">Partial Split</option>
    </select>
  </div>
  <div class="mb-3">
    <label class="form-label" for="repack-source-container">Source Container / HU</label>
    <div class="d-flex gap-2">
      <input class="form-control" id="repack-source-container" autocomplete="off" autofocus>
      <button class="btn btn-outline-primary" id="add-repack-source" type="button">Add</button>
    </div>
  </div>
  <div class="mb-3">
    <div class="small text-muted mb-1">Scanned Sources</div>
    <ul class="list-group" id="repack-source-list"></ul>
  </div>
  <div class="row g-3">
    <div class="col-md-6">
      <label class="form-label" for="repack-target-container">Target Container / HU</label>
      <input class="form-control" id="repack-target-container" autocomplete="off">
    </div>
    <div class="col-md-6">
      <label class="form-label" for="repack-target-location">Target Location</label>
      <input class="form-control" id="repack-target-location" autocomplete="off">
    </div>
  </div>
  <div class="row g-3 mt-1" id="partial-repack-fields" style="display: none;">
    <div class="col-md-5">
      <label class="form-label" for="repack-item">Item / SKU To Move</label>
      <input class="form-control" id="repack-item" autocomplete="off">
    </div>
    <div class="col-md-3">
      <label class="form-label" for="repack-qty">Qty To Move</label>
      <input class="form-control" id="repack-qty" inputmode="decimal" autocomplete="off">
    </div>
    <div class="col-md-4">
      <label class="form-label" for="repack-uom">UOM</label>
      <input class="form-control" id="repack-uom" autocomplete="off" value="Nos">
    </div>
  </div>
  <div class="d-flex gap-2 align-items-center mt-3">
    <button class="btn btn-primary" id="apply-repack" type="button">Apply Repack</button>
    <span class="text-muted small" id="repack-status"></span>
  </div>
</section>
""".strip()
    repack_script = """
(function () {
  var sourceContainers = [];
  var BLOCKED_SOURCE_STATUSES = ['Shipped', 'Closed', 'Replaced'];

  function byId(id) { return document.getElementById(id); }
  function setStatus(message, isError) {
    var target = byId('repack-status');
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
  function hasWarehouseRole() {
    var roles = (frappe.user_roles || []);
    return roles.indexOf('3PL Warehouse User') !== -1 || roles.indexOf('3PL Warehouse Manager') !== -1 || roles.indexOf('System Manager') !== -1;
  }
  function requireWarehouseRole() {
    if (frappe.user_roles && !hasWarehouseRole()) {
      setStatus('This scanner page is only available to warehouse users.', true);
      var button = byId('apply-repack');
      if (button) button.disabled = true;
      return false;
    }
    return true;
  }
  function getDoc(doctype, name) {
    return api('frappe.client.get', { doctype: doctype, name: name });
  }
  function getValue(doctype, filters, fieldname) {
    return api('frappe.client.get_value', { doctype: doctype, filters: filters, fieldname: fieldname });
  }
  function insertDoc(doc) {
    return api('frappe.client.insert', { doc: doc });
  }
  function saveDoc(doc) {
    return api('frappe.client.save', { doc: doc });
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
  function renderSources() {
    var list = byId('repack-source-list');
    if (!list) return;
    list.innerHTML = '';
    sourceContainers.forEach(function (container) {
      var item = document.createElement('li');
      item.className = 'list-group-item d-flex justify-content-between align-items-center';
      item.innerHTML = '<span>' + container.name + ' - ' + (container.current_warehouse || 'no location') + '</span><span class="badge bg-secondary">' + (container.items || []).length + ' rows</span>';
      list.appendChild(item);
    });
  }
  function currentMode() {
    return byId('repack-mode').value || 'Full Consolidation';
  }
  function refreshModeFields() {
    var partial = currentMode() === 'Partial Split';
    var fields = byId('partial-repack-fields');
    if (fields) fields.style.display = partial ? '' : 'none';
  }
  function addSourceContainer() {
    if (frappe.session && frappe.session.user === 'Guest') {
      window.location.href = '/login?redirect-to=' + encodeURIComponent('/warehouse/repack');
      return;
    }
    if (!requireWarehouseRole()) return;
    var code = (byId('repack-source-container').value || '').trim();
    if (!code) {
      setStatus('Scan a source container first.', true);
      return;
    }
    if (sourceContainers.some(function (container) { return container.name === code; })) {
      setStatus('Source container already added.', true);
      return;
    }
    setStatus('Loading source container...', false);
    getDoc('Three PL Container', code).then(function (response) {
      var container = response.message;
      if (!container || !container.name) throw new Error('Source container not found.');
      if (BLOCKED_SOURCE_STATUSES.indexOf(container.status) !== -1) {
        throw new Error('Source container cannot be repacked from status ' + container.status + '.');
      }
      if (!container.items || !container.items.length) throw new Error('Source container has no item rows.');
      if (sourceContainers.length && sourceContainers[0].client !== container.client) {
        throw new Error('All source containers must belong to the same client.');
      }
      sourceContainers.push(container);
      byId('repack-source-container').value = '';
      renderSources();
      setStatus('Source added: ' + container.name + '.', false);
      byId('repack-source-container').focus();
    }).catch(function (error) {
      setStatus(error.message || 'Could not add source container.', true);
    });
  }
  function aggregateItems() {
    var byKey = {};
    sourceContainers.forEach(function (container) {
      (container.items || []).forEach(function (row) {
        var condition = row.condition_status || 'OK';
        var key = [row.item_code, row.uom, condition].join('||');
        if (!byKey[key]) {
          byKey[key] = {
            item_code: row.item_code,
            client_sku: row.client_sku,
            qty: 0,
            uom: row.uom,
            condition_status: condition,
            notes: 'Aggregated by scanner-first repack page.'
          };
        }
        byKey[key].qty += Number(row.qty || 0);
      });
    });
    return Object.keys(byKey).map(function (key) { return byKey[key]; });
  }
  function partialSplitItems() {
    if (sourceContainers.length !== 1) throw new Error('Partial split requires exactly one source container.');
    var itemCode = (byId('repack-item').value || '').trim();
    var qty = Number((byId('repack-qty').value || '').trim());
    var uom = (byId('repack-uom').value || '').trim() || 'Nos';
    if (!itemCode || Number.isNaN(qty) || qty <= 0) throw new Error('Enter item and positive qty for partial split.');
    var source = sourceContainers[0];
    var sourceRow = (source.items || []).find(function (row) {
      return row.item_code === itemCode && (row.uom || uom) === uom && Number(row.qty || 0) >= qty;
    });
    if (!sourceRow) throw new Error('Source container does not have enough item quantity to split.');
    return [{
      item_code: sourceRow.item_code,
      client_sku: sourceRow.client_sku,
      qty: qty,
      uom: sourceRow.uom || uom,
      condition_status: sourceRow.condition_status || 'OK',
      notes: 'Moved by scanner-first partial split.'
    }];
  }
  function itemKey(row) {
    return [row.item_code, row.uom, row.condition_status || 'OK'].join('||');
  }
  function addItemsToTarget(target, items) {
    target.items = target.items || [];
    items.forEach(function (item) {
      var matched = false;
      target.items.forEach(function (row) {
        if (itemKey(row) === itemKey(item)) {
          row.qty = Number(row.qty || 0) + Number(item.qty || 0);
          matched = true;
        }
      });
      if (!matched) target.items.push(item);
    });
  }
  function subtractItemsFromSource(source, items) {
    items.forEach(function (item) {
      var remaining = Number(item.qty || 0);
      source.items = (source.items || []).reduce(function (kept, row) {
        if (itemKey(row) !== itemKey(item)) {
          kept.push(row);
          return kept;
        }
        var available = Number(row.qty || 0);
        var moved = Math.min(available, remaining);
        var left = available - moved;
        remaining -= moved;
        if (left > 0) {
          row.qty = left;
          kept.push(row);
        }
        return kept;
      }, []);
      if (remaining > 0) throw new Error('Source container changed while splitting item ' + item.item_code + '.');
    });
  }
  function ensureTargetContainer(targetCode, client, targetLocation, items, movementTime, mode) {
    return getValue('Three PL Container', { name: targetCode }, 'name').then(function (response) {
      if (!response.message || !response.message.name) {
        return insertDoc({
          doctype: 'Three PL Container',
          container_code: targetCode,
          barcode: targetCode,
          container_type: 'Box',
          client: client,
          current_warehouse: targetLocation,
          status: 'Stored',
          last_moved_at: movementTime,
          items: items
        }).then(function (insertResponse) {
          return insertResponse.message;
        });
      }
      return getDoc('Three PL Container', targetCode).then(function (targetResponse) {
        var target = targetResponse.message;
        if (target.client && target.client !== client) throw new Error('Target container belongs to another client.');
        if (BLOCKED_SOURCE_STATUSES.indexOf(target.status) !== -1) throw new Error('Target container cannot be reused from status ' + target.status + '.');
        target.barcode = target.barcode || targetCode;
        target.container_type = target.container_type || 'Box';
        target.client = client;
        target.current_warehouse = targetLocation;
        target.status = 'Stored';
        target.last_moved_at = movementTime;
        if (mode === 'Partial Split') addItemsToTarget(target, items);
        else target.items = items;
        return saveDoc(target).then(function (saveResponse) {
          return saveResponse.message || target;
        });
      });
    });
  }
  function applyRepack() {
    if (frappe.session && frappe.session.user === 'Guest') {
      window.location.href = '/login?redirect-to=' + encodeURIComponent('/warehouse/repack');
      return;
    }
    if (!requireWarehouseRole()) return;
    var targetCode = (byId('repack-target-container').value || '').trim();
    var targetLocation = (byId('repack-target-location').value || '').trim();
    var mode = currentMode();
    if (sourceContainers.length < 1 || !targetCode || !targetLocation) {
      setStatus('Scan sources, target container, and target location first.', true);
      return;
    }
    if (mode === 'Partial Split' && sourceContainers.length !== 1) {
      setStatus('Partial split supports exactly one source container.', true);
      return;
    }
    if (sourceContainers.some(function (container) { return container.name === targetCode; })) {
      setStatus('Target container cannot be one of the source containers.', true);
      return;
    }
    setStatus('Applying repack...', false);
    getValue('Warehouse', { name: targetLocation }, 'name').then(function (warehouseResponse) {
      if (!warehouseResponse.message || !warehouseResponse.message.name) throw new Error('Target location not found.');
      var movementTime = frappe.datetime.now_datetime();
      var client = sourceContainers[0].client;
      var items = mode === 'Partial Split' ? partialSplitItems() : aggregateItems();
      return ensureTargetContainer(targetCode, client, targetLocation, items, movementTime, mode).then(function () {
        return insertDoc({
          doctype: 'Three PL Container Repack',
          operation_reference: 'REPACK-' + targetCode + '-' + Date.now(),
          operation_datetime: movementTime,
          status: 'Draft',
          repack_mode: mode,
          client: client,
          target_container: targetCode,
          target_location: targetLocation,
          source_containers: sourceContainers.map(function (container) {
            return { source_container: container.name, source_location: container.current_warehouse };
          }),
          items: items,
          notes: 'Created from scanner-first repack page.'
        }).then(function (repackResponse) {
          var repack = repackResponse.message;
          return insertDoc({
            doctype: 'Three PL Container Movement',
            movement_datetime: movementTime,
            container_code: targetCode,
            client: client,
            movement_type: 'Repacked',
            to_warehouse: targetLocation,
            from_container: sourceContainers[0].name,
            to_container: targetCode,
            reference_doctype: 'Three PL Container Repack',
            reference_name: repack.name,
            notes: 'Applied immediately from scanner-first repack page.'
          }).then(function (movementResponse) {
            var movement = movementResponse.message;
            var sourceUpdate;
            if (mode === 'Partial Split') {
              var source = sourceContainers[0];
              subtractItemsFromSource(source, items);
              source.status = source.items && source.items.length ? 'Stored' : 'Empty';
              source.last_moved_at = movementTime;
              sourceUpdate = saveDoc(source);
            } else {
              sourceUpdate = sourceContainers.reduce(function (promise, container) {
                return promise.then(function () {
                  return setValues('Three PL Container', container.name, {
                    status: 'Replaced',
                    replaced_by: targetCode,
                    last_moved_at: movementTime
                  });
                });
              }, Promise.resolve());
            }
            return sourceUpdate.then(function () {
              return setValues('Three PL Container Repack', repack.name, {
                status: 'Applied',
                movement: movement.name
              });
            }).then(function () {
              return { repack: repack, movement: movement };
            });
          });
        });
      });
    }).then(function (result) {
      setStatus('Repack applied: ' + result.repack.name + ' / ' + result.movement.name + '.', false);
      sourceContainers = [];
      renderSources();
      byId('repack-source-container').value = '';
      byId('repack-target-container').value = '';
      byId('repack-target-location').value = '';
      byId('repack-item').value = '';
      byId('repack-qty').value = '';
      byId('repack-source-container').focus();
    }).catch(function (error) {
      setStatus(error.message || 'Could not apply repack.', true);
    });
  }
  frappe.ready(function () {
    if (frappe.session && frappe.session.user === 'Guest') {
      window.location.href = '/login?redirect-to=' + encodeURIComponent('/warehouse/repack');
      return;
    }
    requireWarehouseRole();
    refreshModeFields();
    var addButton = byId('add-repack-source');
    var applyButton = byId('apply-repack');
    var mode = byId('repack-mode');
    if (mode) mode.addEventListener('change', refreshModeFields);
    if (addButton) addButton.addEventListener('click', addSourceContainer);
    if (applyButton) applyButton.addEventListener('click', applyRepack);
    byId('repack-source-container').addEventListener('keydown', function (event) {
      if (event.key === 'Enter') {
        event.preventDefault();
        addSourceContainer();
      }
    });
    byId('repack-target-container').addEventListener('keydown', function (event) {
      if (event.key === 'Enter') {
        event.preventDefault();
        byId('repack-target-location').focus();
      }
    });
    byId('repack-target-location').addEventListener('keydown', function (event) {
      if (event.key === 'Enter') {
        event.preventDefault();
        applyRepack();
      }
    });
  });
})();
""".strip()

    existing_repack_page = frappe.db.get_value("Web Page", {"route": "warehouse/repack"}, "name")
    if existing_repack_page:
        repack_page = frappe.get_doc("Web Page", existing_repack_page)
    else:
        repack_page = frappe.new_doc("Web Page")
        repack_page.name = "warehouse/repack"

    repack_page.title = "Container Repack"
    repack_page.route = "warehouse/repack"
    repack_page.published = 1
    if repack_page.meta.has_field("login_required"):
        repack_page.login_required = 1
    repack_page.content_type = "HTML"
    repack_page.main_section = repack_html
    if repack_page.meta.has_field("main_section_html"):
        repack_page.main_section_html = repack_html
    repack_page.javascript = repack_script
    repack_page.insert_code = 0
    repack_page.show_sidebar = 0
    repack_page.save(ignore_permissions=True)

    outbound_html = """
<section class="container py-4" style="max-width: 820px;">
  <h1 class="h3 mb-3">Outbound Fulfillment</h1>
  <div class="row g-3">
    <div class="col-md-5">
      <label class="form-label" for="shipment-reference">Shipment Request / Reference</label>
      <input class="form-control" id="shipment-reference" autocomplete="off" autofocus>
    </div>
    <div class="col-md-5">
      <label class="form-label" for="fulfillment-container">Container / HU</label>
      <input class="form-control" id="fulfillment-container" autocomplete="off">
    </div>
    <div class="col-md-2">
      <label class="form-label" for="fulfillment-flow">Flow</label>
      <select class="form-select" id="fulfillment-flow">
        <option value="Packing">Packing</option>
        <option value="Shipping">Shipping</option>
      </select>
    </div>
  </div>
  <div class="d-flex gap-2 align-items-center mt-3">
    <button class="btn btn-primary" id="submit-fulfillment" type="button">Submit Operation</button>
    <span class="text-muted small" id="fulfillment-status"></span>
  </div>
</section>
""".strip()

    outbound_script = """
(function () {
  var FLOW = {
    Packing: {
      stock_entry_type: '3PL Packing',
      purpose: 'Material Transfer',
      target_warehouse: 'Packing - 3',
      request_status: 'Packed',
      container_status: 'Packed',
      movement_type: 'Packed'
    },
    Shipping: {
      stock_entry_type: '3PL Shipping',
      purpose: 'Material Issue',
      target_warehouse: null,
      request_status: 'Shipped',
      container_status: 'Shipped',
      movement_type: 'Shipped'
    }
  };

  function byId(id) { return document.getElementById(id); }
  function setStatus(message, isError) {
    var target = byId('fulfillment-status');
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
  function hasWarehouseRole() {
    var roles = (frappe.user_roles || []);
    return roles.indexOf('3PL Warehouse User') !== -1 || roles.indexOf('3PL Warehouse Manager') !== -1 || roles.indexOf('System Manager') !== -1;
  }
  function requireWarehouseRole() {
    if (frappe.user_roles && !hasWarehouseRole()) {
      setStatus('This scanner page is only available to warehouse users.', true);
      var button = byId('submit-fulfillment');
      if (button) button.disabled = true;
      return false;
    }
    return true;
  }
  function getValue(doctype, filters, fieldname) {
    return api('frappe.client.get_value', { doctype: doctype, filters: filters, fieldname: fieldname });
  }
  function getDoc(doctype, name) {
    return api('frappe.client.get', { doctype: doctype, name: name });
  }
  function insertDoc(doc) {
    return api('frappe.client.insert', { doc: doc });
  }
  function submitDoc(doc) {
    return api('frappe.client.submit', { doc: doc });
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
  function findRequest(reference) {
    return getValue('Three PL Shipment Request', { name: reference }, ['name', 'customer', 'external_reference']).then(function (response) {
      if (response.message && response.message.name) return response.message;
      return getValue('Three PL Shipment Request', { external_reference: reference }, ['name', 'customer', 'external_reference']).then(function (byReference) {
        if (byReference.message && byReference.message.name) return byReference.message;
        throw new Error('Shipment request not found.');
      });
    });
  }
  function buildItems(container, config) {
    if (!container.items || !container.items.length) {
      throw new Error('Container has no item rows.');
    }
    return container.items.map(function (row) {
      return {
        item_code: row.item_code,
        qty: row.qty,
        s_warehouse: container.current_warehouse,
        t_warehouse: config.target_warehouse,
        uom: row.uom,
        stock_uom: row.uom,
        conversion_factor: 1,
        basic_rate: 1,
        scanned_location: container.current_warehouse,
        container_code: container.name
      };
    });
  }
  function createStockEntry(request, container, flow, config) {
    return insertDoc({
      doctype: 'Stock Entry',
      stock_entry_type: config.stock_entry_type,
      purpose: config.purpose,
      company: '3pl',
      posting_date: frappe.datetime.get_today(),
      client: request.customer,
      shipment_request: request.name,
      shipment_reference: request.external_reference,
      warehouse_flow: flow,
      scanned_location: container.current_warehouse,
      container_code: container.name,
      items: buildItems(container, config)
    }).then(function (insertResponse) {
      return submitDoc(insertResponse.message);
    });
  }
  function createMovement(entry, request, container, config) {
    return insertDoc({
      doctype: 'Three PL Container Movement',
      movement_datetime: frappe.datetime.now_datetime(),
      container_code: container.name,
      client: container.client,
      movement_type: config.movement_type,
      from_warehouse: container.current_warehouse,
      to_warehouse: config.target_warehouse,
      reference_doctype: 'Stock Entry',
      reference_name: entry.name,
      notes: 'Created from scanner-first outbound fulfillment page for shipment ' + (request.external_reference || request.name) + '.'
    });
  }
  function submitFulfillment() {
    if (frappe.session && frappe.session.user === 'Guest') {
      window.location.href = '/login?redirect-to=' + encodeURIComponent('/warehouse/outbound-fulfillment');
      return;
    }
    if (!requireWarehouseRole()) return;
    var reference = (byId('shipment-reference').value || '').trim();
    var containerCode = (byId('fulfillment-container').value || '').trim();
    var flow = byId('fulfillment-flow').value;
    var config = FLOW[flow];
    if (!reference || !containerCode || !config) {
      setStatus('Scan shipment and container first.', true);
      return;
    }
    setStatus('Submitting ' + flow.toLowerCase() + '...', false);
    var request;
    var container;
    findRequest(reference).then(function (foundRequest) {
      request = foundRequest;
      return getDoc('Three PL Container', containerCode);
    }).then(function (containerResponse) {
      container = containerResponse.message;
      if (!container || !container.name) throw new Error('Container not found.');
      if (container.client !== request.customer) throw new Error('Container belongs to another client.');
      if (!container.current_warehouse) throw new Error('Container has no current warehouse.');
      return createStockEntry(request, container, flow, config);
    }).then(function (entryResponse) {
      var entry = entryResponse.message;
      return createMovement(entry, request, container, config).then(function () {
        var values = {
          status: config.container_status,
          last_moved_at: frappe.datetime.now_datetime()
        };
        if (config.target_warehouse) values.current_warehouse = config.target_warehouse;
        return setValues('Three PL Container', container.name, values).then(function () {
          return setValue('Three PL Shipment Request', request.name, 'status', config.request_status);
        }).then(function () {
          return entry;
        });
      });
    }).then(function (entry) {
      setStatus(flow + ' submitted: ' + entry.name + '.', false);
      byId('fulfillment-container').value = '';
      byId('fulfillment-container').focus();
    }).catch(function (error) {
      setStatus(error.message || 'Could not submit outbound operation.', true);
    });
  }
  frappe.ready(function () {
    if (frappe.session && frappe.session.user === 'Guest') {
      window.location.href = '/login?redirect-to=' + encodeURIComponent('/warehouse/outbound-fulfillment');
      return;
    }
    requireWarehouseRole();
    var button = byId('submit-fulfillment');
    if (button) button.addEventListener('click', submitFulfillment);
    ['shipment-reference', 'fulfillment-container'].forEach(function (id) {
      var input = byId(id);
      if (input) input.addEventListener('keydown', function (event) {
        if (event.key === 'Enter') {
          event.preventDefault();
          if (id === 'shipment-reference') byId('fulfillment-container').focus();
          else submitFulfillment();
        }
      });
    });
  });
})();
""".strip()

    existing_outbound_page = frappe.db.get_value("Web Page", {"route": "warehouse/outbound-fulfillment"}, "name")
    if existing_outbound_page:
        outbound_page = frappe.get_doc("Web Page", existing_outbound_page)
    else:
        outbound_page = frappe.new_doc("Web Page")
        outbound_page.name = "warehouse/outbound-fulfillment"

    outbound_page.title = "Outbound Fulfillment"
    outbound_page.route = "warehouse/outbound-fulfillment"
    outbound_page.published = 1
    if outbound_page.meta.has_field("login_required"):
        outbound_page.login_required = 1
    outbound_page.content_type = "HTML"
    outbound_page.main_section = outbound_html
    if outbound_page.meta.has_field("main_section_html"):
        outbound_page.main_section_html = outbound_html
    outbound_page.javascript = outbound_script
    outbound_page.insert_code = 0
    outbound_page.show_sidebar = 0
    outbound_page.save(ignore_permissions=True)

    picking_html = """
<section class="container py-4" style="max-width: 760px;">
  <h1 class="h3 mb-3">Picking Confirmation</h1>
  <div class="mb-3">
    <label class="form-label" for="pick-list">Pick List</label>
    <input class="form-control" id="pick-list" autocomplete="off" autofocus>
  </div>
  <div class="mb-3">
    <label class="form-label" for="picked-container">Container / HU</label>
    <input class="form-control" id="picked-container" autocomplete="off">
  </div>
  <div class="d-flex gap-2 align-items-center">
    <button class="btn btn-primary" id="confirm-pick" type="button">Confirm Picked</button>
    <span class="text-muted small" id="picking-status"></span>
  </div>
</section>
""".strip()

    picking_script = """
(function () {
  function byId(id) { return document.getElementById(id); }
  function setStatus(message, isError) {
    var target = byId('picking-status');
    if (!target) return;
    target.textContent = message || '';
    target.className = isError ? 'text-danger small' : 'text-muted small';
  }
  function getCsrfToken() {
    if (frappe.csrf_token && frappe.csrf_token !== 'None') return Promise.resolve(frappe.csrf_token);
    if (window.__threePlCsrfTokenPromise) return window.__threePlCsrfTokenPromise;
    window.__threePlCsrfTokenPromise = fetch('/app', { credentials: 'same-origin' })
      .then(function (response) { return response.text(); })
      .then(function (html) {
        var match = html.match(/frappe\\.csrf_token\\s*=\\s*"([^"]+)"/);
        if (!match || !match[1] || match[1] === 'None') throw new Error('Could not initialize session token. Please refresh and try again.');
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
          if (!response.ok) throw new Error(parseServerMessage(payload) || ('Request failed: ' + response.status));
          return payload;
        });
      });
    });
  }
  function hasWarehouseRole() {
    var roles = (frappe.user_roles || []);
    return roles.indexOf('3PL Warehouse User') !== -1 || roles.indexOf('3PL Warehouse Manager') !== -1 || roles.indexOf('System Manager') !== -1;
  }
  function requireWarehouseRole() {
    if (frappe.user_roles && !hasWarehouseRole()) {
      setStatus('This scanner page is only available to warehouse users.', true);
      var button = byId('confirm-pick');
      if (button) button.disabled = true;
      return false;
    }
    return true;
  }
  function getDoc(doctype, name) {
    return api('frappe.client.get', { doctype: doctype, name: name });
  }
  function insertDoc(doc) {
    return api('frappe.client.insert', { doc: doc });
  }
  function setValue(doctype, name, fieldname, value) {
    return api('frappe.client.set_value', { doctype: doctype, name: name, fieldname: fieldname, value: value });
  }
  function setValues(doctype, name, values) {
    return Object.keys(values).reduce(function (promise, fieldname) {
      return promise.then(function () { return setValue(doctype, name, fieldname, values[fieldname]); });
    }, Promise.resolve());
  }
  function confirmPick() {
    if (frappe.session && frappe.session.user === 'Guest') {
      window.location.href = '/login?redirect-to=' + encodeURIComponent('/warehouse/picking-confirmation');
      return;
    }
    if (!requireWarehouseRole()) return;
    var pickListName = (byId('pick-list').value || '').trim();
    var containerCode = (byId('picked-container').value || '').trim();
    if (!pickListName || !containerCode) {
      setStatus('Scan Pick List and container first.', true);
      return;
    }
    setStatus('Confirming pick...', false);
    var pickList;
    var container;
    var rows;
    getDoc('Pick List', pickListName).then(function (pickResponse) {
      pickList = pickResponse.message;
      rows = (pickList.locations || []).filter(function (row) { return row.container_code === containerCode; });
      if (!rows.length) throw new Error('Container is not allocated in this Pick List.');
      return getDoc('Three PL Container', containerCode);
    }).then(function (containerResponse) {
      container = containerResponse.message;
      return rows.reduce(function (promise, row) {
        return promise.then(function () {
          return setValue('Pick List Item', row.name, 'picked_qty', row.stock_qty || row.qty || 0);
        });
      }, Promise.resolve());
    }).then(function () {
      return insertDoc({
        doctype: 'Three PL Container Movement',
        movement_datetime: frappe.datetime.now_datetime(),
        container_code: container.name,
        client: container.client,
        movement_type: 'Picked',
        from_warehouse: container.current_warehouse,
        to_warehouse: container.current_warehouse,
        reference_doctype: 'Pick List',
        reference_name: pickList.name,
        notes: 'Created from scanner-first picking confirmation page.'
      });
    }).then(function () {
      return setValues('Three PL Container', container.name, {
        status: 'Picked',
        last_moved_at: frappe.datetime.now_datetime()
      });
    }).then(function () {
      setStatus('Pick confirmed for ' + containerCode + '.', false);
      byId('picked-container').value = '';
      byId('picked-container').focus();
    }).catch(function (error) {
      setStatus(error.message || 'Could not confirm pick.', true);
    });
  }
  frappe.ready(function () {
    if (frappe.session && frappe.session.user === 'Guest') {
      window.location.href = '/login?redirect-to=' + encodeURIComponent('/warehouse/picking-confirmation');
      return;
    }
    requireWarehouseRole();
    var button = byId('confirm-pick');
    if (button) button.addEventListener('click', confirmPick);
    ['pick-list', 'picked-container'].forEach(function (id) {
      var input = byId(id);
      if (input) input.addEventListener('keydown', function (event) {
        if (event.key === 'Enter') {
          event.preventDefault();
          if (id === 'pick-list') byId('picked-container').focus();
          else confirmPick();
        }
      });
    });
  });
})();
""".strip()

    existing_picking_page = frappe.db.get_value("Web Page", {"route": "warehouse/picking-confirmation"}, "name")
    if existing_picking_page:
        picking_page = frappe.get_doc("Web Page", existing_picking_page)
    else:
        picking_page = frappe.new_doc("Web Page")
        picking_page.name = "warehouse/picking-confirmation"

    picking_page.title = "Picking Confirmation"
    picking_page.route = "warehouse/picking-confirmation"
    picking_page.published = 1
    if picking_page.meta.has_field("login_required"):
        picking_page.login_required = 1
    picking_page.content_type = "HTML"
    picking_page.main_section = picking_html
    if picking_page.meta.has_field("main_section_html"):
        picking_page.main_section_html = picking_html
    picking_page.javascript = picking_script
    picking_page.insert_code = 0
    picking_page.show_sidebar = 0
    picking_page.save(ignore_permissions=True)

    receiving_review_html = """
<section class="container py-4" style="max-width: 1120px;">
  <div class="d-flex align-items-center justify-content-between gap-3 mb-3">
    <h1 class="h3 m-0">Receiving Review</h1>
    <button class="btn btn-outline-secondary btn-sm" id="refresh-receiving-review" type="button">Refresh</button>
  </div>
  <div class="text-muted small mb-3">Confirm receiving status and client-instruction state after warehouse comparison.</div>
  <div class="table-responsive">
    <table class="table table-sm align-middle">
      <thead>
        <tr>
          <th>Notice</th>
          <th>Client Ref</th>
          <th>Client</th>
          <th>Status</th>
          <th>Instruction</th>
          <th>Expected</th>
          <th>Received</th>
          <th>Variance</th>
          <th class="text-end">Action</th>
        </tr>
      </thead>
      <tbody id="receiving-review-body">
        <tr><td colspan="9" class="text-muted">Loading...</td></tr>
      </tbody>
    </table>
  </div>
  <div class="small text-muted" id="receiving-review-status"></div>
</section>
""".strip()
    receiving_review_script = """
(function () {
  function byId(id) { return document.getElementById(id); }
  function setStatus(message, isError) {
    var target = byId('receiving-review-status');
    if (!target) return;
    target.textContent = message || '';
    target.className = isError ? 'small text-danger' : 'small text-muted';
  }
  function getCsrfToken() {
    if (frappe.csrf_token && frappe.csrf_token !== 'None') return Promise.resolve(frappe.csrf_token);
    return fetch('/app', { credentials: 'same-origin' }).then(function (response) { return response.text(); }).then(function (html) {
      var match = html.match(/frappe\\.csrf_token\\s*=\\s*"([^"]+)"/);
      if (!match || !match[1] || match[1] === 'None') throw new Error('Could not initialize session token. Please refresh and try again.');
      frappe.csrf_token = match[1];
      return match[1];
    });
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
        headers: {'Content-Type': 'application/x-www-form-urlencoded', 'X-Frappe-CSRF-Token': csrfToken},
        body: body
      }).then(function (response) {
        return response.text().then(function (text) {
          var payload = text ? JSON.parse(text) : {};
          if (!response.ok) throw new Error(parseServerMessage(payload) || ('Request failed: ' + response.status));
          return payload;
        });
      });
    });
  }
  function hasWarehouseRole() {
    var roles = frappe.user_roles || [];
    return roles.indexOf('3PL Warehouse User') !== -1 || roles.indexOf('3PL Warehouse Manager') !== -1 || roles.indexOf('Stock Manager') !== -1 || roles.indexOf('System Manager') !== -1;
  }
  function escapeHtml(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, function (ch) {
      return ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'})[ch];
    });
  }
  function loadRows() {
    if (!hasWarehouseRole()) {
      byId('receiving-review-body').innerHTML = '<tr><td colspan="9" class="text-danger">This page is only available to warehouse users.</td></tr>';
      return;
    }
    setStatus('Loading receiving notices...', false);
    api('frappe.client.get_list', {
      doctype: 'Inbound Shipment Notice',
      filters: { status: ['not in', ['Closed']] },
      fields: ['name', 'external_reference', 'customer', 'status', 'client_instruction_status'],
      order_by: 'modified desc',
      limit_page_length: 50
    }).then(function (response) {
      var notices = response.message || [];
      if (!notices.length) {
        byId('receiving-review-body').innerHTML = '<tr><td colspan="9" class="text-muted">No active receiving notices.</td></tr>';
        setStatus('', false);
        return;
      }
      return Promise.all(notices.map(function (notice) {
        return api('frappe.client.get', { doctype: 'Inbound Shipment Notice', name: notice.name }).then(function (docResponse) {
          var doc = docResponse.message;
          var expected = 0;
          var received = 0;
          (doc.items || []).forEach(function (row) {
            expected += Number(row.expected_qty || 0);
            received += Number(row.received_qty || 0);
          });
          notice.expected = expected;
          notice.received = received;
          notice.variance = received - expected;
          return notice;
        });
      }));
    }).then(function (rows) {
      if (!rows) return;
      byId('receiving-review-body').innerHTML = rows.map(function (row) {
        return '<tr>' +
          '<td><a href="/app/inbound-shipment-notice/' + encodeURIComponent(row.name) + '">' + escapeHtml(row.name) + '</a></td>' +
          '<td>' + escapeHtml(row.external_reference) + '</td>' +
          '<td>' + escapeHtml(row.customer) + '</td>' +
          '<td>' + escapeHtml(row.status) + '</td>' +
          '<td>' + escapeHtml(row.client_instruction_status) + '</td>' +
          '<td>' + escapeHtml(row.expected) + '</td>' +
          '<td>' + escapeHtml(row.received) + '</td>' +
          '<td>' + escapeHtml(row.variance) + '</td>' +
          '<td class="text-end text-nowrap">' +
            '<button class="btn btn-sm btn-outline-primary me-1" data-action="received" data-name="' + escapeHtml(row.name) + '">Confirm Received</button>' +
            '<button class="btn btn-sm btn-outline-warning me-1" data-action="wait-client" data-name="' + escapeHtml(row.name) + '">Wait Client</button>' +
            '<button class="btn btn-sm btn-outline-secondary" data-action="close" data-name="' + escapeHtml(row.name) + '">Close</button>' +
          '</td>' +
        '</tr>';
      }).join('');
      setStatus(rows.length + ' active receiving notice(s).', false);
    }).catch(function (error) {
      setStatus(error.message || 'Could not load receiving notices.', true);
    });
  }
  function updateNotice(name, action) {
    var values = {};
    if (action === 'received') {
      values.status = 'Received';
      values.client_instruction_status = 'Not Required';
    }
    if (action === 'wait-client') {
      values.status = 'Discrepancy Review';
      values.client_instruction_status = 'Waiting for Client';
    }
    if (action === 'close') {
      values.status = 'Closed';
    }
    setStatus('Updating ' + name + '...', false);
    api('frappe.client.set_value', {
      doctype: 'Inbound Shipment Notice',
      name: name,
      fieldname: values
    }).then(loadRows).catch(function (error) {
      setStatus(error.message || 'Could not update receiving notice.', true);
    });
  }
  frappe.ready(function () {
    if (frappe.session && frappe.session.user === 'Guest') {
      window.location.href = '/login?redirect-to=' + encodeURIComponent('/warehouse/receiving-review');
      return;
    }
    var refresh = byId('refresh-receiving-review');
    if (refresh) refresh.addEventListener('click', loadRows);
    var body = byId('receiving-review-body');
    if (body) body.addEventListener('click', function (event) {
      var button = event.target.closest('button[data-action]');
      if (!button) return;
      updateNotice(button.getAttribute('data-name'), button.getAttribute('data-action'));
    });
    loadRows();
  });
})();
""".strip()

    existing_receiving_review_page = frappe.db.get_value("Web Page", {"route": "warehouse/receiving-review"}, "name")
    if existing_receiving_review_page:
        receiving_review_page = frappe.get_doc("Web Page", existing_receiving_review_page)
    else:
        receiving_review_page = frappe.new_doc("Web Page")
        receiving_review_page.name = "warehouse/receiving-review"

    receiving_review_page.title = "Receiving Review"
    receiving_review_page.route = "warehouse/receiving-review"
    receiving_review_page.published = 1
    if receiving_review_page.meta.has_field("login_required"):
        receiving_review_page.login_required = 1
    receiving_review_page.content_type = "HTML"
    receiving_review_page.main_section = receiving_review_html
    if receiving_review_page.meta.has_field("main_section_html"):
        receiving_review_page.main_section_html = receiving_review_html
    receiving_review_page.javascript = receiving_review_script
    receiving_review_page.insert_code = 0
    receiving_review_page.show_sidebar = 0
    receiving_review_page.save(ignore_permissions=True)

    shipment_review_html = """
<section class="container py-4" style="max-width: 1040px;">
  <div class="d-flex align-items-center justify-content-between gap-3 mb-3">
    <h1 class="h3 m-0">Shipment Review</h1>
    <button class="btn btn-outline-secondary btn-sm" id="refresh-shipment-review" type="button">Refresh</button>
  </div>
  <div class="text-muted small mb-3">Accept, close, or cancel outbound requests after warehouse processing.</div>
  <div class="table-responsive">
    <table class="table table-sm align-middle">
      <thead>
        <tr>
          <th>Request</th>
          <th>Client Ref</th>
          <th>Client</th>
          <th>Status</th>
          <th>Ship Date</th>
          <th>Destination</th>
          <th class="text-end">Action</th>
        </tr>
      </thead>
      <tbody id="shipment-review-body">
        <tr><td colspan="7" class="text-muted">Loading...</td></tr>
      </tbody>
    </table>
  </div>
  <div class="small text-muted" id="shipment-review-status"></div>
</section>
""".strip()
    shipment_review_script = """
(function () {
  function byId(id) { return document.getElementById(id); }
  function setStatus(message, isError) {
    var target = byId('shipment-review-status');
    if (!target) return;
    target.textContent = message || '';
    target.className = isError ? 'small text-danger' : 'small text-muted';
  }
  function getCsrfToken() {
    if (frappe.csrf_token && frappe.csrf_token !== 'None') return Promise.resolve(frappe.csrf_token);
    return fetch('/app', { credentials: 'same-origin' }).then(function (response) { return response.text(); }).then(function (html) {
      var match = html.match(/frappe\\.csrf_token\\s*=\\s*"([^"]+)"/);
      if (!match || !match[1] || match[1] === 'None') throw new Error('Could not initialize session token. Please refresh and try again.');
      frappe.csrf_token = match[1];
      return match[1];
    });
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
        headers: {'Content-Type': 'application/x-www-form-urlencoded', 'X-Frappe-CSRF-Token': csrfToken},
        body: body
      }).then(function (response) {
        return response.text().then(function (text) {
          var payload = text ? JSON.parse(text) : {};
          if (!response.ok) throw new Error(parseServerMessage(payload) || ('Request failed: ' + response.status));
          return payload;
        });
      });
    });
  }
  function hasWarehouseRole() {
    var roles = frappe.user_roles || [];
    return roles.indexOf('3PL Warehouse User') !== -1 || roles.indexOf('3PL Warehouse Manager') !== -1 || roles.indexOf('Stock Manager') !== -1 || roles.indexOf('System Manager') !== -1;
  }
  function escapeHtml(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, function (ch) {
      return ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'})[ch];
    });
  }
  function loadRows() {
    if (!hasWarehouseRole()) {
      byId('shipment-review-body').innerHTML = '<tr><td colspan="7" class="text-danger">This page is only available to warehouse users.</td></tr>';
      return;
    }
    setStatus('Loading shipment requests...', false);
    api('frappe.client.get_list', {
      doctype: 'Three PL Shipment Request',
      filters: { status: ['not in', ['Closed', 'Cancelled']] },
      fields: ['name', 'external_reference', 'customer', 'status', 'requested_ship_date', 'destination_name'],
      order_by: 'modified desc',
      limit_page_length: 50
    }).then(function (response) {
      var rows = response.message || [];
      if (!rows.length) {
        byId('shipment-review-body').innerHTML = '<tr><td colspan="7" class="text-muted">No active shipment requests.</td></tr>';
        setStatus('', false);
        return;
      }
      byId('shipment-review-body').innerHTML = rows.map(function (row) {
        return '<tr>' +
          '<td><a href="/app/three-pl-shipment-request/' + encodeURIComponent(row.name) + '">' + escapeHtml(row.name) + '</a></td>' +
          '<td>' + escapeHtml(row.external_reference) + '</td>' +
          '<td>' + escapeHtml(row.customer) + '</td>' +
          '<td>' + escapeHtml(row.status) + '</td>' +
          '<td>' + escapeHtml(row.requested_ship_date) + '</td>' +
          '<td>' + escapeHtml(row.destination_name) + '</td>' +
          '<td class="text-end text-nowrap">' +
            '<button class="btn btn-sm btn-outline-primary me-1" data-action="accepted" data-name="' + escapeHtml(row.name) + '">Accept</button>' +
            '<button class="btn btn-sm btn-outline-secondary me-1" data-action="closed" data-name="' + escapeHtml(row.name) + '">Close</button>' +
            '<button class="btn btn-sm btn-outline-danger" data-action="cancelled" data-name="' + escapeHtml(row.name) + '">Cancel</button>' +
          '</td>' +
        '</tr>';
      }).join('');
      setStatus(rows.length + ' active shipment request(s).', false);
    }).catch(function (error) {
      setStatus(error.message || 'Could not load shipment requests.', true);
    });
  }
  function updateRequest(name, action) {
    var status = action === 'accepted' ? 'Accepted' : (action === 'closed' ? 'Closed' : 'Cancelled');
    setStatus('Updating ' + name + '...', false);
    api('frappe.client.set_value', {
      doctype: 'Three PL Shipment Request',
      name: name,
      fieldname: { status: status }
    }).then(loadRows).catch(function (error) {
      setStatus(error.message || 'Could not update shipment request.', true);
    });
  }
  frappe.ready(function () {
    if (frappe.session && frappe.session.user === 'Guest') {
      window.location.href = '/login?redirect-to=' + encodeURIComponent('/warehouse/shipment-review');
      return;
    }
    var refresh = byId('refresh-shipment-review');
    if (refresh) refresh.addEventListener('click', loadRows);
    var body = byId('shipment-review-body');
    if (body) body.addEventListener('click', function (event) {
      var button = event.target.closest('button[data-action]');
      if (!button) return;
      updateRequest(button.getAttribute('data-name'), button.getAttribute('data-action'));
    });
    loadRows();
  });
})();
""".strip()

    existing_shipment_review_page = frappe.db.get_value("Web Page", {"route": "warehouse/shipment-review"}, "name")
    if existing_shipment_review_page:
        shipment_review_page = frappe.get_doc("Web Page", existing_shipment_review_page)
    else:
        shipment_review_page = frappe.new_doc("Web Page")
        shipment_review_page.name = "warehouse/shipment-review"

    shipment_review_page.title = "Shipment Review"
    shipment_review_page.route = "warehouse/shipment-review"
    shipment_review_page.published = 1
    if shipment_review_page.meta.has_field("login_required"):
        shipment_review_page.login_required = 1
    shipment_review_page.content_type = "HTML"
    shipment_review_page.main_section = shipment_review_html
    if shipment_review_page.meta.has_field("main_section_html"):
        shipment_review_page.main_section_html = shipment_review_html
    shipment_review_page.javascript = shipment_review_script
    shipment_review_page.insert_code = 0
    shipment_review_page.show_sidebar = 0
    shipment_review_page.save(ignore_permissions=True)

    correction_review_html = """
<section class="container py-4" style="max-width: 1120px;">
  <div class="d-flex align-items-center justify-content-between gap-3 mb-3">
    <h1 class="h3 m-0">Correction Review</h1>
    <button class="btn btn-outline-secondary btn-sm" id="refresh-correction-review" type="button">Refresh</button>
  </div>
  <div class="text-muted small mb-3">Review warehouse corrections where ERPNext stock posting needs a manager decision.</div>
  <div class="mb-3">
    <label class="form-label" for="correction-review-notes">Review Notes</label>
    <input class="form-control" id="correction-review-notes" autocomplete="off" placeholder="Optional manager decision note">
  </div>
  <div class="table-responsive">
    <table class="table table-sm align-middle">
      <thead>
        <tr>
          <th>Correction</th>
          <th>Client</th>
          <th>Container</th>
          <th>Item</th>
          <th>Delta</th>
          <th>Location</th>
          <th>Error</th>
          <th class="text-end">Action</th>
        </tr>
      </thead>
      <tbody id="correction-review-body">
        <tr><td colspan="8" class="text-muted">Loading...</td></tr>
      </tbody>
    </table>
  </div>
  <div class="small text-muted" id="correction-review-status"></div>
</section>
""".strip()
    correction_review_script = """
(function () {
  function byId(id) { return document.getElementById(id); }
  function setStatus(message, isError) {
    var target = byId('correction-review-status');
    if (!target) return;
    target.textContent = message || '';
    target.className = isError ? 'small text-danger' : 'small text-muted';
  }
  function getCsrfToken() {
    if (frappe.csrf_token && frappe.csrf_token !== 'None') return Promise.resolve(frappe.csrf_token);
    if (window.__threePlCsrfTokenPromise) return window.__threePlCsrfTokenPromise;
    window.__threePlCsrfTokenPromise = fetch('/app', { credentials: 'same-origin' })
      .then(function (response) { return response.text(); })
      .then(function (html) {
        var match = html.match(/frappe\\.csrf_token\\s*=\\s*"([^"]+)"/);
        if (!match || !match[1] || match[1] === 'None') throw new Error('Could not initialize session token. Please refresh and try again.');
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
          if (!response.ok) throw new Error(parseServerMessage(payload) || ('Request failed: ' + response.status));
          return payload;
        });
      });
    });
  }
  function hasManagerRole() {
    var roles = (frappe.user_roles || []);
    return roles.indexOf('3PL Warehouse Manager') !== -1 || roles.indexOf('Stock Manager') !== -1 || roles.indexOf('System Manager') !== -1;
  }
  function escapeHtml(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, function (ch) {
      return ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'})[ch];
    });
  }
  function loadRows() {
    if (!hasManagerRole()) {
      byId('correction-review-body').innerHTML = '<tr><td colspan="8" class="text-danger">This page is only available to warehouse managers.</td></tr>';
      return;
    }
    setStatus('Loading corrections...', false);
    api('frappe.client.get_list', {
      doctype: 'Three PL Warehouse Correction',
      filters: { stock_posting_status: 'Needs Review' },
      fields: ['name', 'client', 'container_code', 'item_code', 'qty_delta', 'warehouse', 'stock_posting_error'],
      order_by: 'modified desc',
      limit_page_length: 50
    }).then(function (response) {
      var rows = response.message || [];
      if (!rows.length) {
        byId('correction-review-body').innerHTML = '<tr><td colspan="8" class="text-muted">No corrections need review.</td></tr>';
        setStatus('', false);
        return;
      }
      byId('correction-review-body').innerHTML = rows.map(function (row) {
        return '<tr>' +
          '<td><a href="/app/three-pl-warehouse-correction/' + encodeURIComponent(row.name) + '">' + escapeHtml(row.name) + '</a></td>' +
          '<td>' + escapeHtml(row.client) + '</td>' +
          '<td>' + escapeHtml(row.container_code) + '</td>' +
          '<td>' + escapeHtml(row.item_code) + '</td>' +
          '<td>' + escapeHtml(row.qty_delta) + '</td>' +
          '<td>' + escapeHtml(row.warehouse) + '</td>' +
          '<td class="small text-muted" style="max-width: 360px;">' + escapeHtml(row.stock_posting_error) + '</td>' +
          '<td class="text-end text-nowrap">' +
            '<button class="btn btn-sm btn-outline-primary me-1" data-action="retry" data-name="' + escapeHtml(row.name) + '">Retry</button>' +
            '<button class="btn btn-sm btn-outline-secondary me-1" data-action="not-required" data-name="' + escapeHtml(row.name) + '">Not Required</button>' +
            '<button class="btn btn-sm btn-outline-danger" data-action="cancel" data-name="' + escapeHtml(row.name) + '">Cancel</button>' +
          '</td>' +
        '</tr>';
      }).join('');
      setStatus(rows.length + ' correction(s) need review.', false);
    }).catch(function (error) {
      setStatus(error.message || 'Could not load corrections.', true);
    });
  }
  function updateCorrection(name, action) {
    var notesInput = byId('correction-review-notes');
    var reviewNotes = notesInput ? (notesInput.value || '').trim() : '';
    var values = {
      stock_posting_error: '',
      reviewed_by: frappe.session.user,
      reviewed_at: frappe.datetime.now_datetime(),
      review_notes: reviewNotes
    };
    if (action === 'retry') {
      values.stock_posting_status = 'Pending';
      values.review_decision = 'Retry Posting';
    }
    if (action === 'not-required') {
      values.stock_posting_status = 'Not Required';
      values.review_decision = 'No Stock Posting Required';
    }
    if (action === 'cancel') {
      values.status = 'Cancelled';
      values.stock_posting_status = 'Not Required';
      values.review_decision = 'Cancelled';
    }
    setStatus('Updating ' + name + '...', false);
    return api('frappe.client.set_value', {
      doctype: 'Three PL Warehouse Correction',
      name: name,
      fieldname: values
    }).then(function () {
      loadRows();
    }).catch(function (error) {
      setStatus(error.message || 'Could not update correction.', true);
    });
  }
  frappe.ready(function () {
    if (frappe.session && frappe.session.user === 'Guest') {
      window.location.href = '/login?redirect-to=' + encodeURIComponent('/warehouse/correction-review');
      return;
    }
    var refresh = byId('refresh-correction-review');
    if (refresh) refresh.addEventListener('click', loadRows);
    var body = byId('correction-review-body');
    if (body) body.addEventListener('click', function (event) {
      var button = event.target.closest('button[data-action]');
      if (!button) return;
      var action = button.getAttribute('data-action');
      var name = button.getAttribute('data-name');
      if (action === 'retry') updateCorrection(name, 'retry');
      if (action === 'not-required') updateCorrection(name, 'not-required');
      if (action === 'cancel') updateCorrection(name, 'cancel');
    });
    loadRows();
  });
})();
""".strip()

    existing_correction_review_page = frappe.db.get_value("Web Page", {"route": "warehouse/correction-review"}, "name")
    if existing_correction_review_page:
        correction_review_page = frappe.get_doc("Web Page", existing_correction_review_page)
    else:
        correction_review_page = frappe.new_doc("Web Page")
        correction_review_page.name = "warehouse/correction-review"

    correction_review_page.title = "Correction Review"
    correction_review_page.route = "warehouse/correction-review"
    correction_review_page.published = 1
    if correction_review_page.meta.has_field("login_required"):
        correction_review_page.login_required = 1
    correction_review_page.content_type = "HTML"
    correction_review_page.main_section = correction_review_html
    if correction_review_page.meta.has_field("main_section_html"):
        correction_review_page.main_section_html = correction_review_html
    correction_review_page.javascript = correction_review_script
    correction_review_page.insert_code = 0
    correction_review_page.show_sidebar = 0
    correction_review_page.save(ignore_permissions=True)


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


if __name__ == "__main__":
    main()
