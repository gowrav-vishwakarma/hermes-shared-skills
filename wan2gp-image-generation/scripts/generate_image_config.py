#!/usr/bin/env python3
"""generate_image_config.py -- WanGP image_generation.json builder.

Reads a Qwen Image Edit Plus template, applies CLI overrides, and writes
a full WanGP `--process` task JSON to <output-dir>/image_generation.json.

Why this exists:
    Hermes agents repeatedly authored partial / wrong JSONs for `wgp.py
    --process` (missing keys, wrong `video_prompt_type`, square output from
    `KI` + single square ref, etc). This script clones the right template
    and only patches what the agent explicitly changes -- preventing both
    key drift and the `KI` / `I` aspect-ratio trap.

Reusable refs:
    Pass `--ref-assets <slug...>` to pull named refs from the profile asset
    library (`<profile-home>/assets/assets.json`). They are resolved to
    absolute paths and prepended to any `--image-refs` you also pass. The
    final list is capped at 3 (Qwen Image Edit Plus 2511 hard limit). Pass
    nothing at all to run pure text-to-image (empty `image_refs`,
    `video_prompt_type: ""`).

Stdlib only (json, argparse, pathlib, copy, os, sys, struct). Safe to run
with system `python3` -- does NOT import torch / diffusers.

Usage:
    python3 generate_image_config.py \\
        --prompt "Cinematic medium shot ..." \\
        --ref-assets character_base spaceship_cockpit \\
        --output-filename character_aurora_wonder \\
        --output-dir /home/.../posts/2026-04-30_5

Add `--run` to also execute `wgp.py --process` from the WanGP venv (must
be invoked from a shell that can `cd` into the WanGP app dir).
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import struct
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
TEMPLATES_DIR = SKILL_DIR / "templates"

sys.path.insert(0, str(SCRIPT_DIR))
try:
    from _env import required  # type: ignore
finally:
    try:
        sys.path.remove(str(SCRIPT_DIR))
    except ValueError:
        pass

WAN_APP_DIR = required("WAN_APP_DIR")

MAX_QWEN_REFS = 3

TEMPLATE_ALIASES = {
    "default": "qwen-image-edit-plus2-9x16.json",
    "9x16": "qwen-image-edit-plus2-9x16.json",
    "9x16-i": "qwen-image-edit-plus2-9x16.json",
    "ki": "qwen-image-edit-plus2-9x16-KI.json",
    "9x16-ki": "qwen-image-edit-plus2-9x16-KI.json",
    "16x9": "qwen-image-edit-plus2-16x9.json",
    "9x16-quality": "qwen-image-edit-plus2-9x16-quality.json",
    "16x9-quality": "qwen-image-edit-plus2-16x9-quality.json",
    "lightning": "qwen-image-edit-plus2-9x16-lightning.json",
    "9x16-lightning": "qwen-image-edit-plus2-9x16-lightning.json",
    "16x9-lightning": "qwen-image-edit-plus2-16x9-lightning.json",
    "flux": "flux2-klein-9b.json",
    "flux-klein": "flux2-klein-9b.json",
    "flux-16x9": "flux2-klein-16x9.json",
    "flux-klein-16x9": "flux2-klein-16x9.json",
}

ASPECT_RESOLUTIONS = {
    "9:16": "720x1280",
    "16:9": "1280x720",
}

ASPECT_RESOLUTIONS_QUALITY = {
    "9:16": "928x1664",
    "16:9": "1664x928",
}

# Imported lazily so the script remains usable in environments where the
# manifest helper is missing (e.g. fresh skill checkout). The lazy import
# also prevents an import cycle if asset_manifest ever needs anything here.
def _load_asset_manifest_module():
    sys.path.insert(0, str(SCRIPT_DIR))
    try:
        import asset_manifest  # type: ignore
    finally:
        try:
            sys.path.remove(str(SCRIPT_DIR))
        except ValueError:
            pass
    return asset_manifest


def resolve_template(template_arg: str | None, video_prompt_type: str | None,
                     image_refs: list[str], aspect: str | None = None,
                     quality: bool = False) -> Path:
    """Pick the template file based on shorthand or path.

    Defaults to `qwen-image-edit-plus2-9x16.json` (mode `I`). If the caller
    explicitly asks for `KI`, prefer the KI-shaped template.  When *aspect* is
    ``"16:9"`` and no explicit template is given, selects the 16x9 variant.
    When *quality* is True, selects the native-resolution quality template.
    """
    if template_arg:
        candidate = Path(template_arg)
        if candidate.is_file():
            return candidate
        alias = TEMPLATE_ALIASES.get(template_arg.lower())
        if alias:
            return TEMPLATES_DIR / alias
        guess = TEMPLATES_DIR / template_arg
        if guess.is_file():
            return guess
        raise SystemExit(
            f"[generate_image_config] template not found: {template_arg!r}. "
            f"Aliases: {sorted(TEMPLATE_ALIASES)}"
        )
    if (video_prompt_type or "").upper() == "KI" and len(image_refs) >= 2:
        return TEMPLATES_DIR / "qwen-image-edit-plus2-9x16-KI.json"
    if quality:
        if aspect == "16:9":
            return TEMPLATES_DIR / "qwen-image-edit-plus2-16x9-quality.json"
        return TEMPLATES_DIR / "qwen-image-edit-plus2-9x16-quality.json"
    if aspect == "16:9":
        return TEMPLATES_DIR / "qwen-image-edit-plus2-16x9.json"
    return TEMPLATES_DIR / "qwen-image-edit-plus2-9x16.json"


def _read_image_dimensions(path: Path) -> tuple[int, int] | None:
    """Best-effort PNG/JPEG/WEBP width/height read using stdlib only.

    Returns (width, height) or None if the file isn't a recognised raster.
    Used purely to pick a sensible `I` vs `KI` default.
    """
    try:
        with path.open("rb") as fh:
            head = fh.read(32)
        if head.startswith(b"\x89PNG\r\n\x1a\n"):
            with path.open("rb") as fh:
                fh.seek(16)
                w, h = struct.unpack(">II", fh.read(8))
            return int(w), int(h)
        if head[:3] == b"\xff\xd8\xff":
            with path.open("rb") as fh:
                fh.read(2)
                while True:
                    b = fh.read(1)
                    while b and b != b"\xff":
                        b = fh.read(1)
                    marker = fh.read(1)
                    if not marker:
                        return None
                    m = marker[0]
                    if 0xC0 <= m <= 0xCF and m not in (0xC4, 0xC8, 0xCC):
                        fh.read(3)
                        h = int.from_bytes(fh.read(2), "big")
                        w = int.from_bytes(fh.read(2), "big")
                        return w, h
                    seg_len = int.from_bytes(fh.read(2), "big")
                    fh.read(seg_len - 2)
        if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
            if head[12:16] == b"VP8 ":
                with path.open("rb") as fh:
                    fh.seek(26)
                    w = int.from_bytes(fh.read(2), "little") & 0x3FFF
                    h = int.from_bytes(fh.read(2), "little") & 0x3FFF
                return w, h
            if head[12:16] == b"VP8L":
                with path.open("rb") as fh:
                    fh.seek(21)
                    b = fh.read(4)
                w = (b[0] | (b[1] << 8)) & 0x3FFF
                h = ((b[1] >> 6) | (b[2] << 2) | ((b[3] & 0xF) << 10)) & 0x3FFF
                return w + 1, h + 1
    except Exception:
        return None
    return None


def decide_video_prompt_type(explicit: str | None, refs: list[str]) -> str:
    """Pick `I`, `KI`, or `""` based on explicit flag, ref count, and first-ref aspect.

    Rules (in order):
      * If --video-prompt-type is given, respect it (uppercased; "" stays "").
      * 0 refs                -> `""` (text-to-image / no reference path).
      * 1 ref                 -> `I` (single identity / no scene plate possible).
      * 2+ refs:
          - First ref non-square (w/h < 0.8 or > 1.2) -> `KI` (real scene plate).
          - Otherwise         -> `I`  (avoid the square-ref aspect collapse).
    """
    if explicit is not None:
        return explicit.upper() if explicit else ""
    if not refs:
        return ""
    if len(refs) < 2:
        return "I"
    first = Path(refs[0])
    dims = _read_image_dimensions(first) if first.is_file() else None
    if dims:
        w, h = dims
        if h and (w / h < 0.8 or w / h > 1.2):
            return "KI"
    return "I"


def merge_refs(ref_assets: list[str] | None, image_refs: list[str] | None,
               *, manifest_path=None) -> list[str]:
    """Resolve `ref_assets` slugs (via asset_manifest) and append `image_refs` paths.

    Order: library assets first, then explicit paths. Caps total at
    `MAX_QWEN_REFS` and exits with a clear error if exceeded.
    """
    out: list[str] = []
    if ref_assets:
        am = _load_asset_manifest_module()
        out.extend(am.resolve_refs(ref_assets, manifest_path=manifest_path))
    if image_refs:
        out.extend(str(Path(p)) for p in image_refs)
    if len(out) > MAX_QWEN_REFS:
        raise SystemExit(
            f"[generate_image_config] {len(out)} refs supplied; Qwen Image "
            f"Edit Plus 2511 caps at {MAX_QWEN_REFS}. Trim --ref-assets / "
            "--image-refs."
        )
    return out


def build_settings(template_path: Path, *, prompt: str,
                   image_refs: list[str], video_prompt_type: str,
                   output_filename: str, resolution: str = "720x1280",
                   seed: int = -1, alt_prompt: str | None = None,
                   negative_prompt: str | None = None,
                   steps: int | None = None,
                   guidance_scale: float | None = None,
                   activated_loras: list[str] | None = None,
                   loras_multipliers: str | None = None) -> dict:
    """Clone the template and patch the agent-controlled fields.

    Exposed as a module-level helper so generate_asset.py (and any future
    helper) can build the same settings dict without re-parsing argv.
    """
    template = json.loads(template_path.read_text())
    settings = copy.deepcopy(template)

    settings["prompt"] = prompt
    if alt_prompt is not None:
        settings["alt_prompt"] = alt_prompt
    if negative_prompt is not None:
        settings["negative_prompt"] = negative_prompt

    settings["image_refs"] = list(image_refs)
    settings["video_prompt_type"] = video_prompt_type

    settings["output_filename"] = output_filename
    settings["resolution"] = resolution
    settings["seed"] = seed

    if steps is not None:
        settings["num_inference_steps"] = steps
    if guidance_scale is not None:
        settings["guidance_scale"] = guidance_scale
    if activated_loras is not None:
        settings["activated_loras"] = activated_loras
    if loras_multipliers is not None:
        settings["loras_multipliers"] = loras_multipliers

    return settings


def write_settings(settings: dict, out_dir: Path,
                   filename: str = "image_generation.json") -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / filename
    out_path.write_text(json.dumps(settings, indent=4) + "\n")
    return out_path


def run_wgp(settings_path: Path, out_dir: Path,
            extra_args: list[str] | None = None) -> int:
    """Invoke `wgp.py --process` via the WanGP venv. Returns the exit code."""
    if not WAN_APP_DIR.is_dir():
        print(f"[generate_image_config] WanGP app dir not found: {WAN_APP_DIR}",
              file=sys.stderr)
        return 2
    env_python_str = os.environ.get("WAN_PYTHON")
    env_python = Path(env_python_str) if env_python_str else WAN_APP_DIR / "env" / "bin" / "python"
    if not env_python.is_file():
        print(f"[generate_image_config] WanGP venv python missing: {env_python}",
              file=sys.stderr)
        return 2
    cmd = [
        str(env_python), "wgp.py",
        "--process", str(settings_path),
        "--output-dir", str(out_dir),
        "--compile", "--attention", "sage2",
        "--profile", "4", "--bf16",
        *(extra_args or []),
    ]
    print(f"[generate_image_config] running: {' '.join(cmd)}", file=sys.stderr)
    return subprocess.call(cmd, cwd=str(WAN_APP_DIR))


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Build a WanGP image_generation.json from a template + overrides."
    )
    ap.add_argument("--prompt", required=True, help="Image prompt text.")
    ap.add_argument("--alt-prompt", default=None)
    ap.add_argument("--negative-prompt", default=None)
    ap.add_argument(
        "--image-refs", nargs="*", default=[],
        help="Zero or more reference image paths (absolute). Optional; for "
             "library assets prefer --ref-assets.",
    )
    ap.add_argument(
        "--ref-assets", nargs="*", default=[],
        help="Asset slugs from the profile manifest (assets.json) -- resolved to "
             "absolute paths and prepended to --image-refs.",
    )
    ap.add_argument(
        "--video-prompt-type", default=None,
        choices=["I", "KI", "i", "ki", ""],
        help="Force I, KI, or '' (text-only). If omitted, auto-decides based "
             "on ref count + first-ref aspect.",
    )
    ap.add_argument("--output-filename", required=True,
                    help="WanGP `output_filename` (basename, no extension).")
    ap.add_argument("--output-dir", required=True,
                    help="Destination folder. image_generation.json is written here.")
    ap.add_argument("--aspect", default=None, choices=["9:16", "16:9"],
                    help="Aspect ratio shorthand. Sets resolution and picks the "
                         "matching template when --resolution/--template are not "
                         "given. 9:16=720x1280 (portrait), 16:9=1280x720 (landscape).")
    ap.add_argument("--resolution", default=None,
                    help="WxH (e.g. 720x1280 or 1280x720). Overrides --aspect. "
                         "Default: derived from --aspect, or 720x1280 if neither given.")
    ap.add_argument("--seed", type=int, default=-1)
    ap.add_argument("--steps", type=int, default=None,
                    help="num_inference_steps override (template default 50).")
    ap.add_argument("--guidance-scale", type=float, default=None)
    ap.add_argument("--quality", action="store_true",
                    help="Use native model resolution (928x1664 / 1664x928) for "
                         "maximum photorealism. Slower but significantly sharper.")
    ap.add_argument("--activated-loras", nargs="*", default=None)
    ap.add_argument("--loras-multipliers", default=None)
    ap.add_argument("--template", default=None,
                    help=f"Template path or alias. Aliases: {sorted(TEMPLATE_ALIASES)}")
    ap.add_argument("--run", action="store_true",
                    help="After writing JSON, execute wgp.py --process via WanGP venv.")
    ap.add_argument("--extra-wgp-args", nargs=argparse.REMAINDER, default=[],
                    help="Extra args appended to wgp.py when --run is set.")
    args = ap.parse_args()

    out_dir = Path(args.output_dir).resolve()

    if args.resolution is None:
        res_map = ASPECT_RESOLUTIONS_QUALITY if args.quality else ASPECT_RESOLUTIONS
        args.resolution = res_map.get(args.aspect, "928x1664" if args.quality else "720x1280")

    image_refs = merge_refs(args.ref_assets, args.image_refs)

    template_path = resolve_template(args.template, args.video_prompt_type,
                                     image_refs, args.aspect,
                                     quality=args.quality)
    video_prompt_type = decide_video_prompt_type(args.video_prompt_type,
                                                 image_refs)

    settings = build_settings(
        template_path,
        prompt=args.prompt,
        image_refs=image_refs,
        video_prompt_type=video_prompt_type,
        output_filename=args.output_filename,
        resolution=args.resolution,
        seed=args.seed,
        alt_prompt=args.alt_prompt,
        negative_prompt=args.negative_prompt,
        steps=args.steps,
        guidance_scale=args.guidance_scale,
        activated_loras=args.activated_loras,
        loras_multipliers=args.loras_multipliers,
    )

    out_path = write_settings(settings, out_dir)

    print(str(out_path))

    if args.ref_assets:
        for slug, path in zip(args.ref_assets, image_refs[: len(args.ref_assets)]):
            print(f"[generate_image_config] ref-asset {slug!r} -> {path}",
                  file=sys.stderr)

    print(
        f"[generate_image_config] template={template_path.name} "
        f"video_prompt_type={video_prompt_type!r} "
        f"resolution={settings['resolution']} "
        f"refs={len(image_refs)}",
        file=sys.stderr,
    )

    if args.run:
        return run_wgp(out_path, out_dir, args.extra_wgp_args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
