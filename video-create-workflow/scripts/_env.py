"""_env.py -- strict env-var helpers for the video-create-workflow scripts.

Stdlib-only. All helpers in this skill funnel through ``required(...)`` so
that missing env vars fail loudly with a clear recovery hint instead of
silently falling back to ``Path.home() / ...`` (which inside Hermes maps to
the active profile home and silently lands on the wrong files).

Source the canonical values from ``$PROFILE_ROOT/.env``::

    set -a; source $PROFILE_ROOT/.env; set +a
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def required(name: str) -> Path:
    """Return ``Path(os.environ[name])``; exit with a clear message if unset."""
    val = os.environ.get(name)
    if not val:
        sys.exit(
            f"[env] required env var {name!r} is not set. "
            f"Source $PROFILE_ROOT/.env (or export {name}=...) and retry. "
            f"Recovery: `set -a; source $PROFILE_ROOT/.env; set +a`."
        )
    return Path(val)


def optional(name: str, default: str | None = None) -> Path | None:
    val = os.environ.get(name)
    if val:
        return Path(val)
    if default is None:
        return None
    return Path(default)


__all__ = ["required", "optional"]
