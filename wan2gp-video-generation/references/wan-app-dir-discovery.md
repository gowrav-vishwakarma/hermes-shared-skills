# WAN_APP_DIR Discovery

## Environment Variable Issue

`$WAN_APP_DIR` may be empty in new sessions. The WanGP app path is:
`/home/gowrav/pinokio/api/wan.git/app`

**When empty, discover it with:**
```bash
find /home/gowrav -name "wgp.py" 2>/dev/null | head -5
```

The path is typically under `$HOME/pinokio/api/wan.git/app/wgp.py`.

## Always verify before use

```bash
ls "$WAN_APP_DIR/env/bin/python" "$WAN_APP_DIR/wgp.py"
```

If they don't exist, the variable isn't set — search for `wgp.py` and set `WAN_APP_DIR` explicitly.