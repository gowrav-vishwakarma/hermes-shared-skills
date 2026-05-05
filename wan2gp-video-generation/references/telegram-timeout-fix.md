# Telegram Timeout Problem — Diagnosis & Fix

## The Problem

LTX-2.3 I2V video generation takes 3-4 minutes (8-step first pass + 3-step second pass).
When running from Telegram, the Hermes agent turn timeout (~180-300s) can fire mid-generation.

**Old pattern (`--run`):** `generate_video_config.py --run` calls `subprocess.call()` which blocks
the terminal call for the full duration. When the Telegram agent turn times out:
- The terminal session (and subprocess.call blocking) gets killed
- The GPU process (wgp.py) keeps running on the VM (it's a separate process)
- The agent loses track of the PID
- On the next turn, the agent thinks it timed out, can't find output, may try to re-run (OOM risk)

## Evidence from Session (2026-05-02, post #6)

### What we found

**Process tree before fix:**
```
PID 223355 (session 223355, TTY ?) — generate_video_config.py --run (BLOCKING parent)
  └── PID 223364 (session 223355, TTY ?) — wgp.py --process video_generation.json (GPU crunching)
       └── 32 torch compile_worker children
```

Both had `?` TTY (no terminal attached) — they were running in a background Hermes terminal session.
The parent (223355) was blocked in subprocess.call() waiting for child (223364) to finish.

**Output file appeared mid-generation:**
- `character_office_motivational_reel.mp4` — 28.4 MB, 704x1280 portrait, 20s, h264+AAC
- Created at 19:02, parent process had been running 105s
- GPU still at ~60%, PID 223364 still crunching at that point

### Timeline

1. ~18:50 — Agent writes video_generation.json via generate_video_config.py
2. ~18:50 — Agent calls --run which spawns wgp.py (PID 223364)
3. ~19:02 — Output MP4 written to disk (first pass done, before second pass cleanup)
4. ~19:06 — Agent turn times out (if it was running then)
5. ~19:06+ — GPU process keeps running in background session 223355
6. ~19:08 — GPU still at ~60%, 105s elapsed (expected ~3-4 min total)

### Key observations

1. **Output file can appear before process fully finishes.** The MP4 was written at 19:02 but
   the GPU process was still active. The monitor script checks output file FIRST before checking
   process liveness — this catches "job done but process hasn't cleaned up yet" cases.

2. **Background sessions survive agent timeout.** The parent (PID 223355) was in session 223355
   with no TTY. If the Telegram agent turn times out, the Hermes terminal gets killed but
   the background session and its subprocesses keep running.

3. **No PID tracker was written.** The agent didn't write to `.video_gen_tracker.json`, so
   the next turn had no way to find and monitor the running process.

## The Fix (split workflow)

### Step A: Config write (2s, zero timeout risk)
```bash
python3 generate_video_config.py --prompt "..." --image-start ... --output-dir ... --aspect 9:16
# NO --run flag. Just writes video_generation.json
```

### Step B: Background execution (survives agent timeout)
```bash
"$WAN_APP_DIR"/env/bin/python wgp.py \
    --process video_generation.json \
    --output-dir /path/to/post \
    --compile --attention sage2 --profile 4 --fp16
```
Run via `terminal(background=true, notify_on_complete=true)`. Separate VM process, survives timeout.

### Step C: Write PID tracker
```bash
echo '{"post": "SLUG", "pid": PID, "session_id": "SID", "status": "running"}' \
    > <profile-home>/.video_gen_tracker.json
```

### Step D: Poll every 60-90s
```bash
python3 monitor_video_gen.py <post-folder>
# Exit 0 + "COMPLETED" = done
# Exit 1 + "RUNNING" = still going
# Exit 1 + "STALL_RISK" = GPU idle, may be stuck
# Exit 2 + "PROCESS_DEAD" = crashed
```

Each poll takes <5s. Never hits agent turn timeout.

## Why `--run` is dangerous

`subprocess.call()` is a SYNC blocking call. The terminal session that invoked it blocks until
the subprocess finishes. If that terminal session is associated with a Telegram agent turn:

1. Agent turn timer (180-300s) fires
2. Hermes kills the terminal session
3. `subprocess.call()` raises SIGTERM on the blocking call
4. The GPU subprocess (wgp.py) may get SIGTERM too (depending on process group) OR
   survive if it's in a detached process group

**Best case:** GPU survives, keeps running, output file gets written. Agent just can't find it.
**Worst case:** GPU gets killed mid-pass. Partial output, wasted GPU time, agent retries = OOM.

The split approach guarantees the GPU subprocess runs independently of the agent turn lifecycle.
