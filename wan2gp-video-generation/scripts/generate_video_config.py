#!/usr/bin/env python3
"""generate_video_config.py -- WanGP video_generation.json builder for LTX-2.3.

Reads an LTX-2.3 template (T2V or I2V), applies CLI overrides, writes a
full WanGP `--process` task JSON to <output-dir>/video_generation.json.

Why this exists:
    Authoring a 50-key WanGP video JSON by hand is the #1 source of
    config mistakes (missing `sliding_window_size`, wrong `image_mode`,
    legacy `start_image` field, mismatched `video_length`, etc). This
    script clones the right template and patches only what the agent
    explicitly changes.

Stdlib only (json, argparse, pathlib, copy, subprocess). Safe with
system `python3` -- does NOT import torch / diffusers.

Usage (T2V):
    python3 generate_video_config.py \\
        --prompt "EXT. ALIEN STATION DECK..." \\
        --output-filename character_aurora_reel \\
        --output-dir /home/.../posts/2026-04-30_5

Usage (I2V from anchor):
    python3 generate_video_config.py \\
        --prompt "EXT. ALIEN STATION DECK..." \\
        --image-start /home/.../posts/2026-04-30_5/character_aurora_anchor.jpg \\
        --output-filename character_aurora_reel \\
        --output-dir /home/.../posts/2026-04-30_5

Usage (Continue from previous video):
    python3 generate_video_config.py \\
        --prompt "She continues walking along the bank..." \\
        --video-source /home/.../scene_01/scene_01_video.mp4 \\
        --output-filename scene_02_video \\
        --output-dir /home/.../scene_02

Add `--run` to also execute `wgp.py --process` from the WanGP venv.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import os
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

TEMPLATE_ALIASES = {
    "default": "ltx-2.3-t2v.json",
    "t2v": "ltx-2.3-t2v.json",
    "i2v": "ltx-2.3-i2v.json",
    "ltx": "ltx-2.3-t2v.json",
    "ltx-t2v": "ltx-2.3-t2v.json",
    "ltx-i2v": "ltx-2.3-i2v.json",
    "ltx-2.3-t2v": "ltx-2.3-t2v.json",
    "ltx-2.3-i2v": "ltx-2.3-i2v.json",
    "16x9": "ltx-2.3-t2v-16x9.json",
    "t2v-16x9": "ltx-2.3-t2v-16x9.json",
    "i2v-16x9": "ltx-2.3-i2v-16x9.json",
    "ltx-16x9": "ltx-2.3-t2v-16x9.json",
    "ltx-t2v-16x9": "ltx-2.3-t2v-16x9.json",
    "ltx-i2v-16x9": "ltx-2.3-i2v-16x9.json",
    "ltx-2.3-t2v-16x9": "ltx-2.3-t2v-16x9.json",
    "ltx-2.3-i2v-16x9": "ltx-2.3-i2v-16x9.json",
}

ASPECT_RESOLUTIONS = {
    "9:16": "720x1280",
    "16:9": "1280x720",
}

HF_LTX_BASE = "https://huggingface.co/DeepBeepMeep/LTX-2/resolve/main"

MODEL_CONFIGS: dict[str, dict] = {
    "gguf": {
        "model_filename": f"{HF_LTX_BASE}/ltx-2.3-22b-distilled-Q6_K_light.gguf",
        "model_type": "ltx2_22B_distilled_gguf_q6_k",
        "base_model_type": "ltx2_22B",
        "num_inference_steps": 8,
    },
    "distilled-1.1": {
        "model_filename": f"{HF_LTX_BASE}/ltx-2.3-22b-distilled-1.1_diffusion_model_quanto_bf16_int8.safetensors",
        "model_type": "ltx2_22B_distilled_1_1",
        "base_model_type": "ltx2_22B",
        "num_inference_steps": 8,
    },
}

MODEL_CHOICES = sorted(MODEL_CONFIGS)

LTX2_LATENT_SIZE = 8
LTX2_FPS = 24


def _align_frames(n: int, latent_size: int = LTX2_LATENT_SIZE) -> int:
    """Snap frame count to the nearest valid value (must satisfy (n-1) % latent_size == 0)."""
    return (n - 1) // latent_size * latent_size + 1


def _compute_window_count(video_length: int, window_size: int,
                          discard_last: int, overlap: int) -> int:
    """Mirror WanGP's compute_sliding_window_no formula."""
    left = video_length - window_size + discard_last
    return 1 + math.ceil(left / (window_size - discard_last - overlap))


