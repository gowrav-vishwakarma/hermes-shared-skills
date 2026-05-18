---
name: wan2gp-video-generation
description: LTX-2.3 video generation via WanGP -- director-style prompting, audio direction, I2V coherence
category: media
---

# WanGP Video Generation (LTX-2.3)

Generate videos with native audio using **LTX-2.3 22B distilled** through WanGP CLI. Default is ~20 s (481 frames @ 24 fps) in a single pass. For longer videos, WanGP's **sliding window** mechanism generates multiple overlapping windows and stitches them.

Supports **text-to-video** (T2V) and **image-to-video** (I2V) -- the helper auto-picks from `--image-start`.

## ⚠️ CRITICAL: Use `generate_video_config.py --run` for Single Videos

**For a standalone video (single scene, any length), use the generator script with `--run`.** This is the only safe way:

```bash
python3 "$PROFILE_SKILLS/wan2gp-video-generation/scripts/generate_video_config.py" \
    --prompt "Your cinematic prompt here..." \
    --output-filename shot_name \
    --output-dir /path/to/post/folder \
    --aspect 9:16 \
    --seed 42 \
    --run
```

The `--run` flag: generates the config JSON **AND** executes `wgp.py --process` automatically. Single command, zero manual config.

**NEVER:**
- Write the JSON config manually — 50+ fields, easy to get wrong (missing `model_type`, wrong `image_mode`, legacy `start_image` field, etc.).
- Reach for the movie pipeline for a single video — use `video-create-workflow` or direct generation instead.
- Run `generate_video_config.py` in background AND `wgp.py` in foreground — `--run` does both.

**First-run cold start:** TorchInductor compilation takes 5-15 min on first run with ZERO visible GPU output. This is normal. Subsequent runs skip compilation (~3:30).

## ⚠️ CRITICAL: WanGP Setup Verification Pitfall

**Never assume WanGP is available before running video generation.** The `$WAN_APP_DIR` environment variable may be:
- Empty (unconfigured)
- Set to non-existent path
- Set but WanGP not installed

**Always verify before use:**
```bash
echo "$WAN_APP_DIR"
ls "$WAN_APP_DIR/wgp.py"
```

If WanGP is unavailable, fall back to **manim** for standalone 20s videos.

## Generation Time Benchmarks

**RTX 4090 (24GB VRAM), LTX-2.3 distilled-1.1, 1280x720:**

| Scenario | First Run | Subsequent Runs |
|----------|-----------|-----------------|
| Standalone T2V (no LoRA) | ~3:37 | ~3:30 |
| T2V with LoRA | ~3:45 | ~3:38 |
| I2V with anchor | ~3:35 | ~3:30 |
| Extended video (30s, 2 windows) | ~7:15 | ~7:05 |

**Why first run is slower:** TorchInductor kernel compilation happens on first run (5-15 min CPU-bound phase, NO GPU usage, NO output). After compilation, kernels are cached in `~cache/torch_inductor/` and subsequent runs skip this phase.

**Mitigation:** Set `TORCHINDUCTOR_FORCE_DISABLE=1` to skip compilation (faster start but slower per-step inference).

## ⚠️ CRITICAL: WanGP Video Generation — Foreground Only

**You MUST run `wgp.py` in foreground mode (via terminal with `workdir`).** The background wrapper uses the system `python3` (no `torch`), which fails every time.

**Correct invocation:**
```bash
terminal(
    command="$WAN_PYTHON wgp.py --process $CONFIG --output-dir $OUTDIR --compile --attention sage2 --profile 4 --fp16",
    workdir=$WAN_APP_DIR,
    timeout=600
)
```

**What to say when launching:** *"Video generation started. It'll take ~3-5 min. I'll check on it."* Then monitor with `process(action='log')`.

### ⚠️ CONTRADICTION ALERT: Old documentation says "background mode"

Older versions of this skill documented using `terminal(background=true)`. That was **wrong** — it never worked for `wgp.py` because the background wrapper overrides the Python interpreter. The `cli-usage-pitfalls.md` reference has the authoritative fix. Always use foreground + `workdir`.

### Background mode for config generation only

`generate_video_config.py` (config builder, not video generation) IS fast and safe for background mode. Only `wgp.py` itself must be foreground.

### Semicolons in `--loras-multipliers`

