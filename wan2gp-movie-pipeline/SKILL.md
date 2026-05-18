---
name: wan2gp-movie-pipeline
description: Multi-scene movies (3+ connected scenes, each ≤20 s). Agent writes a full movie_script.json; the pipeline renders anchors, videos, and compresses scene-by-scene with GPU gating and crash recovery. Final output is the LAST scene's mp4 (continue_from chains and sliding windows already embed prior content).
version: 2.0.0
author: Hermes
license: MIT
metadata:
  hermes:
    tags: [movie, video, pipeline, batch, long-form]
    related_skills: [video-create-workflow, wan2gp-image-generation, wan2gp-video-generation]
---

# Movie Pipeline

For single posts → `video-create-workflow`. For 3+ connected scenes → this skill.

`$PROFILE_ROOT/.env` is **not** auto-sourced; run `set -a; source $PROFILE_ROOT/.env; set +a` first. Required env: `PROFILE_HOME`, `PROFILE_SKILLS`, `POSTS_DIR`, `WAN_APP_DIR`, `WAN_PYTHON`, `CHARACTER_BASE`. **NOT** used: `CHARACTER_ASSETS_DIR`, `CHARACTER_ASSETS_MANIFEST` — movies are self-contained.

## Folder convention

```
$POSTS_DIR/2026-05-18_movie_<tag>/
├── movie_script.json          # all scenes upfront (creative source of truth)
├── progress.json              # written by the pipeline; crash-safe
├── character_base.jpg         # copied from $CHARACTER_BASE (if used)
├── assets/                    # movie-local plates, NOT registered in assets.json
├── scene_01/
│   ├── image_generation.json
│   ├── scene_01_anchor.jpg
│   ├── video_generation.json
│   ├── scene_01_video.mp4
│   └── scene_01_compressed.mp4
├── scene_02/                  # continue_from=scene_01 → no anchor gen
├── scene_03/                  # anchor_from_last_frame=scene_02 → new composition
└── scene_NN/scene_NN_video.mp4  # FINAL OUTPUT (last scene in the chain)
```

Folder slug: `YYYY-MM-DD_movie_<tag>`. Create it with `video-create-workflow/scripts/new_post.py --movie --tag <tag>`.

## Anchor consistency (mandatory)

Each scene's anchor IS that scene's frame 0. Every character that appears in the scene MUST be in the anchor; otherwise LTX-2.3 invents random faces. For multi-character scenes generate the anchor with `wan2gp-image-generation` Qwen multi-ref (image 1 = character A, image 2 = character B, ...), referenced by index in the anchor prompt.

For continuity across scenes use one of three patterns:

