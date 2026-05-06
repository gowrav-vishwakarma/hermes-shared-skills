---
name: wan2gp-image-generation
description: Qwen Image Edit Plus 2511 via WanGP -- reusable asset library and per-post anchor images
category: media
---

# WanGP Image Generation (Assets + Anchors)

Two image jobs come out of this skill:

- **Assets** -- reusable library refs (spaceship, creature, location plate) rendered once and re-used across posts via `--ref-assets <slug>`.
- **Anchors** -- per-post first frame for LTX-2.3 I2V, compositing the character into a scene using library assets as Qwen refs.

Both use **Qwen Image Edit Plus 2511** (`qwen_image_edit_plus2_20B`) through WanGP CLI.

## Environment variables

All paths come from `$PROFILE_ROOT/.env`. **Important: the .env file is NOT auto-sourced into agent subprocess shells.** Before running any helper script, source it manually:

```bash
set -a; source $PROFILE_ROOT/.env; set +a
```

## Environment variables

**CRITICAL: The `.env` file is NOT auto-sourced into agent subprocess shells.** Before running any helper script, you MUST manually source it:

```bash
set -a; source $PROFILE_ROOT/.env; set +a
```

Or in Python subprocess calls, explicitly pass the env dict after sourcing:
```python
env = {**os.environ}
with open('$PROFILE_ROOT/.env') as f:
    for line in f:
        if '=' in line:
            k, v = line.split('=', 1)
            env[k.strip()] = v.strip()
```

The helper scripts are strict consumers and will exit with `[env] required env var ... not set` if any required key is missing.

**NOTE on `$PROFILE_SKILLS`:** In this profile, it points to `/home/gowrav/.hermes/shared-skills` (NOT the local skills dir). Verify: `grep PROFILE_SKILLS $PROFILE_ROOT/.env`.

Used by this skill:

- `PROFILE_HOME` -- profile workspace (also `$HOME` for the agent)
- `PROFILE_SKILLS` -- shared skills dir (`/home/gowrav/.hermes/shared-skills` in this profile)
- `POSTS_DIR` -- `$PROFILE_HOME/posts`
- `WAN_APP_DIR` -- WanGP app dir (contains `wgp.py`, `env/bin/python`, `defaults/`)
- `WAN_PYTHON` -- `$WAN_APP_DIR/env/bin/python` (override interpreter)
- `CHARACTER_ASSETS_DIR` -- `$PROFILE_HOME/assets`
- `CHARACTER_ASSETS_MANIFEST` -- `$CHARACTER_ASSETS_DIR/assets.json`
- `CHARACTER_BASE` -- `$PROFILE_HOME/character.png`

Always pass **absolute paths** to `--output-dir`, `--assets-dir`, and `--ref-assets`. Never pass `~/.hermes/...` as a relative path.

## Asset library

> **Scope: journey and regular posts only.** The asset library (`assets.json`) and `$CHARACTER_ASSETS_DIR` are for the character's ongoing journey managed by `video-create-workflow`. Movies do NOT use the manifest -- they manage their own local assets inside the movie folder. See `wan2gp-movie-pipeline` for movie asset handling.

**Layout:**

```
$PROFILE_HOME/
├── character.png                   # $CHARACTER_BASE (slug: character_base)
└── assets/                         # $CHARACTER_ASSETS_DIR
    ├── assets.json                 # $CHARACTER_ASSETS_MANIFEST
    ├── spaceship_exterior.jpg
    ├── creature_moon_guardian.jpg
    └── ...
```

**Naming -- snake_case, kind-prefixed slugs:**

| Kind | Prefix | Examples |
|------|--------|----------|
| `character` | `character_` | `character_spacesuit_helmet`, `character_home_civilian` |
| `vehicle` | `vehicle_` / `spaceship_` | `spaceship_exterior`, `spaceship_cockpit` |
| `creature` | `creature_` | `creature_moon_guardian` |
| `location` | `location_` | `location_lunar_cavern`, `location_alien_station_dome` |
| `prop` | `prop_` | `prop_communicator` |

**Manifest entry shape** (see [`scripts/asset_manifest.py`](scripts/asset_manifest.py)):

```json
{
    "path": "<absolute path>",
    "kind": "character|vehicle|creature|location|prop|other",
    "aspect": "9:16|16:9|1:1|free",
    "description": "<one sentence>",
    "tags": ["..."],
    "parent_refs": ["<slug>", ...],
    "source_post": "<post slug or 'seed'>",
    "created": "YYYY-MM-DD"
}
```

