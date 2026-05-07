# Dual-Frame Keyframing (Start + End)

LTX-2.3 via WanGP supports specifying both a start image AND an end image in a single I2V pass. This creates a keyframed video that evolves from one composition to another.

## How it works

Use `--image-start` for frame 0 and `--image-end` for the final frame. The `generate_video_config.py` script automatically appends `"E"` to `image_prompt_type`, making it `"SE"`. The model guides generation toward the end composition at the last frame.

## Example invocation

```bash
python3 "$PROFILE_SKILLS/wan2gp-video-generation/scripts/generate_video_config.py" \
    --prompt "Accountant sinks in water of numbers, face panicked, eyes widening. At ~5s Ginnie reaches down, pulls him up through the water. He emerges dripping, face shifts from terror to relief. Ginnie stands on dock, confident, gives thumbs up." \
    --image-start "/path/to/sinking_anchor.jpg" \
    --image-end "/path/to/rescue_anchor.jpg" \
    --output-filename sinking_to_rescue \
    --output-dir "$POSTS_DIR/2026-05-07_1" \
    --aspect 9:16 \
    --video-length 481 \
    --model distilled-1.1 \
    --run
```

## When to use this vs alternatives

| Approach | When | Pros | Cons |
|----------|------|------|------|
| **Start + End (SE)** | You know both opening and closing compositions | Single pass, coherent transition, no scene breaks | Model must bridge both compositions in one prompt |
| **Movie pipeline (`continue_from`)** | Multi-scene narrative, hard cuts between distinct scenes | Each scene is self-contained, full control per scene | Requires multiple GPU passes, stitching |
| **I2V only (S)** | Single continuous shot, no hard end composition needed | Fastest, simplest | No guarantee of final frame composition |
| **Frame injection (KFI)** | You need intermediate keyframes at specific positions | Precise control at specific timestamps | More refs = more VRAM, more complex prompting |

## Prompting for dual-frame

- Describe the **entire narrative arc** in the prompt — the beginning matches the start image, the middle is the transition, the end matches the end image.
- The video prompt still follows the I2V rule: minimal static description of the opening composition (matching start image), then purely motion/action for the rest.
- Explicitly describe **when** key beats happen: "At approximately 5 seconds..."
- The end image must be visually compatible with the story arc — sudden unrelated compositions cause artifacts.

## Session evidence

2026-05-07: Used dual-frame for "sinking accountant" reel. Start = sinking in numbers (panic), End = Ginnie pulling accountant onto dock (relief, thumbs up). Video completed in 4m 08s, 20s duration, 720x1280. The transition was coherent — panic escalation for first ~5s, then rescue, then Ginnie's thumbs up match.
