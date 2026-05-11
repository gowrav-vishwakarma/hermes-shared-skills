# Multi-Ref Character Consistency

## The Problem

Qwen Image Edit Plus 20B does NOT reliably lock character identity from references alone. When generating scenes with multiple characters, generic prompts like "an Indian male accountant in his 30s wearing a white button-down shirt and red tie" produce characters that look like generic accountants, not the specific ref image. The model ignores or partially matches the reference.

## Solution: Exhaustive Visual Description

When generating multi-ref images, the prompt must describe **every visual feature** of each reference character in exhaustive detail, matching the actual reference image pixel-by-pixel:

### Checklist for Each Character

For **each** reference character, describe:
1. **Skin tone/complexion** — exact color, texture
2. **Hair** — color, style, length, parting, texture
3. **Face shape & features** — nose shape, eye shape, facial hair specifics
4. **Clothing** — exact colors, fabric type, button styles, accessories
5. **Accessories** — glasses type/frames, jewelry, specific items
6. **Pose & body language** — posture, arm position, stance
7. **Expression** — exact facial expression, eye direction, mouth position
8. **Lower body** — pants, shoes, tail/smoke/etc.

### Reference-Specific Details

For known ref images, inspect them first (via vision or description) and copy the features verbatim into the prompt:

**Example accountant:**
- "light warm peach skin" (NOT just "skin tone")
- "short light brown swept-back hair with side part" (NOT just "brown hair")
- "round thin metal wire-rimmed glasses" (NOT just "glasses")
- "light blue button-down dress shirt with collar and pocket" (NOT just "blue shirt")
- "bright solid red necktie" (NOT just "red tie")

**Example blue genie:**
- "solid vibrant medium blue skin" (NOT just "blue skin")
- "large wrapped blue turban matching skin tone with a teal triangular symbol (letter A) on front" (NOT just "blue turban")
- "thick dark brown beard with curled mustache" (NOT just "has beard")
- "pointed ears with gold hoop earrings" (NOT just "gold earrings")
- "one thick gold band near left shoulder, two gold bands on right arm (one near shoulder, one near elbow)" (NOT just "gold bands")
- "wide gold belt with large circular buckle" (NOT just "gold belt")
- "lower body tapers into long blue smoke-like tail in S-shape" (NOT just "snake tail")

### Image Index References

Always reference each character by index in the prompt AND in the image_refs array order:

```
Accountant (image 1) — [detailed features]
Blue genie (image 2) — [detailed features]
```

The `image_refs` array order must match: `[character_accountant.jpg, character_ginnie.jpg]`

### Prompt Structure

```
Cinematic medium shot, 9:16. INT. modern office room. Two Pixar-style 3D animated characters. EXACT character consistency from reference images.

On the left: Indian male accountant (image 1) — [exhaustive visual features]. 
Accountant looks [specific expression]: [detailed facial description], [detailed body language].

On the right: Blue genie character (image 2) — [exhaustive visual features].
Genie stands [specific pose], [specific expression].

[Background description]
EXACT character matching — use reference images for identity.
```

## Why This Works

Qwen IEP 20B uses the prompt text to assign references to visual roles in the scene. Without exhaustive description, the model guesses which ref goes where based on vague keywords. With exhaustive matching, the model can verify "this ref matches this description perfectly" and place it correctly.

## Session Evidence

**2026-05-11:** First attempt with generic description ("Indian male accountant in his 30s wearing white button-down shirt and red tie") produced characters that looked like generic accountants, not the specific ref. After inspecting ref images and rewriting the prompt with exhaustive visual features (skin tone, hair style, exact clothing colors, specific jewelry types), both characters achieved 10/10 consistency with their reference images.

## Limitations

- Requires knowing the exact appearance of each ref before writing the prompt
- Must inspect ref images (via vision analysis or existing descriptions) before generating
- More prompt text to write, but saves GPU time by avoiding failed generations
- Works best for characters that already have reference images; pure text-to-image characters still look AI-generated
