# Divine Deity Video Prompt Patterns

## Overview

Patterns for generating video prompts featuring Hindu deities (Lord Shiva, Durga, etc.) delivering divine messages.

## Core Visual Elements

### Lord Shiva Specific Elements

**Physical Attributes:**
- "Third eye closed on forehead, glowing softly with inner divine light"
- "Rudraksha beads around neck"
- "Sacred ash (vibhuti) on body and forehead"
- "Flowing matted hair (jatā) with river Ganga flowing through"
- "Crescent moon on head"
- "Serene, meditative expression"
- "Cobras around neck (optional)"

**Environment:**
- "Ethereal clouds illuminated by golden light rays"
- "Divine clouds swirling softly"
- "Cosmic backdrop with subtle starlight"
- "Himalayan mountain peaks in distant background (optional)"

**Lighting:**
- "Golden light rays breaking through clouds"
- "Soft inner glow from third eye"
- "Natural divine lighting"
- "Cinematic divine lighting"

## Prompt Structure for Divine Videos

### Structure

```
[Camera movement], [shot scale] on [deity name], a divine [tradition] deity from [setting].
[Physical description with cultural elements].
[Environment description].
[Lighting description].
The being says: "[dialogue line 1]. [Dialogue line 2]. [Final line of message.]"
[Visual closing beat - NO DIALOGUE].
[Camera movement]. [Environmental detail]. Shot on [camera specs], [lens], [lighting style], [photorealism marker].
```

### Example: Lord Shiva (2026-05-12)

```
Slow dolly in, close-up on Lord Shiva, a divine Hindu deity from heaven. The radiant cosmic being with a serene, meditative expression speaks with divine authority and compassion. Third eye glows softly. Sacred ash and rudraksha beads visible. Golden light rays illuminate ethereal clouds around. The being says: "In every challenge, there is an opportunity to trust. Surrender your fears to the divine and find peace within. Faith is not the absence of struggle, but the courage to believe even when you cannot see the path. Let go of control and trust in a greater plan. Your surrender is your strength." The camera slowly pulls back as Lord Shiva offers a gentle, reassuring presence. Divine clouds swirl softly. Shot on Canon EOS R5, 85mm lens, cinematic divine lighting.
```

## Key Guidelines

### 1. Cultural Accuracy

**Include specific cultural elements:**
- Rudraksha beads (not generic beads)
- Sacred ash (vibhuti)
- Third eye (for Shiva)
- Ganga flowing through matted hair
- Crescent moon
- Serene, meditative expression

**Avoid:**
- Generic "ancient wisdom" visual cues
- Non-specific "divine" elements
- Cultural misattributions

### 2. Visual Closing Beat

**Must have NO DIALOGUE in visual closing beat.**

**Example:**
```
[Final dialogue line.]
The camera slowly pulls back as Lord Shiva offers a gentle, reassuring presence. Divine clouds swirl softly.
```

**Why:** LTX-2.3 reads the prompt once. Without a clear visual closing beat, the model may:
- Loop the last dialogue line
- Repeat the message
- End abruptly with frozen frames

### 3. Duration Matching

**20s videos (481 frames):**
- 3-5 dialogue lines
- One continuous visual beat
- Simple camera movement

**30s videos (721 frames):**
- 5-7 dialogue lines
- Extended visual closing beat
- Multiple camera movements possible

**Rule:** Count quoted dialogue lines. Each line should occupy roughly 4-6 seconds of video time.

### 4. Camera Movement

**Recommended for divine videos:**
- "Slow dolly in" - builds intimacy
- "Tight close-up" - focuses on expression
- "Camera slowly pulls back" - gentle closing
- "Tilt up" - reveals grandeur

**Avoid:**
- "Fast dolly in" - too aggressive for divine message
- "Whip pan" - jarring for contemplative content
- "Handheld camera" - breaks the divine atmosphere

### 5. Lighting and Atmosphere

**Divine lighting markers:**
- "Golden light rays"
- "Ethereal clouds"
- "Inner glow"
- "Cinematic divine lighting"
- "Natural divine lighting"

**Atmosphere markers:**
- "Divine clouds swirl softly"
- "Cosmic backdrop with subtle starlight"
- "Glow softly"

## Common Prompt Templates

### Template 1: Lord Shiva - Meditation Message
```
[Camera move] on Lord Shiva. Radiant cosmic being, serene meditative expression, third eye glowing softly. Rudraksha beads, sacred ash, flowing matted hair with Ganga. Golden light rays, ethereal clouds. The being says: "[message]." Camera slowly pulls back. Divine clouds swirl. Shot on Canon EOS R5, 85mm lens, cinematic divine lighting.
```

### Template 2: Durga - Strength Message
```
[Camera move] on Goddess Durga. Radiant warrior goddess, compassionate expression, multiple arms holding divine weapons. Golden armor, lotus flowers, divine glow. The being says: "[message]." Camera slowly pushes in. Divine light intensifies. Shot on Canon EOS R5, 85mm lens, cinematic divine lighting.
```

### Template 3: Krishna - Love Message
```
[Camera move] on Lord Krishna. Gentle divine form, peacock feather on head, flute at side, blue skin with golden glow. Lotus flowers, divine forest backdrop. The being says: "[message]." Camera slowly pulls back. Soft breeze through forest. Shot on Canon EOS R5, 50mm lens, natural divine lighting.
```

## Session Evidence

**2026-05-12: Lord Shiva Divine Message**
- **Image:** `shiva_divine_character_anchor.jpg` (Flux 2 Klein, seed 52000)
- **Video:** `shiva_faith_motivation.mp4` (LTX-2.3, 20s, no CTA)
- **Result:** Successful generation with pure divine message, visual closing beat, no dialogue after final line
- **Duration:** 20s (481 frames)
- **Key:** Final line "Your surrender is your strength." was last quoted text

## Pitfalls to Avoid

### 1. Adding CTA to Divine Messages
**Wrong:** "Your surrender is your strength. Hit like and follow for more divine wisdom."
**Right:** "Your surrender is your strength." [visual closing beat]

Divine messages are complete without CTA.

### 2. Missing Cultural Elements
**Wrong:** Generic "ancient wise being" without specific deity attributes
**Right:** Specific elements (third eye, rudraksha, sacred ash, Ganga, crescent moon)

Cultural accuracy is critical for divine deity content.

### 3. Dialogue After Visual Beat
**Wrong:** "Your surrender is your strength." [beat] "Follow for more."
**Right:** "Your surrender is your strength." [beat, no dialogue]

The last quoted line must be the final text in the prompt.

### 4. Wrong Camera Movement
**Wrong:** "Whip pan transition" for contemplative divine message
**Right:** "Slow dolly in" or "camera slowly pulls back"

Camera movement should match the contemplative nature of divine messages.

## References

- [`references/qwen-realism-challenge.md`](qwen-realism-challenge.md) - Flux 2 Klein for realistic deity generation
- [`references/dialogue-video-workflow.md`](dialogue-video-workflow.md) - CTA and dialogue workflow
- Session 2026-05-12: Lord Shiva divine message video
