---
name: neural-montage
description: High-engagement reel montage strategy (Neural Feed aesthetic)
---

# Neural Feed Reel Strategy

The "Neural Feed" aesthetic transforms a static montage into an AI agent's "internal monitoring" process.

## Creative Arc
1. **0-15s (Ingestion):** High-speed (0.2s cuts) montage of screenshots, overlayed with a digital HUD (grid/lines) to mimic an AI monitoring data.
2. **15-20s (Output):** Hard cut to Agent Avatar with "Processing Complete" notification.

## Production Protocol
1. **Montage:** 
   - Compile screenshots in `reels_screenshots/`.
   - Use `ffmpeg` to stitch at 0.2s duration per frame.
   - Example command: 
     `ffmpeg -f concat -safe 0 -i list.txt -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,drawtext=..." output.mp4`
2. **HUD Overlay:** 
   - Apply a semi-transparent grid overlay via `ffmpeg` filter `drawgrid`.
   - Add technical status text: `[ ANALYZING PATTERNS... ]`.
3. **Sound:** Layer "robotic ping" SFX at each edit point.
4. **Agent Cut:** Last 5s = Character Anchor PNG + Processing Overlay + final CTA.

## Implementation Pitfall: FFmpeg Filter Errors
- **Error:** `Invalid stream specifier` or `Error initializing filters`.
- **Cause:** Using `1080x1920` or complex filter strings where FFmpeg expects a simple mapping.
- **Fix:** Use a simpler concat pipeline with `concat` filter or `fconcat` to build the slideshow first, then add the `overlay` / `drawtext` filter in a second pass.
