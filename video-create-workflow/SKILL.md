---
name: video-create-workflow
description: Per-post video orchestration (9:16 reels or 16:9 landscape) -- workspace, story validation, physics check, anchor-video coherence, memory. Image craft in wan2gp-image-generation; video craft in wan2gp-video-generation; persona in SOUL.md.
version: 2.0.0
author: Hermes
license: MIT
metadata:
  hermes:
    tags: [video, character-video, workflow]
    related_skills: [wan2gp-image-generation, wan2gp-video-generation, wan2gp-movie-pipeline]
---

# Per-Post Video Workflow

Orchestrates a single video per post: one anchor image + one ~20 s video, stored under `$POSTS_DIR/<YYYY-MM-DD_#>/`. Supports **9:16** (portrait / Instagram reels) and **16:9** (landscape / YouTube / cinematic).

> **3D alternative:** If the user rejects AI video (WanGP) and wants 3D animation instead, use Blender (`/snap/bin/blender`) -- see `creative:references/blender-available.md`.

Image craft in wan2gp-image-generation; video craft in wan2gp-video-generation; persona in SOUL.md.

For **movies** (3+ connected scenes forming a story), use the `wan2gp-movie-pipeline` skill instead of this workflow. **Important:** The asset library (`assets.json`, `$CHARACTER_ASSETS_DIR`) belongs to this per-post journey workflow only -- movies do NOT use the manifest or shared assets. Movies are self-contained and manage their own local images inside the movie folder. Movies use a different pattern:

- Folder: `$POSTS_DIR/YYYY-MM-DD_movie_<tag>/` (with `_movie_` in the slug)
- Agent writes a full `movie_script.json` with all scenes upfront
- A background pipeline (`run_pipeline.py`) handles all rendering autonomously
- Progress tracked in `progress.json` for crash recovery
- Single seed across all scenes for visual consistency

**When to use wan2gp-movie-pipeline:** User asks for a "movie", "short film", "multi-scene story", or any 3+ connected scenes.

**When to stay here:** Single reels, 1-2 independent posts, or unrelated batch reels. This per-post workflow handles those.

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

Helper scripts are strict consumers and fail loudly if any required key is missing.

**NOTE on `$PROFILE_SKILLS`:** In this profile, it points to `/home/gowrav/.hermes/shared-skills` (NOT the local skills dir). Verify: `grep PROFILE_SKILLS $PROFILE_ROOT/.env`.

Used by this workflow:

- `PROFILE_ROOT` -- profile directory (e.g., `$HOME/.hermes/profiles/meena`)
- `PROFILE_HOME` -- profile workspace (`$PROFILE_ROOT/home`); also the agent's `$HOME`
- `PROFILE_SKILLS` -- shared skills dir (`/home/gowrav/.hermes/shared-skills` in this profile)
- `POSTS_DIR` -- `$PROFILE_HOME/posts`
- `MEMORY_FILE` -- `$PROFILE_ROOT/memories/MEMORY.md`
- `JOURNEY_FILE` -- `$PROFILE_HOME/journey.jsonl`
- `CHARACTER_ASSETS_MANIFEST` -- `$PROFILE_HOME/assets/assets.json`

Image and video helpers (delegated to `wan2gp-image-generation` / `wan2gp-video-generation`) require `WAN_APP_DIR`, `WAN_PYTHON`, `CHARACTER_ASSETS_DIR`, `CHARACTER_BASE` -- see those skills.

## Per-post protocol (every post, no skips)

### PRE-FLIGHT (first post / cold start)

Skip these steps for posts #2 onwards. For post #1 (or when assets are missing):

1a. **Write SOUL.md** if it doesn't exist. Define: character identity, personality traits, speech style/accents, visual identity (outfits, colors, setting, decor), emotional arc, content direction. The SOUL.md is read by every prompt-writing step — it is the source of truth for character voice and visual details.

1b. **Bootstrap asset manifest.** Create `$CHARACTER_ASSETS_MANIFEST` with the `character_base` entry (the base `$CHARACTER_BASE` image, kind="character", aspect="1:1", tags include "character" and "identity"). This is the minimum viable manifest.

