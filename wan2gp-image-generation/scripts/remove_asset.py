#!/usr/bin/env python3
"""remove_asset.py -- remove one or more assets from the profile library.

Deletes the image file, its co-located .json config, and removes the entry
from assets.json.  Supports removing multiple slugs in one invocation.

Usage:
    python3 remove_asset.py location_courtyard_outdoor_v2
    python3 remove_asset.py location_courtyard_outdoor_v2 location_courtyard_outdoor_v3
    python3 remove_asset.py location_courtyard_outdoor_v2 --keep-files   # manifest only
    python3 remove_asset.py --list                                       # show all slugs
    python3 remove_asset.py --list --kind location                       # filter by kind

Stdlib-only.  Imports asset_manifest from the same folder.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def _import_manifest():
    sys.path.insert(0, str(SCRIPT_DIR))
    try:
        import asset_manifest  # type: ignore
    finally:
        try:
            sys.path.remove(str(SCRIPT_DIR))
        except ValueError:
            pass
    return asset_manifest


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Remove assets from the profile library (files + manifest).",
    )
    ap.add_argument("slugs", nargs="*",
                    help="Asset slug(s) to remove, e.g. location_courtyard_outdoor_v2.")
    ap.add_argument("--keep-files", action="store_true",
                    help="Only remove the manifest entry; leave image/json on disk.")
    ap.add_argument("--list", action="store_true", dest="list_assets",
                    help="List all registered assets and exit.")
    ap.add_argument("--kind", default=None,
                    help="When used with --list, filter by kind.")
    args = ap.parse_args()

    am = _import_manifest()

    if args.list_assets:
        assets = am.list_assets(kind=args.kind)
        if not assets:
            print("[remove_asset] no assets found.", file=sys.stderr)
            return 0
        for a in assets:
            exists = "ok" if Path(a["path"]).is_file() else "MISSING"
            print(f"  {a['name']:40s} {a['kind']:12s} [{exists}]  {a['path']}")
        print(f"\n  {len(assets)} asset(s) total.", file=sys.stderr)
        return 0

    if not args.slugs:
        ap.error("provide at least one slug to remove, or use --list.")

    errors = 0
    for slug in args.slugs:
        existing = am.get(slug)
        if existing is None:
            print(f"[remove_asset] slug {slug!r} not found in manifest.",
                  file=sys.stderr)
            errors += 1
            continue

        files_before: list[tuple[Path, bool]] = []
        if not args.keep_files:
            raster = Path(existing["path"])
            for f in (raster, raster.with_suffix(".json")):
                files_before.append((f, f.is_file()))

        am.remove(slug, delete_files=not args.keep_files)

        print(f"[remove_asset] removed {slug!r} from manifest.", file=sys.stderr)
        for f, existed in files_before:
            if existed:
                print(f"  deleted {f}", file=sys.stderr)
            else:
                print(f"  (not on disk) {f}", file=sys.stderr)

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
