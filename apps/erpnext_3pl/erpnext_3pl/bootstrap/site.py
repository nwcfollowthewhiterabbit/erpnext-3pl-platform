import json
from datetime import date

import frappe
from frappe.utils import getdate, nowdate

from erpnext_3pl.config.project_config import (
    CLIENT_DESK_USER,
    COMPANY,
    COMPANY_ABBR,
    COUNTRY,
    CURRENCY,
    LANGUAGE,
    PLACEHOLDER_EMAIL,
    TIME_ZONE,
)


APP_REPLACED_SERVER_SCRIPTS = [
    "3PL Client Product Immediate Sync",
    "3PL Container Inventory Snapshot Sync",
    "3PL Receiving Notice Discrepancy Sync",
    "3PL Client Instruction Status Sync",
    "3PL Shipment Request Immediate Pick List Sync",
    "3PL Product Import Immediate Sync",
    "3PL Stock Entry Immediate Flow Sync",
    "3PL Pick List Immediate Picked Sync",
]
CLIENT_DESK_READ_ONLY_DOCTYPES = {
    "Three PL Container Movement",
    "Three PL Inventory Balance Snapshot",
    "Three PL Inventory Snapshot",
}
CUSTOM_DOCTYPE_MODULE = "ERPNext 3PL"
STANDARD_DESKTOP_ICONS_TO_HIDE = {
    "Accounts",
    "Accounting",
    "Assets",
    "Automation",
    "Banking",
    "Budget",
    "Build",
    "Buying",
    "CRM",
    "Data",
    "Email",
    "ERPNext",
    "ERPNext Settings",
    "Financial Reports",
    "Framework",
    "Integrations",
    "Manufacturing",
    "My Workspaces",
    "Printing",
    "Projects",
    "Quality",
    "Selling",
    "Share Management",
    "Stock",
    "Subcontracting",
    "Subscription",
    "Support",
    "System",
    "Taxes",
    "Users",
    "Website",
}
CLIENT_DESKTOP_SHORTCUTS = [
    {
        "label": "3PL Client",
        "icon": "users",
        "item": {"label": "3PL Client", "link_type": "URL", "url": "/desk/3pl-client"},
    },
    {
        "label": "Receiving Notices",
        "icon": "truck",
        "group": "Inbound",
        "item": {"label": "Receiving Notices", "link_type": "DocType", "link_to": "Inbound Shipment Notice"},
    },
    {
        "label": "Shipment Requests",
        "icon": "send",
        "group": "Outbound",
        "item": {"label": "Shipment Requests", "link_type": "DocType", "link_to": "Three PL Shipment Request"},
    },
    {
        "label": "Products",
        "icon": "package",
        "group": "Products & Issues",
        "item": {"label": "Products", "link_type": "DocType", "link_to": "Three PL Client Product"},
    },
    {
        "label": "Discrepancy Instructions",
        "icon": "message-square-warning",
        "group": "Products & Issues",
        "item": {
            "label": "Discrepancy Instructions",
            "link_type": "DocType",
            "link_to": "Three PL Client Instruction",
        },
    },
    {
        "label": "Receiving Discrepancies",
        "icon": "triangle-alert",
        "group": "Inbound",
        "item": {"label": "Receiving Discrepancies", "link_type": "Report", "link_to": "3PL Receiving Discrepancies"},
    },
    {
        "label": "Current Inventory",
        "icon": "clipboard-list",
        "group": "Inventory",
        "item": {"label": "Current Inventory", "link_type": "Report", "link_to": "3PL Client Inventory Summary"},
    },
    {
        "label": "Inventory By Date",
        "icon": "calendar-days",
        "group": "Inventory",
        "item": {"label": "Inventory By Date", "link_type": "Report", "link_to": "3PL Inventory Balance By Date"},
    },
    {
        "label": "Operation Turnover",
        "icon": "history",
        "group": "Inventory",
        "item": {"label": "Operation Turnover", "link_type": "Report", "link_to": "3PL Warehouse Operation Turnover"},
    },
]
CLIENT_DESKTOP_GROUPS = [
    {"label": "Inbound", "icon": "truck"},
    {"label": "Outbound", "icon": "send"},
    {"label": "Inventory", "icon": "clipboard-list"},
    {"label": "Products & Issues", "icon": "package"},
]


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

    today = getdate(nowdate())
    fiscal_year_name = frappe.db.get_value(
        "Fiscal Year",
        {
            "year_start_date": ("<=", today),
            "year_end_date": (">=", today),
            "disabled": 0,
        },
        "name",
        order_by="year_start_date desc",
    )
    if fiscal_year_name:
        fiscal_year = frappe.get_doc("Fiscal Year", fiscal_year_name)
    else:
        fiscal_year = frappe.new_doc("Fiscal Year")
        fiscal_year.year = str(today.year)
        fiscal_year.year_start_date = date(today.year, 1, 1)
        fiscal_year.year_end_date = date(today.year, 12, 31)
        fiscal_year.disabled = 0
    if not any(row.company == COMPANY for row in fiscal_year.get("companies", [])):
        fiscal_year.append("companies", {"company": COMPANY})
    fiscal_year.save(ignore_permissions=True)


