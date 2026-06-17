import ast
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_PROJECT_PATTERN = re.compile(r"run_project_script\.py\s+\S+\s+\S+\s+0(?:\s|$)")
LEGACY_PROJECT_RUN_PATTERN = re.compile(r"run_project_script\.py|docker cp scripts/[^ \n]+\.py|/tmp/[^ \n]+\.py")
APP_ROOT = ROOT / "apps" / "erpnext_3pl" / "erpnext_3pl"
LEGACY_SETUP_MODULE = "setup" + "_site"
LEGACY_APP_IMPORT_PATTERN = re.compile(
    r"(^|\n)\s*((from|import)\s+(project_config|validate_site|sync_[a-z0-9_]+|apply_[a-z0-9_]+)\b|__import__\()"
)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def validate_no_top_level_main_calls():
    offenders = []
    paths = list((ROOT / "scripts").glob("*.py"))
    if APP_ROOT.exists():
        paths.extend(APP_ROOT.rglob("*.py"))

    for path in sorted(paths):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and getattr(node.value.func, "id", None) == "main":
                offenders.append(path.relative_to(ROOT))

    require(
        not offenders,
        "Project scripts must not call main() at import time: " + ", ".join(str(path) for path in offenders),
    )


def validate_explicit_project_script_runs():
    offenders = []
    for base in (ROOT / "scripts", ROOT / "docs"):
        for path in sorted(base.rglob("*")):
            if path.suffix not in {".sh", ".md"}:
                continue
            text = path.read_text(encoding="utf-8")
            if RUN_PROJECT_PATTERN.search(text):
                offenders.append(path.relative_to(ROOT))

    require(
        not offenders,
        "run_project_script.py calls must use explicit call_main=1: " + ", ".join(str(path) for path in offenders),
    )


def validate_deploy_uses_app_methods_not_tmp_scripts():
    offenders = []
    for base in (ROOT / "scripts", ROOT / "docs"):
        for path in sorted(base.rglob("*")):
            if path.name == "validate_repo.py" or path.suffix not in {".sh", ".md"}:
                continue
            text = path.read_text(encoding="utf-8")
            if LEGACY_PROJECT_RUN_PATTERN.search(text):
                offenders.append(path.relative_to(ROOT))

    require(
        not offenders,
        "Deploy/validation entrypoints must call app methods, not /tmp legacy scripts: " + ", ".join(str(path) for path in offenders),
    )


def validate_app_has_no_legacy_script_imports():
    if not APP_ROOT.exists():
        return

    offenders = []
    for path in sorted(APP_ROOT.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        if LEGACY_APP_IMPORT_PATTERN.search(text) or re.search(r"/tmp/[^ \n'\"]+\.py", text):
            offenders.append(path.relative_to(ROOT))

    require(
        not offenders,
        "ERPNext 3PL app modules must use package imports, not legacy script imports: " + ", ".join(str(path) for path in offenders),
    )


def validate_legacy_setup_script_removed():
    setup_path = APP_ROOT / f"{LEGACY_SETUP_MODULE}.py"
    require(
        not setup_path.exists(),
        "legacy broad setup module must not be restored; use focused bootstrap/maintenance modules",
    )


def validate_setup_not_run_after_migrate():
    hooks = APP_ROOT / "hooks.py"
    if not hooks.exists():
        return

    text = hooks.read_text(encoding="utf-8")
    require(
        "after_migrate" not in text or LEGACY_SETUP_MODULE not in text,
        "legacy broad setup must not run automatically on every bench migrate",
    )


def validate_no_legacy_setup_references():
    offenders = []
    for base in (APP_ROOT, ROOT / "scripts", ROOT / "docs", ROOT / ".github"):
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_dir() or path.suffix not in {".py", ".sh", ".md", ".yml", ".yaml"}:
                continue
            if path.name == "validate_repo.py":
                continue
            text = path.read_text(encoding="utf-8")
            if LEGACY_SETUP_MODULE in text:
                offenders.append(path.relative_to(ROOT))

    require(
        not offenders,
        "legacy broad setup references must be removed: " + ", ".join(str(path) for path in offenders),
    )


def main():
    validate_no_top_level_main_calls()
    validate_explicit_project_script_runs()
    validate_deploy_uses_app_methods_not_tmp_scripts()
    validate_app_has_no_legacy_script_imports()
    validate_legacy_setup_script_removed()
    validate_setup_not_run_after_migrate()
    validate_no_legacy_setup_references()
    print("Repository validation passed")


if __name__ == "__main__":
    main()
