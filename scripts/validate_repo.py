import ast
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_PROJECT_PATTERN = re.compile(r"run_project_script\.py\s+\S+\s+\S+\s+0(?:\s|$)")


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def validate_no_top_level_main_calls():
    offenders = []
    for path in sorted((ROOT / "scripts").glob("*.py")):
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


def main():
    validate_no_top_level_main_calls()
    validate_explicit_project_script_runs()
    print("Repository validation passed")


if __name__ == "__main__":
    main()
