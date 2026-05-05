#!/usr/bin/env python3
"""run_pipeline.py -- Autonomous movie pipeline runner.

Reads movie_script.json + progress.json, then processes each scene
sequentially: anchor image -> video -> compress. Updates progress.json
atomically after every step for crash recovery.

Usage:
    python3 run_pipeline.py --movie-dir /path/to/posts/2026-05-04_movie_fantasy

Run via terminal(background=true) -- this is a long-running process.
Re-running after a crash resumes from the last completed step.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
PROFILE_SKILLS = SKILL_DIR.parent

IMAGE_GEN_SCRIPT = PROFILE_SKILLS / "wan2gp-image-generation" / "scripts" / "generate_image_config.py"
VIDEO_GEN_SCRIPT = PROFILE_SKILLS / "wan2gp-video-generation" / "scripts" / "generate_video_config.py"

sys.path.insert(0, str(SCRIPT_DIR))
try:
    from _env import required  # type: ignore
finally:
    try:
        sys.path.remove(str(SCRIPT_DIR))
    except ValueError:
        pass

WAN_APP_DIR = required("WAN_APP_DIR")
_wan_python_override = os.environ.get("WAN_PYTHON")
WAN_PYTHON = Path(_wan_python_override) if _wan_python_override else WAN_APP_DIR / "env" / "bin" / "python"
WGP_SCRIPT = WAN_APP_DIR / "wgp.py"
ASSETS_DIR = required("CHARACTER_ASSETS_DIR")

GPU_POLL_INTERVAL = 30
GPU_MAX_WAIT = 1800  # 30 minutes max wait for GPU

FFMPEG_COMPRESS_ARGS = [
    "ffmpeg", "-y", "-loglevel", "error",
    "-i", "{input}",
    "-vcodec", "libx264", "-acodec", "aac",
    "-b:v", "2000k", "-b:a", "128k",
    "-movflags", "+faststart",
    "{output}",
]

_shutdown_requested = False


def _signal_handler(signum, frame):
    global _shutdown_requested
    _shutdown_requested = True
    log(f"Received signal {signum}, will exit after current step completes")


def log(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def atomic_write_json(path: Path, data: dict) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    os.rename(str(tmp), str(path))


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# GPU gating
# ---------------------------------------------------------------------------

def find_wgp_processes() -> list[dict]:
    """Find running wgp.py processes."""
    try:
        result = subprocess.run(
            ["ps", "aux"], capture_output=True, text=True, timeout=10,
        )
    except subprocess.TimeoutExpired:
        return []
    procs = []
    for line in result.stdout.strip().split("\n"):
        if "wgp.py" in line and "grep" not in line and "run_pipeline" not in line:
            parts = line.split()
            if len(parts) >= 2:
                try:
                    procs.append({"pid": int(parts[1]), "cmd": " ".join(parts[10:])})
                except (ValueError, IndexError):
                    pass
    return procs


def kill_orphan(pid: int) -> bool:
    """Try to kill an orphaned wgp.py. Returns True if killed successfully."""
    log(f"Attempting to kill orphaned wgp.py (PID {pid})")
    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(5)
        try:
            os.kill(pid, 0)
        except OSError:
            log(f"  PID {pid} terminated gracefully")
            return True

        log(f"  SIGTERM didn't work, trying SIGKILL on PID {pid}")
        os.kill(pid, signal.SIGKILL)
        time.sleep(3)
        try:
            os.kill(pid, 0)
        except OSError:
            log(f"  PID {pid} killed with SIGKILL")
            return True

        log(f"  WARNING: PID {pid} survived SIGKILL -- GPU may be in D-state (deadlocked)")
        log(f"  A hard reboot is likely required. Exiting pipeline.")
        return False
    except OSError as e:
        log(f"  kill failed: {e}")
        return True  # process already dead


def check_nvidia_smi() -> bool:
    """Quick check that nvidia-smi responds (GPU not deadlocked)."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                parts = line.split(",")
                if len(parts) >= 2:
                    used = int(parts[0].strip())
                    total = int(parts[1].strip())
                    log(f"  GPU: {used}MB / {total}MB VRAM")
            return True
    except subprocess.TimeoutExpired:
        log("  WARNING: nvidia-smi timed out -- GPU may be deadlocked")
    except Exception as e:
        log(f"  WARNING: nvidia-smi failed: {e}")
    return False


