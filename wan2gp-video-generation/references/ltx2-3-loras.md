# LTX-2.3 LoRA Inventory & Usage Guide

All LoRAs live under `$WAN_APP_DIR/loras/ltx2/`.

## Conditionally auto-loaded (feature-gated)

These LoRAs are **pre-downloaded** by the model config's `preload_URLs`, but they are **NOT always active**. WanGP's `get_loras_transformer()` adds them only when their corresponding feature is enabled. For plain T2V or I2V (`image_prompt_type: "S"` with empty `video_prompt_type`), **none of these are applied**.

| LoRA | Trigger | When it activates |
|---|---|---|
| `ltx-2.3-22b-ic-lora-union-control-ref0.5.safetensors` | `video_prompt_type` contains `O`, `P`, `D`, or `E` | Pose / depth / canny edge control modes |
| `ltx-2.3-22b-ic-lora-outpaint.safetensors` | Outpainting dimensions configured | Spatial outpainting enabled |
| `ltx-2.3-22b-ic-lora-hdr-0.9.safetensors` | `video_prompt_type` contains `&` | "Convert SDR to HDR (IC-LoRA)" mode |

If you manually add one of these to `activated_loras`, WanGP deduplicates — it won't load the same LoRA twice. Manual activation is useful to override the default multiplier.

## Template defaults

**T2V** (`ltx-2.3-t2v.json`):

```json
"activated_loras": ["LTX2.3_Crisp_Enhance.safetensors"],
"loras_multipliers": "0.5"
```

**I2V** (`ltx-2.3-i2v.json`):

```json
"activated_loras": ["LTX2.3_Crisp_Enhance.safetensors", "Ltx2.3-Licon-VBVR-I2V-96000-R32.safetensors"],
"loras_multipliers": "0.5;0.5"
```

Crisp_Enhance sharpens detail; VBVR (I2V only) improves temporal consistency, motion dynamics, and complex prompt understanding. Override with `--activated-loras` or disable with `--no-loras`.

## Manual activation — CLI flags

In `generate_video_config.py`:

```bash
# Single LoRA, default multiplier (0.5)
--activated-loras LTX2.3_Crisp_Enhance.safetensors

# Single LoRA, custom multiplier
--loras-multipliers 0.7 --activated-loras LTX2.3_Crisp_Enhance.safetensors

# Multiple LoRAs: space-separated filenames, semicolon-separated multipliers
--activated-loras LTX2.3_Crisp_Enhance.safetensors ltx23_zoomout_z00m047.safetensors \
  --loras-multipliers "0.6;0.4"

# Disable all LoRAs (overrides template defaults)
--no-loras
```

**CRITICAL BUG — Multi-LoRA config requires manual fix:**
After running `generate_video_config.py` with multiple LoRAs, **always check the output JSON**. The CLI tool often merges multiple filenames into a single space-separated string inside the `activated_loras` array (e.g., `["Pixar_Toon.safetensors LTX2.3_Crisp_Enhance.safetensors"]` instead of two separate items). **Fix:** edit `video_generation.json` manually to split them:

```json
"activated_loras": ["Pixar_Toon.safetensors", "LTX2.3_Crisp_Enhance.safetensors"],
"loras_multipliers": "0.9;0.5"
```

Or edit directly via Python/JSON before running `wgp.py`. Never trust multi-LoRA CLI output without verification.

## Recommended LoRA multiplier ranges

**This is critical — wrong multipliers = invisible LoRA:**

| LoRA Type | Safe Range | Effect at 0.5 | Effect at 0.8+ | Effect at 1.5 |
|---|---|---|---|---|
| **Control** (union-control-ref0.5, outpaint, HDR, zoomout) | 0.3–0.5 | Works fine | May over-control | Unpredictable |
| **Detail/Quality** (Crisp_Enhance, VBVR) | 0.3–0.5 | Works fine | May sharpen too much | Artifacts possible |
| **Style/Aesthetic** (Pixar_Toon, Claymation, CozyFelt, Fantasy_*) | **0.8–1.5** | **INVISIBLE / barely detectable** | Visible style shift | Strong cartoon/anime look, character distortion at extreme |
| **Motion** (danceV2) | 0.5–0.6 | Subtle improvement | Noticeable dance fluidity | May cause wobble artifacts |
| **Identity** (Licon-VBVR-I2V) | 0.5 | Good temporal consistency | Stronger but may over-lock | Identity lock too tight, less natural motion |

