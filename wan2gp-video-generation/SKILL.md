---
name: wan2gp-video-generation
description: LTX-2.3 22B video generation via WanGP. Director-style prompting, dual-frame keyframing, audio sync, tools. Default 481 frames @ 24 fps (~20 s); longer via sliding window.
category: media
---

# WanGP Video Generation (LTX-2.3)

Single tool: `scripts/generate_video_config.py`. T2V vs I2V is auto-picked from `--image-start`.

`$PROFILE_ROOT/.env` is **not** auto-sourced; run `set -a; source $PROFILE_ROOT/.env; set +a` first. Required env: `WAN_APP_DIR`, `WAN_PYTHON`, `PROFILE_HOME`, `PROFILE_SKILLS`.

## Script modes (mutually exclusive)

| Flag | Effect |
|------|--------|
| (no flag) or `--generate-only` | Build JSON, write `<output-dir>/video_generation.json`, exit. |
| `--generate-and-run` or `--run` | Build + run `wgp.py --process` via `$WAN_PYTHON` in `$WAN_APP_DIR`. |
| `--run-json PATH` | Skip build; run an existing JSON. Re-run `--generate-only` with corrected args first to overwrite the JSON, then `--run-json` it — no separate "fix" script needed. |

**CRITICAL — GPU runs MUST be launched in background with notify:**

`--generate-and-run` and `--run-json` block for 3-15 min (wgp.py holds the GPU). A new user message kills a blocking shell call. Always launch via:

```
terminal(
    command="python3 $PROFILE_SKILLS/wan2gp-video-generation/scripts/generate_video_config.py --generate-and-run ...",
    background=true,
    notify_on_complete=true
)
```

The system `python3` lacks torch — never invoke `wgp.py` outside `$WAN_PYTHON`. `workdir` for the terminal should be `$WAN_APP_DIR`.

## Anchor consistency (mandatory)

The anchor IS frame 0. Every character that should appear anywhere in the shot — start, middle, or end — MUST be visible in a single anchor image. LTX-2.3 invents new random faces for anyone not present in the anchor.

| Need | Use |
|------|-----|
| 1 character, single composition for the whole shot | `--image-start <anchor>` |
| Different opening and closing compositions (known start AND end frame) | `--image-start <start> --image-end <end>` (auto-adds `E` to `image_prompt_type`) |
| Intermediate keyframes at specific positions | `--image-start <a>` + `--image-refs <k1> <k2> ...` + `--frames-positions "120 240"` (auto-adds `F`, video_prompt_type=`KFI`) |
| 2-3 characters in the same shot | Build the anchor in `wan2gp-image-generation` with all of them composited, then I2V with that single anchor |
| Secondary characters who never appear in the anchor | See [`references/secondary-characters-from-text.md`](references/secondary-characters-from-text.md) — describe them only in the video prompt; their identity will NOT be locked |

For multi-frame keyframing details (dual-frame "SE" mode and beyond) see [`references/dual-frame-keyframing.md`](references/dual-frame-keyframing.md).

## LTX-2.3 prompt guide (compact)

**Anchor prompt ≠ video prompt.** The anchor (image) gets WHAT (static description); the video prompt gets HOW (motion, dialogue, audio). Never re-describe character / wardrobe / location detail in the video prompt — the model already sees it.

Video prompt rules:

1. **One opening tableau sentence** matching the anchor composition: `INT/EXT — TIME-OF-DAY. The character stands by the window, dupatta catching the light...`. After that, no more static description.
2. **Camera vocabulary**: dolly in/out, push-in, pull-back, pan, tilt, tracking, orbit, handheld shake. Pick one, name it. The model reacts to lens language.
3. **Action via verbs**: gestures, body language, expressions IN MOTION. Not "she wears a red kurti" (static) but "she tugs the dupatta tighter as her shoulders drop" (motion).
4. **Dialogue in "quotes"** with acting beats between lines: `"Hi doston..." (small pause, looks down, fidgets with the dupatta) "Han... main AI hun."`. The model speaks the quoted text and uses the beats as timing cues.
5. **Audio direction explicit**: ambient sound, music genre, voice tone/accent, background score. `Audio: gentle acoustic guitar, distant temple bells, warm teenage-girl voice.`
6. **Temporal connectors** glue moments: `as`, `then`, `while`, `before`, `after`. They are how the model paces.
7. **No hard cuts in per-post I2V**: never write `CUT TO`, `JUMP CUT`, `MEANWHILE` for single-shot reels — evolve the frame via camera moves. (`CUT TO:` IS used and required for `continue_from` scenes in `wan2gp-movie-pipeline` — different mechanism.)
8. **Duration cues** match `--video-length`. Default 481 frames ≈ 20 s @ 24 fps. For 30-40 s use sliding window (`--video-length 961 --sliding-window-size 481 --sliding-window-overlap 17`) and write a prompt that spans the whole duration. Each window generates independently — pure T2V across many windows produces disconnected output; always pair sliding window with `--image-start` or `--video-source`.
9. **Match aspect to context**: `--aspect 9:16` (720x1280) for reels, `--aspect 16:9` (1280x720) for landscape. The flag auto-picks the right template.
10. **Native audio**: LTX-2.3 generates audio directly from the prompt's dialogue + audio cues. For external audio sync use `--audio-guide FILE` (audio_prompt_type=`A`). For trend copy use `--video-guide FILE --video-prompt-type OVG --audio-from-control-video` (audio_prompt_type=`K`).

Deep dives: [`references/t2v-standalone-narrative.md`](references/t2v-standalone-narrative.md), [`references/dialogue-video-workflow.md`](references/dialogue-video-workflow.md), [`references/audio-conditioning-workflow.md`](references/audio-conditioning-workflow.md), [`references/meme-video-prompt-patterns.md`](references/meme-video-prompt-patterns.md), [`references/divine-deity-video-prompt-patterns.md`](references/divine-deity-video-prompt-patterns.md).

