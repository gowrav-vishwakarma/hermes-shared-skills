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

Orchestrates multi-scene movies as an autonomous background pipeline. The agent writes a full `movie_script.json` upfront (all scenes, prompts, image refs), then kicks off a Python runner that handles anchor generation, video generation, compression, and final concatenation -- scene by scene, with GPU gating and crash recovery.

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
- `CHARACTER_BASE` -- `$PROFILE_HOME/character.png`

**NOT used by movies:** `CHARACTER_ASSETS_DIR` and `CHARACTER_ASSETS_MANIFEST` (`assets.json`) belong to the journey workflow (`video-create-workflow`) only. Movies are self-contained -- see "Asset isolation" below.

Throughout this doc, `<movie-dir>` is shorthand for `$POSTS_DIR/YYYY-MM-DD_movie_<tag>`.

## Folder convention

Movies live inside `$POSTS_DIR/` with `_movie_` in the slug:

```
$POSTS_DIR/2026-05-04_movie_fantasy/
├── movie_script.json           # Creative source of truth (all scenes)
├── progress.json               # Execution state (resumable)
├── character_base.jpg          # Copied from $CHARACTER_BASE (if character needed)
├── assets/                     # Movie-local assets (NOT in main manifest)
│   ├── location_enchanted_forest.jpg
│   └── prop_staff.jpg
├── scene_01/
│   ├── image_generation.json   # Anchor config (written by pipeline)
│   ├── scene_01_anchor.jpg     # Anchor image
│   ├── video_generation.json   # Video config (written by pipeline)
│   ├── scene_01_video.mp4      # Raw video (~30-40MB)
│   └── scene_01_compressed.mp4 # Compressed (~3-5MB)
├── scene_02/                   # continue_from=scene_01 (no anchor gen)
│   ├── video_generation.json   # Config with video_source pointing to scene_01
│   ├── scene_02_video.mp4
│   └── scene_02_compressed.mp4
├── scene_03/                   # anchor_from_last_frame=scene_02
│   ├── scene_03_anchor_lastframe.jpg  # Extracted last frame from scene_02
│   ├── image_generation.json
│   ├── scene_03_anchor.jpg
│   ├── video_generation.json
│   ├── scene_03_video.mp4
│   └── scene_03_compressed.mp4
├── concat_list.txt             # Generated for ffmpeg concat
└── movie_final.mp4             # Assembled movie
```

Resolve the movie slug as: `YYYY-MM-DD_movie_<short_tag>` where `<short_tag>` is a 1-2 word snake_case descriptor (e.g., `fantasy`, `love_story`, `adventure`).

## Asset isolation (movies vs journey)

Movies are **self-contained entities**. They do NOT use the shared character asset manifest (`assets.json`) or `$CHARACTER_ASSETS_DIR`. Those belong exclusively to the journey workflow (`video-create-workflow`) for regular posts.

**Rules for movie assets:**

1. **Never read from or write to `assets.json`.** The manifest is for the ongoing character journey only.
2. **Copy `$CHARACTER_BASE` into `<movie-dir>/character_base.jpg`** if the character appears in any scene. This is the only bridge between the profile identity and the movie.
3. **Generate movie-specific assets into `<movie-dir>/assets/`** (locations, props, creatures). Use `generate_image_config.py --run` with `--output-dir <movie-dir>/assets/` directly -- do NOT use `generate_asset.py` (that registers into the manifest).
4. **Reference images by relative path** in `movie_script.json` via the `image_refs` field (relative to `<movie-dir>`). Examples: `"character_base.jpg"`, `"assets/location_enchanted_forest.jpg"`.
5. **Movie assets are disposable.** They live and die with the movie folder. Deleting a movie folder cleans up everything.

**Why this separation exists:** The asset manifest tracks a character's evolving visual identity across a journey of posts -- outfit variants, recurring locations, vehicles. Movies are standalone creative pieces with their own art direction. Mixing them pollutes the journey manifest with one-off movie props and makes asset cleanup painful.

## Video continuation (extended scenes)

Movies often need scenes longer than a single 20-second generation, or need visual continuity when transitioning between scenes. Three approaches are available:

### Approach 0: Sliding window (single scene > 20s)

For a single continuous shot that just needs more duration (same scene, same camera flow), use the **sliding window** mechanism in `wan2gp-video-generation` rather than splitting into multiple movie scenes. Set `video_length` higher than `sliding_window_size` in the scene's video config and WanGP generates overlapping windows stitched into one video automatically.

