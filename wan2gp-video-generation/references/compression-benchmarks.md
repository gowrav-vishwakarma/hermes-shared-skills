# Compression Benchmarks

Session 2026-05-05 — 6-scene cinematic guitar music video (1280x720, ~20s each, distilled-1.1)

| Scene | Raw Size | Compressed | CRF/Bitrate | Compression Ratio |
|-------|----------|------------|-------------|-------------------|
| Scene 1 (Cliff) | 29 MB | 2.4 MB | CRF 28, maxrate 3M | ~92% |
| Scene 2 (Practice) | 30 MB | 2.2 MB | CRF 28, maxrate 3M | ~93% |
| Scene 3 (Neon City) | 33 MB | 2.5 MB | CRF 28, maxrate 3M | ~92% |
| Scene 4 (Stage) | 36 MB | 2.7 MB | CRF 28, maxrate 3M | ~93% |
| Scene 5 (Climax) | 38 MB | 2.8 MB | CRF 28, maxrate 3M | ~93% |
| Scene 6 (Outro) | 16 MB | 2.2 MB | CRF 28, maxrate 3M | ~86% |

**Command:**
```bash
ffmpeg -i <input.mp4> -vcodec libx264 -crf 28 -maxrate 3M -bufsize 2M -acodec aac -strict experimental -movflags +faststart <output_compressed.mp4> -y
```

**Notes:**
- All scenes compressed in ~5-10 seconds each (ffmpeg is very fast)
- CRF 28 + maxrate 3M consistently achieves ~92-93% compression while maintaining visual quality
- All compressed scenes well under 5MB Telegram limit
- Average bitrate ~500-1350 kb/s (well under 2000k)
- Scene 6 had lower raw size (16MB) but compressed to same 2.2MB — suggests the scene had less motion/detail
