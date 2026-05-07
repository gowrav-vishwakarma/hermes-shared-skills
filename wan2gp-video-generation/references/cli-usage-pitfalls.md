# `generate_video_config.py` CLI Usage Pitfalls

Session-specific notes for using the WanGP video config builder correctly.

## Correct flags

- **`--prompt`** — the LTX-2.3 cinematic/text prompt. NOT `--video-prompt` (which is not a real flag).
- **`--video-prompt-type`** — only accepts `PVG`, `OVG`, `DVG`, `EVG`, `VG`, `KFI`. These are **control video modes**. Only meaningful when `--video-guide` is also set. For plain I2V or T2V, **omit this flag entirely**.

## Shell quoting pitfalls

### Long prompts with apostrophes

Prompts containing `'` (e.g., `don't`, `we'll`, `doesn't`) will break shell single-quote escaping with `'...'\''...'` patterns. The parser consumes subsequent flags as the prompt value, producing errors like:

```
generate_video_config.py: error: argument --video-prompt-type: invalid choice: 'EXT. GARDEN -- DAY...' (choose from 'PVG', 'OVG', ...)
```

**Fix:** Write the prompt to a `.txt` file in the post directory, then read it:

```bash
# Write prompt to file
echo 'Girl says "don'\''t worry..." Boy laughs.' > "$POSTS_DIR/.../video_prompt.txt"

# Read it back via command substitution
python3 "$PROFILE_SKILLS/wan2gp-video-generation/scripts/generate_video_config.py" \
    --image-start "$POSTS_DIR/.../anchor.jpg" \
    --prompt "$(cat "$POSTS_DIR/.../video_prompt.txt")" \
    --output-filename my_reel \
    --output-dir "$POSTS_DIR/..." \
    --run
```

Command substitution (`$(cat ...)`) handles all quoting internally.

### Semicolons in `--loras-multipliers`

The shell splits `;` as a command separator. Unquoted `--loras-multipliers 0.5;1.5` becomes two commands: `--loras-multipliers 0.5` and `1.5`.

**Fix:** Always double-quote multipliers:

```bash
--loras-multipliers "0.5;1.5"
```

## `wgp.py` has no execute permission (CRITICAL)

`wgp.py` is **not executable** — no `chmod +x` applied. Running it as `wgp.py --process ...` or `./wgp.py` fails with:

```
bash: /home/gowrav/pinokio/api/wan.git/app/wgp.py: Permission denied
```

**Fix:** Always run through the virtual environment Python interpreter:

```bash
/home/gowrav/pinokio/api/wan.git/app/env/bin/python3 /home/gowrav/pinokio/api/wan.git/app/wgp.py --process "..."
```

Or using env vars:
```bash
$WAN_PYTHON wgp.py --process "..."
```

**When this hits:** Any time you manually launch `wgp.py --process` from a terminal or background process. (Config builder scripts that invoke it internally may already handle this.)

## `wgp.py --process` cwd requirement (CRITICAL)

`wgp.py` resolves `models/_settings.json` and other internal paths **relative to the current working directory**, NOT relative to the config file path passed via `--process`. If run from an arbitrary directory (e.g., the post folder), it fails with:

```
FileNotFoundError: [Errno 2] No such file or directory: 'models/_settings.json'
```

**Fix:** Always `cd $WAN_APP_DIR` before running `wgp.py --process`:

```bash
set -a; source $PROFILE_ROOT/.env; set +a

cd $WAN_APP_DIR
$WAN_PYTHON wgp.py --process "$POSTS_DIR/.../video_generation.json" \
    --output-dir "$POSTS_DIR/.../"
```

This also applies when running `wgp.py` directly (not via generate_video_config.py). If you use a terminal background process, make sure the working directory is set to WAN_APP_DIR, not the post directory.

## Quick reference command (multi-character dialogue reel)

```bash
set -a; source $PROFILE_ROOT/.env; set +a

# Step 1: Write prompt to file (avoids quoting hell)
cat > "$POSTS_DIR/2026-05-06_X/video_prompt.txt" << 'HEREDOC'
Girl looks at camera and says "okay.. wait.. so we got our Instagram account now..."
She tilts her head, hands in hoodie pockets. Boy adjusts his glasses, looks at her.
He says "yep, we are not real characters..."
HEREDOC

# Step 2: Generate video config
python3 "$PROFILE_SKILLS/wan2gp-video-generation/scripts/generate_video_config.py" \
    --image-start "$POSTS_DIR/2026-05-06_X/anchor.jpg" \
    --prompt "$(cat "$POSTS_DIR/2026-05-06_X/video_prompt.txt")" \
    --sliding-window-size 481 \
    --video-length 721 \
    --seed 742981 \
    --aspect 9:16 \
    --steps 25 \
    --guidance-scale 3.5 \
    --output-filename my_reel \
    --output-dir "$POSTS_DIR/2026-05-06_X" \
    --activated-loras LTX2.3_Crisp_Enhance.safetensors Pixar_Toon.safetensors \
    --loras-multipliers "0.5;1.5" \
    --run
```

Key: `<< 'HEREDOC'` (quoted heredoc delimiter) means NO shell expansion inside — safe for any apostrophes or special chars.