def wait_for_gpu() -> bool:
    """Block until no wgp.py processes are running. Returns False if GPU is deadlocked."""
    waited = 0
    while True:
        if _shutdown_requested:
            return False

        procs = find_wgp_processes()
        if not procs:
            if not check_nvidia_smi():
                log("GPU appears deadlocked. Cannot continue.")
                return False
            return True

        if waited == 0:
            log(f"GPU busy: {len(procs)} wgp.py process(es) running")
            for p in procs:
                log(f"  PID {p['pid']}: {p['cmd'][:80]}")

        if waited >= GPU_MAX_WAIT:
            log(f"GPU busy for {GPU_MAX_WAIT}s, attempting to kill orphans")
            for p in procs:
                if not kill_orphan(p["pid"]):
                    return False
            time.sleep(5)
            if find_wgp_processes():
                log("Failed to clear GPU after killing orphans")
                return False
            return check_nvidia_smi()

        time.sleep(GPU_POLL_INTERVAL)
        waited += GPU_POLL_INTERVAL
        if waited % 120 == 0:
            log(f"  Still waiting for GPU... ({waited}s elapsed)")


# ---------------------------------------------------------------------------
# Generation steps
# ---------------------------------------------------------------------------

def detect_anchor(scene_dir: Path, basename: str) -> Path | None:
    """Find the rendered anchor image (jpg/png/mp4->jpg promotion)."""
    for ext in (".jpg", ".jpeg", ".png"):
        candidate = scene_dir / f"{basename}{ext}"
        if candidate.is_file():
            return candidate

    mp4 = scene_dir / f"{basename}.mp4"
    if mp4.is_file():
        jpg = scene_dir / f"{basename}.jpg"
        rc = subprocess.call([
            "ffmpeg", "-loglevel", "error", "-y",
            "-i", str(mp4),
            "-vf", "select=eq(n\\,0)",
            "-vframes", "1", "-update", "1",
            str(jpg),
        ])
        if rc == 0 and jpg.is_file():
            return jpg
        return mp4

    return None


def detect_video(scene_dir: Path, basename: str) -> Path | None:
    """Find the rendered video file."""
    for ext in (".mp4",):
        candidate = scene_dir / f"{basename}{ext}"
        if candidate.is_file() and candidate.stat().st_size > 1_000_000:
            return candidate
    return None


def run_image_gen(scene: dict, scene_dir: Path, script: dict) -> int:
    """Generate anchor image via generate_image_config.py --run."""
    cmd = [
        str(WAN_PYTHON), str(IMAGE_GEN_SCRIPT),
        "--prompt", scene["anchor_prompt"],
        "--output-filename", scene["anchor_filename"],
        "--output-dir", str(scene_dir),
        "--aspect", script.get("aspect", "9:16"),
        "--seed", str(script["seed"]),
    ]

    ref_assets = scene.get("ref_assets", [])
    if ref_assets:
        cmd.extend(["--ref-assets"] + ref_assets)

    cmd.append("--run")

    log(f"  Running image gen: {scene['anchor_filename']}")
    env = os.environ.copy()
    env["CHARACTER_ASSETS_DIR"] = str(ASSETS_DIR)
    return subprocess.call(cmd, cwd=str(WAN_APP_DIR), env=env)


