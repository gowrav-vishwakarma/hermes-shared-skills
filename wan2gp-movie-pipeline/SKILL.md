---
name: wan2gp-movie-pipeline
description: Use when the user asks for a multi-scene movie or long-form video (3+ connected scenes). Orchestrates full script writing, autonomous scene-by-scene rendering (anchor image + video + compress), GPU gating, crash recovery via progress tracking, and final concatenation. Single posts use video-create-workflow instead.
version: 1.0.0
author: Hermes
license: MIT
metadata:
  hermes:
    tags: [movie, video, pipeline, batch, long-form]
    related_skills: [video-create-workflow, wan2gp-image-generation, wan2gp-video-generation]
---

# Movie Pipeline

Orchestrates multi-scene movies as an autonomous background pipeline. The agent writes a full `movie_script.json` upfront (all scenes, prompts, asset refs), then kicks off a Python runner that handles anchor generation, video generation, compression, and final concatenation -- scene by scene, with GPU gating and crash recovery.

## When to use

- User asks for a "movie", "short film", "multi-scene video", or any connected sequence of 3+ scenes.
- User asks for a "fantasy movie", "story reel series", or similar long-form content.

## When NOT to use

- Single reels or 1-2 independent posts -- use `video-create-workflow` instead.
- Unrelated batch reels (e.g., "make 5 different reels") -- use the batch protocol in `video-create-workflow`.

## Environment variables

All paths come from `$PROFILE_ROOT/.env`, which is auto-sourced into agent shells. The pipeline scripts (`init_movie.py`, `run_pipeline.py`) are strict consumers and exit with `[env] required env var ... not set` if any required key is missing. Recovery: `set -a; source $PROFILE_ROOT/.env; set +a`.

Used by this skill:

- `PROFILE_HOME` -- profile workspace
- `PROFILE_SKILLS` -- `$PROFILE_ROOT/skills`; used in command examples
- `POSTS_DIR` -- `$PROFILE_HOME/posts` (movies live here as `<YYYY-MM-DD_movie_X>/`)
- `WAN_APP_DIR` -- WanGP app dir (contains `wgp.py`, `env/bin/python`)
- `WAN_PYTHON` -- `$WAN_APP_DIR/env/bin/python`
- `CHARACTER_ASSETS_DIR` -- `$PROFILE_HOME/assets`
- `CHARACTER_ASSETS_MANIFEST` -- `$CHARACTER_ASSETS_DIR/assets.json`
- `CHARACTER_BASE` -- `$PROFILE_HOME/character.png`

Throughout this doc, `<movie-dir>` is shorthand for `$POSTS_DIR/YYYY-MM-DD_movie_<tag>`.

## Folder convention

Movies live inside `$POSTS_DIR/` with `_movie_` in the slug:

```
$POSTS_DIR/2026-05-04_movie_fantasy/
├── movie_script.json           # Creative source of truth (all scenes)
├── progress.json               # Execution state (resumable)
├── scene_01/
│   ├── image_generation.json   # Anchor config (written by pipeline)
│   ├── scene_01_anchor.jpg     # Anchor image
│   ├── video_generation.json   # Video config (written by pipeline)
│   ├── scene_01_video.mp4      # Raw video (~30-40MB)
│   └── scene_01_compressed.mp4 # Compressed (~3-5MB)
├── scene_02/
│   └── ...
├── concat_list.txt             # Generated for ffmpeg concat
└── movie_final.mp4             # Assembled movie
```

Resolve the movie slug as: `YYYY-MM-DD_movie_<short_tag>` where `<short_tag>` is a 1-2 word snake_case descriptor (e.g., `fantasy`, `love_story`, `adventure`).

## movie_script.json schema

