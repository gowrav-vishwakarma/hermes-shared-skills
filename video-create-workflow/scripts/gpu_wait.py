#!/usr/bin/env python3
"""gpu_wait.py -- block until no wgp.py is running (and GPU is idle).

Polls every ``--interval`` seconds until either:
  * no ``wgp.py`` process is running (exit 0), or
  * ``--timeout`` seconds elapse (exit 124).

If ``nvidia-smi`` is on PATH, also waits until GPU memory used drops below
``--mem-threshold-mb`` (default 2000). Without ``nvidia-smi`` the script
only checks the process list.

Usage::

    python3 gpu_wait.py
    python3 gpu_wait.py --timeout 1800 --interval 15
    python3 gpu_wait.py --quiet

Stdlib only.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time


def _wgp_pids() -> list[int]:
    try:
        out = subprocess.check_output(["pgrep", "-f", "wgp.py"], text=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return []
    pids: list[int] = []
    for line in out.splitlines():
        line = line.strip()
        if line.isdigit():
            pids.append(int(line))
    return pids


def _gpu_mem_used_mb() -> int | None:
    if not shutil.which("nvidia-smi"):
        return None
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            text=True, timeout=10,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
    totals = [int(x.strip()) for x in out.splitlines() if x.strip().isdigit()]
    return max(totals) if totals else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--timeout", type=float, default=600.0,
                    help="Seconds before giving up (default 600).")
    ap.add_argument("--interval", type=float, default=10.0,
                    help="Seconds between checks (default 10).")
    ap.add_argument("--mem-threshold-mb", type=int, default=2000,
                    help="GPU mem (MB) considered idle (default 2000).")
    ap.add_argument("--quiet", action="store_true", help="Suppress progress logs.")
    args = ap.parse_args()

    start = time.time()
    while True:
        pids = _wgp_pids()
        mem = _gpu_mem_used_mb()
        idle = (not pids) and (mem is None or mem < args.mem_threshold_mb)
        if idle:
            if not args.quiet:
                print(f"[gpu_wait] idle after {time.time() - start:.0f}s "
                      f"(mem={mem} MB pids={pids})", file=sys.stderr)
            return 0
        elapsed = time.time() - start
        if elapsed > args.timeout:
            print(f"[gpu_wait] TIMEOUT after {elapsed:.0f}s "
                  f"(pids={pids} mem={mem} MB)", file=sys.stderr)
            return 124
        if not args.quiet:
            print(f"[gpu_wait] waiting... pids={pids} mem={mem} MB "
                  f"elapsed={elapsed:.0f}s/{args.timeout:.0f}s", file=sys.stderr)
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