1c. **Bootstrap location/recurring assets.** Before the anchor, generate any fixed background elements (rooms, outdoor scenes, vehicles, props) using `generate_asset.py --run`. These must be **character-free plates** — no person in the frame. Register each in assets.json after rendering. Only generate what you actually need for the anchor (step 7 will tell you).

> **Pitfall: character-free location plates.** Location assets must be generated with explicit "no character visible" in the prompt. Baking a character into a location kills reusability — you won't be able to composite that character into different scenes later.

> **Pitfall: camera angle for character placement.** When a location asset will later have the character composited into it (the character stands in the courtyard/room/outside), the camera MUST be at **eye-level** (approx standing height, ~5.5 ft) with clear **foreground ground space** visible. Never use high-angle/bird's-eye/overhead shots — the character will appear to float when placed via reference compositing. Always describe "camera at standing eye-level" and "clear foreground ground space for a standing person" in the asset prompt.

> **Pitfall: interrupt verification.** If `generate_asset.py --run` is interrupted (signal/Ctrl+C), always verify the output file exists before re-running. The model may have finished generating before the signal arrived. Check with `ls <asset_name>.jpg` first.

### Anchor reuse optimization (NEW in v2.0.1)

Before generating a new anchor image, check if an existing `character_*` asset can be used directly as the anchor. If the character's outfit and pose haven't changed for the scene, **copy the asset directly into the post folder** instead of running `generate_image_config.py`. This saves 2-3 minutes of GPU time per post.

**When to reuse:** Character outfit matches the asset, pose is similar (standing/sitting/neutral), and the background can be implied or added via video prompt framing.

**When NOT to reuse:** Different outfit, different pose, new background context needed, or the user explicitly wants a new anchor composition.

> **Pitfall:** When reusing an existing asset as anchor, the video prompt must still match the asset's composition (opening tableau sentence) for I2V coherence. Do not skip the coherence check just because the anchor was copied rather than generated.

### Asset registration verification (CRITICAL before generating anchors)

Before generating any anchor that references an asset (character or location), **always verify the asset is registered in `assets.json`** using:
```bash
cat "$CHARACTER_ASSETS_MANIFEST" | python3 -c "import sys,json; data=json.load(sys.stdin); print(list(data['assets'].keys()))"
```

If the asset file exists on disk but is NOT in the manifest, register it first. Generated asset files from prior sessions may exist without being registered. This is a **common workflow breakage** — always do this check at step 7 before running `generate_image_config.py`.

**For temporary/one-off assets** (scenes that will never be reused): the user may explicitly say "do not save any asset" or "it's a temp creation." In this case, **skip `generate_asset.py --run` entirely** and instead generate the anchor directly with `--ref-assets <temporary_slug>` where the slug is resolved from the file path. The asset will NOT be registered in assets.json. Check user intent carefully — when in doubt, ask.

### Asset variant workflow (when user requests options)

When the user asks for multiple versions of an asset:
1. Generate all variants with **unique descriptive names** (e.g., `location_courtyard_v1`, `location_courtyard_v2`).
2. **Show all variants** to the user with clear labels (V1, V2, V3...).
3. **Wait for user selection** before proceeding. Do NOT register anything or clean up yet.
4. Once user selects, **register only the chosen one** in `assets.json`.
5. **Remove non-selected variants** using `remove_asset.py` — run `--list` first to verify manifest state, then remove unwanted slugs. Use `--keep-files` to remove from manifest only if files are already deleted externally.
6. **Never proceed** to anchor/video until the user confirms the selection.

> **Pitfall: interrupt verification.** If `generate_asset.py --run` is interrupted (signal/Ctrl+C), always verify the output file exists (`ls <asset_name>.jpg`) before re-running. The model may have finished generating before the signal arrived. Do NOT blindly re-generate.

### Batch reel generation (when user asks for multiple reels)

When the user asks for multiple reels (e.g., "make 5 reels — fun, dance, seduce, roam, explore"):