def configure_module_profiles():
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

    old_in_install = getattr(frappe.flags, "in_install", False)
    try:
        frappe.flags.in_install = True
        for profile_name in ("Warehouse Only", "3PL Client Only"):
            if frappe.db.exists("Module Profile", profile_name):
                profile = frappe.get_doc("Module Profile", profile_name)
                profile.set("block_modules", [])
            else:
                profile = frappe.new_doc("Module Profile")
                profile.module_profile_name = profile_name

            for module in blocked_modules:
                profile.append("block_modules", {"module": module})
            profile.save(ignore_permissions=True)
    except frappe.DocumentLockedError:
        frappe.log_error("3PL module profile is locked; skipping profile update")
    finally:
        frappe.flags.in_install = old_in_install

    for role_name in ("3PL Warehouse User", "3PL Warehouse Manager", "3PL Client"):
        if not frappe.db.exists("Role", role_name):
            frappe.get_doc({"doctype": "Role", "role_name": role_name}).insert(ignore_permissions=True)

    if frappe.db.exists("Role", "3PL Client"):
        role = frappe.get_doc("Role", "3PL Client")
        changed = False
        if role.meta.has_field("desk_access") and not role.desk_access:
            role.desk_access = 1
            changed = True
        if role.home_page != "desk/3pl-client":
            role.home_page = "desk/3pl-client"
            changed = True
        if changed:
            role.save(ignore_permissions=True)

    for role_name in ("Stock User", "Stock Manager", "3PL Warehouse User", "3PL Warehouse Manager"):
        if frappe.db.exists("Role", role_name):
            frappe.db.set_value("Role", role_name, "home_page", "desk/3pl-warehouse")

    frappe.db.set_default("desktop:home_page", "workspace")


def configure_home_workspace():
    for sidebar_item in frappe.get_all("Workspace Sidebar Item", filters={"parent": "Home"}, pluck="name"):
        frappe.delete_doc("Workspace Sidebar Item", sidebar_item, ignore_permissions=True, force=True)

    if frappe.db.exists("Workspace", "Home"):
        workspace = frappe.get_doc("Workspace", "Home")
    else:
        workspace = frappe.new_doc("Workspace")
        workspace.label = "Home"
        workspace.title = "Home"
        workspace.name = "Home"

    workspace.public = 1
    workspace.is_hidden = 0
    workspace.module = CUSTOM_DOCTYPE_MODULE
    workspace.content = json.dumps(
        [
            {
                "id": "erpnext_3pl_home_header",
                "type": "header",
                "data": {"text": '<span class="h4"><b>ERPNext 3PL</b></span>', "col": 12},
            }
        ]
    )
    for table_field in ("links", "shortcuts", "number_cards", "charts", "custom_blocks", "quick_lists"):
        if workspace.meta.has_field(table_field):
            workspace.set(table_field, [])
    workspace.set("roles", [])
    for idx, role in enumerate(("3PL Client", "3PL Warehouse User", "3PL Warehouse Manager", "System Manager"), start=1):
        workspace.append("roles", {"idx": idx, "role": role})
    workspace.save(ignore_permissions=True)


