#!/usr/bin/env python3
"""PostToolUse: ruff-format and auto-fix the Python file that was just edited.

No-op (exit 0) if the edited file is not Python or if ruff is not installed, so it never
blocks editing. Operates only on the single changed file to stay fast.
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
    path = ti.get("file_path") or ""
    if not path.endswith(".py") or not os.path.exists(path):
        sys.exit(0)

    for args in (["format", path], ["check", "--fix", "--quiet", path]):
        try:
            subprocess.run(
                [sys.executable, "-m", "ruff", *args],
                capture_output=True,
                text=True,
                timeout=60,
            )
        except Exception:
            sys.exit(0)  # ruff missing or errored — stay out of the way

    sys.exit(0)


if __name__ == "__main__":
    main()
