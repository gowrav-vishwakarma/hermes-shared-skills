# WanGP Environment Verification

## Quick Check

Before running any `wgp.py` commands, verify the WanGP virtual environment:

```bash
cd "$WAN_APP_DIR"
./env/bin/python -c "import torch; print('Torch:', torch.__version__)"
```

**Expected output**: Torch version number (e.g., `2.5.1`)

**Failure modes**:
- `ModuleNotFoundError: No module named 'torch'` → Wrong Python interpreter! Use `./env/bin/python`
- `Permission denied` → Run `chmod +x env/bin/python` or use full path
- `No such file or directory` → Not in WanGP app directory

## Common Mistake Patterns

### ❌ Wrong: Using system Python
```bash
python3 wgp.py --process settings.json  # FAILS
python wgp.py --process settings.json   # FAILS
```

### ✅ Correct: Using WanGP venv
```bash
cd "$WAN_APP_DIR"
./env/bin/python wgp.py --process settings.json  # WORKS
```

### ✅ Alternative: Activate venv first
```bash
cd "$WAN_APP_DIR"
source env/bin/activate
python wgp.py --process settings.json  # WORKS
```

## Why This Matters

WanGP depends on PyTorch and other heavy libraries that are **not** installed in the system Python. Using the wrong interpreter causes immediate `ModuleNotFoundError` failures that waste time debugging.

## Verification Script

Use the helper script for comprehensive checks:

```bash
./scripts/verify_wan_env.py
```

This checks:
1. WanGP Python interpreter exists
2. WanGP app directory is correct
3. PyTorch imports successfully in the venv

## Debugging Checklist

If `./env/bin/python wgp.py` still fails:

1. **Confirm directory**: `pwd` should show the WanGP app directory (`$WAN_APP_DIR`)
2. **Check Python**: `./env/bin/python --version`
3. **Check torch**: `./env/bin/python -c "import torch; print(torch.__version__)"`
4. **Check wgp.py**: `ls -la wgp.py` (should exist)
5. **Kill orphaned processes**: `ps aux | grep wgp.py` then `kill -9 <pid>` for any stuck processes

## Related Skills

- `wan2gp-image-generation` → WanGP Python section
- `wan2gp-video-generation` → Complete Video Generation Workflow section
