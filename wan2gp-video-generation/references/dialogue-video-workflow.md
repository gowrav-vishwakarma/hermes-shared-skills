# Dialogue-Heavy Video Workflow

## The repetition problem

LTX-2.3 reads the `prompt` **ONCE across all frames**. If the dialogue finishes before the video duration ends, the model has no more text to follow and loops back to the **beginning of the prompt**, repeating the first lines.

### Symptoms
- 30s video with 10s of dialogue: the first 10s repeat for the remaining 20s
- "okay.. wait.." appears multiple times throughout the video
- Characters repeat the same expression/motion from the start

### Solutions

**Option A: Use 20s single pass (RECOMMENDED for dialogue)**
```json
{
  "video_length": 481,
  "sliding_window_size": 481
}
```
Single pass = prompt read once = no repetition. Shorten the dialogue to fit comfortably in 20s.

**Option B: 30s+ with sliding window — add visual closing beat**
If dialogue must be longer, end with a purely visual moment (wave, jump, smirk, camera pull-back) with **NO dialogue** for the remaining seconds. The model will loop to the start of the prompt, but if the first line is the visual closing action (not dialogue), the loop is less jarring.

Example: After the last spoken line, describe "Both characters jump up into the air simultaneously, arms raised, frozen in a moment of joy. Camera holds on the jump pose, sunlight flares through trees. No more speech."

The loop will repeat this visual beat, which is acceptable.

## Prompt structure for dialogue

```
EXT. LOCATION -- TIME. Opening composition description matching anchor.

[Camera movement]. [Character action] says "[line 1]". [Reaction/micro-action].
[Pause/describe silence]. [Character action] says "[line 2]". [Reaction].
[More dialogue with pauses between lines].
[Final line to camera]. [Reaction].
[Visual ending: jump/wave/smirk with NO speech description].
```

Use ellipses (...) between dialogue lines to signal pauses and slow the delivery:
- `"okay... so we got our Instagram account now..."` (slower, more natural)
- vs `"okay so we got our Instagram account now"` (rushed)

## generate_video_config.py flag reference

- `--prompt "text"` — the cinematic prompt (REQUIRED for text-based generation)
- `--image-start /path/to/anchor.jpg` — I2V anchor image
- `--video-prompt-type` — ONLY accepts PVG/OVG/DVG/EVG/VG/KFI (control video modes). For plain text prompts, **do NOT pass this flag**. Passing `--video-prompt-type S` is a known error — the prompt text gets consumed as the type value.
- For I2V with plain text: use `--prompt` + `--image-start`, no `--video-prompt-type`
- If shell quoting is problematic for long prompts, write to a `.txt` file and use `$(cat file.txt)`
- `--sliding-window-size 481` — for 20s single pass
- `--video-length 721` — for 30s with sliding window (requires `sliding_window_size < video_length`)
