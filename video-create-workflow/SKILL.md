---
name: video-create-workflow
description: Per-post orchestration for one anchor image + one ~20 s video, 9:16 or 16:9. Routes to wan2gp-image-generation and wan2gp-video-generation; uses wan2gp-movie-pipeline for multi-scene stories.
version: 3.0.0
author: Hermes
license: MIT
metadata:
  hermes:
    tags: [video, character-video, workflow]
    related_skills: [wan2gp-image-generation, wan2gp-video-generation, wan2gp-movie-pipeline]
---

# Per-Post Video Workflow

One post = one anchor image + one ~20 s video in `$POSTS_DIR/<YYYY-MM-DD_#>/`.

## Route first

| Ask | Skill |
|-----|-------|
| Single reel / 1-2 independent shots | this skill |
| 3+ connected scenes (movie, short film, narrative) | `wan2gp-movie-pipeline` |
| Image-only work (assets, base character, anchors) | `wan2gp-image-generation` |
| Video-only work (LTX-2.3 prompt deep-dive, tools) | `wan2gp-video-generation` |
| User rejects AI video / wants 3D | Blender (`/snap/bin/blender`) |

## Use the tools, not bash

All operations are scripts in `$PROFILE_SKILLS/video-create-workflow/scripts/`. Read `--help` for args. Never hand-write the equivalent shell.

| Job | Tool |
|-----|------|
| Cold-start dirs + seed `assets.json` | `bootstrap_profile.py` |
| New post folder (auto-indexed) | `new_post.py [--tag T] [--movie --tag T]` |
| List posts | `list_posts.py [--with-status] [--json]` |
| Find half-done posts (anchor without video, config without mp4) | `incomplete_posts.py` |
| Delete a post | `remove_post.py <slug>` |
| Show / filter registered assets | `list_assets.py [--kind K] [--check]` |
| Register an on-disk image (no re-render) | `register_asset.py --name ... --kind ... --aspect ... --path ... --description "..."` |
| Find media files (mp4/jpg/png) | `find_media.py --ext mp4 [--name '*anchor*']` |
| Wait for GPU idle (no wgp.py running) | `gpu_wait.py [--timeout SEC]` |
| Kill stray wgp.py processes | `kill_orphans.py [--dry-run]` |
| Compress video for Telegram (~3-5 MB) | `compress_video.py <input.mp4>` |
| Prune sliding-window partial mp4s | `cleanup_windows.py <post-dir>` |
| Append a journey entry (atomic) | `journey_append.py --n N --date ... --slug ... --aspect ... --location ... --beat ... --anchor-file ... --reel-file ... [--assets-used a b c]` |
| Rewrite `<Character> State:` line | `memory_update.py --character ... --prev ... --current ... --last-beat ... --next-hint ... --active-assets a,b,c` |

`$PROFILE_ROOT/.env` is **not** auto-sourced. Run `set -a; source $PROFILE_ROOT/.env; set +a` once per shell. Scripts fail loudly if `POSTS_DIR`, `MEMORY_FILE`, `JOURNEY_FILE`, `CHARACTER_ASSETS_DIR`, `CHARACTER_ASSETS_MANIFEST`, `CHARACTER_BASE`, `WAN_APP_DIR`, `PROFILE_HOME`, or `PROFILE_SKILLS` is missing.

**Rule for every GPU call (image gen, video gen, movie pipeline): launch as `terminal(background=true, notify_on_complete=true)`.** A new user message kills a blocking shell; it does NOT kill a Hermes background task.

## Anchor consistency (mandatory)

**The anchor image is frame 0 of the video.** Whoever you want visible in the shot — main character, secondary characters, creatures — MUST appear in a single composite anchor image, otherwise LTX-2.3 will invent new random faces mid-shot.