### Character Asset Generation Workflow (Isolated)

When the user requests character asset generation for branding, follow this specific workflow to ensure reusability and consistent output quality:

1. **Isolation:** Use "Simple studio background, high-key lighting, isolated character, no background details" in the prompt to ensure the model focuses purely on the character silhouette.
2. **Naming Convention:** Always use the requested slug (e.g., `character_girl`, `character_geek_boy`) and ensure the final file saved to `$CHARACTER_ASSETS_DIR` is a `.png`.
3. **Automated Conversion:** The WanGP pipeline generates `.jpg` by default. Always follow up with a terminal `mv` command to rename the output to `.png` to match the requested assets folder naming convention.
4. **Consistency:** Ensure the prompt describes the character's clothing and style accurately based on the user's provided description, while enforcing the "no background" constraint.

When the user sends a photo to use as their base character, **NEVER just copy it as `character.png`**. The original may be in any aspect ratio (4:3, landscape, square, etc.) and will distort or miscompose in video generation workflows that expect 9:16.

**Correct workflow:**

1. **Save the original separately:** `cp <user-photo> "$CHARACTER_ASSETS_DIR/character_original.png"` (or similar name). This preserves the exact source.
2. **Generate a proper 9:16 version** using `generate_image_config.py --run` with the original as `--image-refs`, targeting `--aspect 9:16`. This uses WanGP's image model to re-compose the character without stretching or distortion.
3. **Copy the 9:16 version as `character.png`:** `cp "$PROFILE_HOME/character_9x16.jpg" "$PROFILE_HOME/character.png"`. This becomes the main identity anchor.
4. **Register both in `assets.json`:** `character_original` (kind: character, aspect: free) and `character_base` (kind: character, aspect: 9:16).

**Why:** Video prompts expect a consistent aspect ratio for anchors. A 4:3 or landscape source photo will cause composition mismatches when WanGP composites the character into 9:16 video frames. The 9:16 generation step re-frames the character correctly.

## Pick the best character ref

Do NOT always pass `character_base`. Before each anchor, inspect all `kind: "character"` assets in `assets.json` and choose the slug that best matches the current outfit, helmet state, pose, or angle. Use `character_base` only as the fallback when no specific `character_*` asset fits the scene.

**Character asset bootstrap (initial setup):** When setting up a new character, do NOT use the original photo directly as `character.png` if it's not 9:16. Generate a clean 9:16 version first using `generate_image_config.py --image-refs <original_photo>`, save the generated version as `character.png`, and keep the original with a different name (e.g., `character_original.png`). This ensures proper aspect ratio for video anchors.

**Multi-variant LoRA testing workflow:** When user wants to test the same scene with different LoRA weights (e.g., Pixar_Toon at 1.5 vs 3.0), do NOT regenerate the anchor — copy the previous post's `video_generation.json` to a new `YYYY-MM-DD_#` folder, change only the LoRA weight(s), and regenerate the video. This saves 2-3 minutes per variant since the anchor already exists.

## Ref-count decision (0 / 1 / 2 / 3)

The Qwen Image Edit Plus 2511 cap is **3 refs**, but the cap is a maximum, not a target. Pick the **smallest** set that locks identity + environment + creature.

| Refs | When | Example |
|------|------|---------|
| **0** | Brand-new look with no reuse; seeding a never-seen-before element. | `--ref-assets` (empty) |
| **1** | Identity-only -- character in a generic or one-off context. | `--ref-assets <best_character_slug>` |
| **2** | Identity + one recurring environment or vehicle/creature. | `--ref-assets <best_character_slug> spaceship_cockpit` |
| **3** | Identity + creature/vehicle + location all need simultaneous locking. | `--ref-assets <best_character_slug> creature_moon_guardian location_lunar_cavern` |

**Character asset aspect ratio handling:**

When your provided character photo has a different aspect ratio than needed for video (e.g., 4:3 photo for 9:16 video), do NOT crop or stretch it. Instead:

1. **Save the original** as `character_original.png` (preserves the exact source).
2. **Generate a new version** using WanGP with `--aspect <target>` and `--image-refs <original>`. This creates a clean, correctly-proportioned character image without distortion.
3. **Set the generated version** as the main `character.png` for the profile.

