import json
import os
import re
from copy import deepcopy

import frappe

from erpnext_3pl.config.fixtures import FIXTURES


VOLATILE_KEYS = {
    "_assign",
    "_comments",
    "_liked_by",
    "_user_tags",
    "creation",
    "modified",
    "modified_by",
    "owner",
}


def _fixture_filename(doctype):
    filename = re.sub(r"[^a-z0-9]+", "_", doctype.lower()).strip("_")
    return f"{filename}.json"


def _scrub(value):
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _clean(value):
    if isinstance(value, dict):
        return {
            key: _clean(child)
            for key, child in value.items()
            if key not in VOLATILE_KEYS and child is not None
        }
    if isinstance(value, list):
        return [_clean(child) for child in value]
    return value


def _get_names(doctype, filters):
    return frappe.get_all(
        doctype,
        filters=filters,
        pluck="name",
        order_by="name asc",
        ignore_permissions=True,
    )


def export(path=None):
    """Export the app-owned schema/UI records into deterministic fixture JSON."""
    target_dir = path or frappe.get_app_path("erpnext_3pl", "fixtures")
    os.makedirs(target_dir, exist_ok=True)

    grouped = {}
    for fixture in FIXTURES:
        doctype = fixture["dt"]
        filters = fixture.get("filters")
        grouped.setdefault(doctype, set()).update(_get_names(doctype, filters))

    written = {}
    for doctype in sorted(grouped):
        docs = []
        for name in sorted(grouped[doctype]):
            doc = frappe.get_doc(doctype, name)
            data = _clean(deepcopy(doc.as_dict(no_nulls=False)))
            docs.append(data)

        fixture_path = os.path.join(target_dir, _fixture_filename(doctype))
        with open(fixture_path, "w", encoding="utf-8") as handle:
            json.dump(docs, handle, indent=2, sort_keys=True)
            handle.write("\n")
        written[doctype] = {"count": len(docs), "path": fixture_path}

    return written


def export_workspaces(path=None):
    """Export Workspaces using Frappe's native module workspace layout."""
    base_dir = path or frappe.get_app_path("erpnext_3pl", "erpnext_3pl", "workspace")
    os.makedirs(base_dir, exist_ok=True)

    written = {}
    for name in ("3PL Warehouse", "Stock Reference"):
        doc = frappe.get_doc("Workspace", name)
        data = _clean(deepcopy(doc.as_dict(no_nulls=False)))
        data["app"] = "erpnext_3pl"
        data["module"] = "ERPNext 3PL"

        workspace_id = _scrub(name)
        workspace_dir = os.path.join(base_dir, workspace_id)
        os.makedirs(workspace_dir, exist_ok=True)
        workspace_path = os.path.join(workspace_dir, f"{workspace_id}.json")
        with open(workspace_path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=1, sort_keys=True)
            handle.write("\n")
        written[name] = workspace_path

    return written
