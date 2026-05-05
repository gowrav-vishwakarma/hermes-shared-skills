# Asset Rename Workaround

## Problem

`asset_manifest.py` has NO `rename` function — only `add`, `remove`, `get`, `list_assets`.

## Solution

```bash
# 1. Remove old slug but KEEP files on disk
python3 <profile-skills>/wan2gp-image-generation/scripts/remove_asset.py \
    <old_slug> --keep-files

# 2. Add new slug with updated description/tags, same file path
python3 <profile-skills>/wan2gp-image-generation/scripts/asset_manifest.py add \
    --name <new_slug> \
    --path <same_file_path> \
    --kind <kind> \
    --description "<improved description>" \
    --aspect "<aspect>" \
    --tags tag1 tag2 \
    --parent_refs ref1 \
    --source-post <post_slug> \
    --manifest-path <manifest.json>
```

Or use the Python API directly:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(SCRIPT_DIR))
import asset_manifest

# Remove keeping files
result = asset_manifest.remove(old_slug, delete_files=False, manifest_path=MANIFEST_PATH)

# Add with new slug, same file
asset_manifest.add(
    name=new_slug,
    path=result["path"],  # same file
    kind="character",
    description="updated description with shot type info",
    aspect="9:16",
    tags=["tag1", "tag2"],
    parent_refs=["character_base"],
    source_post="2026-05-02_2",
    manifest_path=MANIFEST_PATH,
)
```

## Naming conventions

- **Slug format:** `snake_case`, kind-prefixed: `character_*`, `location_*`, `vehicle_*`, `creature_*`, `prop_*`
- **Shot-type in slug:** append shot type when relevant: `_23rd` (2/3rd), `_full` (full body), `_closeup`
- **Shot-type in description:** include framing details: "2/3rd shot (mid-thigh up)", "full body visible", "tight close-up"
- **Tags:** add shot-type tag for filtering: `23rd`, `mid-thigh`, `full`, `closeup`

## Files affected

- `assets.json` — manifest entry renamed (via remove+add)
- Image files (.jpg/.png) — remain at same path
- Co-located config .json — remains at same path
- Historical post files — keep old slug reference (historical record)
- Session transcripts — keep old slug reference (historical record)
- Future posts — will use new slug automatically via manifest lookup

## Warning

Do NOT delete the image file when renaming — always use `--keep-files` on remove, then add with same path. Deleting files will break asset references until regenerated.