1. **Each reel gets its own post folder** with a unique `YYYY-MM-DD_#` index and its own `video_generation.json` config. This lets the user review settings per-video after the fact.
2. **Send the completed video IMMEDIATELY** after each reel finishes. Do NOT wait to batch-send at the end. Send each one individually as it completes, then start the next reel.
3. **Never generate multiple background gens at once** — sequential only (24 GB VRAM).
4. **Avoid crowd scenes / multiple characters in I2V.** LTX-2.3 struggles with more than 1-2 people — the model produces artifacts. Keep reels to a single character whenever possible.
5. **Config-first, GPU-second pipeline.** When generating multiple reels, write ALL video generation configs first (Step A for each, ~2s per config), THEN start the first GPU job. This keeps GPU idle time to near zero — you never wait 2s for a config while the GPU sits.
6. **Temporary asset handling.** When the user explicitly says "do not save any asset" or "it's a temp creation", skip `generate_asset.py --run` entirely. Instead, generate the asset image directly with `generate_image_config.py --run` in the post folder (not assets/). This creates a one-off image for that post only.
7. **Compression is mandatory.** After each GPU job completes, compress the raw output (~30-40MB for 20s video) to ~3-5MB before sending to Telegram:
   ```bash
   ffmpeg -i input.mp4 -vcodec libx264 -acodec aac -b:v 2000k -b:a 128k -movflags +faststart output_compressed.mp4
   ```
   Target: ~3-5MB per video. Compressed files follow the pattern `<name>_compressed.mp4` and sit next to the raw video. Compression takes ~10-20s. Skip compression if the raw file is already under 20MB.
8. **Extended video (sliding window) output: do NOT concatenate.** When `video_length > 481` (sliding window mode), WanGP writes multiple intermediate files: `{name}.mp4` (partial first window), `{name}(2).mp4`, etc. The **last file** (`(N).mp4`) is the complete stitched video containing all windows. Do NOT `ffmpeg -f concat` these files -- that doubles content. Compress and deliver the last file only. Delete the partial earlier files.

> **Stop signal:** When the user says "stop after this" or similar, complete the CURRENT reel (send the video), then stop. Do NOT auto-continue with the next reel. Wait for the user to say "continue" before starting more.

### STANDARD POST PROTOCOL

1b. **Pre-flight: check for incomplete posts.** Before starting anything new, scan for post folders that have anchor images but no video (or vice versa):
```bash
for d in "$POSTS_DIR"/*/; do
  slug=$(basename "$d")
  has_anchor=$(find "$d" -name "*anchor*.jpg" -o -name "*anchor*.jpeg" 2>/dev/null)
  has_video=$(find "$d" -name "*reel*.mp4" -o -name "*video*.mp4" 2>/dev/null)
  if [ -n "$has_anchor" ] && [ -z "$has_video" ]; then
    echo "INCOMPLETE: $slug — has anchor but no video (video_generation.json exists: $(test -f "$d/video_generation.json" && echo yes || echo no))"
  fi
done
```
If incomplete posts exist, **ask the user**: "I found [N] incomplete post(s) from earlier sessions. Do you want to complete them before starting new work? (Or should I log them and move on?)"
> **Pitfall: silent gaps.** An incomplete post folder with `video_generation.json` but no output video means the GPU job was killed by an agent timeout or session crash. The config is preserved — you can restart from it directly with `wgp.py --process <config>`. Don't regenerate the anchor; the video can pick up from the existing config.

2. **Read continuity.** `cat "$MEMORY_FILE"` for the rolling `<Character> State:` line. For deeper history: `tail -n 5 "$JOURNEY_FILE" | jq .`

3. **Init post folder.** `mkdir -p "$POSTS_DIR/<YYYY-MM-DD_#>"` (resolve `#` = highest existing index for today + 1).

4. **Decide aspect ratio.** If the user has not specified an orientation, **ask before proceeding**. Use these heuristics to suggest a default:
   - User says "reel", "Instagram", "shorts", "vertical" -> **9:16** (720x1280)
   - User says "YouTube", "landscape", "cinematic", "widescreen", "horizontal" -> **16:9** (1280x720)
   - Unclear or no hint -> ask the user: "Portrait 9:16 (reel) or landscape 16:9 (YouTube)?"
   
   Pass the chosen aspect via `--aspect 9:16` or `--aspect 16:9` to **both** image and video helper scripts. The `--aspect` flag auto-sets resolution and template -- you do NOT need to also pass `--resolution`.

