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

## Special Case: Pure Divine Messages

**Exception:** Pure divine/holy message videos (featuring deities like Lord Shiva, Durga) do NOT require CTA. The sacred message itself is the complete content.

**Pattern:**
1. Final line of dialogue is the last line of the sacred teaching (no CTA)
2. Visual closing beat after the message (camera pull-back, clouds swirling, etc.)
3. No dialogue in the closing beat

**Example prompt structure (2026-05-12):**
```
"Slow dolly in, close-up on Lord Shiva. The radiant cosmic being speaks with divine authority. Third eye glows softly. Sacred ash and rudraksha beads visible. Golden light rays illuminate ethereal clouds around. The being says: 'In every challenge, there is an opportunity to trust. Surrender your fears to the divine and find peace within. Faith is not the absence of struggle, but the courage to believe even when you cannot see the path. Let go of control and trust in a greater plan. Your surrender is your strength.' The camera slowly pulls back as Lord Shiva offers a gentle, reassuring presence. Divine clouds swirl softly. Shot on Canon EOS R5, 85mm lens, cinematic divine lighting."
```

**Key observation:** The final line of dialogue ("Your surrender is your strength.") is the **last quoted text**. No CTA follows. Visual beat follows but contains no dialogue.

**Session evidence (2026-05-12):** `shiva_faith_motivation.mp4` generated successfully with pure divine message, no CTA, 20-second duration.

**Rule summary:**
- Avatar intros → CTA required, must be last quote
- Divine/holy messages → No CTA, message is complete content
- Motivational content → CTA optional ("Hit like and follow for more")

## Avoiding "flat" static output (CRITICAL)

LTX-2.3 I2V dialogue videos **default to static/flat output** — if the subject has no explicit motion described, they become a talking head with barely visible movement. The model needs explicit action cues.

**Always include dynamic movement cues** in the prompt for any character or creature monologue:
- **Head movements**: "head tilts left, then right", "nodding slightly", "head tilt for emphasis"
- **Facial expressions**: "slow blinking", "knowing smile", "raised eyebrows"
- **Body language**: "leans forward toward camera", "pulls back slightly", "gesturing with hands/wings"
- **Environment interaction**: "feathers ruffle in the breeze", "tail sways", "clothing flutters"
- **Camera movement**: "slow dolly-in", "subtle zoom on key phrase", "camera drifts left"
- **Progressive beats**: describe movements that happen *during* the speech, not just at the start or end

**Bad prompt (flat):**
> "A wise owl perched on a branch. The owl speaks. The owl says: 'Motivational quote here.' The camera holds on the owl."

**Good prompt (dynamic):**
> "Cinematic medium close-up of a wise owl perched on a branch. The owl slowly leans forward toward the camera, blinking slowly, then pulls back. Head tilts left then right as if pondering. Feathers ruffle slightly in the breeze. The owl says: 'Motivational quote here.' Gives a knowing slow blink, head tilts upward with a self-satisfied expression."

**Session evidence (2026-05-14):** First owl wisdom video was rejected as "too flat." Second version with explicit movement cues (leaning, tilting, blinking, feather ruffling) was accepted.

**When you can skip explicit movement:** Only for divine/holy message subjects (deities like Shiva, Durga) where the serene, still presentation is intentional and culturally appropriate.

## generate_video_config.py flag reference

- `--prompt "text"` — the cinematic prompt (REQUIRED for text-based generation)
- `--image-start /path/to/anchor.jpg` — I2V anchor image
- `--video-prompt-type` — ONLY accepts PVG/OVG/DVG/EVG/VG/KFI (control video modes). For plain text prompts, **do NOT pass this flag**. Passing `--video-prompt-type S` is a known error — the prompt text gets consumed as the type value.
- For I2V with plain text: use `--prompt` + `--image-start`, no `--video-prompt-type`
- If shell quoting is problematic for long prompts, write to a `.txt` file and use `$(cat file.txt)`
- `--sliding-window-size 481` — for 20s single pass
- `--video-length 721` — for 30s with sliding window (requires `sliding_window_size < video_length`)

## Writing Prompts from Real-World Source Images (Memes, Photos, Screenshots)

When the anchor image is a real-world scene (meme, photo, screenshot), the prompt must **translate visual elements into explicit cinematic description**. Never assume the model will "read" the image and know who does what — describe everything.

### Step 1: Analyze the Source Image First

**ALWAYS run `vision_analyze` on the source image before writing the prompt.** Ask it to identify:
- Who/what is in the image
- Their positions (left/center/right, foreground/background)
- Clothing and appearance details
- Current expressions and poses
- Spatial relationships between subjects

This produces the raw material for a detailed prompt — you'll know the exact clothing colors, who's where, and what they look like before you write the prompt.

### Step 2: Structure the Prompt — Positions + Actions + Dialogue

For multi-character scenes from source images, follow this exact structure:

```
Cinematic [shot type] of [scene description].

[NUMBER] CHARACTERS, LEFT TO RIGHT:
- On the FAR LEFT — [person] in [clothing], [what they're doing], [expression].
- In the CENTER — [person] in [clothing], [body orientation], [what they're doing/facing], [expression].
- On the FAR RIGHT — [person] in [clothing], [what they're doing/facing], [expression/mood].

MOVEMENT BEATS:
- [Character 1] does [specific motion 1], then [motion 2].
- [Character 2] does [specific motion 1], then [motion 2].
- [Character 3] does [specific motion 1], then [motion 2].

Camera [camera movement].

AUDIO — [character name] says/dicts/shouts: "[exact quoted dialogue 1]"
[char] responds/says: "[exact quoted dialogue 2]"
[char] interrupts: "[exact quoted dialogue 3]"
[char] deadpan/exclaims: "[exact quoted dialogue 4]"

Audio: [background sound description].
```

**Rules for dialogue quoting:**
- Each spoken line must be in **single quotes** with clear speaker attribution before it
- Use active verbs: *says, shouts, whispers, responds, interrupts, deadpan, exclaims, chuckles*
- Do NOT merge multiple speakers into one sentence — each dialogue line gets its own "X says:" line
- Include emotional tone cues inside the attribution: *nervously, sheepishly, deadpan, voice rising, chuckling*

**Example (Distracted Boyfriend meme, 2026-05-15):**
> "On the FAR LEFT — woman in a bright red sleeveless dress, long brown hair, walking AWAY from camera... In the CENTER — young man in a blue and white plaid shirt, body facing forward-left... but his HEAD is snapped back sharply over his RIGHT shoulder... On the FAR RIGHT — his girlfriend in a light blue sleeveless tank top... staring at HIM... MOVEMENT BEATS: The man slowly turns his head EVEN FURTHER back, a guilty but amused smirk spreading. The girlfriend slowly raises ONE HAND to her mouth in shock... AUDIO — girlfriend shouts 'Wait... are you LOOKING at her?!' The boyfriend tries to play it cool, chuckling nervously: 'Me? No. I just... uh...' The girlfriend interrupts, voice rising: 'YOU WERE STARING AT HER IN MY FACE!' The boyfriend sheepishly admits: 'Okay yes. She had a RED DRESS. You know how I feel about red.'"

**Session evidence (2026-05-15):** `distracted-meme/video_generation.json` — source image analyzed via `vision_analyze`, prompt written with full character positions, clothing details, explicit movement beats, and 6 dialogue lines each with speaker attribution and quotes.
