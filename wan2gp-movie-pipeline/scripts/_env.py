"""_env.py -- strict env-var helpers for the WanGP / asset-library scripts.

Stdlib-only. All helpers in this skill (and the movie-pipeline scripts that
import from here) call `required("WAN_APP_DIR")` instead of falling back to
`Path.home() / "pinokio" / ...`. Hermes maps `$HOME` to the active profile
home, so `~`-based defaults silently land on the wrong assets / wgp.py
location -- this module forces a clear failure message instead.

Source the canonical values from `<PROFILE_ROOT>/.env`.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def required(name: str) -> Path:
    """Return `Path(os.environ[name])`, exiting with a clear message if unset.

    The message tells the caller exactly which env var is missing and how to
    recover (source the profile .env). All scripts that depend on the asset
    library / WanGP install funnel through this helper so the diagnostic is
    consistent.
    """
    val = os.environ.get(name)
    if not val:
        sys.exit(
            f"[env] required env var {name!r} is not set. "
            f"Source $PROFILE_ROOT/.env (or export {name}=...) and retry. "
            f"Recovery: `set -a; source $PROFILE_ROOT/.env; set +a`."
        )
    return Path(val)


def optional(name: str, default: str | None = None) -> Path | None:
    """Return `Path(os.environ[name])` if set, else `Path(default)` or None."""
    val = os.environ.get(name)
    if val:
        return Path(val)
    if default is None:
        return None
    return Path(default)


__all__ = ["required", "optional"]