Example:
```bash
cp /path/to/user/photo.jpg "$CHARACTER_ASSETS_DIR/character_original.png"
python3 "$PROFILE_SKILLS/wan2gp-image-generation/scripts/generate_image_config.py" \
    --prompt "Cinematic medium shot, 9:16. The man (image 1) with short dark hair thinning on top, wire-rimmed glasses, light-colored button-down shirt, confident friendly expression. Seated in office chair. Clean 9:16 composition, natural lighting, realistic photograph style -- Canon EOS R5, 85mm lens." \
    --image-refs "$CHARACTER_ASSETS_DIR/character_original.png" \
    --output-filename character_9x16 \
    --output-dir "$PROFILE_HOME" \
    --aspect 9:16 \
    --seed 742981 \
    --run
cp "$PROFILE_HOME/character_9x16.jpg" "$PROFILE_HOME/character.png"
```

This avoids stretching or cropping that would distort facial features or body proportions. The generated image will have the correct composition and aspect ratio while preserving character identity.

**Golden rule for location assets:**

Location and interior assets must be generated as **clean, character-free plates**. Never bake a character into a location asset -- it kills reusability.

- Prompt explicitly says "no character visible", "empty cockpit", "interior only".
- Pass only related-environment refs for look-and-feel consistency (e.g. `spaceship_exterior` when bootstrapping `spaceship_cockpit`).

## Multi-ref prompting

Describe each reference by index in the prompt, with the slug for auditability:

> The character (image 1, character_base) sits cross-legged inside the cozy Indian teenage bedroom from image 2 (location_indian_home). Warm golden hour light fills the room. She wears a simple cotton kurta with a rose-pink dupatta, a small bindi on her forehead, and a shy smile. Behind her: a wooden shelf with a brass Ganesha idol, string of marigold flowers in the corner, and pink fairy lights along the wall.

**Rules:**
- **Image index order must match `image_refs` order.** If the prompt says "image 1 is the character," then `image_refs[0]` must be the character file.
- **Use slugs for auditability** (not just image descriptions) so the prompt can be traced back to the asset library.
- **First ref is usually `character_base`** for identity locking. Always pass the character file first unless the scene composition demands otherwise.

> **Pitfall: swapping ref order.** If you write "image 1 is the room, image 2 is the character" but pass `--image-refs character.png location.png`, Qwen will put the character IN the room's place and the room as the character. Always verify the order matches the prompt.

> **Pitfall: forgetting character_base.** When the user has a `character.png` base image, ALWAYS use it as the first image ref for character anchors. This locks identity across all posts. Do not generate a new character image from scratch.

> **Pitfall: sticker images cannot be extracted.** Telegram stickers are vector/metadata objects, not embedded images — `browser_get_images` returns 0 hits. If the user sends a character/photo as a sticker, ask them to resend as a **regular image** (no sticker format). Session evidence (2026-05-05): user sent base character as sticker, agent failed to extract image, had to ask for regular photo. Wasted one turn.

## Helper invocations

### Bootstrap a new asset

**Portrait (9:16):**
```bash
python3 "$PROFILE_SKILLS/wan2gp-image-generation/scripts/generate_asset.py" \
    --name spaceship_cockpit \
    --kind location \
    --aspect 9:16 \
    --description "Spaceship cockpit interior -- gold mandala panels, curved viewport, warm amber glow." \
    --prompt "INT. spaceship cockpit. Empty cockpit, no character visible. Curved viewport fills the upper frame showing star-dense space. Panels carry gold mandala detailing. Warm amber instrument glow across the pilot seat and console." \
    --ref-assets spaceship_exterior \
    --tags spaceship interior cockpit \
    --source-post 2026-05-02_1 \
    --run
```

**Landscape (16:9):**
```bash
python3 "$PROFILE_SKILLS/wan2gp-image-generation/scripts/generate_asset.py" \
    --name location_valley_wide \
    --kind location \
    --aspect 16:9 \
    --description "Wide valley landscape -- rolling hills, golden hour, cinematic." \
    --prompt "EXT. wide valley landscape. No character visible. Rolling green hills under golden hour light, distant mountains, dramatic sky." \
    --tags landscape valley exterior \
    --source-post 2026-05-02_1 \
    --run
```

The `--aspect` flag sets both the manifest tag and the render resolution/template automatically. You do NOT need to also pass `--resolution`.

### Remove an asset

```bash
python3 "$PROFILE_SKILLS/wan2gp-image-generation/scripts/remove_asset.py" \
    location_courtyard_outdoor_v2 location_courtyard_outdoor_v3
```

