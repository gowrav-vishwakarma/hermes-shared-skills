#!/usr/bin/env python3
"""monitor_video_gen.py -- Watch a running WanGP video gen.

Usage:
    python3 monitor_video_gen.py <post-folder>

Output: always prints STATUS + elapsed minutes.
Returns exit code 0 if COMPLETED, 1 if RUNNING, 2 if crashed.

The script computes elapsed minutes from process uptime so the agent
never has to track time between turns.

Exit codes:
    0 = COMPLETED (output MP4 exists)
    1 = RUNNING (still processing)
    2 = DEAD/CRASHED (process no longer alive, no output)
"""

import subprocess
import sys
import re
from pathlib import Path


def parse_etime(etime_str: str) -> int:
    """Parse ps etime format [DD-]HH:MM:SS into total seconds."""
    etime_str = etime_str.strip()
    days = 0
    if "-" in etime_str:
        days, etime_str = etime_str.split("-", 1)
        days = int(days)

    parts = etime_str.split(":")
    if len(parts) == 3:
        h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
    elif len(parts) == 2:
        h, m = 0, int(parts[0]), int(parts[1])
    else:
        h = m = s = 0

    return days * 86400 + h * 3600 + m * 60 + s


def find_video_process(post_dir: str) -> list[dict]:
    """Find wgp.py processes whose --process arg references the post folder."""
    result = subprocess.run(
        ["ps", "aux"], capture_output=True, text=True
    )
    running = []
    for line in result.stdout.strip().split("\n"):
        if "wgp.py" not in line or "grep" in line:
            continue
        parts = line.split()
        if len(parts) < 11:
            continue
        pid = parts[1]
        cpu = parts[2]
        mem = parts[3]
        etime = parts[9] if len(parts) > 9 else "00:00:00"
        cmd = " ".join(parts[10:])

        if post_dir in cmd:
            elapsed = parse_etime(etime)
            running.append({
                "pid": int(pid),
                "cpu": float(cpu),
                "mem": float(mem),
                "elapsed_seconds": elapsed,
                "elapsed_minutes": round(elapsed / 60, 1),
                "etime_raw": etime,
                "cmd": cmd,
            })
    return running


def check_gpu_usage() -> dict:
    """Quick snapshot of GPU memory usage."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True
        )
        lines = result.stdout.strip().split("\n")
        gpus = []
        for line in lines:
            parts = line.split(",")
            if len(parts) >= 2:
                used = int(parts[0].strip())
                total = int(parts[1].strip())
                gpus.append({"used_mb": used, "total_mb": total})
        return {"gpus": gpus, "ok": True}
    except Exception:
        return {"gpus": [], "ok": False, "error": "nvidia-smi failed"}


def check_output_file(post_dir: str) -> dict:
    """Check if output video file exists and its size."""
    out_dir = Path(post_dir)
    mp4_files = list(out_dir.glob("*.mp4"))
    if not mp4_files:
        return {"exists": False}
    for f in sorted(mp4_files, key=lambda p: p.stat().st_mtime, reverse=True):
        if "test" not in f.name.lower():
            return {
                "exists": True,
                "path": str(f),
                "size_mb": round(f.stat().st_size / 1_048_576, 2),
            }
    if mp4_files:
        f = mp4_files[0]
        return {
            "exists": True,
            "path": str(f),
            "size_mb": round(f.stat().st_size / 1_048_576, 2),
        }
    return {"exists": False}


def main():
    if len(sys.argv) < 2:
        print("Usage: monitor_video_gen.py <post-folder>")
        sys.exit(2)

    post_dir = sys.argv[1]
    post_path = Path(post_dir).resolve()
    if not post_path.is_dir():
        print(f"ERROR: Post folder not found: {post_dir}")
        sys.exit(2)

    # Check output file first (process may have finished)
    output = check_output_file(post_dir)
    if output["exists"]:
        print(f"COMPLETED: {output['path']} ({output['size_mb']} MB)")
        sys.exit(0)

    # Find the running process
    procs = find_video_process(post_dir)
    if not procs:
        print("NO_PROCESS: No wgp.py running for this post folder")
        result = subprocess.run(
            ["ps", "aux"], capture_output=True, text=True
        )
        has_any_wgp = any("wgp.py" in line and "grep" not in line
                          for line in result.stdout.split("\n"))
        if has_any_wgp:
            print("NOTE: A wgp.py is running but not matching this post folder.")
        sys.exit(1)

    proc = procs[0]
    pid = proc["pid"]
    elapsed_min = proc["elapsed_minutes"]

    # Check if process is alive
    alive = True
    try:
        os.kill(pid, 0)
    except OSError:
        alive = False

    if not alive:
        print(f"PROCESS_DEAD: PID {pid} is no longer alive")
        print(f"Elapsed: {elapsed_min} minutes")
        sys.exit(2)

    # Check GPU for stall detection
    gpu = check_gpu_usage()
    stall_risk = False
    if proc["cpu"] < 1.0 and gpu["ok"]:
        gpus = gpu.get("gpus", [])
        if gpus:
            total_used = sum(g["used_mb"] for g in gpus)
            stall_risk = True

    # Print clear status with elapsed minutes (no agent timing needed)
    status = "STALLED" if stall_risk else "RUNNING"
    print(f"{status}: PID {pid} running for {elapsed_min} minutes")
    print(f"GPU: {gpu}")

    if stall_risk:
        print("WARNING: Process appears stalled (CPU idle but GPU still occupied).")

    # Always show the 10-minute threshold context
    if elapsed_min >= 10:
        print("ALERT: Job has exceeded 10 minutes (normal: 3-6 min). Ask user if they want to wait or cancel.")
    elif elapsed_min >= 8:
        print("NOTE: Job approaching 10-minute threshold (normal: 3-6 min).")

    sys.exit(1)


if __name__ == "__main__":
    import os
    main()