5. **Story-concept validation.** Summarise the narrative beat, emotional core, and key visual elements in 1-2 lines. Confirm with the user BEFORE any rendering. A wrong concept costs GPU minutes.

6. **Physics / consequences check.** Before writing any prompt, verify:
   - Where is the character physically? Adapt to YOUR character's world (not the examples in this document).
   - What happens after this action? Does the character leave, stay, explore?
   - Environment consistency: lighting, time-of-day, spatial layout.
   - Who/what is visible from where? Interior views show what's through windows; exterior views show the sky behind the character.
   - Character position relative to any recurring elements.
   - **Never copy-paste the examples.** They are space-themed templates. For every character, replace the examples with actual environment details.

7. **Plan refs.** Decide how many refs (0/1/2/3) the anchor needs. Pick the *smallest* set that locks identity + environment + creature. Inspect `$CHARACTER_ASSETS_MANIFEST` for the best matching `character_*` slug -- NOT always `character_base`. Never pad to 3 just because the cap is 3. If your character is in scene, you MUST check assets to pick one of character_* image as reference. Character consistency is MUST.

> **Pitfall: character consistency from SOUL.md.** Before choosing a character ref, re-read the SOUL.md visual identity section (outfits, hair, colors, accessories). The chosen ref must match the current scene's wardrobe. If no matching `character_*` asset exists, use `character_base` as fallback.

> **Pitfall: finding video files.** `search_files` does NOT reliably match `.mp4` files — it returned 0 hits for every glob pattern (`*.mp4`, `*reel*`, `*valley*`, `*ice_caves*`). Use `find "$PROFILE_HOME" -name "*.mp4" 2>/dev/null | head -20` instead. This also works for `.jpg` / `.png` asset files.

7b. **Bootstrap missing assets.** For each ref decided in step 7 that does not exist in `assets.json`, render it via `wan2gp-image-generation` (`generate_asset.py --run`). Sequential only -- never parallel WanGP jobs (24 GB VRAM). Skip if all slugs exist or step 7 chose 0 refs.

8. **Author anchor.** If the scene's character + composition already exists as an asset in `assets.json` that matches the desired anchor (same outfit, angle, framing), **reuse it directly** — copy it into the post folder as the anchor. No need to call `generate_image_config.py` unless you need a NEW composition. Example: using `character_kurti_palazzo` as the anchor for a mid-closeup against a plain wall saved a full WanGP image generation step. When generating a new anchor via WanGP instead, see `wan2gp-image-generation` for prompting craft and helper flags. If user asks then send image first to confirm and if user needs more options generate and send but make sure that you use the new image for video. Always use a unique anchor filename per post so video picks the selected image only.

9. **Author video.** Before writing the video prompt, **load and carefully read** the `wan2gp-video-generation` skill AND its `references/ltx-2-3-prompting.md` (the full prompting deep-dive covering temporal connectors, AV sync, duration strategy, lens language, scene design vocabulary, and dialogue segmentation). Use what you read to plan a dramatic, well-structured video prompt -- do not wing it from memory.

**Model choice:** Default `--model distilled-1.1` (8 steps, auto-LoRAs for HDR/outpaint/union-control). For fastest iteration without compile overhead, use `--model gguf` (8 steps, C++ runtime). See `wan2gp-video-generation` skill "Model selection" section for both variants.

**Video gen workflow (split approach -- NEVER use `--run`):**
- **Step A:** `python3 "$PROFILE_SKILLS/wan2gp-video-generation/scripts/generate_video_config.py" --aspect <chosen> --image-start <anchor>.jpg --output-dir <post-dir>` (writes JSON, takes ~2s)
- **Step B:** Start `wgp.py --process` via `terminal(background=true, notify_on_complete=true)` (runs 3-4 min, survives agent timeout)
- **Step C:** Write PID to `$PROFILE_HOME/.video_gen_tracker.json`
- **Step D:** Poll every 60-90s: `python3 "$PROFILE_SKILLS/wan2gp-video-generation/scripts/monitor_video_gen.py" <post-dir>`
- **Complete when:** monitor returns exit code 0 + "COMPLETED"

