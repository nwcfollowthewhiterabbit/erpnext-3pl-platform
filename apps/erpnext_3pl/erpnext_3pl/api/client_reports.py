import frappe
from frappe import _
from frappe.utils import add_days, getdate, nowdate


def _require_login():
    if frappe.session.user == "Guest":
        frappe.throw(_("Login required"), frappe.PermissionError)


def _customer_for_user():
    _require_login()

    allowed = frappe.get_all(
        "User Permission",
        filters={"user": frappe.session.user, "allow": "Customer"},
        pluck="for_value",
        limit=2,
    )
    if len(allowed) != 1:
        frappe.throw(_("A single Customer user permission is required for client reports."), frappe.PermissionError)
    return allowed[0]


def _date_range(from_date=None, to_date=None):
    end = getdate(to_date or nowdate())
    start = getdate(from_date or add_days(end, -30))
    if start > end:
        frappe.throw(_("From Date cannot be after To Date"))
    return start, end


@frappe.whitelist()
def inventory_balance(snapshot_date=None):
    customer = _customer_for_user()
    target_date = getdate(snapshot_date or nowdate())
    return frappe.db.sql(
        """
        select
            bal.snapshot_date,
            bal.item_code,
            bal.client_sku,
            bal.item_name,
            sum(bal.qty) as qty,
            bal.uom,
            bal.status,
            group_concat(distinct bal.warehouse order by bal.warehouse separator ', ') as locations,
            group_concat(distinct bal.container_code order by bal.container_code separator ', ') as containers,
            max(bal.captured_at) as captured_at
        from `tabThree PL Inventory Balance Snapshot` bal
        where bal.customer = %s
          and bal.snapshot_date = %s
        group by bal.snapshot_date, bal.item_code, bal.client_sku, bal.item_name, bal.uom, bal.status
        order by bal.item_code asc, bal.status asc
        """,
        (customer, target_date),
        as_dict=True,
    )


@frappe.whitelist()
def operation_turnover(from_date=None, to_date=None):
    customer = _customer_for_user()
    start, end = _date_range(from_date, to_date)
    return frappe.db.sql(
        """
        select
            date(m.movement_datetime) as operation_date,
            m.movement_datetime as operation_time,
            m.movement_type as operation_type,
            m.container_code,
            m.from_warehouse,
            m.to_warehouse,
            m.from_container,
            m.to_container,
            m.reference_doctype,
            m.reference_name,
            m.notes
        from `tabThree PL Container Movement` m
        where m.client = %s
          and date(m.movement_datetime) between %s and %s
        order by m.movement_datetime desc, m.creation desc
        limit 500
        """,
        (customer, start, end),
        as_dict=True,
    )