Removes the manifest entry, deletes the `.jpg`/`.png` and co-located `.json` config. Pass `--keep-files` to only remove from the manifest. Use `--list` (optionally with `--kind location`) to see all registered assets before deciding what to remove.

### Per-post anchor

**Portrait (9:16):**
```bash
python3 "$PROFILE_SKILLS/wan2gp-image-generation/scripts/generate_image_config.py" \
    --prompt "Cinematic medium shot. The character (image 1, character_spacesuit_helmet) in their signature suit stands on the cratered lunar surface beside the towering crystalline guardian (image 2, creature_moon_guardian). Earth hangs in the black sky. Harsh sunlight from camera-left." \
    --ref-assets character_spacesuit_helmet creature_moon_guardian \
    --output-filename character_guardian_meeting_anchor \
    --output-dir "$POSTS_DIR/2026-05-02_1" \
    --aspect 9:16 \
    --seed 742981 \
    --run
```

**Landscape (16:9):**
```bash
python3 "$PROFILE_SKILLS/wan2gp-image-generation/scripts/generate_image_config.py" \
    --prompt "Cinematic wide shot. The character (image 1, character_spacesuit_helmet) in their signature suit stands on the cratered lunar surface, the towering crystalline guardian (image 2, creature_moon_guardian) rises to the right. Earth hangs in the black sky. Harsh sunlight from camera-left." \
    --ref-assets character_spacesuit_helmet creature_moon_guardian \
    --output-filename character_guardian_meeting_anchor \
    --output-dir "$POSTS_DIR/2026-05-02_1" \
    --aspect 16:9 \
    --seed 742981 \
    --run
```

**Mandatory flags:**
- `--output-filename` is **required** (not optional).
- `--aspect` is the preferred way to control orientation (`9:16` or `16:9`). It auto-sets resolution and template. You can still pass `--resolution "WxH"` directly to override.
- `--image-refs` takes absolute paths to reference images; `--ref-assets` takes asset slugs from `$CHARACTER_ASSETS_MANIFEST`.
- **`$WAN_APP_DIR` points at the `/app/` subdirectory** of the WanGP install (e.g., `/home/gowrav/pinokio/api/wan.git/app`), not the git repo root. `wgp.py`, `env/bin/python`, and `models/_settings.json` all live inside that `app/` directory.

The helpers auto-pick `I` vs `KI` based on ref count and first-ref aspect, enforce the 3-ref cap, resolve slugs against `assets.json`, promote Qwen's MP4 output to JPG, and write full WanGP-compatible JSON. Agents do not configure these details manually.

## Operational rules

- **Sequential only.** Never run two `wgp.py` jobs at once (24 GB VRAM / OOM risk).
- **3-ref anchors need extended timeout.** Generating anchors with 3 reference images (the cap) is significantly more VRAM-intensive than 2-ref or 1-ref anchors and can timeout at the default 180s wall-clock limit. **Always use `timeout 480` (or higher) when running `generate_image_config.py` with `--ref-assets` specifying 3 slugs.** Example: `timeout 480 python3 "$PROFILE_SKILLS/wan2gp-image-generation/scripts/generate_image_config.py" ... --run`. A 2-ref anchor typically completes in ~3 min; a 3-ref anchor can take ~3.5 min. If it fails with `[Command timed out]` but no output file exists, retry with the longer timeout.
- **Character images may exist on disk but not in manifest.** Before using `--ref-assets <slug>` with character images, always verify the slug is registered in `$CHARACTER_ASSETS_MANIFEST`. Character images generated in a prior session or manually placed may not be registered. Use `cat "$CHARACTER_ASSETS_MANIFEST" | python3 -c "import sys,json; print(list(json.load(sys.stdin)['assets'].keys()))"` to list registered slugs. If missing, register via `generate_asset.py --run` or manually add to `assets.json` before proceeding to anchor generation.
- **Kill orphans.** Before starting a new run: `ps aux | grep wgp.py` and `kill -9` any stray processes (the WanGP web UI can leave hidden processes). **WARNING:** If `kill -9` fails with "Cannot send process signal", the process is in D-state (uninterruptible sleep) and the GPU driver is deadlocked. Do NOT continue — the system is already hanging. Run `nvidia-smi` to confirm; if it hangs, a hard reboot is the only recovery. See `wan2gp-video-generation:references/orphan-process-hang.md` for full case study and prevention checklist.
- **WanGP Python.** When invoking `wgp.py` manually (without `--run`), always use `$WAN_PYTHON` (= `$WAN_APP_DIR/env/bin/python`). System `python3` lacks PyTorch. See [`references/execution-pitfalls.md`](references/execution-pitfalls.md).
- **Verify asset registration before anchor gen.** Before running `generate_image_config.py` with a `--ref-assets <slug>`, confirm the slug is registered in `$CHARACTER_ASSETS_MANIFEST`:
  ```bash
  cat "$CHARACTER_ASSETS_MANIFEST" | python3 -c "import sys,json; print(list(json.load(sys.stdin)['assets'].keys()))"
  ```
  If the file exists on disk but is missing from the manifest (common after session restarts or interrupted runs), register it via `generate_asset.py --run` or write a small Python registration helper. A missing entry fails with `unknown asset '<slug>'`.