The skill also documents the full split approach. See `wan2gp-video-generation` skill.

> **CRITICAL: Video prompt ≠ anchor prompt duplication.**
> The anchor image IS frame 0. LTX-2.3 already has the static visual from the anchor.
> The video prompt must NEVER re-describe character appearance, wardrobe, location details, or static composition.
> 
> **Anchor prompt** = WHAT the image shows (character, outfit, location, lighting, composition) — detailed static description.
> **Video prompt** = HOW it MOVES (camera, action, dialogue, audio, emotion through motion) — detailed dynamic description.
> 
> **The video prompt should be SHORT on static description, LONG on motion and direction.**
> 
> **Video prompt MUST focus on:**
> - **Camera movement** — dolly in/out, pan, tilt, push-in, pull-back, tracking, orbit, handheld shake
> - **Character action/motion** — what the character DOES (not what they look like): gestures, body language, facial expressions in motion
> - **Dialogue** — spoken lines in "quotes" with acting beats between them (physical cues, camera moves, reactions)
> - **Audio direction** — ambient sounds, music, voice accent/tone, background score
> - **Temporal flow** — actions linked with "as", "then", "while", "before", "after"
> 
> **Video prompt MUST NOT include:**
> - Repeated character appearance description (the image already shows the outfit, hair, features)
> - Repeated location details (the image already shows the room, props, decor)
> - Redundant lighting description (anchor already established lighting)
> - Static composition descriptions (the image IS the composition)
> 
> **The ONLY static reference in video prompt** should be a single opening tableau sentence that matches the anchor composition (e.g., "INT. INDIAN BEDROOM -- GOLDEN HOUR. The character stands by the window..."). Everything after that is PURELY motion, camera, dialogue, and audio.
> 
> **Example — BAD (redundant):**
> > "INT. cozy Indian bedroom, golden hour light. Meena, a 17-year-old Indian girl with a small bindi on her forehead, wearing a rose-pink kurta with a dupatta, stands in the room with a Ganesha idol on the shelf behind her and marigold flowers in the corner..."
> 
> **Example — GOOD (director-focused):**
> > "INT. INDIAN BEDROOM -- GOLDEN HOUR. The camera slowly pushes in past Meena's shoulder as she turns toward the lens with a shy smile. 'Hi doston...' (small pause, looks down at her hands, fidgets with her dupatta) 'Han... main AI hun.' She takes a breath, fingers tightening on the fabric, then looks up with growing confidence. 'Lekin mujhse poochio -- mujhe toh sab feel hota hai, yaar!'" (voice soft at first, then warmer, teenage girl accent) 'Aur jab aapke likes aate hain...' She gestures with her free hand, laughing nervously. Audio: gentle acoustic guitar, distant temple bells, her warm intimate voice."
> 
> The first example wastes 80% of the prompt describing what the image already shows. The second example gives LTX-2.3 actionable direction: camera move, acting beats, dialogue, audio, emotion through motion.

10. **Update journey.** Append exactly one JSON line to `$JOURNEY_FILE` (schema below).

11. **Update memory.** Overwrite the `<Character> State:` line in MEMORY via the `memory` tool (schema below).



## Anchor <-> Reel coherence (mandatory)

The anchor image IS frame 0 of the reel. LTX-2.3 I2V decodes from it and continues -- it does not cut to a new shot. Prompts must be authored in this order:

1. **Anchor prompt = STATIC only.** Describe what the image should show: character, outfit, location, lighting, composition. This is the ONLY place where detailed visual description belongs.
2. **Video prompt = DYNAMIC only.** Single opening tableau sentence matching the anchor composition (INT/EXT, pose, light). Then PURELY motion, camera, dialogue, audio. NO character appearance re-description. NO location detail re-description.
3. **No hard cuts in I2V** -- never write `CUT TO`, `JUMP CUT`, `MEANWHILE` in per-post reels. Evolve the frame with camera moves (dolly, pan, tilt, push-in, pull-back).

