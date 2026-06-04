import frappe


REQUIRED_WORKSPACES = ["3PL Warehouse", "Stock Reference"]
REQUIRED_USERS = {
    "warehouse.demo@example.test": ["Stock User", "3PL Warehouse User"],
    "warehouse.manager@example.test": ["Stock User", "Stock Manager", "3PL Warehouse Manager"],
    "rupusm@gmail.com": ["System Manager", "Stock User", "Stock Manager", "Item Manager", "3PL Warehouse Manager"],
    "alpha.client@example.test": ["3PL Client"],
}
REQUIRED_DOCTYPES = [
    "Inbound Shipment Notice",
    "Inbound Shipment Notice Item",
    "Inbound Shipment Discrepancy",
    "Three PL Container",
    "Three PL Container Item",
]
REQUIRED_REPORTS = ["3PL ASN vs Received", "3PL Receiving Discrepancies", "3PL Containers"]
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
REQUIRED_COUNTRY = "Lithuania"
REQUIRED_CURRENCY = "EUR"
REQUIRED_LANGUAGE = "en"
REQUIRED_TIME_ZONE = "Europe/Vilnius"
REQUIRED_PLACEHOLDER_EMAIL = "noreply@example.invalid"
CLIENT_PORTAL_USER = "alpha.client@example.test"
CLIENT_PORTAL_CUSTOMER = "Demo Client Alpha"
CLIENT_PORTAL_ROUTE = "client/receiving-notice"


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
        expected_module_profile = None if user in {"rupusm@gmail.com", CLIENT_PORTAL_USER} else "Warehouse Only"
        require(doc.module_profile == expected_module_profile, f"Wrong module profile for {user}: {doc.module_profile}")
        expected_workspace = None if user == CLIENT_PORTAL_USER else "3PL Warehouse"
        require(doc.default_workspace == expected_workspace, f"Wrong default workspace for {user}: {doc.default_workspace}")
        if doc.meta.has_field("default_app"):
            expected_app = None if user == CLIENT_PORTAL_USER else "erpnext"
            require(doc.default_app == expected_app, f"Wrong default app for {user}: {doc.default_app}")
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

    client_role = frappe.get_doc("Role", "3PL Client")
    if client_role.meta.has_field("desk_access"):
        require(client_role.desk_access == 0, "3PL Client role must not have Desk access")
    require(client_role.home_page == CLIENT_PORTAL_ROUTE, f"Wrong 3PL Client home_page: {client_role.home_page}")

    require(
        frappe.db.exists("Portal Menu Item", {"title": "Receiving Notices", "route": CLIENT_PORTAL_ROUTE, "role": "3PL Client", "enabled": 1}),
        "Missing client portal menu item",
    )
    portal_settings = frappe.get_single("Portal Settings")
    require(portal_settings.default_portal_home == CLIENT_PORTAL_ROUTE, f"Wrong default portal home: {portal_settings.default_portal_home}")
    web_form_name = frappe.db.get_value("Web Form", {"route": CLIENT_PORTAL_ROUTE}, "name")
    require(web_form_name, "Missing client receiving Web Form")
    web_form = frappe.get_doc("Web Form", web_form_name)
    require(web_form.title == "3PL Client Receiving Notice", f"Wrong client Web Form title: {web_form.title}")
    require(web_form.route == CLIENT_PORTAL_ROUTE, f"Wrong client Web Form route: {web_form.route}")
    require(web_form.login_required == 1, "Client Web Form must require login")
    require(web_form.apply_document_permissions == 1, "Client Web Form must apply document permissions")
    require(web_form.allow_multiple == 1, "Client Web Form must allow multiple notices")
    require({row.fieldname for row in web_form.web_form_fields} >= {"customer", "external_reference", "expected_arrival_date", "items"}, "Client Web Form misses required fields")

    require(
        frappe.db.exists("User Permission", {"user": CLIENT_PORTAL_USER, "allow": "Customer", "for_value": CLIENT_PORTAL_CUSTOMER}),
        "Missing client Customer User Permission",
    )
    require(
        frappe.db.exists("Contact", {"user": CLIENT_PORTAL_USER}),
        "Missing client Contact link",
    )

    for doctype in ("Inbound Shipment Notice", "Three PL Container"):
        require_role_perm(doctype, "3PL Warehouse User", read=1, write=1, create=1)
        require_role_perm(doctype, "3PL Warehouse Manager", read=1, write=1, create=1, delete=1)
        require_role_perm(doctype, "System Manager", read=1, write=1, create=1, delete=1)
    require_role_perm("Inbound Shipment Notice", "3PL Client", read=1, write=1, create=1)
    require_role_perm("Item", "3PL Client", read=1)
    require_role_perm("Three PL Container", "3PL Client", read=1)

    owner_roles = [row.role for row in frappe.get_doc("User", "rupusm@gmail.com").roles]
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

    expected_items = {
        "SKU-ALPHA-001": ("Demo Client Alpha", "ALPHA-001"),
        "SKU-ALPHA-002": ("Demo Client Alpha", "ALPHA-002"),
        "SKU-BETA-001": ("Demo Client Beta", "BETA-001"),
    }
    for item_code, (client, client_sku) in expected_items.items():
        require(frappe.db.exists("Item", item_code), f"Missing demo Item: {item_code}")
        require(frappe.db.get_value("Item", item_code, "owner_client") == client, f"Wrong owner_client for {item_code}")
        require(frappe.db.get_value("Item", item_code, "client_sku") == client_sku, f"Wrong client_sku for {item_code}")

    container = frappe.get_doc("Three PL Container", "BOX-ALPHA-001")
    require(container.client == "Demo Client Alpha", "Demo container has wrong client")
    require(container.current_warehouse == "Temporary Receiving - 3", "Demo container has wrong location")
    require(container.inbound_shipment_notice == notice_name, "Demo container is not linked to demo ASN")
    require(any(row.item_code == "SKU-ALPHA-002" and row.qty == 24 for row in container.items), "Demo container misses expected item row")

    notice = frappe.get_doc("Inbound Shipment Notice", notice_name)
    require(
        any(row.discrepancy_type == "Quantity Difference" and row.item_code == "SKU-ALPHA-002" and row.variance_qty == -1 for row in notice.discrepancies),
        "Demo ASN misses quantity discrepancy",
    )

    validate_client_portal_permissions()

    print("Site validation passed")


def validate_client_portal_permissions():
    allowed_ref = "PORTAL-VALIDATION-ALPHA"
    forbidden_ref = "PORTAL-VALIDATION-BETA"
    frappe.set_user("Administrator")
    for reference in (allowed_ref, forbidden_ref):
        existing = frappe.db.get_value("Inbound Shipment Notice", {"external_reference": reference}, "name")
        if existing:
            frappe.delete_doc("Inbound Shipment Notice", existing, ignore_permissions=True, force=True)

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
    finally:
        frappe.set_user("Administrator")
        frappe.db.rollback()


main()
