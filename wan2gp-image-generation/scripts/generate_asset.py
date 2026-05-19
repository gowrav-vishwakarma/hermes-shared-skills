#!/usr/bin/env python3
"""generate_asset.py -- bootstrap a reusable image asset for the profile library.

Wraps generate_image_config.py for the specific case of "render once, reuse
forever." Writes the WanGP `--process` JSON into the assets folder, runs it
(if --run), promotes any `<name>.mp4` to `<name>.jpg`, and registers the
result in `assets.json` so future Qwen Image Edit Plus anchors can pull it
by slug via `--ref-assets`.

Why this exists:
    Per-post anchors (`generate_image_config.py`) drift visually because each
    invocation regenerates "the spaceship" or "a moon guardian" from the
    prompt alone. The asset library fixes that by rendering each recurring
    visual element once, then re-using its raster as a Qwen reference.

Usage:
    python3 generate_asset.py \\
        --name spaceship_exterior \\
        --kind vehicle \\
        --description "Gold-and-blue mandala hull, viewport, deep space" \\
        --prompt "Wide 9:16 establishing shot of the character's spaceship..." \\
        [--ref-assets character_base]   # 0-3 library refs, max 3 total
        [--image-refs /abs/extra_ref.png]
        [--tags spaceship exterior]
        [--source-post 2026-05-02_1]
        [--resolution 720x1280]
        [--seed 42]
        [--force]                         # overwrite an existing slug
        [--run]                           # also run wgp.py + register on success

Stdlib-only. Imports asset_manifest + generate_image_config from the same
folder; never touches torch / diffusers itself.
"""

from __future__ import annotations

import argparse
import os
import subprocess
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

ASSETS_DIR = required("CHARACTER_ASSETS_DIR")


def _import_local():
    sys.path.insert(0, str(SCRIPT_DIR))
    try:
        import asset_manifest  # type: ignore
        import generate_image_config as gic  # type: ignore
    finally:
        try:
            sys.path.remove(str(SCRIPT_DIR))
        except ValueError:
            pass
    return asset_manifest, gic


def extract_first_frame(mp4_path: Path, jpg_path: Path) -> bool:
    """Run `ffmpeg` to extract frame 0 of `mp4_path` into `jpg_path`.

    Returns True on success. WanGP's Qwen Image Edit Plus stack often saves
    a single-frame MP4 instead of a JPEG; we promote it so the asset path
    points at a real raster.
    """
    cmd = [
        "ffmpeg", "-loglevel", "error", "-y",
        "-i", str(mp4_path),
        "-vf", "select=eq(n\\,0)",
        "-vframes", "1", "-update", "1",
        str(jpg_path),
    ]
    try:
        subprocess.check_call(cmd)
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f"[generate_asset] ffmpeg frame extraction failed: {exc}",
              file=sys.stderr)
        return False
    return jpg_path.is_file()


