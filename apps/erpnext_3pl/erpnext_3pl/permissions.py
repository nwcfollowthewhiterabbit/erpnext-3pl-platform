import frappe

from erpnext_3pl.client_desk import is_client_desk_user


def user_query_condition(user=None):
    user = user or frappe.session.user
    if not is_client_desk_user(user):
        return None
    return f"`tabUser`.`name` = {frappe.db.escape(user)}"


def user_has_permission(doc, user=None, permission_type=None):
    user = user or frappe.session.user
    if not is_client_desk_user(user):
        return None
    return doc.name == user