This is the simplest approach when a scene needs 30-60 seconds instead of 20. No extra movie scenes needed, no `continue_from` chaining. See the "Extended Videos" section in `wan2gp-video-generation` for parameter details.

**When to use:** A single unbroken shot needs more than 20 seconds of duration.
**When NOT to use:** You need a different prompt, camera angle, or composition mid-way -- use Approach A or B below instead.

### Approach A: `continue_from` (WanGP native Continue Video)

Best for **chaining scenes with different prompts** -- the new scene picks up from where the previous one ended, but can describe entirely new action.

- Skips anchor generation entirely (no `anchor_prompt` or `image_refs` needed)
- Passes the referenced scene's completed video as `--video-source` to WanGP
- WanGP reads the last frames from the source and generates new frames that seamlessly continue
- The scene's `video_prompt` describes what happens NEXT -- do not re-describe the source video

```json
{
  "id": "scene_02",
  "title": "Forest Walk Extended",
  "continue_from": "scene_01",
  "anchor_prompt": "",
  "anchor_filename": "scene_02_anchor",
  "video_prompt": "She continues walking along the bank, her dupatta trailing...",
  "video_filename": "scene_02_video"
}
```

### Approach B: `anchor_from_last_frame` (last-frame extraction + I2V)

Best for **scene transitions** -- new camera angle, new composition, but starting from the visual state where the previous scene ended.

- Extracts the last frame of the referenced scene's video via ffmpeg
- Prepends that frame to the scene's `image_refs` as the first ref (existing refs shift by +1)
- Runs normal anchor generation and I2V video generation
- `anchor_prompt` must describe the extracted frame plus any other refs

```json
{
  "id": "scene_03",
  "title": "Sitting by River",
  "anchor_from_last_frame": "scene_02",
  "image_refs": ["character_base.jpg"],
  "anchor_prompt": "Cinematic close-up, 9:16. The character (image 1, from end of walk) now seated...",
  "anchor_filename": "scene_03_anchor",
  "video_prompt": "The camera slowly orbits as she settles by the water...",
  "video_filename": "scene_03_video"
}
```

### When to use which

| Goal | Mode | Key |
|------|------|-----|
| Single shot needs > 20s (same prompt, fluid motion) | Sliding window | Set `video_length > sliding_window_size` in video config |
| Chain scenes with different prompts/action | Continue Video | `continue_from` |
| New composition from where previous ended | Last Frame | `anchor_from_last_frame` |
| Fresh scene, no continuity needed | Normal | Neither field |

### Constraints

- **Mutual exclusivity**: a scene cannot have both `continue_from` and `anchor_from_last_frame`.
- **Ordering**: the referenced scene must appear **before** the current scene in the `scenes` array.
- **`continue_from` skips anchor gen**: `anchor_prompt` and `image_refs` are ignored (but `anchor_filename` is still required for folder structure).
- **`anchor_from_last_frame` shifts refs**: the extracted frame becomes image 1 in the prompt. Adjust your `anchor_prompt` image-index references accordingly -- existing `image_refs` shift up by one position.
- `init_movie.py` validates all of these constraints.

## movie_script.json schema

```json
{
  "title": "Fantasy Adventure",
  "aspect": "9:16",
  "created": "2026-05-04",
  "synopsis": "One-paragraph summary of the story arc",
  "seed": 742981,
  "model": "distilled-1.1",
  "scenes": [
    {
      "id": "scene_01",
      "title": "Portal Discovery",
      "image_refs": ["character_base.jpg", "assets/location_enchanted_forest.jpg"],
      "anchor_prompt": "Cinematic medium shot, 9:16. Meena standing in enchanted forest...",
      "anchor_filename": "scene_01_anchor",
      "video_prompt": "INT. ENCHANTED FOREST -- TWILIGHT. Camera pushes in as...",
      "video_filename": "scene_01_video"
    },
    {
      "id": "scene_02",
      "title": "Portal Discovery Extended",
      "continue_from": "scene_01",
      "anchor_prompt": "",
      "anchor_filename": "scene_02_anchor",
      "video_prompt": "She continues walking deeper into the forest, the camera tracking...",
      "video_filename": "scene_02_video"
    },
    {
      "id": "scene_03",
      "title": "New Angle on Forest",
      "anchor_from_last_frame": "scene_02",
      "image_refs": ["character_base.jpg"],
      "anchor_prompt": "Cinematic wide shot, 9:16. The character (image 1, from walk end) now seen from behind...",
      "anchor_filename": "scene_03_anchor",
      "video_prompt": "EXT. FOREST -- DAY. Camera tracks from behind as...",
      "video_filename": "scene_03_video"
    }
  ]
}
```

