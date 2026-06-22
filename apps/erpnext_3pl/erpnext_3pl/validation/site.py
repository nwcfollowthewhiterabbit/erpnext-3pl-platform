import json
import os
import tempfile

import frappe
from frappe.utils import flt, now_datetime, nowdate

from erpnext_3pl.config.project_config import (
    BUSINESS_OWNER_USER,
    CLIENT_DESK_CUSTOMER,
    CLIENT_DESK_RECEIVING_REF_PREFIX,
    CLIENT_DESK_SHIPMENT_REF_PREFIX,
    CLIENT_DESK_USER,
    COUNTRY as REQUIRED_COUNTRY,
    CURRENCY as REQUIRED_CURRENCY,
    DEMO_ITEMS,
    LANGUAGE as REQUIRED_LANGUAGE,
    PLACEHOLDER_EMAIL as REQUIRED_PLACEHOLDER_EMAIL,
    TIME_ZONE as REQUIRED_TIME_ZONE,
    WAREHOUSE_MANAGER_USER,
    WAREHOUSE_OPERATOR_USER,
)
from erpnext_3pl.config.workflows import MVP_WORKFLOWS


REQUIRED_WORKSPACES = ["3PL Warehouse", "Stock Reference"]
REQUIRED_DESKTOP_ICONS = {
    "3PL Client": {"item": {"link_type": "URL", "url": "/desk/3pl-client"}, "hidden": 0, "parent_icon": None},
    "Receiving Notices": {
        "item": {"link_type": "DocType", "link_to": "Inbound Shipment Notice"},
        "hidden": 0,
        "parent_icon": "Inbound",
    },
    "Shipment Requests": {
        "item": {"link_type": "DocType", "link_to": "Three PL Shipment Request"},
        "hidden": 0,
        "parent_icon": "Outbound",
    },
    "Products": {
        "item": {"link_type": "DocType", "link_to": "Three PL Client Product"},
        "hidden": 0,
        "parent_icon": "Products & Issues",
    },
    "Discrepancy Instructions": {
        "item": {"link_type": "DocType", "link_to": "Three PL Client Instruction"},
        "hidden": 0,
        "parent_icon": "Products & Issues",
    },
    "Receiving Discrepancies": {
        "item": {"link_type": "Report", "link_to": "3PL Receiving Discrepancies"},
        "hidden": 0,
        "parent_icon": "Inbound",
    },
    "Current Inventory": {
        "item": {"link_type": "Report", "link_to": "3PL Client Inventory Summary"},
        "hidden": 0,
        "parent_icon": "Inventory",
    },
    "Inventory By Date": {
        "item": {"link_type": "Report", "link_to": "3PL Inventory Balance By Date"},
        "hidden": 0,
        "parent_icon": "Inventory",
    },
    "Operation Turnover": {
        "item": {"link_type": "Report", "link_to": "3PL Warehouse Operation Turnover"},
        "hidden": 0,
        "parent_icon": "Inventory",
    },
    "3PL Warehouse": {"item": {"link_type": "URL", "url": "/desk/3pl-warehouse"}, "hidden": 0, "parent_icon": None},
    "Receiving Scan": {
        "item": {"link_type": "URL", "url": "/warehouse/receiving"},
        "hidden": 0,
        "parent_icon": "Warehouse Receiving",
    },
    "Receiving Review": {
        "item": {"link_type": "URL", "url": "/warehouse/receiving-review"},
        "hidden": 0,
        "parent_icon": "Warehouse Receiving",
    },
    "Putaway": {
        "item": {"link_type": "URL", "url": "/warehouse/putaway"},
        "hidden": 0,
        "parent_icon": "Warehouse Receiving",
    },
    "ASN vs Received": {
        "item": {"link_type": "Report", "link_to": "3PL ASN vs Received"},
        "hidden": 0,
        "parent_icon": "Warehouse Receiving",
    },
    "Picking Confirmation": {
        "item": {"link_type": "URL", "url": "/warehouse/picking-confirmation"},
        "hidden": 0,
        "parent_icon": "Warehouse Outbound",
    },
    "Shipment Review": {
        "item": {"link_type": "URL", "url": "/warehouse/shipment-review"},
        "hidden": 0,
        "parent_icon": "Warehouse Outbound",
    },
    "Outbound Fulfillment": {
        "item": {"link_type": "URL", "url": "/warehouse/outbound-fulfillment"},
        "hidden": 0,
        "parent_icon": "Warehouse Outbound",
    },
    "Pick Lists": {
        "item": {"link_type": "DocType", "link_to": "Pick List"},
        "hidden": 0,
        "parent_icon": "Warehouse Outbound",
    },
    "Container Move": {
        "item": {"link_type": "URL", "url": "/warehouse/container-move"},
        "hidden": 0,
        "parent_icon": "Warehouse Operations",
    },
    "Container Repack": {
        "item": {"link_type": "URL", "url": "/warehouse/repack"},
        "hidden": 0,
        "parent_icon": "Warehouse Operations",
    },
    "Warehouse Correction": {
        "item": {"link_type": "URL", "url": "/warehouse/correction"},
        "hidden": 0,
        "parent_icon": "Warehouse Operations",
    },
    "Stocktake": {
        "item": {"link_type": "URL", "url": "/warehouse/stocktake"},
        "hidden": 0,
        "parent_icon": "Warehouse Operations",
    },
    "Correction Review": {
        "item": {"link_type": "URL", "url": "/warehouse/correction-review"},
        "hidden": 0,
        "parent_icon": "Warehouse Operations",
    },
    "Containers Report": {
        "item": {"link_type": "Report", "link_to": "3PL Containers"},
        "hidden": 0,
        "parent_icon": "Warehouse Reports",
    },
    "Container Movements": {
        "item": {"link_type": "Report", "link_to": "3PL Container Movements"},
        "hidden": 0,
        "parent_icon": "Warehouse Reports",
    },
    "Operation Turnover Report": {
        "item": {"link_type": "Report", "link_to": "3PL Warehouse Operation Turnover"},
        "hidden": 0,
        "parent_icon": "Warehouse Reports",
    },
    "Inventory Summary Report": {
        "item": {"link_type": "Report", "link_to": "3PL Client Inventory Summary"},
        "hidden": 0,
        "parent_icon": "Warehouse Reports",
    },
}
REQUIRED_DESKTOP_FOLDERS = {
    "Inbound": 0,
    "Outbound": 0,
    "Inventory": 0,
    "Products & Issues": 0,
    "Warehouse Receiving": 0,
    "Warehouse Outbound": 0,
    "Warehouse Operations": 0,
    "Warehouse Reports": 0,
}
HIDDEN_STANDARD_DESKTOP_ICONS = {
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
REQUIRED_SERVER_SCRIPTS = {
    "3PL Client Product Immediate Sync": ("Three PL Client Product", "After Save"),
    "3PL Container Inventory Snapshot Sync": ("Three PL Container", "After Save"),
    "3PL Receiving Notice Discrepancy Sync": ("Inbound Shipment Notice", "Before Save"),
    "3PL Client Instruction Status Sync": ("Three PL Client Instruction", "After Save"),
    "3PL Shipment Request Immediate Pick List Sync": ("Three PL Shipment Request", "After Save"),
    "3PL Product Import Immediate Sync": ("Three PL Client Product Import", "After Save"),
    "3PL Stock Entry Immediate Flow Sync": ("Stock Entry", "After Submit"),
    "3PL Pick List Immediate Picked Sync": ("Pick List", "After Save"),
}
REQUIRED_APP_DOC_EVENTS = {
    "Three PL Client Product": {"on_update": "erpnext_3pl.hooks_events.sync_client_product"},
    "Three PL Client Product Import": {"on_update": "erpnext_3pl.hooks_events.sync_product_import"},
    "Three PL Client Instruction": {"on_update": "erpnext_3pl.hooks_events.sync_client_instruction_status"},
    "Three PL Container": {"on_update": "erpnext_3pl.hooks_events.sync_container_inventory"},
    "Inbound Shipment Notice": {"before_save": "erpnext_3pl.hooks_events.sync_receiving_notice_discrepancies"},
    "Three PL Shipment Request": {"on_update": "erpnext_3pl.hooks_events.sync_shipment_request_pick_list"},
    "Pick List": {"on_update": "erpnext_3pl.hooks_events.sync_pick_list_picked"},
    "Stock Entry": {"on_submit": "erpnext_3pl.hooks_events.sync_stock_entry_flow"},
}
REQUIRED_USERS = {
    WAREHOUSE_OPERATOR_USER: ["Stock User", "3PL Warehouse User"],
    WAREHOUSE_MANAGER_USER: ["Stock User", "Stock Manager", "3PL Warehouse Manager"],
    BUSINESS_OWNER_USER: ["System Manager", "Stock User", "Stock Manager", "Item Manager", "3PL Warehouse Manager"],
    CLIENT_DESK_USER: ["3PL Client"],
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
    "Three PL Stocktake Session",
    "Three PL Stocktake",
    "Three PL Inventory Snapshot",
    "Three PL Inventory Balance Snapshot",
    "Three PL Client Product",
    "Three PL Client Product Change Log",
    "Three PL Client Product Import",
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
    "repack_mode",
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
    "review_decision",
    "reviewed_by",
    "reviewed_at",
    "review_notes",
}
REQUIRED_STOCKTAKE_SESSION_FIELDS = {
    "session_reference",
    "status",
    "client",
    "warehouse",
    "started_at",
    "completed_at",
}
REQUIRED_STOCKTAKE_FIELDS = {
    "operation_reference",
    "operation_datetime",
    "status",
    "stocktake_session",
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
REQUIRED_CLIENT_PRODUCT_FIELDS = {
    "customer",
    "client_sku",
    "product_name",
    "product_description",
    "uom",
    "barcode",
    "product_image",
    "status",
    "item_code",
    "sync_status",
    "last_synced_at",
    "sync_error",
    "last_synced_snapshot",
    "notes",
}
REQUIRED_CLIENT_PRODUCT_LOG_FIELDS = {
    "product",
    "customer",
    "item_code",
    "action",
    "changed_by",
    "change_datetime",
    "old_values",
    "new_values",
    "notes",
}
REQUIRED_CLIENT_PRODUCT_IMPORT_FIELDS = {
    "customer",
    "import_file",
    "status",
    "processed_at",
    "rows_total",
    "rows_applied",
    "error_log",
    "notes",
}
REQUIRED_REPORTS = [
    "3PL ASN vs Received",
    "3PL Receiving Discrepancies",
    "3PL Containers",
    "3PL Container Moves",
    "3PL Container Repacks",
    "3PL Warehouse Corrections",
    "3PL Corrections Needing Review",
    "3PL Stocktake Sessions",
    "3PL Stocktakes",
    "3PL Container Movements",
    "3PL Shipment Requests",
    "3PL Client Inventory",
    "3PL Client Inventory Summary",
    "3PL Inventory Balance By Date",
    "3PL Warehouse Operation Turnover",
]
REQUIRED_REPORT_ROLES = {
    "System Manager",
    "Stock Manager",
    "Stock User",
    "3PL Warehouse Manager",
    "3PL Warehouse User",
}
CLIENT_DESK_REPORTS = {
    "3PL Client Inventory",
    "3PL Client Inventory Summary",
    "3PL Inventory Balance By Date",
    "3PL Warehouse Operation Turnover",
    "3PL Shipment Requests",
    "3PL Receiving Discrepancies",
}
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


def require_client_system_access_restricted():
    current_user = frappe.session.user
    try:
        frappe.set_user(CLIENT_DESK_USER)
        visible_users = set(frappe.get_list("User", pluck="name"))
        require(visible_users <= {CLIENT_DESK_USER}, f"Client can list unrelated users: {sorted(visible_users - {CLIENT_DESK_USER})}")
        for doctype in ("Role", "DocType", "Module Profile", "System Settings"):
            require(not frappe.has_permission(doctype, "read"), f"Client has read access to system DocType: {doctype}")
    finally:
        frappe.set_user(current_user)


def is_app_installed():
    try:
        return "erpnext_3pl" in frappe.get_installed_apps()
    except Exception:
        return False


def validate_event_automation():
    if is_app_installed():
        from erpnext_3pl.hooks import doc_events, has_permission, permission_query_conditions

        for doctype, events in REQUIRED_APP_DOC_EVENTS.items():
            require(doctype in doc_events, f"ERPNext 3PL app misses doc_events for {doctype}")
            for event_name, handler in events.items():
                require(
                    doc_events[doctype].get(event_name) == handler,
                    f"ERPNext 3PL app has wrong {doctype}.{event_name} hook",
                )
        require(
            permission_query_conditions.get("User") == "erpnext_3pl.permissions.user_query_condition",
            "ERPNext 3PL app misses User permission query condition",
        )
        require(
            has_permission.get("User") == "erpnext_3pl.permissions.user_has_permission",
            "ERPNext 3PL app misses User has_permission hook",
        )
        for script_name in REQUIRED_SERVER_SCRIPTS:
            if frappe.db.exists("Server Script", script_name):
                server_script = frappe.get_doc("Server Script", script_name)
                require(server_script.disabled == 1, f"Duplicate Server Script must be disabled when ERPNext 3PL app is installed: {script_name}")
        return

    require(
        frappe.conf.get("server_script_enabled") in (1, "1", True),
        "Server Scripts must be enabled for immediate client product synchronization",
    )
    for script_name, (reference_doctype, doctype_event) in REQUIRED_SERVER_SCRIPTS.items():
        require(frappe.db.exists("Server Script", script_name), f"Missing Server Script: {script_name}")
        server_script = frappe.get_doc("Server Script", script_name)
        require(server_script.disabled == 0, f"Server Script is disabled: {script_name}")
        require(server_script.script_type == "DocType Event", f"Server Script has wrong type: {script_name}")
        require(server_script.reference_doctype == reference_doctype, f"Server Script has wrong reference doctype: {script_name}")
        require(server_script.doctype_event == doctype_event, f"Server Script has wrong event: {script_name}")


def validate_mvp_workflows():
    for workflow_definition in MVP_WORKFLOWS:
        workflow_name = workflow_definition["name"]
        require(frappe.db.exists("Workflow", workflow_name), f"Missing MVP workflow: {workflow_name}")

        workflow = frappe.get_doc("Workflow", workflow_name)
        require(workflow.is_active == 1, f"MVP workflow is not active: {workflow_name}")
        require(workflow.document_type == workflow_definition["document_type"], f"MVP workflow has wrong DocType: {workflow_name}")
        require(workflow.workflow_state_field == "status", f"MVP workflow must use status as state field: {workflow_name}")

        expected_states = set(workflow_definition["states"])
        actual_states = {row.state for row in workflow.states}
        require(expected_states <= actual_states, f"MVP workflow misses states for {workflow_name}: {sorted(expected_states - actual_states)}")

        expected_transitions = {
            (state, action, next_state, role)
            for state, action, next_state, roles in workflow_definition["transitions"]
            for role in roles
        }
        actual_transitions = {
            (row.state, row.action, row.next_state, row.allowed)
            for row in workflow.transitions
        }
        require(
            expected_transitions <= actual_transitions,
            f"MVP workflow misses transitions for {workflow_name}: {sorted(expected_transitions - actual_transitions)}",
        )


def delete_stock_entries(filters):
    for entry_name in frappe.get_all("Stock Entry", filters=filters, pluck="name"):
        entry = frappe.get_doc("Stock Entry", entry_name)
        if entry.docstatus == 1:
            entry.cancel()
        frappe.delete_doc("Stock Entry", entry.name, ignore_permissions=True, force=True)


def validate_demo_inventory_stock_ledger():
    from erpnext_3pl.sync.inventory_snapshots import sync_inventory_snapshots

    sync_inventory_snapshots()
    demo_item_codes = [item["item_code"] for item in DEMO_ITEMS]

    stock_ledger_rows = frappe.db.sql(
        """
        select sum(actual_qty)
        from `tabStock Ledger Entry`
        where item_code = 'SKU-ALPHA-003'
          and warehouse = 'Aisle A - 3'
          and is_cancelled = 0
        """,
        as_list=True,
    )
    require(stock_ledger_rows and stock_ledger_rows[0][0] == 36, "Wrong Alpha SKU-ALPHA-003 stock ledger balance")

    active_container_statuses = ("Received", "In Verification", "Ready for Putaway", "Stored", "Picking", "Picked", "Packed")
    container_rows = frappe.db.sql(
        """
        select item.item_code, container.current_warehouse, sum(item.qty) as qty
        from `tabThree PL Container Item` item
        inner join `tabThree PL Container` container on container.name = item.parent
        where item.item_code in %(item_codes)s
          and container.status in %(statuses)s
          and container.current_warehouse is not null
          and container.current_warehouse != ''
        group by item.item_code, container.current_warehouse
        """,
        {"item_codes": demo_item_codes, "statuses": active_container_statuses},
        as_dict=True,
    )
    snapshot_rows = frappe.db.sql(
        """
        select item_code, warehouse as current_warehouse, sum(qty) as qty
        from `tabThree PL Inventory Snapshot`
        where item_code in %(item_codes)s
          and container_code is not null
          and container_code != ''
        group by item_code, warehouse
        """,
        {"item_codes": demo_item_codes},
        as_dict=True,
    )
    ledger_rows = frappe.db.sql(
        """
        select item_code, warehouse as current_warehouse, sum(actual_qty) as qty
        from `tabStock Ledger Entry`
        where item_code in %(item_codes)s
          and is_cancelled = 0
        group by item_code, warehouse
        """,
        {"item_codes": demo_item_codes},
        as_dict=True,
    )

    def totals(rows):
        return {
            (row.item_code, row.current_warehouse): flt(row.qty)
            for row in rows
            if flt(row.qty) != 0
        }

    container_totals = totals(container_rows)
    snapshot_totals = totals(snapshot_rows)
    ledger_totals = totals(ledger_rows)
    require(snapshot_totals == container_totals, f"Inventory snapshot totals do not match container model: {snapshot_totals} != {container_totals}")


def require_permission_error(action, message):
    try:
        action()
    except frappe.PermissionError:
        return
    raise RuntimeError(message)


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
        if workspace == "3PL Warehouse":
            workspace_links = {row.link_to for row in doc.links if row.link_to}
            workspace_shortcuts = {row.link_to for row in doc.shortcuts if row.link_to}
            required_staff_doctypes = {
                "Customer",
                "Inbound Shipment Notice",
                "Three PL Shipment Request",
                "Three PL Client Product",
                "Three PL Client Product Import",
                "Three PL Client Product Change Log",
                "Three PL Client Instruction",
                "Three PL Inventory Snapshot",
                "Three PL Inventory Balance Snapshot",
                "Item",
                "Warehouse",
            }
            missing_links = required_staff_doctypes - workspace_links - workspace_shortcuts
            require(not missing_links, "3PL Warehouse workspace misses staff links: " + ", ".join(sorted(missing_links)))

    for doctype in REQUIRED_DOCTYPES:
        require(frappe.db.exists("DocType", doctype), f"Missing DocType: {doctype}")
        doctype_record = frappe.db.get_value("DocType", doctype, ["module", "custom"], as_dict=True)
        require(doctype_record.module == "ERPNext 3PL", f"App DocType must use ERPNext 3PL module: {doctype}")
        require(not doctype_record.custom, f"App DocType must be a standard app-owned DocType: {doctype}")

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
    stocktake_session_meta = frappe.get_meta("Three PL Stocktake Session")
    stocktake_session_fields = {field.fieldname for field in stocktake_session_meta.fields}
    require(stocktake_session_fields >= REQUIRED_STOCKTAKE_SESSION_FIELDS, "Three PL Stocktake Session misses required fields")
    stocktake_meta = frappe.get_meta("Three PL Stocktake")
    stocktake_fields = {field.fieldname for field in stocktake_meta.fields}
    require(stocktake_fields >= REQUIRED_STOCKTAKE_FIELDS, "Three PL Stocktake misses required fields")
    balance_snapshot_meta = frappe.get_meta("Three PL Inventory Balance Snapshot")
    balance_snapshot_fields = {field.fieldname for field in balance_snapshot_meta.fields}
    require(
        balance_snapshot_fields >= REQUIRED_INVENTORY_BALANCE_SNAPSHOT_FIELDS,
        "Three PL Inventory Balance Snapshot misses required fields",
    )
    client_product_meta = frappe.get_meta("Three PL Client Product")
    client_product_fields = {field.fieldname for field in client_product_meta.fields}
    require(client_product_fields >= REQUIRED_CLIENT_PRODUCT_FIELDS, "Three PL Client Product misses required fields")
    client_product_log_meta = frappe.get_meta("Three PL Client Product Change Log")
    client_product_log_fields = {field.fieldname for field in client_product_log_meta.fields}
    require(client_product_log_fields >= REQUIRED_CLIENT_PRODUCT_LOG_FIELDS, "Three PL Client Product Change Log misses required fields")
    client_product_import_meta = frappe.get_meta("Three PL Client Product Import")
    client_product_import_fields = {field.fieldname for field in client_product_import_meta.fields}
    require(client_product_import_fields >= REQUIRED_CLIENT_PRODUCT_IMPORT_FIELDS, "Three PL Client Product Import misses required fields")

    validate_event_automation()
    validate_mvp_workflows()

    for report in REQUIRED_REPORTS:
        require(frappe.db.exists("Report", report), f"Missing Report: {report}")
        report_doc = frappe.get_doc("Report", report)
        report_roles = {row.role for row in report_doc.roles}
        missing_roles = REQUIRED_REPORT_ROLES - report_roles
        require(not missing_roles, f"Report {report} misses roles: {', '.join(sorted(missing_roles))}")
        if report in CLIENT_DESK_REPORTS:
            require("3PL Client" in report_roles, f"Client Desk report misses 3PL Client role: {report}")
        if report_doc.report_type == "Query Report":
            frappe.db.sql(report_doc.query)

    for route, label in (
        ("warehouse/receiving", "receiving"),
        ("warehouse/receiving-review", "receiving review"),
        ("warehouse/correction", "correction"),
        ("warehouse/correction-review", "correction review"),
        ("warehouse/stocktake", "stocktake"),
        ("warehouse/container-move", "container move"),
        ("warehouse/putaway", "putaway"),
        ("warehouse/repack", "repack"),
        ("warehouse/picking-confirmation", "picking confirmation"),
        ("warehouse/shipment-review", "shipment review"),
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
    purpose_field = stock_entry_meta.get_field("purpose")
    require(purpose_field and not purpose_field.hidden, "Stock Entry purpose must be visible for manual tester confirmation")
    require(purpose_field and purpose_field.read_only, "Stock Entry purpose must remain read-only")
    for fieldname in ("client", "inbound_shipment_notice", "scanned_location", "container_code"):
        field = stock_entry_meta.get_field(fieldname)
        require(field and field.mandatory_depends_on == "eval:doc.warehouse_flow=='Inbound Receipt'", f"Stock Entry {fieldname} must be mandatory for inbound receipts")

    for user, roles in REQUIRED_USERS.items():
        require(frappe.db.exists("User", user), f"Missing User: {user}")
        doc = frappe.get_doc("User", user)
        user_roles = {row.role for row in doc.roles}
        require(doc.enabled == 1, f"User is disabled: {user}")
        expected_module_profile = "3PL Client Only" if user == CLIENT_DESK_USER else (None if user == BUSINESS_OWNER_USER else "Warehouse Only")
        require(doc.module_profile == expected_module_profile, f"Wrong module profile for {user}: {doc.module_profile}")
        expected_workspace = "3PL Client" if user == CLIENT_DESK_USER else "3PL Warehouse"
        require(doc.default_workspace == expected_workspace, f"Wrong default workspace for {user}: {doc.default_workspace}")
        if doc.meta.has_field("default_app"):
            require(doc.default_app is None, f"Wrong default app for {user}: {doc.default_app}")
        expected_user_type = "System User"
        require(doc.user_type == expected_user_type, f"Wrong user_type for {user}: {doc.user_type}")
        for role in roles:
            require(role in user_roles, f"Missing role for {user}: {role}")
        if user == CLIENT_DESK_USER:
            require("Customer" not in user_roles, "Desk-native client user must not keep legacy Customer role")

    for role in ("Stock User", "Stock Manager", "3PL Warehouse User", "3PL Warehouse Manager"):
        require(frappe.db.get_value("Role", role, "home_page") == "desk/3pl-warehouse", f"Wrong home_page for role: {role}")
    require(frappe.db.exists("Workspace", "3PL Client"), "Missing 3PL Client Workspace")
    client_workspace = frappe.get_doc("Workspace", "3PL Client")
    require(
        "Three PL Client Product Import" not in {row.link_to for row in client_workspace.links if row.link_to},
        "Product Import must stay outside MVP1 client workspace",
    )
    for label, hidden in REQUIRED_DESKTOP_FOLDERS.items():
        folder = frappe.db.get_value(
            "Desktop Icon",
            label,
            ["standard", "app", "icon_type", "parent_icon", "hidden"],
            as_dict=True,
        )
        require(folder, f"Missing 3PL Desktop folder: {label}")
        require(folder.standard == 1, f"3PL Desktop folder must be standard: {label}")
        require(folder.app == "erpnext_3pl", f"3PL Desktop folder has wrong app: {label}")
        require(folder.icon_type == "Folder", f"3PL Desktop folder has wrong type: {label}")
        require(not folder.parent_icon, f"3PL Desktop folder must be top-level: {label}")
        require(folder.hidden == hidden, f"3PL Desktop folder hidden state is wrong: {label}")

    client_workspace_links = {
        (row.link_type, row.link_to, row.label) for row in client_workspace.links if row.link_type or row.link_to
    }
    for label, spec in REQUIRED_DESKTOP_ICONS.items():
        if spec["parent_icon"] not in {"Inbound", "Outbound", "Inventory", "Products & Issues"}:
            continue
        item = spec["item"]
        if item.get("link_to"):
            require(
                (item["link_type"], item["link_to"], label) in client_workspace_links,
                f"Missing 3PL Client Workspace link: {label}",
            )
    visible_standard_icons = {
        row.name
        for row in frappe.get_all(
            "Desktop Icon",
            filters={"name": ("in", sorted(HIDDEN_STANDARD_DESKTOP_ICONS)), "hidden": 0},
            fields=["name"],
        )
    }
    require(not visible_standard_icons, "Standard Desktop icons must stay hidden: " + ", ".join(sorted(visible_standard_icons)))

    for role in ("3PL Warehouse User", "3PL Warehouse Manager"):
        require(
            frappe.db.exists(
                "Custom DocPerm",
                {"parent": "Page", "role": role, "permlevel": 0, "if_owner": 0, "read": 1},
            ),
            f"Missing Page read permission for role: {role}",
        )
    require(
        not frappe.db.exists("Custom DocPerm", {"parent": "Page", "role": "3PL Client", "read": 1}),
        "3PL Client must not have broad Page read permission",
    )

    client_role = frappe.get_doc("Role", "3PL Client")
    if client_role.meta.has_field("desk_access"):
        require(client_role.desk_access == 1, "3PL Client role must have Desk access")
    require(client_role.home_page == "desk/3pl-client", f"Wrong 3PL Client home_page: {client_role.home_page}")

    require(
        frappe.db.exists("User Permission", {"user": CLIENT_DESK_USER, "allow": "Customer", "for_value": CLIENT_DESK_CUSTOMER}),
        "Missing client Customer User Permission",
    )
    require(
        frappe.db.exists("Contact", {"user": CLIENT_DESK_USER}),
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
    require_role_perm("Three PL Container Movement", "3PL Client", read=1, report=1)
    require_role_perm("Three PL Container Repack", "3PL Client", read=1)
    require_role_perm("Three PL Warehouse Correction", "3PL Client", read=1)
    require_role_perm("Three PL Stocktake", "3PL Client", read=1)
    require_role_perm("Three PL Repack Source", "3PL Client", read=1)
    require_role_perm("Three PL Repack Item", "3PL Client", read=1)
    require_role_perm("Three PL Inventory Snapshot", "3PL Client", read=1, report=1)
    require_role_perm("Three PL Inventory Balance Snapshot", "3PL Client", read=1, report=1)
    require_role_perm("Three PL Client Product", "3PL Client", read=1, write=1, create=1)
    require_role_perm("Three PL Client Product Change Log", "3PL Client", read=1)
    require(
        not frappe.db.exists("Custom DocPerm", {"parent": "Three PL Client Product Import", "role": "3PL Client"}),
        "Product Import must stay outside MVP1 client permissions",
    )
    require_role_perm("Three PL Shipment Request", "3PL Client", read=1, write=1, create=1)
    require_role_perm("Three PL Shipment Request Item", "3PL Client", read=1, write=1, create=1)
    require_role_perm("Three PL Client Instruction", "3PL Client", read=1, write=1, create=1)
    require_client_system_access_restricted()
    staff_client_doctypes = (
        "Customer",
        "Inbound Shipment Notice",
        "Three PL Shipment Request",
        "Three PL Client Product",
        "Three PL Client Product Import",
        "Three PL Client Product Change Log",
        "Three PL Client Instruction",
        "Three PL Inventory Snapshot",
        "Three PL Inventory Balance Snapshot",
    )
    for doctype in staff_client_doctypes:
        require_role_perm(doctype, "3PL Warehouse Manager", read=1)
        if doctype != "Customer":
            require_role_perm(doctype, "System Manager", read=1)
    for doctype in ("Three PL Client Product", "Three PL Client Product Import", "Three PL Shipment Request", "Three PL Client Instruction"):
        require_role_perm(doctype, "3PL Warehouse Manager", write=1, create=1)
        require_role_perm(doctype, "System Manager", write=1, create=1)

    for doctype in ("Warehouse", "Item", "Inbound Shipment Notice", "Three PL Container", "Three PL Container Move", "Three PL Warehouse Correction", "Three PL Stocktake"):
        require_effective_perm(WAREHOUSE_MANAGER_USER, doctype, "read", "create")
    for doctype in staff_client_doctypes:
        require_effective_perm(WAREHOUSE_MANAGER_USER, doctype, "read")
        require_effective_perm(BUSINESS_OWNER_USER, doctype, "read")
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
    stock_ledger_rows = frappe.db.sql(
        """
        select sum(actual_qty)
        from `tabStock Ledger Entry`
        where item_code = 'SKU-ALPHA-003'
          and warehouse = 'Aisle A - 3'
          and is_cancelled = 0
        """,
        as_list=True,
    )
    require(stock_ledger_rows and stock_ledger_rows[0][0] == 36, "Wrong Alpha SKU-ALPHA-003 stock ledger balance")
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
        any(row.item_code == "SKU-ALPHA-003" and row.qty == 18 and row.container_code for row in demo_pick_list.locations),
        "Demo Pick List misses whole-container allocated item/location row",
    )
    require(frappe.db.exists("Three PL Client Instruction", {"customer": "Demo Client Alpha", "receiving_notice": notice_name}), "Missing demo client discrepancy instruction")

    validate_receiving_sync()
    validate_shipment_sync()
    validate_warehouse_correction()
    validate_warehouse_correction_stock_posting()
    validate_stocktake()
    validate_partial_repack()
    validate_putaway_operation()
    validate_picking_confirmation()
    validate_outbound_fulfillment()
    validate_client_desk_native_controls()
    validate_client_desk_permissions()
    validate_demo_inventory_stock_ledger()

    print("Site validation passed")


def cleanup_receiving_validation_docs():
    frappe.set_user("Administrator")
    notice_names = frappe.get_all("Inbound Shipment Notice", filters={"external_reference": ("like", "RECV-VALIDATION-%")}, pluck="name")
    if notice_names:
        for entry_name in frappe.get_all("Stock Entry", filters={"inbound_shipment_notice": ("in", notice_names)}, pluck="name"):
            entry = frappe.get_doc("Stock Entry", entry_name)
            if entry.docstatus == 1:
                entry.cancel()
            frappe.delete_doc("Stock Entry", entry.name, ignore_permissions=True, force=True)
    for notice_name in notice_names:
        frappe.delete_doc("Inbound Shipment Notice", notice_name, ignore_permissions=True, force=True)
    for container_name in frappe.get_all("Three PL Container", filters={"name": ("like", "BOX300%")}, pluck="name"):
        for snapshot_name in frappe.get_all("Three PL Inventory Snapshot", filters={"container_code": container_name}, pluck="name"):
            frappe.delete_doc("Three PL Inventory Snapshot", snapshot_name, ignore_permissions=True, force=True)
        for movement_name in frappe.get_all("Three PL Container Movement", filters={"container_code": container_name}, pluck="name"):
            frappe.delete_doc("Three PL Container Movement", movement_name, ignore_permissions=True, force=True)
        frappe.delete_doc("Three PL Container", container_name, ignore_permissions=True, force=True)


def validate_receiving_sync():
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
                },
                {
                    "item_code": "SKU-ALPHA-002",
                    "qty": 3,
                    "t_warehouse": "Temporary Receiving - 3",
                    "uom": "Nos",
                    "stock_uom": "Nos",
                    "conversion_factor": 1,
                    "basic_rate": 1,
                    "scanned_location": "Temporary Receiving - 3",
                    "container_code": "BOX-ALPHA-001",
                },
            ],
        }
    )
    entry.insert(ignore_permissions=True)
    entry.submit()

    notice.reload()
    require(notice.status == "Discrepancy Review", f"Receiving validation notice has wrong status: {notice.status}")
    require(notice.items[0].received_qty == 4, "Receiving validation did not update received_qty")
    require(notice.items[0].variance_qty == -1, "Receiving validation did not update variance_qty")
    require(
        any(row.auto_generated and row.discrepancy_type == "Quantity Difference" and row.variance_qty == -1 for row in notice.discrepancies),
        "Receiving validation did not create auto discrepancy",
    )
    require(
        any(row.auto_generated and row.discrepancy_type == "Unexpected Product" and row.item_code == "SKU-ALPHA-002" and row.actual_qty == 3 for row in notice.discrepancies),
        "Receiving validation did not create unexpected product discrepancy",
    )

    manual_reference = "RECV-VALIDATION-MANUAL-QTY"
    manual_notice = frappe.get_doc(
        {
            "doctype": "Inbound Shipment Notice",
            "customer": "Demo Client Alpha",
            "external_reference": manual_reference,
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
    manual_notice.insert(ignore_permissions=True)
    manual_notice.items[0].received_qty = 3
    manual_notice.save(ignore_permissions=True)
    manual_notice.reload()
    require(manual_notice.items[0].variance_qty == -2, "Manual received qty save did not update variance_qty")
    require(
        any(row.auto_generated and row.discrepancy_type == "Quantity Difference" and row.actual_qty == 3 and row.variance_qty == -2 for row in manual_notice.discrepancies),
        "Manual received qty save did not update auto discrepancy",
    )

    cleanup_receiving_validation_docs()


def cleanup_shipment_validation_docs():
    frappe.set_user("Administrator")
    request_names = frappe.get_all("Three PL Shipment Request", filters={"external_reference": ("like", "SHIP-VALIDATION-%")}, pluck="name")
    if request_names:
        for pick_name in frappe.get_all("Pick List", filters={"shipment_request": ("in", request_names)}, pluck="name"):
            pick_list = frappe.get_doc("Pick List", pick_name)
            if pick_list.docstatus == 1:
                pick_list.cancel()
            frappe.delete_doc("Pick List", pick_list.name, ignore_permissions=True, force=True)
    for request_name in request_names:
        frappe.delete_doc("Three PL Shipment Request", request_name, ignore_permissions=True, force=True)


def validate_partial_shipment_allocation_is_rejected():
    from erpnext_3pl.sync.inventory_snapshots import sync_inventory_snapshots

    container = frappe.get_doc("Three PL Container", "BOX-ALPHA-005")
    container.status = "Stored"
    container.save(ignore_permissions=True)
    sync_inventory_snapshots()

    request = frappe.get_doc(
        {
            "doctype": "Three PL Shipment Request",
            "customer": "Demo Client Alpha",
            "external_reference": "SHIP-VALIDATION-PARTIAL",
            "requested_ship_date": nowdate(),
            "destination_name": "Shipment Validation Partial",
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
    request.reload()

    require(
        not frappe.db.exists("Pick List", {"shipment_request": request.name}),
        "Partial shipment validation created a Pick List for a non-split container",
    )
    require(request.status == "Submitted", f"Partial shipment validation changed request status: {request.status}")
    require(
        "whole-container allocation" in (request.notes or ""),
        "Partial shipment validation did not explain the whole-container allocation requirement",
    )
    container.reload()
    require(container.status == "Stored", f"Partial shipment validation changed container status: {container.status}")


def validate_shipment_sync():
    from erpnext_3pl.sync.inventory_snapshots import sync_inventory_snapshots

    cleanup_shipment_validation_docs()
    frappe.set_user("Administrator")
    validate_partial_shipment_allocation_is_rejected()

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
                    "qty": 18,
                    "uom": "Nos",
                }
            ],
        }
    )
    request.insert(ignore_permissions=True)
    request.reload()

    pick_list_name = frappe.db.get_value("Pick List", {"shipment_request": request.name}, "name")
    require(pick_list_name, "Shipment validation did not create Pick List")
    pick_list = frappe.get_doc("Pick List", pick_list_name)
    require(request.status == "Picking", f"Shipment validation request has wrong status: {request.status}")
    require(pick_list.purpose == "Delivery", f"Shipment validation Pick List has wrong purpose: {pick_list.purpose}")
    require(pick_list.client == "Demo Client Alpha", "Shipment validation Pick List has wrong client")
    require(pick_list.shipment_request == request.name, "Shipment validation Pick List is not linked to request")
    require(
        any(row.item_code == "SKU-ALPHA-003" and row.qty == 18 and row.warehouse == "Aisle A - 3" and row.container_code == "BOX-ALPHA-005" for row in pick_list.locations),
        "Shipment validation Pick List misses whole-container allocated stock row",
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
    validation_containers = ["BOX-CORRECTION-VALIDATION", "BOX-CORRECTION-POSTING-VALIDATION"]
    correction_names = frappe.get_all(
        "Three PL Warehouse Correction",
        filters={"container_code": ("in", validation_containers)},
        pluck="name",
    )
    for correction_name in correction_names:
        delete_stock_entries({"warehouse_correction": correction_name})
    for movement_name in frappe.get_all(
        "Three PL Container Movement",
        filters={"container_code": ("in", validation_containers)},
        pluck="name",
    ):
        frappe.delete_doc("Three PL Container Movement", movement_name, ignore_permissions=True, force=True)
    for snapshot_name in frappe.get_all(
        "Three PL Inventory Snapshot",
        filters={"container_code": ("in", validation_containers)},
        pluck="name",
    ):
        frappe.delete_doc("Three PL Inventory Snapshot", snapshot_name, ignore_permissions=True, force=True)
    for correction_name in frappe.get_all(
        "Three PL Warehouse Correction",
        filters={"container_code": ("in", validation_containers)},
        pluck="name",
    ):
        frappe.delete_doc("Three PL Warehouse Correction", correction_name, ignore_permissions=True, force=True)
    for container_name in validation_containers:
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
    correction.status = "Applied"
    correction.save(ignore_permissions=True)
    frappe.db.commit()

    from erpnext_3pl.warehouse.warehouse_corrections import apply_correction_stock_posting

    entry_name = apply_correction_stock_posting(correction)
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
    for session_name in frappe.get_all(
        "Three PL Stocktake Session",
        filters={"session_reference": "STOCKTAKE-VALIDATION-SESSION"},
        pluck="name",
    ):
        frappe.delete_doc("Three PL Stocktake Session", session_name, ignore_permissions=True, force=True)
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
    stocktake_session = frappe.get_doc(
        {
            "doctype": "Three PL Stocktake Session",
            "session_reference": "STOCKTAKE-VALIDATION-SESSION",
            "client": "Demo Client Alpha",
            "warehouse": "Aisle B - 3",
            "started_at": operation_time,
            "notes": "Validation grouped stocktake session.",
        }
    )
    stocktake_session.insert()
    stocktake_session.status = "In Progress"
    stocktake_session.save()
    stocktake_same = frappe.get_doc(
        {
            "doctype": "Three PL Stocktake",
            "operation_reference": "STOCKTAKE-VALIDATION-SAME",
            "operation_datetime": operation_time,
            "stocktake_session": stocktake_session.name,
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
    stocktake_same.status = "No Difference"
    stocktake_same.save()

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
            "stocktake_session": stocktake_session.name,
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
    stocktake_session.status = "Completed"
    stocktake_session.completed_at = operation_time
    stocktake_session.save()

    frappe.set_user("Administrator")
    container.reload()
    stocktake_same.reload()
    stocktake_delta.reload()
    stocktake_session.reload()
    require(stocktake_same.status == "No Difference", "No-difference stocktake has wrong status")
    require(stocktake_same.stocktake_session == stocktake_session.name, "No-difference stocktake is not linked to session")
    require(container.items[0].qty == counted_qty, "Stocktake did not update container quantity")
    require(stocktake_delta.status == "Applied", "Delta stocktake was not applied")
    require(stocktake_delta.stocktake_session == stocktake_session.name, "Delta stocktake is not linked to session")
    require(stocktake_session.status == "Completed", "Stocktake session was not completed")
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


def cleanup_partial_repack_validation_docs():
    frappe.set_user("Administrator")
    for movement_name in frappe.get_all(
        "Three PL Container Movement",
        filters={"container_code": ("in", ["BOX-REPACK-SPLIT-SOURCE", "BOX-REPACK-SPLIT-TARGET"])},
        pluck="name",
    ):
        frappe.delete_doc("Three PL Container Movement", movement_name, ignore_permissions=True, force=True)
    for repack_name in frappe.get_all(
        "Three PL Container Repack",
        filters={"operation_reference": ("like", "REPACK-SPLIT-VALIDATION%")},
        pluck="name",
    ):
        frappe.delete_doc("Three PL Container Repack", repack_name, ignore_permissions=True, force=True)
    for container_name in ("BOX-REPACK-SPLIT-TARGET", "BOX-REPACK-SPLIT-SOURCE"):
        if frappe.db.exists("Three PL Container", container_name):
            frappe.delete_doc("Three PL Container", container_name, ignore_permissions=True, force=True)


def validate_partial_repack():
    cleanup_partial_repack_validation_docs()
    frappe.set_user("Administrator")

    source = frappe.get_doc(
        {
            "doctype": "Three PL Container",
            "container_code": "BOX-REPACK-SPLIT-SOURCE",
            "barcode": "BOX-REPACK-SPLIT-SOURCE",
            "container_type": "Box",
            "client": "Demo Client Alpha",
            "current_warehouse": "Aisle B - 3",
            "status": "Stored",
            "items": [
                {
                    "item_code": "SKU-ALPHA-001",
                    "client_sku": "ALPHA-001",
                    "qty": 10,
                    "uom": "Nos",
                    "condition_status": "OK",
                }
            ],
        }
    )
    source.insert(ignore_permissions=True)
    target = frappe.get_doc(
        {
            "doctype": "Three PL Container",
            "container_code": "BOX-REPACK-SPLIT-TARGET",
            "barcode": "BOX-REPACK-SPLIT-TARGET",
            "container_type": "Box",
            "client": "Demo Client Alpha",
            "current_warehouse": "Aisle A - 3",
            "status": "Stored",
        }
    )
    target.insert(ignore_permissions=True)

    operation_time = now_datetime()
    repack = frappe.get_doc(
        {
            "doctype": "Three PL Container Repack",
            "operation_reference": "REPACK-SPLIT-VALIDATION",
            "operation_datetime": operation_time,
            "status": "Draft",
            "repack_mode": "Partial Split",
            "client": "Demo Client Alpha",
            "target_container": "BOX-REPACK-SPLIT-TARGET",
            "target_location": "Aisle A - 3",
            "source_containers": [
                {
                    "source_container": "BOX-REPACK-SPLIT-SOURCE",
                    "source_location": "Aisle B - 3",
                }
            ],
            "items": [
                {
                    "item_code": "SKU-ALPHA-001",
                    "client_sku": "ALPHA-001",
                    "qty": 4,
                    "uom": "Nos",
                    "condition_status": "OK",
                    "notes": "Validation partial split.",
                }
            ],
            "notes": "Validation partial repack.",
        }
    )
    repack.insert(ignore_permissions=True)

    from erpnext_3pl.warehouse.container_repacks import apply_repack

    movement_name = apply_repack(repack).name

    source.reload()
    target = frappe.get_doc("Three PL Container", "BOX-REPACK-SPLIT-TARGET")
    repack.reload()
    require(repack.status == "Applied", "Partial repack was not applied")
    require(repack.repack_mode == "Partial Split", "Partial repack has wrong mode")
    require(repack.movement == movement_name, "Partial repack is not linked to movement")
    require(source.status == "Stored", "Partial repack source should remain stored while it has remaining stock")
    require(not source.replaced_by, "Partial repack source must not be marked replaced")
    require(source.items[0].qty == 6, "Partial repack did not subtract source quantity")
    require(target.current_warehouse == "Aisle A - 3", "Partial repack target has wrong location")
    require(target.items[0].qty == 4, "Partial repack target has wrong quantity")
    require(
        frappe.db.exists(
            "Three PL Container Movement",
            {
                "name": movement_name,
                "movement_type": "Repacked",
                "container_code": "BOX-REPACK-SPLIT-TARGET",
                "from_container": "BOX-REPACK-SPLIT-SOURCE",
                "to_container": "BOX-REPACK-SPLIT-TARGET",
            },
        ),
        "Partial repack did not create movement history",
    )

    cleanup_partial_repack_validation_docs()


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
    for snapshot_name in frappe.get_all(
        "Three PL Inventory Snapshot",
        filters={"container_code": "BOX-PUTAWAY-VALIDATION"},
        pluck="name",
    ):
        frappe.delete_doc("Three PL Inventory Snapshot", snapshot_name, ignore_permissions=True, force=True)
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
    snapshot_name = frappe.db.get_value(
        "Three PL Inventory Snapshot",
        {"customer": container.client, "item_code": "SKU-ALPHA-001", "container_code": container.name},
        "name",
    )
    require(snapshot_name, "Putaway validation did not update client inventory snapshot")
    snapshot = frappe.get_doc("Three PL Inventory Snapshot", snapshot_name)
    require(snapshot.warehouse == "Aisle B - 3", f"Putaway inventory snapshot has wrong location: {snapshot.warehouse}")
    require(snapshot.status == "Available", f"Putaway inventory snapshot has wrong status: {snapshot.status}")
    require(snapshot.qty == 1, f"Putaway inventory snapshot has wrong qty: {snapshot.qty}")

    cleanup_putaway_validation_docs()


def cleanup_picking_validation_docs():
    frappe.set_user("Administrator")
    reference = "PICK-VALIDATION-ALPHA"
    delete_stock_entries({"remarks": ("like", "PICKING-VALIDATION-STOCK%")})
    request_names = frappe.get_all("Three PL Shipment Request", filters={"external_reference": reference}, pluck="name")
    pick_names = frappe.get_all("Pick List", filters={"shipment_request": ("in", request_names)}, pluck="name") if request_names else []
    allocated_containers = set()
    for pick_name in pick_names:
        allocated_containers.update(
            row.container_code
            for row in frappe.get_all(
                "Pick List Item",
                filters={"parent": pick_name, "container_code": ("is", "set")},
                fields=["container_code"],
            )
            if row.container_code
        )
    if pick_names:
        for movement_name in frappe.get_all(
            "Three PL Container Movement",
            filters={"reference_doctype": "Pick List", "reference_name": ("in", pick_names)},
            pluck="name",
        ):
            frappe.delete_doc("Three PL Container Movement", movement_name, ignore_permissions=True, force=True)
    for container_name in allocated_containers:
        if frappe.db.exists("Three PL Container", container_name):
            container = frappe.get_doc("Three PL Container", container_name)
            if container.status == "Picking":
                container.status = "Stored"
                container.save(ignore_permissions=True)
    for movement_name in frappe.get_all(
        "Three PL Container Movement",
        filters={"container_code": "BOX-PICKING-VALIDATION"},
        pluck="name",
    ):
        frappe.delete_doc("Three PL Container Movement", movement_name, ignore_permissions=True, force=True)
    for pick_name in pick_names:
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


def ensure_picking_validation_item():
    item_code = "SKU-PICKING-VALIDATION"
    if frappe.db.exists("Item", item_code):
        item = frappe.get_doc("Item", item_code)
    else:
        item = frappe.get_doc(
            {
                "doctype": "Item",
                "item_code": item_code,
                "item_name": "Picking Validation Product",
                "item_group": "Products",
                "stock_uom": "Nos",
                "is_stock_item": 1,
            }
        )
    item.item_name = "Picking Validation Product"
    item.item_group = "Products"
    item.stock_uom = "Nos"
    if item.meta.has_field("owner_client"):
        item.owner_client = "Demo Client Alpha"
    if item.meta.has_field("client_sku"):
        item.client_sku = "PICK-VALIDATION"
    if item.meta.has_field("client_product_name"):
        item.client_product_name = "Picking Validation Product"
    item.save(ignore_permissions=True)
    return item_code


def ensure_picking_validation_stock(item_code):
    entry = frappe.get_doc(
        {
            "doctype": "Stock Entry",
            "stock_entry_type": "3PL Inbound Receipt",
            "purpose": "Material Receipt",
            "company": "3pl",
            "posting_date": nowdate(),
            "client": "Demo Client Alpha",
            "warehouse_flow": "Inbound Receipt",
            "scanned_location": "Temporary Receiving - 3",
            "container_code": "BOX-PICKING-VALIDATION",
            "remarks": "PICKING-VALIDATION-STOCK temporary stock for picking validation.",
            "items": [
                {
                    "item_code": item_code,
                    "qty": 2,
                    "t_warehouse": "Temporary Receiving - 3",
                    "uom": "Nos",
                    "stock_uom": "Nos",
                    "conversion_factor": 1,
                    "basic_rate": 1,
                    "scanned_location": "Temporary Receiving - 3",
                    "container_code": "BOX-PICKING-VALIDATION",
                }
            ],
        }
    )
    entry.insert(ignore_permissions=True)
    entry.submit()
    return entry.name


def validate_picking_confirmation():
    from erpnext_3pl.sync.inventory_snapshots import sync_inventory_snapshots

    cleanup_picking_validation_docs()
    frappe.set_user("Administrator")
    item_code = ensure_picking_validation_item()

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
                    "item_code": item_code,
                    "client_sku": "PICK-VALIDATION",
                    "qty": 2,
                    "uom": "Nos",
                    "condition_status": "OK",
                }
            ],
        }
    )
    container.insert(ignore_permissions=True)
    ensure_picking_validation_stock(item_code)
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
                    "item_code": item_code,
                    "client_sku": "PICK-VALIDATION",
                    "qty": 2,
                    "uom": "Nos",
                }
            ],
        }
    )
    request.insert(ignore_permissions=True)

    pick_list_name = frappe.db.get_value("Pick List", {"shipment_request": request.name}, "name")
    require(pick_list_name, "Picking validation did not create Pick List")
    pick_list = frappe.get_doc("Pick List", pick_list_name)
    picked = False
    for row in pick_list.locations:
        if row.container_code == "BOX-PICKING-VALIDATION":
            row.picked_qty = row.stock_qty or row.qty
            picked = True
    require(picked, "Picking validation Pick List did not allocate validation container")
    pick_list.save(ignore_permissions=True)

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
    if request_names:
        for pick_name in frappe.get_all("Pick List", filters={"shipment_request": ("in", request_names)}, pluck="name"):
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
    request.status = "Picking"
    request.save(ignore_permissions=True)

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


