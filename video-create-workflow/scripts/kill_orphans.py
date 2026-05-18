#!/usr/bin/env python3
"""kill_orphans.py -- terminate stray wgp.py processes.

Lists all running ``wgp.py`` processes. Sends SIGTERM, waits ``--grace``
seconds, then SIGKILL anything still alive. If a process is in D-state
(uninterruptible sleep) after SIGKILL the GPU driver is deadlocked --
the script logs the warning and exits non-zero (only a reboot recovers).

Usage::

    python3 kill_orphans.py                # kill all wgp.py procs
    python3 kill_orphans.py --dry-run      # list only, do not signal
    python3 kill_orphans.py --grace 10     # custom grace period

Stdlib only.
"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def _wgp_pids() -> list[int]:
    try:
        out = subprocess.check_output(["pgrep", "-af", "wgp.py"], text=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return []
    pids: list[int] = []
    for line in out.splitlines():
        parts = line.strip().split(maxsplit=1)
        if parts and parts[0].isdigit():
            pids.append(int(parts[0]))
    return pids


def _proc_state(pid: int) -> str | None:
    try:
        with Path(f"/proc/{pid}/status").open() as fh:
            for line in fh:
                if line.startswith("State:"):
                    return line.split()[1]
    except OSError:
        return None
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="List only.")
    ap.add_argument("--grace", type=float, default=5.0,
                    help="Seconds to wait after SIGTERM before SIGKILL.")
    args = ap.parse_args()

    pids = _wgp_pids()
    if not pids:
        print("[kill_orphans] no wgp.py processes.", file=sys.stderr)
        return 0

    for pid in pids:
        st = _proc_state(pid)
        print(f"  pid={pid} state={st}")

    if args.dry_run:
        return 0

    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"[kill_orphans] SIGTERM pid={pid}", file=sys.stderr)
        except ProcessLookupError:
            pass

    time.sleep(args.grace)

    alive = _wgp_pids()
    if alive:
        for pid in alive:
            try:
                os.kill(pid, signal.SIGKILL)
                print(f"[kill_orphans] SIGKILL pid={pid}", file=sys.stderr)
            except ProcessLookupError:
                pass
        time.sleep(1)

    final = _wgp_pids()
    rc = 0
    for pid in final:
        st = _proc_state(pid)
        if st == "D":
            print(f"[kill_orphans] WARNING: pid={pid} in D-state -- "
                  f"GPU driver may be deadlocked. Reboot likely required.",
                  file=sys.stderr)
        else:
            print(f"[kill_orphans] WARNING: pid={pid} still alive (state={st}).",
                  file=sys.stderr)
        rc = 1
    if rc == 0:
        print(f"[kill_orphans] cleaned {len(pids)} process(es).", file=sys.stderr)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
