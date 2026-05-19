#!/usr/bin/env python3
"""copy_trend.py -- Download an Instagram reel and generate a version with your character.

Orchestrates: yt-dlp download -> ffprobe inspect -> generate_video_config.py -> wgp.py

Requires: yt-dlp (pip install yt-dlp), ffprobe (from ffmpeg).

Usage:
    python3 copy_trend.py \\
        --url "https://www.instagram.com/reel/XXXXX/" \\
        --character-image /path/to/character_anchor.jpg \\
        --prompt "A young woman performs the trending dance in a studio..." \\
        --output-dir /path/to/output \\
        --output-filename trend_copy_v1

    # Download only (skip generation):
    python3 copy_trend.py \\
        --url "https://www.instagram.com/reel/XXXXX/" \\
        --download-only \\
        --output-dir /path/to/output

    # Use a pre-downloaded video (skip download):
    python3 copy_trend.py \\
        --trend-video /path/to/already_downloaded.mp4 \\
        --character-image /path/to/character_anchor.jpg \\
        --prompt "..." \\
        --output-dir /path/to/output \\
        --output-filename trend_copy_v1
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

sys.path.insert(0, str(SCRIPT_DIR))
try:
    from _env import resolve_path  # type: ignore
finally:
    try:
        sys.path.remove(str(SCRIPT_DIR))
    except ValueError:
        pass


def _reencode_for_decord(raw_path: Path, output_dir: Path) -> Path:
    """Re-encode a video to H.264/AAC so WanGP's decord reader can parse it.

    Instagram videos sometimes use codec settings that crash decord's
    avcodec_send_packet. A clean re-encode to yuv420p H.264 @ 24fps fixes this.
    """
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print("[copy_trend] WARNING: ffmpeg not found, skipping re-encode.", file=sys.stderr)
        return raw_path

    clean_path = output_dir / "trend_source_clean.mp4"
    cmd = [
        ffmpeg, "-i", str(raw_path),
        "-vcodec", "libx264", "-acodec", "aac",
        "-pix_fmt", "yuv420p", "-r", "24",
        "-movflags", "+faststart",
        str(clean_path), "-y",
    ]
    print(f"[copy_trend] Re-encoding for decord compatibility...", file=sys.stderr)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[copy_trend] WARNING: re-encode failed, using original: {result.stderr[:200]}", file=sys.stderr)
        return raw_path
    print(f"[copy_trend] Re-encoded: {clean_path}", file=sys.stderr)
    return clean_path


def download_reel(url: str, output_dir: Path) -> Path:
    """Download an Instagram reel via yt-dlp. Returns the path to the downloaded file."""
    yt_dlp = shutil.which("yt-dlp")
    if not yt_dlp:
        raise SystemExit(
            "[copy_trend] yt-dlp not found. Install it: pip install yt-dlp"
        )

    output_template = str(output_dir / "trend_source.%(ext)s")
    cmd = [
        yt_dlp,
        "--no-playlist",
        "-o", output_template,
        "--merge-output-format", "mp4",
        url,
    ]
    print(f"[copy_trend] Downloading: {url}", file=sys.stderr)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise SystemExit(f"[copy_trend] yt-dlp failed with exit code {result.returncode}")

    candidates = sorted(output_dir.glob("trend_source.*"), key=lambda p: p.stat().st_mtime, reverse=True)
    mp4_candidates = [c for c in candidates if c.suffix == ".mp4"]
    if mp4_candidates:
        raw = mp4_candidates[0]
    elif candidates:
        raw = candidates[0]
    else:
        raise SystemExit("[copy_trend] Download succeeded but no output file found.")

    clean = _reencode_for_decord(raw, output_dir)
    return clean


def probe_video(video_path: Path) -> dict:
    """Get video metadata via ffprobe."""
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        print("[copy_trend] WARNING: ffprobe not found, skipping video inspection.", file=sys.stderr)
        return {}

    cmd = [
        ffprobe, "-v", "quiet",
        "-print_format", "json",
        "-show_format", "-show_streams",
        str(video_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[copy_trend] WARNING: ffprobe failed: {result.stderr}", file=sys.stderr)
        return {}

    data = json.loads(result.stdout)
    info = {}
    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video":
            info["width"] = int(stream.get("width", 0))
            info["height"] = int(stream.get("height", 0))
            r_frame_rate = stream.get("r_frame_rate", "24/1")
            try:
                num, den = r_frame_rate.split("/")
                info["fps"] = round(int(num) / int(den), 2)
            except (ValueError, ZeroDivisionError):
                info["fps"] = 24.0
            info["nb_frames"] = int(stream.get("nb_frames", 0))
            break

    fmt = data.get("format", {})
    duration = float(fmt.get("duration", 0))
    info["duration"] = duration
    return info


def compute_video_length(duration: float, fps: float = 24.0, max_frames: int = 481) -> int:
    """Compute aligned frame count from duration, capped at max_frames."""
    raw = int(round(duration * fps)) + 1
    latent_size = 8
    aligned = (raw - 1) // latent_size * latent_size + 1
    return min(aligned, max_frames)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Download a trending reel and generate a character version via WanGP."
    )

    source = ap.add_mutually_exclusive_group(required=True)
    source.add_argument("--url", help="Instagram reel URL to download.")
    source.add_argument("--trend-video", help="Path to an already-downloaded trend video (skip download).")

    ap.add_argument("--character-image", default=None,
                    help="Path to character anchor image. Required for OVG mode.")
    ap.add_argument("--prompt", default=None,
                    help="LTX-2.3 prompt describing the character performing the trend.")
    ap.add_argument("--output-dir", required=True,
                    help="Output directory for downloaded video and generated config/video.")
    ap.add_argument("--output-filename", default="trend_copy",
                    help="Output video filename (no extension). Default: trend_copy.")
    ap.add_argument("--mode", default="OVG",
                    choices=["PVG", "OVG", "DVG", "EVG", "VG"],
                    help="Motion transfer mode. OVG=Aligned Pose (default), "
                         "PVG=Human Motion, DVG=Depth, EVG=Canny Edges.")
    ap.add_argument("--denoising-strength", type=float, default=1.0,
                    help="0.0-1.0. 1.0=full regeneration (default). Lower blends with original.")
    ap.add_argument("--aspect", default="9:16", choices=["9:16", "16:9"],
                    help="Output aspect ratio. Default: 9:16 (portrait/reel).")
    ap.add_argument("--seed", type=int, default=-1)
    ap.add_argument("--model", default="distilled-1.1",
                    help="LTX-2.3 model variant. Default: distilled-1.1.")
    ap.add_argument("--download-only", action="store_true",
                    help="Download the reel and print video info, then exit (no generation).")
    ap.add_argument("--config-only", action="store_true",
                    help="Write video_generation.json but don't start wgp.py.")
    ap.add_argument("--no-loras", action="store_true",
                    help="Disable all LoRAs.")
    ap.add_argument("--activated-loras", nargs="*", default=None)
    ap.add_argument("--loras-multipliers", default=None)
    ap.add_argument("--audio-from-control-video", action="store_true",
                    help="Extract audio from the control video and use it as soundtrack. "
                         "Auto-sets audio_prompt_type='K'. This is recommended for trend copy "
                         "so the character video uses the same sound as the original reel.")

    args = ap.parse_args()

    out_dir = resolve_path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- Step 1: Get the trend video ---
    if args.url:
        trend_video = download_reel(args.url, out_dir)
    else:
        trend_video = resolve_path(args.trend_video)
        if not trend_video.is_file():
            raise SystemExit(f"[copy_trend] Trend video not found: {trend_video}")
        trend_video = _reencode_for_decord(trend_video, out_dir)

    print(f"[copy_trend] Trend video: {trend_video}", file=sys.stderr)

    # --- Step 2: Inspect the video ---
    info = probe_video(trend_video)
    if info:
        print(
            f"[copy_trend] Video info: {info.get('width', '?')}x{info.get('height', '?')} "
            f"@ {info.get('fps', '?')} fps, {info.get('duration', '?'):.1f}s",
            file=sys.stderr,
        )

    if args.download_only:
        print(str(trend_video))
        if info:
            print(json.dumps(info, indent=2))
        return 0

    # --- Step 3: Validate required args for generation ---
    if not args.prompt:
        raise SystemExit(
            "[copy_trend] --prompt is required for generation. Describe the "
            "character performing the trend action."
        )
    if args.mode == "OVG" and not args.character_image:
        raise SystemExit(
            "[copy_trend] --character-image is required for OVG (Aligned Pose) mode."
        )

    # --- Step 4: Build generate_video_config.py command ---
    duration = info.get("duration", 20.0)
    video_length = compute_video_length(duration)

    config_cmd = [
        sys.executable,
        str(SCRIPT_DIR / "generate_video_config.py"),
        "--prompt", args.prompt,
        "--video-guide", str(trend_video),
        "--video-prompt-type", args.mode,
        "--denoising-strength", str(args.denoising_strength),
        "--output-filename", args.output_filename,
        "--output-dir", str(out_dir),
        "--aspect", args.aspect,
        "--seed", str(args.seed),
        "--model", args.model,
        "--video-length", str(video_length),
    ]
    if args.character_image:
        config_cmd += ["--image-start", str(resolve_path(args.character_image))]
    if args.no_loras:
        config_cmd.append("--no-loras")
    if args.activated_loras:
        config_cmd += ["--activated-loras"] + args.activated_loras
    if args.loras_multipliers:
        config_cmd += ["--loras-multipliers", args.loras_multipliers]
    if args.audio_from_control_video:
        config_cmd.append("--audio-from-control-video")

    print(f"[copy_trend] Generating config...", file=sys.stderr)
    result = subprocess.run(config_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise SystemExit(f"[copy_trend] generate_video_config.py failed (exit {result.returncode})")

    config_path = result.stdout.strip().split("\n")[0]
    print(result.stderr, file=sys.stderr, end="")
    print(f"[copy_trend] Config written: {config_path}", file=sys.stderr)

    if args.config_only:
        print(config_path)
        return 0

    # --- Step 5: Print wgp.py launch command ---
    wan_python = os.environ.get("WAN_PYTHON", "")
    wan_app_dir = os.environ.get("WAN_APP_DIR", "")
    if wan_python and wan_app_dir:
        launch_cmd = (
            f'TORCHINDUCTOR_FORCE_DISABLE=1 "{wan_python}" "{wan_app_dir}/wgp.py" '
            f'--process "{config_path}" '
            f'--output-dir "{out_dir}" '
            f'--attention sage2 --profile 4'
        )
        print(f"\n[copy_trend] Ready to generate. Run:", file=sys.stderr)
        print(launch_cmd, file=sys.stderr)
    else:
        print(
            "\n[copy_trend] Config ready. Set WAN_PYTHON and WAN_APP_DIR env vars, "
            "then run wgp.py --process with the config above.",
            file=sys.stderr,
        )

    print(config_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