## Build flags (the ones agents need most)

| Flag | Purpose |
|------|---------|
| `--prompt "..."` | LTX-2.3 director-style prompt (rules above). Required unless `--run-json`. |
| `--output-filename NAME` / `--output-dir PATH` | Required (basename, no ext) and destination folder. |
| `--aspect 9:16 \| 16:9` | Sets resolution and picks T2V or I2V template. |
| `--seed N` | Reproducibility. Same seed across a movie keeps look. |
| `--model distilled-1.1 \| gguf` | Default `distilled-1.1` (8 steps, auto-LoRAs). `gguf` skips compile (~3 min). |
| `--image-start PATH` | Anchor frame 0; switches to I2V via `image_prompt_type='S'`. |
| `--image-end PATH` | End frame; auto-adds `E` (mode `SE`). |
| `--image-refs P [P ...]` + `--frames-positions "120 240"` | Intermediate keyframe injection (`KFI`). |
| `--video-source PATH` | Continue a previous video (`image_prompt_type='V'`). Mutually exclusive with `--image-start`. Used by movies. |
| `--video-guide PATH --video-prompt-type {PVG,OVG,DVG,EVG,VG}` | Control video for motion / pose / depth / edges transfer. `OVG` requires `--image-start`. |
| `--audio-guide PATH` | External audio conditioning (sets `audio_prompt_type='A'`). |
| `--audio-from-control-video` | Use the control video's own audio track (sets `K`); needs `--video-guide` with `V` in the prompt type. |
| `--video-length N` / `--sliding-window-size N` / `--sliding-window-overlap N` | Extended videos. Window default 481, max 501; overlap aligned to latent step (1, 9, 17, 25). |
| `--loras-multipliers "0.5;1.5"` | Semicolons only, numbers only, same order as `activated_loras`. Always double-quote in shell. |

Full arg list: `python3 generate_video_config.py --help`.

## Tools you will need

| Tool | Purpose |
|------|---------|
| `scripts/generate_video_config.py` | Build / build+run / run-only the WanGP config (above). |
| `scripts/monitor_video_gen.py <post-dir>` | Poll while wgp.py runs. Exit 0=completed, 1=running, 2=crashed. Prints elapsed minutes. |
| `scripts/copy_trend.py` | Download a trend video, re-encode, build OVG config, launch. See [`references/copy-trend-workflow.md`](references/copy-trend-workflow.md). Known bug: does not set `audio_prompt_type='K'` itself — use `generate_video_config.py --video-guide ... --audio-from-control-video` instead. |
| `video-create-workflow/scripts/compress_video.py` | ffmpeg compress raw mp4 (~30-40 MB) to Telegram-friendly (~3-5 MB). |
| `video-create-workflow/scripts/cleanup_windows.py` | Prune partial sliding-window mp4s; keep only the final `(N).mp4`. |
| `video-create-workflow/scripts/gpu_wait.py` / `kill_orphans.py` | GPU gating between consecutive runs. |
| ffmpeg (system) | Extract a last frame for movie continuity: `ffmpeg -y -i in.mp4 -sseof -0.5 -frames:v 1 last.jpg` (use `ffprobe` to compute duration first; `-sseof` is unreliable on some mp4s). |

## Sliding window output

When `video_length > sliding_window_size`, WanGP writes one mp4 per window: `name.mp4`, `name(2).mp4`, ... The **last** file (`(N).mp4`) is the complete stitched video; the earlier files are partials. **Do NOT `ffmpeg concat` them** — that doubles content. Compress only the last file. `cleanup_windows.py` does the pruning for you. See [`references/sliding-window-output-files.md`](references/sliding-window-output-files.md).

## Benchmarks (RTX 4090, distilled-1.1, 1280x720)

| Scenario | First run | Cached |
|----------|-----------|--------|
| Standalone T2V | ~3:37 | ~3:30 |
| I2V from anchor | ~3:35 | ~3:30 |
| 30 s extended (2 windows) | ~7:15 | ~7:05 |

First-run cold compile is TorchInductor: 5–15 min CPU-bound, zero GPU output. Normal. `TORCHINDUCTOR_FORCE_DISABLE=1` skips it (faster start, slower per-step).

## Pitfalls (one line each)

- Sequential only — never two `wgp.py` at once. Run `gpu_wait.py` before each background launch; lays wait until current job finishes.
- Always background with `notify_on_complete=true` (see "Script modes" above). Never blocking shell call for GPU work.
- `--process` is the ONLY flag that accepts a JSON file. `-c` and `--config` are wrong (take a folder).
- LTX-2.3 native I2V (`image_mode: 1`) crashes at the VAE step. The builder uses the proven workaround: `image_mode: 0` + `image_prompt_type: 'S'` + `input_video_strength: 1`. Do not edit those manually.
- Stale `__pycache__` can mask edits with `NameError: 'os' not defined`. Clear with `find <script-dir> -name '*.pyc' -delete && find <script-dir> -name __pycache__ -type d -exec rm -rf {} +`.

## More references

`references/`: `cli-usage-pitfalls.md`, `dual-frame-keyframing.md`, `secondary-characters-from-text.md`, `oom-upsampling-fix.md`, `orphan-process-hang.md`, `torch-inductor-kill-switch.md`, `model_configs.md`, `ltx2-3-loras.md`, `audio-generation-limitations.md`, `compression-benchmarks.md`, `dialogue-video-workflow.md`, `audio-conditioning-workflow.md`, `copy-trend-workflow.md`, `divine-deity-video-prompt-patterns.md`, `meme-video-prompt-patterns.md`.
