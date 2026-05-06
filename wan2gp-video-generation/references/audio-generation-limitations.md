# LTX-2.3 Audio Generation Limitations

## No External Audio Input

LTX-2.3 **does NOT accept external audio files** (mp3, wav, flac) as input for video generation. The pipeline has no mechanism to load an audio track and layer it onto a video.

## How Audio Works

- **Dialogue**: Text wrapped in double quotes in the prompt → LTX-2.3 generates speech via built-in TTS
- **Audio direction**: Descriptions in the prompt (e.g., "warm confident voice, slight Indian accent, upbeat lofi music") → sets voice style, accent, and background audio

## Implications

- **No lip-sync to external audio**: If you have a pre-recorded audio file, LTX-2.3 cannot match character lip movement to it
- **AI-generated voice only**: All speech comes from the model's internal TTS, controlled by prompt dialogue in quotes
- **Post-sync alternative**: Generate a silent/ambient video, then use ffmpeg to overlay external audio — but lip-sync won't match

## Workaround for Custom Audio

If you must use a specific audio recording:
1. Generate video with placeholder dialogue (or ambient audio only)
2. Use `ffmpeg -i video.mp4 -i audio.mp3 -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 output.mp4` to layer the audio
3. Accept that character lip movement will NOT match the audio content

Session 2026-05-05 confirmed this limitation with Gowrav's request.
