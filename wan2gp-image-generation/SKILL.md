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

All paths come from `$PROFILE_ROOT/.env`, which is auto-sourced into agent shells. The helper scripts are strict consumers and will exit with `[env] required env var ... not set` if any required key is missing. Recovery: `set -a; source $PROFILE_ROOT/.env; set +a`.

Used by this skill:

- `PROFILE_HOME` -- profile workspace (also `$HOME` for the agent)
- `PROFILE_SKILLS` -- `$PROFILE_ROOT/skills`; used in command examples
- `POSTS_DIR` -- `$PROFILE_HOME/posts`
- `WAN_APP_DIR` -- WanGP app dir (contains `wgp.py`, `env/bin/python`, `defaults/`)
- `WAN_PYTHON` -- `$WAN_APP_DIR/env/bin/python` (override interpreter)
- `CHARACTER_ASSETS_DIR` -- `$PROFILE_HOME/assets`
- `CHARACTER_ASSETS_MANIFEST` -- `$CHARACTER_ASSETS_DIR/assets.json`
- `CHARACTER_BASE` -- `$PROFILE_HOME/character.png`

Always pass **absolute paths** to `--output-dir`, `--assets-dir`, and `--ref-assets`. Never pass `~/.hermes/...` as a relative path.

## Asset library

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

## Pick the best character ref

Do NOT always pass `character_base`. Before each anchor, inspect all `kind: "character"` assets in `assets.json` and choose the slug that best matches the current outfit, helmet state, pose, or angle. Use `character_base` only as the fallback when no specific `character_*` asset fits the scene.

## Ref-count decision (0 / 1 / 2 / 3)

The Qwen Image Edit Plus 2511 cap is **3 refs**, but the cap is a maximum, not a target. Pick the **smallest** set that locks identity + environment + creature.

| Refs | When | Example |
|------|------|---------|
| **0** | Brand-new look with no reuse; seeding a never-seen-before element. | `--ref-assets` (empty) |
| **1** | Identity-only -- character in a generic or one-off context. | `--ref-assets <best_character_slug>` |
| **2** | Identity + one recurring environment or vehicle/creature. | `--ref-assets <best_character_slug> spaceship_cockpit` |
| **3** | Identity + creature/vehicle + location all need simultaneous locking. | `--ref-assets <best_character_slug> creature_moon_guardian location_lunar_cavern` |

## Golden rule for location assets

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
