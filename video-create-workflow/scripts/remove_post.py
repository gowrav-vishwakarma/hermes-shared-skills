#!/usr/bin/env python3
"""remove_post.py -- delete a post folder under $POSTS_DIR.

Refuses to act on a path that is not a child of $POSTS_DIR. Use
--dry-run to preview the deletion. Multiple slugs may be passed.

Usage::

    python3 remove_post.py 2026-05-18_3
    python3 remove_post.py 2026-05-18_3 2026-05-18_4 --dry-run

Stdlib only.
"""

from __future__ import annotations

import argparse
import shutil
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

POSTS_DIR = required("POSTS_DIR").resolve()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("slugs", nargs="+", help="Post folder slug(s), e.g. 2026-05-18_3.")
    ap.add_argument("--dry-run", action="store_true", help="Show what would be deleted.")
    args = ap.parse_args()

    rc = 0
    for slug in args.slugs:
        target = (POSTS_DIR / slug).resolve()
        try:
            target.relative_to(POSTS_DIR)
        except ValueError:
            print(f"[remove_post] refusing {target}: not inside {POSTS_DIR}", file=sys.stderr)
            rc = 1
            continue
        if not target.is_dir():
            print(f"[remove_post] not a directory: {target}", file=sys.stderr)
            rc = 1
            continue
        if args.dry_run:
            size = sum(p.stat().st_size for p in target.rglob("*") if p.is_file())
            n = sum(1 for _ in target.rglob("*"))
            print(f"[remove_post] DRY: would remove {target} ({n} entries, {size} bytes)")
            continue
        shutil.rmtree(target)
        print(f"[remove_post] removed {target}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