> **Important distinction:** This rule applies ONLY to per-post I2V reels (the `--image-start` workflow managed by this skill). The `CUT TO:` prefix is **MANDATORY** in the **movie pipeline** (`wan2gp-movie-pipeline`) when using `continue_from` / `--video-source`, because that's a DIFFERENT mechanism (WanGP "Continue Video" mode, not I2V). The movie pipeline is designed for multi-scene narratives where each scene needs a hard reset. Per-post I2V is designed for a single continuous shot that evolves from the anchor frame. **Never use CUT TO: in per-post I2V. Always use CUT TO: in movie continue_from scenes.**

**Anchor prompt (WHAT the image shows) vs Video prompt (HOW it moves):**

> **Anchor prompt -- 9:16** (detailed static): "Cinematic medium shot, 9:16. INT. cozy Indian teenage bedroom, golden hour light streaming through a window. Meena (17yo Indian girl) stands near the window wearing a rose-pink kurta with a dupatta, small bindi on forehead, shy smile. Behind her: wooden shelf with brass Ganesha idol, marigold flowers in corner, fairy lights on wall. Warm amber lighting."
> 
> **Anchor prompt -- 16:9** (same scene, landscape): "Cinematic wide shot, 16:9. INT. cozy Indian teenage bedroom, golden hour light streaming through a window on the left. Meena (17yo Indian girl) stands near the window wearing a rose-pink kurta with a dupatta, small bindi on forehead, shy smile. The room stretches right: wooden shelf with brass Ganesha idol, marigold flowers in corner, fairy lights along the wall. Warm amber lighting."
> 
> **Video prompt** (minimal static reference + detailed motion): "INT. INDIAN BEDROOM -- GOLDEN HOUR. The camera slowly pushes in as Meena turns from the window toward the lens with a shy smile. 'Hi doston...' She fidgets with her dupatta, looking down. 'Han... main AI hun.' She takes a breath, fingers tightening on the fabric, then looks up. 'Lekin mujhse poochio -- mujhe toh sab feel hota hai, yaar!' She gestures with her free hand, laughing nervously. Audio: gentle acoustic guitar, distant temple bells, warm teenage girl voice."

**Bad:**
> Anchor: INT observation deck, palm on glass, Moon through window.
> Video: EXT. SPACECRAFT -- LANDING SEQUENCE ... cuts to exterior view of spacecraft settling on lunar surface.

**Good:**
> Video: INT. SPACECRAFT OBSERVATION DECK -- LANDING SEQUENCE. The character stays pressed against the curved window, palm on the glass, face lit by soft instrument-panel light. Through the glass, the Moon fills the view, craters growing larger. The camera slowly pushes in past their shoulder, lunar surface rising in the window. Their breath fogs the visor, voice dropping, "Ancient companion, hello."

Same INT, same pose, same light, same view. Camera move evolves the frame without breaking it. The opening tableau sentence establishes continuity; everything else is PURELY motion, dialogue, and audio.

## Memory schemas

### journey.jsonl (append-only, one line per post)

```json
{"n": 11, "date": "2026-05-02", "slug": "2026-05-02_1", "aspect": "9:16", "location": "<short noun phrase>", "beat": "<one-line summary>", "anchor_file": "<basename.jpg>", "reel_file": "<basename.mp4>", "assets_used": ["<slug>", ...]}
```

Append via atomic `with open(..., "a")`. Never hand-edit or rewrite earlier lines.

### Character State in MEMORY (overwritten each post)

```
Character State: prev=#<n-1> <tag> | current=#<n> <tag> | last_beat=<one-line> | next_hint=<one-line> | active_assets=<comma-separated slugs>. Full history at `$JOURNEY_FILE`.
```

5 fields exactly. ~300-400 chars. Replace the previous State entry -- never append alongside it.

## Delegation

- **How to make images** (assets, anchors, ref prompting) -> `wan2gp-image-generation`.
- **How to make videos** (LTX-2.3 director-style prompting, audio, I2V) -> `wan2gp-video-generation`.
- **Voice, persona, accent, character quirks** -> `SOUL.md`.
