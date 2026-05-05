# LTX-2.3 Model Configurations Reference

Two LTX-2.3 22B checkpoints are available. The helper script `generate_video_config.py` selects the right one via `--model <alias>`.

## Quick-reference table

| Alias | Checkpoint file | Size | `model_type` | Steps | Solver | Notes |
|---|---|---|---|---|---|---|
| `gguf` (default) | `ltx-2.3-22b-distilled-Q6_K_light.gguf` | 16 GB | `ltx2_22B_distilled_gguf_q6_k` | 8 | template default | Fastest. GGUF Q6_K quantized. Good for iteration. |
| `distilled-1.1` | `ltx-2.3-22b-distilled-1.1_diffusion_model_quanto_bf16_int8.safetensors` | 19 GB | `ltx2_22B_distilled_1_1` | 8 | template default | Distilled v1.1. WanGP auto-loads HDR, outpaint, and union-control LoRAs internally when needed. |

Both share `base_model_type: "ltx2_22B"`.

## gguf (default)

- **When to use**: Day-to-day iteration, quick previews, batch renders.
- **Steps**: 8 (distilled -- more steps give diminishing returns).
- **Guidance scale**: 1--3 works well; templates default to 3.
- **LoRAs**: None baked in. Templates ship with empty `activated_loras`. Add LoRAs explicitly via `--activated-loras` / `--loras-multipliers`.
- **VRAM**: ~16 GB peak with `--profile 4 --fp16`.

## distilled-1.1

- **When to use**: When you want the distilled speed (8 steps) but need WanGP's built-in HDR/outpaint/union-control LoRA support. These LoRAs are loaded automatically by WanGP when the model type is `ltx2_22B_distilled_1_1` -- they do NOT appear in `activated_loras` in the JSON.
- **Steps**: 8.
- **Guidance scale**: Same as gguf (1--3, default 3).
- **LoRAs**: WanGP auto-loads these internally (not in our template):
  - `ltx-2.3-22b-ic-lora-union-control-ref0.5.safetensors`
  - `ltx-2.3-22b-ic-lora-outpaint.safetensors`
  - `ltx-2.3-22b-ic-lora-hdr-0.9.safetensors`
  - `ltx-2.3-22b-ic-lora-hdr-scene-emb.safetensors`
- **VRAM**: ~19 GB peak.

## Guidance scale advice

Both models respond well to `guidance_scale` 1--3. Values above 5 cause over-saturation and colour blow-out. The helper script sets guidance_scale from the model config only when `--guidance-scale` is not explicitly passed.

## Helper flag precedence

The `--model` flag sets model-level defaults (steps, solver, guidance, perturbation). Explicit CLI flags always win:
- `--steps 15` overrides the model's default step count.
- `--guidance-scale 2.0` overrides the model's default guidance.
