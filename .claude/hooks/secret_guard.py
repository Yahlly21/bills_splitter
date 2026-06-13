#!/usr/bin/env python3
"""PreToolUse guard: block reading, printing, or committing the .env / ANTHROPIC_API_KEY.

The app ships a real Claude API key. This hook keeps it out of the transcript and out of
git: it denies tool calls that would read the .env file or expose the key via the shell.
`.env.example` / `.env.sample` are always allowed. Exits 2 (with a reason on stderr) to
block the call; exits 0 to allow.
"""
import json
import os
import re
import sys


def deny(msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(2)


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool = data.get("tool_name", "")
    ti = data.get("tool_input", {}) or {}

    # Direct file reads of the secret file.
    if tool == "Read":
        base = os.path.basename((ti.get("file_path") or "").replace("\\", "/"))
        if base.startswith(".env") and not base.endswith((".example", ".sample")):
            deny(
                f"Blocked by secret-guard hook: {base} holds ANTHROPIC_API_KEY and must not "
                "be read into the transcript. See .env.example for the shareable template."
            )

    # Shell commands that would expose or commit the secret.
    if tool in ("Bash", "PowerShell"):
        cmd = (ti.get("command", "") or "").lower()
        mentions_env = bool(re.search(r"\.env\b", cmd)) and ".env.example" not in cmd and ".env.sample" not in cmd
        reads_env = mentions_env and re.search(r"\b(cat|type|more|less|head|tail|get-content|gc)\b", cmd)
        commits_env = mentions_env and re.search(r"\bgit\s+add\b", cmd)
        leaks_key = "anthropic_api_key" in cmd and re.search(r"\b(echo|print|printenv|env|cat|get-content|gc|set)\b", cmd)
        if reads_env or commits_env or leaks_key:
            deny(
                "Blocked by secret-guard hook: this command would expose or commit the "
                "ANTHROPIC_API_KEY. Keep it only in the local .env (gitignored) and in "
                "Render's environment variables."
            )

    sys.exit(0)


if __name__ == "__main__":
    main()