- **Temporary / one-off assets.** When the user says "do not save any asset" or "it's a temp creation", skip `generate_asset.py --run` entirely. Generate the image directly with `generate_image_config.py --run` into the post folder; do NOT add to `$CHARACTER_ASSETS_MANIFEST`.
- **Use batch orchestration scripts for multi-reel generation.** When generating many anchors or assets in sequence, write a Python orchestration script and run it via `terminal(background=true)`. Always invoke WanGP helpers with `$WAN_PYTHON`; only use system Python for plain manifest reads. See `references/batch-orchestration.md` for the complete pattern.
- **Env var sanity.** If a helper script errors with `[env] required env var ... not set`, the agent shell did not source `$PROFILE_ROOT/.env`. Recover with `set -a; source $PROFILE_ROOT/.env; set +a` and retry. The strict requirement exists because `Path.home()` inside Hermes maps to `$PROFILE_HOME`, so silent fallbacks to `~/assets/...` previously landed on the wrong files.

- **Qwen model produces hyper-perfect AI-looking outputs for natural scenes.** Qwen Image Edit Plus 2511 naturally gravitates toward saturated colors, crystal-clear water, perfectly-distributed lighting, and uniform textures when generating nature/outdoor/location assets. The result looks like AI art, not a photograph. **Counter-strategy for realistic look:**
  - Explicitly instruct "documentary photography, natural colors, slight film grain, nothing overly saturated or perfect — like a real photograph taken by a nature photographer"
  - Add camera specs: "Shot on Canon EOS R5, 35mm lens, natural light" (specific camera info helps the model think photographically)
  - Describe imperfections: "muddy and earthen banks with scattered rocks, dead leaves, small patches of grass", "rough bark texture", "not crystal-perfect water", "gentle ripples and slight reflection, not crystal-clear"
  - Explicitly negate: "No fantasy elements, no magical glow, nothing overly saturated"
  - Even with these cues, the output may still lean toward AI-perfect — be prepared to iterate with more aggressive imperfection cues or consider that Qwen may not be capable of pure photorealism for nature scenes.
  - **Session evidence (2026-05-05):** First attempt with "photorealistic" prompt was rejected as "not that great." Second attempt with "documentary photography, Canon EOS R5, 35mm lens" prompt was still rejected as leaning too AI-perfect (hyper-clarity, bloom lighting, texture uniformity). Two iterations needed, quality still debatable.

## Supporting references

- [`references/qwen-realism-challenge.md`](references/qwen-realism-challenge.md) — Qwen's inherent hyper-perfect aesthetic and workarounds for documentary/photorealistic style.

- **Aspect ratio mismatch when regenerating existing assets.** When you regenerate an asset that already exists in `assets.json`, the `--aspect` flag sets the new aspect ratio but old files with the old aspect ratio may still exist on disk (renamed with `(2)` suffix or backup names). **Always check for stale files after regeneration:**
  - After `generate_asset.py --force --run`, check the assets directory for files matching the slug name that aren't the expected `slug.jpg` and `slug.json`
  - Example (2026-05-05): Generated `location_jungle_river` as 16:9 but needed 9:16. Had to manually rename old files, remove manifest entry, then regenerate with correct aspect. Lost ~4 minutes to cleanup.
  - **Rule:** After regenerating with `--force`, immediately `ls $CHARACTER_ASSETS_DIR | grep <slug>` to verify only the correct files exist. If unexpected variants remain, clean them up before proceeding.

- **Aspect ratio must match video needs.** When generating a location asset that will be used as a video background, ensure the aspect matches the video output. Video reels are 9:16 (720x1280), but location assets are often generated 16:9 (1280x720) by default. **Always check `--aspect` before running** — a mismatched aspect means the anchor composition won't work for the reel format.
