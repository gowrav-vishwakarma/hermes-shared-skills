# Text-to-Video (T2V) for Standalone Narrative Scenes

When generating videos without character references (no `--image-start`), the prompt must fully describe the entire scene including subject, action, environment, lighting, and camera movement. This is the **text-to-video (T2V)** workflow.

## When to use T2V standalone

- **Standalone narrative scenes** (no character continuity required)
- **Establishing shots** (cityscapes, landscapes, environments)
- **Action sequences** (robot patrols, explosions, chases)
- **Atmospheric pieces** (mood pieces, transitions)
- **B-roll footage** (supporting visual elements)

## T2V Prompt Structure

For a 20-second standalone scene, include all 6 cinematic elements:

### 1. Establish the Shot
```
Cinematic wide establishing shot of dystopian 2050 city at night
```

### 2. Set the Scene (Lighting, Atmosphere, Color)
```
Heavy rain falls on neon-lit streets, fog rolls across the ground
Cold blue and teal color palette, high contrast, cyberpunk aesthetic
```

### 3. Describe the Action
```
Sleek metallic robots with glowing blue AI cores patrol the streets, their optical sensors scanning with laser beams
Humans crouch in shadows behind overturned debris, huddled together in fear
```

### 4. Camera Movement
```
Camera slowly pans right, handheld documentary style for gritty realism
```

### 5. Audio Description
```
Sound of rain, distant sirens, mechanical footsteps
```

### 6. Visual Style Markers
```
Photorealistic, 8K, film grain
```

## Complete T2V Prompt Template

```
[Shot scale], [subject] [action] in [environment]. [Lighting/atmosphere]. [Color palette], [contrast level]. [Camera movement]. [Audio description]. [Visual style markers].
```

**Example:**
> "Cinematic wide establishing shot of dystopian 2050 city at night. Heavy rain falls on neon-lit streets, fog rolls across the ground. In the foreground, sleek metallic robots with glowing blue AI cores patrol the streets, their optical sensors scanning with laser beams. Humans crouch in shadows behind overturned debris, huddled together in fear, their faces illuminated only by flickering neon signs. Cold blue and teal color palette, high contrast, cyberpunk aesthetic. Camera slowly pans right, handheld documentary style for gritty realism. Sound of rain, distant sirens, mechanical footsteps."

## T2V vs I2V Decision Matrix

| Use Case | Recommended Approach |
|----------|---------------------|
| Character introduction/reintroduction | I2V with anchor |
| Same character across scenes | I2V with anchor |
| Standalone scene (no character) | T2V |
| Establishing shot | T2V |
| Continuity of specific visual element | I2V with anchor |
| New location/scene with character | I2V with anchor |
| Abstract/atmospheric piece | T2V |

## T2V Configuration Parameters

For standalone narrative scenes, use these defaults:

```bash
--aspect 16:9           # or 9:16 for Instagram
--seed 12345            # random seed for variation
--steps 25              # standard quality
--guidance-scale 3.5    # balanced prompt adherence
--sliding-window-size 481  # 20 seconds @ 24fps
--video-length 481      # single-pass generation
```

## Common T2V Pitfalls

1. **Missing action verbs** - Even "calm" scenes need motion: "steam curls from the mug" not just "a cup of coffee"
2. **Incomplete scene description** - Model fills gaps unpredictably
3. **No camera movement** - Static prompts produce static images
4. **No audio description** - Audio generation will be generic or missing
5. **Overly complex scenes** - Keep to 1-2 focal points per shot

## Example: Robot Patrol Scene (Session 2026-05-12)

**Prompt:**
> "Cinematic wide establishing shot of dystopian 2050 city at night. Heavy rain falls on neon-lit streets, fog rolls across the ground. In the foreground, sleek metallic robots with glowing blue AI cores patrol the streets, their optical sensors scanning with laser beams. Humans crouch in shadows behind overturned debris, huddled together in fear, their faces illuminated only by flickering neon signs. Cold blue and teal color palette, high contrast, cyberpunk aesthetic. Camera slowly pans right, handheld documentary style for gritty realism. Sound of rain, distant sirens, mechanical footsteps."

**Output:** `/home/gowrav/.hermes/profiles/gvs/home/posts/2026-05-12/scifi_2050_robots/scifi_2050_robots.mp4`
**Duration:** ~20s
**Generation time:** 3m 37s (includes TorchInductor compilation)
