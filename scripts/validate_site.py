import frappe

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
    "Three PL Inventory Snapshot",
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
REQUIRED_REPORTS = [
    "3PL ASN vs Received",
    "3PL Receiving Discrepancies",
    "3PL Containers",
    "3PL Container Moves",
    "3PL Container Movements",
    "3PL Shipment Requests",
    "3PL Client Inventory",
]
REQUIRED_CUSTOM_FIELDS = [
    "Item-owner_client",
    "Item-client_sku",
    "Item-client_product_name",
    "Stock Entry-container_code",
    "Stock Entry Detail-container_code",
    "Pick List-container_code",
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
    move_meta = frappe.get_meta("Three PL Container Move")
    move_fields = {field.fieldname for field in move_meta.fields}
    require(move_fields >= REQUIRED_CONTAINER_MOVE_FIELDS, "Three PL Container Move misses required fields")

    for report in REQUIRED_REPORTS:
        require(frappe.db.exists("Report", report), f"Missing Report: {report}")
        report_doc = frappe.get_doc("Report", report)
        if report_doc.report_type == "Query Report":
            frappe.db.sql(report_doc.query)

    for custom_field in REQUIRED_CUSTOM_FIELDS:
        require(frappe.db.exists("Custom Field", custom_field), f"Missing Custom Field: {custom_field}")

    for warehouse in REQUIRED_WAREHOUSES:
        require(frappe.db.exists("Warehouse", warehouse), f"Missing Warehouse: {warehouse}")

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

    for doctype in ("Inbound Shipment Notice", "Three PL Container", "Three PL Container Move", "Three PL Container Movement"):
        require_role_perm(doctype, "3PL Warehouse User", read=1, write=1, create=1)
        require_role_perm(doctype, "3PL Warehouse Manager", read=1, write=1, create=1, delete=1)
        require_role_perm(doctype, "System Manager", read=1, write=1, create=1, delete=1)
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
    require_role_perm("Three PL Inventory Snapshot", "3PL Client", read=1)
    require_role_perm("Three PL Shipment Request", "3PL Client", read=1, write=1, create=1)
    require_role_perm("Three PL Shipment Request Item", "3PL Client", read=1, write=1, create=1)
    require_role_perm("Three PL Client Instruction", "3PL Client", read=1, write=1, create=1)

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
    require(storage_container.status == "Stored", "Applied container move did not update container status")

    notice = frappe.get_doc("Inbound Shipment Notice", notice_name)
    require(
        any(row.discrepancy_type == "Quantity Difference" and row.item_code == "SKU-ALPHA-002" and row.variance_qty == -1 for row in notice.discrepancies),
        "Demo ASN misses quantity discrepancy",
    )
    require(frappe.db.exists("Three PL Inventory Snapshot", {"customer": "Demo Client Alpha", "item_code": "SKU-ALPHA-001"}), "Missing demo client inventory snapshot")
    require(frappe.db.exists("Three PL Inventory Snapshot", {"customer": "Demo Client Beta", "item_code": "SKU-BETA-001"}), "Missing demo beta inventory snapshot")
    require(frappe.db.exists("Inbound Shipment Notice", {"customer": "Demo Client Beta", "external_reference": "ASN-BETA-001"}), "Missing demo beta ASN")
    require(frappe.db.exists("Three PL Shipment Request", {"customer": "Demo Client Alpha", "external_reference": "SHIP-ALPHA-001"}), "Missing demo shipment request")
    require(frappe.db.exists("Three PL Client Instruction", {"customer": "Demo Client Alpha", "receiving_notice": notice_name}), "Missing demo client discrepancy instruction")

    validate_client_portal_permissions()

    print("Site validation passed")


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

    forbidden_docs = [
        ("Item", frappe.db.get_value("Item", {"item_code": "SKU-BETA-001"})),
        ("Inbound Shipment Notice", frappe.db.get_value("Inbound Shipment Notice", {"customer": "Demo Client Beta", "external_reference": "ASN-BETA-001"})),
        ("Three PL Inventory Snapshot", frappe.db.get_value("Three PL Inventory Snapshot", {"customer": "Demo Client Beta", "item_code": "SKU-BETA-001"})),
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
