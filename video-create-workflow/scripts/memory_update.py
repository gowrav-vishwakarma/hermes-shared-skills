#!/usr/bin/env python3
"""memory_update.py -- rewrite the single ``<Character> State:`` line in $MEMORY_FILE.

The memory file is a plain-text MEMORY.md. This script searches for a line
matching ``<Character> State:`` (case-insensitive on the prefix) and replaces
it with a freshly-formatted single-line entry. If no such line exists, it is
appended at the end of the file (one blank line of separation).

Required:
  --character NAME       Character name (e.g. Meena)
  --prev "#10 tag"       Previous post tag
  --current "#11 tag"    Current post tag
  --last-beat "..."      One-line summary of the latest beat
  --next-hint "..."      One-line hint for the next post
  --active-assets a,b,c  Comma-separated slugs

Usage::

    python3 memory_update.py --character Meena \\
        --prev "#10 kitchen" --current "#11 garden" \\
        --last-beat "Meena waters tulsi at dawn" \\
        --next-hint "Morning prayer scene" \\
        --active-assets character_base,location_garden

Stdlib only.
"""

from __future__ import annotations

import argparse
import re
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

MEMORY_FILE = required("MEMORY_FILE")
JOURNEY_FILE = required("JOURNEY_FILE")


def _format_line(args: argparse.Namespace) -> str:
    return (
        f"{args.character} State: prev={args.prev} | current={args.current} | "
        f"last_beat={args.last_beat} | next_hint={args.next_hint} | "
        f"active_assets={args.active_assets}. Full history at `{JOURNEY_FILE}`."
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--character", required=True)
    ap.add_argument("--prev", required=True)
    ap.add_argument("--current", required=True)
    ap.add_argument("--last-beat", required=True)
    ap.add_argument("--next-hint", required=True)
    ap.add_argument("--active-assets", required=True,
                    help="Comma-separated asset slugs.")
    args = ap.parse_args()

    new_line = _format_line(args)
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    text = MEMORY_FILE.read_text() if MEMORY_FILE.is_file() else ""

    pattern = re.compile(
        rf"^{re.escape(args.character)}\s+State:.*$", re.MULTILINE | re.IGNORECASE
    )
    if pattern.search(text):
        text = pattern.sub(new_line, text)
    else:
        if text and not text.endswith("\n"):
            text += "\n"
        if text and not text.endswith("\n\n"):
            text += "\n"
        text += new_line + "\n"

    MEMORY_FILE.write_text(text)
    print(new_line)
    print(f"[memory_update] wrote {MEMORY_FILE}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
