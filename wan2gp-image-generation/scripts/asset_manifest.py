"""asset_manifest.py -- profile reusable image-asset library.

Stdlib-only (json, os, pathlib, datetime, tempfile). Safe to import from any
helper script -- no torch / diffusers.

The character-video workflow keeps a growing library of reusable reference images
(character in different outfits, spaceships, creatures, locations, props) so
that future Qwen Image Edit Plus anchors can pull 0-3 named refs by slug
instead of regenerating identity / style every time.

Layout (canonical, all paths come from $PROFILE_ROOT/.env):
    $CHARACTER_BASE                                  # base identity (square)
    $CHARACTER_ASSETS_DIR/                           # all bootstrapped refs
        $CHARACTER_ASSETS_MANIFEST                    # source-of-truth manifest
        character_spacesuit_helmet.png
        spaceship_exterior.png
        ...

`CHARACTER_ASSETS_MANIFEST` and `CHARACTER_BASE` are REQUIRED env vars; this
module exits with a clear message if either is missing.

Manifest schema (version 1):
    {
        "version": 1,
        "assets": {
            "<slug>": {
                "path": "<absolute path to the image>",
                "kind": "<character|vehicle|creature|location|prop|other>",
                "aspect": "<1:1|9:16|16:9|free>",
                "description": "<one-sentence visual description>",
                "tags": ["...", "..."],
                "parent_refs": ["<slug>", ...],   # which library refs fed this
                "source_post": "<post folder slug or 'seed'>",
                "created": "YYYY-MM-DD"
            },
            ...
        }
    }

Names are snake_case; kind-prefixed slugs are recommended (character_*,
spaceship_*, vehicle_*, creature_*, location_*, prop_*).
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import date
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from _env import required  # type: ignore
finally:
    try:
        sys.path.remove(str(Path(__file__).resolve().parent))
    except ValueError:
        pass

DEFAULT_MANIFEST_PATH = required("CHARACTER_ASSETS_MANIFEST")
DEFAULT_CHARACTER_BASE = required("CHARACTER_BASE")
SCHEMA_VERSION = 1
VALID_KINDS = {"character", "vehicle", "creature", "location", "prop", "other"}


def _empty_manifest() -> dict:
    return {"version": SCHEMA_VERSION, "assets": {}}


def _seed_character_base(manifest: dict) -> bool:
    """Add `character_base` if the canonical character.png exists and is missing.

    Returns True if the manifest was mutated.
    """
    if "character_base" in manifest.get("assets", {}):
        return False
    if not DEFAULT_CHARACTER_BASE.is_file():
        return False
    manifest.setdefault("assets", {})["character_base"] = {
        "path": str(DEFAULT_CHARACTER_BASE),
        "kind": "character",
        "aspect": "1:1",
        "description": "Base character identity reference (neutral background, square).",
        "tags": ["character", "identity", "base"],
        "parent_refs": [],
        "source_post": "seed",
        "created": date.today().isoformat(),
    }
    return True


def load_manifest(manifest_path: Path | None = None,
                  *, auto_seed: bool = True) -> dict:
    """Load the manifest from disk; create a fresh one if missing.

    When `auto_seed` is True (default), ensure `character_base` is present
    if `character.png` exists. The manifest is written back to disk if any
    auto-seeding happened, so the on-disk file always matches what callers
    see.
    """
    path = manifest_path or DEFAULT_MANIFEST_PATH
    if path.is_file():
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            raise SystemExit(
                f"[asset_manifest] manifest at {path} is not valid JSON: {exc}"
            )
        if not isinstance(data, dict):
            raise SystemExit(
                f"[asset_manifest] manifest at {path} is not a JSON object"
            )
        data.setdefault("version", SCHEMA_VERSION)
        data.setdefault("assets", {})
    else:
        data = _empty_manifest()

    mutated = False
    if auto_seed:
        mutated = _seed_character_base(data)

    if mutated or not path.is_file():
        save_manifest(data, path)
    return data


def save_manifest(manifest: dict, manifest_path: Path | None = None) -> Path:
    """Atomically write the manifest (tmp + rename in the same dir)."""
    path = manifest_path or DEFAULT_MANIFEST_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".assets_", suffix=".json.tmp",
                                    dir=str(path.parent))
    try:
        with os.fdopen(fd, "w") as fh:
            json.dump(manifest, fh, indent=4, sort_keys=False)
            fh.write("\n")
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    return path


def get(name: str, manifest_path: Path | None = None) -> dict | None:
    """Return the asset entry for `name`, or None if missing."""
    manifest = load_manifest(manifest_path)
    entry = manifest.get("assets", {}).get(name)
    return dict(entry) if entry else None


def list_assets(kind: str | None = None, tag: str | None = None,
                manifest_path: Path | None = None) -> list[dict]:
    """Return all assets, optionally filtered by `kind` and/or `tag`.

    Each returned dict includes the slug under the `name` key for convenience.
    """
    manifest = load_manifest(manifest_path)
    out: list[dict] = []
    for slug, entry in manifest.get("assets", {}).items():
        if kind and entry.get("kind") != kind:
            continue
        if tag and tag not in (entry.get("tags") or []):
            continue
        item = dict(entry)
        item["name"] = slug
        out.append(item)
    return out


def add(name: str, path: str | os.PathLike, *, kind: str, description: str,
        aspect: str = "9:16", tags: Iterable[str] | None = None,
        parent_refs: Iterable[str] | None = None,
        source_post: str | None = None, force: bool = False,
        manifest_path: Path | None = None) -> dict:
    """Register (or overwrite with `force=True`) an asset in the manifest.

    Validates `kind` against `VALID_KINDS`. Does not require the file to
    exist (callers may register an asset whose render is still in flight),
    but absolute paths are recommended.

    Returns the freshly written entry.
    """
    if not name or not name.replace("_", "").isalnum():
        raise SystemExit(
            f"[asset_manifest] invalid slug {name!r}; use snake_case "
            "alphanumerics (e.g. character_spacesuit_helmet)"
        )
    if kind not in VALID_KINDS:
        raise SystemExit(
            f"[asset_manifest] invalid kind {kind!r}; choose from {sorted(VALID_KINDS)}"
        )

    manifest = load_manifest(manifest_path)
    if name in manifest.get("assets", {}) and not force:
        raise SystemExit(
            f"[asset_manifest] asset {name!r} already exists; pass force=True "
            "(or --force) to overwrite"
        )

    entry = {
        "path": str(Path(path)),
        "kind": kind,
        "aspect": aspect,
        "description": description,
        "tags": sorted(set(tags or [])),
        "parent_refs": list(parent_refs or []),
        "source_post": source_post or "",
        "created": date.today().isoformat(),
    }
    manifest.setdefault("assets", {})[name] = entry
    save_manifest(manifest, manifest_path)
    return entry


def remove(name: str, *, delete_files: bool = True,
           manifest_path: Path | None = None) -> dict | None:
    """Remove an asset from the manifest and optionally delete its files.

    Returns the removed entry, or None if the slug was not found.
    When `delete_files` is True, removes the registered image/png/jpg and
    any co-located .json config with the same stem.
    """
    manifest = load_manifest(manifest_path)
    assets = manifest.get("assets", {})
    entry = assets.pop(name, None)
    if entry is None:
        return None

    save_manifest(manifest, manifest_path)

    if delete_files:
        raster = Path(entry["path"])
        for f in (raster, raster.with_suffix(".json")):
            if f.is_file():
                f.unlink()

    return entry


def resolve_refs(names: Iterable[str],
                 manifest_path: Path | None = None) -> list[str]:
    """Resolve a list of asset slugs to absolute image paths.

    Raises SystemExit with a clear message on the first missing slug or on
    any slug whose registered path does not exist on disk.
    """
    manifest = load_manifest(manifest_path)
    assets = manifest.get("assets", {})
    out: list[str] = []
    for slug in names:
        entry = assets.get(slug)
        if not entry:
            available = sorted(assets.keys())
            raise SystemExit(
                f"[asset_manifest] unknown asset {slug!r}. "
                f"Available: {available}"
            )
        path = Path(entry["path"])
        if not path.is_file():
            raise SystemExit(
                f"[asset_manifest] asset {slug!r} registered at {path} "
                "but the file is missing on disk"
            )
        out.append(str(path))
    return out


__all__ = [
    "DEFAULT_MANIFEST_PATH",
    "DEFAULT_CHARACTER_BASE",
    "SCHEMA_VERSION",
    "VALID_KINDS",
    "load_manifest",
    "save_manifest",
    "get",
    "list_assets",
    "add",
    "remove",
    "resolve_refs",
]
