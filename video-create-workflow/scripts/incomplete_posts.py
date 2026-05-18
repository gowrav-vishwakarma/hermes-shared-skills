#!/usr/bin/env python3
"""incomplete_posts.py -- find post folders that are partially rendered.

A post is "incomplete" when:
  * it has an anchor image but no final video, OR
  * it has a video_generation.json but no matching mp4

Movies are skipped by default (use --include-movies to include them).

Usage::

    python3 incomplete_posts.py
    python3 incomplete_posts.py --json
    python3 incomplete_posts.py --include-movies

Exit code 0 always (printing is the result). Stdlib only.
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

POSTS_DIR = required("POSTS_DIR")


def _is_incomplete(folder: Path) -> tuple[bool, str]:
    mp4s = list(folder.glob("*.mp4"))
    anchors = [p for p in folder.glob("*anchor*")
               if p.suffix.lower() in {".jpg", ".jpeg", ".png"}]
    has_video_cfg = (folder / "video_generation.json").is_file()
    if mp4s:
        return False, "ok"
    if anchors and not mp4s:
        return True, "anchor without video"
    if has_video_cfg and not mp4s:
        return True, "video_generation.json without mp4"
    return False, "no anchor, no config"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="Machine-readable output.")
    ap.add_argument("--include-movies", action="store_true",
                    help="Also flag incomplete movie folders.")
    args = ap.parse_args()

    if not POSTS_DIR.is_dir():
        if args.json:
            print("[]")
        return 0

    out = []
    for folder in sorted(POSTS_DIR.iterdir()):
        if not folder.is_dir():
            continue
        if "_movie_" in folder.name and not args.include_movies:
            continue
        bad, reason = _is_incomplete(folder)
        if bad:
            out.append({"slug": folder.name, "path": str(folder), "reason": reason})

    if args.json:
        print(json.dumps(out, indent=2))
    else:
        if not out:
            print("[incomplete_posts] none.", file=sys.stderr)
        for entry in out:
            print(f"  INCOMPLETE: {entry['slug']:50s} -- {entry['reason']}")
    print(f"  {len(out)} incomplete", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
