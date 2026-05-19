---
name: wan2gp-image-generation
description: Image generation via WanGP — Flux 2 Klein 9B (default, single ref) and Qwen Image Edit Plus 2511 (multi-ref compositing). Asset library, anchors, character bases.
category: media
---

# WanGP Image Generation

Three job types come out of this skill — all via the same script:

| Job | Tool | Notes |
|-----|------|-------|
| Standalone image (anchor, character base) | `scripts/generate_image_config.py` | Pick the right `--template` |
| Reusable library asset (renders + registers in `assets.json`) | `scripts/generate_asset.py` | Wraps the above + manifest |
| Remove / list registered assets | `scripts/remove_asset.py` | `--list`, `--keep-only`, `--keep-files` |

`$PROFILE_ROOT/.env` is **not** auto-sourced; run `set -a; source $PROFILE_ROOT/.env; set +a` first (**never** `source $PROFILE_HOME/.env`). Required env (resolved by `_env.py`): `WAN_APP_DIR`, `WAN_PYTHON`, `CHARACTER_ASSETS_DIR`, `CHARACTER_ASSETS_MANIFEST`, `CHARACTER_BASE`, `PROFILE_HOME`, `POSTS_DIR`. **`--output-dir`** = path from `new_post.py`, not `~/.hermes/...` — see [`../video-create-workflow/references/hermes-path-pitfall.md`](../video-create-workflow/references/hermes-path-pitfall.md).

## Model preference (PICK FLUX UNLESS YOU NEED MULTI-REF)

| Model | Template alias | Use when | Speed | Refs |
|-------|---------------|----------|-------|------|
| **Flux 2 Klein 9B** (default) | `flux-klein` (9:16), `flux-klein-16x9` | Any character base, single-ref portraits, location plates | ~35 s (8 steps, guidance 2.5) | 0–1 ref |
| Qwen Image Edit Plus 2511 | `default` / `16x9` (standard), `9x16-quality` / `16x9-quality` (native 928x1664), `lightning` (4-step draft) | Multi-ref compositing (2–3 refs), image-edit tasks | ~3 min (50 steps) | 0–3 refs (cap) |

Flux is fundamentally more realistic (visible skin texture, natural hair). Qwen leans hyper-perfect. Both are photorealistic — neither can produce Pixar / cartoon / anime. For stylized output use ComfyUI (see `references/model-style-limits.md`).

## Script modes

`generate_image_config.py` and `generate_asset.py` accept three mutually-exclusive modes (default = generate-only):

| Flag | Effect |
|------|--------|
| (no flag) or `--generate-only` | Build the JSON, write it, exit. Print the JSON path. |
| `--generate-and-run` or `--run` | Build the JSON, write it, then run `wgp.py --process` on it via `$WAN_PYTHON`. |
| `--run-json PATH` | Skip the build; run `wgp.py --process` on an existing JSON. Useful to re-run after fixing the prompt or loras — just re-run with `--generate-only` to overwrite the JSON, then `--run-json` it. |

Use generate-only when you want to inspect or hand-edit the JSON before paying GPU cost. Re-running `--generate-only` with corrected args always overwrites the existing JSON (the output filename is fixed as `image_generation.json` in the output dir).

**CRITICAL — GPU runs MUST be launched in background with notify:**

Any invocation of `--generate-and-run` or `--run-json` blocks for 30 s – 10 min (wgp.py holds the GPU). Launch the entire Python call as a background terminal task so a new user message does not kill the process:

```
terminal(
    command="python3 $PROFILE_SKILLS/wan2gp-image-generation/scripts/generate_image_config.py --generate-and-run ...",
    background=true,
    notify_on_complete=true
)
```

Never run GPU-invoking commands in a blocking shell call or without `notify_on_complete`. The GPU process survives agent timeouts and session interruptions only when launched this way.

## Required flags for the build step

| Flag | Required | Notes |
|------|----------|-------|
| `--prompt "..."` | yes (unless `--run-json`) | Detailed static description: subject, outfit, location, lighting, composition. |
| `--output-filename NAME` | yes (unless `--run-json`) | Basename, no extension. |
| `--output-dir PATH` | yes (unless `--run-json`) | Absolute path. JSON is written here as `image_generation.json`. |
| `--aspect 9:16 \| 16:9` | recommended | Sets resolution and picks the matching template. |
| `--template ALIAS` | optional | Default = Qwen 9:16. Use `flux-klein` for Flux. |
| `--seed N` | recommended | Same seed across a story keeps visual consistency. |
| `--ref-assets slug [slug ...]` | optional | Resolves slugs from `assets.json` → absolute paths. Auto-picks `I` vs `KI`. Max 3 (Qwen cap). |
| `--image-refs PATH [PATH ...]` | optional | Absolute paths; prepended after `--ref-assets`. Do NOT duplicate the same file across both flags. |
| `--quality` | optional | Qwen only: render at native 928x1664 / 1664x928 for max detail. |