def validate_client_desk_native_controls():
    receiving_note = "Desk native receiving validation"
    shipment_note = "Desk native shipment validation"
    product_sku = "DESK-NATIVE-PRODUCT"
    forbidden_product_sku = "DESK-NATIVE-BETA"

    frappe.set_user("Administrator")
    for doctype, filters in (
        ("Inbound Shipment Notice", {"notes": receiving_note}),
        ("Three PL Shipment Request", {"notes": shipment_note}),
        ("Three PL Client Product", {"client_sku": product_sku}),
        ("Three PL Client Product", {"client_sku": forbidden_product_sku}),
        ("Three PL Client Instruction", {"instruction_text": ("like", "Desk native validation%")}),
    ):
        for name in frappe.get_all(doctype, filters=filters, pluck="name"):
            if doctype == "Three PL Client Product":
                for log_name in frappe.get_all("Three PL Client Product Change Log", filters={"product": name}, pluck="name"):
                    frappe.delete_doc("Three PL Client Product Change Log", log_name, ignore_permissions=True, force=True)
            frappe.delete_doc(doctype, name, ignore_permissions=True, force=True)
    for item_name in frappe.get_all("Item", filters={"client_sku": ("in", [product_sku, forbidden_product_sku])}, pluck="name"):
        frappe.delete_doc("Item", item_name, ignore_permissions=True, force=True)

    frappe.set_user(CLIENT_DESK_USER)
    notice = frappe.get_doc(
        {
            "doctype": "Inbound Shipment Notice",
            "expected_arrival_date": nowdate(),
            "notes": receiving_note,
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
    notice.insert()
    require(notice.customer == CLIENT_DESK_CUSTOMER, f"Desk receiving notice did not default customer: {notice.customer}")
    require(notice.external_reference.startswith(f"{CLIENT_DESK_RECEIVING_REF_PREFIX}-"), f"Desk receiving notice did not auto-reference: {notice.external_reference}")
    require(notice.status == "Draft", f"Desk receiving notice has wrong initial status: {notice.status}")
    require(notice.portal_source == 1, "Desk receiving notice did not mark portal_source/client source")

    require_permission_error(
        lambda: frappe.get_doc(
            {
                "doctype": "Inbound Shipment Notice",
                "customer": "Demo Client Beta",
                "expected_arrival_date": nowdate(),
                "notes": "Desk native forbidden receiving validation",
            }
        ).insert(),
        "Client Desk user can create receiving notice for another customer",
    )

    frappe.set_user("Administrator")
    frappe.db.set_value("Inbound Shipment Notice", notice.name, "status", "In Verification", update_modified=False)
    frappe.set_user(CLIENT_DESK_USER)
    locked_notice = frappe.get_doc("Inbound Shipment Notice", notice.name)
    locked_notice.notes = "Client attempted edit after warehouse started work"
    require_permission_error(
        lambda: locked_notice.save(),
        "Client Desk user can edit receiving notice after warehouse-controlled status",
    )

    shipment = frappe.get_doc(
        {
            "doctype": "Three PL Shipment Request",
            "requested_ship_date": nowdate(),
            "destination_name": "Desk Native Validation",
            "destination_address": "Validation Address",
            "notes": shipment_note,
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
    require(shipment.customer == CLIENT_DESK_CUSTOMER, f"Desk shipment request did not default customer: {shipment.customer}")
    require(shipment.external_reference.startswith(f"{CLIENT_DESK_SHIPMENT_REF_PREFIX}-"), f"Desk shipment request did not auto-reference: {shipment.external_reference}")
    require(shipment.status == "Submitted", f"Desk shipment request has wrong initial status: {shipment.status}")
    require(shipment.portal_source == 1, "Desk shipment request did not mark portal_source/client source")

    require_permission_error(
        lambda: frappe.get_doc(
            {
                "doctype": "Three PL Shipment Request",
                "customer": "Demo Client Beta",
                "requested_ship_date": nowdate(),
                "destination_name": "Forbidden Desk Native Validation",
            }
        ).insert(),
        "Client Desk user can create shipment request for another customer",
    )

    frappe.set_user("Administrator")
    frappe.db.set_value("Three PL Shipment Request", shipment.name, "status", "Picking", update_modified=False)
    frappe.set_user(CLIENT_DESK_USER)
    locked_shipment = frappe.get_doc("Three PL Shipment Request", shipment.name)
    locked_shipment.notes = "Client attempted edit after picking started"
    require_permission_error(
        lambda: locked_shipment.save(),
        "Client Desk user can edit shipment request after warehouse-controlled status",
    )

    product = frappe.get_doc(
        {
            "doctype": "Three PL Client Product",
            "client_sku": product_sku,
            "product_name": "Desk Native Product",
            "uom": "Nos",
            "notes": "Desk native validation product",
        }
    )
    product.insert()
    require(product.customer == CLIENT_DESK_CUSTOMER, f"Desk product did not default customer: {product.customer}")
    require(product.status == "Active", f"Desk product has wrong initial status: {product.status}")

    require_permission_error(
        lambda: frappe.get_doc(
            {
                "doctype": "Three PL Client Product",
                "customer": "Demo Client Beta",
                "client_sku": forbidden_product_sku,
                "product_name": "Forbidden Desk Native Product",
                "uom": "Nos",
            }
        ).insert(),
        "Client Desk user can create product for another customer",
    )

    instruction = frappe.get_doc(
        {
            "doctype": "Three PL Client Instruction",
            "receiving_notice": notice.name,
            "item_code": "SKU-ALPHA-001",
            "client_sku": "ALPHA-001",
            "instruction_type": "Hold For Review",
            "instruction_text": "Desk native validation instruction",
        }
    )
    instruction.insert()
    require(instruction.customer == CLIENT_DESK_CUSTOMER, f"Desk instruction did not default customer: {instruction.customer}")
    require(instruction.status == "Submitted", f"Desk instruction has wrong initial status: {instruction.status}")
    require(instruction.portal_source == 1, "Desk instruction did not mark portal_source/client source")

    beta_notice = frappe.db.get_value("Inbound Shipment Notice", {"customer": "Demo Client Beta", "external_reference": "ASN-BETA-001"}, "name")
    require(beta_notice, "Missing beta notice for Desk native permission validation")
    require_permission_error(
        lambda: frappe.get_doc(
            {
                "doctype": "Three PL Client Instruction",
                "receiving_notice": beta_notice,
                "instruction_type": "Hold For Review",
                "instruction_text": "Desk native validation forbidden instruction",
            }
        ).insert(),
        "Client Desk user can create instruction against another customer's receiving notice",
    )

    require_permission_error(
        lambda: frappe.get_doc(
            {
                "doctype": "Three PL Client Product Import",
                "customer": CLIENT_DESK_CUSTOMER,
                "import_file": "/private/files/not-part-of-mvp1.csv",
            }
        ).insert(),
        "Client Desk user can create Product Import even though it is outside MVP1",
    )

    frappe.set_user("Administrator")
    frappe.db.rollback()


def validate_client_desk_permissions():
    allowed_ref = "DESK-VALIDATION-ALPHA"
    forbidden_ref = "DESK-VALIDATION-BETA"
    structured_ref = "DESK-STRUCTURED-ALPHA"
    shipment_ref = "DESK-SHIPMENT-ALPHA"
    forbidden_shipment_ref = "DESK-SHIPMENT-BETA"
    structured_shipment_ref = "DESK-SHIPMENT-STRUCTURED-ALPHA"
    product_sku = "DESK-PRODUCT-ALPHA"
    forbidden_product_sku = "DESK-PRODUCT-BETA"
    frappe.set_user("Administrator")
    for reference in (allowed_ref, forbidden_ref, structured_ref):
        existing = frappe.db.get_value("Inbound Shipment Notice", {"external_reference": reference}, "name")
        if existing:
            frappe.delete_doc("Inbound Shipment Notice", existing, ignore_permissions=True, force=True)
    for reference in (shipment_ref, forbidden_shipment_ref, structured_shipment_ref):
        existing = frappe.db.get_value("Three PL Shipment Request", {"external_reference": reference}, "name")
        if existing:
            frappe.delete_doc("Three PL Shipment Request", existing, ignore_permissions=True, force=True)
    for existing in frappe.get_all("Three PL Client Instruction", filters={"instruction_text": ("like", "Desk validation%")}, pluck="name"):
        frappe.delete_doc("Three PL Client Instruction", existing, ignore_permissions=True, force=True)
    for sku in (product_sku, forbidden_product_sku):
        for product_name in frappe.get_all("Three PL Client Product", filters={"client_sku": sku}, pluck="name"):
            for log_name in frappe.get_all("Three PL Client Product Change Log", filters={"product": product_name}, pluck="name"):
                frappe.delete_doc("Three PL Client Product Change Log", log_name, ignore_permissions=True, force=True)
            frappe.delete_doc("Three PL Client Product", product_name, ignore_permissions=True, force=True)
        for item_name in frappe.get_all("Item", filters={"client_sku": sku}, pluck="name"):
            frappe.delete_doc("Item", item_name, ignore_permissions=True, force=True)

    frappe.set_user(CLIENT_DESK_USER)
    allowed = frappe.get_doc(
        {
            "doctype": "Inbound Shipment Notice",
            "customer": CLIENT_DESK_CUSTOMER,
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
    require(allowed.owner == CLIENT_DESK_USER, f"Client-created notice has wrong owner: {allowed.owner}")

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
            "customer": CLIENT_DESK_CUSTOMER,
            "external_reference": shipment_ref,
            "requested_ship_date": frappe.utils.nowdate(),
            "destination_name": "Desk Validation",
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
    require(shipment.owner == CLIENT_DESK_USER, f"Client-created shipment request has wrong owner: {shipment.owner}")

    structured_items_payload = json.dumps(
        {
            "version": 1,
            "source": "client_product_picker",
            "mode": "receiving",
            "items": [
                {
                    "item_code": "SKU-ALPHA-001",
                    "client_sku": "ALPHA-001",
                    "item_name": "Demo Alpha Widget",
                    "uom": "Nos",
                    "expected_qty": 2,
                    "qty": 2,
                    "notes": "Structured receiving validation row",
                }
            ],
        }
    )
    structured_notice = frappe.get_doc(
        {
            "doctype": "Inbound Shipment Notice",
            "customer": CLIENT_DESK_CUSTOMER,
            "external_reference": structured_ref,
            "expected_arrival_date": frappe.utils.nowdate(),
            "portal_source": 1,
            "portal_items_description": structured_items_payload,
        }
    )
    structured_notice.insert()
    require(structured_notice.owner == CLIENT_DESK_USER, f"Structured client notice has wrong owner: {structured_notice.owner}")

    structured_shipment_payload = json.dumps(
        {
            "version": 1,
            "source": "client_product_picker",
            "mode": "shipment",
            "items": [
                {
                    "item_code": "SKU-ALPHA-001",
                    "client_sku": "ALPHA-001",
                    "item_name": "Demo Alpha Widget",
                    "uom": "Nos",
                    "qty": 1,
                    "notes": "Structured shipment validation row",
                }
            ],
        }
    )
    structured_shipment = frappe.get_doc(
        {
            "doctype": "Three PL Shipment Request",
            "customer": CLIENT_DESK_CUSTOMER,
            "external_reference": structured_shipment_ref,
            "requested_ship_date": frappe.utils.nowdate(),
            "destination_name": "Desk Structured Validation",
            "destination_address": "Validation Address",
            "portal_source": 1,
            "portal_items_description": structured_shipment_payload,
        }
    )
    structured_shipment.insert()
    require(structured_shipment.owner == CLIENT_DESK_USER, f"Structured client shipment has wrong owner: {structured_shipment.owner}")

    try:
        forbidden_shipment = frappe.get_doc(
            {
                "doctype": "Three PL Shipment Request",
                "customer": "Demo Client Beta",
                "external_reference": forbidden_shipment_ref,
                "requested_ship_date": frappe.utils.nowdate(),
                "destination_name": "Desk Validation",
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
            "customer": CLIENT_DESK_CUSTOMER,
            "receiving_notice": allowed.name,
            "item_code": "SKU-ALPHA-001",
            "client_sku": "ALPHA-001",
            "instruction_type": "Accept Difference",
            "portal_source": 1,
            "instruction_text": "Desk validation instruction",
        }
    )
    instruction.insert()
    require(instruction.owner == CLIENT_DESK_USER, f"Client-created instruction has wrong owner: {instruction.owner}")
    allowed.reload()
    require(allowed.client_instruction_status == "Instruction Received", "Client instruction did not update receiving notice instruction status")

    product = frappe.get_doc(
        {
            "doctype": "Three PL Client Product",
            "customer": CLIENT_DESK_CUSTOMER,
            "client_sku": product_sku,
            "product_name": "Desk Validation Product",
            "product_description": "Created by Desk validation.",
            "uom": "Nos",
            "barcode": "DESK-PRODUCT-ALPHA-BARCODE",
            "status": "Active",
            "notes": "Desk validation product card.",
        }
    )
    product.insert()
    require(product.owner == CLIENT_DESK_USER, f"Client-created product has wrong owner: {product.owner}")

    try:
        forbidden_product = frappe.get_doc(
            {
                "doctype": "Three PL Client Product",
                "customer": "Demo Client Beta",
                "client_sku": forbidden_product_sku,
                "product_name": "Forbidden Portal Product",
                "uom": "Nos",
                "status": "Active",
            }
        )
        forbidden_product.insert()
    except frappe.PermissionError:
        pass
    else:
        raise RuntimeError("Client user can create product for another customer")

    frappe.set_user("Administrator")
    structured_notice.reload()
    require(len(structured_notice.items) == 1, "Structured receiving notice did not create child item rows")
    require(structured_notice.items[0].item_code == "SKU-ALPHA-001", "Structured receiving item_code is wrong")
    require(structured_notice.items[0].expected_qty == 2, "Structured receiving expected_qty is wrong")

    structured_shipment.reload()
    require(len(structured_shipment.items) == 1, "Structured shipment request did not create child item rows")
    require(structured_shipment.items[0].item_code == "SKU-ALPHA-001", "Structured shipment item_code is wrong")
    require(structured_shipment.items[0].qty == 1, "Structured shipment qty is wrong")

    product.reload()
    item = frappe.get_doc("Item", product.item_code)
    require(product.sync_status == "Synced", "Client product was not synchronized")
    require(product.item_code == item.name, "Client product is not linked to synced Item")
    require(item.owner_client == CLIENT_DESK_CUSTOMER, "Synced Item has wrong owner_client")
    require(item.client_sku == product_sku, "Synced Item has wrong client_sku")
    require(item.item_name == "Desk Validation Product", "Synced Item has wrong item_name")
    require(item.disabled == 0, "Active client product created disabled Item")
    require(
        frappe.db.exists("Three PL Client Product Change Log", {"product": product.name, "action": "Created"}),
        "Client product creation was not logged",
    )

    frappe.set_user(CLIENT_DESK_USER)
    product = frappe.get_doc("Three PL Client Product", product.name)
    product.product_name = "Desk Validation Product Updated"
    product.status = "Inactive"
    product.save()

    frappe.set_user("Administrator")
    product.reload()
    item = frappe.get_doc("Item", product.item_code)
    require(item.item_name == "Desk Validation Product Updated", "Client product update did not sync to Item")
    require(item.disabled == 1, "Inactive client product did not disable Item")
    require(
        frappe.db.exists("Three PL Client Product Change Log", {"product": product.name, "action": "Deactivated"}),
        "Client product deactivation was not logged",
    )

    frappe.set_user(CLIENT_DESK_USER)

    inventory = frappe.get_doc("Three PL Inventory Snapshot", frappe.db.get_value("Three PL Inventory Snapshot", {"customer": CLIENT_DESK_CUSTOMER, "item_code": "SKU-ALPHA-001"}))
    require(inventory.customer == CLIENT_DESK_CUSTOMER, "Client could not read own inventory snapshot")
    balance_snapshot = frappe.get_doc(
        "Three PL Inventory Balance Snapshot",
        frappe.db.get_value("Three PL Inventory Balance Snapshot", {"customer": CLIENT_DESK_CUSTOMER, "item_code": "SKU-ALPHA-001"}),
    )
    require(balance_snapshot.customer == CLIENT_DESK_CUSTOMER, "Client could not read own inventory balance snapshot")

    from erpnext_3pl.api.client_reports import inventory_balance, operation_turnover

    balance_rows = inventory_balance(balance_snapshot.snapshot_date)
    require(balance_rows, "Client inventory balance report returned no rows")
    require(any(row.item_code == "SKU-ALPHA-001" for row in balance_rows), "Client inventory balance report misses own SKU")

    turnover_rows = operation_turnover()
    require(turnover_rows, "Client operation turnover report returned no rows")
    require(
        all(row.operation_type in REQUIRED_CONTAINER_MOVEMENT_TYPES for row in turnover_rows),
        "Client operation turnover report returned an unknown operation type",
    )

    forbidden_docs = [
        ("Item", frappe.db.get_value("Item", {"item_code": "SKU-BETA-001"})),
        ("Three PL Client Product", frappe.db.get_value("Three PL Client Product", {"customer": "Demo Client Beta", "client_sku": "BETA-001"})),
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


if __name__ == "__main__":
    main()