def run_video_gen(scene: dict, scene_dir: Path, script: dict, anchor_path: Path) -> int:
    """Generate video config then run wgp.py."""
    config_cmd = [
        str(WAN_PYTHON), str(VIDEO_GEN_SCRIPT),
        "--prompt", scene["video_prompt"],
        "--image-start", str(anchor_path),
        "--output-filename", scene["video_filename"],
        "--output-dir", str(scene_dir),
        "--aspect", script.get("aspect", "9:16"),
        "--seed", str(script["seed"]),
    ]

    model = script.get("model", "gguf")
    if model != "gguf":
        config_cmd.extend(["--model", model])

    log(f"  Writing video config: {scene['video_filename']}")
    env = os.environ.copy()
    env["CHARACTER_ASSETS_DIR"] = str(ASSETS_DIR)
    rc = subprocess.call(config_cmd, cwd=str(WAN_APP_DIR), env=env)
    if rc != 0:
        log(f"  ERROR: generate_video_config.py exited {rc}")
        return rc

    config_path = scene_dir / "video_generation.json"
    if not config_path.is_file():
        log(f"  ERROR: video_generation.json not created at {config_path}")
        return 1

    wgp_cmd = [
        str(WAN_PYTHON), str(WGP_SCRIPT),
        "--process", str(config_path),
        "--output-dir", str(scene_dir),
        "--compile", "--attention", "sage2",
        "--profile", "4", "--fp16",
    ]

    env = os.environ.copy()
    env["CHARACTER_ASSETS_DIR"] = str(ASSETS_DIR)
    log(f"  Running wgp.py for video (this takes 3-10 min)...")
    return subprocess.call(wgp_cmd, cwd=str(WAN_APP_DIR), env=env)


def run_compress(raw_path: Path, compressed_path: Path) -> int:
    """Compress video with ffmpeg."""
    if raw_path.stat().st_size < 20_000_000:
        log(f"  Raw file under 20MB ({raw_path.stat().st_size // 1_048_576}MB), copying as-is")
        import shutil
        shutil.copy2(str(raw_path), str(compressed_path))
        return 0

    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(raw_path),
        "-vcodec", "libx264", "-acodec", "aac",
        "-b:v", "2000k", "-b:a", "128k",
        "-movflags", "+faststart",
        str(compressed_path),
    ]
    log(f"  Compressing: {raw_path.name} -> {compressed_path.name}")
    return subprocess.call(cmd)


def run_concat(movie_dir: Path, script: dict) -> int:
    """Build concat_list.txt and concatenate all compressed scenes."""
    concat_list = movie_dir / "concat_list.txt"
    lines = []
    for scene in script["scenes"]:
        scene_dir = movie_dir / scene["id"]
        compressed = scene_dir / f"{scene['video_filename']}_compressed.mp4"
        if not compressed.is_file():
            raw = detect_video(scene_dir, scene["video_filename"])
            if raw:
                compressed = raw
            else:
                log(f"  WARNING: No video found for {scene['id']}, skipping in concat")
                continue
        lines.append(f"file '{compressed}'\n")

    if not lines:
        log("ERROR: No videos found to concatenate")
        return 1

    concat_list.write_text("".join(lines))

    output = movie_dir / "movie_final.mp4"
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(output),
    ]
    log(f"Concatenating {len(lines)} scenes -> movie_final.mp4")
    rc = subprocess.call(cmd)
    if rc == 0 and output.is_file():
        size_mb = round(output.stat().st_size / 1_048_576, 1)
        log(f"MOVIE COMPLETE: {output} ({size_mb} MB)")
    return rc


# ---------------------------------------------------------------------------
# Main pipeline loop
# ---------------------------------------------------------------------------

