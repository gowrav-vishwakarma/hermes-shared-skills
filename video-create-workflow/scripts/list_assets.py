#!/usr/bin/env python3
"""list_assets.py -- thin wrapper around the asset manifest.

Reads ``$CHARACTER_ASSETS_MANIFEST`` (assets.json) directly and prints the
registered slugs. Optional filters: --kind, --tag. Optional output mode:
--json (full entries) or default (slug-only one-per-line).

Usage::

    python3 list_assets.py
    python3 list_assets.py --kind character
    python3 list_assets.py --tag identity --json
    python3 list_assets.py --check     # also flag missing-on-disk entries

Stdlib only. Does not call into the image-generation skill.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
try:
    from _env import required  # type: ignore
finally:
    try:
        sys.path.remove(str(SCRIPT_DIR))
    except ValueError:
        pass

MANIFEST = required("CHARACTER_ASSETS_MANIFEST")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kind", default=None,
                    help="Filter by kind (character, vehicle, creature, location, prop, other).")
    ap.add_argument("--tag", default=None, help="Filter by tag.")
    ap.add_argument("--json", action="store_true", help="Emit full JSON entries.")
    ap.add_argument("--check", action="store_true",
                    help="Verify each registered path exists on disk; flag missing.")
    args = ap.parse_args()

    if not MANIFEST.is_file():
        print(f"[list_assets] manifest missing: {MANIFEST}", file=sys.stderr)
        if args.json:
            print("[]")
        return 0

    data = json.loads(MANIFEST.read_text())
    assets = data.get("assets", {})

    filtered: list[tuple[str, dict]] = []
    for slug, entry in assets.items():
        if args.kind and entry.get("kind") != args.kind:
            continue
        if args.tag and args.tag not in (entry.get("tags") or []):
            continue
        filtered.append((slug, entry))

    if args.json:
        out = []
        for slug, entry in filtered:
            row = dict(entry)
            row["slug"] = slug
            if args.check:
                row["on_disk"] = Path(entry.get("path", "")).is_file()
            out.append(row)
        print(json.dumps(out, indent=2))
    else:
        for slug, entry in filtered:
            line = f"  {slug:40s} {entry.get('kind', '?'):10s} {entry.get('aspect', '?'):5s}"
            if args.check:
                tag = "ok" if Path(entry.get("path", "")).is_file() else "MISSING"
                line += f" [{tag}]"
            line += f"  {entry.get('path', '')}"
            print(line)
    print(f"  {len(filtered)} / {len(assets)} asset(s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
