---
name: wan2gp-video-generation
description: LTX-2.3 video generation via WanGP -- director-style prompting, audio direction, I2V coherence
category: media
---

# WanGP Video Generation (LTX-2.3)

Generate ~20 s videos (481 frames @ 24 fps) with native audio using **LTX-2.3 22B distilled** through WanGP CLI. Supports **text-to-video** (T2V) and **image-to-video** (I2V) -- the helper auto-picks from `--image-start`.

## Environment variables

**CRITICAL: The `.env` file is NOT auto-sourced into agent subprocess shells.** Before running any helper script, you MUST manually source it:

```bash
set -a; source $PROFILE_ROOT/.env; set +a
```

Or in Python subprocess calls, explicitly pass the env dict after sourcing:
```python
env = {**os.environ}
with open('$PROFILE_ROOT/.env') as f:
    for line in f:
        if '=' in line:
            k, v = line.split('=', 1)
            env[k.strip()] = v.strip()
```

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
| Large Scale Drone Orbit | `Large scale drone orbit, massive sweeping circle around the landscape` | Epic environment showcase |
| Top Down (God's Eye) | `Top down shot, camera pointing straight down, slow twist` | Abstract composition; overhead reveal |
| FPV Drone Dive | `FPV drone dive, aggressive diving motion down a vertical structure` | Adrenaline; vertiginous descent |

#### Stylized / Effect

| Movement | Prompt phrase | When to use |
|----------|--------------|-------------|
| Handheld Documentary | `Handheld camera, shaky motion, natural movement, documentary style` | Raw authenticity; vlog feel |
| Dutch Angle (Roll) | `Dutch angle, camera roll, tilted sideways on Z-axis` | Unease, instability, tension |
| POV Walk | `POV walk, first person camera moving forward with bobbing motion` | Immersive exploration; horror |
| Over the Shoulder | `Over the shoulder shot, camera mounted behind subject A framing subject B` | Dialogue scenes; spatial relationship |
| Hyperlapse | `Hyperlapse, camera moves forward rapidly, time accelerated, fast motion, light trails` | Time passage; city energy |
| Barrel Roll | `Barrel roll, camera spins 360 degrees clockwise while moving forward, disorienting` | Surreal, dreamlike sequences |
| Bullet Time | `Bullet time, frozen moment, ultra slow motion, camera orbit` | Freeze peak-action moment |
| Worm's Eye Tracking | `Worm's eye view, low angle tracking, camera moves along the ground looking up` | Power, dominance; hero entrance |

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

#### Pre-flight Checklist

Before running, verify every spoken line is:
1. Wrapped in `"quotes"`
2. Separated from the next line by at least one acting beat
3. 5-15 words per quoted line (keep lines short)
4. Voice/accent specified once near the start
5. Audio direction includes ambient sound and music
6. For I2V: opening sentence mirrors the anchor composition

---

### Multi-Character Scenes

Scenes with 2+ characters require careful camera pacing to avoid visual confusion.

- **Linger before transitioning.** Hold on one speaker for their full line and reaction before moving to the next.
- **Flow through reactions.** Describe transitions as natural camera movements -- pan, follow a gesture, shift focus -- not cuts.
- **Physical handoffs.** Have one character gesture toward the other or look in their direction, then describe the camera following that gesture.
- **Keep it to 2-3 characters.** More than 3 subjects in a 20-second shot overwhelms the model.

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

### What Works Well

| Strength | Description |
|----------|-------------|
| Cinematic compositions | Wide, medium, close-up with thoughtful lighting, shallow DoF, natural motion |
| Emotive human moments | Single-subject expressions, subtle gestures, facial nuance |
| Atmosphere and setting | Fog, mist, golden-hour light, rain, reflections, ambient textures |
| Clear camera language | "slow dolly in", "handheld tracking", "CUT TO:", "camera circles around" |
| Stylized aesthetics | Painterly, noir, analog film, fashion editorial, pixelated animation |
| Lighting and mood control | Backlighting, color palettes, rim light, flickering lamps |
| Voice | Characters can talk and sing; supports multiple languages and accents |

### What to Avoid

| Avoid | Why |
|-------|-----|
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

## I2V Coherence (mandatory when `--image-start` is set)

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

Describe the acoustic environment, character voice qualities, and ambient sounds. Pull persona-specific voice qualities (accent, tone, verbal quirks) from `SOUL.md` -- this skill does not define them.

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
    --prompt "She continues walking along the bank, her dupatta trailing in the wind..." \
    --video-source "$POSTS_DIR/2026-05-04_movie_fantasy/scene_01/scene_01_video.mp4" \
    --output-filename scene_02_video \
    --output-dir "$POSTS_DIR/2026-05-04_movie_fantasy/scene_02" \
    --aspect 9:16 \
    --seed 742981
```
Sets `image_prompt_type: "V"` (WanGP "Continue Video" mode). Mutually exclusive with `--image-start`. Optional `--keep-frames-video-source` controls how many source frames to keep (empty=all). Primarily used by `wan2gp-movie-pipeline` for `continue_from` scenes -- see that skill for full details.

### Step B: Start background execution (survives agent timeout)

```bash
"$WAN_PYTHON" "$WAN_APP_DIR/wgp.py" \
    --process "$POSTS_DIR/2026-05-02_1/video_generation.json" \
    --output-dir "$POSTS_DIR/2026-05-02_1" \
    --compile --attention sage2 --profile 4 --fp16
```
**CRITICAL:** Run this via `terminal(background=true)` with `notify_on_complete=true`. This starts a separate VM process that survives agent turn timeout.

**CRITICAL: `--settings` does NOT trigger generation.** Passing `--settings /path/to/dir` loads the Gradio web UI on port 7860 — it is a web frontend, NOT a CLI execution flag. The process sits idle waiting for a web request. To actually generate, you MUST use `--process <path_to_video_generation.json>` (note: singular `--process`, not `--settings`). See [`references/wan-settings-vs-process-flag.md`](references/wan-settings-vs-process-flag.md) for the full breakdown.

### Step C: Pre-flight -- Check no other wgp.py is running

Before Step B, always verify:
```bash
ps aux | grep "wgp.py" | grep -v grep
```
If any wgp.py is running, DO NOT start a new one (24 GB VRAM / OOM risk). Wait for it to finish first.

**Mandatory flags:**
- `--image-start` is **required** for I2V (NOT `--image-ref` -- that flag does not exist).
- `--aspect` is the preferred way to control orientation (`9:16` or `16:9`). It auto-sets resolution and template. You can still pass `--resolution "WxH"` directly to override.
- `--output-filename` takes the basename without extension.
- **NEVER use `--run` flag.** Always use the split Step A + Step B approach.
- **`$WAN_APP_DIR` points at the `/app/` subdirectory** of the WanGP install (e.g., `/home/gowrav/pinokio/api/wan.git/app`), not the git repo root. `wgp.py` and `env/bin/python` live inside that `app/` directory.

The helper auto-applies the I2V crash-bypass (`image_mode: 0`, `image_prompt_type: "S"`, `input_video_strength: 1`), aligns `sliding_window_size` with `video_length` for a one-pass shot, and prints a coherence reminder when `--image-start` is set. Agents do not configure these details manually.

**LoRAs:** Templates ship with no LoRAs by default (`activated_loras: []`). To add LoRAs, pass `--activated-loras` with the desired LoRA filenames and `--loras-multipliers` with their weights. See [`references/ltx2-3-loras.md`](references/ltx2-3-loras.md) for the full inventory and feature-gated LoRA behavior.

## Model selection

The helper supports two LTX-2.3 checkpoints via `--model <alias>`:

| Alias | Checkpoint | Steps | Speed | When to use |
|---|---|---|---|---|
| `gguf`  | Q6_K GGUF (16 GB) | 8 | Fastest | Day-to-day iteration, quick previews |
| `distilled-1.1` (default) | Distilled v1.1 int8 (19 GB) | 8 | Fast | Need WanGP auto-HDR/outpaint/union-control LoRAs |

> **Benchmark data (RTX 4090, 720x1280, 20s video):**
> - `gguf` (8 steps): ~3-4 min total, no compilation needed (gguf runtime is C++, already compiled)
> - `distilled-1.1` (8 steps): ~3-4 min gen, ~5-8 min first run (TorchInductor compile), ~3-4 min cached re-run

> **Why gguf is fast:** GGUF runtime is llama.cpp (C++ based), weights are pre-compiled and quantized at build time. No PyTorch compilation needed. Loading = "read weights, map to GPU VRAM, go".

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

- **Sequential only.** Never run two `wgp.py` jobs at once (24 GB VRAM / OOM risk).
- **NEVER use `--run` flag.** Always split into Step A (config write) + Step B (background execution). The `--run` flag blocks the terminal call and is killed by agent turn timeout during the 5-6 minute generation.
- **Background execution.** Always run Step B via `terminal(background=true)` with `notify_on_complete=true`. The GPU process runs on the VM and survives agent turn timeout. Use `process(session_id).wait()` to block until completion if needed.
- **WanGP Python.** Always use `$WAN_PYTHON` (= `$WAN_APP_DIR/env/bin/python`) — system `python3` lacks PyTorch and will fail silently.
- **Model configs.** See [`references/model_configs.md`](references/model_configs.md) for exact model string constants.
- **Kill orphans.** Before starting: `ps aux | grep "wgp.py" | grep -v grep` and `kill -9` any stray processes (WanGP web UI can leave hidden ones).

### Polling and notification rules

- **Primary: use `notify_on_complete=true`.** This sends a single notification when the GPU job finishes. No polling needed. This is the recommended approach.
- **Fallback: use the monitor script for timing.** The monitor script reports the process uptime itself. Just check its output for the "RUNNING" status + elapsed time. Act on what it tells you.
- **Never try to track time yourself.** The agent CANNOT reliably count elapsed time between turns. The monitor script reads the process uptime directly. Use its output. Do not try to track start time yourself.

## Pitfalls

- **Using `--run` flag.** KILLS the job on agent turn timeout. The 5-6 minute generation never completes because the terminal call is killed. Always split into config-write + background-exec.
- **Wrong flags.** `--image-ref` does NOT exist -- use `--image-start`. `--aspect-ratio` does NOT exist -- use `--aspect` (preferred) or `--resolution "WxH"`.
- **Aggressive polling.** Polling the monitor script repeatedly creates message spam in Telegram. Use `notify_on_complete=true` as primary method. Only poll once as fallback, never in a loop.
- **Trying to track elapsed time.** The agent CANNOT reliably count minutes between turns. The monitor script reports process uptime — use that. Do not try to track start time yourself.
- **Ignoring stale tracker.** If the tracker file exists with `"status": "running"` but the PID is dead, the gen may have finished between turns. Check `*.mp4` output file directly as fallback.
- **Re-running after timeout.** If the agent thinks it timed out and tries to re-start the same generation without checking for existing output, it risks OOM. Always check for running process AND output file before restarting.
- **Exit code 127 — env vars not expanded.** If `$WAN_APP_DIR` / `$WAN_PYTHON` are not exported in the shell, the command line expands to `/env/bin/python` (empty prefix) and bash returns `No such file or directory` with exit code 127. Recovery: `set -a; source $PROFILE_ROOT/.env; set +a` then retry. When invoking from a Python subprocess, pass `env={**os.environ}` after sourcing, or set the keys explicitly via `env_vars={...}` on the terminal call.

- **Exit code 1 — `models/_settings.json` not found (CWD mismatch).** Running `wgp.py` from any directory other than `$WAN_APP_DIR` causes `FileNotFoundError: models/_settings.json`. The binary loads model config relative to CWD. **Fix:** Always run with `cwd="$WAN_APP_DIR"` (`workdir: "$WAN_APP_DIR"` in terminal calls).

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

- **`monitor_video_gen.py` etime parse bug.** The `parse_etime` function in `monitor_video_gen.py` had a bug on line 37 where `h, m = 0, int(parts[0]), int(parts[1])` tried to unpack 3 values into 2 variables, causing `ValueError: too many values to unpack`. **Fix:** changed to `h, m, s = int(parts[0]), int(parts[1]), 0`. If you encounter this error on a fresh checkout, apply the same fix. Patch applied to skill as of 2026-05-05.
- **`$CHARACTER_ASSETS_MANIFEST` (when using `--ref-assets` in video).** The video config helper imports `asset_manifest.py`, which is now a strict consumer of `$CHARACTER_ASSETS_MANIFEST`. If the env var is missing the script exits immediately with `[env] required env var 'CHARACTER_ASSETS_MANIFEST' not set`. Source `$PROFILE_ROOT/.env` to fix.
- **LTX-2.3 I2V cannot preserve exact visual identity during motion.** LTX-2.3 REGENERATES subjects during motion rather than animating exact anchor pixels. Even with zero LoRAs, high guidance scale (5+), simplified prompts ("same exact idols"), and explicit negative prompts ("transform, change style, different look, new style, fantasy art, cartoon, anime, different appearance, blue skin, different sculpture"), the model will reinterpret/transform subjects — especially complex subjects like religious idols, sculptures, or anything with detailed ornamentation. This is an architectural limitation, not a config issue. **Session evidence (2026-05-02, Radha-Krishna idols):** 3 full iterations attempted: (1) Fantasy_Realism LoRA at 1.0 → complete style transform. (2) No LoRA, negative prompt targeting style change, guidance 6 → STILL transformed. (3) No LoRA, negative prompt, guidance 5, ultra-simple prompt ("exact same colors, same appearance, same golden marble style") → STILL transformed, model reinterpreted the deities. All 3 failed to preserve exact appearance. **Confirmed: works for simple subjects** (single cat on sunlit floor — cat identity preserved across steps). The failure is specifically with complex ornamented subjects (religious icons, detailed sculptures, heavily costumed characters). **Workarounds:** (1) Frame interpolation between manually crafted keyframes — the exact anchor pixel is preserved because it IS a frame. (2) Use a different I2V model (e.g., Mochi) if exact preservation is critical. (3) Composite a static PNG onto a blank background animation in post. (4) Accept approximate preservation — output may still be beautiful even if not pixel-perfect. **Rule of thumb:** Simple subjects (animals, people in basic poses) → I2V works fine. Complex ornamented subjects (religious icons, detailed sculptures, heavily costumed characters) → I2V will transform them. Use alternatives for the latter.
- **Orphaned wgp.py can deadlock GPU → system hang.** When a Hermes session ends mid-execution (timeout, Telegram disconnect, agent crash), background `wgp.py` GPU processes are left orphaned. These processes can enter a hung/deadlocked state in the NVIDIA driver (`D` state / uninterruptible sleep). Processes in `D` state CANNOT be killed with `kill -9`. When the GPU driver is stuck, the entire system becomes unresponsive — no new terminal sessions, no SSH, no Ctrl-Alt-F1. The ONLY recovery is a hard reboot. **Prevention:** (1) Always check for orphans BEFORE starting a new job: `ps aux | grep "wgp.py" | grep -v grep`. (2) If orphaned wgp.py is found, try `kill -15 <pid>` first (graceful), wait 5s, then `kill -9 <pid>`. If `kill -9` does nothing or returns "Cannot send process signal", the process is in D state and the GPU is already deadlocked. (3) After killing orphans, run `nvidia-smi` — if it hangs/fails, the GPU driver is deadlocked and a reboot is required. **Recovery when GPU is deadlocked:** Hard reboot is the only option. After reboot, check `journalctl -b -1` — if logs end abruptly with no shutdown sequence, this confirms a hard crash from GPU deadlock. See `references/orphan-process-hang.md` for the May 3 crash case study. **Session evidence (2026-05-03):** Fantasy reel batch generation session ended at 01:50 AM. Orphaned wgp.py from mid-execution batch 2 deadlocked GPU. System had zero logs between May 3 01:50 and May 4 10:08 — the journal never flushed because the crash was immediate hardware-level. `dmesg` empty, no OOM killer, no kernel panic. Confirmed: force-reboot resolved it.

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

- [`references/model_configs.md`](references/model_configs.md) — Model checkpoint details, guidance scale advice, flag precedence.
- [`references/ltx2-3-loras.md`](references/ltx2-3-loras.md) — Full LoRA inventory, multiplier ranges, feature-gated behavior.
- [`references/telegram-timeout-fix.md`](references/telegram-timeout-fix.md) — Diagnosis of the Telegram agent-turn timeout problem with `--run`.
- [`references/orphan-process-hang.md`](references/orphan-process-hang.md) — GPU deadlock case study from May 3.
- [`references/video-delivery-pattern.md`](references/video-delivery-pattern.md) — Video delivery workflow.
- [`references/wan-app-dir-discovery.md`](references/wan-app-dir-discovery.md) — WanGP app directory discovery.
- [`references/telegram-delivery-pattern.md`](references/telegram-delivery-pattern.md) — Telegram delivery pattern.