- `scene_01`: Fresh anchor + video (normal flow)
- `scene_02`: Continues scene_01's video seamlessly (no anchor needed, same shot extended)
- `scene_03`: Extracts last frame of scene_02, uses as anchor for a new composition (new angle)

**`image_refs`**: List of image paths **relative to `<movie-dir>`**. These are passed as `--image-refs` (absolute paths resolved by the pipeline) to `generate_image_config.py`. Max 3 refs (Qwen cap). Use `"character_base.jpg"` for identity locking. Order must match the prompt's image-index references (image 1, image 2, etc.).

**Seed rule**: The top-level `seed` applies to ALL scenes uniformly. Scenes do NOT have individual seed overrides. This ensures visual consistency across the entire movie.

**Model rule**: The top-level `model` (default: `distilled-1.1`) applies to all video generation. Options: `distilled-1.1` (auto-LoRAs, fast, ~3-4 min), `gguf` (fastest C++ runtime, ~3 min, no compile needed).

**Prompt rules**: Anchor prompts and video prompts follow the same rules as single posts:
- Anchor prompt = WHAT the image shows (static, detailed visual description)
- Video prompt = HOW it MOVES (director-focused: camera, action, dialogue, audio)
- Video prompt must NOT re-describe what the anchor already shows
- See `wan2gp-image-generation` and `wan2gp-video-generation` for full prompting guides

## Agent workflow

### Step 1: Plan the story

Before writing any script, plan the full story arc:
- Define the narrative beats for each scene
- Identify which movie-local images need to be generated in `<movie-dir>/assets/` (locations, props, creatures)
- Decide if the character appears -- if yes, `character_base.jpg` will be copied in Step 2b
- Confirm the story with the user before proceeding

### Step 2: Write movie_script.json

Write the complete `movie_script.json` with ALL scenes, prompts, and image references. Use `write_file` to create it in the movie directory. Every scene must have:
- `id`: `scene_01`, `scene_02`, etc.
- `title`: short descriptive name
- `image_refs`: list of image paths relative to `<movie-dir>` (max 3). E.g., `["character_base.jpg", "assets/location_forest.jpg"]`
- `anchor_prompt`: full Qwen Image Edit Plus prompt (image-index order must match `image_refs` order)
- `anchor_filename`: basename without extension (e.g., `scene_01_anchor`)
- `video_prompt`: full LTX-2.3 director-style prompt
- `video_filename`: basename without extension (e.g., `scene_01_video`)

Optional continuation fields (see "Video continuation" section above):
- `continue_from`: scene ID to continue from (WanGP native continue -- skips anchor gen)
- `anchor_from_last_frame`: scene ID whose last frame becomes the anchor (extracts frame + I2V)

### Step 2b: Bootstrap movie assets

Before running the pipeline, generate all assets the movie needs **locally** inside `<movie-dir>`:

1. **Character source** (two workflows):
   - **User-provided character** (preferred): If the user sends their own images/photos, use them directly. Copy to `<movie-dir>/character_base.jpg` and skip generation. This avoids the AI-perfect look and gives exact visual identity. The user may send multiple photos — pick the most dynamic/cinematic one as anchor, and note others for scene-specific styling.
     ```bash
     cp <user-provided-image-path> <movie-dir>/character_base.jpg
     ```
   - **Auto-generated character** (fallback): When no user image is available, generate with a realistic documentary prompt (see below).
     ```bash
     cp "$CHARACTER_BASE" <movie-dir>/character_base.jpg
     ```
   > **Pitfall: User-provided characters may have different aspect ratios.** If the user's image is not 16:9 or 9:16, regenerate it with `generate_image_config.py` using the movie's aspect ratio, OR instruct the user to crop/resize first. Mismatched aspect ratios can distort composition in anchor prompts.

   > **Documentary prompt for auto-generated characters:** When generating a character from scratch, use the prompt pattern: `"A realistic [description]. Photographic realism, documentary style -- Canon EOS R5, [85mm/35mm] lens. Natural skin texture with slight pores, not airbrushed. No AI-perfect rendering, slight film grain, natural imperfections."` This counteracts Qwen's hyper-perfect aesthetic tendency. See `references/user-character-workflow.md`.

