# CLI Processing Flag

## Running a JSON config file

**Correct flag: `--process` (double dash)**

```bash
cd /home/gowrav/pinokio/api/wan.git/app && WAN_APP_DIR=/home/gowrav/pinokio/api/wan.git/app /home/gowrav/pinokio/api/wan.git/app/env/bin/python wgp.py --fp16 --profile 4 --attention sage2 --process /path/to/video_generation.json
```

## WRONG flags (they don't work for single JSON files)

- `-c <file>` → error: unrecognized arguments
- `--config <file>` → error: unrecognized arguments (this takes a **folder**, not a file)

## Flag summary

| Flag | Argument type | Purpose |
|------|--------------|---------|
| `--process` | Single `.json` file | Process one settings config |
| `--config` | Folder path | Config folder containing wgp_config.json |
| `--settings` | Folder path | Settings folder |

## Full command template

```bash
cd $WAN_APP_DIR && WAN_APP_DIR=$WAN_APP_DIR $WAN_PYTHON wgp.py \
  --fp16 --profile 4 --attention sage2 \
  --process /path/to/video_generation.json
```

Do NOT pass individual CLI args alongside `--process` — all params come from the JSON config.
