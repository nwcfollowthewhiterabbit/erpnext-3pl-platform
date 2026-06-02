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


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    require(frappe.is_setup_complete(), "Setup wizard is not marked complete")

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

    print("Site validation passed")


main()
