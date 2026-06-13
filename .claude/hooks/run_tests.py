#!/usr/bin/env python3
"""PostToolUse: run pytest when an app/ or tests/ Python file changes.

Surfaces failures back to Claude (exit 2 with a trimmed tail) so regressions are caught
immediately. Stays quiet (exit 0) when tests pass, when none are collected, or when pytest
is not installed.
"""
import json
import os
import subprocess
import sys


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    ti = data.get("tool_input", {}) or {}
    path = (ti.get("file_path") or "").replace("\\", "/")
    if not path.endswith(".py"):
        sys.exit(0)
    if "/app/" not in path and "/tests/" not in path:
        sys.exit(0)
    if not os.path.isdir("tests"):
        sys.exit(0)

    try:
        r = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--no-header"],
            capture_output=True,
            text=True,
            timeout=180,
        )
    except Exception:
        sys.exit(0)

    out = (r.stdout or "") + (r.stderr or "")
    # 0 = passed, 5 = no tests collected; pytest not installed -> stay quiet.
    if r.returncode in (0, 5) or "No module named pytest" in out:
        sys.exit(0)

    tail = "\n".join(out.strip().splitlines()[-25:])
    print("pytest failed after this edit:\n" + tail, file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