def ensure_desktop_icon(label, idx, icon, icon_type="Link", parent_icon=None, hidden=0):
    if frappe.db.exists("Desktop Icon", label):
        doc = frappe.get_doc("Desktop Icon", label)
    else:
        doc = frappe.new_doc("Desktop Icon")
        doc.label = label

    expected = {
        "standard": 1,
        "app": "erpnext_3pl",
        "icon_type": icon_type,
        "link_type": "Workspace Sidebar",
        "link_to": label if icon_type == "Link" else None,
        "sidebar": None,
        "parent_icon": parent_icon,
        "hidden": hidden,
        "restrict_removal": 1,
        "idx": idx,
    }
    if doc.meta.has_field("icon"):
        expected["icon"] = icon
    changed = False
    for fieldname, value in expected.items():
        if getattr(doc, fieldname, None) != value:
            setattr(doc, fieldname, value)
            changed = True
    if doc.is_new():
        doc.insert(ignore_permissions=True)
    elif changed:
        doc.save(ignore_permissions=True)


def ensure_desktop_folder(label, idx, icon):
    ensure_desktop_icon(label, idx, icon, icon_type="Folder")


def ensure_workspace_sidebar(title, idx, icon):
    if frappe.db.exists("Workspace Sidebar", title):
        sidebar = frappe.get_doc("Workspace Sidebar", title)
    else:
        sidebar = frappe.new_doc("Workspace Sidebar")
        sidebar.title = title

    expected = {
        "idx": idx,
        "header_icon": icon,
        "module": CUSTOM_DOCTYPE_MODULE,
        "standard": 1,
        "app": "erpnext_3pl",
    }
    changed = False
    for fieldname, value in expected.items():
        if getattr(sidebar, fieldname, None) != value:
            setattr(sidebar, fieldname, value)
            changed = True
    if sidebar.is_new():
        sidebar.insert(ignore_permissions=True)
    elif changed:
        sidebar.save(ignore_permissions=True)

    existing_item = frappe.db.get_value(
        "Workspace Sidebar Item",
        {"parent": title, "type": "Link", "link_type": "Workspace", "link_to": title},
        "name",
    )
    if existing_item:
        item = frappe.get_doc("Workspace Sidebar Item", existing_item)
    else:
        item = frappe.new_doc("Workspace Sidebar Item")
        item.parent = title
        item.parenttype = "Workspace Sidebar"
        item.parentfield = "items"

    expected_item = {
        "idx": 1,
        "label": title,
        "type": "Link",
        "link_type": "Workspace",
        "link_to": title,
        "icon": icon,
        "child": 0,
    }
    changed = False
    for fieldname, value in expected_item.items():
        if getattr(item, fieldname, None) != value:
            setattr(item, fieldname, value)
            changed = True
    if item.is_new():
        item.insert(ignore_permissions=True)
    elif changed:
        item.save(ignore_permissions=True)


def ensure_desktop_shortcut(shortcut, idx):
    title = shortcut["label"]
    item_spec = shortcut["item"]
    icon = shortcut["icon"]

    if frappe.db.exists("Workspace Sidebar", title):
        sidebar = frappe.get_doc("Workspace Sidebar", title)
    else:
        sidebar = frappe.new_doc("Workspace Sidebar")
        sidebar.title = title

    expected_sidebar = {
        "idx": idx,
        "header_icon": icon,
        "module": CUSTOM_DOCTYPE_MODULE,
        "standard": 1,
        "app": "erpnext_3pl",
    }
    changed = False
    for fieldname, value in expected_sidebar.items():
        if getattr(sidebar, fieldname, None) != value:
            setattr(sidebar, fieldname, value)
            changed = True
    if sidebar.is_new():
        sidebar.insert(ignore_permissions=True)
    elif changed:
        sidebar.save(ignore_permissions=True)

    for existing in frappe.get_all("Workspace Sidebar Item", filters={"parent": title}, pluck="name"):
        frappe.delete_doc("Workspace Sidebar Item", existing, ignore_permissions=True, force=True)

    item = frappe.new_doc("Workspace Sidebar Item")
    item.parent = title
    item.parenttype = "Workspace Sidebar"
    item.parentfield = "items"
    item.idx = 1
    item.label = item_spec["label"]
    item.type = "Link"
    item.link_type = item_spec["link_type"]
    item.link_to = item_spec.get("link_to")
    item.url = item_spec.get("url")
    item.icon = icon
    item.child = 0
    item.insert(ignore_permissions=True)

    ensure_desktop_icon(title, idx, icon, parent_icon=shortcut.get("group"))


