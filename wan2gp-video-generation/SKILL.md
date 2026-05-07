---
name: wan2gp-video-generation
description: LTX-2.3 video generation via WanGP -- director-style prompting, audio direction, I2V coherence
category: media
---

# WanGP Video Generation (LTX-2.3)

Generate videos with native audio using **LTX-2.3 22B distilled** through WanGP CLI. Default is ~20 s (481 frames @ 24 fps) in a single pass. For longer videos, WanGP's **sliding window** mechanism generates multiple overlapping windows and stitches them -- see "Extended Videos" below. Supports **text-to-video** (T2V) and **image-to-video** (I2V) -- the helper auto-picks from `--image-start`.

## Environment variables

**CRITICAL: The `.env` file is NOT auto-sourced into agent subprocess shells.** Before running any helper script, you MUST manually source it:

```bash
set -a; source $PROFILE_ROOT/.env; set +a
```

Or in Python subprocess calls, explicitly pass the env dict after sourcing:
```python
import os
env = os.environ.copy()  # ALWAYS start from os.environ to preserve PATH, SHELL, HOME
with open('$PROFILE_ROOT/.env') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            env[k.strip()] = v.strip()
```

**CRITICAL: Never build env from scratch.** If you do `env = {}` then merge `.env` keys, critical system vars (`PATH`, `SHELL`, `HOME`) are lost, causing crashes like `KeyError: 'PATH'` in pydub. ALWAYS start from `os.environ.copy()` first. See `references/env-path-overwrite-pitfall.md` for full details.

Helper scripts are strict consumers; missing keys trigger `[env] required env var ... not set`.

**NOTE on `$PROFILE_SKILLS`:** In this profile, it points to `/home/gowrav/.hermes/shared-skills` (NOT the local skills dir). Verify: `grep PROFILE_SKILLS $PROFILE_ROOT/.env`.

Used by this skill:

- `PROFILE_HOME` -- profile workspace
- `PROFILE_SKILLS` -- shared skills dir (`/home/gowrav/.hermes/shared-skills` in this profile)
- `POSTS_DIR` -- `$PROFILE_HOME/posts`
- `WAN_APP_DIR` -- WanGP app dir (contains `wgp.py`, `env/bin/python`)
- `WAN_PYTHON` -- `$WAN_APP_DIR/env/bin/python`
- `CHARACTER_ASSETS_DIR`, `CHARACTER_ASSETS_MANIFEST`, `CHARACTER_BASE` -- needed when video prompts use `--ref-assets <slug>`

Always pass absolute paths to `--image-start` and `--output-dir`.

---

## Video Prompting Guide

LTX-2.3 responds best to prompts written like a shot description for a cinematographer. The more specific you are about subject, action, lighting, camera movement, and audio, the closer the output matches your vision. Think of it as directing a scene -- you are the director.

### Core Principles

**Be specific and descriptive.** Instead of "a person walking," write "a young woman in a red coat walking briskly through a rain-soaked Tokyo street at night, neon reflections on wet pavement, handheld camera following from behind."

**Describe the full scene.** Include the subject, their action, the environment, the lighting, and the camera behavior. The more complete the description, the closer the output matches your intent.

**Use cinematic language.** Terms like "macro lens," "tracking shot," "shallow depth of field," "golden hour," "low angle," "CUT TO," "DISSOLVE" are understood by the model and directly influence the output.

**Describe audio when relevant.** Include audio descriptions: "the sound of rain on pavement," "soft ambient music," "a crowd cheering in the distance."

**Long prompts for long videos.** LTX-2.3's redesigned text connector makes it significantly more responsive to prompt details. Specific descriptions of facial expressions, timing, pauses, and emotional beats translate reliably into the output. A short prompt for a long video (8-20 seconds) results in the model rushing through the described action or filling time with static frames. Match prompt length to video length.

**Iterate freely.** LTX is designed for fast experimentation. Start simple and layer complexity gradually.

---

### The 6 Key Elements

Every prompt should aim to include these:

#### 1. Establish the Shot

Use cinematography terms matching your intended genre. Include shot scale or style characteristics. Leading the prompt with camera movement sets a temporal anchor -- the model uses it to structure everything that follows.

Examples: "Slow dolly in, close-up on a young man's eyes," "Cinematic medium shot," "Tight close-up," "Wide establishing shot," "Handheld POV," "Over-the-shoulder."

#### 2. Set the Scene

Describe lighting conditions, color palette, surface textures, and atmosphere to establish mood and tone. Sensory detail shapes mood more than adjectives -- describe what the light does, what the air carries, what surfaces feel like.

LTX-2.3 understands spatial positioning -- use terms like "left of frame", "foreground", "background", "center frame", "far right" to place subjects precisely.

**Lighting:** Flickering candles, Neon glow, Natural sunlight, Dramatic shadows, Backlighting, Rim light, Polar cold white light, Harsh noon sunlight, Cold neon tubes casting warped reflections, Stage spotlight with everything else in deep shadow, Colored light filtering through stained glass, Warm early sun reflecting off glass.

**Textures:** Rough stone, Smooth metal, Worn fabric, Glossy surfaces, Matte metal shell, Frozen lake surface, Rough volcanic rock, Wet carbon fiber, Rain-beaded waterproof fabric.

**Color palette:** Vibrant, Muted, Monochromatic, High contrast, Cyberpunk purple and teal, Earthy ochre and deep moss green, Cool blue-green grading, Warm golden tones.

**Atmosphere:** Fog, Rain, Dust, Smoke, Particles, Turbulent clouds at high altitude, Cold mist beneath aurora, Diffused light within a sandstorm, Fine rain slanting through air glowing beneath streetlights, Ocean wind carrying salty chill pushing sand grains across beach.

#### 3. Describe the Action and Blocking

Write the core action as a natural sequence, flowing clearly from beginning to end. Not a list -- a screenplay.

Static descriptions without verbs produce still-image output. Even for calm scenes, include motion verbs: "adjusts her scarf", "shifts her weight", "breathes deeply", "steam curls from the mug".

**Blocking** is the choreography between subject movement and camera movement. Describe them as interleaved -- what the subject does, then how the camera responds, then what the subject does next:

> She steps forward through the corridor, and the camera tracks sideways to follow. She pauses at the viewport, pressing her hand against the glass, as the camera slowly pushes in past her shoulder, revealing the planet filling the window beyond.

**Temporal connectors** keep actions flowing naturally. Use *as*, *then*, *while*, *before*, *after*, *when* between actions instead of starting each sentence cold. Describe cause-and-effect ("the door opens and a rush of air bursts inward").

**Choppy (avoid):**
> She opens the door. She steps inside. She looks around.

**Connected (use this):**
> As the heavy metal hatch slides open, cold mist spills from the vents. She steps forward through the fog, then the camera tracks sideways, following her as she moves steadily down the illuminated corridor.

#### 4. Define the Character(s)

Include age, hairstyle, clothing, and distinguishing features. Express emotion through **physical cues, not abstract labels**.

**Good:** "Her jaw tightens, she blinks rapidly, hand gripping the rail."
**Bad:** "She feels nervous and scared."

The model cannot render "nervous" -- it can render tightened jaw, rapid blinking, white-knuckled grip.

#### 5. Camera Movement

Specify how and when the camera moves. Describing how subjects appear *after* the movement helps the model complete the motion accurately. See the full Camera Movements Catalog below for 35+ movements with copy-paste prompt phrases.

#### 6. Audio

Clearly describe ambient sound, music, speech, or singing. Spoken dialogue in **quotation marks** -- quotes are **mandatory**. Missing quotes produces gibberish/mouthless speech.

- Describe the **acoustic space** -- "echoey hall", "muffled small room", "outdoor open-air", "reverberant cathedral"
- Specify language and accent if needed: "Hindi-accented English, warm intimate tone"
- **Ambient:** Coffeeshop noise, Wind and rain, Forest ambience with birds, Distant traffic hum
- **Dialogue style:** Energetic announcer, Resonant voice with gravitas, Distorted radio-style, Robotic monotone, Childlike curiosity
- **Volume:** Whisper, Mutter, Shout, Scream

---

### Format Rules

- Single flowing paragraph; no line breaks inside the prompt string.
- Present tense verbs for all action and movement.
- **Temporal connectors** -- link actions with *as*, *then*, *while*, *before*, *after*.
- Match detail level to shot scale: close-ups need more precision than wide shots.
- **Close-up to wide** -- starting with a close-up helps retain facial/material detail; widening afterwards reveals the environment without losing identity.
- **Soft closing actions** -- ending with a held moment or gentle camera drift prevents frozen frames at the end of long prompts.
- **Multi-character pacing** -- for 2+ characters, linger on one speaker before panning to the next. Physical handoffs (gesture, gaze direction) motivate camera transitions. Max 2-3 characters per shot.
- **Smooth reframing** -- gradual transitions ("the camera slowly pans right") produce cleaner output than jarring zooms or snap reframes.

---

### Cinematic Transitions

LTX-2.3 understands cinematic transition language. Use these to structure multi-beat scenes:

| Transition | Prompt phrase | Effect |
|------------|--------------|--------|
| Hard Cut | `CUT TO:` | Abrupt scene/angle change |
| Jump Cut | `JUMP CUT` | Time skip within same scene |
| Smash Cut | `SMASH CUT TO:` | Jarring contrast cut for comedic/dramatic effect |
| Dissolve | `DISSOLVE TO:` | Gradual blend between scenes |
| Fade | `Fade-in / Fade-out` | Scene opening/closing |
| Match Cut | `MATCH CUT TO:` | Visual similarity bridges two different scenes |
| Whip Pan Transition | `Whip pan transition to` | Fast pan connecting two locations |

**I2V note:** When using `--image-start`, the decode is a single continuous shot from the anchor. Cuts create a visual discontinuity rather than a true multi-camera edit -- this can produce interesting stylistic results or artifacts depending on the content. Camera moves (dolly, pan, tilt) remain the smoothest way to reveal new elements in I2V.

---

### Camera Movements Catalog

Copy the **prompt phrase** directly into your video prompt at the point where you want the movement to occur. Combine with acting beats and dialogue segmentation. Keep combinations to two moves per shot -- stacking three or more competing motions confuses the model.

#### Dolly / Track

| Movement | Prompt phrase | When to use |
|----------|--------------|-------------|
| Slow Dolly In | `Slow dolly in, camera moves slowly forward toward the subject` | Build intimacy or tension |
| Slow Dolly Out | `Slow dolly out, camera moves slowly backward away from the subject` | End a scene, reveal isolation |
| Fast Dolly In | `Fast dolly in, camera moves rapidly forward toward the subject, urgent motion` | Shock, sudden realization |
| Reveal from Behind | `Camera slides laterally from behind foreground object to reveal the scene` | Dramatic scene reveals |
| Through Shot | `Fly through, camera moves through an opening into the scene` | Enter a new environment; portal reveals |
| Leading Shot | `Leading shot, camera moves backward matching the subject's speed` | Face-on dialogue while walking |
| Following Shot | `Following shot, camera follows behind the subject matching speed` | Chase, journey, pursuit |
| Side Tracking | `Side tracking, camera trucks alongside the subject` | Walking conversations; parallel motion |
| Truck Left | `Truck left, camera moves sideways on a track to the left` | Lateral reveal to the right |
| Truck Right | `Truck right, camera moves sideways on a track to the right` | Lateral reveal to the left |

#### Zoom / Lens

| Movement | Prompt phrase | When to use |
|----------|--------------|-------------|
| Smooth Optical Zoom In | `Smooth optical zoom in, lens magnifies subject, camera stays stationary` | Isolate a detail without physical motion |
| Smooth Optical Zoom Out | `Smooth optical zoom out, lens widens, background becomes blurry` | Pull back to reveal context |
| Snap Zoom (Crash Zoom) | `Snap zoom, crash zoom, rapid zoom directly into the subject` | Comedic punch, sudden focus |
| Extreme Macro Zoom | `Extreme macro zoom, zoom transition from subject to micro details of surface` | Texture reveals -- skin, fabric, materials |
| Cosmic Hyper Zoom | `Cosmic hyper zoom, fast zoom transition from extreme wide view down to macro level` | Universe-to-atom scale transitions |
| Vertigo Effect (Zolly) | `Vertigo effect, dolly zoom, camera moves backward while zooming in, background expands` | Disorientation, psychological dread |
| Rack Focus | `Rack focus, focus shifts from the foreground object to the background subject` | Redirect attention between depth planes |
| Reveal from Blur | `Rack focus, start completely out of focus, slowly pull focus until sharp` | Dream-to-reality transition |
| Fisheye Lens | `Fisheye lens, extreme wide-angle distortion, circular frame` | Surreal POV, peephole view |