The shell splits `;` as a command separator. Unquoted `--loras-multipliers 0.5;1.5` becomes two commands: `--loras-multipliers 0.5` and `1.5`.

**Fix:** Always double-quote multipliers:

```bash
--loras-multipliers "0.5;1.5"
```

### Loras multipliers format (CRITICAL)

`loras_multipliers` MUST be semicolon-separated **numbers only**, matching the order of `activated_loras` in the config.

**WRONG (keyword=weight syntax fails):**
```json
"loras_multipliers": "CrispEnhance=0.5 VBVR=1.5"
```
Error: `Lora Multiplier no 1 (CrispEnhance=0.5) is invalid for task #1. Skipping.`

**CORRECT (semicolon-separated numbers matching array order):**
```json
"activated_loras": ["LTX2.3_Crisp_Enhance.safetensors", "Ltx2.3-Licon-VBVR-I2V-96000-R32.safetensors"],
"loras_multipliers": "0.5;1.5"
```

**Python subprocess:** `str(args.loras_multipliers)` produces `"0.5;1.5"` which is correct — no extra quoting needed in Python.

## `--process` vs `-c` vs `--config` (CRITICAL)

**`--process <file>`** is the ONLY flag that accepts a single JSON settings file.

**`-c <file>`** and **`--config <file>`** do NOT accept JSON files — they produce `unrecognized arguments` or take a folder path instead.

```bash
# CORRECT — single JSON settings file
$WAN_PYTHON wgp.py --fp16 --profile 4 --attention sage2 --process /path/to/video_generation.json

# WRONG — produces "unrecognized arguments: -c ..."
$WAN_PYTHON wgp.py -c /path/to/video_generation.json

# WRONG for files — --config takes a FOLDER, not a file
$WAN_PYTHON wgp.py --config /path/to/video_generation.json
```

**Rule:** When using `--process`, do NOT pass individual CLI args alongside it. All params must come from the JSON config.

## `wgp.py has no execute permission (CRITICAL)
```python
import os
env = os.environ.copy()  # ALWAYS start from os.environ to preserve PATH, SHELL, HOME
with open('$PROFILE_ROOT/.env') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            env[k.strip()] = v.strip()
```

**CRITICAL: Never build env from scratch.** If you do `env = {...}`, you'll lose PATH, SHELL, HOME and the subprocess will fail.

- [`references/t2v-standalone-narrative.md`](references/t2v-standalone-narrative.md) - Text-to-video workflow for standalone narrative scenes without character references
- [`references/copy-trend-workflow.md`](references/copy-trend-workflow.md) - Trend copy via `copy_trend.py` with audio extraction, OVG pose transfer, and common pitfalls

## Script: copy_trend.py

The `scripts/copy_trend.py` helper orchestrates the full trend-copy pipeline: download → re-encode → config → launch.

**Usage:**
```bash
python3 copy_trend.py \
    --url "https://www.instagram.com/p/XXXXX/" \
    --character-image "/path/to/character.png" \
    --prompt "Describe character performing the trend..." \
    --output-dir "/path/to/post/folder" \
    --output-filename trend_copy \
    --mode OVG \
    --no-loras
```

**CRITICAL BUG:** `copy_trend.py` does NOT accept `--audio-from-control-video` and does NOT set `audio_prompt_type: "K"` internally. **You must manually add `c["audio_prompt_type"] = "K"` to the generated config** after running copy_trend.py, or the output video will be silent. See [`references/copy-trend-workflow.md`](references/copy-trend-workflow.md) for the full fix.
- `references/wan-app-dir-discovery.md` - How to discover WanGP path when $WAN_APP_DIR is empty
- `references/fallback-video-workflows.md` - Use manim for standalone 20s videos when WanGP unavailable
- `references/dialogue-video-workflow.md` - Proper structure for videos with spoken dialogue
- `references/sliding-window-output-files.md` - Critical: LAST file (N).mp4 contains the COMPLETE stitched video
- `references/post-gen-compression.md` - Always compress WanGP output before Telegram delivery (18-56 MB → 2-8 MB via ffmpeg CRF 23)
- `references/generator-vs-direct-workflow.md` - Trust generator scripts, don't manually edit configs
- `references/cli-usage-pitfalls.md` - Never run WanGP CLI directly, use generator script
