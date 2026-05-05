# Extended Video Output Files

## Problem

When WanGP generates extended videos with sliding windows (`--video-length > 481`), it produces **multiple output files** during a single job. This was initially mistaken for needing concatenation.

## Output Pattern

| File | Description |
|------|-------------|
| `{name}.mp4` | First window output (~20s, partial) |
| `{name}(2).mp4` | **FINAL COMPLETE VIDEO** (target duration, e.g. 30s+) |
| `{name}(3).mp4` | If 3+ windows, this is next in sequence |

## Key Rule

**The last file (`(N).mp4`) is the complete stitched video. Do NOT concatenate files.**

## Session Evidence

**2026-05-05, Meena nature reel (#24/2026-05-05_9):**
- Generated 30s reel with sliding window (721 frames, 2 windows)
- Got `nature_reel_30s.mp4` (20s) and `nature_reel_30s(2).mp4` (30s)
- Mistakenly concatenated → 50s garbage file
- Correct approach: compress and deliver `nature_reel_30s(2).mp4` directly
- Final result: 8.8MB, 30s ✅

## Checklist

1. After sliding window gen completes, list all `.mp4` files in output dir
2. Check duration of each — the longest is the complete video
3. That's your deliverable — compress and send it
4. Remove any partial/intermediate files
