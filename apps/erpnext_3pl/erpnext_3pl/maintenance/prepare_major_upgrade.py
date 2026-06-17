import frappe


def main():
    # Frappe v16 no longer ships frappe.social, but v15 sites can retain its
    # standard Module Def. Leaving it in place makes bench migrate import a
    # module that no longer exists.
    if frappe.db.exists("Module Def", "Social"):
        frappe.db.sql(
            "delete from `tabModule Def` where name = %s and app_name = %s",
            ("Social", "frappe"),
        )
