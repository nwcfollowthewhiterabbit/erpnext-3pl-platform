import re
from datetime import datetime

import frappe
from frappe import _

from erpnext_3pl.config.project_config import (
    CLIENT_DESK_CUSTOMER,
    CLIENT_DESK_RECEIVING_REF_PREFIX,
    CLIENT_DESK_SHIPMENT_REF_PREFIX,
)


CLIENT_ROLE = "3PL Client"
PRIVILEGED_ROLES = {"System Manager", "3PL Warehouse Manager", "3PL Warehouse User", "Stock Manager", "Stock User"}


def is_client_desk_user(user=None):
    user = user or frappe.session.user
    if user in {"Administrator", "Guest"}:
        return False
    roles = set(frappe.get_roles(user))
    return CLIENT_ROLE in roles and not roles.intersection(PRIVILEGED_ROLES)


def get_allowed_customer(user=None):
    user = user or frappe.session.user
    customers = frappe.get_all(
        "User Permission",
        filters={"user": user, "allow": "Customer"},
        pluck="for_value",
        order_by="creation asc",
    )
    if len(customers) != 1:
        frappe.throw(
            _("Client user {0} must have exactly one Customer User Permission.").format(user),
            frappe.PermissionError,
        )
    return customers[0]


def set_client_customer(doc):
    if not is_client_desk_user():
        return
    customer = get_allowed_customer()
    if doc.get("customer") and doc.customer != customer:
        frappe.throw(_("You can only create or update documents for your assigned customer."), frappe.PermissionError)
    doc.customer = customer
    if doc.meta.has_field("portal_source"):
        doc.portal_source = 1


def client_reference_prefix(doc, fallback_prefix):
    customer = doc.get("customer")
    if customer == CLIENT_DESK_CUSTOMER:
        return fallback_prefix
    base = re.sub(r"[^A-Z0-9]+", "-", (customer or "CLIENT").upper()).strip("-")
    return f"{base[:24]}-{fallback_prefix.rsplit('-', 1)[-1]}"


def set_reference_if_missing(doc, fallback_prefix):
    if doc.get("external_reference"):
        return
    prefix = client_reference_prefix(doc, fallback_prefix)
    date_part = datetime.utcnow().strftime("%Y%m%d")
    base = f"{prefix}-{date_part}"
    existing_refs = frappe.get_all(
        doc.doctype,
        filters={"external_reference": ("like", f"{base}-%")},
        pluck="external_reference",
        order_by="external_reference desc",
        limit_page_length=1,
    )
    next_number = 1
    if existing_refs:
        match = re.search(r"-(\d+)$", existing_refs[0] or "")
        if match:
            next_number = int(match.group(1)) + 1
    doc.external_reference = f"{base}-{next_number:03d}"


def set_initial_status(doc, status):
    if is_client_desk_user() and doc.is_new():
        doc.status = status


def freeze_status_for_client(doc, allowed_initial_status):
    if frappe.flags.get("three_pl_internal_status_sync"):
        return
    if not is_client_desk_user() or doc.is_new():
        return
    previous = frappe.db.get_value(doc.doctype, doc.name, "status")
    locked_statuses = {
        "In Verification",
        "Partially Received",
        "Discrepancy Review",
        "Received",
        "Closed",
        "Accepted",
        "Picking",
        "Packed",
        "Shipped",
        "Cancelled",
        "Reviewed",
        "Applied",
    }
    if previous in locked_statuses:
        frappe.throw(_("This document is already controlled by the warehouse team."), frappe.PermissionError)
    if previous and doc.status != previous:
        frappe.throw(_("Warehouse status is managed by the warehouse team."), frappe.PermissionError)
    if not previous:
        doc.status = allowed_initial_status


def prepare_inbound_notice(doc):
    set_client_customer(doc)
    set_reference_if_missing(doc, CLIENT_DESK_RECEIVING_REF_PREFIX)
    set_initial_status(doc, "Draft")
    freeze_status_for_client(doc, "Draft")


def prepare_shipment_request(doc):
    set_client_customer(doc)
    set_reference_if_missing(doc, CLIENT_DESK_SHIPMENT_REF_PREFIX)
    set_initial_status(doc, "Submitted")
    freeze_status_for_client(doc, "Submitted")


def prepare_client_product(doc):
    set_client_customer(doc)
    if is_client_desk_user() and doc.is_new():
        doc.status = doc.status or "Active"


def prepare_client_product_import(doc):
    set_client_customer(doc)


def prepare_client_instruction(doc):
    set_client_customer(doc)
    if doc.receiving_notice:
        notice_customer = frappe.db.get_value("Inbound Shipment Notice", doc.receiving_notice, "customer")
        if notice_customer and doc.customer and notice_customer != doc.customer:
            frappe.throw(_("Instruction receiving notice must belong to your assigned customer."), frappe.PermissionError)
    if is_client_desk_user() and doc.is_new():
        doc.status = "Submitted"
    freeze_status_for_client(doc, "Submitted")
