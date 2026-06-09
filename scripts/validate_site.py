import importlib.util

import frappe
from frappe.utils import now_datetime, nowdate

from project_config import (
    BUSINESS_OWNER_USER,
    CLIENT_PORTAL_CUSTOMER,
    CLIENT_PORTAL_FORMS,
    CLIENT_PORTAL_HOME,
    CLIENT_PORTAL_ROUTES,
    CLIENT_PORTAL_USER,
    COUNTRY as REQUIRED_COUNTRY,
    CURRENCY as REQUIRED_CURRENCY,
    DEMO_ITEMS,
    LANGUAGE as REQUIRED_LANGUAGE,
    PLACEHOLDER_EMAIL as REQUIRED_PLACEHOLDER_EMAIL,
    TIME_ZONE as REQUIRED_TIME_ZONE,
    WAREHOUSE_MANAGER_USER,
    WAREHOUSE_OPERATOR_USER,
)


REQUIRED_WORKSPACES = ["3PL Warehouse", "Stock Reference"]
REQUIRED_USERS = {
    WAREHOUSE_OPERATOR_USER: ["Stock User", "3PL Warehouse User"],
    WAREHOUSE_MANAGER_USER: ["Stock User", "Stock Manager", "3PL Warehouse Manager"],
    BUSINESS_OWNER_USER: ["System Manager", "Stock User", "Stock Manager", "Item Manager", "3PL Warehouse Manager"],
    CLIENT_PORTAL_USER: ["3PL Client"],
}
REQUIRED_DOCTYPES = [
    "Inbound Shipment Notice",
    "Inbound Shipment Notice Item",
    "Inbound Shipment Discrepancy",
    "Three PL Container",
    "Three PL Container Item",
    "Three PL Container Move",
    "Three PL Container Movement",
    "Three PL Container Repack",
    "Three PL Repack Source",
    "Three PL Repack Item",
    "Three PL Warehouse Correction",
    "Three PL Stocktake",
    "Three PL Inventory Snapshot",
    "Three PL Inventory Balance Snapshot",
    "Three PL Shipment Request",
    "Three PL Shipment Request Item",
    "Three PL Client Instruction",
]
REQUIRED_CONTAINER_FIELDS = {
    "container_code",
    "barcode",
    "container_type",
    "client",
    "current_warehouse",
    "status",
    "last_moved_at",
    "parent_container",
    "replaced_by",
    "items",
}
REQUIRED_CONTAINER_STATUSES = {
    "Expected",
    "Received",
    "In Verification",
    "Ready for Putaway",
    "Stored",
    "Picking",
    "Picked",
    "Packed",
    "Shipped",
    "Empty",
    "Closed",
    "Replaced",
}
REQUIRED_CONTAINER_MOVEMENT_FIELDS = {
    "movement_datetime",
    "container_code",
    "client",
    "movement_type",
    "from_warehouse",
    "to_warehouse",
    "from_container",
    "to_container",
    "reference_doctype",
    "reference_name",
}
REQUIRED_CONTAINER_MOVEMENT_TYPES = {
    "Expected",
    "Received",
    "Moved",
    "Putaway",
    "Picking",
    "Picked",
    "Packed",
    "Shipped",
    "Repacked",
    "Adjusted",
}
REQUIRED_CONTAINER_MOVE_FIELDS = {
    "operation_reference",
    "operation_datetime",
    "status",
    "container_code",
    "client",
    "from_warehouse",
    "to_warehouse",
    "stock_entry",
    "movement",
}
REQUIRED_CONTAINER_REPACK_FIELDS = {
    "operation_reference",
    "operation_datetime",
    "status",
    "client",
    "target_container",
    "target_location",
    "movement",
    "source_containers",
    "items",
}
REQUIRED_WAREHOUSE_CORRECTION_FIELDS = {
    "operation_reference",
    "operation_datetime",
    "status",
    "correction_type",
    "client",
    "container_code",
    "warehouse",
    "item_code",
    "expected_qty",
    "actual_qty",
    "qty_delta",
    "condition_status",
    "movement",
    "stock_entry",
    "stock_posting_status",
    "stock_posting_error",
}
REQUIRED_STOCKTAKE_FIELDS = {
    "operation_reference",
    "operation_datetime",
    "status",
    "client",
    "warehouse",
    "container_code",
    "item_code",
    "expected_qty",
    "counted_qty",
    "qty_delta",
    "condition_status",
    "correction",
    "movement",
}
REQUIRED_INVENTORY_BALANCE_SNAPSHOT_FIELDS = {
    "snapshot_date",
    "customer",
    "item_code",
    "client_sku",
    "item_name",
    "qty",
    "uom",
    "warehouse",
    "container_code",
    "status",
    "source_snapshot",
    "captured_at",
}
REQUIRED_REPORTS = [
    "3PL ASN vs Received",
    "3PL Receiving Discrepancies",
    "3PL Containers",
    "3PL Container Moves",
    "3PL Container Repacks",
    "3PL Warehouse Corrections",
    "3PL Corrections Needing Review",
    "3PL Stocktakes",
    "3PL Container Movements",
    "3PL Shipment Requests",
    "3PL Client Inventory",
    "3PL Client Inventory Summary",
    "3PL Inventory Balance By Date",
    "3PL Warehouse Operation Turnover",
]
REQUIRED_CUSTOM_FIELDS = [
    "Stock Entry-client",
    "Stock Entry-inbound_shipment_notice",
    "Stock Entry-shipment_request",
    "Stock Entry-shipment_reference",
    "Stock Entry-warehouse_flow",
    "Stock Entry-scanned_location",
    "Item-owner_client",
    "Item-client_sku",
    "Item-client_product_name",
    "Stock Entry-container_code",
    "Stock Entry-warehouse_correction",
    "Stock Entry Detail-container_code",
    "Pick List-container_code",
    "Pick List-shipment_request",
    "Pick List Item-container_code",
]
REQUIRED_WAREHOUSES = [
    "Receiving Area - 3",
    "Temporary Receiving - 3",
    "Inspection and Comparison - 3",
    "Storage Locations - 3",
    "Aisle A - 3",
    "Aisle B - 3",
    "Overflow - 3",
    "Packing - 3",
    "Shipping - 3",
]


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def require_role_perm(doctype, role, **expected):
    permissions = []
    for table in ("DocPerm", "Custom DocPerm"):
        permissions.extend(frappe.get_all(table, filters={"parent": doctype, "role": role}, fields=list(expected)))

    require(
        any(all(row.get(permission) == value for permission, value in expected.items()) for row in permissions),
        f"Missing permission for {role} on {doctype}: {expected}",
    )


def require_effective_perm(user, doctype, *permission_types):
    current_user = frappe.session.user
    try:
        frappe.set_user(user)
        for permission_type in permission_types:
            require(
                frappe.has_permission(doctype, permission_type),
                f"{user} lacks effective {permission_type} permission for {doctype}",
            )
    finally:
        frappe.set_user(current_user)


