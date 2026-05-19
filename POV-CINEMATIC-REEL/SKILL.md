---
name: POV-CINEMATIC-REEL
description: Generate vertical POV cinematic reels using WanGP — Flux Klein for anchors, LTX-2.3 for video. Multi-scene chain with sliding window.
version: 1.0.0
author: Hermes
license: MIT
metadata:
  hermes:
    tags: [POV, cinematic, reel, vertical, 9:16]
    related_skills: [wan2gp-image-generation, wan2gp-video-generation]
---

# POV Cinematic Reel

Generate vertical (9:16) first-person POV cinematic reels using WanGP. Two-stage workflow: anchor image → video.

## Prerequisites

- **Python**: `/home/gowrav/pinokio/api/wan.git/app/env/bin/python` (torch 2.7.0+cu128)
- **WAN_APP**: `/home/gowrav/pinokio/api/wan.git/app`
- **Skills**: `wan2gp-image-generation`, `wan2gp-video-generation`
- **Environment**: `set -a; source $PROFILE_ROOT/.env; set +a` (absolute path to profile `.env` — **never** `~/.hermes/...` or `$HOME/.hermes/...`; see [`video-create-workflow/references/hermes-path-pitfall.md`](../video-create-workflow/references/hermes-path-pitfall.md))

```bash
set -a; source $PROFILE_ROOT/.env; set +a
```

## Environment Variables

```bash
PYTHON="/home/gowrav/pinokio/api/wan.git/app/env/bin/python"
WAN_APP="/home/gowrav/pinokio/api/wan.git/app"
WAN_IMG_SKILLS="/home/gowrav/.hermes/shared-skills/wan2gp-image-generation/scripts"
WAN_VID_SKILLS="/home/gowrav/.hermes/shared-skills/wan2gp-video-generation/scripts"
```

## Workflow Overview

```
1. PLAN → Confirm scene, POV type, mood with user
2. GENERATE ANCHOR → Flux Klein, 9:16, POV perspective
3. GENERATE VIDEO → LTX-2.3 I2V, 20s (481 frames), 9:16
4. VERIFY → Check output files
```

## Step 1: Generate Anchor Image

Use Flux Klein for photorealistic POV perspective. The anchor IS frame 0 — everything visible in the video must be in the anchor.

```bash
$PYTHON "$WAN_IMG_SKILLS/generate_image_config.py" \
    --prompt "Cinematic first-person POV perspective running through [ENVIRONMENT]. [DETAILS]. Chest-mounted camera movement. Photorealistic, 9:16 vertical." \
    --output-filename "scene_anchor" \
    --output-dir "<OUTPUT_DIR>" \
    --aspect "9:16" \
    --template "flux-klein" \
    --steps 8 \
    --guidance-scale 2.5 \
    --seed 481 \
    --generate-and-run
```

**Anchor prompt rules:**
- Describe the POV environment, not the viewer
- Include: stone walls, debris, lighting, atmosphere
- No character should be visible (first-person perspective)
- 9:16 vertical aspect ratio
- Chest-mounted or head-mounted camera movement implied
- Photorealistic, cinematic lighting

## Step 2: Generate Video

Use LTX-2.3 I2V (image-to-video) with the anchor. Single 20-second shot.

```bash
$PYTHON "$WAN_VID_SKILLS/generate_video_config.py" \
    --prompt "INT/EXT. [TIME]. [ACTION]. Camera [MOVEMENT]. [DETAILS]. Audio: [SOUNDS]." \
    --output-filename "scene_video" \
    --output-dir "<OUTPUT_DIR>" \
    --aspect "9:16" \
    --seed 481 \
    --steps 25 \
    --guidance-scale 3.5 \
    --image-start "<ANCHOR_PATH>" \
    --model "distilled-1.1" \
    --generate-and-run
```

**Video prompt rules:**
- Start with environment/time: `INT. ANCIENT RUINS — DAY.`
- Describe camera movement: `chest-mounted camera, handheld shake`
- One dominant action per shot
- Temporal connectors: `as`, `then`, `while`
- Audio cues explicit: `Audio: heavy breathing, footsteps, wind`
- No hard cuts (`CUT TO` only for multi-scene movies)
- Match anchor composition in first sentence

## Output Files

```
<OUTPUT_DIR>/
├── scene_anchor.jpg          # Anchor image (~0.3 MB)
├── scene_video.mp4           # Final video (~35-40 MB)
├── image_generation.json     # Image config
└── video_generation.json     # Video config
```

## Prompt Templates

### Anchor Template

```
Cinematic first-person POV perspective [ACTION] through [ENVIRONMENT]. [DETAILS: walls, debris, lighting, atmosphere]. Chest-mounted camera movement creates [MOVEMENT: running sway, walking stride]. Photorealistic, 9:16 vertical, cinematic lighting, atmospheric [PARTICLES: dust, fog, rain].
```

### Video Template

```
INT/EXT. [LOCATION] — [TIME]. First-person POV, [CAMERA_TYPE] camera, [ACTION]. [DETAILS: what's happening, environment changes]. [LIGHTING: sunlight shafts, neon, emergency lights]. Camera [MOVEMENT: bobs, sways, tracks]. Audio: [SOUNDS: breathing, footsteps, wind, ambient].
```

## Common POV Environments

| Environment | Anchor Keywords | Video Actions |
|------------|----------------|---------------|
| Ancient ruins | stone walls, moss, cracks, debris | running, collapsing ceiling, dust clouds |
| Cyberpunk city | neon signs, rain, holograms, wet streets | walking, scanning, dodging |
| Forest | tall trees, mist, sunlight, animals | walking, discovering, startled |
| Space station | metallic walls, panels, windows, stars | running, emergency, zero-g |
| Desert | sand dunes, heat shimmer, ruins | walking, discovering, storm |

## Pitfalls

- **Sequential only** — never two `wgp.py` jobs at once. Use `video-create-workflow/scripts/gpu_wait.py` before launching.
- **Background + notify** — GPU work blocks 3-5 min. Launch via `terminal(command="...", background=true, notify_on_complete=true)`.
- **Anchor must match** — first sentence of video prompt must describe same composition as anchor image.
- **No hard cuts** — use camera moves to transition, not `CUT TO`.
- **POV consistency** — no character visible in anchor or video (first-person perspective).
- **9:16 vertical** — always specify `--aspect 9:16`.

## Quick Reference

```bash
# Anchor
$PYTHON "$WAN_IMG_SKILLS/generate_image_config.py" \
    --prompt "Cinematic first-person POV perspective through ancient ruins..." \
    --output-filename "anchor" --output-dir "./output" \
    --aspect "9:16" --template "flux-klein" --steps 8 --guidance-scale 2.5 --seed 481 --generate-and-run

# Video
$PYTHON "$WAN_VID_SKILLS/generate_video_config.py" \
    --prompt "INT. RUINS — DAY. First-person POV running through collapsing temple..." \
    --output-filename "video" --output-dir "./output" \
    --aspect "9:16" --seed 481 --steps 25 --guidance-scale 3.5 \
    --image-start "./output/anchor.jpg" --model "distilled-1.1" --generate-and-run
```

## Related Skills

- `wan2gp-image-generation` — Image generation (Flux Klein, Qwen)
- `wan2gp-video-generation` — Video generation (LTX-2.3)
- `wan2gp-movie-pipeline` — Multi-scene movies (3+ connected scenes)
