# WAN_APP_DIR Discovery

## Python with torch is NOT system python3

The system `python3` (venv, conda-base) **lacks torch**. WanGP ships its own bundled Python at `$WAN_APP_DIR/env/bin/python`.

**Always use:** `$WAN_PYTHON` (pointing to `<WAN-APP>/env/bin/python`) — never `python3` or `sys.python`.

### Discovery recipe

When `python3 -c 'import torch'` fails:

```bash
# 1. Find the actual wgp.py
find ~ -path '*/wan*/app/wgp.py' 2>/dev/null | head -5

# 2. Verify bundled Python has torch
$WAN_PYTHON -c 'import torch; print(torch.__version__)'

# 3. Verify CUDA
$WAN_PYTHON -c 'import torch; print(f"CUDA: {torch.cuda.is_available()}, devices: {torch.cuda.device_count()}")'
```

If `$WAN_APP_DIR/env/bin/python` doesn't exist, the WanGP install may be under a different path (e.g., Pinokio wrappers at `~/pinokio/api/wan.git/`).

## Environment variables must be exported

`$PROFILE_ROOT/.env` is **not** auto-sourced by the agent. Run `set -a; source $PROFILE_ROOT/.env; set +a` before any WanGP command.

Required vars: `WAN_APP_DIR`, `WAN_PYTHON`, `PROFILE_HOME`, `PROFILE_SKILLS`.

## Always verify before use

```bash
ls "$WAN_APP_DIR/env/bin/python" "$WAN_APP_DIR/wgp.py"
```

If they don't exist, the variable isn't set — search for `wgp.py` and set `WAN_APP_DIR` explicitly.