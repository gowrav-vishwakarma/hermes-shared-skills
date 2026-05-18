# Trend Copy Workflow via copy_trend.py

Orchestrates downloading an Instagram reel/trend and generating a video of your character performing the same choreography using WanGP's OVG (Aligned Pose Transfer) mode.

## Prerequisites

1. **yt-dlp installed**: `pip install yt-dlp --break-system-packages`
2. **character_girl asset**: Must be registered in `assets.json`
3. **WanGP venv Python**: `$WAN_PYTHON` (`/home/gowrav/pinokio/api/wan.git/app/env/bin/python`)
4. **WanGP app dir**: `$WAN_APP_DIR` (`/home/gowrav/pinokio/api/wan.git/app`)

## Full Workflow

### Step 1: Run copy_trend.py

```bash
python3 "$PROFILE_SKILLS/wan2gp-video-generation/scripts/copy_trend.py" \
    --url "https://www.instagram.com/p/<POST_ID>/" \
    --character-image "/home/gowrav/.hermes/profiles/gvs/home/assets/character_girl.png" \
    --prompt "A young woman (image 1) performs a dance routine following the choreography steps. Focus on body movement and dance steps, no lip-sync needed. Natural arm movements, footwork, hip motion matching the beat. She stands in a simple room with neutral background, wearing casual clothing. Camera: steady medium shot, slight push-in." \
    --output-dir "/home/gowrav/.hermes/profiles/gvs/home/posts/YYYY-MM-DD_trend_dance" \
    --output-filename trend_dance_girl \
    --mode OVG \
    --no-loras
```

**Key flags:**
- `--mode OVG`: Aligned Pose Transfer (character follows the pose/motion of the trend)
- `--no-loras`: Clean generation without LoRA enhancements (faster, less style interference)
- `--prompt`: Describe the character performing the trend. IMPORTANT: specify "no lip-sync" and focus on body movement to avoid unintended facial animation.

### Step 2: Fix Audio Extraction (MANDATORY — copy_trend.py BUG)

`copy_trend.py` DOES NOT pass `--audio-from-control-video` internally. It writes `video_generation.json` with `audio_prompt_type: ""` (empty). **The output will be silent unless you fix this.**

```python
import json
with open("<post-dir>/video_generation.json") as f:
    c = json.load(f)
c["audio_prompt_type"] = "K"
with open("<post-dir>/video_generation.json", "w") as f:
    json.dump(c, f, indent=4)
```

### Step 3: Launch wgp.py

**CRITICAL: Must run from WanGP app directory** because `wgp.py` looks for `models/_settings.json` relative to CWD.

**CRITICAL: Must use WanGP venv Python** — system `python3` lacks `torch`.

```bash
cd "$WAN_APP_DIR" && \
  "$WAN_PYTHON" wgp.py \
  --process "<post-dir>/video_generation.json" \
  --output-dir "<post-dir>" \
  --attention sage2 --profile 4 --fp16
```

### Step 4: Compress

```bash
ffmpeg -y -i "<post-dir>/trend_dance_girl.mp4" -vcodec libx264 -acodec aac -b:v 2000k -b:a 128k -movflags +faststart "<post-dir>/trend_dance_girl_compressed.mp4"
```

## Audio Conditioning (Alternative: No Motion Transfer)

If you want to use the audio from a trend video but NOT transfer pose/motion (just play the audio with the character dancing freely):

1. Extract audio from the trend video (copy_trend.py creates `trend_source_clean_control_audio.wav` automatically)
2. Use `generate_video_config.py` with `--audio-guide` instead of `--video-guide`:

```bash
python3 "$PROFILE_SKILLS/wan2gp-video-generation/scripts/generate_video_config.py" \
    --prompt "INT. STUDIO. She breaks into dance... (detailed dance description)" \
    --image-start "<post-dir>/dance_anchor.jpg" \
    --audio-guide "<post-dir>/trend_source_clean_control_audio.wav" \
    --output-filename dance_audio_reel \
    --output-dir "<post-dir>" \
    --aspect 9:16
```

This sets `audio_prompt_type: "A"` — the model conditions video on the audio waveform (lip sync + movement to beat) but does NOT transfer motion from any control video.

## Common Pitfalls

1. **Silent video (MOST COMMON)**: copy_trend.py never sets `audio_prompt_type: "K"`. You MUST manually fix it (Step 2).
2. **`models/_settings.json` not found**: Running `wgp.py` from wrong CWD. Must `cd` into `$WAN_APP_DIR`.
3. **`No module named 'torch'`**: Using system `python3` instead of WanGP venv Python (`$WAN_PYTHON`).
4. **Character lip-syncing in OVG**: Prompt must explicitly say "no lip-sync" and focus on body movement only.
5. **Aspect ratio mismatch**: Output may be slightly off 9:16 (e.g., 704x1280 vs 720x1280). Fine for Instagram but can be fixed by passing `--resolution 720x1280` instead of `--aspect 9:16`.
6. **LoRA format**: If adding LoRAs, `loras_multipliers` must be semicolon-separated numbers matching `activated_loras` array order: `"0.5;1.5"` — NOT `"CrispEnhance=0.5 VBVR=1.5"`.