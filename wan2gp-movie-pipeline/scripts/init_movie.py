#!/usr/bin/env python3
"""init_movie.py -- Initialize a movie project from movie_script.json.

Validates the script, creates scene subfolders, and writes an initial
progress.json with all scenes set to "pending".

Usage:
    python3 init_movie.py --movie-dir /path/to/posts/2026-05-04_movie_fantasy
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REQUIRED_MOVIE_FIELDS = {"title", "aspect", "seed", "scenes"}
BASE_SCENE_FIELDS = {
    "id", "title", "anchor_filename", "video_prompt", "video_filename",
}
ANCHOR_SCENE_FIELDS = {"anchor_prompt", "image_refs"}
VALID_ASPECTS = {"9:16", "16:9"}
VALID_MODELS = {"gguf", "distilled-1.1"}

def validate_script(script: dict, movie_dir: Path) -> list[str]:
    """Return a list of validation errors (empty = valid).

    Validates image_refs as local paths relative to movie_dir (no manifest).
    Validates continue_from / anchor_from_last_frame mutual exclusivity and
    scene ordering.
    """
    errors: list[str] = []

    for field in REQUIRED_MOVIE_FIELDS:
        if field not in script:
            errors.append(f"Missing top-level field: {field}")

    aspect = script.get("aspect", "")
    if aspect and aspect not in VALID_ASPECTS:
        errors.append(f"Invalid aspect '{aspect}'; must be one of {VALID_ASPECTS}")

    model = script.get("model", "distilled-1.1")
    if model not in VALID_MODELS:
        errors.append(f"Invalid model '{model}'; must be one of {VALID_MODELS}")

    seed = script.get("seed")
    if seed is not None and not isinstance(seed, int):
        errors.append(f"seed must be an integer, got {type(seed).__name__}")

    scenes = script.get("scenes", [])
    if not scenes:
        errors.append("scenes array is empty")

    seen_ids: list[str] = []
    for i, scene in enumerate(scenes):
        prefix = f"scenes[{i}]"
        if not isinstance(scene, dict):
            errors.append(f"{prefix}: must be an object")
            continue

        continue_from = scene.get("continue_from")
        anchor_from_last = scene.get("anchor_from_last_frame")

        if continue_from and anchor_from_last:
            errors.append(
                f"{prefix}: cannot have both 'continue_from' and "
                f"'anchor_from_last_frame' on the same scene"
            )

        for field in BASE_SCENE_FIELDS:
            if field not in scene:
                errors.append(f"{prefix}: missing field '{field}'")

        if not continue_from:
            for field in ANCHOR_SCENE_FIELDS:
                if field not in scene:
                    errors.append(f"{prefix}: missing field '{field}' "
                                  f"(required unless 'continue_from' is set)")

        sid = scene.get("id", "")
        if sid in seen_ids:
            errors.append(f"{prefix}: duplicate scene id '{sid}'")
        seen_ids.append(sid)

        if continue_from:
            if continue_from not in seen_ids:
                if continue_from == sid:
                    errors.append(f"{prefix}: 'continue_from' cannot reference itself")
                else:
                    errors.append(
                        f"{prefix}: 'continue_from' references '{continue_from}' "
                        f"which has not appeared earlier in the scenes array"
                    )

        if anchor_from_last:
            if anchor_from_last not in seen_ids:
                if anchor_from_last == sid:
                    errors.append(f"{prefix}: 'anchor_from_last_frame' cannot reference itself")
                else:
                    errors.append(
                        f"{prefix}: 'anchor_from_last_frame' references "
                        f"'{anchor_from_last}' which has not appeared earlier "
                        f"in the scenes array"
                    )

        image_refs = scene.get("image_refs", [])
        if len(image_refs) > 3:
            errors.append(
                f"{prefix}: image_refs has {len(image_refs)} entries; "
                f"Qwen Image Edit Plus caps at 3"
            )
        for ref_path in image_refs:
            resolved = movie_dir / ref_path
            if not resolved.is_file():
                errors.append(
                    f"{prefix}: image_ref '{ref_path}' not found at {resolved}. "
                    f"Run Step 2b (bootstrap movie assets) before init."
                )

    return errors


def init_progress(movie_dir: Path, script: dict) -> dict:
    """Build the initial progress.json structure."""
    scenes = {}
    for scene in script["scenes"]:
        scenes[scene["id"]] = {
            "status": "pending",
            "steps": {
                "anchor_gen": {"status": "pending"},
                "video_gen": {"status": "pending"},
                "compress": {"status": "pending"},
            },
        }

    return {
        "movie_id": movie_dir.name,
        "status": "pending",
        "total_scenes": len(script["scenes"]),
        "completed_scenes": 0,
        "current_scene": None,
        "current_step": None,
        "started_at": None,
        "pipeline_pid": None,
        "scenes": scenes,
    }


def atomic_write_json(path: Path, data: dict) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    os.rename(str(tmp), str(path))


def main() -> int:
    ap = argparse.ArgumentParser(description="Initialize a movie project.")
    ap.add_argument(
        "--movie-dir", required=True,
        help="Path to the movie folder (e.g., posts/2026-05-04_movie_fantasy). "
             "Will be created if it doesn't exist.",
    )
    args = ap.parse_args()

    movie_dir = Path(args.movie_dir).resolve()
    script_path = movie_dir / "movie_script.json"

    if not script_path.is_file():
        print(f"ERROR: movie_script.json not found at {script_path}", file=sys.stderr)
        print("Write movie_script.json first, then run init_movie.py.", file=sys.stderr)
        return 1

    script = json.loads(script_path.read_text())

    errors = validate_script(script, movie_dir)
    if errors:
        print("VALIDATION ERRORS:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    for scene in script["scenes"]:
        scene_dir = movie_dir / scene["id"]
        scene_dir.mkdir(parents=True, exist_ok=True)

    progress = init_progress(movie_dir, script)
    atomic_write_json(movie_dir / "progress.json", progress)

    print(f"Movie initialized: {movie_dir.name}")
    print(f"  Title:  {script.get('title', '(untitled)')}")
    print(f"  Aspect: {script.get('aspect', '9:16')}")
    print(f"  Seed:   {script.get('seed', -1)}")
    print(f"  Model:  {script.get('model', 'distilled-1.1')}")
    print(f"  Scenes: {len(script['scenes'])}")
    for scene in script["scenes"]:
        mode = "normal"
        if scene.get("continue_from"):
            mode = f"continue_from={scene['continue_from']}"
        elif scene.get("anchor_from_last_frame"):
            mode = f"anchor_from_last_frame={scene['anchor_from_last_frame']}"
        refs = ", ".join(scene.get("image_refs", [])) or "(none)"
        print(f"    {scene['id']}: {scene['title']} [{mode}] [image_refs: {refs}]")
    print(f"\nProgress file: {movie_dir / 'progress.json'}")
    print("Run: python3 .../run_pipeline.py --movie-dir", movie_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
