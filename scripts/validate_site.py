import frappe


REQUIRED_WORKSPACES = ["3PL Warehouse", "Stock Reference"]
REQUIRED_USERS = {
    "warehouse.demo@example.test": ["Stock User", "3PL Warehouse User"],
    "warehouse.manager@example.test": ["Stock User", "Stock Manager", "3PL Warehouse Manager"],
    "rupusm@gmail.com": ["System Manager", "Stock User", "Stock Manager", "3PL Warehouse Manager"],
}
REQUIRED_DOCTYPES = ["Inbound Shipment Notice", "Inbound Shipment Notice Item"]
REQUIRED_REPORTS = ["3PL ASN vs Received"]
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


def require(condition, message):
    if not condition:
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

    for doctype in REQUIRED_DOCTYPES:
        require(frappe.db.exists("DocType", doctype), f"Missing DocType: {doctype}")

    for report in REQUIRED_REPORTS:
        require(frappe.db.exists("Report", report), f"Missing Report: {report}")

    for warehouse in REQUIRED_WAREHOUSES:
        require(frappe.db.exists("Warehouse", warehouse), f"Missing Warehouse: {warehouse}")

    for user, roles in REQUIRED_USERS.items():
        require(frappe.db.exists("User", user), f"Missing User: {user}")
        doc = frappe.get_doc("User", user)
        user_roles = {row.role for row in doc.roles}
        require(doc.enabled == 1, f"User is disabled: {user}")
        expected_module_profile = None if user == "rupusm@gmail.com" else "Warehouse Only"
        require(doc.module_profile == expected_module_profile, f"Wrong module profile for {user}: {doc.module_profile}")
        require(doc.default_workspace == "3PL Warehouse", f"Wrong default workspace for {user}: {doc.default_workspace}")
        if doc.meta.has_field("default_app"):
            require(doc.default_app == "erpnext", f"Wrong default app for {user}: {doc.default_app}")
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

    require(frappe.db.exists("Inbound Shipment Notice", {"external_reference": "ASN-ALPHA-001"}), "Missing demo ASN")
    require(frappe.db.exists("Stock Entry", {"client": "Demo Client Alpha", "warehouse_flow": "Inbound Receipt"}), "Missing demo Stock Entry")
    for customer in ("Demo Client Alpha", "Demo Client Beta"):
        require(frappe.db.get_value("Customer", customer, "territory") == REQUIRED_COUNTRY, f"Wrong customer territory: {customer}")

    print("Site validation passed")


main()