```json
{
  "title": "Fantasy Adventure",
  "aspect": "9:16",
  "created": "2026-05-04",
  "synopsis": "One-paragraph summary of the story arc",
  "seed": 742981,
  "model": "gguf",
  "scenes": [
    {
      "id": "scene_01",
      "title": "Portal Discovery",
      "ref_assets": ["character_fantasy", "location_enchanted_forest", "prop_staff"],
      "anchor_prompt": "Cinematic medium shot, 9:16. Meena standing in enchanted forest...",
      "anchor_filename": "scene_01_anchor",
      "video_prompt": "INT. ENCHANTED FOREST -- TWILIGHT. Camera pushes in as...",
      "video_filename": "scene_01_video"
    }
  ]
}
```

**Seed rule**: The top-level `seed` applies to ALL scenes uniformly. Scenes do NOT have individual seed overrides. This ensures visual consistency across the entire movie.

**Model rule**: The top-level `model` (default: `gguf`) applies to all video generation. Options: `gguf` (fastest, ~3 min, use for quick iterations), `distilled-1.1` (auto-LoRAs, fast, ~3-4 min).

**Prompt rules**: Anchor prompts and video prompts follow the same rules as single posts:
- Anchor prompt = WHAT the image shows (static, detailed visual description)
- Video prompt = HOW it MOVES (director-focused: camera, action, dialogue, audio)
- Video prompt must NOT re-describe what the anchor already shows
- See `wan2gp-image-generation` and `wan2gp-video-generation` for full prompting guides

## Agent workflow

### Step 1: Plan the story

Before writing any script, plan the full story arc:
- Define the narrative beats for each scene
- Identify which assets exist and which need to be bootstrapped
- Verify all `ref_assets` slugs exist in `$CHARACTER_ASSETS_MANIFEST`
- Confirm the story with the user before proceeding

### Step 2: Write movie_script.json

Write the complete `movie_script.json` with ALL scenes, prompts, and asset references. Use `write_file` to create it in the movie directory. Every scene must have:
- `id`: `scene_01`, `scene_02`, etc.
- `title`: short descriptive name
- `ref_assets`: list of asset slugs for the anchor (max 3)
- `anchor_prompt`: full Qwen Image Edit Plus prompt
- `anchor_filename`: basename without extension (e.g., `scene_01_anchor`)
- `video_prompt`: full LTX-2.3 director-style prompt
- `video_filename`: basename without extension (e.g., `scene_01_video`)

### Step 3: Initialize

```bash
python3 "$PROFILE_SKILLS/wan2gp-movie-pipeline/scripts/init_movie.py" \
    --movie-dir <movie-dir>
```

This validates the script, creates scene subfolders, and initializes `progress.json`.

### Step 4: Run the pipeline

```bash
python3 "$PROFILE_SKILLS/wan2gp-movie-pipeline/scripts/run_pipeline.py" \
    --movie-dir <movie-dir>
```

Run via `terminal(background=true, notify_on_complete=true)`. The pipeline:
1. Checks GPU availability before each operation
2. Generates anchor image for each scene (Qwen Image Edit Plus)
3. Generates video for each scene (LTX-2.3)
4. Compresses each video with ffmpeg
5. Concatenates all scenes into `movie_final.mp4`
6. Updates `progress.json` after every step (crash-safe)

### Step 5: Monitor

```bash
python3 "$PROFILE_SKILLS/wan2gp-movie-pipeline/scripts/movie_status.py" \
    --movie-dir <movie-dir>
```

Exit codes: 0 = all done, 1 = in progress, 2 = failed/stalled.

### Step 6: Resume after crash

Just re-run `run_pipeline.py`. It reads `progress.json` and skips completed scenes automatically.

### Step 7: Manual concat (if needed)

If all scenes completed but concat was interrupted:

```bash
python3 "$PROFILE_SKILLS/wan2gp-movie-pipeline/scripts/concat_movie.py" \
    --movie-dir <movie-dir>
```

## GPU safety

