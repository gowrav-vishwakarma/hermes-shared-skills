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

Usage (Trend copy -- transfer motion from a reference video to a character):
    python3 generate_video_config.py \\
        --prompt "A young woman performs the dance..." \\
        --video-guide /home/.../downloaded_trend.mp4 \\
        --image-start /home/.../character_anchor.jpg \\
        --video-prompt-type OVG \\
        --output-filename trend_copy_v1 \\
        --output-dir /home/.../output

Usage (Trend copy with audio sync -- dance to the source video's music):
    python3 generate_video_config.py \\
        --prompt "A young woman dances energetically to the beat..." \\
        --video-guide /home/.../trend_source_clean.mp4 \\
        --image-start /home/.../character_anchor.jpg \\
        --video-prompt-type OVG \\
        --audio-from-control-video \\
        --output-filename trend_dance_v1 \\
        --output-dir /home/.../output

Usage (External audio conditioning -- sync to a specific soundtrack):
    python3 generate_video_config.py \\
        --prompt "The character dances to the rhythm..." \\
        --image-start /home/.../character_anchor.jpg \\
        --audio-guide /home/.../music_track.wav \\
        --output-filename dance_reel \\
        --output-dir /home/.../output

Usage (Intermediate frame injection -- keyframes at specific positions):
    python3 generate_video_config.py \\
        --prompt "The character transitions through emotional beats..." \\
        --image-start /home/.../opening.jpg \\
        --image-refs /home/.../midpoint.jpg /home/.../climax.jpg \\
        --frames-positions "120 240" \\
        --image-end /home/.../closing.jpg \\
        --video-length 361 \\
        --output-filename keyframe_reel \\
        --output-dir /home/.../output

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

VALID_VIDEO_PROMPT_TYPES = {
    "PVG": "Transfer Human Motion",
    "OVG": "Transfer Human Motion With Pose Alignment",
    "DVG": "Transfer Depth",
    "EVG": "Transfer Canny Edges",
    "VG": "LTX2 Raw Format / Control Video for IC LoRA",
    "KFI": "Inject Frames (Keyframe Injection)",
}


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
                     video_source: str | None = None,
                     video_guide: str | None = None,
                     image_end: str | None = None,
                     image_refs: list | None = None) -> Path:
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
    has_image_input = image_start or video_source or video_guide or image_end or image_refs
    if has_image_input:
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
    if args.video_source and args.video_guide:
        raise SystemExit(
            "[generate_video_config] --video-source and --video-guide are "
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

    # --- End frame ---
    if args.image_end:
        ipt = settings.get("image_prompt_type", "")
        if "E" not in ipt:
            settings["image_prompt_type"] = ipt + "E"
        settings["image_end"] = args.image_end

    # --- Intermediate frame injection (keyframes at specific positions) ---
    if args.image_refs:
        settings["image_refs"] = args.image_refs
        vpt_cur = settings.get("video_prompt_type", "")
        if "F" not in vpt_cur:
            settings["video_prompt_type"] = "KFI" if not vpt_cur else vpt_cur + "F"
        if args.frames_positions:
            positions_tokens = args.frames_positions.replace(",", " ").split()
            if len(positions_tokens) > len(args.image_refs):
                raise SystemExit(
                    f"[generate_video_config] --frames-positions has "
                    f"{len(positions_tokens)} tokens but only "
                    f"{len(args.image_refs)} --image-refs provided. "
                    f"Each position needs a corresponding image ref."
                )
            for tok in positions_tokens:
                if tok.upper() == "L":
                    continue
                if not tok.isdigit() or int(tok) < 1 or int(tok) > 3000:
                    raise SystemExit(
                        f"[generate_video_config] invalid frame position "
                        f"'{tok}'. Must be integer 1-3000 or 'L'."
                    )
            settings["frames_positions"] = args.frames_positions
        else:
            raise SystemExit(
                "[generate_video_config] --image-refs requires "
                "--frames-positions to specify where each keyframe goes."
            )
        vpt_final = settings.get("video_prompt_type", "")
        if "&" in vpt_final:
            raise SystemExit(
                "[generate_video_config] frame injection (F) cannot be "
                "combined with HDR IC-LoRA (&) in video_prompt_type."
            )

    # --- Control Video (motion/pose/depth transfer from a guide video) ---
    if args.video_guide:
        vpt = args.video_prompt_type
        if vpt not in VALID_VIDEO_PROMPT_TYPES:
            raise SystemExit(
                f"[generate_video_config] --video-prompt-type must be one of "
                f"{list(VALID_VIDEO_PROMPT_TYPES)} when --video-guide is set, "
                f"got {vpt!r}."
            )
        if "O" in vpt and not args.image_start:
            raise SystemExit(
                "[generate_video_config] Aligned Pose Transfer (OVG) requires "
                "--image-start. Provide a character anchor image."
            )
        settings["video_guide"] = args.video_guide
        settings["video_prompt_type"] = vpt
        settings["denoising_strength"] = args.denoising_strength
        settings["keep_frames_video_guide"] = args.keep_frames_video_guide

    # --- Audio conditioning ---
    if args.audio_guide and args.audio_from_control_video:
        raise SystemExit(
            "[generate_video_config] --audio-guide and --audio-from-control-video "
            "are mutually exclusive. Use one or the other."
        )

    if args.audio_from_control_video:
        if not args.video_guide:
            raise SystemExit(
                "[generate_video_config] --audio-from-control-video requires "
                "--video-guide. Provide a control video to extract audio from."
            )
        vpt_cur = settings.get("video_prompt_type", "")
        if "V" not in vpt_cur:
            raise SystemExit(
                "[generate_video_config] --audio-from-control-video requires 'V' "
                f"in video_prompt_type, got '{vpt_cur}'. Use OVG, PVG, DVG, EVG, or VG."
            )
        settings["audio_prompt_type"] = "K"
    elif args.audio_guide:
        settings["audio_prompt_type"] = "A"
        settings["audio_guide"] = args.audio_guide

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
        "--image-end", default=None,
        help="Absolute path to end-frame image. Auto-adds 'E' to image_prompt_type. "
             "The model will guide the video to end at this composition.",
    )
    ap.add_argument(
        "--image-refs", nargs="+", default=None,
        help="One or more paths to keyframe images for intermediate frame injection. "
             "Each pairs 1:1 with a position in --frames-positions. Auto-adds 'F' "
             "to video_prompt_type.",
    )
    ap.add_argument(
        "--frames-positions", default=None,
        help="Space- or comma-separated frame positions for --image-refs. "
             "Each token is a 1-based frame number (e.g., '80 160 240') or 'L' "
             "(last frame of window). Required when --image-refs is set.",
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
    ap.add_argument(
        "--video-guide", default=None,
        help="Absolute path to a control video for motion/pose/depth transfer. "
             "Used with --video-prompt-type to set the transfer mode. "
             "Can coexist with --image-start (recommended for OVG). "
             "Mutually exclusive with --video-source.",
    )
    ap.add_argument(
        "--video-prompt-type", default="OVG",
        choices=list(VALID_VIDEO_PROMPT_TYPES),
        help="Control video processing mode. "
             "PVG=Transfer Human Motion, OVG=Aligned Pose (needs --image-start), "
             "DVG=Transfer Depth, EVG=Transfer Canny Edges, "
             "VG=Raw Format / IC LoRA. Default: OVG.",
    )
    ap.add_argument(
        "--denoising-strength", type=float, default=1.0,
        help="Denoising strength for control video mode (0.0-1.0). "
             "1.0=full regeneration, lower values blend more with original. Default: 1.0.",
    )
    ap.add_argument(
        "--keep-frames-video-guide", default="",
        help="Frames to keep from the control video guide (empty=all).",
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
    ap.add_argument(
        "--audio-guide", default=None,
        help="Absolute path to an audio file (.wav/.mp3) to condition video on. "
             "Auto-sets audio_prompt_type='A'. The model syncs motion and lip "
             "movements to this audio.",
    )
    ap.add_argument(
        "--audio-from-control-video", action="store_true",
        help="Extract audio from --video-guide and use it as audio conditioning. "
             "Auto-sets audio_prompt_type='K'. Ideal for trend copy reels where "
             "the character should dance/lip-sync to the source video's music. "
             "Requires --video-guide with 'V' in --video-prompt-type.",
    )
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
                                     args.video_source, args.video_guide,
                                     args.image_end, args.image_refs)
    settings = build_settings(template_path, args)

    out_path = out_dir / "video_generation.json"
    out_path.write_text(json.dumps(settings, indent=4) + "\n")

    print(str(out_path))
    active_loras = settings.get("activated_loras", [])
    loras_str = ", ".join(active_loras) if active_loras else "none"
    vlen = settings["video_length"]
    wsize = settings["sliding_window_size"]
    woverlap = settings["sliding_window_overlap"]
    vpt = settings.get("video_prompt_type", "")
    vpt_label = VALID_VIDEO_PROMPT_TYPES.get(vpt, "none") if vpt else "none"
    print(
        f"[generate_video_config] model={args.model} template={template_path.name} "
        f"resolution={settings['resolution']} "
        f"steps={settings['num_inference_steps']} "
        f"video_length={vlen} "
        f"sliding_window_size={wsize} "
        f"sliding_window_overlap={woverlap} "
        f"image_start={'yes' if args.image_start else 'no'} "
        f"video_source={'yes' if args.video_source else 'no'} "
        f"video_guide={'yes' if args.video_guide else 'no'} "
        f"video_prompt_type={vpt or 'none'} ({vpt_label}) "
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
    if args.image_start and not args.video_guide:
        # Anchor <-> Reel coherence reminder (only for pure I2V, not control video).
        print(
            "[generate_video_config] coherence reminder: image_start is set, so "
            "LTX-2.3 will decode from the anchor as frame 0. Verify the prompt "
            "opens with the SAME composition as the anchor (same INT/EXT, pose, "
            "wardrobe, light source, view through windows) and contains NO hard "
            "cuts (no 'CUT TO', 'cuts to ...', 'JUMP CUT', 'MEANWHILE'). Reveal "
            "new elements via camera moves only.",
            file=sys.stderr,
        )
    if args.video_guide:
        vpt = settings.get("video_prompt_type", "")
        vpt_label = VALID_VIDEO_PROMPT_TYPES.get(vpt, vpt)
        print(
            f"[generate_video_config] CONTROL VIDEO mode: {vpt_label} ({vpt}). "
            f"Motion/structure from the guide video will be transferred. "
            f"denoising_strength={settings.get('denoising_strength', 1.0)} "
            f"(1.0=full regeneration).",
            file=sys.stderr,
        )
    apt = settings.get("audio_prompt_type", "")
    if apt == "K":
        print(
            "[generate_video_config] AUDIO: using control video's audio track "
            "(audio_prompt_type='K'). Character will sync to the video_guide's "
            "music/speech.",
            file=sys.stderr,
        )
    elif apt == "A":
        print(
            f"[generate_video_config] AUDIO: external audio file conditioning "
            f"(audio_prompt_type='A'). audio_guide={args.audio_guide}",
            file=sys.stderr,
        )
    if args.image_end:
        print(
            f"[generate_video_config] END FRAME: image_end is set, model will "
            f"guide video toward this composition at the last frame.",
            file=sys.stderr,
        )
    if args.image_refs:
        print(
            f"[generate_video_config] FRAME INJECTION: {len(args.image_refs)} "
            f"keyframe(s) at positions [{args.frames_positions}]. "
            f"video_prompt_type={settings.get('video_prompt_type', '')}.",
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
