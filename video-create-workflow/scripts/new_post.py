#!/usr/bin/env python3
"""new_post.py -- create a new per-post (or movie) folder under $POSTS_DIR.

Picks the next available index for today (or --date), creating
``$POSTS_DIR/<YYYY-MM-DD_#>/`` (or ``<YYYY-MM-DD_movie_<tag>>/`` when
--movie is set) and prints the absolute path.

Usage::

    python3 new_post.py
    python3 new_post.py --date 2026-05-18
    python3 new_post.py --movie --tag fantasy
    python3 new_post.py --tag dance_reel

Stdlib only.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
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


POSTS_DIR = required("POSTS_DIR")
_INDEX_RE = re.compile(r"^(?P<date>\d{4}-\d{2}-\d{2})_(?P<idx>\d+)(?:_.*)?$")


def _next_index(day: str) -> int:
    if not POSTS_DIR.is_dir():
        return 1
    used: list[int] = []
    for child in POSTS_DIR.iterdir():
        if not child.is_dir():
            continue
        m = _INDEX_RE.match(child.name)
        if m and m.group("date") == day:
            used.append(int(m.group("idx")))
    return (max(used) + 1) if used else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", default=None, help="YYYY-MM-DD (default: today).")
    ap.add_argument("--tag", default=None,
                    help="Optional snake_case tag appended after the index "
                         "(or used as movie slug with --movie).")
    ap.add_argument("--movie", action="store_true",
                    help="Create a movie folder: <YYYY-MM-DD_movie_<tag>/>. "
                         "Requires --tag.")
    args = ap.parse_args()

    day = args.date or date.today().isoformat()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", day):
        sys.exit(f"[new_post] --date must be YYYY-MM-DD, got {day!r}")

    POSTS_DIR.mkdir(parents=True, exist_ok=True)

    if args.movie:
        if not args.tag:
            sys.exit("[new_post] --movie requires --tag (e.g. --tag fantasy).")
        slug = f"{day}_movie_{args.tag}"
    else:
        idx = _next_index(day)
        slug = f"{day}_{idx}"
        if args.tag:
            slug = f"{slug}_{args.tag}"

    target = POSTS_DIR / slug
    if target.exists():
        sys.exit(f"[new_post] target already exists: {target}")
    target.mkdir(parents=True)
    print(str(target))
    print(f"[new_post] created {slug}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