The pipeline enforces these rules automatically:
- **Pre-flight check**: before every `wgp.py` call, checks `ps aux` for running wgp.py processes
- **Wait loop**: if GPU is busy, polls every 30s until free
- **Orphan detection**: if a wgp.py process is found but no matching job is running, attempts graceful kill (SIGTERM), waits 5s, then SIGKILL
- **D-state detection**: if `kill -9` fails, logs a warning that GPU may be deadlocked and exits (reboot required)
- **Sequential only**: never runs two wgp.py processes simultaneously (24 GB VRAM)

## Crash recovery

`progress.json` is the recovery mechanism:
- Updated atomically (write to `.tmp`, then `os.rename`) after every step
- Each scene tracks three steps: `anchor_gen`, `video_gen`, `compress`
- On resume, the pipeline checks which step each scene is at:
  - `completed` scenes are skipped entirely
  - `in_progress` scenes check for existing output files before re-generating
  - `pending` scenes start from scratch

## Common pitfalls

1. **Missing assets.** Before writing `movie_script.json`, verify all `ref_assets` slugs exist in `$CHARACTER_ASSETS_MANIFEST`. The `init_movie.py` script validates this and will error if slugs are missing.

2. **Seed inconsistency.** Never add per-scene seeds. The movie-level seed ensures visual consistency. If you need a different seed, change the top-level `seed` and re-run.

3. **Anchor-video coherence.** Each scene's video prompt must match its anchor composition. The pipeline does NOT validate prompt coherence -- the agent must ensure this when writing the script.

4. **Long runtime.** A 5-scene movie takes ~30-40 minutes (gguf model). A 10-scene movie takes ~60-80 minutes. Use `movie_status.py` to check progress, not aggressive polling.

5. **Orphaned processes after crash.** If the system crashed mid-generation, check for orphaned wgp.py before re-running: `ps aux | grep wgp.py | grep -v grep`. Kill any orphans first.

6. **Stale `__pycache__` causes misleading `NameError`.** If `generate_video_config.py` fails with `NameError: name 'os' is not defined` despite having `import os` at the top, there is likely a stale `.pyc` bytecode file. Clear it:
   ```bash
   find <script-dir> -name "*.pyc" -delete
   find <script-dir> -name "__pycache__" -type d -exec rm -rf {} +
   ```
   See `wan2gp-video-generation` skill for full details.

7. **Movie script field validation.** `init_movie.py` validates `id`, `anchor_prompt`, `anchor_filename`, `video_prompt`, and `video_filename`, but DOES NOT validate the `title` field. The pipeline accesses `scene["title"]` at line 554 of `run_pipeline.py` — if missing, it crashes with `KeyError: 'title'` mid-scene. **Always add a `title` field to every scene** in the JSON before running the pipeline. This is an easy-to-miss required field that causes a non-obvious failure.

8. **Never manually edit progress.json.** The pipeline writes to `progress.json` itself via `atomic_write_json()` at every step (anchor_gen done, video_gen running, compress done, scene completed, etc.). This is the pipeline's sole responsibility for crash-recovery. Manually editing it is unnecessary interference and can corrupt state. If the pipeline seems stuck, check for orphans or GPU issues — not `progress.json`.

9. **Kill stale pipelines before starting new ones.** Multiple pipelines from the same profile share the same GPU and block each other via the `wait_for_gpu()` gating. The GPU RAM usage will be low if you see no `wgp.py` process running — it likely means a pipeline is queued behind another. Always check `ps aux | grep -E "(wgp|run_pipeline)" | grep -v grep` before launching a new movie pipeline. If old pipelines are still running, kill them first unless you intentionally want to queue behind them.

## Delegation

- **How to make images** (assets, anchors, ref prompting) -> `wan2gp-image-generation`
- **How to make videos** (LTX-2.3 director-style prompting, audio, I2V) -> `wan2gp-video-generation`
- **Single posts** -> `video-create-workflow`
- **Voice, persona, accent, character quirks** -> `SOUL.md`
