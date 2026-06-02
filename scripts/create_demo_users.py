import frappe


USERS = [
    {
        "email": "warehouse.demo@example.test",
        "first_name": "Warehouse",
        "last_name": "Demo",
        "password": "WarehouseDemo2026!",
        "roles": ["Stock User", "3PL Warehouse User"],
    },
    {
        "email": "warehouse.manager@example.test",
        "first_name": "Warehouse",
        "last_name": "Manager",
        "password": "WarehouseManager2026!",
        "roles": ["Stock User", "Stock Manager", "3PL Warehouse Manager"],
    },
    {
        "email": "rupusm@gmail.com",
        "first_name": "Nerijus",
        "last_name": "",
        "password": "6elz4oeiuUGAHSGRccwngNmb",
        "roles": ["System Manager", "Stock User", "Stock Manager", "3PL Warehouse Manager"],
        "module_profile": None,
    },
]


def ensure_user(user_data):
    email = user_data["email"]
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
                "user_type": "System User",
            }
        )

    user.enabled = 1
    if "module_profile" in user_data:
        user.module_profile = user_data["module_profile"]
    else:
        user.module_profile = "Warehouse Only" if frappe.db.exists("Module Profile", "Warehouse Only") else None
    user.default_workspace = "3PL Warehouse" if frappe.db.exists("Workspace", "3PL Warehouse") else None
    if user.meta.has_field("default_app"):
        user.default_app = "erpnext"
    user.set("roles", [])
    for role in user_data["roles"]:
        user.append("roles", {"role": role})

    user.save(ignore_permissions=True)
    user.new_password = user_data["password"]
    user.save(ignore_permissions=True)
    return user


def main():
    for user_data in USERS:
        ensure_user(user_data)

    frappe.db.commit()
    frappe.clear_cache()
