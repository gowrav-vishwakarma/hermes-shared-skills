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
import re
import sys
from pathlib import Path

_PHANTOM_RE = re.compile(r"/profiles/[^/]+/home/\.hermes/")


def _real_user_home() -> Path:
    override = os.environ.get("HERMES_REAL_HOME", "").strip()
    if override:
        return Path(override)
    try:
        import pwd

        return Path(pwd.getpwuid(os.getuid()).pw_dir)
    except (ImportError, KeyError):
        user = os.environ.get("USER") or os.environ.get("LOGNAME") or ""
        if user:
            return Path("/home") / user
        return Path.home()


def _check_phantom(resolved: Path) -> None:
    s = str(resolved).replace("\\", "/")
    if _PHANTOM_RE.search(s):
        sys.exit(
            f"[env] phantom path detected: {resolved}\n"
            "Inside Hermes, ~ and $HOME map to $PROFILE_HOME, not /home/<user>.\n"
            "Use $PROFILE_ROOT, $POSTS_DIR, or the path printed by new_post.py — "
            "not ~/.hermes/profiles/... or $PROFILE_ROOT/cron/output/ for reels.\n"
            "See: video-create-workflow/references/hermes-path-pitfall.md"
        )


def resolve_path(raw: str) -> Path:
    """Expand paths safely when Hermes sets HOME=$PROFILE_HOME."""
    raw = raw.strip()
    if not raw:
        sys.exit("[env] empty path")
    if raw == "~":
        return _real_user_home().resolve()
    if raw.startswith("~/") or raw.startswith("~/.hermes"):
        resolved = (_real_user_home() / raw[2:]).resolve()
        _check_phantom(resolved)
        return resolved
    resolved = Path(raw).expanduser().resolve()
    _check_phantom(resolved)
    return resolved


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


__all__ = ["required", "optional", "resolve_path"]
