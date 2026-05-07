# Model Style Limits: Photorealism Trap

## Core Finding (2026-05-07)

**Qwen Image Edit Plus 2511 and Flux 2 Klein 9B are fundamentally photorealistic models.** Neither can produce stylized/cartoon/3D-animated output regardless of:
- Explicit style prompts ("Pixar style", "3D animated", "cartoon")
- Reference images with stylized content
- Negative prompts ("photorealistic", "realistic")
- Higher step counts or guidance scale variations

Both models are trained/instruct-tuned for realism and will always resist stylization.

## Evidence

- **Qwen 2511** — Image-edit model trained on real photos. Tested with explicit Pixar/Disney prompts + character_base reference. Result: photorealistic corporate headshot.
- **Flux 2 Klein 9B** — Distilled Flux model. Tested with text-to-image (no refs), explicit Pixar prompts, higher steps. Result: photorealistic portrait.
- Both models resisted style even when prompted to do so directly.

## What DOES Work for Stylized Output

### Option A: ComfyUI
Install ComfyUI for access to SDXL, SD 1.5, and other models that produce stylized output natively. Load a 3D-animated / cartoon checkpoint + Pixar LoRA from CivitAI. This is the most reliable path.

### Option B: LTX-2.3 Pixar_Toon LoRA
The `Pixar_Toon.safetensors` LoRA exists at `loras/ltx2/`. It works with LTX-2.3 video generation (not Qwen/Flux image). Use it via `wan2gp-video-generation` for video anchors that need Pixar style.

### Option C: External generation
Generate stylized character sheets externally (Midjourney, DALL-E, etc.) and use as `--image-refs` in WanGP pipelines.

## Pitfalls

- **Do NOT waste GPU time** trying multiple prompt variations of Qwen/Flux for stylized output. If the first attempt doesn't produce style, stop and switch models.
- **Do NOT assume "Pixar_Toon LoRA"** will work with Qwen or Flux. It is LTX-2.3 only.
- **Image references do NOT transfer style.** Even passing a Pixar-styled `character_base` as reference does not make Qwen/Flux output in that style. The models use refs for identity only, not style transfer.

## When This Matters

When users request: Pixar style, cartoon, anime, hand-drawn, sketch, watercolor, claymation, or any non-photorealistic output. Qwen and Flux are the wrong tools for this class of task.
