# Orphan Process GPU Hang — Case Study (May 3, 2026)

## What happened

During the fantasy reel generation session, Batch 2 was mid-execution (generating `location_training_grounds`, `location_fairy_garden`, `location_shadow_forest`) when the session was terminated. Background `wgp.py` GPU processes were left orphaned.

## Symptoms

1. **System became completely unresponsive** — no terminal sessions, no SSH, no response to input
2. **No graceful shutdown** — the system was force-rebooted on May 4 at 10:08 AM
3. **Zero journal logs** between May 3 01:50:06 and May 4 10:08 AM (~32.5 hours)
4. **No kernel panic, OOM killer, or segfault** in `journalctl -b -1`
5. **`dmesg` empty** — no boot messages recorded
6. **Normal system logs** ending abruptly at May 3 01:50:06 (CRON jobs)

## Root cause analysis

The orphaned `wgp.py` process entered a hung state in the NVIDIA driver:

1. **Orphaned GPU process:** `wgp.py` was running with `--compile --attention sage2 --profile 4 --fp16` when the session ended
2. **Driver deadlock:** The process entered `D` state (uninterruptible sleep) — stuck in I/O with the GPU driver
3. **System-wide impact:** When a GPU process hangs in `D` state, the NVIDIA driver itself becomes unresponsive. This blocks:
   - Any new process trying to access the GPU
   - System calls involving the driver
   - In severe cases, the entire kernel
4. **Cannot be killed:** Processes in `D` state cannot receive signals — `kill -9` has no effect
5. **No OOM trigger:** The OOM killer didn't fire because `D`-state processes don't consume swappable memory — they hold hardware resources

## Why no crash logs?

This is a **hardware-level deadlock**, not a software crash:
- The NVIDIA kernel module entered a deadlocked state
- No kernel panic was triggered because the driver didn't "crash" — it just stopped responding
- No OOM killer because memory wasn't exhausted
- No log flushing because the kernel couldn't write to disk while stuck

## Recovery

Hard reboot (force power cycle) was the ONLY option:
1. Cut power / hard reset
2. Boot completes normally
3. System is responsive again

## Prevention checklist

Before starting ANY new WanGP job (image or video):

```bash
# 1. Check for orphaned wgp.py processes
ps aux | grep "wgp.py" | grep -v grep

# 2. If found, try graceful kill first
kill -15 <pid>
sleep 5
ps aux | grep "wgp.py" | grep -v grep

# 3. If still running, force kill
kill -9 <pid>

# 4. Verify GPU driver is responsive
nvidia-smi
# If this hangs or errors, the GPU is still deadlocked — REBOOT REQUIRED
```

## Diagnostic pattern for future crashes

If system hangs again, check after reboot:
```bash
# Look for abrupt log cutoff (no shutdown sequence)
journalctl -b -1 --since "2026-05-03 00:00" | tail -5

# Check for D-state processes before crash (if we can capture it)
ps aux | awk '$8 ~ /D/ {print}'

# Check nvidia-smi responsiveness
timeout 5 nvidia-smi || echo "GPU driver deadlocked"
```

## Key takeaway

**GPU processes in `D` state are the silent system-killer.** They produce no error messages, trigger no logs, and cannot be killed. Prevention through pre-flight orphan checks is the only defense.