In the prompt, **always** label each reference by index AND slug for auditability: `"Alice (image 1, character_alice)... Bob (image 2, character_bob)..."`. Order of `--image-refs` / `--ref-assets` MUST match the prompt's image-N labels.

## Asset library layout

```
$PROFILE_HOME/
├── character.png                       # $CHARACTER_BASE (slug: character_base)
└── assets/                             # $CHARACTER_ASSETS_DIR
    ├── assets.json                     # $CHARACTER_ASSETS_MANIFEST
    ├── character_kurti_palazzo.jpg
    ├── location_indian_bedroom.jpg
    └── ...
```

Slug convention: `kind_descriptor` (snake_case). Kinds: `character`, `vehicle` / `spaceship`, `creature`, `location`, `prop`, `other`. Use the per-post helper `register_asset.py` (in `video-create-workflow/scripts/`) to register existing files without re-rendering. Asset library is **per-post journey only**; movies manage their own local assets (see `wan2gp-movie-pipeline`).

Location and interior plates must be **character-free** ("no character visible") at eye-level (~5.5 ft) with clear foreground ground space — otherwise composited characters appear to float.

## Quick recipes

Flux character base (text-to-image, photoreal):
```bash
python3 "$PROFILE_SKILLS/wan2gp-image-generation/scripts/generate_image_config.py" \
    --prompt "Candid phone photo of a 22-year-old Indian woman, natural skin texture..." \
    --output-filename character_base \
    --output-dir "$PROFILE_HOME" \
    --template flux-klein --aspect 9:16 --steps 8 --guidance-scale 2.5 \
    --seed 31337 --generate-and-run
```

Qwen multi-ref anchor (2-3 refs):
```bash
python3 "$PROFILE_SKILLS/wan2gp-image-generation/scripts/generate_image_config.py" \
    --prompt "Cinematic medium shot, 9:16. Alice (image 1, character_alice) ... Bob (image 2, character_bob) ... in courtyard (image 3, location_courtyard)." \
    --ref-assets character_alice character_bob location_courtyard \
    --output-filename meeting_anchor \
    --output-dir "$POSTS_DIR/2026-05-18_1" \
    --aspect 9:16 --seed 742981 --generate-and-run
```

Register a new asset (renders + adds to manifest):
```bash
python3 "$PROFILE_SKILLS/wan2gp-image-generation/scripts/generate_asset.py" \
    --name location_indian_bedroom --kind location --aspect 9:16 \
    --description "INT. Indian bedroom, golden hour, no character visible." \
    --prompt "INT. cozy Indian bedroom..." --generate-and-run
```

Aspect ratio fix without GPU (character centered on solid background):
```bash
ffmpeg -y -i input.png -vf "crop=720:1280:(in_w-720)/2:(in_h-1280)/2" output.png
```

## Pitfalls (one line each)

- 3-ref anchors are VRAM-heavy — expect up to 5 min; background launch (above) prevents timeout kills.
- Sequential only — never two `wgp.py` jobs at once. Use `video-create-workflow/scripts/gpu_wait.py` before launching.
- Don't pass the same file in both `--ref-assets` and `--image-refs`; it gets duplicated, switching the mode from `I` to `KI`.
- Flux can't subdir in `--output-filename`; point `--output-dir` directly at the target folder.
- For temp / one-off images the user says "don't save": use `generate_image_config.py` (writes only to your post folder), NOT `generate_asset.py` (which registers in the manifest).
- 4:3 / square user-supplied photos that are centered on a solid background should be cropped with ffmpeg (above) instead of WanGP-regenerated.
- First Qwen run cold-compiles for 5–10 min with zero visible output — that is normal.

## References

- [`references/model-style-limits.md`](references/model-style-limits.md) — both Qwen and Flux Klein are photorealistic only; use ComfyUI for stylized work.
- [`references/qwen-realism-challenge.md`](references/qwen-realism-challenge.md) — fighting Qwen's hyper-perfect aesthetic for documentary nature scenes.
- [`references/multi-ref-character-consistency.md`](references/multi-ref-character-consistency.md) — multi-character anchor patterns.
- [`references/divine-deity-video-prompt-patterns.md`](references/divine-deity-video-prompt-patterns.md) — Hindu deity scene patterns (Flux Klein).
