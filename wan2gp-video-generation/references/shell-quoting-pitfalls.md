# Shell Quoting Pitfalls with WanGP Helpers

## Problem: Complex video prompts break `generate_video_config.py`

When passing multi-line dialogue-heavy prompts with nested quotes to `generate_video_config.py` via shell args, the shell mangling causes the wrong argument to receive the prompt text.

**Symptoms:**
- `generate_video_config.py: error: argument --video-prompt-type: invalid choice: 'EXT. GARDEN -- DAY...'` — the full prompt text was consumed by `--video-prompt-type` instead of `--video-prompt`
- `0.5;1.5: command not found` — the `;` in lora multipliers was eaten by the shell
- Escaping single quotes inside single-quoted strings doesn't work in bash (`'\''` breaks the whole argument chain)

## Solutions (in order of reliability)

### 1. Write JSON directly (RECOMMENDED for complex prompts)

Write the full `video_generation.json` yourself with the prompt in a JSON string. Then run WanGP directly with `--process`:

```bash
# Write the JSON manually or via Python (avoids shell entirely)
python3 -c "
import json
prompt = open('video_prompt.txt').read().strip()
config = {
    'model_type': 'I2V',
    'model': 'LTX-2.3 22B Distilled',
    'image_start': '.../anchor.jpg',
    'video_prompt': prompt,
    'video_prompt_type': 'S',
    'sliding_window_size': 481,
    'video_length': 721,
    'num_inference_steps': 25,
    'guidance_scale': 3.5,
    'seed': -1,
    'activated_loras': ['LTX2.3_Crisp_Enhance.safetensors', 'Pixar_Toon.safetensors'],
    'loras_multipliers': '0.5;1.5'
}
with open('video_generation.json', 'w') as f:
    json.dump(config, f, indent=2)
"

# Run WanGP directly
$WAN_PYTHON wgp.py --process video_generation.json --output-dir . --compile --attention sage2 --profile 4 --fp16
```

### 2. Write prompt to a file, use Python to construct full JSON

If you want the helper to validate/adjust parameters, read the prompt from a file via Python and write the output JSON:

```bash
# Write prompt to file first
echo 'EXT. GARDEN -- DAY...' > video_prompt.txt

# Then use Python to build the config (as above)
```

### 3. Use heredoc for `--video-prompt` (works for simpler prompts)

```bash
python3 "$PROFILE_SKILLS/.../generate_video_config.py" \
    --image-start anchor.jpg \
    --video-prompt "$(cat <<'EOF'
EXT. GARDEN -- DAY. Character says "hello" and jumps.
EOF
)" \
    --video-prompt-type S \
    --output-filename test \
    --output-dir . \
    --aspect 9:16 \
    --run
```

The heredoc with `<<'EOF'` (quoted delimiter) prevents all shell expansion inside the block.

### 4. If using `generate_video_config.py` with simple prompts

For short prompts with NO quotes, single-quote the args and use `"` inside:

```bash
python3 "$PROFILE_SKILLS/.../generate_video_config.py" \
    --image-start anchor.jpg \
    --video-prompt 'Camera pushes in slowly.' \
    --video-prompt-type S \
    --output-filename test \
    --output-dir . \
    --aspect 9:16 \
    --activated-loras Crisp.safetensors \
    --loras-multipliers "0.5" \
    --run
```

## Key rule

**If your video prompt contains dialogue with quoted speech, multi-line structure, or complex descriptions — write the JSON manually or via Python. Do NOT try to shell-quote it into `generate_video_config.py`.** The helper is designed for simple prompts; complex dialogue requires the JSON file approach.
