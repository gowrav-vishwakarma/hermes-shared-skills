#!/usr/bin/env python3
"""list_posts.py -- list post folders under $POSTS_DIR with optional status.

Usage::

    python3 list_posts.py
    python3 list_posts.py --with-status
    python3 list_posts.py --json
    python3 list_posts.py --movie-only

For each folder reports presence of: anchor image, video config, final mp4.
Stdlib only.
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


def _status(folder: Path) -> dict:
    anchors = [p.name for p in folder.glob("*anchor*") if p.suffix.lower() in {".jpg", ".jpeg", ".png"}]
    mp4s = sorted(p.name for p in folder.glob("*.mp4"))
    compressed = [n for n in mp4s if "compressed" in n.lower()]
    raw = [n for n in mp4s if n not in compressed]
    return {
        "slug": folder.name,
        "is_movie": "_movie_" in folder.name,
        "has_image_config": (folder / "image_generation.json").is_file(),
        "has_video_config": (folder / "video_generation.json").is_file(),
        "anchors": anchors,
        "videos_raw": raw,
        "videos_compressed": compressed,
        "complete": bool(mp4s),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--with-status", action="store_true",
                    help="Show anchor/config/video presence per folder.")
    ap.add_argument("--json", action="store_true",
                    help="Emit machine-readable JSON.")
    ap.add_argument("--movie-only", action="store_true",
                    help="List only movie folders (slug contains _movie_).")
    ap.add_argument("--no-movies", action="store_true",
                    help="Exclude movie folders.")
    args = ap.parse_args()

    if not POSTS_DIR.is_dir():
        if args.json:
            print("[]")
        else:
            print(f"[list_posts] no posts dir at {POSTS_DIR}", file=sys.stderr)
        return 0

    folders = sorted(p for p in POSTS_DIR.iterdir() if p.is_dir())
    if args.movie_only:
        folders = [p for p in folders if "_movie_" in p.name]
    if args.no_movies:
        folders = [p for p in folders if "_movie_" not in p.name]

    if args.json or args.with_status:
        data = [_status(p) for p in folders]
    else:
        data = None

    if args.json:
        print(json.dumps(data, indent=2))
        return 0

    if args.with_status and data is not None:
        for d in data:
            kind = "movie" if d["is_movie"] else "post"
            flag = "ok" if d["complete"] else "INCOMPLETE"
            print(f"  {d['slug']:50s} {kind:5s} [{flag}] "
                  f"anchors={len(d['anchors'])} "
                  f"videos_raw={len(d['videos_raw'])} "
                  f"compressed={len(d['videos_compressed'])} "
                  f"video_cfg={'y' if d['has_video_config'] else 'n'}")
    else:
        for p in folders:
            print(p.name)
    print(f"  {len(folders)} folder(s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
