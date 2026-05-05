# Video Compression Reference

WanGP LTX-2.3 outputs videos at very high bitrate (~36,000 kb/s, 70-88MB for 20s). Telegram max is 20MB, so compression is mandatory.

## Compression Command

```bash
ffmpeg -i <input.mp4> -vcodec libx264 -acodec aac -strict experimental \
    -b:v 2000k -b:a 128k -movflags +faststart \
    <output_compressed.mp4>
```

## Typical Results (RTX 4090, 720x1280, 20s video)

| Input Size | Output Size | Reduction | Quality |
|------------|-------------|-----------|---------|
| 54 MB (temple_come_down) | 4.7 MB | ~91% | Good |
| 88 MB (temple_dance) | 4.0 MB | ~95% | Good |
| 70 MB (temple_blessing) | 3.8 MB | ~95% | Good |
| 18 MB (cat_home_walk) | ~4 MB | ~78% | Good |

## When Compression Isn't Needed

If the original video is already under 20MB (e.g., the cat video at 18MB), skip compression and send directly.

## Timing

- Compression takes ~10-20 seconds for a 20s video.
- Always compress before sending to Telegram.