def resolve_template(template_arg: str | None, image_start: str | None,
                     aspect: str | None = None,
                     video_source: str | None = None) -> Path:
    """Pick a template file based on shorthand, path, anchor/video presence, or aspect."""
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
            f"[generate_video_config] template not found: {template_arg!r}. "
            f"Aliases: {sorted(TEMPLATE_ALIASES)}"
        )
    is_landscape = aspect == "16:9"
    if image_start or video_source:
        return TEMPLATES_DIR / ("ltx-2.3-i2v-16x9.json" if is_landscape else "ltx-2.3-i2v.json")
    return TEMPLATES_DIR / ("ltx-2.3-t2v-16x9.json" if is_landscape else "ltx-2.3-t2v.json")


def build_settings(template_path: Path, args: argparse.Namespace) -> dict:
    template = json.loads(template_path.read_text())
    settings = copy.deepcopy(template)

    # --- Model config overlay (before CLI scalars so explicit flags win) ---
    mcfg = MODEL_CONFIGS[args.model]
    settings["model_filename"] = mcfg["model_filename"]
    settings["model_type"] = mcfg["model_type"]
    settings["base_model_type"] = mcfg["base_model_type"]
    if args.steps is None:
        settings["num_inference_steps"] = mcfg["num_inference_steps"]
    for key in ("sample_solver", "audio_guidance_scale", "alt_guidance_scale",
                "alt_scale", "perturbation_switch", "perturbation_layers",
                "perturbation_start_perc", "perturbation_end_perc",
                "apg_switch", "cfg_star_switch"):
        if key in mcfg:
            settings[key] = mcfg[key]
    if args.guidance_scale is None and "guidance_scale" in mcfg:
        settings["guidance_scale"] = mcfg["guidance_scale"]

    # --- Prompt / output ---
    settings["prompt"] = args.prompt
    if args.alt_prompt is not None:
        settings["alt_prompt"] = args.alt_prompt
    if args.negative_prompt is not None:
        settings["negative_prompt"] = args.negative_prompt

    settings["output_filename"] = args.output_filename
    settings["resolution"] = args.resolution
    settings["seed"] = args.seed

    if args.video_length is not None:
        settings["video_length"] = args.video_length
    if args.sliding_window_size is not None:
        settings["sliding_window_size"] = args.sliding_window_size
    if args.sliding_window_overlap is not None:
        settings["sliding_window_overlap"] = args.sliding_window_overlap

    if args.steps is not None:
        settings["num_inference_steps"] = args.steps
    if args.guidance_scale is not None:
        settings["guidance_scale"] = args.guidance_scale
    if args.audio_scale is not None:
        settings["audio_scale"] = args.audio_scale
    if args.loras_multipliers is not None:
        settings["loras_multipliers"] = args.loras_multipliers
    if args.activated_loras is not None:
        settings["activated_loras"] = args.activated_loras

    if args.no_loras:
        settings["activated_loras"] = []
        settings["loras_multipliers"] = ""

    if args.video_source and args.image_start:
        raise SystemExit(
            "[generate_video_config] --video-source and --image-start are "
            "mutually exclusive. Use one or the other."
        )

    if args.video_source:
        settings["image_mode"] = 0
        settings["image_prompt_type"] = "V"
        settings["input_video_strength"] = 1
        settings["video_source"] = args.video_source
        settings["keep_frames_video_source"] = args.keep_frames_video_source

    elif args.image_start:
        # LTX-2.3 native I2V (`image_mode: 1`) crashes at the VAE step in
        # WanGP. The proven workaround keeps `image_mode: 0` and feeds the
        # anchor through `image_prompt_type: "S"` + `input_video_strength: 1`
        # (see wan2gp-video-generation/SKILL.md "LTX-2.3 I2V Crash Bypass").
        settings["image_mode"] = 0
        settings["image_prompt_type"] = "S"
        settings["input_video_strength"] = 1
        settings["image_start"] = args.image_start

    return settings


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Build a WanGP LTX-2.3 video_generation.json from a template + overrides."
    )
    ap.add_argument("--prompt", required=True, help="LTX-2.3 cinematic prompt.")
    ap.add_argument("--alt-prompt", default=None)
    ap.add_argument("--negative-prompt", default=None)
    ap.add_argument(
        "--image-start", default=None,
        help="Absolute path to anchor JPG/PNG (auto-switches template to I2V).",
    )
    ap.add_argument(
        "--video-source", default=None,
        help="Absolute path to video to continue from (sets image_prompt_type='V'). "
             "Mutually exclusive with --image-start.",
    )
    ap.add_argument(
        "--keep-frames-video-source", default="",
        help="Frames to keep from source video (empty=all, negative=truncate from end).",
    )
    ap.add_argument("--output-filename", required=True,
                    help="WanGP `output_filename` (basename, no extension).")
    ap.add_argument("--output-dir", required=True,
                    help="Destination folder. video_generation.json is written here.")
    ap.add_argument("--aspect", default=None, choices=["9:16", "16:9"],
                    help="Aspect ratio shorthand. Sets resolution and picks the "
                         "matching template when --resolution/--template are not "
                         "given. 9:16=720x1280 (portrait), 16:9=1280x720 (landscape).")
    ap.add_argument("--resolution", default=None,
                    help="WxH (e.g. 720x1280 or 1280x720). Overrides --aspect. "
                         "Default: derived from --aspect, or 720x1280 if neither given.")
    ap.add_argument("--seed", type=int, default=-1)
    ap.add_argument("--video-length", type=int, default=None,
                    help="Total frames to generate; template default is 481 (~20s @ 24fps). "
                         "Set higher than sliding_window_size for multi-window "
                         "extended videos (e.g. 961 for ~40s).")
    ap.add_argument("--sliding-window-size", type=int, default=None,
                    help="Frames per generation window; template default is 481. "
                         "When video_length > this value, WanGP generates multiple "
                         "overlapping windows and stitches them. Max 501 for LTX2.")
    ap.add_argument("--sliding-window-overlap", type=int, default=None,
                    help="Overlap frames between consecutive windows (default 17 "
                         "from template). More overlap = smoother transitions. "
                         "Must be aligned to latent step (valid: 1, 9, 17, 25...).")
    ap.add_argument("--steps", type=int, default=None,
                    help="num_inference_steps override (template default 8-10).")
    ap.add_argument("--guidance-scale", type=float, default=None)
    ap.add_argument("--audio-scale", type=float, default=None)
    ap.add_argument("--loras-multipliers", default=None)
    ap.add_argument("--activated-loras", nargs="*", default=None)
    ap.add_argument("--no-loras", action="store_true",
                    help="Clear all LoRAs (overrides template defaults).")
    ap.add_argument("--model", default="distilled-1.1", choices=MODEL_CHOICES,
                    help="LTX-2.3 checkpoint variant. Sets model_filename, model_type, "
                         f"and num_inference_steps. Choices: {MODEL_CHOICES}. "
                         "Default: distilled-1.1.")
    ap.add_argument("--template", default=None,
                    help=f"Template path or alias. Aliases: {sorted(TEMPLATE_ALIASES)}")
    ap.add_argument("--run", action="store_true",
                    help="After writing JSON, execute wgp.py --process via WanGP venv.")
    ap.add_argument("--extra-wgp-args", nargs=argparse.REMAINDER, default=[],
                    help="Extra args appended to wgp.py when --run is set.")
    args = ap.parse_args()

    out_dir = Path(args.output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.resolution is None:
        args.resolution = ASPECT_RESOLUTIONS.get(args.aspect, "720x1280")

    template_path = resolve_template(args.template, args.image_start, args.aspect,
                                     args.video_source)
    settings = build_settings(template_path, args)

    out_path = out_dir / "video_generation.json"
    out_path.write_text(json.dumps(settings, indent=4) + "\n")

    print(str(out_path))
    active_loras = settings.get("activated_loras", [])
    loras_str = ", ".join(active_loras) if active_loras else "none"
    vlen = settings["video_length"]
    wsize = settings["sliding_window_size"]
    woverlap = settings["sliding_window_overlap"]
    print(
        f"[generate_video_config] model={args.model} template={template_path.name} "
        f"resolution={settings['resolution']} "
        f"steps={settings['num_inference_steps']} "
        f"video_length={vlen} "
        f"sliding_window_size={wsize} "
        f"sliding_window_overlap={woverlap} "
        f"image_start={'yes' if args.image_start else 'no'} "
        f"video_source={'yes' if args.video_source else 'no'} "
        f"loras=[{loras_str}]",
        file=sys.stderr,
    )
    if vlen > wsize:
        discard = settings.get("sliding_window_discard_last_frames", 0)
        n_windows = _compute_window_count(vlen, wsize, discard, woverlap)
        duration_s = vlen / LTX2_FPS
        print(
            f"[generate_video_config] EXTENDED VIDEO: {n_windows} sliding windows "
            f"will be generated for ~{duration_s:.1f}s total ({vlen} frames). "
            f"Each window is {wsize} frames with {woverlap} frames overlap. "
            f"Estimated time: ~{n_windows * 3.5:.0f} min (distilled-1.1, RTX 4090).",
            file=sys.stderr,
        )
        if not args.image_start and not args.video_source:
            print(
                "[generate_video_config] WARNING: multi-window with T2V (no "
                "--image-start or --video-source). Each window generates "
                "independently without seeing prior frames. This may produce "
                "repetitive/disconnected output. Consider using --image-start "
                "or --video-source for coherent extended videos.",
                file=sys.stderr,
            )
    if args.video_source:
        print(
            "[generate_video_config] continue mode: video_source is set, so "
            "WanGP will continue from the last frames of the source video. "
            "The prompt should describe what happens NEXT (pure continuation "
            "motion), not re-describe the source video's content.",
            file=sys.stderr,
        )
    if args.image_start:
        # Anchor <-> Reel coherence reminder. LTX-2.3 in I2V mode decodes from
        # the anchor as frame 0, so the prompt opening MUST mirror the anchor
        # composition (same INT/EXT, same pose, same wardrobe, same light) and
        # MUST NOT contain hard cuts. See video-create-workflow SKILL.md ->
        # "Anchor <-> Reel coherence" and wan2gp-video-generation SKILL.md ->
        # "Opening frame must mirror your I2V anchor (no hard cuts)".
        print(
            "[generate_video_config] coherence reminder: image_start is set, so "
            "LTX-2.3 will decode from the anchor as frame 0. Verify the prompt "
            "opens with the SAME composition as the anchor (same INT/EXT, pose, "
            "wardrobe, light source, view through windows) and contains NO hard "
            "cuts (no 'CUT TO', 'cuts to ...', 'JUMP CUT', 'MEANWHILE'). Reveal "
            "new elements via camera moves only.",
            file=sys.stderr,
        )

    if args.run:
        if not WAN_APP_DIR.is_dir():
            print(f"[generate_video_config] WanGP app dir not found: {WAN_APP_DIR}",
                  file=sys.stderr)
            return 2
        env_python_str = os.environ.get("WAN_PYTHON")
        env_python = Path(env_python_str) if env_python_str else WAN_APP_DIR / "env" / "bin" / "python"
        if not env_python.is_file():
            print(f"[generate_video_config] WanGP venv python missing: {env_python}",
                  file=sys.stderr)
            return 2
        cmd = [
            str(env_python), "wgp.py",
            "--process", str(out_path),
            "--output-dir", str(out_dir),
            "--compile", "--attention", "sage2",
            "--profile", "4", "--fp16",
            *args.extra_wgp_args,
        ]
        print(f"[generate_video_config] running: {' '.join(cmd)}", file=sys.stderr)
        return subprocess.call(cmd, cwd=str(WAN_APP_DIR))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
