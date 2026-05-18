# Telegram Video Compression Reference

## Compression parameters for Instagram/Telegram delivery

When delivering videos via Telegram, always compress the native WanGP output. Use these parameters:

```bash
ffmpeg -y -i <original.mp4> -vcodec libx264 -preset medium -crf 23 -acodec aac -b:a 128k -movflags +faststart <output_tg.mp4>
```

### CRF Sweet Spot: 23

- **CRF 28** → too aggressive, visible blockiness (e.g., 56M → 3.7M)
- **CRF 23** → clean visual quality, good compression (e.g., 18-22M → 2.5-4.0M)
- **CRF 20** → near-lossless, files stay large (30M+)

CRF 23 consistently produces files under 5M while preserving Pixar animation quality. Telegram's file limit is 20M for non-premium, so CRF 23 leaves safe headroom.

### Size expectations (LTX-2.3, 20s, 9:16, Pixar_Toon)

| Original | CRF 23 TG | Quality |
|----------|-----------|---------|
| 18M | 2.0M | Good |
| 20M | 2.5M | Good |
| 22M | 2.5-3.1M | Good |
| 32M | 4.0M | Good |
| 56M | 8.0M | Acceptable |

### Always include `-movflags +faststart`

This repositions the moov atom to the beginning of the file so streaming works before the full download completes.