- Pick the frame where ALL characters are simultaneously visible (start frame, end frame, or first intermediate). Compose the anchor at that moment.
- For 2-3 characters in one shot, use Qwen Image Edit Plus 2511 with one ref per character (see `wan2gp-image-generation`). Reference each by index in the prompt: "Alice (image 1)... Bob (image 2)...". Order of `--image-refs` must match the prompt's image-N labels.
- For dual keyframing (different opening / closing composition), use `generate_video_config.py --image-start ... --image-end ...` (auto-adds `E` to `image_prompt_type`). For more than two keyframes, see `--image-refs` + `--frames-positions` in the same script.
- Re-read SOUL.md for outfits, colors, accents BEFORE choosing the character ref — pick the `character_*` slug whose wardrobe matches this scene, falling back to `character_base`.

## Model preference

- **First choice for any image: Flux 2 Klein 9B** (`generate_image_config.py --template flux-klein --steps 8 --guidance-scale 2.5`). Faster (~35 s) and more realistic skin/hair than Qwen.
- **Use Qwen Image Edit Plus 2511 only when you need multi-ref compositing** (2-3 reference images for character + location + creature). Flux is single-ref only.
- **Default video model**: `--model distilled-1.1` (8 steps, auto-LoRAs). Use `--model gguf` for fastest iteration with no compile.

## Per-post protocol

1. `bootstrap_profile.py` (idempotent; safe to call every time).
2. `incomplete_posts.py` — finish or delete leftovers before starting new work.
3. Confirm aspect with the user if unclear: 9:16 (reel) vs 16:9 (YouTube). Pass `--aspect` to both image and video scripts.
4. Confirm concept (1-2 sentences) and physics (where is the character; what happens after) BEFORE rendering.
5. `new_post.py [--tag <slug>]` → returns `<post-dir>`.
6. Pick refs (smallest set that locks identity + environment). Verify each slug with `list_assets.py --check`. Bootstrap any missing assets via `wan2gp-image-generation`.
7. Author the anchor — reuse an existing `character_*` asset by copying it into `<post-dir>` if the outfit/pose already matches, otherwise call `generate_image_config.py --generate-and-run` (Flux first, Qwen for multi-ref).
8. Author the video — see `wan2gp-video-generation` for the LTX-2.3 prompt rules and tools. Build the config first with `--generate-only`, then launch:
   ```
   terminal(command="python3 $PROFILE_SKILLS/wan2gp-video-generation/scripts/generate_video_config.py --run-json <post-dir>/video_generation.json", background=true, notify_on_complete=true)
   ```
   Always background + `notify_on_complete=true` for any GPU call — a new user message kills a blocking shell, but NOT a Hermes background task. Monitor with `monitor_video_gen.py <post-dir>`.
9. `cleanup_windows.py` if `video_length > sliding_window_size`, then `compress_video.py`. Deliver.
10. `journey_append.py` and `memory_update.py` AFTER delivery is confirmed.

## Anchor / video prompt split

- **Anchor prompt** = WHAT the frame shows: character, outfit, location, lighting, composition. Detailed and static.
- **Video prompt** = HOW it MOVES: camera move, action, dialogue in quotes, audio direction, temporal connectors (as / then / while / before / after). Open with ONE tableau sentence matching the anchor (INT/EXT, pose, light); after that PURE motion.
- Never re-describe the character or wardrobe in the video prompt — the anchor already shows it.
- Default no hard cuts in per-post I2V (no `CUT TO:`, no `JUMP CUT`). Evolve the frame with camera moves. Movies use `CUT TO:` differently — see `wan2gp-movie-pipeline`.

## Delegation

- Image craft → [`wan2gp-image-generation`](../wan2gp-image-generation/SKILL.md)
- Video craft, LTX-2.3 prompt guide, tools list → [`wan2gp-video-generation`](../wan2gp-video-generation/SKILL.md)
- Multi-scene stories → [`wan2gp-movie-pipeline`](../wan2gp-movie-pipeline/SKILL.md)
- Voice, persona, accent → SOUL.md
