# Generator vs Direct JSON Workflow

## The Problem

`generate_video_config.py` reads from `video_prompt.txt` and **completely overwrites** `video_generation.json`. This means:

- If the user manually edits `video_generation.json` (e.g., removes dialogue lines, changes seed, adjusts timing), running the generator will **destroy all manual edits** and replace them with content from `video_prompt.txt`.
- This has happened multiple times (sessions 2026-05-06_4 and 2026-05-06_5) causing the user to lose their edited prompts.

## Correct Workflow Decision Tree

### When to use `generate_video_config.py`:
- Starting a post from scratch
- `video_prompt.txt` IS the source of truth
- No manual edits have been made to `video_generation.json`
- You want the generator to build the JSON from a prompt file

### When to SKIP the generator:
- User has manually edited `video_generation.json`
- Dialogue lines were changed in the JSON but NOT in the txt file
- Seed was changed manually in JSON
- User says "I updated the JSON directly" or "just run wgp.py"

### When user says they updated the JSON:
1. Verify the JSON is correct by reading it
2. Update `video_prompt.txt` to MATCH the JSON (so they stay in sync)
3. Run `wgp.py` directly — do NOT run the generator
4. Only run generator if user explicitly asks for it

## Example: User Updated JSON

```bash
# WRONG — destroys manual edits:
python3 "$PROFILE_SKILLS/wan2gp-video-generation/scripts/generate_video_config.py" \
    --image-start <path> --prompt "$(cat video_prompt.txt)" --run

# RIGHT — uses existing JSON as-is:
$WAN_PYTHON wgp.py --process "$POSTS_DIR/<post>/video_generation.json" \
    --output-dir "$POSTS_DIR/<post>" --compile --attention sage2 --profile 4 --fp16
```

## `--video-prompt-type` Gotcha

The `generate_video_config.py` script does NOT accept `S` for `--video-prompt-type`. It only accepts:
- PVG, OVG, DVG, EVG, VG, KFI

For plain text prompts (no control video), **omit the flag entirely**. The JSON field `video_prompt_type` should be `""` (empty string).

## Session Evidence

- **2026-05-06_4**: Generator overwrote user's dialogue edits from JSON with old txt content — had to manually rewrite JSON
- **2026-05-06_5**: Same issue — generator overwrote JSON with txt, user had to re-edit