# Aggressive Compression for Telegram Delivery

## When to use

Standard CRF 23 compression (per `post-gen-compression.md` and `video-delivery-pattern.md`) produces 2-8 MB files that usually work. Use this aggressive profile when:
- Standard compression still results in a file that times out on `send_message(target="telegram")`
- The raw video is unusually large (>40 MB) and CRF 23 alone isn't enough
- You need a guaranteed sub-2 MB file for maximum reliability

## Compression profiles (escalating)

### Profile 1: Standard (use first every time)

```bash
ffmpeg -y -i input.mp4 -c:v libx264 -crf 30 -preset faster -acodec aac -b:a 64k -movflags +faststart output.mp4
```

### Profile 2: Aggressive (when standard still times out)

```bash
ffmpeg -y -i input.mp4 -c:v libx264 -crf 30 -preset faster -acodec aac -b:a 64k -movflags +faststart output_aggressive.mp4
```

### Profile 3: Nuclear (session 2026-05-18 — 20s raw 23MB → ~600 KB, no timeout)

```bash
ffmpeg -y -i input.mp4 -c:v libx264 -preset veryfast -crf 34 -b:v 600k -maxrate 600k -bufsize 1M -c:a aac -b:a 32k -movflags +faststart output_nuclear.mp4
```

**Parameters that matter most for size:**
- `-crf 34` — quality (34 = very small, visible blockiness)
- `-b:v 600k` — hard bitrate cap (dominates over CRF when both set)
- `-b:a 32k` — audio at minimum tolerable (fine for ambient/no-dialogue clips)
- `-maxrate 600k -bufsize 1M` — prevents bitrate spikes

### Parameter comparison

| Parameter | Standard | Aggressive | Nuclear |
|-----------|----------|------------|---------|
| CRF | 30 | 30 | 34 |
| Video bitrate | N/A (CRF-controlled) | N/A (CRF-controlled) | 600k hard cap |
| Audio | 64k | 64k | 32k |
| Preset | faster | faster | veryfast |

## Typical results (session 2026-05-18)

| Original | Aggressive output | Quality |
|----------|-------------------|---------|
| 29 MB | 940 KB | Acceptable for short clips |

## Fallback strategy

1. Compress with standard profile (CRF 23, medium preset)
2. Try `send_message` with standard compressed file
3. If timeout: compress with aggressive profile (CRF 30, faster preset)
4. Try `send_message` again with aggressively compressed file
5. If still timeout: try sending via `send_message(action='list')` to find the correct target name first

## Quality notes

- CRF 30 introduces visible blockiness on complex scenes
- For Pixar/animation style (flat colors, clean edges), CRF 30 looks much better than on photorealistic content
- Audio at 64k AAC is fine for 10-20s clips with no dialogue