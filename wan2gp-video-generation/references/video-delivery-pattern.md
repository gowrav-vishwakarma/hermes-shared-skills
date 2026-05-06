# Video Delivery to Telegram

## Compression Recipe

**Working command (bitrate-based, simple and reliable):**
```bash
ffmpeg -i input.mp4 -vcodec libx264 -acodec aac -b:v 2000k -b:a 128k -movflags +faststart output_compressed.mp4
```

**Expected results (720x1280, 20s):** ~3.8-4.7 MB (~91-95% reduction from ~70-88MB). Takes ~10-20s. Skip compression if input is already <20MB.

> **Pitfall: Do NOT use CRF/maxrate approach.** Earlier recipe used `crf 28 -maxrate 3M` which is slower and more complex. The bitrate-based approach (`-b:v 2000k -b:a 128k`) is the established working pattern.

## Telegram Sending Pattern

**CRITICAL: `MEDIA:/absolute/path/to/file` must be on its OWN LINE, with NO surrounding text or markdown formatting.** If mixed with other text, Telegram renders it as a link instead of a file attachment.

**Correct format:**
```
✨ Here is your video!

MEDIA:/home/gowrav/.hermes/profiles/meena/home/posts/2026-05-06_1/tn_election_news_compressed.mp4
```

**Wrong format (renders as link, not file):**
```
✨ Here is your video! Media:/home/gowrav/.../tn_election_news_compressed.mp4
```

## Workflow Integration

1. Generate video (~70-88MB)
2. **COMPRESS** to ~3-5MB using bitrate command above
3. Send with `MEDIA:/path/to/compressed.mp4` **on its own line only**
4. If input is already <20MB, skip compression and send directly