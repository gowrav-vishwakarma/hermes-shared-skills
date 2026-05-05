# Video Delivery to Telegram

## The Problem

Videos are WAY too big for Telegram. Original 20s LTX outputs are 40-50MB. These will TIMEOUT every time.

## Compression Recipe

**The command that works reliably:**
```bash
ffmpeg -y -i input.mp4 -c:v libx264 -preset medium -crf 28 -maxrate 3M -bufsize 6M -c:a aac -b:a 96k -movflags +faststart output_compressed.mp4
```

**Parameter rationale:**
- CRF 28: Good quality/size tradeoff (lower=larger, higher=smaller)
- -maxrate 3M: Hard cap prevents bitrate spikes
- -bufsize 6M: 2x maxrate for VBR stability
- Audio 96kbps: Sufficient for most content, saves space
- -movflags +faststart: Enables streaming/progressive download

**Expected compression results (20s video):**
- 44MB original → ~11MB (CRF 22, 5M maxrate) — MAY STILL TIMEOUT
- 44MB original → ~4.5MB (CRF 28, 3M maxrate) — RELIABLE ✓

**If 4.5MB still times out, go even smaller:**
```bash
ffmpeg -y -i input.mp4 -c:v libx264 -preset medium -crf 32 -maxrate 2M -bufsize 4M -c:a aac -b:a 64k -movflags +faststart output_tiny.mp4
```

## Telegram Sending Pattern

1. Generate video (40-50MB)
2. **COMPRESS to <5MB** using recipe above
3. Send with `MEDIA:/path/to/compressed.mp4`
4. If timeout persists, compress further with CRF 32

**NEVER send uncompressed or lightly compressed videos (>10MB)**

## Workflow Integration

Always compress AFTER generation, before Telegram delivery. This is not optional — it's required for reliable delivery.