def load_tmp_module(module_name):
    spec = importlib.util.spec_from_file_location(module_name, f"/tmp/{module_name}.py")
    require(spec and spec.loader, f"Missing validation helper module: {module_name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def delete_stock_entries(filters):
    for entry_name in frappe.get_all("Stock Entry", filters=filters, pluck="name"):
        entry = frappe.get_doc("Stock Entry", entry_name)
        if entry.docstatus == 1:
            entry.cancel()
        frappe.delete_doc("Stock Entry", entry.name, ignore_permissions=True, force=True)


def portal_list_route(route):
    return route if route.endswith("/list") else f"{route}/list"


def main():
    require(frappe.is_setup_complete(), "Setup wizard is not marked complete")

    system_settings = frappe.get_single("System Settings")
    require(system_settings.country == REQUIRED_COUNTRY, f"Wrong system country: {system_settings.country}")
    require(system_settings.currency == REQUIRED_CURRENCY, f"Wrong system currency: {system_settings.currency}")
    require(system_settings.language == REQUIRED_LANGUAGE, f"Wrong system language: {system_settings.language}")
    require(system_settings.time_zone == REQUIRED_TIME_ZONE, f"Wrong system time zone: {system_settings.time_zone}")

    company = frappe.get_doc("Company", "3pl")
    require(company.country == REQUIRED_COUNTRY, f"Wrong company country: {company.country}")
    require(company.default_currency == REQUIRED_CURRENCY, f"Wrong company currency: {company.default_currency}")
    require(frappe.db.get_default("country") == REQUIRED_COUNTRY, f"Wrong default country: {frappe.db.get_default('country')}")
    require(frappe.db.get_default("currency") == REQUIRED_CURRENCY, f"Wrong default currency: {frappe.db.get_default('currency')}")
    require(
        frappe.db.count("Account", {"company": "3pl", "account_currency": ("!=", REQUIRED_CURRENCY)}) == 0,
        "Company has accounts with non-EUR currency",
    )
    require(
        frappe.db.exists(
            "Email Account",
            {
                "email_id": REQUIRED_PLACEHOLDER_EMAIL,
                "enable_outgoing": 1,
                "default_outgoing": 1,
            },
        ),
        "Missing placeholder default outgoing Email Account",
    )

    for workspace in REQUIRED_WORKSPACES:
        require(frappe.db.exists("Workspace", workspace), f"Missing Workspace: {workspace}")
        doc = frappe.get_doc("Workspace", workspace)
        require(doc.public == 1, f"Workspace is not public: {workspace}")
        require(doc.is_hidden == 0, f"Workspace is hidden: {workspace}")

    for doctype in REQUIRED_DOCTYPES:
        require(frappe.db.exists("DocType", doctype), f"Missing DocType: {doctype}")
        require(frappe.get_meta(doctype).module == "Website", f"Custom DocType must use Website module for portal list compatibility: {doctype}")

    container_meta = frappe.get_meta("Three PL Container")
    container_fields = {field.fieldname for field in container_meta.fields}
    require(container_fields >= REQUIRED_CONTAINER_FIELDS, "Three PL Container misses Handling Unit fields")
    status_field = container_meta.get_field("status")
    require(status_field, "Three PL Container misses status field")
    status_options = set((status_field.options or "").splitlines())
    require(status_options >= REQUIRED_CONTAINER_STATUSES, "Three PL Container misses Handling Unit statuses")
    movement_meta = frappe.get_meta("Three PL Container Movement")
    movement_fields = {field.fieldname for field in movement_meta.fields}
    require(movement_fields >= REQUIRED_CONTAINER_MOVEMENT_FIELDS, "Three PL Container Movement misses required fields")
    movement_type_field = movement_meta.get_field("movement_type")
    require(movement_type_field, "Three PL Container Movement misses movement_type field")
    require(set((movement_type_field.options or "").splitlines()) >= REQUIRED_CONTAINER_MOVEMENT_TYPES, "Three PL Container Movement misses required movement types")
    move_meta = frappe.get_meta("Three PL Container Move")
    move_fields = {field.fieldname for field in move_meta.fields}
    require(move_fields >= REQUIRED_CONTAINER_MOVE_FIELDS, "Three PL Container Move misses required fields")
    repack_meta = frappe.get_meta("Three PL Container Repack")
    repack_fields = {field.fieldname for field in repack_meta.fields}
    require(repack_fields >= REQUIRED_CONTAINER_REPACK_FIELDS, "Three PL Container Repack misses required fields")
    correction_meta = frappe.get_meta("Three PL Warehouse Correction")
    correction_fields = {field.fieldname for field in correction_meta.fields}
    require(correction_fields >= REQUIRED_WAREHOUSE_CORRECTION_FIELDS, "Three PL Warehouse Correction misses required fields")
    stocktake_meta = frappe.get_meta("Three PL Stocktake")
    stocktake_fields = {field.fieldname for field in stocktake_meta.fields}
    require(stocktake_fields >= REQUIRED_STOCKTAKE_FIELDS, "Three PL Stocktake misses required fields")
    balance_snapshot_meta = frappe.get_meta("Three PL Inventory Balance Snapshot")
    balance_snapshot_fields = {field.fieldname for field in balance_snapshot_meta.fields}
    require(
        balance_snapshot_fields >= REQUIRED_INVENTORY_BALANCE_SNAPSHOT_FIELDS,
        "Three PL Inventory Balance Snapshot misses required fields",
    )

    for report in REQUIRED_REPORTS:
        require(frappe.db.exists("Report", report), f"Missing Report: {report}")
        report_doc = frappe.get_doc("Report", report)
        if report_doc.report_type == "Query Report":
            frappe.db.sql(report_doc.query)

    for route, label in (
        ("warehouse/receiving", "receiving"),
        ("warehouse/correction", "correction"),
        ("warehouse/correction-review", "correction review"),
        ("warehouse/stocktake", "stocktake"),
        ("warehouse/container-move", "container move"),
        ("warehouse/putaway", "putaway"),
        ("warehouse/repack", "repack"),
        ("warehouse/picking-confirmation", "picking confirmation"),
        ("warehouse/outbound-fulfillment", "outbound fulfillment"),
    ):
        scanner_page_name = frappe.db.get_value("Web Page", {"route": route}, "name")
        require(scanner_page_name, f"Missing scanner {label} Web Page")
        scanner_page = frappe.get_doc("Web Page", scanner_page_name)
        require(scanner_page.published == 1, f"Scanner {label} Web Page is not published")
        if scanner_page.meta.has_field("login_required"):
            require(scanner_page.login_required == 1, f"Scanner {label} Web Page must require login")

    for custom_field in REQUIRED_CUSTOM_FIELDS:
        require(frappe.db.exists("Custom Field", custom_field), f"Missing Custom Field: {custom_field}")

    for warehouse in REQUIRED_WAREHOUSES:
        require(frappe.db.exists("Warehouse", warehouse), f"Missing Warehouse: {warehouse}")
    require(frappe.get_meta("Warehouse").allow_rename == 0, "Warehouse location rename must stay disabled for normal warehouse roles")
    stock_entry_meta = frappe.get_meta("Stock Entry")
    for fieldname in ("client", "inbound_shipment_notice", "scanned_location", "container_code"):
        field = stock_entry_meta.get_field(fieldname)
        require(field and field.mandatory_depends_on == "eval:doc.warehouse_flow=='Inbound Receipt'", f"Stock Entry {fieldname} must be mandatory for inbound receipts")

    for user, roles in REQUIRED_USERS.items():
        require(frappe.db.exists("User", user), f"Missing User: {user}")
        doc = frappe.get_doc("User", user)
        user_roles = {row.role for row in doc.roles}
        require(doc.enabled == 1, f"User is disabled: {user}")
        expected_module_profile = None if user in {BUSINESS_OWNER_USER, CLIENT_PORTAL_USER} else "Warehouse Only"
        require(doc.module_profile == expected_module_profile, f"Wrong module profile for {user}: {doc.module_profile}")
        expected_workspace = None if user == CLIENT_PORTAL_USER else "3PL Warehouse"
        require(doc.default_workspace == expected_workspace, f"Wrong default workspace for {user}: {doc.default_workspace}")
        if doc.meta.has_field("default_app"):
            require(doc.default_app is None, f"Wrong default app for {user}: {doc.default_app}")
        expected_user_type = "Website User" if user == CLIENT_PORTAL_USER else "System User"
        require(doc.user_type == expected_user_type, f"Wrong user_type for {user}: {doc.user_type}")
        for role in roles:
            require(role in user_roles, f"Missing role for {user}: {role}")

    for role in ("Stock User", "Stock Manager", "3PL Warehouse User", "3PL Warehouse Manager"):
        require(frappe.db.get_value("Role", role, "home_page") == "app/3pl-warehouse", f"Wrong home_page for role: {role}")

    for role in ("3PL Warehouse User", "3PL Warehouse Manager"):
        require(
            frappe.db.exists(
                "Custom DocPerm",
                {"parent": "Page", "role": role, "permlevel": 0, "if_owner": 0, "read": 1},
            ),
            f"Missing Page read permission for role: {role}",
        )

    for role_name in ("3PL Client", "Customer"):
        client_role = frappe.get_doc("Role", role_name)
        if client_role.meta.has_field("desk_access"):
            require(client_role.desk_access == 0, f"{role_name} role must not have Desk access")
        require(client_role.home_page == CLIENT_PORTAL_HOME, f"Wrong {role_name} home_page: {client_role.home_page}")

    for form in CLIENT_PORTAL_FORMS:
        require(
            frappe.db.exists("Portal Menu Item", {"title": form["menu_title"], "route": portal_list_route(form["route"]), "role": "3PL Client", "enabled": 1}),
            f"Missing client portal menu item: {form['menu_title']}",
        )
    portal_settings = frappe.get_single("Portal Settings")
    require(portal_settings.default_portal_home == CLIENT_PORTAL_HOME, f"Wrong default portal home: {portal_settings.default_portal_home}")
    for title, (route, expected_fields) in CLIENT_PORTAL_ROUTES.items():
        web_form_name = frappe.db.get_value("Web Form", {"route": route}, "name")
        require(web_form_name, f"Missing client Web Form: {title}")
        web_form = frappe.get_doc("Web Form", web_form_name)
        require(web_form.title == title, f"Wrong client Web Form title: {web_form.title}")
        require(web_form.module == "Website", f"Client Web Form must use Website module to avoid ERPNext transaction list filters: {title}")
        require(web_form.login_required == 1, f"Client Web Form must require login: {title}")
        require(web_form.apply_document_permissions == 0, f"Client Web Form must use owner-based portal permissions: {title}")
        require(web_form.hide_navbar == 1, f"Client Web Form must hide standard navbar: {title}")
        require(web_form.hide_footer == 1, f"Client Web Form must hide standard footer: {title}")
        require({row.fieldname for row in web_form.web_form_fields} >= expected_fields, f"Client Web Form misses required fields: {title}")
        require("Receiving Notices" in web_form.introduction_text, f"Client Web Form misses portal nav: {title}")
        customer_field = next((row for row in web_form.web_form_fields if row.fieldname == "customer"), None)
        require(customer_field, f"Client Web Form misses customer field: {title}")
        require(customer_field.hidden == 1, f"Client Web Form customer field must be hidden: {title}")
        require(customer_field.default == CLIENT_PORTAL_CUSTOMER, f"Client Web Form customer field has wrong default: {title}")
        for field in web_form.web_form_fields:
            if field.fieldtype == "Link":
                require(field.allow_read_on_all_link_options == 1, f"Client Web Form Link field must not be owner-filtered: {title}.{field.fieldname}")

    require(
        frappe.db.exists("User Permission", {"user": CLIENT_PORTAL_USER, "allow": "Customer", "for_value": CLIENT_PORTAL_CUSTOMER}),
        "Missing client Customer User Permission",
    )
    require(
        frappe.db.exists("Contact", {"user": CLIENT_PORTAL_USER}),
        "Missing client Contact link",
    )

    for doctype in ("Inbound Shipment Notice", "Three PL Container", "Three PL Container Move", "Three PL Container Movement", "Three PL Container Repack", "Three PL Warehouse Correction", "Three PL Stocktake"):
        require_role_perm(doctype, "3PL Warehouse User", read=1, write=1, create=1)
        require_role_perm(doctype, "3PL Warehouse Manager", read=1, write=1, create=1, delete=1)
        require_role_perm(doctype, "System Manager", read=1, write=1, create=1, delete=1)
    require_role_perm("Three PL Inventory Balance Snapshot", "3PL Warehouse User", read=1)
    require_role_perm("Three PL Inventory Balance Snapshot", "3PL Warehouse Manager", read=1, write=1, create=1, delete=1)
    require_role_perm("Three PL Inventory Balance Snapshot", "System Manager", read=1, write=1, create=1, delete=1)
    require_role_perm("Inbound Shipment Notice", "3PL Client", read=1, write=1, create=1)
    require_role_perm("Inbound Shipment Notice Item", "3PL Client", read=1, write=1, create=1)
    require_role_perm("Inbound Shipment Discrepancy", "3PL Client", read=1)
    require_role_perm("Customer", "3PL Client", read=1)
    require_role_perm("Item", "3PL Client", read=1)
    require_role_perm("UOM", "3PL Client", read=1)
    require_role_perm("Warehouse", "3PL Client", read=1)
    require_role_perm("Web Form", "3PL Client", read=1)
    require_role_perm("Three PL Container", "3PL Client", read=1)
    require_role_perm("Three PL Container Item", "3PL Client", read=1)
    require_role_perm("Three PL Container Move", "3PL Client", read=1)
    require_role_perm("Three PL Container Movement", "3PL Client", read=1)
    require_role_perm("Three PL Container Repack", "3PL Client", read=1)
    require_role_perm("Three PL Warehouse Correction", "3PL Client", read=1)
    require_role_perm("Three PL Stocktake", "3PL Client", read=1)
    require_role_perm("Three PL Repack Source", "3PL Client", read=1)
    require_role_perm("Three PL Repack Item", "3PL Client", read=1)
    require_role_perm("Three PL Inventory Snapshot", "3PL Client", read=1)
    require_role_perm("Three PL Inventory Balance Snapshot", "3PL Client", read=1)
    require_role_perm("Three PL Shipment Request", "3PL Client", read=1, write=1, create=1)
    require_role_perm("Three PL Shipment Request Item", "3PL Client", read=1, write=1, create=1)
    require_role_perm("Three PL Client Instruction", "3PL Client", read=1, write=1, create=1)

    for doctype in ("Warehouse", "Item", "Inbound Shipment Notice", "Three PL Container", "Three PL Container Move", "Three PL Warehouse Correction", "Three PL Stocktake"):
        require_effective_perm(WAREHOUSE_MANAGER_USER, doctype, "read", "create")
    for doctype in ("Warehouse", "Inbound Shipment Notice", "Three PL Container", "Three PL Container Move"):
        require_effective_perm(WAREHOUSE_OPERATOR_USER, doctype, "read")
    for doctype in ("Inbound Shipment Notice", "Three PL Container", "Three PL Container Move", "Three PL Warehouse Correction", "Three PL Stocktake"):
        require_effective_perm(WAREHOUSE_OPERATOR_USER, doctype, "create")
    for doctype in ("Warehouse", "Item", "Item Group", "UOM", "Three PL Container", "Inbound Shipment Notice"):
        require_effective_perm(BUSINESS_OWNER_USER, doctype, "read", "create")

    owner_roles = [row.role for row in frappe.get_doc("User", BUSINESS_OWNER_USER).roles]
    for doctype in ("Warehouse", "Item", "Item Group", "UOM"):
        permissions = []
        for table in ("DocPerm", "Custom DocPerm"):
            permissions.extend(
                frappe.get_all(
                    table,
                    filters={"parent": doctype, "role": ("in", owner_roles)},
                    fields=["read", "write", "create", "delete"],
                )
            )
        require(any(row.read and row.write and row.create for row in permissions), f"Owner cannot create/write {doctype}")

    notice_name = frappe.db.get_value("Inbound Shipment Notice", {"external_reference": "ASN-ALPHA-001"})
    require(notice_name, "Missing demo ASN")
    require(frappe.db.exists("Stock Entry", {"client": "Demo Client Alpha", "warehouse_flow": "Inbound Receipt"}), "Missing demo Stock Entry")
    for customer in ("Demo Client Alpha", "Demo Client Beta"):
        require(frappe.db.get_value("Customer", customer, "territory") == REQUIRED_COUNTRY, f"Wrong customer territory: {customer}")

    expected_items = {item["item_code"]: (item["client"], item["client_sku"]) for item in DEMO_ITEMS}
    for item_code, (client, client_sku) in expected_items.items():
        require(frappe.db.exists("Item", item_code), f"Missing demo Item: {item_code}")
        require(frappe.db.get_value("Item", item_code, "owner_client") == client, f"Wrong owner_client for {item_code}")
        require(frappe.db.get_value("Item", item_code, "client_sku") == client_sku, f"Wrong client_sku for {item_code}")

    container = frappe.get_doc("Three PL Container", "BOX-ALPHA-001")
    require(container.client == "Demo Client Alpha", "Demo container has wrong client")
    require(container.container_type == "Box", "Demo container has wrong container type")
    require(container.current_warehouse == "Temporary Receiving - 3", "Demo container has wrong location")
    require(container.inbound_shipment_notice == notice_name, "Demo container is not linked to demo ASN")
    require(any(row.item_code == "SKU-ALPHA-002" and row.qty == 24 for row in container.items), "Demo container misses expected item row")
    require(
        frappe.db.exists(
            "Three PL Container Movement",
            {"container_code": "BOX-ALPHA-001", "movement_type": "Received", "to_warehouse": "Temporary Receiving - 3"},
        ),
        "Missing demo received container movement",
    )
    require(
        frappe.db.exists(
            "Three PL Container Movement",
            {"container_code": "BOX-ALPHA-002", "movement_type": "Putaway", "to_warehouse": "Aisle A - 3"},
        ),
        "Missing demo putaway container movement",
    )
    move_name = frappe.db.get_value("Three PL Container Move", {"operation_reference": "MOVE-ALPHA-001"}, "name")
    require(move_name, "Missing demo container move operation")
    move = frappe.get_doc("Three PL Container Move", move_name)
    require(move.status == "Applied", "Demo container move is not applied")
    require(move.container_code == "BOX-ALPHA-002", "Demo container move has wrong container")
    require(move.from_warehouse == "Temporary Receiving - 3" and move.to_warehouse == "Aisle A - 3", "Demo container move has wrong locations")
    require(move.movement and frappe.db.exists("Three PL Container Movement", move.movement), "Demo container move is not linked to movement history")
    storage_container = frappe.get_doc("Three PL Container", "BOX-ALPHA-002")
    require(storage_container.current_warehouse == "Aisle A - 3", "Applied container move did not update container location")
    require(storage_container.status in {"Stored", "Picking"}, "Applied container move did not update container status")
    repack_name = frappe.db.get_value("Three PL Container Repack", {"operation_reference": "REPACK-ALPHA-001"}, "name")
    require(repack_name, "Missing demo container repack operation")
    repack = frappe.get_doc("Three PL Container Repack", repack_name)
    require(repack.status == "Applied", "Demo container repack is not applied")
    require(repack.target_container == "BOX-ALPHA-005", "Demo container repack has wrong target container")
    require(repack.movement and frappe.db.exists("Three PL Container Movement", repack.movement), "Demo container repack is not linked to movement history")
    for source_name in ("BOX-ALPHA-003", "BOX-ALPHA-004"):
        source = frappe.get_doc("Three PL Container", source_name)
        require(source.status == "Replaced", f"Demo source container is not replaced: {source_name}")
        require(source.replaced_by == "BOX-ALPHA-005", f"Demo source container has wrong replacement: {source_name}")
    target = frappe.get_doc("Three PL Container", "BOX-ALPHA-005")
    require(target.status in {"Stored", "Picking"}, "Demo repack target is not stored or allocated for picking")
    require(target.current_warehouse == "Aisle A - 3", "Demo repack target has wrong location")
    require(any(row.item_code == "SKU-ALPHA-003" and row.qty == 18 for row in target.items), "Demo repack target misses expected contents")

    notice = frappe.get_doc("Inbound Shipment Notice", notice_name)
    require(
        any(row.discrepancy_type == "Quantity Difference" and row.item_code == "SKU-ALPHA-002" and row.variance_qty == -1 for row in notice.discrepancies),
        "Demo ASN misses quantity discrepancy",
    )
    require(
        frappe.db.exists(
            "Three PL Inventory Snapshot",
            {"customer": "Demo Client Alpha", "item_code": "SKU-ALPHA-001", "container_code": "BOX-ALPHA-001", "warehouse": "Temporary Receiving - 3", "status": "Receiving"},
        ),
        "Missing synced receiving inventory snapshot",
    )
    require(
        frappe.db.exists(
            "Three PL Inventory Snapshot",
            {"customer": "Demo Client Alpha", "item_code": "SKU-ALPHA-003", "container_code": "BOX-ALPHA-005", "warehouse": "Aisle A - 3", "status": ("in", ["Available", "Allocated"])},
        ),
        "Missing synced repack target inventory snapshot",
    )
    summary_rows = frappe.db.sql(
        """
        select sum(qty)
        from `tabThree PL Inventory Snapshot`
        where customer = 'Demo Client Alpha'
          and item_code = 'SKU-ALPHA-003'
        """,
        as_list=True,
    )
    require(summary_rows and summary_rows[0][0] == 36, "Wrong Alpha SKU-ALPHA-003 inventory summary")
    allocated_rows = frappe.db.sql(
        """
        select sum(qty)
        from `tabThree PL Inventory Snapshot`
        where customer = 'Demo Client Alpha'
          and item_code = 'SKU-ALPHA-003'
          and status = 'Allocated'
        """,
        as_list=True,
    )
    require(allocated_rows and allocated_rows[0][0] > 0, "Wrong Alpha SKU-ALPHA-003 allocated inventory summary")
    require(
        not frappe.db.exists("Three PL Inventory Snapshot", {"container_code": ("in", ["BOX-ALPHA-003", "BOX-ALPHA-004"])}),
        "Stale source container inventory snapshots were not removed",
    )
    require(frappe.db.exists("Three PL Inventory Snapshot", {"customer": "Demo Client Beta", "item_code": "SKU-BETA-001"}), "Missing demo beta inventory snapshot")
    require(
        frappe.db.exists(
            "Three PL Inventory Balance Snapshot",
            {
                "snapshot_date": nowdate(),
                "customer": "Demo Client Alpha",
                "item_code": "SKU-ALPHA-001",
                "container_code": "BOX-ALPHA-001",
            },
        ),
        "Missing daily Alpha inventory balance snapshot",
    )
    require(
        frappe.db.exists(
            "Three PL Inventory Balance Snapshot",
            {
                "snapshot_date": nowdate(),
                "customer": "Demo Client Beta",
                "item_code": "SKU-BETA-001",
            },
        ),
        "Missing daily Beta inventory balance snapshot",
    )
    require(
        frappe.db.count("Three PL Container Movement", {"client": "Demo Client Alpha"}) > 0,
        "Warehouse operation turnover has no Alpha movement source rows",
    )
    daily_summary_rows = frappe.db.sql(
        """
        select sum(qty)
        from `tabThree PL Inventory Balance Snapshot`
        where snapshot_date = %s
          and customer = 'Demo Client Alpha'
          and item_code = 'SKU-ALPHA-003'
        """,
        (nowdate(),),
        as_list=True,
    )
    require(daily_summary_rows and daily_summary_rows[0][0] == 36, "Wrong Alpha SKU-ALPHA-003 daily inventory balance")
    require(frappe.db.exists("Inbound Shipment Notice", {"customer": "Demo Client Beta", "external_reference": "ASN-BETA-001"}), "Missing demo beta ASN")
    demo_shipment_name = frappe.db.get_value("Three PL Shipment Request", {"customer": "Demo Client Alpha", "external_reference": "SHIP-ALPHA-001"}, "name")
    require(demo_shipment_name, "Missing demo shipment request")
    demo_pick_list_name = frappe.db.get_value("Pick List", {"shipment_request": demo_shipment_name}, "name")
    require(demo_pick_list_name, "Demo shipment request did not create a Pick List")
    demo_pick_list = frappe.get_doc("Pick List", demo_pick_list_name)
    require(demo_pick_list.client == "Demo Client Alpha", "Demo Pick List has wrong client")
    require(demo_pick_list.shipment_reference == "SHIP-ALPHA-001", "Demo Pick List has wrong shipment reference")
    require(
        any(row.item_code == "SKU-ALPHA-003" and row.qty == 1 and row.container_code for row in demo_pick_list.locations),
        "Demo Pick List misses allocated item/location row",
    )
    require(frappe.db.exists("Three PL Client Instruction", {"customer": "Demo Client Alpha", "receiving_notice": notice_name}), "Missing demo client discrepancy instruction")

    validate_receiving_sync()
    validate_shipment_sync()
    validate_warehouse_correction()
    validate_warehouse_correction_stock_posting()
    validate_stocktake()
    validate_putaway_operation()
    validate_picking_confirmation()
    validate_outbound_fulfillment()
    validate_client_portal_permissions()

    print("Site validation passed")


def cleanup_receiving_validation_docs():
    frappe.set_user("Administrator")
    notice_names = frappe.get_all("Inbound Shipment Notice", filters={"external_reference": ("like", "RECV-VALIDATION-%")}, pluck="name")
    for entry_name in frappe.get_all("Stock Entry", filters={"inbound_shipment_notice": ("in", notice_names or [""] )}, pluck="name"):
        entry = frappe.get_doc("Stock Entry", entry_name)
        if entry.docstatus == 1:
            entry.cancel()
        frappe.delete_doc("Stock Entry", entry.name, ignore_permissions=True, force=True)
    for notice_name in notice_names:
        frappe.delete_doc("Inbound Shipment Notice", notice_name, ignore_permissions=True, force=True)


def validate_receiving_sync():
    from sync_receiving_notices import sync_notice

    cleanup_receiving_validation_docs()
    frappe.set_user("Administrator")

    reference = "RECV-VALIDATION-ALPHA"
    notice = frappe.get_doc(
        {
            "doctype": "Inbound Shipment Notice",
            "customer": "Demo Client Alpha",
            "external_reference": reference,
            "expected_arrival_date": nowdate(),
            "temporary_warehouse": "Temporary Receiving - 3",
            "items": [
                {
                    "item_code": "SKU-ALPHA-001",
                    "client_sku": "ALPHA-001",
                    "expected_qty": 5,
                    "uom": "Nos",
                }
            ],
        }
    )
    notice.insert(ignore_permissions=True)

    entry = frappe.get_doc(
        {
            "doctype": "Stock Entry",
            "stock_entry_type": "3PL Inbound Receipt",
            "purpose": "Material Receipt",
            "company": "3pl",
            "posting_date": nowdate(),
            "client": "Demo Client Alpha",
            "inbound_shipment_notice": notice.name,
            "warehouse_flow": "Inbound Receipt",
            "scanned_location": "Temporary Receiving - 3",
            "container_code": "BOX-ALPHA-001",
            "items": [
                {
                    "item_code": "SKU-ALPHA-001",
                    "qty": 4,
                    "t_warehouse": "Temporary Receiving - 3",
                    "uom": "Nos",
                    "stock_uom": "Nos",
                    "conversion_factor": 1,
                    "basic_rate": 1,
                    "scanned_location": "Temporary Receiving - 3",
                    "container_code": "BOX-ALPHA-001",
                }
            ],
        }
    )
    entry.insert(ignore_permissions=True)
    entry.submit()

    sync_notice(notice.name)
    notice.reload()
    require(notice.status == "Discrepancy Review", f"Receiving validation notice has wrong status: {notice.status}")
    require(notice.items[0].received_qty == 4, "Receiving validation did not update received_qty")
    require(notice.items[0].variance_qty == -1, "Receiving validation did not update variance_qty")
    require(
        any(row.auto_generated and row.discrepancy_type == "Quantity Difference" and row.variance_qty == -1 for row in notice.discrepancies),
        "Receiving validation did not create auto discrepancy",
    )

    cleanup_receiving_validation_docs()


def cleanup_shipment_validation_docs():
    frappe.set_user("Administrator")
    request_names = frappe.get_all("Three PL Shipment Request", filters={"external_reference": ("like", "SHIP-VALIDATION-%")}, pluck="name")
    for pick_name in frappe.get_all("Pick List", filters={"shipment_request": ("in", request_names or [""])}, pluck="name"):
        pick_list = frappe.get_doc("Pick List", pick_name)
        if pick_list.docstatus == 1:
            pick_list.cancel()
        frappe.delete_doc("Pick List", pick_list.name, ignore_permissions=True, force=True)
    for request_name in request_names:
        frappe.delete_doc("Three PL Shipment Request", request_name, ignore_permissions=True, force=True)


def validate_shipment_sync():
    from sync_inventory_snapshots import sync_inventory_snapshots
    from sync_shipment_requests import sync_request

    cleanup_shipment_validation_docs()
    frappe.set_user("Administrator")

    container = frappe.get_doc("Three PL Container", "BOX-ALPHA-005")
    container.status = "Stored"
    container.save(ignore_permissions=True)
    sync_inventory_snapshots()

    request = frappe.get_doc(
        {
            "doctype": "Three PL Shipment Request",
            "customer": "Demo Client Alpha",
            "external_reference": "SHIP-VALIDATION-ALPHA",
            "requested_ship_date": nowdate(),
            "destination_name": "Shipment Validation",
            "destination_address": "Validation Address",
            "portal_source": 1,
            "items": [
                {
                    "item_code": "SKU-ALPHA-003",
                    "client_sku": "ALPHA-003",
                    "qty": 2,
                    "uom": "Nos",
                }
            ],
        }
    )
    request.insert(ignore_permissions=True)

    pick_list_name = sync_request(request.name)
    require(pick_list_name, "Shipment validation did not create Pick List")
    request.reload()
    pick_list = frappe.get_doc("Pick List", pick_list_name)
    require(request.status == "Picking", f"Shipment validation request has wrong status: {request.status}")
    require(pick_list.purpose == "Delivery", f"Shipment validation Pick List has wrong purpose: {pick_list.purpose}")
    require(pick_list.client == "Demo Client Alpha", "Shipment validation Pick List has wrong client")
    require(pick_list.shipment_request == request.name, "Shipment validation Pick List is not linked to request")
    require(
        any(row.item_code == "SKU-ALPHA-003" and row.qty == 2 and row.warehouse == "Aisle A - 3" and row.container_code for row in pick_list.locations),
        "Shipment validation Pick List misses allocated stock row",
    )
    container.reload()
    require(container.status == "Picking", f"Shipment validation container has wrong status: {container.status}")
    require(
        frappe.db.exists(
            "Three PL Container Movement",
            {
                "container_code": container.name,
                "movement_type": "Picking",
                "reference_doctype": "Pick List",
                "reference_name": pick_list.name,
            },
        ),
        "Shipment validation did not create picking movement",
    )

    cleanup_shipment_validation_docs()


def cleanup_warehouse_correction_validation_docs():
    frappe.set_user("Administrator")
    correction_names = frappe.get_all(
        "Three PL Warehouse Correction",
        filters={"container_code": ("in", ["BOX-CORRECTION-VALIDATION", "BOX-CORRECTION-POSTING-VALIDATION"])},
        pluck="name",
    )
    for correction_name in correction_names:
        delete_stock_entries({"warehouse_correction": correction_name})
    for movement_name in frappe.get_all(
        "Three PL Container Movement",
        filters={"container_code": ("in", ["BOX-CORRECTION-VALIDATION", "BOX-CORRECTION-POSTING-VALIDATION"])},
        pluck="name",
    ):
        frappe.delete_doc("Three PL Container Movement", movement_name, ignore_permissions=True, force=True)
    for correction_name in frappe.get_all(
        "Three PL Warehouse Correction",
        filters={"container_code": ("in", ["BOX-CORRECTION-VALIDATION", "BOX-CORRECTION-POSTING-VALIDATION"])},
        pluck="name",
    ):
        frappe.delete_doc("Three PL Warehouse Correction", correction_name, ignore_permissions=True, force=True)
    for container_name in ("BOX-CORRECTION-VALIDATION", "BOX-CORRECTION-POSTING-VALIDATION"):
        if frappe.db.exists("Three PL Container", container_name):
            frappe.delete_doc("Three PL Container", container_name, ignore_permissions=True, force=True)


def validate_warehouse_correction():
    cleanup_warehouse_correction_validation_docs()
    frappe.set_user("Administrator")

    container = frappe.get_doc(
        {
            "doctype": "Three PL Container",
            "container_code": "BOX-CORRECTION-VALIDATION",
            "barcode": "BOX-CORRECTION-VALIDATION",
            "container_type": "Box",
            "client": "Demo Client Alpha",
            "current_warehouse": "Aisle B - 3",
            "status": "Stored",
            "items": [
                {
                    "item_code": "SKU-ALPHA-001",
                    "client_sku": "ALPHA-001",
                    "qty": 5,
                    "uom": "Nos",
                    "condition_status": "OK",
                }
            ],
        }
    )
    container.insert(ignore_permissions=True)

    frappe.set_user(WAREHOUSE_MANAGER_USER)
    container = frappe.get_doc("Three PL Container", "BOX-CORRECTION-VALIDATION")
    expected_qty = container.items[0].qty
    actual_qty = 4
    operation_time = now_datetime()
    container.items[0].qty = actual_qty
    container.items[0].condition_status = "Hold"
    container.status = "In Verification"
    container.last_moved_at = operation_time
    container.save()

    correction = frappe.get_doc(
        {
            "doctype": "Three PL Warehouse Correction",
            "operation_reference": "CORR-VALIDATION-ALPHA",
            "operation_datetime": operation_time,
            "status": "Draft",
            "correction_type": "Quantity Count",
            "client": container.client,
            "container_code": container.name,
            "warehouse": container.current_warehouse,
            "item_code": "SKU-ALPHA-001",
            "client_sku": "ALPHA-001",
            "uom": "Nos",
            "expected_qty": expected_qty,
            "actual_qty": actual_qty,
            "qty_delta": actual_qty - expected_qty,
            "condition_status": "Hold",
            "notes": "Validation warehouse correction.",
        }
    )
    correction.insert()
    movement = frappe.get_doc(
        {
            "doctype": "Three PL Container Movement",
            "movement_datetime": operation_time,
            "container_code": container.name,
            "client": container.client,
            "movement_type": "Adjusted",
            "from_warehouse": container.current_warehouse,
            "to_warehouse": container.current_warehouse,
            "reference_doctype": "Three PL Warehouse Correction",
            "reference_name": correction.name,
            "notes": "Validation warehouse correction movement.",
        }
    )
    movement.insert()
    correction.status = "Applied"
    correction.movement = movement.name
    correction.save()

    frappe.set_user("Administrator")
    container.reload()
    correction.reload()
    require(container.status == "In Verification", "Warehouse correction did not hold container")
    require(container.items[0].qty == actual_qty, "Warehouse correction did not update container quantity")
    require(correction.status == "Applied", "Warehouse correction was not applied")
    require(correction.qty_delta == -1, "Warehouse correction has wrong delta")
    require(correction.movement == movement.name, "Warehouse correction is not linked to movement")
    require(
        frappe.db.exists(
            "Three PL Container Movement",
            {
                "container_code": container.name,
                "movement_type": "Adjusted",
                "reference_doctype": "Three PL Warehouse Correction",
                "reference_name": correction.name,
            },
        ),
        "Warehouse correction did not create adjustment movement",
    )

    cleanup_warehouse_correction_validation_docs()


def validate_warehouse_correction_stock_posting():
    cleanup_warehouse_correction_validation_docs()
    frappe.set_user("Administrator")

    container = frappe.get_doc(
        {
            "doctype": "Three PL Container",
            "container_code": "BOX-CORRECTION-POSTING-VALIDATION",
            "barcode": "BOX-CORRECTION-POSTING-VALIDATION",
            "container_type": "Box",
            "client": "Demo Client Alpha",
            "current_warehouse": "Aisle B - 3",
            "status": "Stored",
            "items": [
                {
                    "item_code": "SKU-ALPHA-001",
                    "client_sku": "ALPHA-001",
                    "qty": 2,
                    "uom": "Nos",
                    "condition_status": "OK",
                }
            ],
        }
    )
    container.insert(ignore_permissions=True)

    operation_time = now_datetime()
    container.items[0].qty = 3
    container.last_moved_at = operation_time
    container.save(ignore_permissions=True)

    correction = frappe.get_doc(
        {
            "doctype": "Three PL Warehouse Correction",
            "operation_reference": "CORR-POSTING-VALIDATION",
            "operation_datetime": operation_time,
            "status": "Applied",
            "correction_type": "Quantity Count",
            "client": container.client,
            "container_code": container.name,
            "warehouse": container.current_warehouse,
            "item_code": "SKU-ALPHA-001",
            "client_sku": "ALPHA-001",
            "uom": "Nos",
            "expected_qty": 2,
            "actual_qty": 3,
            "qty_delta": 1,
            "condition_status": "OK",
            "notes": "Validation warehouse correction stock posting.",
        }
    )
    correction.insert(ignore_permissions=True)
    frappe.db.commit()

    processor = load_tmp_module("apply_warehouse_corrections")
    entry_name = processor.apply_correction_stock_posting(correction)
    require(entry_name, "Warehouse correction did not create stock posting")

    correction.reload()
    entry = frappe.get_doc("Stock Entry", entry_name)
    require(correction.stock_posting_status == "Posted", "Warehouse correction stock posting status is not Posted")
    require(correction.stock_entry == entry.name, "Warehouse correction is not linked to Stock Entry")
    require(entry.docstatus == 1, "Warehouse correction Stock Entry is not submitted")
    require(entry.stock_entry_type == "3PL Quantity Gain", "Warehouse correction Stock Entry has wrong type")
    require(entry.purpose == "Material Receipt", "Warehouse correction Stock Entry has wrong purpose")
    require(entry.warehouse_flow == "Warehouse Correction", "Warehouse correction Stock Entry has wrong flow")
    require(entry.warehouse_correction == correction.name, "Stock Entry is not linked back to correction")
    require(entry.items[0].item_code == "SKU-ALPHA-001", "Correction Stock Entry has wrong item")
    require(entry.items[0].qty == 1, "Correction Stock Entry has wrong qty")
    require(entry.items[0].t_warehouse == "Aisle B - 3", "Correction Stock Entry has wrong target warehouse")

    cleanup_warehouse_correction_validation_docs()


def cleanup_stocktake_validation_docs():
    frappe.set_user("Administrator")
    for movement_name in frappe.get_all(
        "Three PL Container Movement",
        filters={"container_code": "BOX-STOCKTAKE-VALIDATION"},
        pluck="name",
    ):
        frappe.delete_doc("Three PL Container Movement", movement_name, ignore_permissions=True, force=True)
    for correction_name in frappe.get_all(
        "Three PL Warehouse Correction",
        filters={"container_code": "BOX-STOCKTAKE-VALIDATION"},
        pluck="name",
    ):
        frappe.delete_doc("Three PL Warehouse Correction", correction_name, ignore_permissions=True, force=True)
    for stocktake_name in frappe.get_all(
        "Three PL Stocktake",
        filters={"container_code": "BOX-STOCKTAKE-VALIDATION"},
        pluck="name",
    ):
        frappe.delete_doc("Three PL Stocktake", stocktake_name, ignore_permissions=True, force=True)
    if frappe.db.exists("Three PL Container", "BOX-STOCKTAKE-VALIDATION"):
        frappe.delete_doc("Three PL Container", "BOX-STOCKTAKE-VALIDATION", ignore_permissions=True, force=True)


def validate_stocktake():
    cleanup_stocktake_validation_docs()
    frappe.set_user("Administrator")

    container = frappe.get_doc(
        {
            "doctype": "Three PL Container",
            "container_code": "BOX-STOCKTAKE-VALIDATION",
            "barcode": "BOX-STOCKTAKE-VALIDATION",
            "container_type": "Box",
            "client": "Demo Client Alpha",
            "current_warehouse": "Aisle B - 3",
            "status": "Stored",
            "items": [
                {
                    "item_code": "SKU-ALPHA-001",
                    "client_sku": "ALPHA-001",
                    "qty": 5,
                    "uom": "Nos",
                    "condition_status": "OK",
                }
            ],
        }
    )
    container.insert(ignore_permissions=True)

    frappe.set_user(WAREHOUSE_MANAGER_USER)
    operation_time = now_datetime()
    stocktake_same = frappe.get_doc(
        {
            "doctype": "Three PL Stocktake",
            "operation_reference": "STOCKTAKE-VALIDATION-SAME",
            "operation_datetime": operation_time,
            "status": "No Difference",
            "client": "Demo Client Alpha",
            "warehouse": "Aisle B - 3",
            "container_code": "BOX-STOCKTAKE-VALIDATION",
            "item_code": "SKU-ALPHA-001",
            "client_sku": "ALPHA-001",
            "uom": "Nos",
            "expected_qty": 5,
            "counted_qty": 5,
            "qty_delta": 0,
            "condition_status": "OK",
            "notes": "Validation no-difference stocktake.",
        }
    )
    stocktake_same.insert()

    container = frappe.get_doc("Three PL Container", "BOX-STOCKTAKE-VALIDATION")
    expected_qty = container.items[0].qty
    counted_qty = 4
    container.items[0].qty = counted_qty
    container.last_moved_at = operation_time
    container.save()

    stocktake_delta = frappe.get_doc(
        {
            "doctype": "Three PL Stocktake",
            "operation_reference": "STOCKTAKE-VALIDATION-DELTA",
            "operation_datetime": operation_time,
            "status": "Draft",
            "client": container.client,
            "warehouse": container.current_warehouse,
            "container_code": container.name,
            "item_code": "SKU-ALPHA-001",
            "client_sku": "ALPHA-001",
            "uom": "Nos",
            "expected_qty": expected_qty,
            "counted_qty": counted_qty,
            "qty_delta": counted_qty - expected_qty,
            "condition_status": "OK",
            "notes": "Validation delta stocktake.",
        }
    )
    stocktake_delta.insert()
    correction = frappe.get_doc(
        {
            "doctype": "Three PL Warehouse Correction",
            "operation_reference": "CORR-STOCKTAKE-VALIDATION",
            "operation_datetime": operation_time,
            "status": "Draft",
            "correction_type": "Quantity Count",
            "client": container.client,
            "container_code": container.name,
            "warehouse": container.current_warehouse,
            "item_code": "SKU-ALPHA-001",
            "client_sku": "ALPHA-001",
            "uom": "Nos",
            "expected_qty": expected_qty,
            "actual_qty": counted_qty,
            "qty_delta": counted_qty - expected_qty,
            "condition_status": "OK",
            "source_doctype": "Three PL Stocktake",
            "source_name": stocktake_delta.name,
            "notes": "Validation stocktake correction.",
        }
    )
    correction.insert()
    movement = frappe.get_doc(
        {
            "doctype": "Three PL Container Movement",
            "movement_datetime": operation_time,
            "container_code": container.name,
            "client": container.client,
            "movement_type": "Adjusted",
            "from_warehouse": container.current_warehouse,
            "to_warehouse": container.current_warehouse,
            "reference_doctype": "Three PL Stocktake",
            "reference_name": stocktake_delta.name,
            "notes": "Validation stocktake adjustment movement.",
        }
    )
    movement.insert()
    correction.status = "Applied"
    correction.movement = movement.name
    correction.save()
    stocktake_delta.status = "Applied"
    stocktake_delta.correction = correction.name
    stocktake_delta.movement = movement.name
    stocktake_delta.save()

    frappe.set_user("Administrator")
    container.reload()
    stocktake_same.reload()
    stocktake_delta.reload()
    require(stocktake_same.status == "No Difference", "No-difference stocktake has wrong status")
    require(container.items[0].qty == counted_qty, "Stocktake did not update container quantity")
    require(stocktake_delta.status == "Applied", "Delta stocktake was not applied")
    require(stocktake_delta.qty_delta == -1, "Delta stocktake has wrong delta")
    require(stocktake_delta.correction == correction.name, "Stocktake is not linked to correction")
    require(stocktake_delta.movement == movement.name, "Stocktake is not linked to movement")
    require(
        frappe.db.exists(
            "Three PL Container Movement",
            {
                "container_code": container.name,
                "movement_type": "Adjusted",
                "reference_doctype": "Three PL Stocktake",
                "reference_name": stocktake_delta.name,
            },
        ),
        "Stocktake did not create adjustment movement",
    )

    cleanup_stocktake_validation_docs()


def cleanup_putaway_validation_docs():
    frappe.set_user("Administrator")
    for movement_name in frappe.get_all(
        "Three PL Container Movement",
        filters={"container_code": "BOX-PUTAWAY-VALIDATION"},
        pluck="name",
    ):
        frappe.delete_doc("Three PL Container Movement", movement_name, ignore_permissions=True, force=True)
    for move_name in frappe.get_all(
        "Three PL Container Move",
        filters={"container_code": "BOX-PUTAWAY-VALIDATION"},
        pluck="name",
    ):
        frappe.delete_doc("Three PL Container Move", move_name, ignore_permissions=True, force=True)
    if frappe.db.exists("Three PL Container", "BOX-PUTAWAY-VALIDATION"):
        frappe.delete_doc("Three PL Container", "BOX-PUTAWAY-VALIDATION", ignore_permissions=True, force=True)


def validate_putaway_operation():
    cleanup_putaway_validation_docs()
    frappe.set_user("Administrator")

    container = frappe.get_doc(
        {
            "doctype": "Three PL Container",
            "container_code": "BOX-PUTAWAY-VALIDATION",
            "barcode": "BOX-PUTAWAY-VALIDATION",
            "container_type": "Box",
            "client": "Demo Client Alpha",
            "current_warehouse": "Temporary Receiving - 3",
            "status": "Ready for Putaway",
            "items": [
                {
                    "item_code": "SKU-ALPHA-001",
                    "client_sku": "ALPHA-001",
                    "qty": 1,
                    "uom": "Nos",
                    "condition_status": "OK",
                }
            ],
        }
    )
    container.insert(ignore_permissions=True)

    frappe.set_user(WAREHOUSE_MANAGER_USER)
    container = frappe.get_doc("Three PL Container", "BOX-PUTAWAY-VALIDATION")
    require(container.status in {"Received", "In Verification", "Ready for Putaway"}, "Putaway validation container is not ready")
    require(container.current_warehouse != "Aisle B - 3", "Putaway validation target is already current location")
    operation_time = now_datetime()
    move = frappe.get_doc(
        {
            "doctype": "Three PL Container Move",
            "operation_reference": "PUTAWAY-VALIDATION-ALPHA",
            "operation_datetime": operation_time,
            "status": "Draft",
            "container_code": container.name,
            "client": container.client,
            "from_warehouse": container.current_warehouse,
            "to_warehouse": "Aisle B - 3",
            "notes": "Validation putaway operation.",
        }
    )
    move.insert()
    movement = frappe.get_doc(
        {
            "doctype": "Three PL Container Movement",
            "movement_datetime": operation_time,
            "container_code": container.name,
            "client": container.client,
            "movement_type": "Putaway",
            "from_warehouse": container.current_warehouse,
            "to_warehouse": "Aisle B - 3",
            "reference_doctype": "Three PL Container Move",
            "reference_name": move.name,
            "notes": "Validation putaway movement.",
        }
    )
    movement.insert()
    container.current_warehouse = "Aisle B - 3"
    container.status = "Stored"
    container.last_moved_at = operation_time
    container.save()
    move.status = "Applied"
    move.movement = movement.name
    move.save()

    frappe.set_user("Administrator")
    container.reload()
    move.reload()
    require(container.current_warehouse == "Aisle B - 3", "Putaway validation did not update container location")
    require(container.status == "Stored", "Putaway validation did not store container")
    require(move.status == "Applied", "Putaway validation did not apply move")
    require(move.movement == movement.name, "Putaway validation move is not linked to movement")
    require(
        frappe.db.exists(
            "Three PL Container Movement",
            {
                "container_code": container.name,
                "movement_type": "Putaway",
                "reference_doctype": "Three PL Container Move",
                "reference_name": move.name,
            },
        ),
        "Putaway validation did not create movement history",
    )

    cleanup_putaway_validation_docs()


def cleanup_picking_validation_docs():
    frappe.set_user("Administrator")
    reference = "PICK-VALIDATION-ALPHA"
    request_names = frappe.get_all("Three PL Shipment Request", filters={"external_reference": reference}, pluck="name")
    for movement_name in frappe.get_all(
        "Three PL Container Movement",
        filters={"container_code": "BOX-PICKING-VALIDATION"},
        pluck="name",
    ):
        frappe.delete_doc("Three PL Container Movement", movement_name, ignore_permissions=True, force=True)
    for pick_name in frappe.get_all("Pick List", filters={"shipment_request": ("in", request_names or [""])}, pluck="name"):
        pick_list = frappe.get_doc("Pick List", pick_name)
        if pick_list.docstatus == 1:
            pick_list.cancel()
        frappe.delete_doc("Pick List", pick_list.name, ignore_permissions=True, force=True)
    for request_name in request_names:
        frappe.delete_doc("Three PL Shipment Request", request_name, ignore_permissions=True, force=True)
    for snapshot_name in frappe.get_all("Three PL Inventory Snapshot", filters={"container_code": "BOX-PICKING-VALIDATION"}, pluck="name"):
        frappe.delete_doc("Three PL Inventory Snapshot", snapshot_name, ignore_permissions=True, force=True)
    if frappe.db.exists("Three PL Container", "BOX-PICKING-VALIDATION"):
        frappe.delete_doc("Three PL Container", "BOX-PICKING-VALIDATION", ignore_permissions=True, force=True)


def validate_picking_confirmation():
    from sync_inventory_snapshots import sync_inventory_snapshots
    from sync_picking_confirmations import sync_pick_list
    from sync_shipment_requests import sync_request

    cleanup_picking_validation_docs()
    frappe.set_user("Administrator")

    container = frappe.get_doc(
        {
            "doctype": "Three PL Container",
            "container_code": "BOX-PICKING-VALIDATION",
            "barcode": "BOX-PICKING-VALIDATION",
            "container_type": "Box",
            "client": "Demo Client Alpha",
            "current_warehouse": "Temporary Receiving - 3",
            "status": "Stored",
            "items": [
                {
                    "item_code": "SKU-ALPHA-001",
                    "client_sku": "ALPHA-001",
                    "qty": 2,
                    "uom": "Nos",
                    "condition_status": "OK",
                }
            ],
        }
    )
    container.insert(ignore_permissions=True)
    sync_inventory_snapshots()

    request = frappe.get_doc(
        {
            "doctype": "Three PL Shipment Request",
            "customer": "Demo Client Alpha",
            "external_reference": "PICK-VALIDATION-ALPHA",
            "requested_ship_date": nowdate(),
            "destination_name": "Picking Validation",
            "destination_address": "Validation Address",
            "portal_source": 1,
            "items": [
                {
                    "item_code": "SKU-ALPHA-001",
                    "client_sku": "ALPHA-001",
                    "qty": 2,
                    "uom": "Nos",
                }
            ],
        }
    )
    request.insert(ignore_permissions=True)

    pick_list_name = sync_request(request.name)
    require(pick_list_name, "Picking validation did not create Pick List")
    pick_list = frappe.get_doc("Pick List", pick_list_name)
    picked = False
    for row in pick_list.locations:
        if row.container_code == "BOX-PICKING-VALIDATION":
            row.picked_qty = row.stock_qty or row.qty
            picked = True
    require(picked, "Picking validation Pick List did not allocate validation container")
    pick_list.save(ignore_permissions=True)

    synced = sync_pick_list(pick_list.name)
    require("BOX-PICKING-VALIDATION" in synced, "Picking validation did not sync picked container")
    container.reload()
    require(container.status == "Picked", f"Picking validation container has wrong status: {container.status}")
    require(
        frappe.db.exists(
            "Three PL Container Movement",
            {
                "container_code": container.name,
                "movement_type": "Picked",
                "reference_doctype": "Pick List",
                "reference_name": pick_list.name,
            },
        ),
        "Picking validation did not create picked movement",
    )

    cleanup_picking_validation_docs()


def cleanup_outbound_fulfillment_validation_docs():
    frappe.set_user("Administrator")
    reference = "SHIP-FULFILLMENT-VALIDATION"
    request_names = frappe.get_all("Three PL Shipment Request", filters={"external_reference": reference}, pluck="name")
    for entry_name in frappe.get_all("Stock Entry", filters={"shipment_reference": reference}, pluck="name", order_by="creation desc"):
        entry = frappe.get_doc("Stock Entry", entry_name)
        if entry.docstatus == 1:
            entry.cancel()
        frappe.delete_doc("Stock Entry", entry.name, ignore_permissions=True, force=True)
    for movement_name in frappe.get_all(
        "Three PL Container Movement",
        filters={"container_code": "BOX-FULFILLMENT-VALIDATION"},
        pluck="name",
    ):
        frappe.delete_doc("Three PL Container Movement", movement_name, ignore_permissions=True, force=True)
    for pick_name in frappe.get_all("Pick List", filters={"shipment_request": ("in", request_names or [""])}, pluck="name"):
        pick_list = frappe.get_doc("Pick List", pick_name)
        if pick_list.docstatus == 1:
            pick_list.cancel()
        frappe.delete_doc("Pick List", pick_list.name, ignore_permissions=True, force=True)
    for request_name in request_names:
        frappe.delete_doc("Three PL Shipment Request", request_name, ignore_permissions=True, force=True)
    if frappe.db.exists("Three PL Container", "BOX-FULFILLMENT-VALIDATION"):
        frappe.delete_doc("Three PL Container", "BOX-FULFILLMENT-VALIDATION", ignore_permissions=True, force=True)


def make_fulfillment_stock_entry(request, flow, entry_type, purpose, source_warehouse, target_warehouse=None):
    entry = frappe.get_doc(
        {
            "doctype": "Stock Entry",
            "stock_entry_type": entry_type,
            "purpose": purpose,
            "company": "3pl",
            "posting_date": nowdate(),
            "client": "Demo Client Alpha",
            "shipment_request": request.name,
            "shipment_reference": request.external_reference,
            "warehouse_flow": flow,
            "container_code": "BOX-FULFILLMENT-VALIDATION",
            "items": [
                {
                    "item_code": "SKU-ALPHA-001",
                    "qty": 1,
                    "s_warehouse": source_warehouse,
                    "t_warehouse": target_warehouse,
                    "uom": "Nos",
                    "stock_uom": "Nos",
                    "conversion_factor": 1,
                    "basic_rate": 1,
                    "container_code": "BOX-FULFILLMENT-VALIDATION",
                    "scanned_location": source_warehouse,
                }
            ],
        }
    )
    entry.insert(ignore_permissions=True)
    entry.submit()
    return entry


def validate_outbound_fulfillment():
    from sync_outbound_fulfillment import sync_entry

    cleanup_outbound_fulfillment_validation_docs()
    frappe.set_user("Administrator")

    request = frappe.get_doc(
        {
            "doctype": "Three PL Shipment Request",
            "customer": "Demo Client Alpha",
            "external_reference": "SHIP-FULFILLMENT-VALIDATION",
            "requested_ship_date": nowdate(),
            "destination_name": "Fulfillment Validation",
            "destination_address": "Validation Address",
            "portal_source": 1,
            "status": "Picking",
            "items": [
                {
                    "item_code": "SKU-ALPHA-001",
                    "client_sku": "ALPHA-001",
                    "qty": 1,
                    "uom": "Nos",
                }
            ],
        }
    )
    request.insert(ignore_permissions=True)

    container = frappe.get_doc(
        {
            "doctype": "Three PL Container",
            "container_code": "BOX-FULFILLMENT-VALIDATION",
            "barcode": "BOX-FULFILLMENT-VALIDATION",
            "container_type": "Box",
            "client": "Demo Client Alpha",
            "current_warehouse": "Temporary Receiving - 3",
            "status": "Picking",
            "items": [
                {
                    "item_code": "SKU-ALPHA-001",
                    "client_sku": "ALPHA-001",
                    "qty": 1,
                    "uom": "Nos",
                    "condition_status": "OK",
                }
            ],
        }
    )
    container.insert(ignore_permissions=True)

    packing = make_fulfillment_stock_entry(
        request,
        flow="Packing",
        entry_type="3PL Packing",
        purpose="Material Transfer",
        source_warehouse="Temporary Receiving - 3",
        target_warehouse="Packing - 3",
    )
    sync_entry(packing.name)
    request.reload()
    container.reload()
    require(request.status == "Packed", f"Outbound validation request was not packed: {request.status}")
    require(container.status == "Packed", f"Outbound validation container was not packed: {container.status}")
    require(container.current_warehouse == "Packing - 3", f"Outbound validation container has wrong packing location: {container.current_warehouse}")
    require(
        frappe.db.exists(
            "Three PL Container Movement",
            {
                "container_code": container.name,
                "movement_type": "Packed",
                "reference_doctype": "Stock Entry",
                "reference_name": packing.name,
            },
        ),
        "Outbound validation did not create packing movement",
    )

    shipping = make_fulfillment_stock_entry(
        request,
        flow="Shipping",
        entry_type="3PL Shipping",
        purpose="Material Issue",
        source_warehouse="Packing - 3",
    )
    sync_entry(shipping.name)
    request.reload()
    container.reload()
    require(request.status == "Shipped", f"Outbound validation request was not shipped: {request.status}")
    require(container.status == "Shipped", f"Outbound validation container was not shipped: {container.status}")
    require(
        frappe.db.exists(
            "Three PL Container Movement",
            {
                "container_code": container.name,
                "movement_type": "Shipped",
                "reference_doctype": "Stock Entry",
                "reference_name": shipping.name,
            },
        ),
        "Outbound validation did not create shipping movement",
    )

    cleanup_outbound_fulfillment_validation_docs()


def validate_client_portal_permissions():
    allowed_ref = "PORTAL-VALIDATION-ALPHA"
    forbidden_ref = "PORTAL-VALIDATION-BETA"
    shipment_ref = "PORTAL-SHIPMENT-ALPHA"
    forbidden_shipment_ref = "PORTAL-SHIPMENT-BETA"
    frappe.set_user("Administrator")
    for reference in (allowed_ref, forbidden_ref):
        existing = frappe.db.get_value("Inbound Shipment Notice", {"external_reference": reference}, "name")
        if existing:
            frappe.delete_doc("Inbound Shipment Notice", existing, ignore_permissions=True, force=True)
    for reference in (shipment_ref, forbidden_shipment_ref):
        existing = frappe.db.get_value("Three PL Shipment Request", {"external_reference": reference}, "name")
        if existing:
            frappe.delete_doc("Three PL Shipment Request", existing, ignore_permissions=True, force=True)
    for existing in frappe.get_all("Three PL Client Instruction", filters={"instruction_text": ("like", "Portal validation%")}, pluck="name"):
        frappe.delete_doc("Three PL Client Instruction", existing, ignore_permissions=True, force=True)

    frappe.set_user(CLIENT_PORTAL_USER)
    allowed = frappe.get_doc(
        {
            "doctype": "Inbound Shipment Notice",
            "customer": CLIENT_PORTAL_CUSTOMER,
            "external_reference": allowed_ref,
            "expected_arrival_date": frappe.utils.nowdate(),
            "portal_source": 1,
            "items": [
                {
                    "item_code": "SKU-ALPHA-001",
                    "client_sku": "ALPHA-001",
                    "expected_qty": 1,
                    "uom": "Nos",
                }
            ],
        }
    )
    allowed.insert()
    require(allowed.owner == CLIENT_PORTAL_USER, f"Client-created notice has wrong owner: {allowed.owner}")

    try:
        forbidden = frappe.get_doc(
            {
                "doctype": "Inbound Shipment Notice",
                "customer": "Demo Client Beta",
                "external_reference": forbidden_ref,
                "expected_arrival_date": frappe.utils.nowdate(),
                "portal_source": 1,
                "items": [
                    {
                        "item_code": "SKU-BETA-001",
                        "client_sku": "BETA-001",
                        "expected_qty": 1,
                        "uom": "Nos",
                    }
                ],
            }
        )
        forbidden.insert()
    except frappe.PermissionError:
        pass
    else:
        raise RuntimeError("Client user can create receiving notice for another customer")

    shipment = frappe.get_doc(
        {
            "doctype": "Three PL Shipment Request",
            "customer": CLIENT_PORTAL_CUSTOMER,
            "external_reference": shipment_ref,
            "requested_ship_date": frappe.utils.nowdate(),
            "destination_name": "Portal Validation",
            "destination_address": "Validation Address",
            "portal_source": 1,
            "items": [
                {
                    "item_code": "SKU-ALPHA-001",
                    "client_sku": "ALPHA-001",
                    "qty": 1,
                    "uom": "Nos",
                }
            ],
        }
    )
    shipment.insert()
    require(shipment.owner == CLIENT_PORTAL_USER, f"Client-created shipment request has wrong owner: {shipment.owner}")

    try:
        forbidden_shipment = frappe.get_doc(
            {
                "doctype": "Three PL Shipment Request",
                "customer": "Demo Client Beta",
                "external_reference": forbidden_shipment_ref,
                "requested_ship_date": frappe.utils.nowdate(),
                "destination_name": "Portal Validation",
                "destination_address": "Validation Address",
                "portal_source": 1,
                "items": [
                    {
                        "item_code": "SKU-BETA-001",
                        "client_sku": "BETA-001",
                        "qty": 1,
                        "uom": "Nos",
                    }
                ],
            }
        )
        forbidden_shipment.insert()
    except frappe.PermissionError:
        pass
    else:
        raise RuntimeError("Client user can create shipment request for another customer")

    instruction = frappe.get_doc(
        {
            "doctype": "Three PL Client Instruction",
            "customer": CLIENT_PORTAL_CUSTOMER,
            "receiving_notice": frappe.db.get_value("Inbound Shipment Notice", {"external_reference": "ASN-ALPHA-001"}),
            "item_code": "SKU-ALPHA-002",
            "client_sku": "ALPHA-002",
            "instruction_type": "Accept Difference",
            "portal_source": 1,
            "instruction_text": "Portal validation instruction",
        }
    )
    instruction.insert()
    require(instruction.owner == CLIENT_PORTAL_USER, f"Client-created instruction has wrong owner: {instruction.owner}")

    inventory = frappe.get_doc("Three PL Inventory Snapshot", frappe.db.get_value("Three PL Inventory Snapshot", {"customer": CLIENT_PORTAL_CUSTOMER, "item_code": "SKU-ALPHA-001"}))
    require(inventory.customer == CLIENT_PORTAL_CUSTOMER, "Client could not read own inventory snapshot")
    balance_snapshot = frappe.get_doc(
        "Three PL Inventory Balance Snapshot",
        frappe.db.get_value("Three PL Inventory Balance Snapshot", {"customer": CLIENT_PORTAL_CUSTOMER, "item_code": "SKU-ALPHA-001"}),
    )
    require(balance_snapshot.customer == CLIENT_PORTAL_CUSTOMER, "Client could not read own inventory balance snapshot")

    forbidden_docs = [
        ("Item", frappe.db.get_value("Item", {"item_code": "SKU-BETA-001"})),
        ("Inbound Shipment Notice", frappe.db.get_value("Inbound Shipment Notice", {"customer": "Demo Client Beta", "external_reference": "ASN-BETA-001"})),
        ("Three PL Inventory Snapshot", frappe.db.get_value("Three PL Inventory Snapshot", {"customer": "Demo Client Beta", "item_code": "SKU-BETA-001"})),
        ("Three PL Inventory Balance Snapshot", frappe.db.get_value("Three PL Inventory Balance Snapshot", {"customer": "Demo Client Beta", "item_code": "SKU-BETA-001"})),
    ]
    for doctype, name in forbidden_docs:
        require(name, f"Missing forbidden demo record for permission validation: {doctype}")
        doc = frappe.get_doc(doctype, name)
        require(not frappe.has_permission(doctype, "read", doc=doc), f"Client user can read another customer's {doctype}: {name}")

        try:
            doc.check_permission("read")
        except frappe.PermissionError:
            pass
        else:
            raise RuntimeError(f"Client user passed direct permission check for another customer's {doctype}: {name}")

    frappe.set_user("Administrator")
    frappe.db.rollback()


main()
