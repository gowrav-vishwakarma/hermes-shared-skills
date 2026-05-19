# T2V with Style LoRA — No Anchor Needed

When generating stylized video (Pixar, cartoon, claymation, etc.) via **pure T2V** (no `--image-start`), a style LoRA alone is sufficient — no anchor image required. The LoRA transforms the base model's output style from photorealistic to the target aesthetic.

## Proven recipe

```bash
python3 generate_video_config.py \
  --prompt "Your detailed prompt..." \
  --output-filename "my_video" \
  --aspect "9:16" \
  --model "gguf" \
  --activated-loras "Pixar_Toon.safetensors" \
  --loras-multipliers "1.5" \
  --seed 42 \
  --generate-and-run
```

## Why no anchor?

- **I2V anchors lock character identity** — critical when the model might invent random faces
- **T2V with style LoRA** — the LoRA controls the style globally; the prompt describes character/appearance in text
- For T2V, the model generates characters from the prompt text + style injection from the LoRA
- If you need character consistency across multiple shots, switch to I2V with an anchor for those specific shots

## Timing (GGUF model + Pixar_Toon at 1.5x)

| Phase | Duration |
|-------|----------|
| Model load + prompt encoding | ~30s |
| VAE encoding | ~10s |
| Denoising first pass (8 steps) | ~1 min |
| VAE decoding | ~1.5 min |
| Denoising second pass (3 steps) | ~1.5 min |
| VAE decoding | ~3 min |
| **Total** | **~3.5–4 min** |

Consistently fast because GGUF skips TorchInductor compilation entirely.

## When to add an anchor anyway

Even in T2V, consider `--image-start` if:
- The character design is complex (specific outfit, accessories, pose)
- You need precise control over the opening composition
- The style LoRA alone isn't producing the exact character look you want

In those cases, generate the anchor separately (via ComfyUI or `wan2gp-image-generation`), then do I2V with the same LoRA multiplier.

## Style LoRA checklist for T2V

1. Pick style LoRA from `$WAN_APP_DIR/loras/ltx2/`
2. Set multiplier to **0.8–1.5** (style LoRAs are invisible at 0.5)
3. Use `--model gguf` to skip compilation delay
4. Write a full scene description in the prompt (camera moves, action, mood, lighting)
5. Launch in background with `notify_on_complete=true`