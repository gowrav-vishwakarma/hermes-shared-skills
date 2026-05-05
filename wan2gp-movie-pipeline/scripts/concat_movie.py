#!/usr/bin/env python3
"""concat_movie.py -- Concatenate all scene videos into the final movie.

Standalone script that can be run independently if the pipeline was
interrupted after all scenes completed but before concatenation.

Usage:
    python3 concat_movie.py --movie-dir /path/to/posts/2026-05-04_movie_fantasy
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Concatenate movie scenes into final video.")
    ap.add_argument("--movie-dir", required=True, help="Path to the movie folder.")
    ap.add_argument(
        "--use-raw", action="store_true",
        help="Use raw (uncompressed) video files instead of compressed.",
    )
    ap.add_argument(
        "--output", default=None,
        help="Output filename (default: movie_final.mp4 in movie-dir).",
    )
    args = ap.parse_args()

    movie_dir = Path(args.movie_dir).resolve()
    script_path = movie_dir / "movie_script.json"

    if not script_path.is_file():
        print(f"ERROR: movie_script.json not found at {script_path}", file=sys.stderr)
        return 1

    script = json.loads(script_path.read_text())
    scenes = script.get("scenes", [])

    if not scenes:
        print("ERROR: No scenes in movie_script.json", file=sys.stderr)
        return 1

    concat_list = movie_dir / "concat_list.txt"
    lines = []
    missing = []

    for scene in scenes:
        scene_dir = movie_dir / scene["id"]
        basename = scene["video_filename"]

        if args.use_raw:
            video = scene_dir / f"{basename}.mp4"
        else:
            video = scene_dir / f"{basename}_compressed.mp4"
            if not video.is_file():
                video = scene_dir / f"{basename}.mp4"

        if video.is_file():
            lines.append(f"file '{video}'\n")
        else:
            missing.append(scene["id"])

    if missing:
        print(f"WARNING: Missing videos for scenes: {', '.join(missing)}", file=sys.stderr)
        if not lines:
            print("ERROR: No videos found to concatenate", file=sys.stderr)
            return 1
        print(f"Proceeding with {len(lines)}/{len(scenes)} scenes", file=sys.stderr)

    concat_list.write_text("".join(lines))

    output = Path(args.output) if args.output else movie_dir / "movie_final.mp4"

    cmd = [
        "ffmpeg", "-y", "-loglevel", "warning",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(output),
    ]

    print(f"Concatenating {len(lines)} scenes...")
    rc = subprocess.call(cmd)

    if rc == 0 and output.is_file():
        size_mb = round(output.stat().st_size / 1_048_576, 1)
        print(f"DONE: {output} ({size_mb} MB)")
    elif rc != 0:
        print(f"ERROR: ffmpeg exited {rc}", file=sys.stderr)

    return rc


if __name__ == "__main__":
    raise SystemExit(main())
