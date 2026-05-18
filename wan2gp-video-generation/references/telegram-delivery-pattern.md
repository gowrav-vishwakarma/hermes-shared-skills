# Telegram Media Delivery Patterns

## Known Issue: MP3 Upload Timeouts

**Pattern:** MP3 audio files (2-4MB) frequently timeout on Telegram upload, even with valid file paths.

**Observed behavior:**
- Files ~2.3MB often succeed
- Files ~3.9MB (320kbps) frequently timeout
- Smaller files (~1.6MB at 128kbps) are more reliable

**Workarounds that work:**
1. **Reduce bitrate:** `ffmpeg -i input.mp3 -b:a 192k -ar 44100 output.mp3` (brings files to ~2.3MB, more reliable)
2. **Smaller filename:** Sometimes helps (e.g., `s1.mp3` instead of long names)
3. **One at a time:** Don't batch send multiple media files in one message

**Workaround that doesn't help:**
- Copying to root home directory (~/) doesn't fix the issue
- Changing path format doesn't help

**Recommendation:** Convert all deliverables to 192kbps/44.1kHz MP3 before sending to Telegram for best reliability.

## Video Compression for Telegram

**Problem:** WanGP generates ~50-57MB MP4s. Telegram can handle this but compression speeds delivery and reduces bandwidth.

**Recommended compression:**
```bash
ffmpeg -y -i input.mp4 -vcodec libx264 -preset medium -crf 23 -acodec aac -b:a 128k -movflags +faststart output_tg_send.mp4
```

**Results (session 2026-05-17):** 56M → 8M, quality preserved. Use CRF 23 for balance — CRF 28 dropped to 3.7M but quality became blocky.

**Key flags:**
- `-crf 23` — quality compression (20-28 range, lower = better quality)
- `-movflags +faststart` — enables streaming/web playback
- `-preset medium` — balanced speed/quality
- `-b:a 128k` — audio bitrate

**Naming convention:** Suffix `_tg_send.mp4` so original is preserved.

**When to compress:** Always compress before sending video to Telegram. 8MB range is sweet spot — fast delivery, no visible quality loss.

## Stems Delivery Pattern

When delivering multiple stems via Telegram:
- Convert all WAV stems (19MB) to MP3 first (~2.3MB at 192kbps)
- Send intro text message FIRST
- Then send each stem as a separate message
- This avoids timeout accumulation across multiple files