**Key insight from session (2026-05-02):** Style LoRAs at default 0.5 multiplier produce **no visible visual change**. The model's base output overwhelms the style injection at low weights. For Pixar_Toon specifically:
- 0.5 → no visible difference from no-LoRA
- 0.8 → noticeable cartoon styling, faces rounded
- 1.5 → strong Pixar/toon aesthetic, character features exaggerated but recognizable

**When to use high multipliers:** Only for style/aesthetic LoRAs when you explicitly want the look to dominate. For character content (like Meena's reels), keep Pixar_Toon between 0.8–1.2 to avoid over-distorting the character's identity.

## Complete inventory

### Style / Aesthetic LoRAs

| File | Size | Effect | Best Multiplier |
|---|---|---|---|
| `LTX2.3_Crisp_Enhance.safetensors` | 705MB | Sharpens edges, enhances detail clarity | 0.5 |
| `LTX-2.3_Cinematic hardcut.safetensors` | 654MB | Cinematic grading with hard-cut transitions (not for I2V) | 0.5 |
| `LTX-2.3-danceV2.comfy.safetensors` | 402MB | Enhanced dance/body motion fluidity | 0.5–0.6 |
| `Ltx2.3-Licon-VBVR-I2V-96000-R32.safetensors` | 554MB | VBVR video reasoning: temporal consistency, motion dynamics, complex prompt understanding (I2V default) | 0.5 |
| `Claymation.safetensors` | 352MB | Claymation animation look | 0.8–1.2 |
| `CozyFelt.safetensors` | 352MB | Cozy felt/craft texture aesthetic | 0.8–1.2 |
| `Fantasy_Painterly.safetensors` | 352MB | Fantasy painterly oil-painting style | 0.8–1.2 |
| `Fantasy_Realism.safetensors` | 352MB | Fantasy realism rendering | 0.8–1.2 |
| `Pixar_Toon.safetensors` | 352MB | Pixar/toon 3D animation style | **0.8–1.5** (needs high multiplier!) |
| `AmateurHour_01_rank16.safetensors` | 176MB | Amateur/phone-camera aesthetic | 0.8–1.2 |

### Control / Technique LoRAs

| File | Size | Effect |
|---|---|---|
| `ltx23_zoomout_z00m047.safetensors` | 402MB | Zoom-out camera effect |
| `ltx23__demopose_d3m0p0s3.safetensors` | 402MB | Demo pose control (experimental) |
| `LTX2.3-IC-LORA-Dual-Character.safetensors` | ? | Handles two distinct characters in the same frame. Prevents merging/artifacts when scene has 2 characters. Use at 0.5 multiplier alongside a style LoRA. |

### Two-character scene setup

When the prompt calls for two distinct characters (people, animals, creatures):

**Always stack a style LoRA with Dual-Character LoRA:**
- Style LoRA (e.g., `Pixar_Toon.safetensors`) at 1.5–2.0 for aesthetic
- Dual-Character LoRA at 0.5 for character separation
- Command: `--activated-loras "Pixar_Toon.safetensors LTX2.3-IC-LORA-Dual-Character.safetensors" --loras-multipliers "2.0;0.5"`
- **Remember:** Multi-LoRA CLI output merges filenames into one array entry — always split them manually in the JSON.

**Prompt guidance for two characters:**
- Define each character by a unique visual identifier in the prompt (fur color, clothing, size, shape) — NOT by "first/second" or "one/two" which the model confuses
- Give them contrasting attributes (dark/light, big/small, calm/energetic) for reliable separation
- Describe the interaction explicitly: "character A does X to character B" rather than ambiguous pronouns
- Emotional beats must be sequential: "first X, then Y, then Z" with clear temporal markers

## User preferences (Gowrav)

- **Pixar_Toon LoRA multiplier range: 1.0, 1.5, 2.0.** User has used all three in session 2026-05-05: 1.0 (subtle, clean character), 1.5 (balanced Pixar, default for character content), 2.0 (maximum effect, exaggerated cartoon features). The user generates batch variations across these weights to compare. Do not ask about multiplier — use what the user specifies, or default to 1.5 if unspecified.
- **Always use LoRA 1.5 multiplier for other style LoRAs.** When not using Pixar_Toon, use 1.5. Do not ask about LoRA weight unless the user specifies otherwise.
- **Start with strongest LoRA first.** When testing style LoRAs, begin at the strongest (1.5 or 2.0 for Pixar) and only reduce if the output is too distorted. Do not start at 0.5 and progressively increase — the user wants to see the full style effect immediately.
- **Temporary/one-off assets should not be registered.** When user says "no asset" or "it's a temp creation", generate the asset image directly in the post folder without calling `generate_asset.py --run` or adding to `assets.json`. This was confirmed working with the jungle river session.

## Pitfalls

- **VBVR LoRA causes camera shake on talking-head shots.** A/B test (Post #6, 2026-05-02): VBVR (default I2V LoRA at 0.5) introduced visible jitter/shake in a smooth dolly-in talking-head shot. The Crisp_Enhance-only variant (no VBVR) produced a steadier result. **Recommendation:** For Meena's dialogue-heavy reels, start with Crisp_Enhance ONLY (`--activated-loras LTX2.3_Crisp_Enhance.safetensors`), disable VBVR. Enable VBVR only if temporal consistency is visibly poor or for dance content (where its motion dynamics help).
- **Style/Aesthetic LoRAs need HIGH multipliers (0.8–1.0+).** The default 0.5 multiplier does NOT visibly apply style LoRAs like Pixar_Toon, Claymation, Fantasy_Painterly, etc. **For aesthetic LoRAs, use 0.8–0.9 minimum, or even 1.5 for maximum effect.** Crisp_Enhance at 0.5 is fine since it's a detail sharpening LoRA, not a style transformer. Multiplier 1.0+ can produce strong stylistic results.
- **Do not stack too many control LoRAs** (motion, pose, hardcut). Stick to 1–2 total. Style LoRAs can be stacked with control LoRAs if needed.
- **Cinematic hardcut LoRA is incompatible with I2V.** LTX-2.3 I2V is a single continuous shot — hard cut transitions break it.
- **Use `.safetensors` basename** — always use the exact filename including extension (e.g. `"LTX2.3_Crisp_Enhance.safetensors"`).
- **Always test with anchor image** — LoRAs can affect character consistency in I2V mode. Compare with/without before deploying.
- **`--no-loras` for A/B testing** — use this flag to generate without any LoRAs and compare quality.
- **GGUF model supports LoRAs.** Both Pixar_Toon and Fantasy_Realism LoRAs load and render correctly with the distilled GGUF model (verified 2026-05-02). You do NOT need the PyTorch distilled-1.1 model for LoRA support — the GGUF runtime applies them via Triton int8 kernels.
- **Progressive multiplier escalation.** When a style LoRA result looks wrong (too weak or too distorted), escalate: 0.8 → 1.0 → 1.5 → 2.0. Do NOT start at 0.5 — it is invisible for style LoRAs. For character content, test 1.0 first to preserve identity; if the style isn't visible enough, step up to 1.5 or 2.0. Do not step down from 2.0 — it distorts character features irreversibly at that level.

## LTX-2.3 Dialogue & TTS Pitfalls

- **"no text on video" directive** — If you do NOT want the model rendering text onto the video frame (titles, watermarks, captions), ALWAYS add "No text on video" to the prompt. LTX-2.3 may otherwise interpret keywords like "WANTED" or "HIRING" as text to render visually.
- **Capitalized words mispronounce** — ALL-CAPS words like "WANTED", "HIRING", "NOW" often come out garbled or with weird stress in LTX-2.3's TTS. Use lowercase or reword: "wanted" → "looking for", "HIRING" → "we need", "NOW" → "today". Test by reading dialogue aloud yourself — if it sounds awkward, the model will struggle too.
- **Short punchy lines > long monologues** — LTX-2.3 handles dialogue best when lines are short and punchy (max 3-4 seconds per quoted line). Long quoted passages get stretched or slurped. Break dialogue into 2-3 second segments with acting beats between them.
- **Title overlays for job posts** — For hiring/job post videos, use ffmpeg drawtext for overlay titles instead of trying to render text in-video. LTX-2.3 can't do clean typography. Use the `ffmpeg-text-overlay` pattern (see `references/ffmpeg-text-overlay.md` under `hyperframes` skill) — always use `textfile` instead of `text` parameter if the overlay contains colons, apostrophes, or other special chars (they break ffmpeg's argument parser).

**User multiplier preferences:** For Pixar_Toon specifically: 1.0 (subtle, clean character), 1.5 (balanced Pixar, default for character content), 2.0 (maximum effect, exaggerated cartoon features). When the user doesn't specify a multiplier, default to 1.5 for Pixar_Toon and 1.5 for all other style LoRAs. Never start a style LoRA at 0.5 — it is invisible.