def configure_desktop_icons():
    for label in STANDARD_DESKTOP_ICONS_TO_HIDE:
        if frappe.db.exists("Desktop Icon", label):
            frappe.db.set_value("Desktop Icon", label, "hidden", 1, update_modified=False)

    ensure_desktop_shortcut(CLIENT_DESKTOP_SHORTCUTS[0], 1)
    for idx, group in enumerate(CLIENT_DESKTOP_GROUPS, start=2):
        ensure_desktop_folder(group["label"], idx, group["icon"])
    for idx, shortcut in enumerate(CLIENT_DESKTOP_SHORTCUTS[1:], start=1):
        ensure_desktop_shortcut(shortcut, idx)

    if frappe.db.exists("Desktop Icon", "3PL Warehouse"):
        frappe.db.set_value("Desktop Icon", "3PL Warehouse", "hidden", 1, update_modified=False)

    for user in (CLIENT_DESK_USER, "warehouse.demo@example.test", "warehouse.manager@example.test"):
        if frappe.db.exists("User", user):
            frappe.clear_cache(user=user)
    frappe.cache.hdel("desktop_icons", CLIENT_DESK_USER)
    frappe.cache.hdel("bootinfo", CLIENT_DESK_USER)


def configure_client_desk_user():
    if not frappe.db.exists("User", CLIENT_DESK_USER):
        return

    user = frappe.get_doc("User", CLIENT_DESK_USER)
    changed = False
    expected = {
        "enabled": 1,
        "user_type": "System User",
        "module_profile": "3PL Client Only" if frappe.db.exists("Module Profile", "3PL Client Only") else None,
        "default_workspace": "3PL Client" if frappe.db.exists("Workspace", "3PL Client") else None,
    }
    if user.meta.has_field("default_app"):
        expected["default_app"] = None

    for fieldname, value in expected.items():
        if getattr(user, fieldname, None) != value:
            setattr(user, fieldname, value)
            changed = True

    if not any(row.role == "3PL Client" for row in user.roles):
        user.append("roles", {"role": "3PL Client"})
        changed = True

    original_role_count = len(user.roles)
    user.roles = [row for row in user.roles if row.role != "Customer"]
    if len(user.roles) != original_role_count:
        changed = True

    if changed:
        user.save(ignore_permissions=True)


def configure_permissions():
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
    for permission_name in frappe.get_all("Custom DocPerm", filters={"parent": "Page", "role": "3PL Client"}, pluck="name"):
        frappe.delete_doc("Custom DocPerm", permission_name, ignore_permissions=True, force=True)

    for doctype in CLIENT_DESK_READ_ONLY_DOCTYPES:
        filters = {"parent": doctype, "role": "3PL Client", "permlevel": 0, "if_owner": 0}
        if frappe.db.exists("Custom DocPerm", filters):
            permission = frappe.get_doc("Custom DocPerm", filters)
        else:
            permission = frappe.new_doc("Custom DocPerm")
            permission.parent = doctype
            permission.parenttype = "DocType"
            permission.parentfield = "permissions"
            permission.role = "3PL Client"
            permission.permlevel = 0
            permission.if_owner = 0

        for fieldname, value in {
            "read": 1,
            "report": 1,
            "export": 1,
            "print": 1,
            "email": 1,
            "write": 0,
            "create": 0,
            "delete": 0,
            "submit": 0,
            "cancel": 0,
            "amend": 0,
            "share": 0,
            "import": 0,
            "select": 0,
        }.items():
            if permission.meta.has_field(fieldname):
                setattr(permission, fieldname, value)
        permission.save(ignore_permissions=True)


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


def disable_app_replaced_server_scripts():
    for script_name in APP_REPLACED_SERVER_SCRIPTS:
        if frappe.db.exists("Server Script", script_name):
            frappe.db.set_value("Server Script", script_name, "disabled", 1, update_modified=True)


def mark_setup_complete():
    if frappe.db.table_exists("Installed Application"):
        for app_name in ("frappe", "erpnext"):
            if frappe.db.exists("Installed Application", {"app_name": app_name}):
                frappe.db.set_value("Installed Application", {"app_name": app_name}, "is_setup_complete", 1)

    if frappe.db.exists("DocType", "System Settings"):
        frappe.db.set_single_value("System Settings", "setup_complete", frappe.is_setup_complete())


def main():
    configure_company()
    configure_module_profiles()
    configure_home_workspace()
    configure_desktop_icons()
    configure_client_desk_user()
    configure_permissions()
    configure_warehouses()
    disable_app_replaced_server_scripts()
    configure_defaults()
    configure_email_placeholder()
    mark_setup_complete()
    frappe.db.commit()
    frappe.clear_cache()
