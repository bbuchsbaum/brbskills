#!/usr/bin/env python3
"""Claude file-tool guard. Bash is not a security boundary.

Pin with DASHBOARD_DIR in the Claude session environment for an external dashboard.
Otherwise use the nearest initialized .dashboard under cwd or its ancestors.
Only the page can be edited; state, style, lessons and other sessions are excluded.
"""
import json
import os
import sys
from pathlib import Path


def deny(message):
    print(f"dashboard-builder: {message}", file=sys.stderr)
    raise SystemExit(2)


def main():
    try:
        call = json.load(sys.stdin)
        inp = call.get("tool_input")
        if not isinstance(inp, dict):
            deny("missing tool_input")
        target = inp.get("file_path") or inp.get("notebook_path")
        if not isinstance(target, str) or not target:
            deny("missing write target")
        cwd = Path(call.get("cwd") or os.getcwd()).expanduser().resolve()
        explicit = os.environ.get("DASHBOARD_DIR")
        if explicit:
            root = Path(explicit).expanduser().resolve()
            if root.name != ".dashboard":
                deny("DASHBOARD_DIR must name a .dashboard directory")
        else:
            root = next((p / ".dashboard" for p in (cwd, *cwd.parents)
                         if (p / ".dashboard" / "state.json").is_file()), cwd / ".dashboard").resolve()
            if cwd.name == ".dashboard" and (cwd / "state.json").is_file():
                root = cwd
        path = Path(target).expanduser()
        if not path.is_absolute():
            path = cwd / path
        # Do not resolve the allowed filename: index.html itself could be an escape symlink.
        if path.resolve() != root / "index.html":
            deny(f"only {root / 'index.html'} may be edited; refused {path}")
        if not (root / "state.json").is_file():
            deny("parent must initialize this dashboard first")
    except (ValueError, TypeError, AttributeError, OSError) as error:
        deny(f"invalid hook input or path: {error}")


if __name__ == "__main__":
    main()
