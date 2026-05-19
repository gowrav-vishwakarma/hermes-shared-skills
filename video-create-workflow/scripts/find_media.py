#!/usr/bin/env python3
"""find_media.py -- locate media files under a root.

Wraps the `find -name '*.<ext>'` shell idiom because the built-in
``search_files`` tool unreliably matches binary extensions like ``mp4``.

Usage::

    python3 find_media.py --ext mp4
    python3 find_media.py --ext jpg --root $POSTS_DIR
    python3 find_media.py --ext mp4 --name '*anchor*'
    python3 find_media.py --ext mp4 --limit 20

Stdlib only.
"""

from __future__ import annotations

import argparse
import fnmatch
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
try:
    from _env import required, resolve_path  # type: ignore
finally:
    try:
        sys.path.remove(str(SCRIPT_DIR))
    except ValueError:
        pass

DEFAULT_ROOT = required("PROFILE_HOME")
COMMON_EXTS = ["mp4", "mov", "mkv", "webm", "jpg", "jpeg", "png", "webp", "wav", "mp3"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ext", action="append", default=None,
                    help="Extension(s) without dot (e.g. mp4). May be repeated. "
                         f"Default: {COMMON_EXTS}")
    ap.add_argument("--root", default=None, help="Search root (default: $PROFILE_HOME).")
    ap.add_argument("--name", default=None,
                    help="Glob to match against the basename (e.g. '*anchor*').")
    ap.add_argument("--limit", type=int, default=0, help="Stop after N matches (0=all).")
    ap.add_argument("--newest-first", action="store_true",
                    help="Sort by mtime descending instead of path.")
    args = ap.parse_args()

    root = resolve_path(args.root) if args.root else DEFAULT_ROOT.resolve()
    if not root.is_dir():
        sys.exit(f"[find_media] not a directory: {root}")

    exts = [e.lstrip(".").lower() for e in (args.ext or COMMON_EXTS)]
    matches: list[Path] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lstrip(".").lower() not in exts:
            continue
        if args.name and not fnmatch.fnmatch(p.name, args.name):
            continue
        matches.append(p)

    if args.newest_first:
        matches.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    else:
        matches.sort()

    if args.limit > 0:
        matches = matches[: args.limit]

    for p in matches:
        print(str(p))
    print(f"  {len(matches)} match(es) under {root}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