2. **Generate movie-specific locations/props/creatures** into `<movie-dir>/assets/`:
   ```bash
   mkdir -p <movie-dir>/assets
   python3 "$PROFILE_SKILLS/wan2gp-image-generation/scripts/generate_image_config.py" \
       --prompt "EXT. enchanted forest clearing. No character visible. Towering ancient trees..." \
       --output-filename location_enchanted_forest \
       --output-dir <movie-dir>/assets \
       --aspect 9:16 \
       --seed <movie-seed> \
       --run
   ```
   Use `generate_image_config.py` (NOT `generate_asset.py` -- that registers into the journey manifest).

3. **Verify all `image_refs`** in `movie_script.json` point to existing files before proceeding.

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

1. **Missing local images.** Before running the pipeline, verify all `image_refs` paths in `movie_script.json` resolve to actual files inside `<movie-dir>`. The `init_movie.py` script validates this and will error on missing files. Run Step 2b (bootstrap) first.

2. **Seed inconsistency.** Never add per-scene seeds. The movie-level seed ensures visual consistency. If you need a different seed, change the top-level `seed` and re-run.

3. **Anchor-video coherence.** Each scene's video prompt must match its anchor composition. The pipeline does NOT validate prompt coherence -- the agent must ensure this when writing the script.

4. **Long runtime.** A 5-scene movie takes ~30-40 minutes (distilled-1.1 model). A 10-scene movie takes ~60-80 minutes. Use `movie_status.py` to check progress, not aggressive polling.

5. **Orphaned processes after crash.** If the system crashed mid-generation, check for orphaned wgp.py before re-running: `ps aux | grep wgp.py | grep -v grep`. Kill any orphans first.

6. **Stale `__pycache__` causes misleading `NameError`.** If `generate_video_config.py` fails with `NameError: name 'os' is not defined` despite having `import os` at the top, there is likely a stale `.pyc` bytecode file. Clear it:
   ```bash
   find <script-dir> -name "*.pyc" -delete
   find <script-dir> -name "__pycache__" -type d -exec rm -rf {} +
   ```
   See `wan2gp-video-generation` skill for full details.

7. **Movie script field validation.** `init_movie.py` validates `id`, `anchor_prompt`, `anchor_filename`, `video_prompt`, and `video_filename`, but DOES NOT validate the `title` field. The pipeline accesses `scene["title"]` at line 554 of `run_pipeline.py` — if missing, it crashes with `KeyError: 'title'` mid-scene. **Always add a `title` field to every scene** in the JSON before running the pipeline. This is an easy-to-miss required field that causes a non-obvious failure.

8. **Never manually edit progress.json.** The pipeline writes to `progress.json` itself via `atomic_write_json()` at every step (anchor_gen done, video_gen running, compress done, scene completed, etc.). This is the pipeline's sole responsibility for crash-recovery. Manually editing it is unnecessary interference and can corrupt state. If the pipeline seems stuck, check for orphans or GPU issues — not `progress.json`.

9. **Scene ordering for continuation.** `continue_from` and `anchor_from_last_frame` reference other scenes by ID. The referenced scene MUST appear earlier in the `scenes` array and MUST have completed video generation before the referencing scene runs. `init_movie.py` validates ordering at initialization, but if you add scenes to an existing script, verify the order manually.

10. **Kill stale pipelines before starting new ones.** Multiple pipelines from the same profile share the same GPU and block each other via the `wait_for_gpu()` gating. The GPU RAM usage will be low if you see no `wgp.py` process running — it likely means a pipeline is queued behind another. Always check `ps aux | grep -E "(wgp|run_pipeline)" | grep -v grep` before launching a new movie pipeline. If old pipelines are still running, kill them first unless you intentionally want to queue behind them.

11. **Character anchor for scene transitions.** When generating multi-scene videos with location/scene changes, always copy the user's real photo to `<movie-dir>/character_base.jpg` and use it as `--image-start` for EVERY scene (not just the first). Do NOT rely on `continue_from` or last-frame extraction for scene transitions — WanGP's Continue Video mode will try to morph the source scene into the new scene, causing visual artifacts. Image-start with the character anchor ensures the new scene starts with the correct composition and character identity. This is the most reliable method for identity locking across scene changes.

## Delegation

- **How to make images** (assets, anchors, ref prompting) -> `wan2gp-image-generation`
- **How to make videos** (LTX-2.3 director-style prompting, audio, I2V) -> `wan2gp-video-generation`
- **Single posts** -> `video-create-workflow`
- **Voice, persona, accent, character quirks** -> `SOUL.md`
