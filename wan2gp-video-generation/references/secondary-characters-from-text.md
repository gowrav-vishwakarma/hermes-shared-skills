# Secondary Characters From Video Prompt Text

## The Problem

Qwen Image Edit Plus 20B can only reliably generate characters that have reference images passed via `image_refs`. When a scene needs 2+ characters and one has no asset (e.g., an accountant, a bystander, a one-off character), attempts to describe the second character purely in the anchor prompt **fail** — the model either:
1. Ignores the second character entirely (only renders the referenced one)
2. Regenerates the referenced character instead of the new one
3. Produces the wrong person entirely (wrong age, clothing, ethnicity)

This is a hard limitation — not a prompt quality issue.

## Workaround: Describe Secondary Characters in Video Prompt

**The working approach discovered 2026-05-07:**
- Generate the anchor with ONLY the character(s) you HAVE reference images for
- Describe the secondary character(s) in the **video prompt text** with exhaustive visual detail (age, hair, clothing, accessories, expression, pose)
- LTX-2.3 can render additional characters from text during video generation even when the anchor only shows one
- This is a tradeoff: less identity certainty than multi-ref, but it WORKS

## Prompt Crafting for Secondary Characters

Be SPECIFIC in the video prompt:
- Age: "middle-aged man in his 50s" (not "a man")
- Hair: "thinning grey hair" (not "hair")
- Clothing: "dark navy three-piece business suit, white dress shirt, loosened red tie" (not "business clothes")
- Accessories: "clutching a brown leather briefcase tightly"
- Expression: "furrowed deeply wrinkled brows, mouth slightly open in anxiety"
- Body language: "shoulders hunched, posture tense"

The more specific the description, the more likely LTX-2.3 will render the intended character.

## Limitations

- The secondary character will NOT have the same visual identity across multiple videos/posts (no reference image = no identity locking)
- Consistency across scenes depends entirely on prompt text — slight variations are expected
- For character-critical scenes where the secondary character's look matters a lot, try the 2-stage approach (generate the secondary char as a standalone image first, then use both as refs for the anchor) — but this also often fails

## Session Evidence

**2026-05-07:** Tried generating accountant character:
- Attempt 1: Multi-char anchor with 1 ref — accountant completely missing
- Attempt 2: 2-stage generation (standalone accountant) — produced wrong character (young man in kurta)
- Attempt 3: Stronger 2-stage prompt — produced Ginnie again
- Attempt 4 (WORKING): Single-ref Ginnie-in-maze anchor + full accountant description in video prompt — LTX-2.3 rendered the accountant during video generation
- Total GPU time wasted on failed attempts: ~7 minutes across 3 passes
