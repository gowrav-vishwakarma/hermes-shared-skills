#!/usr/bin/env python3
"""bootstrap_profile.py -- create profile workspace dirs and seed assets.json.

Idempotent. Creates the directories agents expect to find on cold start and
writes a minimal ``assets.json`` containing the ``character_base`` entry if
``$CHARACTER_BASE`` already exists on disk.

Created (when missing):
  * ``$CHARACTER_ASSETS_DIR``
  * ``$POSTS_DIR``
  * ``$(dirname $MEMORY_FILE)``
  * ``$(dirname $JOURNEY_FILE)`` and an empty journey file if not present
  * ``$CHARACTER_ASSETS_MANIFEST`` with the ``character_base`` seed

Usage::

    python3 bootstrap_profile.py
    python3 bootstrap_profile.py --json

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
    from _env import required, optional  # type: ignore
finally:
    try:
        sys.path.remove(str(SCRIPT_DIR))
    except ValueError:
        pass


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="JSON report instead of human text.")
    args = ap.parse_args()

    posts_dir = required("POSTS_DIR")
    assets_dir = required("CHARACTER_ASSETS_DIR")
    manifest_path = required("CHARACTER_ASSETS_MANIFEST")
    character_base = required("CHARACTER_BASE")
    memory_file = required("MEMORY_FILE")
    journey_file = required("JOURNEY_FILE")

    report = {"created": [], "existed": [], "manifest_seeded": False}

    for path in (posts_dir, assets_dir, memory_file.parent, journey_file.parent):
        if path.is_dir():
            report["existed"].append(str(path))
        else:
            path.mkdir(parents=True, exist_ok=True)
            report["created"].append(str(path))

    if not journey_file.is_file():
        journey_file.touch()
        report["created"].append(str(journey_file))
    else:
        report["existed"].append(str(journey_file))

    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text())
        except json.JSONDecodeError:
            sys.exit(f"[bootstrap_profile] manifest at {manifest_path} is not valid JSON")
        manifest.setdefault("version", 1)
        manifest.setdefault("assets", {})
    else:
        manifest = {"version": 1, "assets": {}}
        report["created"].append(str(manifest_path))

    if character_base.is_file() and "character_base" not in manifest["assets"]:
        manifest["assets"]["character_base"] = {
            "path": str(character_base),
            "kind": "character",
            "aspect": "1:1",
            "description": "Base character identity reference.",
            "tags": ["character", "identity", "base"],
            "parent_refs": [],
            "source_post": "seed",
            "created": date.today().isoformat(),
        }
        report["manifest_seeded"] = True

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=4) + "\n")

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for p in report["created"]:
            print(f"  created   {p}")
        for p in report["existed"]:
            print(f"  exists    {p}")
        print(f"  manifest  {manifest_path} (seeded={report['manifest_seeded']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