def process_scene(
    scene: dict,
    scene_dir: Path,
    script: dict,
    progress: dict,
    progress_path: Path,
) -> bool:
    """Process a single scene. Returns True on success, False on failure."""
    sid = scene["id"]
    scene_progress = progress["scenes"][sid]
    steps = scene_progress["steps"]

    progress["current_scene"] = sid
    scene_progress["status"] = "in_progress"

    # --- Step 1: Anchor generation ---
    if steps["anchor_gen"]["status"] != "done":
        existing = detect_anchor(scene_dir, scene["anchor_filename"])
        if existing:
            log(f"  Anchor already exists: {existing.name}, skipping gen")
            steps["anchor_gen"]["status"] = "done"
            steps["anchor_gen"]["file"] = str(existing.relative_to(scene_dir.parent))
            steps["anchor_gen"]["finished_at"] = now_iso()
        else:
            progress["current_step"] = "anchor_gen"
            steps["anchor_gen"]["status"] = "running"
            steps["anchor_gen"]["started_at"] = now_iso()
            atomic_write_json(progress_path, progress)

            if not wait_for_gpu():
                return False

            rc = run_image_gen(scene, scene_dir, script)
            if rc != 0:
                log(f"  ERROR: Image generation failed (exit {rc})")
                steps["anchor_gen"]["status"] = "failed"
                steps["anchor_gen"]["error"] = f"exit code {rc}"
                atomic_write_json(progress_path, progress)
                return False

            anchor = detect_anchor(scene_dir, scene["anchor_filename"])
            if not anchor:
                log(f"  ERROR: Anchor image not found after generation")
                steps["anchor_gen"]["status"] = "failed"
                steps["anchor_gen"]["error"] = "output file not found"
                atomic_write_json(progress_path, progress)
                return False

            steps["anchor_gen"]["status"] = "done"
            steps["anchor_gen"]["file"] = str(anchor.relative_to(scene_dir.parent))
            steps["anchor_gen"]["finished_at"] = now_iso()
            atomic_write_json(progress_path, progress)
            log(f"  anchor_gen DONE ({anchor.name})")

    if _shutdown_requested:
        return False

    # --- Step 2: Video generation ---
    if steps["video_gen"]["status"] != "done":
        existing_video = detect_video(scene_dir, scene["video_filename"])
        if existing_video:
            log(f"  Video already exists: {existing_video.name}, skipping gen")
            steps["video_gen"]["status"] = "done"
            steps["video_gen"]["file"] = str(existing_video.relative_to(scene_dir.parent))
            steps["video_gen"]["finished_at"] = now_iso()
        else:
            anchor = detect_anchor(scene_dir, scene["anchor_filename"])
            if not anchor:
                log(f"  ERROR: Cannot generate video -- anchor image missing")
                steps["video_gen"]["status"] = "failed"
                steps["video_gen"]["error"] = "anchor image missing"
                atomic_write_json(progress_path, progress)
                return False

            progress["current_step"] = "video_gen"
            steps["video_gen"]["status"] = "running"
            steps["video_gen"]["started_at"] = now_iso()
            atomic_write_json(progress_path, progress)

            if not wait_for_gpu():
                return False

            rc = run_video_gen(scene, scene_dir, script, anchor)
            if rc != 0:
                log(f"  ERROR: Video generation failed (exit {rc})")
                steps["video_gen"]["status"] = "failed"
                steps["video_gen"]["error"] = f"exit code {rc}"
                atomic_write_json(progress_path, progress)
                return False

            video = detect_video(scene_dir, scene["video_filename"])
            if not video:
                log(f"  ERROR: Video file not found after generation")
                steps["video_gen"]["status"] = "failed"
                steps["video_gen"]["error"] = "output file not found"
                atomic_write_json(progress_path, progress)
                return False

            size_mb = round(video.stat().st_size / 1_048_576, 1)
            steps["video_gen"]["status"] = "done"
            steps["video_gen"]["file"] = str(video.relative_to(scene_dir.parent))
            steps["video_gen"]["finished_at"] = now_iso()
            atomic_write_json(progress_path, progress)
            log(f"  video_gen DONE ({video.name}, {size_mb}MB)")

    if _shutdown_requested:
        return False

    # --- Step 3: Compression ---
    if steps["compress"]["status"] != "done":
        video_file = steps["video_gen"].get("file")
        if not video_file:
            log(f"  ERROR: Cannot compress -- no video file recorded")
            return False

        raw_path = scene_dir.parent / video_file
        compressed_path = scene_dir / f"{scene['video_filename']}_compressed.mp4"

        if compressed_path.is_file() and compressed_path.stat().st_size > 100_000:
            log(f"  Compressed file already exists: {compressed_path.name}")
            steps["compress"]["status"] = "done"
            steps["compress"]["file"] = str(compressed_path.relative_to(scene_dir.parent))
            steps["compress"]["finished_at"] = now_iso()
        else:
            progress["current_step"] = "compress"
            steps["compress"]["status"] = "running"
            atomic_write_json(progress_path, progress)

            rc = run_compress(raw_path, compressed_path)
            if rc != 0:
                log(f"  ERROR: Compression failed (exit {rc})")
                steps["compress"]["status"] = "failed"
                steps["compress"]["error"] = f"exit code {rc}"
                atomic_write_json(progress_path, progress)
                return False

            size_mb = round(compressed_path.stat().st_size / 1_048_576, 1)
            steps["compress"]["status"] = "done"
            steps["compress"]["file"] = str(compressed_path.relative_to(scene_dir.parent))
            steps["compress"]["finished_at"] = now_iso()
            atomic_write_json(progress_path, progress)
            log(f"  compress DONE ({compressed_path.name}, {size_mb}MB)")

    scene_progress["status"] = "completed"
    progress["completed_scenes"] = sum(
        1 for s in progress["scenes"].values() if s["status"] == "completed"
    )
    remaining = progress["total_scenes"] - progress["completed_scenes"]
    atomic_write_json(progress_path, progress)
    log(f"SCENE {sid}: COMPLETED ({remaining} remaining)")
    return True


