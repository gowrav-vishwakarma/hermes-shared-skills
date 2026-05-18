# Qwen Image Edit Plus 2511 — Realism Challenge

## Session Evidence (2026-05-05)

User rejected generated location assets for being too "perfect" and AI-looking:
- **Session 2026-05-05_5**: `location_jungle_river` — too saturated, uniform stones, "glow" bloom effect, unnatural clarity
- **Session 2026-05-05_5 (retry)**: `location_river_realistic` — still had hyper-clarity, smooth uniform foreground, dappled light "glow"

## Flux 2 Klein Outperforms Qwen for Character Bases (2026-05-07)

**Problem:** Three consecutive Qwen 2511 character generations all rejected by user as "not realistic" — too doll-like, perfect skin, uniform eyelashes.

**Attempt 1 — Qwen quality tier (928x1664, 50 steps):**
- Output: Dusty rose t-shirt, large sparkling eyes, rosy cheeks, soft bangs
- Verdict: "Not even realistic image" — too AI-doll, too cute/perfect

**Attempt 2 — Qwen with "realistic" prompt (928x1664, 50 steps):**
- Output: White kurta, bindi as 3D gem (AI hallucination), long uniform lashes
- Verdict: Still AI-looking — skin poreless, eyelashes perfect, bindi wrong

**Attempt 3 — Qwen with "candid phone photo" prompt (928x1664, 50 steps):**
- Output: Grey tie-dye t-shirt, hair cowlick, dramatic window lighting
- Verdict: Still AI — skin still too smooth, lashes too uniform, face perfectly symmetrical

**Attempt 4 — Flux 2 Klein 9B (720x1280, 8 steps):**
- Output: White kurta, flat red bindi, visible skin pores, natural flyaway hairs, natural freckles, realistic shadows
- Verdict: Accepted — looks like a genuine candid photograph
- Speed: 35 seconds vs Qwen's ~3 minutes

**Conclusion:** Qwen 2511 CANNOT produce photorealistic character images, no matter the prompt or settings. Flux 2 Klein is superior for standalone character generation on both realism and speed.

**Evidence:** Skin texture visible in Flux output (pores, freckles), natural hair flyaways (not uniform strands), realistic bindi (not AI's 3D gem hallucination), natural asymmetric lighting from window.

## Root Cause

Qwen Image Edit Plus 2511 inherently produces hyper-perfect, glossy aesthetics:
- Water that's "too clear" (every pebble visible, impossible in nature)
- Uniform stone sizes and shapes
- Saturated, uniform greens
- Specific "bloom/glow" lighting signature common in AI art
- Smooth, perfect foreground textures

**Contributing configuration issues (fixed 2026-05-07):**
- Templates used only 30 inference steps (official recommendation: 50 for T2I, 40 for editing)
- Resolution was 720x1280 instead of the model's native 928x1664 (40% fewer pixels)
- Complex `negative_prompt` instead of official minimal `" "` (single space)
- These sub-optimal settings caused the model to produce less refined, more "AI-generic" output

## Confirmed Fixes (2026-05-07)

Based on official Qwen documentation (HuggingFace model card, QwenLM/Qwen-Image README, DeepWiki):

1. **Step count: 30 → 50** — Official default for T2I is 50 steps, editing is 40. Values below 20 produce low-quality output. Above 50 gives minimal improvement.
2. **Resolution: 720x1280 → 928x1664** (via `--quality` flag) — The model's native trained resolution. Only predefined aspect ratio dimensions are officially supported; arbitrary dimensions may cause quality degradation.
3. **Negative prompt: complex → `" "`** (single space) — Official recommendation. The complex negative prompt was over-constraining the model.
4. **`guidance_scale: 4` confirmed correct** — Maps to `true_cfg_scale=4.0` in the pipeline, the officially recommended balance of prompt adherence vs naturalness.
5. **bf16 precision** — Official recommendation is `torch.bfloat16`. The quantized model (`quanto_bf16_int8`) already forces bf16 in WanGP regardless of flags.

## Workaround Strategy (for natural/outdoor scenes)

Even with optimal parameters, Qwen still trends toward hyper-clarity for nature scenes. Additional prompting strategies:

1. **Camera specs**: "Shot on Canon EOS R5, 35mm lens, natural light"
2. **Imperfections**: "muddy banks", "dead leaves scattered", "rough bark texture", "slight film grain"
3. **Natural chaos**: "scattered rocks of various sizes", "uneven water depth", "debris in water"
4. **Anti-perfection**: "not crystal-perfect", "gentle ripples and slight reflection", "nothing overly saturated"
5. **Reference style**: "documentary photography", "natural colors", "like a real photograph taken by a nature photographer"

## Lightning LoRA — NOT a Quality Solution

Lightning LoRA (4-step or 8-step) does NOT improve realism:
- Disables CFG (`guidance_scale: 1`) — removes negative prompt influence entirely
- Cannot run at higher steps — overcooks/artifacts (confirmed by lightx2v developers)
- Produces "very static and very identical images" (community feedback)
- Use ONLY for rapid composition drafts, never for final output

## Quality Hierarchy (confirmed)

For maximum photorealism:
1. **Best**: Native resolution (928x1664) + 50 steps + `guidance_scale: 4` + `negative_prompt: " "`
2. **Good**: 720x1280 + 50 steps + same parameters (for video anchors)
3. **Draft only**: Lightning 4-step (composition preview, not photorealistic)

---

## Flux 2 Klein for Hindu/Divine Deity Generation (2026-05-12)

**Use Case:** Generating realistic Hindu deity images (Lord Shiva, Durga, etc.) with specific cultural elements.

**Confirmed Pattern:** Flux 2 Klein 9B excels for standalone character generation of divine/hindu deities with cultural attributes:

**Visual Elements for Lord Shiva (successful 2026-05-12):**
- "Third eye closed on forehead, glowing softly with inner divine light"
- "Rudraksha beads, sacred ash on body"
- "Flowing matted hair with river Ganga, crescent moon"
- "Radiant cosmic being with serene, meditative expression"
- "Surrounded by ethereal clouds and golden light rays"

**Why Flux works better than Qwen for deities:**
1. **Cultural accuracy:** Qwen tends to "hallucinate" elements (e.g., bindi as 3D gem instead of flat application)
2. **Texture realism:** Sacred ash appears more natural (powdery, textured) with Flux
3. **Speed:** ~35 seconds vs Qwen's ~3 minutes
4. **Expression:** Serene/meditative expressions render more authentically

**Prompt Structure (Flux template):**
```
Cinematic portrait of [deity name], a divine [tradition] deity. [Physical description]. Wearing [cultural elements]. [Environment/lighting]. Shot on Canon EOS R5, 85mm portrait lens, natural divine lighting, photorealistic. No hands visible, focus on face and upper body.
```

**Example prompt for Lord Shiva:**
> "Cinematic portrait of Lord Shiva, a divine Hindu deity from heaven. A radiant cosmic being with a serene, meditative expression, third eye closed on forehead, glowing softly with inner divine light. Wearing rudraksha beads, sacred ash on body, flowing matted hair with river Ganga, crescent moon. Surrounded by ethereal clouds and golden light rays breaking through. Shot on Canon EOS R5, 85mm portrait lens, natural divine lighting, photorealistic. No hands visible, focus on face and upper body."

**Output:** Realistic, culturally accurate deity image with proper texture and lighting.

**Session evidence (2026-05-12):** `shiva_divine_character_anchor.jpg` generated successfully with Flux 2 Klein, seed 52000, accepted for divine message video.
