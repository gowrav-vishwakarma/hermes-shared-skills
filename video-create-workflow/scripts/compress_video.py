#!/usr/bin/env python3
"""compress_video.py -- ffmpeg-compress an mp4 for Telegram delivery.

Targets ~3-5 MB output for a typical 20s reel using libx264 at ~2 Mbps
video + 128 kbps AAC + faststart. If the input is already under
``--skip-under-mb`` (default 20 MB), the file is left alone and its
path is returned.

Usage::

    python3 compress_video.py path/to/input.mp4
    python3 compress_video.py path/to/input.mp4 --output path/to/out.mp4
    python3 compress_video.py path/to/input.mp4 --vbitrate 1800k --abitrate 96k

Prints the (possibly identical) absolute path of the file to deliver.
Stdlib only (calls system ffmpeg).
"""

from __future__ import annotations

import argparse
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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", help="Source mp4 file.")
    ap.add_argument("--output", default=None,
                    help="Output path. Default: <input>_compressed.mp4 alongside source.")
    ap.add_argument("--vbitrate", default="2000k", help="Video bitrate (libx264).")
    ap.add_argument("--abitrate", default="128k", help="Audio bitrate (aac).")
    ap.add_argument("--skip-under-mb", type=float, default=20.0,
                    help="If input is smaller than this, skip compression.")
    ap.add_argument("--force", action="store_true",
                    help="Always compress, even if input is small.")
    args = ap.parse_args()

    src = resolve_path(args.input)
    if not src.is_file():
        sys.exit(f"[compress_video] not a file: {src}")

    size_mb = src.stat().st_size / (1024 * 1024)
    if not args.force and size_mb < args.skip_under_mb:
        print(str(src))
        print(f"[compress_video] skip: {src.name} is {size_mb:.1f} MB (< {args.skip_under_mb} MB)",
              file=sys.stderr)
        return 0

    dst = resolve_path(args.output) if args.output else \
        src.with_name(f"{src.stem}_compressed.mp4")

    if not shutil.which("ffmpeg"):
        sys.exit("[compress_video] ffmpeg not on PATH.")

    cmd = [
        "ffmpeg", "-y", "-i", str(src),
        "-vcodec", "libx264", "-b:v", args.vbitrate,
        "-acodec", "aac", "-b:a", args.abitrate,
        "-movflags", "+faststart",
        str(dst),
    ]
    rc = subprocess.call(cmd)
    if rc != 0:
        sys.exit(f"[compress_video] ffmpeg failed (exit {rc}).")

    out_mb = dst.stat().st_size / (1024 * 1024)
    print(str(dst))
    print(f"[compress_video] {src.name} ({size_mb:.1f} MB) -> {dst.name} ({out_mb:.1f} MB)",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