def detect_output_raster(out_dir: Path, basename: str) -> Path | None:
    """Look for `<basename>.jpg` / `.png` / `.mp4` in `out_dir`.

    Promotes MP4 -> JPG (WanGP Qwen quirk) when needed.
    """
    jpg = out_dir / f"{basename}.jpg"
    if jpg.is_file():
        return jpg
    png = out_dir / f"{basename}.png"
    if png.is_file():
        return png
    mp4 = out_dir / f"{basename}.mp4"
    if mp4.is_file():
        if extract_first_frame(mp4, jpg):
            return jpg
        return mp4
    return None


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Render and register a reusable character asset (Qwen Image Edit Plus 2511).",
    )
    ap.add_argument("--name", required=True,
                    help="snake_case slug, e.g. character_spacesuit_helmet, "
                         "spaceship_cockpit, creature_moon_guardian.")
    ap.add_argument("--kind", required=True,
                    choices=["character", "vehicle", "creature", "location",
                             "prop", "other"],
                    help="Asset category (also enforces the slug prefix convention).")
    ap.add_argument("--description", required=True,
                    help="One-sentence visual description for future agent recall.")
    ap.add_argument("--prompt", required=True,
                    help="Image prompt text (Qwen edit / generate).")
    ap.add_argument("--alt-prompt", default=None)
    ap.add_argument("--negative-prompt", default=None)
    ap.add_argument("--ref-assets", nargs="*", default=[],
                    help="Library asset slugs to feed Qwen as additional refs.")
    ap.add_argument("--image-refs", nargs="*", default=[],
                    help="Extra raw paths (rare; prefer --ref-assets).")
    ap.add_argument("--video-prompt-type", default=None,
                    choices=["I", "KI", "i", "ki", ""])
    ap.add_argument("--tags", nargs="*", default=[],
                    help="Free-form tags for manifest filtering.")
    ap.add_argument("--aspect", default="9:16",
                    choices=["9:16", "16:9", "1:1", "free"],
                    help="Aspect tag for manifest AND render resolution/template. "
                         "9:16=720x1280, 16:9=1280x720. Also drives template "
                         "selection when --template is not given.")
    ap.add_argument("--resolution", default=None,
                    help="WxH render resolution. Overrides --aspect for rendering. "
                         "Default: derived from --aspect (720x1280 for 9:16, "
                         "1280x720 for 16:9, 720x1280 otherwise).")
    ap.add_argument("--seed", type=int, default=-1)
    ap.add_argument("--steps", type=int, default=None)
    ap.add_argument("--guidance-scale", type=float, default=None)
    ap.add_argument("--activated-loras", nargs="*", default=None)
    ap.add_argument("--loras-multipliers", default=None)
    ap.add_argument("--template", default=None,
                    help="Template path or alias (defaults to the 9x16 Qwen Edit Plus).")
    ap.add_argument("--source-post", default=None,
                    help="Post slug (e.g. 2026-05-02_1) credited as the bootstrap source.")
    ap.add_argument("--force", action="store_true",
                    help="Overwrite an existing slug in the manifest.")
    ap.add_argument("--assets-dir", default=str(ASSETS_DIR),
                    help="Override the assets folder (default: <profile-home>/assets).")
    ap.add_argument("--run", action="store_true",
                    help="After writing JSON, run wgp.py via the WanGP venv "
                         "and register the result.")
    ap.add_argument("--register-only", action="store_true",
                    help="Skip rendering; just register an already-on-disk file "
                         "at <assets-dir>/<name>.{jpg|png}.")
    ap.add_argument("--extra-wgp-args", nargs=argparse.REMAINDER, default=[],
                    help="Extra args appended to wgp.py when --run is set.")
    args = ap.parse_args()

    asset_manifest, gic = _import_local()

    if args.resolution is None:
        args.resolution = gic.ASPECT_RESOLUTIONS.get(args.aspect, "720x1280")

    # Validate slug + kind prefix convention (warning, not fatal -- some
    # legacy / multi-purpose assets may not follow the convention exactly).
    expected_prefixes = {
        "character": "character_",
        "vehicle": ("vehicle_", "spaceship_"),
        "creature": "creature_",
        "location": "location_",
        "prop": "prop_",
        "other": "",
    }
    pref = expected_prefixes[args.kind]
    if pref and not (args.name.startswith(pref) if isinstance(pref, str)
                     else any(args.name.startswith(p) for p in pref)):
        print(
            f"[generate_asset] WARNING: slug {args.name!r} does not start "
            f"with the {args.kind!r} prefix {pref!r}. Continuing anyway.",
            file=sys.stderr,
        )

    assets_dir = resolve_path(args.assets_dir) if args.assets_dir else ASSETS_DIR
    assets_dir.mkdir(parents=True, exist_ok=True)

    # Pre-check: refuse to clobber unless --force.
    if not args.force and asset_manifest.get(args.name):
        raise SystemExit(
            f"[generate_asset] asset {args.name!r} already exists in the "
            f"manifest. Pass --force to overwrite."
        )

    if args.register_only:
        candidate = detect_output_raster(assets_dir, args.name)
        if not candidate:
            raise SystemExit(
                f"[generate_asset] --register-only: no {args.name}.jpg / .png "
                f"/ .mp4 found in {assets_dir}"
            )
        entry = asset_manifest.add(
            args.name, str(candidate),
            kind=args.kind, description=args.description, aspect=args.aspect,
            tags=args.tags, parent_refs=list(args.ref_assets),
            source_post=args.source_post, force=args.force,
        )
        print(str(candidate))
        print(f"[generate_asset] registered {args.name!r} -> {candidate}",
              file=sys.stderr)
        return 0

    image_refs = gic.merge_refs(args.ref_assets, args.image_refs)
    template_path = gic.resolve_template(args.template, args.video_prompt_type,
                                         image_refs, args.aspect)
    video_prompt_type = gic.decide_video_prompt_type(args.video_prompt_type,
                                                     image_refs)

    settings = gic.build_settings(
        template_path,
        prompt=args.prompt,
        image_refs=image_refs,
        video_prompt_type=video_prompt_type,
        output_filename=args.name,
        resolution=args.resolution,
        seed=args.seed,
        alt_prompt=args.alt_prompt,
        negative_prompt=args.negative_prompt,
        steps=args.steps,
        guidance_scale=args.guidance_scale,
        activated_loras=args.activated_loras,
        loras_multipliers=args.loras_multipliers,
    )

    settings_path = gic.write_settings(
        settings, assets_dir, filename=f"{args.name}.json",
    )

    print(str(settings_path))
    if args.ref_assets:
        for slug, path in zip(args.ref_assets, image_refs[: len(args.ref_assets)]):
            print(f"[generate_asset] ref-asset {slug!r} -> {path}",
                  file=sys.stderr)
    print(
        f"[generate_asset] template={template_path.name} "
        f"video_prompt_type={video_prompt_type!r} "
        f"resolution={settings['resolution']} "
        f"refs={len(image_refs)} "
        f"-> {assets_dir}/{args.name}.{{jpg|mp4}}",
        file=sys.stderr,
    )

    if not args.run:
        print(
            "[generate_asset] JSON written; rerun with --run to render and "
            "register, or invoke wgp.py manually then "
            f"`generate_asset.py --register-only --name {args.name} ...`.",
            file=sys.stderr,
        )
        return 0

    rc = gic.run_wgp(settings_path, assets_dir, args.extra_wgp_args)
    if rc != 0:
        print(f"[generate_asset] wgp.py exited {rc}; not registering.",
              file=sys.stderr)
        return rc

    raster = detect_output_raster(assets_dir, args.name)
    if not raster:
        print(f"[generate_asset] WanGP run completed but no raster found at "
              f"{assets_dir}/{args.name}.* -- not registering.",
              file=sys.stderr)
        return 1

    entry = asset_manifest.add(
        args.name, str(raster),
        kind=args.kind, description=args.description, aspect=args.aspect,
        tags=args.tags, parent_refs=list(args.ref_assets),
        source_post=args.source_post, force=args.force,
    )
    print(f"[generate_asset] registered {args.name!r} -> {raster}",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