def main() -> int:
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)

    ap = argparse.ArgumentParser(description="Run the movie pipeline.")
    ap.add_argument("--movie-dir", required=True, help="Path to the movie folder.")
    args = ap.parse_args()

    movie_dir = Path(args.movie_dir).resolve()
    script_path = movie_dir / "movie_script.json"
    progress_path = movie_dir / "progress.json"

    if not script_path.is_file():
        log(f"ERROR: movie_script.json not found at {script_path}")
        return 1
    if not progress_path.is_file():
        log("ERROR: progress.json not found. Run init_movie.py first.")
        return 1

    script = json.loads(script_path.read_text())
    progress = json.loads(progress_path.read_text())

    progress["status"] = "in_progress"
    progress["started_at"] = progress.get("started_at") or now_iso()
    progress["pipeline_pid"] = os.getpid()
    atomic_write_json(progress_path, progress)

    log(f"=== MOVIE PIPELINE START ===")
    log(f"Movie: {script.get('title', '(untitled)')} ({len(script['scenes'])} scenes)")
    log(f"Seed: {script.get('seed', -1)} | Model: {script.get('model', 'gguf')} | Aspect: {script.get('aspect', '9:16')}")
    log(f"PID: {os.getpid()}")

    already_done = sum(
        1 for s in progress["scenes"].values() if s["status"] == "completed"
    )
    if already_done > 0:
        log(f"Resuming: {already_done}/{len(script['scenes'])} scenes already completed")

    failed = False
    for scene in script["scenes"]:
        if _shutdown_requested:
            log("Shutdown requested, stopping after current scene")
            break

        sid = scene["id"]
        if progress["scenes"][sid]["status"] == "completed":
            log(f"SCENE {sid}: already completed, skipping")
            continue

        log(f"SCENE {sid}: {scene['title']}")
        scene_dir = movie_dir / sid
        scene_dir.mkdir(parents=True, exist_ok=True)

        if not process_scene(scene, scene_dir, script, progress, progress_path):
            if _shutdown_requested:
                log(f"Pipeline interrupted at {sid}")
            else:
                log(f"SCENE {sid}: FAILED")
                failed = True
            break

    if _shutdown_requested:
        progress["status"] = "interrupted"
        atomic_write_json(progress_path, progress)
        log("Pipeline interrupted. Re-run to resume.")
        return 130

    if failed:
        progress["status"] = "failed"
        atomic_write_json(progress_path, progress)
        log("Pipeline FAILED. Fix the issue and re-run to resume.")
        return 1

    all_done = all(
        s["status"] == "completed" for s in progress["scenes"].values()
    )
    if not all_done:
        progress["status"] = "incomplete"
        atomic_write_json(progress_path, progress)
        log("Not all scenes completed.")
        return 1

    log("All scenes completed. Starting final concatenation...")
    rc = run_concat(movie_dir, script)
    if rc != 0:
        progress["status"] = "concat_failed"
        atomic_write_json(progress_path, progress)
        log("Concatenation FAILED. Run concat_movie.py manually to retry.")
        return rc

    progress["status"] = "completed"
    progress["finished_at"] = now_iso()
    progress["current_scene"] = None
    progress["current_step"] = None
    progress["pipeline_pid"] = None
    atomic_write_json(progress_path, progress)

    log("=== MOVIE PIPELINE COMPLETE ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
