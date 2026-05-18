# Post-Generation Video Compression

WanGP LTX-2.3 generates ~18-56 MB MP4 files — too large for Telegram (10-20 MB practical limit, much better UX under 5 MB).

## Compression command

```bash
ffmpeg -y -i input.mp4 -vcodec libx264 -preset medium -crf 23 -acodec aac -b:a 128k -movflags +faststart output_tg.mp4
```

## Typical results (RTX 4090)

| Original | After CRF 23 | Quality |
|----------|-------------|---------|
| 56 MB | 8 MB | Very good |
| 22 MB | 2.5-3 MB | Very good |
| 18 MB | 2 MB | Very good |

## When to use

**Always compress before sending** a video generated through WanGP via Telegram. This is the default workflow — never send the raw output.

## Parameter notes

- **CRF 23**: Good balance of quality/size. Use 20 for max quality (bigger file), 28 for smallest (visible artifacts).
- **Preset medium**: Good speed/quality tradeoff. Use `slow` for smaller files (slower encode).
- **`-movflags +faststart`**: Required for web/Telegram streaming — puts moov atom at file start.
- **Audio AAC @ 128k**: Standard quality, minimal overhead (~1 MB for 20s).
