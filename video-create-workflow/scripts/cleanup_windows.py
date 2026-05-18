#!/usr/bin/env python3
"""cleanup_windows.py -- prune sliding-window partial mp4 files.

When ``video_length > sliding_window_size`` WanGP writes one mp4 per
window: ``<name>.mp4`` (first/partial), ``<name>(2).mp4``, ``<name>(3).mp4``,
... The **last** file (highest index) is the complete stitched video. The
earlier files are partials and should be deleted.

This script scans a folder (or a single basename) and removes partial files
while keeping the final ``(N).mp4`` (or the only file if no numbered
variants exist).

Usage::

    python3 cleanup_windows.py path/to/post/
    python3 cleanup_windows.py path/to/post/ --basename my_reel
    python3 cleanup_windows.py path/to/post/ --dry-run

Stdlib only.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

_PAREN_RE = re.compile(r"^(?P<base>.+?)\((?P<idx>\d+)\)\.mp4$")


def _group_by_basename(folder: Path, basename: str | None) -> dict[str, list[tuple[int, Path]]]:
    groups: dict[str, list[tuple[int, Path]]] = defaultdict(list)
    for f in folder.glob("*.mp4"):
        m = _PAREN_RE.match(f.name)
        if m:
            base = m.group("base")
            idx = int(m.group("idx"))
        else:
            base = f.stem
            idx = 1
        if basename and base != basename:
            continue
        groups[base].append((idx, f))
    return groups


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("folder", help="Folder containing the sliding-window mp4 outputs.")
    ap.add_argument("--basename", default=None,
                    help="Restrict to a specific output basename (no extension).")
    ap.add_argument("--dry-run", action="store_true",
                    help="Show what would be deleted, change nothing.")
    args = ap.parse_args()

    folder = Path(args.folder).expanduser().resolve()
    if not folder.is_dir():
        sys.exit(f"[cleanup_windows] not a directory: {folder}")

    groups = _group_by_basename(folder, args.basename)
    if not groups:
        print(f"[cleanup_windows] no mp4 files in {folder}", file=sys.stderr)
        return 0

    removed = 0
    for base, items in groups.items():
        items.sort(key=lambda t: t[0])
        if len(items) < 2:
            continue
        keep_idx, keep_path = items[-1]
        for idx, path in items[:-1]:
            print(f"  prune  {path.name} (window {idx})")
            if not args.dry_run:
                path.unlink()
            removed += 1
        print(f"  keep   {keep_path.name} (final window {keep_idx})")
    print(f"[cleanup_windows] removed={removed} dry_run={args.dry_run}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