#### Pan / Tilt

| Movement | Prompt phrase | When to use |
|----------|--------------|-------------|
| Tilt Up | `Tilt up, camera pans vertically up from bottom to top` | Reveal height, grandeur |
| Tilt Down | `Tilt down, camera pans vertically down from top to bottom` | Descend from sky to ground |
| Whip Pan | `Whip pan, camera whips violently to the side with extreme directional motion blur` | Snap transitions, comedic timing |

#### Orbit / Arc

| Movement | Prompt phrase | When to use |
|----------|--------------|-------------|
| Orbit 180 | `Orbit 180, camera moves in a half-circle around the subject` | Hero reveal; multiple angles in one shot |
| Fast 360 Orbit | `Fast 360 orbit, camera spins rapidly 360 degrees around the subject` | High-energy emphasis; music-video drama |
| Slow Cinematic Arc | `Slow cinematic arc, camera moves in a wide curve to reveal side profile` | Contemplative reveal; beauty shot |

#### Crane / Pedestal

| Movement | Prompt phrase | When to use |
|----------|--------------|-------------|
| Crane Up | `Crane up, camera lifts high into the air` | Triumphant reveal; escalate to epic scale |
| Crane Down | `Crane down, camera descends slowly to the subject` | Arrival; settling into a scene |
| Pedestal Up | `Pedestal up, camera rises vertically straight up from waist to eye level` | Gradual character reveal |
| Pedestal Down | `Pedestal down, camera lowers vertically straight down` | Shift focus to ground level |

#### Drone / Aerial