| Pattern | Field | What happens |
|---------|-------|--------------|
| Same shot needs > 20 s | (none — use sliding window in the scene's video config) | One scene, `video_length > sliding_window_size`. WanGP stitches automatically. |
| Different action, seamless visual continuity | `continue_from: "scene_NN"` | Skips anchor gen. Pipeline passes prior scene's mp4 as `--video-source`. Video prompt MUST start with `CUT TO:` to discard source artifacts. |
| New camera / composition, but starting from where prev scene ended | `anchor_from_last_frame: "scene_NN"` | Pipeline extracts last frame via ffmpeg, prepends it to `image_refs` (existing refs shift by +1). Then normal anchor + I2V. |

`continue_from` and `anchor_from_last_frame` are mutually exclusive per scene. The referenced scene must appear earlier in the `scenes` array. `init_movie.py` validates.

## movie_script.json schema

```json
{
  "title": "Fantasy Adventure",
  "aspect": "9:16",
  "created": "2026-05-18",
  "synopsis": "One-paragraph summary.",
  "seed": 742981,
  "model": "distilled-1.1",
  "scenes": [
    {
      "id": "scene_01",
      "title": "Portal Discovery",
      "image_refs": ["character_base.jpg", "assets/location_forest.jpg"],
      "anchor_prompt": "Cinematic medium shot, 9:16. Meena (image 1, character_base) stands in the enchanted forest (image 2, location_forest)...",
      "anchor_filename": "scene_01_anchor",
      "video_prompt": "INT. ENCHANTED FOREST — TWILIGHT. Camera pushes in past Meena's shoulder as she turns toward the lens...",
      "video_filename": "scene_01_video"
    },
    {
      "id": "scene_02",
      "title": "Walk Extended",
      "continue_from": "scene_01",
      "anchor_prompt": "",
      "anchor_filename": "scene_02_anchor",
      "video_prompt": "CUT TO: She continues walking deeper into the forest...",
      "video_filename": "scene_02_video"
    },
    {
      "id": "scene_03",
      "title": "New Angle",
      "anchor_from_last_frame": "scene_02",
      "image_refs": ["character_base.jpg"],
      "anchor_prompt": "Cinematic wide shot, 9:16. The character (image 1, from end of walk) seen from behind...",
      "anchor_filename": "scene_03_anchor",
      "video_prompt": "EXT. FOREST — DAY. Camera tracks behind her as she...",
      "video_filename": "scene_03_video"
    }
  ]
}
```

Required per scene: `id`, `title`, `anchor_prompt` (may be empty when `continue_from` is set), `anchor_filename`, `video_prompt`, `video_filename`. `image_refs` are relative to the movie folder, max 3, must match the prompt's `image N` labels.

**Top-level `seed` applies to every scene** — no per-scene override. **`model`** = `distilled-1.1` (default) or `gguf`. Anchor / video prompt rules are identical to single posts — see `wan2gp-image-generation` and `wan2gp-video-generation` (especially the LTX-2.3 prompt guide).

## Asset isolation

Movies are self-contained. Never read / write `$CHARACTER_ASSETS_MANIFEST`. Use:

```bash
cp "$CHARACTER_BASE" <movie-dir>/character_base.jpg

mkdir -p <movie-dir>/assets
python3 "$PROFILE_SKILLS/wan2gp-image-generation/scripts/generate_image_config.py" \
    --prompt "EXT. enchanted forest clearing. No character visible..." \
    --output-filename location_forest --output-dir <movie-dir>/assets \
    --template flux-klein --aspect 9:16 --seed <movie-seed> --generate-and-run
```

(Flux first; Qwen only if you need multi-ref compositing.) Deleting the movie folder cleans up everything.

## Agent workflow

1. Plan the story with the user. Confirm before any rendering.
2. `new_post.py --movie --tag <tag>` (in `video-create-workflow/scripts/`) → `<movie-dir>`.
3. Copy `character_base.jpg` and generate all movie-local plates into `<movie-dir>/assets/`. Verify all `image_refs` resolve.
4. Write the full `movie_script.json` (use the absolute `<movie-dir>/movie_script.json` path — `write_file` defaults to CWD, NOT `$POSTS_DIR`).
5. `python3 "$PROFILE_SKILLS/wan2gp-movie-pipeline/scripts/init_movie.py" --movie-dir <movie-dir>` — validates schema, creates scene folders, seeds `progress.json`.
6. Launch the pipeline as a **background task with notify**:
   ```
   terminal(
       command="python3 $PROFILE_SKILLS/wan2gp-movie-pipeline/scripts/run_pipeline.py --movie-dir <movie-dir>",
       background=true,
       notify_on_complete=true
   )
   ```
   A new user message will NOT kill it. Pipeline gates GPU, renders scenes sequentially, compresses, and updates `progress.json` atomically after every step. The same applies to any single-scene `generate_video_config.py --generate-and-run` or `--run-json` call — always background + notify for GPU work.
7. `python3 "$PROFILE_SKILLS/wan2gp-movie-pipeline/scripts/movie_status.py" --movie-dir <movie-dir>` to poll. Exit 0=done, 1=in progress, 2=stalled.
8. On crash just re-run `run_pipeline.py`. It resumes from `progress.json`.

**Final output rule:** When the chain is all `continue_from` (no `anchor_from_last_frame`), the LAST scene's mp4 already contains the full movie. **Do NOT concat.** When any `anchor_from_last_frame` scenes are present they are standalone 20 s clips — final = last `continue_from` scene + each subsequent `anchor_from_last_frame` mp4, joined with `concat_movie.py` only if needed. Compress and deliver.

## Tools

| Tool | Use |
|------|-----|
| `scripts/init_movie.py --movie-dir <D>` | Validate + scaffold. |
| `scripts/run_pipeline.py --movie-dir <D>` | Run the full pipeline; resumable. |
| `scripts/movie_status.py --movie-dir <D>` | Poll status (exit codes above). |
| `scripts/concat_movie.py --movie-dir <D>` | Only when standalone clips need joining (see "Final output rule"). |
| `video-create-workflow/scripts/gpu_wait.py` / `kill_orphans.py` | Pre-flight before launching another movie. |
| `video-create-workflow/scripts/compress_video.py` | Compress the final mp4 for delivery. |

## Pitfalls (one line each)

- **Add `title` to every scene** — `init_movie.py` doesn't validate it, but `run_pipeline.py` crashes with `KeyError` without it.
- **Never edit `progress.json` by hand** — the pipeline writes it atomically. If stuck, check `gpu_wait.py` / `kill_orphans.py`.
- **Single seed, single model** — both are top-level only. No per-scene override.
- **Ordering** — referenced scene IDs must appear earlier in the `scenes` array.
- **Scene 6+ in long `continue_from` chains** can OOM during second-pass denoising (exit `-9`). Just re-run; the pipeline resumes from the failed scene.
- **Standalone scene segfault (`-11`)** = prompt too visually dense (storm clouds, massive particles, many distinct objects). Simplify and re-run.
- **Sliding window or `continue_from` already merge prior content** — concatenating them produces duplicated, garbage output.
- **`continue_from` requires `CUT TO:`** at the start of the video prompt — without it, source video artifacts ghost into the new scene.
- **`anchor_from_last_frame` shifts refs by +1**: extracted frame becomes image 1; existing `image_refs` shift up. Adjust the prompt indices.
- **No journey / memory writes** for movies — they don't use `journey.jsonl` or the `<Character> State:` line.

## Delegation

- Images → [`wan2gp-image-generation`](../wan2gp-image-generation/SKILL.md)
- LTX-2.3 video, prompt guide, tools → [`wan2gp-video-generation`](../wan2gp-video-generation/SKILL.md)
- Single posts → [`video-create-workflow`](../video-create-workflow/SKILL.md)
- Voice, persona → SOUL.md
