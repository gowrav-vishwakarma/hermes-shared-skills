# generate_image_config.py Comma-Separation Bug

## The Bug

When passing multiple image references to `generate_image_config.py` via comma-separated `--image-refs`, the script merges them into a **single JSON array item** instead of separate items:

```
--image-refs /path1.jpg,/path2.jpg  →  "image_refs": ["/path1.jpg,/path2.jpg"]
```

This causes generation to fail with `"File not found" / "You must provide at least one Reference Image"` because Qwen IEP sees one invalid path string.

## Symptoms

- Config file has `"image_refs": ["/path1,/path2"]` (single string with comma)
- Error: `Loaded image` shows only first ref or shows combined path
- Error: `File not found for 'image_refs': /path1,/path2`
- `[ERROR] You must provide at least one Reference Image`

## Workaround

After `generate_image_config.py` writes the JSON config, manually edit the `image_refs` array to split comma-separated paths into separate JSON array items:

```json
// BROKEN (single item):
"image_refs": [
    "/path1.jpg,/path2.jpg"
]

// FIXED (two items):
"image_refs": [
    "/path1.jpg",
    "/path2.jpg"
]
```

Use `skill_manage(action='patch')` or `execute_code` to fix the JSON. Then re-run `wgp.py --process` directly (not via `generate_image_config.py --run`).

## Root Cause

The script's argument parser treats the comma-separated string as a single value. It does not split on commas. This is a known limitation of `generate_image_config.py`.

## Prevention

When generating multi-ref images, prefer writing the config manually or using the python workaround above to ensure proper JSON array structure.
