# .env PATH Overwrite Pitfall

## Problem
When building a subprocess environment by iterating `$PROFILE_ROOT/.env` and merging ALL key=value pairs into `env = {}`, the env file's values can overwrite critical system variables like `PATH`. This causes crashes like:
```
KeyError: 'PATH'
```

## Why it happens
The `.env` file (e.g., `~/.hermes/profiles/gvs/.env`) contains WAN-specific variables. When you do:
```python
env = {}
with open('.env') as f:
    for line in f:
        k, v = line.split('=', 1)
        env[k.strip()] = v.strip()
```
...you create a DICT-ONLY env with no system PATH, no SHELL, no HOME, etc. Python's `os.environ` is not involved.

## Fix
Start from `os.environ.copy()` first, THEN selectively add WAN-specific vars:
```python
import os
env = os.environ.copy()  # preserves PATH, SHELL, HOME, etc.
with open('.env') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            env[k.strip()] = v.strip()
```
OR be even more selective — only add WAN_ prefixed vars:
```python
env = os.environ.copy()
wan_vars = {k: v for k, v in env_vars.items() if k.startswith('WAN_')}
env.update(wan_vars)
```

## Session evidence
- Session 2026-05-07 chipmunk_hug v2 generation: first attempt failed with `KeyError: 'PATH'` from pydub trying to read env vars.
- Fix: switched from `env = env_vars.copy()` to `env = os.environ.copy()` before merging WAN vars.
- Second attempt succeeded.
