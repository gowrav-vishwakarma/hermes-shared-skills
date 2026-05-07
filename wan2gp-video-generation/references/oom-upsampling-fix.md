# Upscaling OOM Fix — May 2026

## Problem
Upscaling phase OOM (exit code -9) after successful denoising. GPU has freed up from denoising but upscaler loads additional latent buffers.

## Affected Settings
- `temporal_upsampling`: rife4, rife2
- `spatial_upsampling`: lanczos1.5, lanczos1.3
- `RIFLEx_setting`: 1 (does NOT cause OOM)

## Pattern
- All 8 denoising first pass steps complete ✅
- VAE decoding completes ✅
- Denoising second pass completes ✅
- `[0/1] Upsampling` → SIGKILL / exit code -9 ❌

## Fix (Verified 2026-05-07)
Remove BOTH upscalers. Keep RIFLEx for smoothness:
```json
"temporal_upsampling": "",
"spatial_upsampling": "",
"RIFLEx_setting": 1
```

## Benchmark — Meena Intro Reel (3 runs)

| Run | Crisp | Temporal | Spatial | RIFLEx | Result | Time | Raw Size |
|-----|-------|----------|---------|--------|--------|------|----------|
| 1 | 0.5 | rife4 | lanczos1.5 | 1 | OOM (exit -9) | — | — |
| 2 | 0.8 | rife2 | removed | 1 | Success | 5m 33s | 25MB |
| 3 | 1.0 | removed | removed | 1 | Success | 3m 52s | 32MB |
| 4 | 0.9 | removed | removed | 1 | Success | 4m 04s | ~24MB |

## Notes
- Removing upscalers = faster gen (skips upscaling step entirely)
- CrispEnhancer @ 0.8–1.0 all work without OOM when upscalers removed
- Raw file size scales with LoRA weight (sharper = more detail = larger)
- Compress with ffmpeg at 2000k video bitrate → ~5MB output
