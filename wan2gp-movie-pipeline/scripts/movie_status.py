#!/usr/bin/env python3
"""movie_status.py -- Check movie pipeline progress.

Reads progress.json and prints a human-readable summary.

Exit codes:
    0 = all scenes completed (movie done)
    1 = in progress or interrupted
    2 = failed or stalled

Usage:
    python3 movie_status.py --movie-dir /path/to/posts/2026-05-04_movie_fantasy
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def is_pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def parse_iso(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{int(seconds)}s"
    if seconds < 3600:
        return f"{int(seconds // 60)}m {int(seconds % 60)}s"
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    return f"{h}h {m}m"


def main() -> int:
    ap = argparse.ArgumentParser(description="Check movie pipeline status.")
    ap.add_argument("--movie-dir", required=True, help="Path to the movie folder.")
    args = ap.parse_args()

    movie_dir = Path(args.movie_dir).resolve()
    progress_path = movie_dir / "progress.json"
    script_path = movie_dir / "movie_script.json"

    if not progress_path.is_file():
        print("ERROR: progress.json not found. Run init_movie.py first.")
        return 2

    progress = json.loads(progress_path.read_text())
    script = json.loads(script_path.read_text()) if script_path.is_file() else {}

    status = progress.get("status", "unknown")
    total = progress.get("total_scenes", 0)
    completed = progress.get("completed_scenes", 0)
    current_scene = progress.get("current_scene")
    current_step = progress.get("current_step")
    pipeline_pid = progress.get("pipeline_pid")

    title = script.get("title", progress.get("movie_id", "(untitled)"))

    print(f"Movie: {title}")
    print(f"Status: {status.upper()}")
    print(f"Progress: {completed}/{total} scenes completed")

    pipeline_alive = False
    if pipeline_pid:
        pipeline_alive = is_pid_alive(pipeline_pid)
        state = "RUNNING" if pipeline_alive else "DEAD"
        print(f"Pipeline PID: {pipeline_pid} ({state})")

    started = parse_iso(progress.get("started_at"))
    finished = parse_iso(progress.get("finished_at"))

    if started:
        if finished:
            elapsed = (finished - started).total_seconds()
            print(f"Total time: {format_duration(elapsed)}")
        else:
            elapsed = (datetime.now(timezone.utc) - started).total_seconds()
            print(f"Elapsed: {format_duration(elapsed)}")

            if completed > 0:
                avg_per_scene = elapsed / completed
                remaining = total - completed
                eta_seconds = avg_per_scene * remaining
                print(f"ETA: ~{format_duration(eta_seconds)} ({format_duration(avg_per_scene)} avg/scene)")

    if current_scene and status not in ("completed", "pending"):
        print(f"\nCurrent: {current_scene} -> {current_step or '?'}")

    print(f"\nScene details:")
    for scene_data in script.get("scenes", []):
        sid = scene_data.get("id", "?")
        scene_title = scene_data.get("title", "")
        sp = progress.get("scenes", {}).get(sid, {})
        scene_status = sp.get("status", "unknown")

        steps_summary = []
        for step_name in ("anchor_gen", "video_gen", "compress"):
            step = sp.get("steps", {}).get(step_name, {})
            st = step.get("status", "pending")
            if st == "done":
                steps_summary.append(f"{step_name}:OK")
            elif st == "running":
                steps_summary.append(f"{step_name}:RUNNING")
            elif st == "failed":
                err = step.get("error", "")
                steps_summary.append(f"{step_name}:FAILED({err})")
            else:
                steps_summary.append(f"{step_name}:--")

        marker = "+" if scene_status == "completed" else (">" if scene_status == "in_progress" else " ")
        print(f"  [{marker}] {sid}: {scene_title} ({scene_status}) [{' | '.join(steps_summary)}]")

    final_movie = movie_dir / "movie_final.mp4"
    if final_movie.is_file():
        size_mb = round(final_movie.stat().st_size / 1_048_576, 1)
        print(f"\nFinal movie: {final_movie} ({size_mb} MB)")

    if status == "completed":
        return 0
    elif status in ("failed", "concat_failed"):
        return 2
    elif not pipeline_alive and status == "in_progress":
        print("\nWARNING: Pipeline PID is dead but status is 'in_progress'.")
        print("The pipeline likely crashed. Re-run run_pipeline.py to resume.")
        return 2
    else:
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
