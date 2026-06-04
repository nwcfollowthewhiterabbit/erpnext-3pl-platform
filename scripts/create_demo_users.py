import frappe

from project_config import (
    BUSINESS_OWNER_PASSWORD,
    BUSINESS_OWNER_USER,
    CLIENT_PORTAL_CUSTOMER,
    CLIENT_PORTAL_PASSWORD,
    CLIENT_PORTAL_USER,
    COUNTRY,
    WAREHOUSE_MANAGER_PASSWORD,
    WAREHOUSE_MANAGER_USER,
    WAREHOUSE_OPERATOR_PASSWORD,
    WAREHOUSE_OPERATOR_USER,
)


USERS = [
    {
        "email": WAREHOUSE_OPERATOR_USER,
        "first_name": "Warehouse",
        "last_name": "Demo",
        "password": WAREHOUSE_OPERATOR_PASSWORD,
        "roles": ["Stock User", "3PL Warehouse User"],
    },
    {
        "email": WAREHOUSE_MANAGER_USER,
        "first_name": "Warehouse",
        "last_name": "Manager",
        "password": WAREHOUSE_MANAGER_PASSWORD,
        "roles": ["Stock User", "Stock Manager", "3PL Warehouse Manager"],
    },
    {
        "email": BUSINESS_OWNER_USER,
        "first_name": "Nerijus",
        "last_name": "",
        "password": BUSINESS_OWNER_PASSWORD,
        "roles": "__all_standard_roles__",
        "module_profile": None,
    },
    {
        "email": CLIENT_PORTAL_USER,
        "first_name": "Alpha",
        "last_name": "Client",
        "password": CLIENT_PORTAL_PASSWORD,
        "roles": ["3PL Client"],
        "user_type": "Website User",
        "customer": CLIENT_PORTAL_CUSTOMER,
        "module_profile": None,
        "default_workspace": None,
        "default_app": None,
    },
]

AUTOMATIC_ROLES = {"All", "Guest", "Desk User"}


def ensure_customer_master_data():
    if not frappe.db.exists("Customer Group", "Commercial"):
        frappe.get_doc(
            {
                "doctype": "Customer Group",
                "customer_group_name": "Commercial",
                "is_group": 0,
            }
        ).insert(ignore_permissions=True)

    if not frappe.db.exists("Territory", COUNTRY):
        frappe.get_doc(
            {
                "doctype": "Territory",
                "territory_name": COUNTRY,
                "is_group": 0,
            }
        ).insert(ignore_permissions=True)


def ensure_customer(customer_name):
    ensure_customer_master_data()
    if frappe.db.exists("Customer", customer_name):
        customer = frappe.get_doc("Customer", customer_name)
    else:
        customer = frappe.new_doc("Customer")
        customer.customer_name = customer_name
        customer.customer_type = "Company"

    customer.customer_group = "Commercial"
    customer.territory = COUNTRY
    customer.save(ignore_permissions=True)
    return customer


def ensure_user(user_data):
    email = user_data["email"]
    if user_data.get("customer"):
        ensure_customer(user_data["customer"])

    if frappe.db.exists("User", email):
        user = frappe.get_doc("User", email)
    else:
        user = frappe.get_doc(
            {
                "doctype": "User",
                "email": email,
                "username": email,
                "first_name": user_data["first_name"],
                "last_name": user_data["last_name"],
                "enabled": 1,
                "send_welcome_email": 0,
                "user_type": user_data.get("user_type", "System User"),
            }
        )

    user.enabled = 1
    user.user_type = user_data.get("user_type", "System User")
    if "module_profile" in user_data:
        user.module_profile = user_data["module_profile"]
    else:
        user.module_profile = "Warehouse Only" if frappe.db.exists("Module Profile", "Warehouse Only") else None
    if "default_workspace" in user_data:
        user.default_workspace = user_data["default_workspace"]
    else:
        user.default_workspace = "3PL Warehouse" if frappe.db.exists("Workspace", "3PL Warehouse") else None
    if user.meta.has_field("default_app"):
        user.default_app = user_data.get("default_app", "erpnext")
    user.set("roles", [])
    roles = user_data["roles"]
    if roles == "__all_standard_roles__":
        roles = sorted(
            role.name
            for role in frappe.get_all("Role", fields=["name", "disabled"])
            if not role.disabled and role.name not in AUTOMATIC_ROLES
        )

    for role in roles:
        user.append("roles", {"role": role})

    user.save(ignore_permissions=True)
    user.new_password = user_data["password"]
    user.save(ignore_permissions=True)

    if user_data.get("customer"):
        ensure_customer_link(email, user_data["customer"], user_data["first_name"], user_data["last_name"])
        ensure_user_permission(email, "Customer", user_data["customer"])

    return user


def ensure_customer_link(email, customer, first_name, last_name):
    contact_name = frappe.db.get_value("Contact", {"email_id": email}, "name")
    if contact_name:
        contact = frappe.get_doc("Contact", contact_name)
    else:
        contact = frappe.new_doc("Contact")
        contact.first_name = first_name
        contact.last_name = last_name
        contact.email_id = email

    contact.user = email
    if not any(row.link_doctype == "Customer" and row.link_name == customer for row in contact.links):
        contact.append("links", {"link_doctype": "Customer", "link_name": customer})
    contact.save(ignore_permissions=True)


def ensure_user_permission(user, allow, for_value):
    filters = {"user": user, "allow": allow, "for_value": for_value}
    if frappe.db.exists("User Permission", filters):
        permission = frappe.get_doc("User Permission", filters)
    else:
        permission = frappe.new_doc("User Permission")
        permission.user = user
        permission.allow = allow
        permission.for_value = for_value

    permission.apply_to_all_doctypes = 1
    permission.save(ignore_permissions=True)


def main():
    for user_data in USERS:
        ensure_user(user_data)

    frappe.db.commit()
    frappe.clear_cache()