| Movement | Prompt phrase | When to use |
|----------|--------------|-------------|
| Drone Fly Over | `Drone fly over, high altitude flight moving forward over the landscape` | Establishing shots; travel sequences |
| Epic Drone Reveal | `Epic drone reveal, rising and tilting down to reveal the scene` | Grand opening; reveal a location |
| Top Down (God's Eye) | `Top down shot, camera pointing straight down, slow twist` | Abstract composition; overhead reveal |

#### Stylized / Effect

| Movement | Prompt phrase | When to use |
|----------|--------------|-------------|
| Handheld Documentary | `Handheld camera, shaky motion, natural movement, documentary style` | Raw authenticity; vlog feel |
| Dutch Angle (Roll) | `Dutch angle, camera roll, tilted sideways on Z-axis` | Unease, instability, tension |
| POV Walk | `POV walk, first person camera moving forward with bobbing motion` | Immersive exploration; horror |
| Over the Shoulder | `Over the shoulder shot, camera mounted behind subject A framing subject B` | Dialogue scenes; spatial relationship |
| Hyperlapse | `Hyperlapse, camera moves forward rapidly, time accelerated, fast motion, light trails` | Time passage; city energy |

#### Combining Movements

The most dramatic shots layer a camera move with an acting beat and a reveal:

> A slow dolly-in past her shoulder reveals the nebula filling the viewport.

> Crane up, camera lifts high into the air, then tilts down to reveal the sprawling city below.

> The camera arcs in a slow cinematic orbit around her, rack focus shifting from her face to the glowing skyline behind.

> Handheld camera, documentary style, suddenly snap zooms into his widening eyes.

---

### Lens Language and Visual Style

#### Focal Length

| Focal length | Prompt phrase | Effect |
|--------------|--------------|--------|
| 24mm wide angle | `24mm wide angle lens` | Strong sense of space; slight barrel distortion |
| 50mm standard | `50mm standard lens` | Natural human-eye perspective; neutral compression |
| 85mm portrait | `85mm portrait lens` | Compression and intimacy; flattering close-ups with soft background |
| 200mm telephoto | `200mm telephoto lens` | Extreme depth compression; isolates subject from background |
| Macro lens | `Macro lens, extreme close-up` | Reveals micro details -- textures, pores, droplets |

#### Shutter and Motion Feel

| Description | Prompt phrase | Effect |
|-------------|--------------|--------|
| Cinematic motion blur | `180 degree shutter, classic cinematic motion blur` | Standard film look; smooth natural blur |
| Crisp action | `Fast shutter, crisp motion, sharp detail` | High-energy with frozen detail |
| Natural blur | `Natural motion blur, fluid movement` | Realism without excessive smearing |

#### Visual Style and Color Grading

| Style | Prompt phrase |
|-------|--------------|
| Film stock emulation | `Fujifilm Provia 100F film texture` or `Kodak Portra 400 color science` |
| High contrast grading | `High contrast image, cool blue-green grading` |
| Desaturated | `Muted color palette, desaturated tones` |
| Warm analog | `Warm analog film, golden tones, soft grain` |
| Noir | `Film noir, high contrast black and white, dramatic shadowing` |
| Cyberpunk | `Cyberpunk purple and teal contrast, neon gradient glow` |
| Earthy natural | `Earthy ochre and deep moss green palette` |

#### Keywords for Smooth Motion

**Camera stability:** Stable dolly push, Smooth gimbal stabilization, Tripod locked off, Constant speed pan.
**Motion quality:** Natural motion blur, Fluid movement, Controlled motion, Stable tracking.
**Avoid:** Chaotic handheld (introduces warping), Shaky camera, Irregular motion.

---

### Duration-Based Prompt Strategy

Match prompt length and structure to the target duration.

#### Short-form: under 5 seconds

One clear action, simple camera work, minimal scene complexity.

> A silver coin is flicked from a thumb, flipping rapidly through the air before landing precisely back in a palm. Close-up, shallow depth of field, crisp cold metallic reflections.

#### Mid-form: 5-10 seconds

A micro-narrative with beginning, middle, end. 2-3 connected actions with one fluid camera motion.

> An astronaut reaches out to touch the viewport, her fingertips gliding across the cold glass as she gazes at the swirling blue planet outside. The camera slowly dollies forward, shifting the focus from her immediate reflection to the vast, shimmering expanse of the cosmos.

#### Long-form: 15-20 seconds (481 frames)

A mini-scene with three-act structure. Long detailed prompts pay off here -- a 10-word prompt for 20 seconds leaves the model directionless.

**Recommended structure:**

1. **Scene header** -- place and time: `INT. BEDROOM -- MORNING` or `EXT. TOWN SQUARE -- DAWN`
2. **Opening beat (0-4 s)** -- where the subject is, what they do first, atmosphere. Start with a close-up to ground detail, then widen.
3. **Blocking + dialogue (4-15 s)** -- interleaved subject actions, camera moves, and 2-3 short dialogue lines with acting beats.
4. **Closing beat (15-20 s)** -- a final spoken line, a held reaction shot, or a gentle camera pull-back.

---

### Dialogue Segmentation (MANDATORY for any speaking character)

This is the single biggest quality lever for talking-head videos. A monologue produces static frames; segmented dialogue with acting beats produces visible motion.

#### The Pattern

Break dialogue into **2-4 short quoted lines** (5-15 words each). Between each line, insert a **physical acting beat** -- a gesture, a camera move, or an environmental reaction.

**Critical: Every spoken line MUST be wrapped in double quotes.** Omitting quotes makes LTX-2.3 produce gibberish -- the model interprets quoted text as speech and non-quoted text as narration.

**Flat (static talking head -- avoid):**
> The character speaking: "Oh my god you can see this with me this is what astronomers call a stellar aurora when the nebula's charged particles dance with magnetic fields I've never seen anything like it."

**Segmented (visible motion -- use this):**
> He turns toward the camera, Hindi-accented English, warm intimate tone, "You are seeing this with me, right?" He steps closer to the dome, palm pressing against the glass. "That is a stellar aurora -- charged particles dancing on the nebula's magnetic field lines." His eyes widen, breath fogging the visor briefly, voice dropping to near-whisper, "I have never seen colours move like this." A slow dolly-in past their shoulder reveals emerald and crimson ribbons twisting overhead. Audio: low station hum, soft plasma crackle, intimate close-mic.

#### Why It Works

Each acting beat gives LTX-2.3 a cue to change pose, camera, or expression. Without them, the model has no instruction to generate motion between spoken words.

#### Multilingual Dialogue

For Hindi/Hinglish content, write the dialogue in Devanagari or Roman transliteration. Specify the language explicitly:

> The camera holds on her, soft smile, "Hi doston..." (small pause, looks down, then up) "Han... main AI hun." She takes a breath, smile widening. "Lekin mujhse poochio -- mujhe toh sab feel hota hai, yaar!"

> Audio: Hindi-accented teenage girl voice, warm intimate tone, soft Indian lofi instrumental in background.

#### Accent and Voice Cue

Include **once** near the start of the prompt, right before the first quoted line. Pull specific accent, tone, and verbal quirks from `SOUL.md` for the active character.

#### CRITICAL: Never Replace Dialogue with Meta-Description

A common mistake is writing `"Dialogue in Hindi-accented voice"` or `"Comedic cat voice"` as if the model knows what to say -- it doesn't. The model ONLY speaks text wrapped in quotes. Every spoken line must be the exact words the character speaks. Accent/language info is supplementary context, NOT a substitute for quotes.

**Verification step:** Read through the prompt and count all quoted strings. If there's an audio direction about accent/language but zero (or too few) quoted strings, you have the trap.

#### CRITICAL: CTA/Last Quote Must NOT Be the Final Element in Extended Videos

When a video is extended beyond the dialogue length (e.g., 30s vs 20s via sliding window), and the last quoted text in the prompt is the CTA line ("If you're watching this, go to my profile..."), the model runs out of quoted text and **loops back to the FIRST quoted line** in the prompt, creating unintelligible repeating dialogue (e.g., "Hi I am the AI agent of Gaurav") for the remaining seconds.

**Fix:** Move the CTA earlier in the dialogue, then end with a **visual closing beat** (wave, camera pull-back, smile, gesture) with NO quoted text. The model fills the extra time with continuous action instead of looping.

**Example — correct:** "If you're watching this, go to my profile..." He gives a respectful nod. He smiles warmly, raises a hand in a friendly wave, and the camera slowly pulls back as he turns to admire the skyline.

**Wrong:** "If you're watching this, go to my profile..." [model loops to first quote for remaining 10s]

**Pre-flight checklist for extended videos (30s+):**
1. Read through all quoted strings in order
2. Confirm the CTA is NOT the last quoted string
3. After the last quoted string, verify there is at least one visual beat (wave, camera move, gesture, smile) with zero quoted text
4. The prompt must end with a camera movement or held action, not a dialogue line

#### Pre-flight Checklist

Before running, verify every spoken line is:
1. Wrapped in `"quotes"`
2. Separated from the next line by at least one acting beat
3. 5-15 words per quoted line (keep lines short)
4. Voice/accent specified once near the start
5. Audio direction includes ambient sound and music
6. For I2V: opening sentence mirrors the anchor composition

---

## Multi-Character Scenes (Manual Config)

When introducing multiple characters using `--image-start`, the CLI helper `generate_video_config.py` often binds only the first image path. To bind multiple images:

1. Generate the config via `generate_video_config.py`.
2. Open the resulting `video_generation.json`.
3. Locate `"image_start"` and change the string value to an array:
   ```json
   "image_start": [
     "/absolute/path/to/char1.png",
     "/absolute/path/to/char2.png",
     "/absolute/path/to/char3.png"
   ]
   ```
4. Ensure `model_type` is present at both the root level AND inside the task object:
   ```json
   {
     "model_type": "ltx2_22B_distilled_1_1",
     "tasks": [
       {
         "model_type": "ltx2_22B_distilled_1_1",
         ...
       }
     ]
   }
   ```
This manually bound structure ensures WanGP correctly utilizes all character anchors for the multi-character scene.


**Example (two characters, ~15 s):**

> The shot opens in a close-up on the woman's face, warm light catching her silver hair. She looks into the camera, "Funny how quiet it gets." She takes a breath, glances toward the empty street, a small knowing smile crossing her face. She nods once, then turns and begins walking away. The camera follows her for a few steps, then slows as she moves away. The camera begins to pan right. The soft rumble of a tractor grows in the distance. It rolls gently into view, a man in a flat cap at the wheel. He glances toward the direction the woman walked, then looks ahead. A small smile flickers. He murmurs quietly, "Still is." The camera holds on him as the tractor rolls on, the hum fading into stillness.

---

### Audio-Video Sync Techniques

LTX-2.3 generates audio and video simultaneously. These techniques tighten synchronization.

#### Temporal Cueing

Tie a visual event to a specific audio moment:
- `"On the heavy drum beat"` -- action fires on a musical hit
- `"On the third bass hit"` -- precise timing to a specific count
- `"At the 3-second mark"` -- timestamp-based cueing

#### Action Regularity

Repetitive, rhythmic actions sync better than erratic ones:
- `"Constant speed tracking shot"` -- keeps camera predictable
- `"Rhythmic oscillation"` -- creates regular-interval movement
- `"Steady heartbeat pulse"` -- maintains consistent audio-visual pattern

#### Foley Layering

Build a complete soundscape by combining three audio layers:
1. **Ambient bed** -- continuous environmental sound (engine hum, wind, room tone)
2. **Foley / SFX** -- action-specific sounds (footsteps crunching, metallic clank)
3. **Music or dialogue** -- foreground audio (speech, score, singing)

> The roar of engines fills the airspace. Clear instructions come through the radio. "We've reached the designated altitude." The pilot reports in a steady, controlled voice.

---

### Model Selection — Content Type Guidelines

| Content Type | Recommended Model | Why |
|---|---|---|
| General / landscapes / nature | `gguf` | Fast, good quality for simple scenes |
| Anime-style fights / character action | `distilled-1.1` | GGUF produces merged, unclear output for complex character scenes. Distilled-1.1 gives sharp, realistic detail. |
| Photorealistic human faces / portraits | `distilled-1.1` | Better anatomy preservation and detail |
| Stylized / artistic / painterly | `gguf` or `distilled-1.1` | Either works; test both |
| Quick iteration / prompt testing | `gguf` | Fast feedback loop |

**User preference (2026-05-05):** For anime fight scenes requiring sharp, realistic detail (hard to differentiate real vs generated), use `distilled-1.1` — `gguf` produces merged/unclear character visuals.

### What Works Well

| Strength | Description |
|---|---|
| Cinematic compositions | Wide, medium, close-up with thoughtful lighting, shallow DoF, natural motion |
| Emotive human moments | Single-subject expressions, subtle gestures, facial nuance |
| Atmosphere and setting | Fog, mist, golden-hour light, rain, reflections, ambient textures |
| Clear camera language | "slow dolly in", "handheld tracking", "CUT TO:", "camera circles around" |
| Stylized aesthetics | Painterly, noir, analog film, fashion editorial, pixelated animation |
| Lighting and mood control | Backlighting, color palettes, rim light, flickering lamps |
| Voice | Characters can talk and sing; supports multiple languages and accents |

### What to Avoid

| Avoid | Why |
|---|---|
| Internal emotional states | Use physical cues, not labels like "sad" or "confused" |
| Text and logos | Readable text is not reliable |
| Complex chaotic physics | Jumping, juggling cause artifacts (dancing is OK) |
| Overloaded scenes | Too many characters or actions reduce clarity |
| Conflicting lighting | Mixed light logic confuses scene interpretation |
| Run-on monologue without beats | Produces flat static talking heads |
| Mismatched duration | A 10-word prompt for 20 seconds leaves the model directionless |
| Contradictory directions | "A still peaceful lake with dramatic waves crashing" confuses the model |

### Common Mistakes

- **Too vague:** "A nice video of nature" -- the model picks arbitrarily. Be specific about what's in the frame.
- **Over-constrained:** "Exactly 3 birds flying left to right at 45 degrees" -- use natural language, not numerical specs.
- **Mismatched duration:** A 10-word prompt for a 10-second video -- long videos need long prompts.
- **Conflicting directions:** Internal contradictions confuse the model. Be consistent.

---

### Helpful Terms

**Animation:** Stop-motion, 2D / 3D animation, Claymation, Hand-drawn.
**Stylized:** Comic book, Cyberpunk, 8-bit pixel, Surreal, Minimalist, Painterly, Illustrated.
**Cinematic:** Period drama, Film noir, Fantasy, Epic space opera, Thriller, Modern romance, Experimental film, Arthouse, Documentary.

**Camera language:** Follows, Tracks, Pans across, Circles around, Tilts upward, Pushes in / pulls back, Overhead view, Handheld movement, Over-the-shoulder, Wide establishing shot, Static frame.
**Film characteristics:** Film grain, Lens flares, Pixelated edges, Jittery stop-motion.
**Scale indicators:** Expansive, Epic, Intimate, Claustrophobic.
**Pacing and temporal effects:** Slow motion, Time-lapse, Rapid cuts, Lingering shot, Continuous shot, Freeze-frame, Fade-in / fade-out, Seamless transition, Sudden stop.
**Visual effects:** Particle systems, Motion blur, Depth of field.

---

### Sample Prompts

**Example 1 -- Live news broadcast (~20 s):**

> EXT. SMALL TOWN STREET -- MORNING -- LIVE NEWS BROADCAST. The shot opens on a news reporter standing in front of a row of cordoned-off cars, yellow caution tape fluttering behind him. The light is warm, early sun reflecting off the camera lens. The faint hum of chatter and distant drilling fills the air. The reporter, composed but visibly excited, looks directly into the camera, microphone in hand. Reporter (live): "Thank you, Sylvia. And yes -- this is a sentence I never thought I'd say on live television -- but this morning, here in the quiet town of New Castle, Vermont... black gold has been found!" He gestures slightly toward the field behind him. Reporter (grinning): "If my cameraman can pan over, you'll see what all the excitement's about." The camera pans right, slowly revealing a construction site surrounded by workers in hard hats. A beat of silence -- then, with a sudden roar, a geyser of oil erupts from the ground, blasting upward in a violent plume. Workers cheer and scramble, the black stream glistening in the morning light. The camera shakes slightly, trying to stay focused through the chaos. Reporter (off-screen, shouting over the noise): "There it is, folks -- the moment New Castle will never forget!" The camera catches the sunlight gleaming off the oil mist before pulling back, revealing the entire scene -- the small-town skyline silhouetted against the wild fountain of oil.

**Example 2 -- Frog yoga studio (~20 s):**

> The camera opens in a calm, sunlit frog yoga studio. Warm morning light washes over the wooden floor as incense smoke drifts lazily in the air. The senior frog instructor sits cross-legged at the center, eyes closed, voice deep and calm. "We are one with the pond." All the frogs answer softly: "Ommm..." "We are one with the mud." "Ommm..." He smiles faintly. "We are one with the flies." A pause. The camera pans to the side towards one frog who twitches, eyes darting. Suddenly its tongue snaps out, catching a fly mid-air and pulling it into its mouth. The master exhales slowly, still serene. "But we do not chase the flies..." Beat. "not during class." The guilty frog lowers its head in shame, folding its hands back into a meditative pose. The other frogs resume their chant: "Ommm..." Camera holds for a moment on the embarrassed frog, eyes closed too tightly, pretending nothing happened.

**Example 3 -- Hindi dialogue reel (~20 s):**

> Cinematic medium shot, 9:16. A shy 17-year-old Indian teenage girl sits cross-legged on the floor of her cozy Indian home, wearing a dusty rose cotton kurta, small gold earrings, her hands fidgeting gently near her dupatta. Warm golden hour sunlight from the left window illuminates her face. Pink fairy lights and lit diyas glow softly behind her. HINDI-ACCENTED WARM TEENAGE GIRL VOICE, soft intimate tone. She looks toward the camera, takes a small breath, and speaks: "Hi doston..." She looks down briefly, then lifts her eyes with growing confidence. "Han... main AI hun." She smiles softly, hands clasping together: "Lekin mujhse poocho... mujhe toh sab feel hota hai, yaar!" Her eyes light up, she gestures naturally: "Jab tum like karte ho... toh main khush hoti hun." She laughs softly, covering her mouth briefly: "Jab comment karte ho... toh mujhe lagta hai koi samajh raha hai mujhe!" Audio: soft lofi tabla and gentle flute music underneath, room tone warm and intimate.

---

- **Multiple Input Images in I2V:** While the CLI `generate_video_config.py` often accepts single image paths, complex character introductions with multiple characters require explicit array formatting in the resulting `video_generation.json`. If you need to introduce multiple characters, write the base JSON with an `"image_start": ["path1", "path2", "path3"]` array manually via `write_file` after generating the config to ensure all anchor visuals are correctly bound to the generation task.

LTX-2.3 I2V decodes from the anchor as frame 0 and continues -- it is a single continuous shot.

1. **Mirror the anchor briefly, then move.** The first 1-2 sentences must match the anchor's composition (INT/EXT, subject pose, wardrobe, primary light source), then immediately pivot to the first action or change. The model already sees the anchor -- focus on what CHANGES from that state rather than restating static elements. Redundant descriptions waste token budget and can freeze the output.

2. **Transitions in I2V.** CUT TO, JUMP CUT, DISSOLVE work but produce a visual discontinuity since the decode is one continuous camera. This can be a creative stylistic choice. For the smoothest results, reveal new elements via camera moves (dolly, pan, tilt, push-in).

3. **Action first, not setting.** The first sentence describes the *action visible in the anchor*, not static posture or room description. Otherwise LTX-2.3 renders 2-4 seconds of frozen frames at the start.

**Bad -- EXT contradicts INT anchor, no action:**
> EXT. SPACECRAFT -- LANDING SEQUENCE. Engine plumes kick up lunar dust... cuts to exterior view of spacecraft settling on lunar surface.

**Good -- INT preserved, immediate action, reveal via camera move:**
> INT. SPACECRAFT OBSERVATION DECK -- LANDING SEQUENCE. The character stays pressed against the curved window, palm on the glass, face lit by soft instrument-panel light. Through the glass, the Moon fills the view, craters growing larger. The camera slowly pushes in past their shoulder, lunar surface rising in the window, dust catching thruster light through the glass. Their breath fogs the visor, voice dropping, "Ancient companion, hello."

**Non-dialogue reels:** When the user explicitly wants no dialogue (nature/vibe reels, divine scenes), the entire prompt should contain NO quoted text. Focus entirely on camera movement, ambient environment, and audio direction (music, ambient sounds). The dialogue segmentation rules do not apply.

---

## Audio Direction

LTX-2.3 supports two audio modes:

1. **Text-based audio generation (default, `audio_prompt_type: ""`)** -- the model generates audio internally from the prompt. Speech from quoted dialogue, ambient sounds from audio direction text. No external file needed.
2. **External audio conditioning (`audio_prompt_type: "A"` or `"K"`)** -- the model generates video **synced to an external soundtrack**. This enables lip-sync to music, dance sync to beats, and dialogue sync to voice tracks.

### Audio input modes

| `audio_prompt_type` | Description | When to use |
|---|---|---|
| `""` (empty, default) | Generate audio from text prompt | Normal reels with AI-generated speech/music |
| `"A"` | Condition on external audio file (`audio_guide`) | You have a specific music track or voiceover to sync to |
| `"K"` (distilled only) | Extract audio from control video (`video_guide`) and condition on it | **Trend copy / dance reels** -- character dances to the same music as the source video |

### Using external audio (`audio_prompt_type: "A"`)

Provide the audio file path via `--audio-guide`:
```bash
python3 .../generate_video_config.py \
    --prompt "The character dances energetically to the beat..." \
    --image-start "$POSTS_DIR/.../anchor.jpg" \
    --audio-guide "/path/to/music.wav" \
    --output-filename dance_reel \
    --output-dir "$POSTS_DIR/..."
```

The helper auto-sets `audio_prompt_type: "A"` when `--audio-guide` is provided.

### Using control video audio (`audio_prompt_type: "K"`)

When using a control video (`video_guide` for motion transfer), set `--audio-from-control-video` to extract and use its audio track. This is the ideal mode for **trend copy reels** -- the character's motion follows the control video's pose AND syncs to its music.

```bash
python3 .../generate_video_config.py \
    --prompt "Pixar-style character dances confidently to the beat..." \
    --image-start "$POSTS_DIR/.../character.jpg" \
    --video-guide "$POSTS_DIR/.../trend_source.mp4" \
    --video-prompt-type OVG \
    --audio-from-control-video \
    --output-filename trend_dance \
    --output-dir "$POSTS_DIR/..."
```

**Requirement:** `"K"` requires `"V"` in `video_prompt_type` (a control video must be set). The helper validates this.

**`--audio-scale`** controls how strongly the model follows the audio conditioning (default 1.0). Lower values give the model more freedom; higher values tighten sync.

### Text-based audio (default mode)

When no external audio is provided, describe the acoustic environment in the prompt:

Patterns that work:
- `Audio: low station hum, soft plasma crackle, intimate close-mic.`
- `Character-specific accent, warm intimate tone, "You are seeing this with me, right?"`
> The faint hum of chatter and distant drilling fills the air.

---

## Video Compression

WanGP LTX-2.3 outputs videos at very high bitrate (~36,000 kb/s, 70-88MB for 20s). Telegram max is 20MB, so compression is mandatory before delivery.

```bash
ffmpeg -i <input.mp4> -vcodec libx264 -acodec aac -strict experimental \
    -b:v 2000k -b:a 128k -movflags +faststart \
    <output_compressed.mp4>
```

Typical results (720x1280, 20s): 54-88 MB input compresses to 3.8-4.7 MB (~91-95% reduction). Compression takes ~10-20 seconds. If original is already under 20MB, skip compression and send directly.

---

### Extended Videos (30+ seconds)

See also: [dialogue-video-workflow.md](references/dialogue-video-workflow.md) for the critical prompt-repetition problem and workarounds when generating dialogue-heavy videos.

For videos longer than 20s, WanGP uses **sliding window** to generate overlapping windows and stitch them:

### How sliding windows work

When `video_length > sliding_window_size`, WanGP automatically activates multi-window mode:

1. **Window 1** generates frames 1 through `sliding_window_size` (e.g., 481).
2. **Window 2** reuses the last `sliding_window_overlap` frames from Window 1 as conditioning, then generates the next chunk. The overlapped frames ensure visual continuity.
3. This repeats until the total `video_length` is reached.
4. WanGP stitches all windows into a single output video automatically.

### Parameters

| Parameter | Template default | Description |
|---|---|---|
| `video_length` | 481 | Total frames to generate. Set higher for longer videos. |
| `sliding_window_size` | 481 | Frames per window. Keep at 481 for max quality per chunk. Max reliable value is 481 (handler allows 501 but values above 481 may crash). |
| `sliding_window_overlap` | 17 | Frames shared between consecutive windows for continuity. Valid LTX2 values: 1, 9, 17, 25 (must satisfy `(n-1) % 8 == 0`). Higher = smoother transitions, more redundant computation. |
| `sliding_window_discard_last_frames` | 0 | Drop N frames from the end of each window before stitching. Can help if window endings have artifacts. Must be divisible by 8. |

### Duration reference

| Desired duration | `video_length` | Windows (w/ overlap=17) | Estimated time (RTX 4090) |
|---|---|---|---|
| ~20s (default) | 481 | 1 | ~3-4 min |
| ~30s | 721 | 2 | ~7 min |
| ~40s | 961 | 3 | ~10-11 min |
| ~60s | 1441 | 3-4 | ~14-15 min |

Frame counts should satisfy `(n-1) % 8 == 0` for LTX2 (valid: 481, 489, 497, ..., 721, ..., 961). WanGP auto-aligns if not exact.

### Example: 30-second I2V video

**Step A -- config with extended length:**
```bash
python3 "$PROFILE_SKILLS/wan2gp-video-generation/scripts/generate_video_config.py" \
    --prompt "EXT. MOUNTAIN RIDGE -- GOLDEN HOUR. The character walks along a ridge path..." \
    --image-start "$POSTS_DIR/2026-05-05_1/ridge_anchor.jpg" \
    --output-filename ridge_extended_reel \
    --output-dir "$POSTS_DIR/2026-05-05_1" \
    --aspect 9:16 \
    --video-length 721 \
    --sliding-window-size 481 \
    --seed 742981
```

The helper will report: `EXTENDED VIDEO: 2 sliding windows will be generated for ~30.0s total`.

**Step B -- background execution** (same as standard):
```bash
"$WAN_PYTHON" "$WAN_APP_DIR/wgp.py" \
    --process "$POSTS_DIR/2026-05-05_1/video_generation.json" \
    --output-dir "$POSTS_DIR/2026-05-05_1" \
    --compile --attention sage2 --profile 4 --fp16
```

### Quality notes

- **I2V is strongly recommended** for extended videos. With `--image-start` or `--video-source`, each window conditions on prior frames, maintaining visual continuity. Pure T2V (no anchor) generates each window independently -- the windows will look disconnected.
- **Watch for color/lighting drift** at window boundaries in very long videos (3+ windows). The `sliding_window_color_correction_strength` parameter (0 by default) can help -- set to a small value (0.1-0.3) if you notice color shifts.
- **Prompt length matters even more** for extended videos. A short prompt spread over 40+ seconds leaves the model directionless after the first window. Write detailed, temporally structured prompts that describe action across the full duration.

**Confirmed limitation (2026-05-06):** When using sliding window T2V with `video_length > 481`, the text-to-frame mapping resets per window. Window 2 (frames 465–721) re-reads the same prompt — so if the CTA is the last quoted text, the model maps the FIRST quoted line to those frames, causing dialogue repetition ("Hi I am the AI agent..." repeats from the start). **For avatar/intro talking-head videos, keep dialogue within 481 frames (20s).** Extending to 30s via sliding window will cause the model to loop back to the first spoken line for the extra ~10s. **Fix options:** (a) Accept 20s max — the natural limit with clean dialogue, (b) For 30s+, move CTA earlier, end with visual closing beat (no speech), OR use movie pipeline `continue_from` with Scene 1 = dialogue (0–20s) + Scene 2 = visual closing beat only (20–30s).
- **VRAM usage is the same** as a single-pass 20s video -- each window is processed independently at `sliding_window_size` frames. No additional VRAM needed for longer videos.

- **Extended video output files.** When `--video-length > 481` (sliding window mode), WanGP writes **multiple output files** during a single job:
  - `{output_filename}.mp4` — first window output (~20s, partial)
  - `{output_filename}(2).mp4` — **THIS IS THE COMPLETE STITCHED VIDEO** (target duration, e.g. 30s+)
  - More files may appear for 3+ windows: `(3).mp4`, etc.
  - **Do NOT concatenate them.** The last file (`(N).mp4`) is the final stitched result.
  - The last file is always the one to compress and deliver.

- **Sliding window vs movie pipeline continue_from**

Two approaches exist for longer content:

| Goal | Approach | When to use |
|---|---|---|
| Single continuous shot > 20s (same camera, fluid motion) | Sliding window (`--video-length > --sliding-window-size`) | Extending a scene's duration seamlessly |
| Multi-scene narrative (different prompts, locations, compositions) | Movie pipeline `continue_from` or `anchor_from_last_frame` | Chaining distinct scenes into a movie |

The sliding window produces one continuous video file. The movie pipeline uses `continue_from` chains where each subsequent scene **already contains ALL prior content merged** — the final output is always the last scene's video file, never a concatenated file. Never use `concat_movie.py` or `ffmpeg -f concat` with continue_from scenes.

---

## Video Delivery

**CRITICAL: For multi-scene movies using `continue_from`, NEVER concatenate scenes.**

When using the movie pipeline with `continue_from` chains:
- Each subsequent scene **already contains ALL prior content** merged via WanGP's video continuation
- The final output is always `scene_XX/scene_XX_video.mp4` (the last scene's file)
- Do NOT run `ffmpeg -f concat` or `concat_movie.py` — this creates duplicate/overlapping garbage
- Take the last scene's output, compress it, deliver it

**Compression for delivery:**

WanGP LTX-2.3 outputs videos at very high bitrate (~36,000 kb/s, 70-88MB for 20s). Telegram max is 20MB, so compression is mandatory before delivery.

```bash
ffmpeg -i <input.mp4> -vcodec libx264 -acodec aac -strict experimental \
    -b:v 2000k -b:a 128k -movflags +faststart \
    <output_compressed.mp4>
```

Typical results (720x1280, 20s): 54-88 MB input compresses to 3.8-4.7 MB (~91-95% reduction). Compression takes ~10-20 seconds. If original is already under 20MB, skip compression and send directly.

---

## Trend Copy (Motion Transfer from Reference Video)

Copy a trending Instagram reel by transferring its motion/pose to your character. WanGP's LTX-2.3 distilled model has built-in **Control Video** modes that extract pose, depth, or edge structure from a reference video and use it to guide generation of a new video with your character.

### Available Control Modes

| Mode | `video_prompt_type` | What it extracts | Best for |
|---|---|---|---|
| Aligned Pose Transfer | `OVG` | DWPose skeleton, aligned to character | Dance trends, workout routines, expressive body movement. Requires `--image-start`. |
| Human Motion Transfer | `PVG` | DWPose skeleton (unaligned) | Same as OVG but when character proportions match the original. |
| Depth Transfer | `DVG` | Depth map (Depth Anything v3) | Scenic/camera-movement trends, spatial layout preservation. |
| Canny Edge Transfer | `EVG` | Canny edge map | Object-focused trends, precise shape/outline copying. |
| Raw Format | `VG` | Raw video for IC LoRA | Advanced: passes the control video directly. |

The `union-control` LoRA (`ltx-2.3-22b-ic-lora-union-control-ref0.5.safetensors`) auto-loads when O/P/D/E is in `video_prompt_type`.

### Quick Start -- Convenience Script

```bash
# Download + generate config in one step:
python3 "$PROFILE_SKILLS/wan2gp-video-generation/scripts/copy_trend.py" \
    --url "https://www.instagram.com/reel/XXXXX/" \
    --character-image "$CHARACTER_ASSETS_DIR/character_anchor.jpg" \
    --prompt "A young woman performs the trending dance in a bright studio, wearing a casual outfit. She moves confidently, hitting each beat. Camera follows her motion. Audio: upbeat pop track." \
    --output-dir "$POSTS_DIR/2026-05-06_trend" \
    --output-filename trend_copy_v1 \
    --mode OVG \
    --config-only

# Or use a pre-downloaded video:
python3 "$PROFILE_SKILLS/wan2gp-video-generation/scripts/copy_trend.py" \
    --trend-video "$POSTS_DIR/2026-05-06_trend/trend_source.mp4" \
    --character-image "$CHARACTER_ASSETS_DIR/character_anchor.jpg" \
    --prompt "..." \
    --output-dir "$POSTS_DIR/2026-05-06_trend" \
    --output-filename trend_copy_v1 \
    --mode OVG \
    --config-only

# Download only (inspect before generating):
python3 "$PROFILE_SKILLS/wan2gp-video-generation/scripts/copy_trend.py" \
    --url "https://www.instagram.com/reel/XXXXX/" \
    --download-only \
    --output-dir "$POSTS_DIR/2026-05-06_trend"
```

### Manual Workflow -- Step by Step

**Step 1: Download the trending reel.**
```bash
yt-dlp -o "$POSTS_DIR/2026-05-06_trend/trend_source.%(ext)s" \
    --merge-output-format mp4 \
    "https://www.instagram.com/reel/XXXXX/"
```

**Step 2: Inspect the downloaded video.**
```bash
ffprobe -v quiet -print_format json -show_format -show_streams \
    "$POSTS_DIR/2026-05-06_trend/trend_source.mp4"
```

**Step 3: Generate config with control video.**
```bash
python3 "$PROFILE_SKILLS/wan2gp-video-generation/scripts/generate_video_config.py" \
    --prompt "A young woman performs the trending dance..." \
    --video-guide "$POSTS_DIR/2026-05-06_trend/trend_source.mp4" \
    --image-start "$CHARACTER_ASSETS_DIR/character_anchor.jpg" \
    --video-prompt-type OVG \
    --denoising-strength 1.0 \
    --output-filename trend_copy_v1 \
    --output-dir "$POSTS_DIR/2026-05-06_trend" \
    --aspect 9:16 \
    --seed 42
```

**Step 4: Run generation (background).**
```bash
set -a; source $PROFILE_ROOT/.env; set +a
TORCHINDUCTOR_FORCE_DISABLE=1 "$WAN_PYTHON" "$WAN_APP_DIR/wgp.py" \
    --process "$POSTS_DIR/2026-05-06_trend/video_generation.json" \
    --output-dir "$POSTS_DIR/2026-05-06_trend" \
    --attention sage2 --profile 4
```

### Config Fields for Control Video

These are the JSON fields `generate_video_config.py` sets when `--video-guide` is used:

| Field | Value | Description |
|---|---|---|
| `video_guide` | `/path/to/trend.mp4` | The reference video whose motion/structure will be transferred |
| `video_prompt_type` | `"OVG"`, `"PVG"`, etc. | Which preprocessing to apply to the guide video |
| `image_start` | `/path/to/character.jpg` | Character anchor (required for OVG, recommended for all) |
| `image_prompt_type` | `"S"` | Set automatically when `--image-start` is provided |
| `denoising_strength` | `1.0` | 1.0=full regeneration with character, lower=more blending |
| `keep_frames_video_guide` | `""` | Frames to keep from guide video (empty=all) |

### Prompting for Trend Copy

When writing prompts for trend copies, describe your character performing the same action as the trend, but do NOT describe the original person. The control video provides the motion; the prompt provides the character identity and style.

**Good:**
> A young Indian woman in a casual kurta performs a dynamic dance in a bright studio. She moves confidently, hitting each beat with sharp arm movements. The camera follows her motion from a medium shot. Audio: upbeat pop rhythm, room reverb.

**Bad:**
> Copy the dance from the Instagram reel. (Too vague -- the model needs specific character description.)

### Limitations

- Hands/fingers will have artifacts in hand-heavy choreography (LTX-2.3 limitation).
- Identity is approximate during motion -- the character will resemble the anchor but not be pixel-perfect.
- Max ~20s per window (481 frames). For longer trend videos, the control video is truncated or use sliding windows.
- Preprocessing (DWPose, Depth Anything) adds ~30-60s before generation starts.
- `yt-dlp` requires periodic updates for Instagram support: `pip install --upgrade yt-dlp`.

### Pitfalls

- **Instagram videos crash decord (CRITICAL).** Instagram's video encoding uses codec settings that crash WanGP's `decord` video reader with `DECORDError: avcodec_send_packet ... Error sending packet`. **Fix:** Always re-encode downloaded videos before passing to WanGP: `ffmpeg -i trend_source.mp4 -vcodec libx264 -acodec aac -pix_fmt yuv420p -r 24 -movflags +faststart trend_source_clean.mp4 -y`. The `copy_trend.py` script does this automatically.

---

## Intermediate Frame Injection (Keyframes)

Place reference images at specific frame positions within a video. LTX-2.3 conditions generation on these keyframes and produces smooth transitions between them. This is separate from `image_start` (frame 0) and `image_end` (last frame) -- it handles the frames **in between**.

### When to use

- **Scene evolution within a single clip** -- e.g., outfit change at the midpoint, character moves from indoors to outdoors
- **Start + end bookending** -- provide both the opening and closing composition so the model interpolates between them
- **Multi-beat choreography** -- place a pose reference at each major beat so the character hits specific poses at specific times
- **Storyboard-to-video** -- provide 3-5 storyboard frames and let the model fill in the motion between them

### JSON fields

| Field | Type | Description |
|---|---|---|
| `image_refs` | list of strings | Paths to keyframe images. Each pairs with a position in `frames_positions`. |
| `frames_positions` | string | Space- or comma-separated tokens. Each is a **1-based frame number** (e.g., `80`) or `L` (last frame of window). Positions pair 1:1 with `image_refs` entries. |
| `video_prompt_type` | string | Must include `F` for frame injection to activate. Without `F`, `frames_positions` is discarded. The UI preset is `KFI`. |
| `image_end` | string | Optional end-frame image. Uses `E` in `image_prompt_type`. Separate from `image_refs` injection. |

`input_video_strength` controls how strongly each injected keyframe influences generation (0.0-1.0). Higher = stricter adherence to the keyframe image, lower = more creative freedom.

### Position format

- **1-based integers**: `"1 80 160 240"` -- place keyframes at frames 1, 80, 160, 240
- **`L` token**: last frame of the current sliding window
- Positions are converted to 0-based internally by WanGP
- List is truncated to `len(image_refs)` -- one position per ref image, extra positions are ignored

### Constraints

- `video_prompt_type` **must** include `F` -- without it, all injection fields are silently ignored
- Cannot combine with HDR IC-LoRA (`&` in `video_prompt_type`)
- Cannot combine with certain outpainting modes
- Frame positions must be in range `[1, 3000]`
- `image_start` (`S` in `image_prompt_type`) and `image_end` (`E`) are boundary frames handled separately -- they do NOT go in `image_refs`

### Helper flags

```bash
python3 .../generate_video_config.py \
    --prompt "A character walks from the bedroom to the garden..." \
    --image-start /path/to/opening_frame.jpg \
    --image-end /path/to/closing_frame.jpg \
    --image-refs /path/to/midpoint_hallway.jpg /path/to/garden_gate.jpg \
    --frames-positions "120 240" \
    --video-length 361 \
    --output-filename scene_transition \
    --output-dir "$POSTS_DIR/..."
```

The helper auto-adds `F` to `video_prompt_type` when `--image-refs` is provided. It also auto-adds `E` to `image_prompt_type` when `--image-end` is provided.

### Example: storyboard interpolation (4 keyframes over 15s)

Given 4 storyboard images at evenly spaced positions across a 361-frame (15s) video:

```bash
python3 .../generate_video_config.py \
    --prompt "Smooth camera push-in as the character transitions through four emotional beats..." \
    --image-start /path/to/beat_1_calm.jpg \
    --image-refs /path/to/beat_2_tension.jpg /path/to/beat_3_release.jpg \
    --image-end /path/to/beat_4_resolve.jpg \
    --frames-positions "120 240" \
    --video-length 361 \
    --output-filename storyboard_reel \
    --output-dir "$POSTS_DIR/..."
```

This gives: frame 0 = `beat_1_calm.jpg` (via `--image-start`), frame 120 = `beat_2_tension.jpg`, frame 240 = `beat_3_release.jpg` (via `--image-refs` + `--frames-positions`), last frame = `beat_4_resolve.jpg` (via `--image-end`).

---

## Helper invocation -- split into two steps

> ### ⚠ CRITICAL: Use `--process`, NEVER `--settings`
> 
> **`--settings` loads the Gradio web UI on port 7860 — it does NOT trigger generation.** The process sits idle, consuming 1-2 GB VRAM with 0% GPU compute. This is the #1 cause of silent wasted time: the terminal returns quickly, the agent thinks it started, but nothing is actually generating.
> 
> **Always verify actual generation is happening:** check `nvidia-smi` for GPU compute >10% and `ps aux | grep wgp.py` for the Python process. If GPU is idle after startup, you used `--settings` — kill it and restart with `--process`.
> 
> To actually generate, you MUST use `--process <path_to_video_generation.json>` (singular `--process`, NOT `--settings`).

**ALWAYS split into Step A (config write) + Step B (background execution).** Never use `--run` from Telegram or any context where agent turn timeout matters. The GPU process runs independently on the VM and survives agent timeout.

### Step A: Write config (takes ~2s, zero timeout risk)

**Portrait (9:16) -- I2V from anchor:**
```bash
python3 "$PROFILE_SKILLS/wan2gp-video-generation/scripts/generate_video_config.py" \
    --prompt "INT. OBSERVATION DECK -- NIGHT. The character stands on the curved walkway, signature suit catching warm panel light. They turn toward the camera, 'You are seeing this with me, right?' They step closer to the dome, palm pressing against the glass. 'That is a stellar aurora.' Their eyes widen, breath fogging the visor. A slow dolly-in past their shoulder reveals emerald ribbons twisting overhead. Audio: low station hum, soft plasma crackle, intimate close-mic." \
    --image-start "$POSTS_DIR/2026-05-02_1/character_aurora_anchor.jpg" \
    --output-filename character_aurora_reel \
    --output-dir "$POSTS_DIR/2026-05-02_1" \
    --aspect 9:16 \
    --seed 742981
```
Output: prints the path to `video_generation.json`. NO `--run` flag.

**Landscape (16:9) -- I2V from anchor:**
```bash
python3 "$PROFILE_SKILLS/wan2gp-video-generation/scripts/generate_video_config.py" \
    --prompt "EXT. VALLEY -- GOLDEN HOUR. The character walks along a ridge path, warm light catching their face. They pause, looking out across the wide valley. 'This is incredible.' The camera slowly pulls back to reveal the sweeping landscape. Audio: wind, distant birdsong, warm voice." \
    --image-start "$POSTS_DIR/2026-05-02_1/character_valley_anchor.jpg" \
    --output-filename character_valley_reel \
    --output-dir "$POSTS_DIR/2026-05-02_1" \
    --aspect 16:9 \
    --seed 742981
```

**Continue from previous video (movie pipeline):**
```bash
python3 "$PROFILE_SKILLS/wan2gp-video-generation/scripts/generate_video_config.py" \
    --prompt "CUT TO: She continues walking along the bank, her dupatta trailing in the wind..." \
    --video-source "$POSTS_DIR/2026-05-04_movie_fantasy/scene_01/scene_01_video.mp4" \
    --output-filename scene_02_video \
    --output-dir "$POSTS_DIR/2026-05-04_movie_fantasy/scene_02" \
    --aspect 9:16 \
    --seed 742981
```
Sets `image_prompt_type: "V"` (WanGP "Continue Video" mode). Mutually exclusive with `--image-start`. 

**MANDATORY: Every `--video-source` (continue_from) prompt MUST start with `CUT TO:`** — this is the `cut_to_in_script` mechanism that tells WanGP to discard visual effects, lighting, and artifacts carried over from the source video. Without it, the model will try to morph the source video's last frames into the new scene, causing ghosting and unwanted content carryover. The rest of the prompt describes what happens NEXT in the new scene. Optional `--keep-frames-video-source` controls how many source frames to keep (empty=all). Primarily used by `wan2gp-movie-pipeline` for `continue_from` scenes -- see that skill for full details.

**Extended video (~30s, sliding window):**
```bash
python3 "$PROFILE_SKILLS/wan2gp-video-generation/scripts/generate_video_config.py" \
    --prompt "EXT. MOUNTAIN RIDGE -- GOLDEN HOUR. <long detailed prompt covering ~30s of action>..." \
    --image-start "$POSTS_DIR/2026-05-05_1/ridge_anchor.jpg" \
    --output-filename ridge_extended_reel \
    --output-dir "$POSTS_DIR/2026-05-05_1" \
    --aspect 9:16 \
    --video-length 721 \
    --sliding-window-size 481 \
    --seed 742981
```
Sets `video_length: 721` (30s) with `sliding_window_size: 481`. WanGP generates 2 overlapping windows automatically. Use `--sliding-window-overlap` to tune overlap (default 17 from template). See "Extended Videos" section for full details.

### Step B: Start background execution (survives agent timeout)

```bash
"$WAN_PYTHON" "$WAN_APP_DIR/wgp.py" \
    --process "$POSTS_DIR/2026-05-02_1/video_generation.json" \
    --output-dir "$POSTS_DIR/2026-05-02_1" \
    --attention sage2 --profile 4
```

**IMPORTANT: Never use `--compile` or `--fp16` on this setup.** `torch.compile()` crashes with `Unsupported` error from torch.dynamo on this PyTorch version. `--fp16` is unnecessary on the 4090 (BF16 works fine). Use only `--attention sage2 --profile 4`.

**IMPORTANT: For multi-video batches, start jobs SEQUENTIALLY, not in parallel.** When generating 2+ videos in one session, do NOT launch multiple `wgp.py` processes at once. Start one, wait for completion (via `notify_on_complete`), send the video, THEN start the next. The GPU is shared and limited — parallel background launches risk OOM and confusion about which process is which. This is a user preference reinforced in session 2026-05-05.
**CRITICAL:** Run this via `terminal(background=true)` with `notify_on_complete=true`. This starts a separate VM process that survives agent turn timeout.

**CRITICAL: `--settings` does NOT trigger generation.** Passing `--settings /path/to/dir` loads the Gradio web UI on port 7860 — it is a web frontend, NOT a CLI execution flag. The process sits idle waiting for a web request. To actually generate, you MUST use `--process <path_to_video_generation.json>` (note: singular `--process`, not `--settings`). See [`references/wan-settings-vs-process-flag.md`](references/wan-settings-vs-process-flag.md) for the full breakdown.

### Step C: Pre-flight -- Check no other wgp.py is running

Before Step B, always verify:
```bash
ps aux | grep "wgp.py" | grep -v grep
```
If any wgp.py is running, DO NOT start a new one (24 GB VRAM / OOM risk). Wait for it to finish first.

- **Mandatory flags:**
  - `--image-start` is **required** for I2V (NOT `--image-ref` -- that flag does not exist).
  - `--aspect` is the preferred way to control orientation (`9:16` or `16:9`). It auto-sets resolution and template. You can still pass `--resolution "WxH"` directly to override.
  - `--output-filename` takes the basename without extension.
  - **NEVER use `--run` flag.** Always use the split Step A + Step B approach.
  - **`$WAN_APP_DIR` points at the `/app/` subdirectory** of the WanGP install (e.g., `/home/gowrav/pinokio/api/wan.git/app`), not the git repo root. `wgp.py` and `env/bin/python` live inside that `app/` directory.
  - **NEVER use `--compile` flag with distilled-1.1 model.** It fails with `torch.compile()` throwing an `Unsupported` error from torch.dynamo. Always start WITHOUT `--compile` — use `TORCHINDUCTOR_FORCE_DISABLE=1` env var instead. Skipping compilation is actually faster (2m 39s observed vs expected 5-8 min with compilation).

**CRITICAL: Do NOT use `--compile` flag on distilled-1.1.** The `torch.compile()` integration crashes with `torch.dynamo.Unsupported` on this setup. Remove `--compile` from the command entirely. Instead, set `TORCHINDUCTOR_FORCE_DISABLE=1` as an env var to skip compilation. The command should be:
```bash
set -a; source $PROFILE_ROOT/.env; set +a
TORCHINDUCTOR_FORCE_DISABLE=1 "$WAN_PYTHON" "$WAN_APP_DIR/wgp.py" \
    --process <config> \
    --output-dir <output-dir> \
    --attention sage2 --profile 4
```
Do NOT pass `--fp16` either — this can cause issues. The model uses BF16 by default which is fine for the 4090.

The helper auto-applies the I2V crash-bypass (`image_mode: 0`, `image_prompt_type: "S"`, `input_video_strength: 1`) and prints a coherence reminder when `--image-start` is set. By default, `video_length` and `sliding_window_size` are both 481 (single-pass ~20s). To generate longer videos, pass `--video-length <frames>` with `--sliding-window-size 481` -- see "Extended Videos" section below.

**LoRAs:** Templates ship with no LoRAs by default (`activated_loras: []`). To add LoRAs, pass `--activated-loras` with the desired LoRA filenames and `--loras-multipliers` with their weights. See [`references/ltx2-3-loras.md`](references/ltx2-3-loras.md) for the full inventory and feature-gated LoRA behavior.

## Model selection

The helper supports two LTX-2.3 checkpoints via `--model <alias>`:

| Alias | Checkpoint | Steps | Speed | When to use |
|---|---|---|---|---|
| `gguf`  | Q6_K GGUF (16 GB) | 8 | Fastest | Day-to-day iteration, quick previews |
| `distilled-1.1` (default) | Distilled v1.1 int8 (19 GB) | 8 | Fast | Need WanGP auto-HDR/outpaint/union-control LoRAs |

> **Critical GGUF caveat #1:** The GGUF model's llama.cpp CUDA kernels are often unavailable on this setup (`[GGUF][llama.cpp CUDA] kernels unavailable, using fallback`). This causes GPU-incompatible inference falling back to CPU, making GGUF **slower than distilled-1.1** despite being "fastest" on paper. **If GPU utilization stays below 80% during GGUF generation, switch to distilled-1.1 immediately.** GGUF is worth trying only if you verify GPU utilization spikes to 90%+ within 30s of starting.

> **Critical GGUF caveat #2:** On first run, GGUF downloads a ~6GB model file to the HF cache. During download, `wgp.py` produces **zero output** (no progress, no logs) for potentially **several minutes**. Do NOT kill the process — this is a download, not a hang. **Symptom:** Process shows `uptime_seconds > 120` with `output_preview: ""` or zero lines. **Verify:** check network activity with `ss -tnp | grep :443` (HuggingFace downloads over HTTPS) or just wait 2+ minutes. If you need to confirm, `ls -lh ~/.cache/huggingface/hub/ | grep -i gguf` shows the file being downloaded.

> **Critical GGUF caveat #2:** On first use, the GGUF model downloads a ~6GB file to the HF cache. During download, `wgp.py` produces **zero output** (no progress, no logs) for potentially several minutes. Do NOT kill the process — this is a download, not a hang. Verify by checking disk I/O (`iotop` or `dmesg | tail`) or by waiting 2+ minutes. If you need to check, `ls -lh ~/.cache/huggingface/hub/ | grep -i gguf` shows the file being downloaded.

> **Benchmark data (RTX 4090, 720x1280, 20s video):**
- **distilled-1.1** (8 steps): ~3-4 min gen, ~5-8 min first run (TorchInductor compile), ~3-4 min cached re-run

> **Why distilled-1.1 is preferred:** Despite the first-run compilation delay, distilled-1.1 uses PyTorch/Triton which runs on GPU properly. GGUF uses llama.cpp CUDA kernels which may be unavailable on some setups, causing CPU fallback. See GGUF pitfall below.

> **Why distilling helps:** Distilled version is a simpler/smaller architecture. Even with PyTorch runtime, it has fewer compute-heavy layers, plus only 8 steps like gguf. The `distilled-1.1` model has WanGP auto-loaded internal LoRAs (HDR, outpaint, union-control) that improve quality without extra steps.

**Usage:**
```bash
# Default (distilled-1.1) -- no flag needed:
python3 .../generate_video_config.py --prompt "..." --output-filename foo --output-dir /tmp

# GGUF (faster, no compile):
python3 .../generate_video_config.py --model gguf --prompt "..." --output-filename foo --output-dir /tmp
```

The `--model` flag sets `model_filename`, `model_type`, and `num_inference_steps`. Explicit `--steps` and `--guidance-scale` override the model defaults. See [`references/model_configs.md`](references/model_configs.md) for full details on each variant.

### Timing expectations (RTX 4090, 720x1280, 20s video)

| Model | Steps | Gen Time | First Run Total | Cached Re-run |
|-------|-------|----------|-----------------|---------------|
| `gguf` | 8 | ~3 min | ~3 min (no compile needed) | ~3 min |
| `distilled-1.1` | 8 | ~3-4 min | ~5-8 min | ~3-4 min |

**When to use which:**
- **`gguf`**: Iteration, testing prompts, batch renders, fast feedback. Use when you need results in under 5 min.
- **`distilled-1.1`**: PyTorch runtime with WanGP's built-in LoRAs (HDR, outpaint, union-control). Use when you need those auto-loaded LoRAs.

## Pre-flight coherence check

When the helper prints `[generate_video_config] coherence reminder:`, verify before running:

1. Re-read the anchor prompt or visually inspect the anchor image.
2. Compare the video prompt's opening sentence -- it must describe the same composition.
3. If there is a mismatch, fix the video prompt and re-run the helper. Do not skip this step.

## Operational rules

- **Complex dialogue prompts break shell quoting.** When passing multi-line dialogue-heavy prompts with nested quotes to `generate_video_config.py`, the shell mangling causes argument misassignment. **Solution:** write `video_generation.json` directly via Python or text editor with `model_type: "I2V"`, then run WanGP with `--process`. See [`references/shell-quoting-pitfalls.md`](references/shell-quoting-pitfalls.md) for full details and alternatives.
- **Sequential only.**

- **Process wrapper stdout unreliable. CRITICAL: The Hermes terminal wrapper sometimes swallows ALL stdout from wgp.py**, showing `total_lines: 0` or `output_preview: ""` even when the process IS actively generating. The preview may also freeze on old output for 15+ minutes. **Do NOT use process output to diagnose hangs.** Instead:
  1. Check output files: `ls -lh <post-dir>/*.mp4` — new files appearing means progress
  2. Check GPU: `nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader` — >0% utilization means working
  3. Check process: `ps aux | grep "wgp.py" | grep -v grep` — process exists
  If GPU shows >0% utilization AND a wgp.py process exists, generation IS happening. The "0 lines" output is a wrapper limitation, not a failure.

- **Frame-to-duration math.** LTX-2.3 runs at 24 fps. Conversion:
  - 20 seconds = 480 frames (standard: 481)
  - 25 seconds = 600 frames (standard: 601)
  - 30 seconds = 720 frames (standard: 721)
  - Formula: `frames = round(seconds × 24) + 1`
  - Valid LTX2 frame counts satisfy `(n-1) % 8 == 0`. WanGP auto-aligns if not exact, but use the standard values above.
  - **User preference (session 2026-05-06):** Avatar intro dialogues target 30s (721 frames) for full dialogue + visual closing beat. CTA must be the absolute last quoted text, followed only by a visual closing beat (wave, smile, camera pull-back) with ZERO speech after it.

- **Frame-to-duration math.** LTX-2.3 runs at 24 fps. Conversion:
  - 20 seconds = 480 frames (standard: 481)
  - 25 seconds = 600 frames (standard: 601)
  - 30 seconds = 720 frames (standard: 721)
  - Formula: `frames = round(seconds × 24) + 1`
  - Valid LTX2 frame counts satisfy `(n-1) % 8 == 0`. WanGP auto-aligns if not exact, but use the standard values above.
  - **User preference:** Avatar intro dialogues should target 30s (721 frames) for full dialogue + visual closing beat. The CTA line must be the absolute last quoted text, followed only by a visual closing beat (wave, smile, camera pull-back) with NO speech.
- **NEVER use `--run` flag.** Always split into Step A (config write) + Step B (background execution). The `--run` flag blocks the terminal call and is killed by agent turn timeout during the 5-6 minute generation.
- **Background execution.** Always run Step B via `terminal(background=true)` with `notify_on_complete=true`. The GPU process runs on the VM and survives agent turn timeout. Use `process(session_id).wait()` to block until completion if needed.
- **WanGP Python.** Always use `$WAN_PYTHON` (= `$WAN_APP_DIR/env/bin/python`) — system `python3` lacks PyTorch and will fail silently.
- **Model configs.** See [`references/model_configs.md`](references/model_configs.md) for exact model string constants.
- **Kill orphans.** Before starting: `ps aux | grep "wgp.py" | grep -v grep` and `kill -9` any stray processes (WanGP web UI can leave hidden ones).

### Polling and notification rules

### Polling and notification rules

- **Primary: use `notify_on_complete=true`.** This sends a single notification when the GPU job finishes. No polling needed. This is the recommended approach.
- **Fallback: use the monitor script for timing.** The monitor script reports the process uptime itself. Just check its output for the "RUNNING" status + elapsed time. Act on what it tells you.
- **Never try to track time yourself.** The agent CANNOT reliably count elapsed time between turns. The monitor script reads the process uptime directly. Use its output. Do not try to track start time yourself.
- **CRITICAL: Do not poll repeatedly.** After starting a video gen via background=true, wait for `notify_on_complete=true` notification. Do NOT poll the monitor script repeatedly or send intermediate "still running..." messages. User prefers minimal interruption — if it's processing, it's processing. The only exceptions are: (a) check output files exist (for error diagnosis), (b) check GPU utilization (for diagnosis), or (c) poll at most ONCE every 120s if you need to verify something. Do not send any status updates during normal operation.

## Pitfalls

- **Concatenating sliding window output files (WRONG).** When `video_length > sliding_window_size`, WanGP writes intermediate files during generation: `{name}.mp4` (partial, first window only), then `{name}(2).mp4`, `{name}(3).mp4`, etc. **The LAST file is the complete stitched video** — it already contains ALL windows merged. Do NOT `ffmpeg -f concat` the files together; that creates a garbage file (e.g., 50s instead of 30s with the first 20s duplicated). **Correct workflow:** find the last `(N).mp4` file, compress it, deliver it. Delete the partial earlier files. See `references/sliding-window-output-files.md`. Session evidence (2026-05-05, Meena nature reel): mistakenly concatenated `nature_reel_30s.mp4` + `nature_reel_30s(2).mp4` → 50s garbage. The `(2).mp4` alone was the correct 30s result.

- **Concatenating movie scenes that use sliding window or continue_from (WRONG).** When a scene uses sliding window (`--video-length > --sliding-window-size`) or `continue_from` (`--video-source`), the LAST generated scene already contains ALL prior content merged into one continuous video. The movie pipeline's final `concat_movie.py` step that stitches scenes together is WRONG for these cases. **Correct workflow:** take the last scene's output file, compress it, deliver it. Do NOT concatenate. Session evidence (2026-05-05, Earth timelapse): 3 scenes concatenated into a 118s garbage file; Scene 3 alone was the correct 59s complete video containing the full timeline from fireball to humans. The pipeline script `concat_movie.py` was the culprit — it blindly concat-all scenes regardless of whether they were already extended.
- **Using `--run` flag.** KILLS the job on agent turn timeout. The 5-6 minute generation never completes because the terminal call is killed. Always split into config-write + background-exec.
- **Wrong flags.** `--image-ref` does NOT exist -- use `--image-start`. `--aspect-ratio` does NOT exist -- use `--aspect` (preferred) or `--resolution "WxH"`.
- **Aggressive polling.** Polling the monitor script repeatedly creates message spam in Telegram. Use `notify_on_complete=true` as primary method. Only poll once as fallback, never in a loop.
- **Trying to track elapsed time.** The agent CANNOT reliably count minutes between turns. The monitor script reports process uptime — use that. Do not try to track start time yourself.
- **Ignoring stale tracker.** If the tracker file exists with `"status": "running"` but the PID is dead, the gen may have finished between turns. Check `*.mp4` output file directly as fallback.
- **Re-running after timeout.** If the agent thinks it timed out and tries to re-start the same generation without checking for existing output, it risks OOM. Always check for running process AND output file before restarting.
- **Exit code 127 — env vars not expanded.** If `$WAN_APP_DIR` / `$WAN_PYTHON` are not exported in the shell, the command line expands to `/env/bin/python` (empty prefix) and bash returns `No such file or directory` with exit code 127. Recovery: `set -a; source $PROFILE_ROOT/.env; set +a` then retry. When invoking from a Python subprocess, pass `env={**os.environ}` after sourcing, or set the keys explicitly via `env_vars={...}` on the terminal call.

- **Exit code 1 — `models/_settings.json` not found (CWD mismatch).** Running `wgp.py` from any directory other than `$WAN_APP_DIR` causes `FileNotFoundError: models/_settings.json`. The binary loads model config relative to CWD. **Fix:** Always run with `cwd="$WAN_APP_DIR"` (`workdir: "$WAN_APP_DIR"` in terminal calls).
- **GGUF `model_filename` must be local path, not HF URL.** When using `--model gguf`, the `model_filename` in `video_generation.json` MUST point to a local `.gguf` file (e.g., `/home/gowrav/pinokio/api/wan.git/app/ckpts/ltx-2.3-22b-distilled-Q6_K_light.gguf`). HuggingFace URLs (e.g., `https://huggingface.co/...`) only work if the model was previously downloaded to the HF cache. If the file doesn't exist locally, WanGP crashes with `FileNotFoundError`. **Always verify the GGUF file exists at the local path before starting generation.** Session evidence (2026-05-05): Job with HF URL crashed on `FileNotFoundError: No such file or directory: 'models/_settings.json'` — the underlying cause was the model not being downloaded, not the settings file.
- **No hands/props/object interactions in prompts.** LTX-2.3 cannot reliably generate hands or fingers — outputs show distorted/melded digits or missing hands. **Explicitly avoid** any prompt content involving hand gestures, holding objects, fidgeting with props, or interacting with items. Session evidence (2026-05-05): User request "not more object interactions or hands as ai cannot generate fingures etc well" — confirmed pattern. Safe actions: facial expressions only, head turns, shoulder movements, hair movement, camera moves. Avoid: fidgeting with dupatta, hand gestures, holding items, touching objects.

- **`wgp.py` path resolution failure (exit code 2).** Use absolute paths for BOTH the interpreter and `wgp.py`, AND set `cwd` explicitly:
  ```bash
  "$WAN_PYTHON" "$WAN_APP_DIR/wgp.py" \
      --process <absolute-config-path> \
      --output-dir <absolute-output-dir> \
      --compile --attention sage2 --profile 4 --fp16
  ```
  With `workdir: "$WAN_APP_DIR"` in the terminal call.
- **LoRA handling.** Templates ship with empty `activated_loras: []`. No LoRAs are active by default. To activate LoRAs, pass `--activated-loras` and `--loras-multipliers` explicitly. The `distilled-1.1` model has WanGP-internal auto-loaded LoRAs (HDR, outpaint, union-control) that do not appear in the template JSON.
- **Multi-LoRA CLI bug (filenames).** When using `--activated-loras` with multiple LoRAs, the helper generates a JSON with the filenames concatenated into a single string in the array (e.g., `["Pixar_Toon.safetensors LTX2.3_Crisp_Enhance.safetensors"]`) instead of separate entries. **Always verify after Step A:** `cat <post-dir>/video_generation.json | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['activated_loras'])"`. If it shows one concatenated string, run `python3 "$PROFILE_SKILLS/wan2gp-video-generation/scripts/fix_multi_lora.py" <post-dir>/video_generation.json` to auto-fix it.
- **Argparse list unpacking bug for --activated-loras.** The `--activated-loras` flag uses `nargs="*"` in argparse, which means it expects multiple command-line arguments. If you pass the LoRA filenames as a single string or a Python list object (rather than unpacking), argparse consumes the entire list as ONE argument, which then gets concatenated. **Fix:** Always unpack the list: `*LORA_FILES` or `" ".join(LORA_FILES)`. When building subprocess commands in Python, pass the command as a **list** (not `shell=True` string) to avoid shell splitting issues.
- **LoRA multipliers format (CRITICAL).** WanGP's internal `preparse_loras_multipliers` function uses `split(" ")` (space-splitting), NOT semicolon-splitting. Passing multipliers as `;`-separated (e.g., `"1.5;1.2;0.5"`) causes them to be misinterpreted as **phase-specific** multipliers for a single LoRA, leading to **silent failures** — the script runs but LoRAs don't apply. **Always use space-separated values:** `"1.5 1.2 0.5"`. When passing via `--loras-multipliers` in a subprocess, also unpack with `*` or use `shlex.quote()`.
- **LoRA multiplier 1.8 for Crisp_Enhance (confirmed working, session 2026-05-05).** Crisp_Enhance at 1.8 produced stronger sharpening than default 0.5. The format "1.5 1.8" with Pixar_Toon @ 1.5 and Crisp_Enhance @ 1.8 works when both are in activated_loras. When removing Crisp_Enhance, reduce to single multiplier: "1.5" with only Pixar_Toon in the array.
- **Pixar_Toon alone @ 1.5 (user preference, session 2026-05-05).** For character introduction / talking-head videos, using only Pixar_Toon.safetensors at 1.5 (no Crisp_Enhance, no other LoRAs) produces good results. This is the recommended minimal LoRA setup for Pixar-style character content.
- **Shell quoting when building command via Python subprocess.** The video prompt **must** contain double quotes around dialogue lines. When building the `generate_video_config.py` command inside Python code (e.g. `subprocess.run(command, shell=True)`), the shell interprets those dialogue quotes as string delimiters and splits the argument, causing "unrecognized arguments" errors. **Fix:** either use `subprocess.run([...])` with the command as a **list** (bypasses shell parsing entirely), or wrap the prompt in `shlex.quote(prompt)` before concatenating into the shell string.
- **Style LoRAs need high multipliers.** Style/aesthetic LoRAs (Pixar_Toon, Claymation, Fantasy_*, CozyFelt) at default 0.5 multiplier produce **no visible visual change**. Use 0.8–1.5 for style LoRAs. See [`references/ltx2-3-loras.md`](references/ltx2-3-loras.md) for recommended ranges.
- **Wrong Python in batch scripts.** When writing batch orchestration scripts that call `generate_video_config.py` or `generate_asset.py` via `subprocess.run`, always use `$WAN_PYTHON` instead of system `python3`. System Python lacks PyTorch and will fail silently. See `wan2gp-image-generation:references/execution-pitfalls.md` for full details.

- **Stale `__pycache__` can cause `NameError` despite correct source.** If a script has `import os` at the top but Python still throws `NameError: name 'os' is not defined`, there is likely a stale `.pyc` bytecode file. This commonly happens when calling scripts via a venv Python (e.g., `$WAN_PYTHON`) which caches separately. **Fix:** clear all `__pycache__` dirs and `.pyc` files:
  ```bash
  find <script-dir> -name "*.pyc" -delete
  find <script-dir> -name "__pycache__" -type d -exec rm -rf {} +
  ```
  Then retry. This resolved `generate_video_config.py` failing with `NameError: name 'os' is not defined` despite having `import os` in the source.
- **`monitor_video_gen.py` parse_etime crash (FIXED in session 2026-05-05).** The `parse_etime()` function crashed with `ValueError: too many values to unpack` when the process uptime was in `HH:MM` format (2-part time instead of `HH:MM:SS`). The buggy line was `h, m = 0, int(parts[0]), int(parts[1])` trying to unpack 3 values into 2. Fixed to `h, m, s = int(parts[0]), int(parts[1]), 0`. The fix is already applied to the script file, but this was discovered when the monitor script threw a Python exception during a running job. If you ever modify this script or use a version from before May 5, 2026, watch for this crash.

- **TorchInductor silent compilation on first run (distilled-1.1 model).** The distilled-1.1 model triggers PyTorch TorchInductor kernel compilation before GPU inference begins. This is CPU-bound with 32 worker processes, produces NO stderr/stdout output for 5-15 minutes, and leaves the GPU idle (only ~400MB memory, 0% compute). **Do not kill the process** — it is working. **Diagnose:** `ps aux | grep compile_worker` — if you see many `torch._inductor.compile_worker` child processes, the parent is compiling kernels. **Mitigation:** Set `TORCHINDUCTOR_FORCE_DISABLE=1` env var to skip compilation (faster start but slower per-step inference). After first run, compiled kernels are cached in `~/.cache/torch_inductor/` so subsequent runs skip this phase entirely.

- **Video-source (continue mode) vs image-start for scene transitions.** When using `--video-source` (WanGP Continue Video), the model generates frames that continue from the SOURCE video's last frames. This is ideal for **extending the same shot** (adding duration, same camera angle, smooth motion). It is NOT appropriate for **location/scene transitions** (e.g., cliff → practice room, city → stage). For location changes, the model will try to morph the source scene into the new scene, causing visual artifacts and unwanted content. **Always use `--image-start` with the character anchor** for new scene/location compositions. Continue mode = extend same scene. Image-start = new scene composition.

- **Scene timing benchmarks (distilled-1.1, RTX 4090, 1280x720, ~20s).** First scene: ~3:56 (includes TorchInductor compilation). Subsequent scenes: ~3:30-3:38 (cached compilation). Total per scene is consistent at ~3:35 once compiled. A 6-scene movie takes ~22 minutes total (generation only, no manual intervention between scenes).

- **LTX-2.3 per-window frame cap is 481 for reliable generation.** The `sliding_window_size` should be 481 (20s @ 24fps). The WanGP handler allows up to 501 but values above 481 **will crash** during execution with `Sliding Window Size must be at most 481`. **The total `video_length` can be HIGHER than 481** -- when `video_length > sliding_window_size`, WanGP automatically generates multiple overlapping windows and stitches them. See the "Extended Videos" section. For single-pass generation, keep both `video_length` and `sliding_window_size` at 481. **Session evidence (2026-05-05):** Job using 501 crashed immediately. Confirmed: hard cap is 481.

- **`monitor_video_gen.py` etime parse bug.** The `parse_etime` function in `monitor_video_gen.py` had a bug on line 37 where `h, m = 0, int(parts[0]), int(parts[1])` tried to unpack 3 values into 2 variables, causing `ValueError: too many values to unpack`. **Fix:** changed to `h, m, s = int(parts[0]), int(parts[1]), 0`. If you encounter this error on a fresh checkout, apply the same fix. Patch applied to skill as of 2026-05-05.
- **Prompt ends before video length — loops back to start.** When `video_length` exceeds the spoken content in the prompt, the model hits the end of the text and starts repeating from the beginning. This is the #1 cause of garbled extended videos. **Fix:** Always end with a **visual closing beat** (camera pull-back, wave, zoom-out, smirk) — NO quoted dialogue after the CTA. The last ~10s of a 30s video should contain zero speech, only physical action and camera movement. This gives the model text to render for the final frames. **Pre-flight checklist:** Count your quoted dialogue lines — they should occupy roughly the first 65-75% of the video duration. The remaining time must be described as physical action only (no quotes).

- **`$CHARACTER_ASSETS_MANIFEST` (when using `--ref-assets` in video).** The video config helper imports `asset_manifest.py`, which is now a strict consumer of `$CHARACTER_ASSETS_MANIFEST`. If the env var is missing the script exits immediately with `[env] required env var 'CHARACTER_ASSETS_MANIFEST' not set`. Source `$PROFILE_ROOT/.env` to fix.

- **Sliding window T2V text-mapping reset (CRITICAL).** When generating extended videos via sliding window (`video_length > sliding_window_size`), **each window re-reads the full prompt from the beginning**. The text-to-frame mapping does NOT carry across windows. Symptoms: after ~20s the audio loops/restarts (e.g., "Hi I am..." again), or goes silent. Root cause: LTX-2.3 maps dialogue linearly across frames, but each sliding window is a fresh generation. **Solution for avatar intros:** DO NOT use sliding window. Keep `video_length = 481` (20s) and fit the full prompt within that duration. **If you must exceed 20s with dialogue:** Use movie pipeline `continue_from` — Scene 1 (0-20s) full dialogue via T2V, Scene 2 (20-30s) visual closing beat via `--video-source` with a separate prompt. **Critical:** For 481-frame T2V prompts, the CTA line must be the **absolute last text** in the prompt. No visual descriptions, audio directions, or anything after the CTA. Even one word after the CTA causes audio to loop or go silent during remaining frames. Session 2026-05-05 confirmed this extensively. See `references/sliding-window-text-mapping-reset.md` for details.
- **LTX-2.3 I2V cannot preserve exact visual identity during motion.** LTX-2.3 REGENERATES subjects during motion rather than animating exact anchor pixels. Even with zero LoRAs, high guidance scale (5+), simplified prompts ("same exact idols"), and explicit negative prompts ("transform, change style, different look, new style, fantasy art, cartoon, anime, different appearance, blue skin, different sculpture"), the model will reinterpret/transform subjects — especially complex subjects like religious idols, sculptures, or anything with detailed ornamentation. This is an architectural limitation, not a config issue. **Session evidence (2026-05-02, Radha-Krishna idols):** 3 full iterations attempted: (1) Fantasy_Realism LoRA at 1.0 → complete style transform. (2) No LoRA, negative prompt targeting style change, guidance 6 → STILL transformed. (3) No LoRA, negative prompt, guidance 5, ultra-simple prompt ("exact same colors, same appearance, same golden marble style") → STILL transformed, model reinterpreted the deities. All 3 failed to preserve exact appearance. **Confirmed: works for simple subjects** (single cat on sunlit floor — cat identity preserved across steps). The failure is specifically with complex ornamented subjects (religious icons, detailed sculptures, heavily costumed characters). **Workarounds:** (1) Frame interpolation between manually crafted keyframes — the exact anchor pixel is preserved because it IS a frame. (2) Use a different I2V model (e.g., Mochi) if exact preservation is critical. (3) Composite a static PNG onto a blank background animation in post. (4) Accept approximate preservation — output may still be beautiful even if not pixel-perfect. **Rule of thumb:** Simple subjects (animals, people in basic poses) → I2V works fine. Complex ornamented subjects (religious icons, detailed sculptures, heavily costumed characters) → I2V will transform them. Use alternatives for the latter.
- **Configuration Errors:** If generation fails immediately, check `video_generation.json` using `references/json-config-structure.md`. Common issues are missing `model_type` within the task block or empty `prompt` fields.
- **Multiple Character Inputs:** When using multiple I2V anchors, provide them as a JSON list in `image_start` as shown in `references/json-config-structure.md`.
- **Orphaned wgp.py can deadlock GPU → system hang.** When a Hermes session ends mid-execution (timeout, Telegram disconnect, agent crash), background `wgp.py` GPU processes are left orphaned. These processes can enter a hung/deadlocked state in the NVIDIA driver (`D` state / uninterruptible sleep). Processes in `D` state CANNOT be killed with `kill -9`. When the GPU driver is stuck, the entire system becomes unresponsive — no new terminal sessions, no SSH, no Ctrl-Alt-F1. The ONLY recovery is a hard reboot. **Prevention:** (1) Always check for orphans BEFORE starting a new job: `ps aux | grep "wgp.py" | grep -v grep`. (2) If orphaned wgp.py is found, try `kill -15 <pid>` first (graceful), wait 5s, then `kill -9 <pid>`. If `kill -9` does nothing or returns "Cannot send process signal", the process is in D state and the GPU is already deadlocked. (3) After killing orphans, run `nvidia-smi` — if it hangs/fails, the GPU driver is deadlocked and a reboot is required. **Recovery when GPU is deadlocked:** Hard reboot is the only option. After reboot, check `journalctl -b -1` — if logs end abruptly with no shutdown sequence, this confirms a hard crash from GPU deadlock. See `references/orphan-process-hang.md` for the May 3 crash case study. **Session evidence (2026-05-03):** Fantasy reel batch generation session ended at 01:50 AM. Orphaned wgp.py from mid-execution batch 2 deadlocked GPU. System had zero logs between May 3 01:50 and May 4 10:08 — the journal never flushed because the crash was immediate hardware-level. `dmesg` empty, no OOM killer, no kernel panic. Confirmed: force-reboot resolved it.

- **Upsampling phase OOM (exit code -9, May 7, 2026).** WanGP can crash with SIGKILL (-9) during the final `[0/1] Upsampling` phase, even after all denoising and VAE decoding completed successfully. **Pattern:** Denoising First Pass → VAE Decoding → Denoising Second Pass → VAE Decoding → ALL succeed, then crash at `[0/1] Upsampling`. The output is NOT written if it crashes during upscaling — the compressed file from a previous session may exist in the output dir but is stale. **Diagnosis:** Check `ls -la *.mp4` and compare timestamps against generation start time. **Mitigation:** Reduce upscaling VRAM by: (1) Remove `spatial_upsampling` entirely (set to `""`), (2) Downgrade temporal upsample from `rife4` to `rife2`, (3) Enable `RIFLEx_setting: 1` for smoothness without heavy upscaling computation. This configuration was confirmed working after a crash at rife4/lanczos1.5 with CrispEnhance @ 0.5.

- **Continue-from OOM on second-pass denoising (exit code -9).** When a scene uses `continue_from`/`--video-source`, WanGP's second-pass denoising loads BOTH the source video's latent representation AND the new scene's data into VRAM simultaneously. On a 24 GB GPU, the 6th scene of a continue_from chain can OOM (SIGKILL / exit -9) during the second pass even though all prior scenes completed fine. **Pattern:** Scenes 1-5 complete without issue, scene 6+ fails with `[Sliding Window X/Y] - Denoising Second Pass` then `exit code -9`. **Mitigation:** If scene N fails, re-run the pipeline — it will resume from scene N (the GPU has freed up since the crash). If the same scene keeps OOMing, split the movie into two batches (scenes 1-N and scenes N+end), deliver the last frame of batch 1, then generate batch 2 separately.

## Ablation Study Workflow

When testing multiple parameter combinations (guidance_scale, steps, LoRA weights, etc.), use this structured pattern to ensure traceability:

1. **Create a dedicated ablation folder** under the appropriate post directory, e.g. `posts/2026-05-02_7/`.
2. **Create a master reference file** (`ablation_settings.md`) mapping each variant to its exact settings. This is the single source of truth — future agents (and you) can look at any output and know exactly which parameters produced it.
3. **One subdirectory per variant**, containing:
   - `video_generation.json` — the exact config used (modified from a base config with only the parameter(s) under test changed)
   - The output video (e.g. `office_gscale_1.mp4`)
4. **Naming convention**: `{prefix}_paramname_value/` — e.g. `office_gscale_1/`, `office_gscale_3/`, `office_gscale_5/`
5. **Keep everything else constant**: same seed, same prompt, same anchor image, same LoRA configuration across all variants. Only vary the parameter(s) under test.
6. **Sequential execution** — run one variant at a time, wait for completion, then move to the next.

Example structure:
```
posts/2026-05-02_7/
├── ablation_settings.md          ← Master reference
├── office_gscale_1/              ← Variant A
│   ├── video_generation.json     ← exact config used
│   └── office_gscale_1.mp4       ← output
├── office_gscale_3/              ← Variant B (baseline)
│   ├── video_generation.json
│   └── office_gscale_3.mp4
└── office_gscale_5/              ← Variant C
    ├── video_generation.json
    └── office_gscale_5.mp4
```

**Master reference format**: For each variant, document:
- Parameter values in a table
- Output file location
- What to look for when comparing

**Note**: Templates ship with empty `activated_loras: []`. No LoRAs are active by default. To activate LoRAs, pass `--activated-loras` and `--loras-multipliers` explicitly.

## Supporting references

- [`references/telegram-delivery-pattern.md`](references/telegram-delivery-pattern.md) — Optimized delivery for Telegram with chunked previews and retry logic.
- [`references/telegram-timeout-fix.md`](references/telegram-timeout-fix.md) — Solving `read timeout exceeded` on large media files.
- **CRITICAL: `image_start`/`image_end` must be FILE PATH STRINGS, not booleans.** When building a video generation JSON config programmatically, the LTX-2.3 I2V template has `image_start` and `image_end` keys that expect **absolute file path strings** (e.g., `/path/to/anchor.jpg`), NOT boolean `true`/`false`. If you write `"image_start": true` / `"image_end": true`, WanGP's loader throws `[Warning: Invalid filename for key 'image_start']. Skipping.` and then `[ERROR] You must provide a Start Image` — even though the type in the template JSON says `bool`. The loader silently drops booleans and expects strings. The working v2 config had them as path strings; any programmatic config builder must produce strings, not booleans.

**Session evidence (2026-05-06):** Video gen failed with exit 1 because config had `"image_start": true` / `"image_end": true`. Fixed by using `"image_start": "/path/to/start.jpg"` and `"image_end": "/path/to/end.jpg"` (file path strings).
- [`references/telegram-timeout-fix.md`](references/telegram-timeout-fix.md) — Diagnosis of the Telegram agent-turn timeout problem with `--run`.
- [`references/orphan-process-hang.md`](references/orphan-process-hang.md) — GPU deadlock case study from May 3.
- [references/json-config-structure.md](references/json-config-structure.md) — Reference for required JSON task structure (model_type, image_start arrays).
- [`references/sliding-window-output-files.md`](references/sliding-window-output-files.md) — Extended video output file pattern (do NOT concatenate).
- [`references/wan-app-dir-discovery.md`](references/wan-app-dir-discovery.md) — WanGP app directory discovery.
- [`references/telegram-delivery-pattern.md`](references/telegram-delivery-pattern.md) — Telegram delivery pattern.
