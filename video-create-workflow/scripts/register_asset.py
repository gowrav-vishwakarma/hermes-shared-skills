#!/usr/bin/env python3
"""register_asset.py -- add an already-on-disk image to assets.json.

For files generated outside the normal ``generate_asset.py`` flow (e.g.
copied from the user, exported by another tool) this script registers the
slug in ``$CHARACTER_ASSETS_MANIFEST`` without re-rendering.

Required:
  --name SLUG
  --kind {character,vehicle,creature,location,prop,other}
  --aspect {9:16,16:9,1:1,free}
  --path PATH       absolute path to the image file (must exist)
  --description "..."

Optional:
  --tags a b c
  --parent-refs slug1 slug2
  --source-post slug
  --force           overwrite existing slug

Usage::

    python3 register_asset.py --name character_kurti_palazzo --kind character \\
        --aspect 9:16 --path /abs/path/character_kurti_palazzo.jpg \\
        --description "Meena in kurti+palazzo, plain-wall midshot."

Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
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

MANIFEST = required("CHARACTER_ASSETS_MANIFEST")
VALID_KINDS = {"character", "vehicle", "creature", "location", "prop", "other"}
VALID_ASPECTS = {"9:16", "16:9", "1:1", "free"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--name", required=True, help="snake_case slug.")
    ap.add_argument("--kind", required=True, choices=sorted(VALID_KINDS))
    ap.add_argument("--aspect", required=True, choices=sorted(VALID_ASPECTS))
    ap.add_argument("--path", required=True, help="Absolute path to the image on disk.")
    ap.add_argument("--description", required=True, help="One-sentence visual description.")
    ap.add_argument("--tags", nargs="*", default=[])
    ap.add_argument("--parent-refs", nargs="*", default=[])
    ap.add_argument("--source-post", default="")
    ap.add_argument("--force", action="store_true", help="Overwrite an existing slug.")
    args = ap.parse_args()

    if not args.name.replace("_", "").isalnum():
        sys.exit(f"[register_asset] invalid slug {args.name!r}; use snake_case alphanumerics.")

    img = resolve_path(args.path)
    if not img.is_file():
        sys.exit(f"[register_asset] path does not exist: {img}")

    if MANIFEST.is_file():
        manifest = json.loads(MANIFEST.read_text())
    else:
        manifest = {"version": 1, "assets": {}}
    manifest.setdefault("version", 1)
    manifest.setdefault("assets", {})

    if args.name in manifest["assets"] and not args.force:
        sys.exit(f"[register_asset] slug {args.name!r} already exists. Use --force to overwrite.")

    entry = {
        "path": str(img),
        "kind": args.kind,
        "aspect": args.aspect,
        "description": args.description,
        "tags": sorted(set(args.tags)),
        "parent_refs": list(args.parent_refs),
        "source_post": args.source_post,
        "created": date.today().isoformat(),
    }
    manifest["assets"][args.name] = entry

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=4) + "\n")

    print(json.dumps({args.name: entry}, indent=2))
    print(f"[register_asset] registered {args.name!r} -> {img}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
