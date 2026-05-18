#!/usr/bin/env python3
"""journey_append.py -- atomic append of one entry to $JOURNEY_FILE.

Owns the schema so the agent never hand-writes JSON. Each entry is written
on its own line (JSONL) via an exclusive ``open(..., 'a')`` call.

Required fields:
  --n N                 sequence number
  --date YYYY-MM-DD
  --slug                post folder slug
  --aspect 9:16|16:9
  --location            short noun phrase
  --beat                one-line summary
  --anchor-file         basename
  --reel-file           basename

Optional:
  --assets-used a b c   list of asset slugs

Usage::

    python3 journey_append.py --n 11 --date 2026-05-18 --slug 2026-05-18_1 \\
        --aspect 9:16 --location "kitchen" --beat "Meena makes chai" \\
        --anchor-file anchor.jpg --reel-file reel.mp4 \\
        --assets-used character_base prop_kettle

Stdlib only.
"""

from __future__ import annotations

import argparse
import json
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

JOURNEY_FILE = required("JOURNEY_FILE")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--date", required=True)
    ap.add_argument("--slug", required=True)
    ap.add_argument("--aspect", required=True, choices=["9:16", "16:9"])
    ap.add_argument("--location", required=True)
    ap.add_argument("--beat", required=True)
    ap.add_argument("--anchor-file", required=True)
    ap.add_argument("--reel-file", required=True)
    ap.add_argument("--assets-used", nargs="*", default=[])
    args = ap.parse_args()

    if not re.match(r"^\d{4}-\d{2}-\d{2}$", args.date):
        sys.exit(f"[journey_append] --date must be YYYY-MM-DD, got {args.date!r}")

    entry = {
        "n": args.n,
        "date": args.date,
        "slug": args.slug,
        "aspect": args.aspect,
        "location": args.location,
        "beat": args.beat,
        "anchor_file": args.anchor_file,
        "reel_file": args.reel_file,
        "assets_used": list(args.assets_used),
    }

    JOURNEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with JOURNEY_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(json.dumps(entry, ensure_ascii=False))
    print(f"[journey_append] appended #{args.n} to {JOURNEY_FILE}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
