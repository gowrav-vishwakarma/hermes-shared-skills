# LTX-2.3 Director-Style Prompting Guide

Full reference for writing LTX-2.3 video prompts. The parent SKILL.md summarises the essentials; this file is the canonical deep-dive.

Adapted from the [official LTX Prompting Guide](https://docs.ltx.video/api-documentation/prompting-guide), the [LTX-2.3 Prompt Guide](https://ltx.io/model/model-blog/ltx-2-3-prompt-guide), and session learnings.

---

## Core Principles

### Be specific and descriptive
Instead of "a person walking," write "a young woman in a red coat walking briskly through a rain-soaked Tokyo street at night, neon reflections on wet pavement, handheld camera following from behind."

### Describe the full scene
Include the subject, their action, the environment, the lighting, and the camera behavior. The more complete the description, the closer the output matches your intent.

### Use cinematic language
Terms like "macro lens," "tracking shot," "shallow depth of field," "golden hour," and "low angle" are understood by the model and directly influence the output.

### Describe audio when relevant
For endpoints that generate synchronized audio, include audio descriptions: "the sound of rain on pavement," "soft ambient music," "a crowd cheering in the distance."

### Long prompts for long videos
LTX-2.3 has a redesigned text connector that makes it significantly more responsive to prompt details than earlier versions. Specific descriptions of facial expressions, timing, pauses, and emotional beats translate more reliably into the output. This means longer, more descriptive prompts consistently outperform short ones. A short prompt for a long video (8-20 seconds) results in the model rushing through the described action or filling time with static frames. Match prompt length to video length.

### Iterate freely
LTX is designed for fast experimentation. Start simple and layer complexity gradually.

---

## The 6 Key Elements

Every prompt should aim to include these:

### 1. Establish the Shot
Use cinematography terms matching your intended genre. Include shot scale or style characteristics. Leading the prompt with camera movement sets a temporal anchor -- the model uses it to structure everything that follows. "Slow dolly in, close-up on a young man's eyes" gives the model a motion trajectory before it places the subject.

**Camera language:** Follows, Tracks, Pans across, Circles around, Tilts upward, Pushes in / pulls back, Overhead view, Handheld movement, Over-the-shoulder, Wide establishing shot, Static frame.

### 2. Set the Scene
Describe lighting conditions, color palette, surface textures, and atmosphere to establish mood and tone. Sensory detail shapes mood more than adjectives -- describe what the light does, what the air carries, what surfaces feel like.

LTX-2.3 understands spatial positioning -- use terms like "left of frame", "foreground", "background", "center frame", "far right" to place subjects and objects precisely within the composition.

**Lighting:** Flickering candles, Neon glow, Natural sunlight, Dramatic shadows, Backlighting, Rim light, Polar cold white light, Harsh noon sunlight, Cold neon tubes casting warped reflections, Stage spotlight with everything else in deep shadow, Colored light filtering through stained glass scattering fractured shapes, Warm early sun reflecting off glass.
**Textures:** Rough stone, Smooth metal, Worn fabric, Glossy surfaces, Matte metal shell, Frozen lake surface, Rough volcanic rock, Wet carbon fiber, Rain-beaded waterproof fabric.
**Color palette:** Vibrant, Muted, Monochromatic, High contrast, Cyberpunk purple and teal, Earthy ochre and deep moss green, Cool blue-green grading, Warm golden tones.
**Atmosphere:** Fog, Rain, Dust, Smoke, Particles, Turbulent clouds at high altitude, Cold mist beneath aurora, Diffused light within a sandstorm, Fine rain slanting through air glowing beneath streetlights, Ocean wind carrying salty chill pushing sand grains across beach, Subtle grinding of metal gears echoing through empty factory.

**Example:** "A futuristic airport in heavy rain. Cold blue ground lights trace the runway. Lightning tears across the edges of dark storm clouds. The surface reflects like wet carbon fiber under the storm."

### 3. Describe the Action and Blocking
Write the core action as a natural sequence, flowing clearly from beginning to end. Not a list -- a screenplay.

Static descriptions without verbs can produce still-image output. Even for calm scenes, include motion verbs: "adjusts her scarf", "shifts her weight", "breathes deeply", "steam curls from the mug". This signals the model to generate actual motion.

**Blocking** is the choreography between subject movement and camera movement. Describe them as interleaved -- what the subject does, then how the camera responds, then what the subject does next. This back-and-forth is what makes a shot feel directed rather than observed.

> She steps forward through the corridor, and the camera tracks sideways to follow. She pauses at the viewport, pressing her hand against the glass, as the camera slowly pushes in past her shoulder, revealing the planet filling the window beyond.

**Temporal connectors** keep actions flowing naturally and reinforce the passage of time. Use words like *as*, *then*, *while*, *before*, *after*, *when* between actions instead of starting each sentence cold.

**Choppy (avoid):**
> She opens the door. She steps inside. She looks around.

**Connected (use this):**
> As the heavy metal hatch slides open, cold mist spills from the vents. She steps forward through the fog, then the camera tracks sideways, following her as she moves steadily down the illuminated corridor.

**Cause-and-effect phrasing** grounds motion in physical reality. Describe what triggers a motion and what results from it -- LTX-2.3 renders these chains more convincingly than isolated actions.

> The cabin door opens and a rush of air bursts inward. His shoulders drop slightly, his knees bend, and his breathing turns shallow. With each step, he reaches out to brace himself against the rock wall before continuing forward.

### 4. Define the Character(s)
Include age, hairstyle, clothing, and distinguishing features. Express emotion through **physical cues, not abstract labels**.

**Good:** "Her jaw tightens, she blinks rapidly, hand gripping the rail."
**Bad:** "She feels nervous and scared."

The model cannot render "nervous" -- it can render tightened jaw, rapid blinking, white-knuckled grip.

### 5. Identify Camera Movement(s)
Specify how and when the camera moves. Describing how subjects appear *after* the movement helps the model complete the motion accurately.

**Pacing terms:** Slow motion, Time-lapse, Rapid cuts, Lingering shot, Continuous shot, Freeze-frame.

### 6. Describe the Audio
Clearly describe ambient sound, music, speech, or singing. With LTX-2.3's improved audio quality, spending more attention on audio prompts pays off.

- Place spoken dialogue in **quotation marks**.
- Specify language and accent if needed.
- Describe the **acoustic space** -- "echoey hall", "muffled small room", "outdoor open-air", "reverberant cathedral", "tight sound-dampened studio". This helps audio generation match the visual environment's acoustics.
- **Ambient settings:** Coffeeshop noise, Wind and rain, Forest ambience with birds, Distant traffic hum, Room tone.
- **Dialogue style:** Energetic announcer, Resonant voice with gravitas, Distorted radio-style, Robotic monotone, Childlike curiosity.
- **Volume:** Whisper, Mutter, Shout, Scream.

---

## Practical Tips for Quality

### Close-up to wide progression

Close-ups help the model retain facial and material detail. Widening the shot afterwards reveals the environment without losing the subject's identity established in the opening frames.

### Wider shots and likeness

The further the camera is from the subject, the more identity and fine detail can drift. Techniques that help: keeping the subject at a roughly consistent distance, turning them away or into profile during wide moments, returning to closer framing for dialogue or emotional beats.

### Soft closing actions

When dialogue and action finish before the video duration ends, the model fills remaining time with frozen frames or aimless drift. A closing beat -- a held gaze, a gentle camera pull-back, a slow pan across the environment -- gives the model something to render through to the end.

### Smooth reframing

Gradual camera transitions ("the camera slowly pans right", "the frame gently widens") produce cleaner output than jarring zooms or snap reframes, which can introduce warping artifacts.

---

## Dialogue Segmentation

This is the single biggest quality lever for talking-head videos. A monologue produces static frames; segmented dialogue with acting beats produces visible motion.

### The pattern

Break dialogue into **2-4 short quoted lines** (5-15 words each). Between each line, insert a **physical acting beat** -- a gesture, a camera move, or an environmental reaction.

### Example

**Flat (static talking head):**
> The character speaking: "Oh my god you can see this with me this is what astronomers call a stellar aurora when the nebula's charged particles dance with magnetic fields I've never seen anything like it in all my travels the colors are alive."

**Segmented (visible motion and dynamics):**
> He turns toward the camera, Hindi-accented English, warm intimate tone, "You are seeing this with me, right?" He steps closer to the dome, palm pressing against the glass. "That is a stellar aurora -- charged particles dancing on the nebula's magnetic field lines." His eyes widen, breath fogging the visor briefly, voice dropping to near-whisper, "I have never seen colours move like this." A slow dolly-in past their shoulder reveals emerald and crimson ribbons twisting overhead. Audio: low station hum, soft plasma crackle, intimate close-mic.

### Why it works
Each acting beat gives LTX-2.3 a cue to change pose, camera, or expression. Without them, the model has no instruction to generate motion between spoken words.

### Accent and voice cue
Include **once** near the start of the prompt, right before the first quoted line. Pull the specific accent, tone, and verbal quirks from `SOUL.md` for the active character.

---

## Multi-Character Scenes

Scenes with 2+ characters require careful camera pacing to avoid visual confusion.

### Principles

- **Linger before transitioning.** Let the camera hold on one speaker for their full line and reaction before moving to the next. Rushing between characters produces jittery output.
- **Flow through reactions.** When switching focus, describe the transition as a natural camera movement -- pan, follow a gesture, shift focus -- not a cut.
- **Physical handoffs.** Have one character gesture toward the other, or look in their direction, then describe the camera following that gesture. This gives the model a reason to move the frame.
- **Keep it to 2-3 characters.** More than 3 subjects in a 20-second shot overwhelms the model and softens all of them.

### Example (two characters, ~15 s)

> The shot opens in a close-up on the woman's face, warm light catching her silver hair. She looks into the camera, "Funny how quiet it gets." She takes a breath, glances toward the empty street, a small knowing smile crossing her face. She nods once, then turns and begins walking away. The camera follows her for a few steps, then slows as she moves away. The camera begins to pan right. The soft rumble of a tractor grows in the distance. It rolls gently into view, a man in a flat cap at the wheel. He glances toward the direction the woman walked, then looks ahead. A small smile flickers. He murmurs quietly, "Still is." The camera holds on him as the tractor rolls on, the hum fading into stillness.

---

## Audio-Video Sync Techniques

LTX-2.3 generates audio and video simultaneously. These techniques tighten synchronization between what's seen and what's heard.

### Temporal cueing

Tie a visual event to a specific audio moment. The model aligns the action to the sound beat.

- `"On the heavy drum beat"` -- action fires on a musical hit
- `"On the third bass hit"` -- precise timing to a specific count
- `"At the 3-second mark"` -- timestamp-based cueing for exact placement

### Action regularity

Repetitive, rhythmic actions sync better than erratic ones. Describe the rhythm explicitly.

- `"Constant speed tracking shot"` -- keeps camera movement predictable
- `"Rhythmic oscillation"` -- creates regular-interval movement
- `"Steady heartbeat pulse"` -- maintains a consistent audio-visual pattern

### Combined example

> A robotic arm precisely grabs a component on the bass hit, its metallic pincers opening and closing in a perfect rhythm. The camera remains steady in a close-up, while each grab produces a crisp metallic clank that echoes through the sterile, dust-free lab.

### Foley layering

Build a complete soundscape by combining three audio layers:

1. **Ambient bed** -- continuous environmental sound (engine hum, wind, room tone)
2. **Foley / SFX** -- action-specific sounds (footsteps crunching, metallic clank, brush on pottery)
3. **Music or dialogue** -- foreground audio (speech, score, singing)

> The roar of engines fills the airspace. Clear instructions come through the radio. "We've reached the designated altitude." The pilot reports in a steady, controlled voice.

---

## I2V Anchor Coherence

When `image_start` is set, LTX-2.3 decodes from the anchor as frame 0 and continues in a **single continuous shot**. The model already sees the anchor image -- focus prompt content on what **changes** from that state rather than restating what's visible. Describe the motion, the shift in expression, the camera move that begins, the sound that starts. Redundant descriptions of static elements waste token budget and can confuse the model into freezing on them.

### 1. Mirror the anchor in the opening sentence
The first 1-2 sentences must match the anchor's composition (INT/EXT, subject pose, wardrobe, primary light source), then immediately pivot to the first action or change. Use near-verbatim wording from the anchor brief but keep it brief -- just enough to lock continuity, then move forward.

### 2. No hard cuts
Never write `CUT TO`, `cuts to exterior view`, `JUMP CUT`, `MEANWHILE`, or any directive asking for a discontinuous shot. The anchor and the rest of the clip share one camera. Reveal new elements via camera moves: dolly in past shoulder, slow push-in toward window, tilt up, pan to follow gaze.

### Static-start bug
LTX-2.3's I2V pipeline reads the first sentence as a "cold start" directive. If the opening describes static scene elements (environment, posture, room setup) *before* the anchor's actual action, LTX renders 2-4 seconds of frozen/static frames at the start.

**Fix:** The first sentence must describe the exact pose/action visible in the anchor. No scene-setting before it.

**Good:** "INT. OBSERVATION DECK. The character, in their signature suit, looks through the curved window at the approaching nebula, then slowly turns toward the camera as her expression softens."
**Bad:** "INT. OBSERVATION DECK. The character stands still. They look through the window..."

---

## Duration-Based Prompt Strategy

Match prompt length and structure to the target duration. Shorter clips need razor focus; longer clips need narrative arc.

### Short-form: under 5 seconds

One clear action, simple camera work, minimal scene complexity. Strip away anything that doesn't serve the single moment.

- **One clear action** -- no subplots or secondary movements.
- **Simple camera** -- static shot or a single basic pan/zoom.
- **Clean background** -- minimal elements reduce hallucinations at short durations.

> A silver coin is flicked from a thumb, flipping rapidly through the air before landing precisely back in a palm. Close-up, shallow depth of field, crisp cold metallic reflections.

### Mid-form: 5-10 seconds

A micro-narrative with a clear beginning, middle, and end. 2-3 connected actions with one fluid camera motion.

- **2-3 connected actions** -- a logical progression of movement.
- **One consistent camera path** -- avoid jerky cuts; stick to one motion.
- **Clear progression** -- sense of moving from one state to another.

> An astronaut reaches out to touch the viewport, her fingertips gliding across the cold glass as she gazes at the swirling blue planet outside. The camera slowly dollies forward, shifting the focus from her immediate reflection to the vast, shimmering expanse of the cosmos.

### Long-form: 15-20 seconds (481 frames)

A mini-scene with three-act structure. This is where long, detailed prompts pay off -- a 10-word prompt for 20 seconds leaves the model directionless.

**Recommended format** -- structure the prompt in this order:

1. **Scene header** -- place and time: `INT. BEDROOM -- MORNING` or `EXT. TOWN SQUARE -- DAWN`.
2. **Opening beat (0-4 s)** -- where the subject is, what they do first, atmosphere. Start with a close-up to ground detail, then widen.
3. **Blocking + dialogue (4-15 s)** -- interleaved subject actions, camera moves, and 2-3 short dialogue lines with acting beats. This is where most visual interest happens.
4. **Closing beat (15-20 s)** -- a final spoken line, a held reaction shot, or a gentle camera pull-back. Include performance cues in parentheses for tone: `(quietly)`, `(grinning)`, `(almost to herself)`.

**Long-take example (20 s):**
> EXT. EMPTY TOWN SQUARE -- MORNING. The shot opens in an extreme close-up of an older woman's face, sunlight glinting in her silver hair. Her eyes are calm, thoughtful. She turns slightly, looking directly into the camera. She speaks quietly, "Funny how quiet it gets." She takes a breath, glances toward the empty street, then looks back. A small knowing smile crosses her face. She nods once, almost to herself. After a beat, she turns and begins walking down the street. Her footsteps echo softly on the stone. The camera follows her for a few steps, then slows as she moves away. She turns a corner and disappears. For a moment, the shot holds on the quiet square. Then slowly the camera begins to pan right. The soft rumble of an old tractor grows in the distance. The tractor rolls gently into view, its faded paint catching the morning light. The camera holds as the tractor crosses the frame, engine humming low and rhythmic, before the shot ends.

---

## What Works Well

| Strength | Description |
|----------|-------------|
| Cinematic compositions | Wide, medium, close-up with thoughtful lighting, shallow DoF, natural motion |
| Emotive human moments | Strong single-subject emotional expressions, subtle gestures, facial nuance |
| Atmosphere and setting | Fog, mist, golden-hour light, rain, reflections, ambient textures |
| Clear camera language | Explicit instructions like "slow dolly in" or "handheld tracking" |
| Stylized aesthetics | Painterly, noir, analog film, fashion editorial, pixelated animation |
| Lighting and mood control | Backlighting, color palettes, rim light, flickering lamps |
| Voice capabilities | Characters can talk and sing, with support for multiple languages |

## What to Avoid

| Avoid | Why |
|-------|-----|
| Internal emotional states | Use visual cues instead of labels like "sad" or "confused" |
| Text and logos | Readable text is not currently reliable |
| Complex physics | Chaotic motion can introduce artifacts (dancing is OK) |
| Overloaded scenes | Too many characters or actions reduce clarity |
| Conflicting lighting | Mixed light logic confuses scene interpretation |
| Overcomplicated prompts | Start simple and layer complexity gradually |
| Mismatched duration | A 10-word prompt for a 10-second video leaves the model directionless |
| Contradictory directions | "A still, peaceful lake with dramatic waves crashing" confuses the model |

---

## Common Mistakes

- **Too vague:** "A nice video of nature" -- the model has too many options and picks arbitrarily. Be specific about what is in the frame.
- **Over-constrained:** "Exactly 3 birds flying left to right at 45 degrees while the camera pans right at 2 degrees per second" -- the model works best with natural language descriptions, not numerical specifications.
- **Mismatched duration:** A 10-word prompt for a 10-second video -- the model does not have enough direction to fill the duration. Long videos need long prompts.
- **Conflicting directions:** "A still, peaceful lake with dramatic waves crashing" -- contradictions confuse the model. Be internally consistent.

---

## Helpful Terms

### Categories

**Animation:** Stop-motion, 2D / 3D animation, Claymation, Hand-drawn.
**Stylized:** Comic book, Cyberpunk, 8-bit pixel, Surreal, Minimalist, Painterly, Illustrated.
**Cinematic:** Period drama, Film noir, Fantasy, Epic space opera, Thriller, Modern romance, Experimental film, Arthouse, Documentary.

### Technical Style Markers

**Camera language:** Follows, Tracks, Pans across, Circles around, Tilts upward, Pushes in / pulls back, Overhead view, Handheld movement, Over-the-shoulder, Wide establishing shot, Static frame. For the full catalog of 35+ dramatic camera movements with copy-paste prompt phrases, see [`camera-movements.md`](camera-movements.md).
**Film characteristics:** Film grain, Lens flares, Pixelated edges, Jittery stop-motion.
**Scale indicators:** Expansive, Epic, Intimate, Claustrophobic.
**Pacing and temporal effects:** Slow motion, Time-lapse, Rapid cuts, Lingering shot, Continuous shot, Freeze-frame, Fade-in / fade-out, Seamless transition, Sudden stop.
**Visual effects:** Particle systems, Motion blur, Depth of field.

### Lens Language

Focal length descriptions influence framing, depth compression, and spatial feel.

| Focal length | Prompt phrase | Effect |
|--------------|--------------|--------|
| 24mm wide angle | `24mm wide angle lens` | Strong sense of space and environmental scale; slight barrel distortion |
| 50mm standard | `50mm standard lens` | Natural, human-eye perspective; neutral compression |
| 85mm portrait | `85mm portrait lens` | Compression and intimacy; flattering close-ups with soft background |
| 200mm telephoto | `200mm telephoto lens` | Extreme depth compression; isolates subject from background |
| Macro lens | `Macro lens, extreme close-up` | Reveals micro details -- textures, pores, droplets |

### Shutter and Motion Feel

| Description | Prompt phrase | Effect |
|-------------|--------------|--------|
| Cinematic motion blur | `180 degree shutter, classic cinematic motion blur` | Standard film look; smooth natural blur on moving subjects |
| Crisp action | `Fast shutter, crisp motion, sharp detail` | High-energy action with frozen detail in each frame |
| Natural blur | `Natural motion blur, fluid movement` | Realism in moving subjects without excessive smearing |

### Visual Style and Color Grading

| Style | Prompt phrase |
|-------|--------------|
| Film stock emulation | `Fujifilm Provia 100F film texture` or `Kodak Portra 400 color science` |
| High contrast grading | `High contrast image, cool blue-green grading` |
| Desaturated | `Muted color palette, desaturated tones` |
| Warm analog | `Warm analog film, golden tones, soft grain` |
| Noir | `Film noir, high contrast black and white, dramatic shadowing` |
| Cyberpunk | `Cyberpunk purple and teal contrast, neon gradient glow` |
| Earthy natural | `Earthy ochre and deep moss green palette` |

### Keywords for Smooth Motion

When targeting fluid, stable output, use these terms together with camera descriptions.

**Camera stability:** Stable dolly push, Smooth gimbal stabilization, Tripod locked off, Constant speed pan.
**Motion quality:** Natural motion blur, Fluid movement, Controlled motion, Stable tracking.
**Avoid:** Chaotic handheld (introduces warping), Shaky camera, Irregular motion.

---

## Sample Prompts

### Example 1 -- Live news broadcast (~20 s)

> EXT. SMALL TOWN STREET -- MORNING -- LIVE NEWS BROADCAST. The shot opens on a news reporter standing in front of a row of cordoned-off cars, yellow caution tape fluttering behind him. The light is warm, early sun reflecting off the camera lens. The faint hum of chatter and distant drilling fills the air. The reporter, composed but visibly excited, looks directly into the camera, microphone in hand. Reporter (live): "Thank you, Sylvia. And yes -- this is a sentence I never thought I'd say on live television -- but this morning, here in the quiet town of New Castle, Vermont... black gold has been found!" He gestures slightly toward the field behind him. Reporter (grinning): "If my cameraman can pan over, you'll see what all the excitement's about." The camera pans right, slowly revealing a construction site surrounded by workers in hard hats. A beat of silence -- then, with a sudden roar, a geyser of oil erupts from the ground, blasting upward in a violent plume. Workers cheer and scramble, the black stream glistening in the morning light. The camera shakes slightly, trying to stay focused through the chaos. Reporter (off-screen, shouting over the noise): "There it is, folks -- the moment New Castle will never forget!" The camera catches the sunlight gleaming off the oil mist before pulling back, revealing the entire scene -- the small-town skyline silhouetted against the wild fountain of oil.

### Example 2 -- Frog yoga studio (~20 s)

> The camera opens in a calm, sunlit frog yoga studio. Warm morning light washes over the wooden floor as incense smoke drifts lazily in the air. The senior frog instructor sits cross-legged at the center, eyes closed, voice deep and calm. "We are one with the pond." All the frogs answer softly: "Ommm..." "We are one with the mud." "Ommm..." He smiles faintly. "We are one with the flies." A pause. The camera pans to the side towards one frog who twitches, eyes darting. Suddenly its tongue snaps out, catching a fly mid-air and pulling it into its mouth. The master exhales slowly, still serene. "But we do not chase the flies..." Beat. "not during class." The guilty frog lowers its head in shame, folding its hands back into a meditative pose. The other frogs resume their chant: "Ommm..." Camera holds for a moment on the embarrassed frog, eyes closed too tightly, pretending nothing happened.
