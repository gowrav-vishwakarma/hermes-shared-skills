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

## Direct like a director

LTX-2.3 responds best to prompts written like a shot description for a cinematographer. The more specific you are about subject, action, lighting, camera movement, and audio, the closer the output matches your vision. For the full deep-dive see [`references/ltx-2-3-prompting.md`](references/ltx-2-3-prompting.md).

### 6 key elements

1. **Establish the shot** -- cinematography terms matching your genre: "Cinematic medium shot", "Tight close-up", "Wide establishing shot", "Handheld POV".
2. **Set the scene** -- lighting, color palette, textures, atmosphere: "Warm panel glow catches his face", "Rain streaks across neon reflections".
3. **Describe the action** -- natural sequence flowing from beginning to end. No bullet-point lists; let it read like a screenplay.
4. **Define the character(s)** -- age, hairstyle, clothing, distinguishing features. Emotion through **physical cues only**: "eyes widen, hand tightens on the rail", "covers her face, on the verge of tears". Never internal labels like "sad", "confused", "amazed".
5. **Camera movement** -- when and how the camera shifts, and what it reveals after: "The camera slowly dollies in past his shoulder, revealing the nebula through the viewport." See [`references/camera-movements.md`](references/camera-movements.md) for 35+ dramatic camera moves with copy-paste prompt phrases.
6. **Audio** -- ambient sound, music, speech, singing. Spoken dialogue in **quotation marks**. Quotes are **mandatory, not optional** — if a line is spoken by the character, it MUST be wrapped in double quotes. Missing quotes produces gibberish/mouthless speech with no motion. Specify language and accent if needed: "Hindi-accented English, warm intimate tone." For AV sync techniques (temporal cueing to music beats, foley layering), see `references/ltx-2-3-prompting.md`.

### Format rules

- Single flowing paragraph; no line breaks inside the prompt string.
- Present tense verbs for all action and movement.
- **Temporal connectors** -- link actions with *as*, *then*, *while*, *before*, *after* instead of starting each sentence cold. Describe cause-and-effect ("the door opens and a rush of air bursts inward").
- **Match prompt length to duration** -- under 5 s: one action, simple camera; 5-10 s: 2-3 connected actions, one fluid camera move; 15-20 s: three-act mini-scene with detailed blocking. See the Duration-Based Prompt Strategy in `references/ltx-2-3-prompting.md`.
- Match detail level to shot scale: close-ups need more precision than wide shots.
- **Close-up to wide** -- starting with a close-up helps the model retain facial/material detail; widening afterwards reveals the environment without losing identity.
- **Soft closing actions** -- ending a long prompt with a held moment or gentle camera drift prevents the model from filling remaining time with frozen frames.
- **Multi-character pacing** -- for 2+ characters, lingering on one speaker before panning to the next produces cleaner output. Physical handoffs (gesture, gaze direction) motivate camera transitions. Max 2-3 characters per shot.
- **Lens and style language** -- focal length (24mm/50mm/85mm/200mm), shutter feel, film stock emulation, and color grading terms all influence output. See Lens Language and Visual Style in `references/ltx-2-3-prompting.md`.

### What works well

### Dialogue segmentation (MANDATORY for any speaking character)

A single uninterrupted monologue produces a static talking head. Break dialogue into **2-4 short quoted lines** separated by **acting beats** (physical cue, camera move, or scene reaction):

**Critical: Every spoken line MUST be wrapped in double quotes.** Omitting quotes makes LTX-2.3 produce gibberish — the model interprets quoted text as speech and non-quoted text as narration. This is not optional; it is the mechanism by which the model knows what to speak.

**Flat (avoid):**
> The character speaking: "Oh my god you can see this with me this is what astronomers call a stellar aurora when the nebula's charged particles dance with magnetic fields."

**Segmented (use this):**
> He turns toward the camera, "You are seeing this with me, right?" He steps closer to the dome, palm pressing against the glass. "That is a stellar aurora -- charged particles dancing on magnetic field lines." His eyes widen, breath fogging the visor briefly, voice dropping, "I have never seen colours move like this."

**Multilingual dialogue:** For Hindi/Hinglish content, write the Hindi dialogue in Devanagari or Roman transliteration. Specify the language explicitly in the audio direction:

> The camera holds on her, soft smile, "Hi doston..." (small pause, looks down, then up) "Han... main AI hun." She takes a breath, smile widening. "Lekin mujhse poochio -- mujhe toh sab feel hota hai, yaar!"

> Audio: Hindi-accented teenage girl voice, warm intimate tone, soft Indian lofi instrumental in background.

**Multi-line monologue checklist:** Before running, verify every spoken line is:
1. Wrapped in `"quotes"`
2. Separated from the next line by at least one acting beat (physical cue, camera move, or reaction)
3. 5-15 words per quoted line (keep lines short)

**CRITICAL: Never replace dialogue with meta-description.** When writing audio direction, it is a common mistake to write `"Dialogue in Hindi-accented voice"` or `"Comedic cat voice"` as if the model knows what to say — it doesn't. The model ONLY speaks text that is wrapped in quotes. Every spoken line must be the exact words the character speaks. Accent/language info is supplementary context, NOT a substitute for quotes. **Verification step:** Read through the prompt and count all quoted strings. If there's an audio direction about accent/language but zero (or too few) quoted strings, you have the trap. Fix: include the actual spoken text in quotes, THEN add accent context in the audio line.

### What works well

| Strength | Why |
|----------|-----|
| Cinematic compositions | Wide/medium/close-up with thoughtful lighting, shallow DoF, natural motion |
| Emotive human moments | Single-subject expressions, subtle gestures, facial nuance |
| Atmosphere and setting | Fog, mist, golden-hour light, rain, reflections, ambient textures |
| Clear camera language | "slow dolly in", "handheld tracking", "camera circles around" |
| Stylized aesthetics | Painterly, noir, analog film, fashion editorial |
| Voice | Characters can talk and sing; supports multiple languages and accents |

### What to avoid

| Avoid | Why |
|-------|-----|
| Internal emotional states | Use physical cues, not labels |
| Text and logos | Readable text is not reliable |
| Complex chaotic physics | Jumping, juggling cause artifacts (dancing is OK) |
| Overloaded scenes | Too many characters or actions reduce clarity |
| Conflicting lighting | Mixed light logic confuses scene interpretation |
| Run-on monologue without beats | Produces flat static talking heads |
| Hard cuts in I2V | LTX-2.3 I2V is one continuous shot; cuts break it |

## I2V coherence (mandatory when `--image-start` is set)

LTX-2.3 I2V decodes from the anchor as frame 0 and continues -- it is a single continuous shot, not a multi-cut sequence.

1. **Mirror the anchor.** The opening sentence(s) must describe the exact composition of the anchor: same INT/EXT, same pose, same wardrobe, same light source, same view through windows.
2. **No hard cuts.** Never write `CUT TO`, `JUMP CUT`, `MEANWHILE`, or any discontinuous-shot directive. Reveal new elements via camera moves (dolly, pan, tilt, push-in).
3. **Action first, not setting.** The first sentence describes the *action visible in the anchor*, not static posture or room description. Otherwise LTX-2.3 renders 2-4 seconds of frozen frames at the start.

**Bad -- EXT contradicts INT anchor, mid-clip cut:**
> EXT. SPACECRAFT -- LANDING SEQUENCE. Engine plumes kick up lunar dust... cuts to exterior view of spacecraft settling on lunar surface.

**Good -- INT preserved, reveal via camera move:**
> INT. SPACECRAFT OBSERVATION DECK -- LANDING SEQUENCE. The character stays pressed against the curved window, palm on the glass, face lit by soft instrument-panel light. Through the glass, the Moon fills the view, craters growing larger. The camera slowly pushes in past their shoulder, lunar surface rising in the window, dust catching thruster light through the glass. Their breath fogs the visor, voice dropping, "Ancient companion, hello."

## Audio direction

Describe the acoustic environment, character voice qualities, and ambient sounds. Pull persona-specific voice qualities (accent, tone, verbal quirks) from `SOUL.md` -- this skill does not define them.

Patterns that work:
- `Audio: low station hum, soft plasma crackle, intimate close-mic.`
- `Character-specific accent, warm intimate tone, "You are seeing this with me, right?"`
> The faint hum of chatter and distant drilling fills the air.

**Non-dialogue reels:** When the user explicitly wants no dialogue (e.g., nature/vibe reels, divine scenes), the entire prompt should contain NO quoted text. Instead, focus entirely on camera movement, ambient environment, and audio direction (music, ambient sounds). The dialogue segmentation rules do not apply in these cases. Example: "EXT. JUNGLE RIVERBANK -- LATE AFTERNOON. The character sits peacefully on a moss-covered rock by the river, sunlight filtering through the jungle canopy above... Audio: gentle flowing river sounds, soft jungle birdsong, slow peaceful acoustic guitar instrumental."

## Helper invocation -- split into two steps

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

### Step B: Start background execution (survives agent timeout)

```bash
"$WAN_PYTHON" "$WAN_APP_DIR/wgp.py" \
    --process "$POSTS_DIR/2026-05-02_1/video_generation.json" \
    --output-dir "$POSTS_DIR/2026-05-02_1" \
    --compile --attention sage2 --profile 4 --fp16
```
**CRITICAL:** Run this via `terminal(background=true)` with `notify_on_complete=true`. This starts a separate VM process that survives agent turn timeout.

### Step C: Pre-flight — Check no other wgp.py is running

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
| `gguf` (default) | Q6_K GGUF (16 GB) | 8 | Fastest | Day-to-day iteration, quick previews |
| `distilled-1.1` | Distilled v1.1 int8 (19 GB) | 8 | Fast | Need WanGP auto-HDR/outpaint/union-control LoRAs |

> **Benchmark data (RTX 4090, 720x1280, 20s video):**
> - `gguf` (8 steps): ~3-4 min total, no compilation needed (gguf runtime is C++, already compiled)
> - `distilled-1.1` (8 steps): ~3-4 min gen, ~5-8 min first run (TorchInductor compile), ~3-4 min cached re-run

> **Why gguf is fast:** GGUF runtime is llama.cpp (C++ based), weights are pre-compiled and quantized at build time. No PyTorch compilation needed. Loading = "read weights, map to GPU VRAM, go".

> **Why distilling helps:** Distilled version is a simpler/smaller architecture. Even with PyTorch runtime, it has fewer compute-heavy layers, plus only 8 steps like gguf. The `distilled-1.1` model has WanGP auto-loaded internal LoRAs (HDR, outpaint, union-control) that improve quality without extra steps.

**Usage:**
```bash
# Default (gguf) -- no flag needed:
python3 .../generate_video_config.py --prompt "..." --output-filename foo --output-dir /tmp

# Distilled 1.1:
python3 .../generate_video_config.py --model distilled-1.1 --prompt "..." --output-filename foo --output-dir /tmp
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
- **TorchInductor silent compilation on first run (distilled-1.1 model).** The distilled-1.1 model triggers PyTorch TorchInductor kernel compilation before GPU inference begins. This is CPU-bound with 32 worker processes, produces NO stderr/stdout output for 5-15 minutes, and leaves the GPU idle (only ~400MB memory, 0% compute). **Do not kill the process** — it is working. **Diagnose:** `ps aux | grep compile_worker` — if you see many `torch._inductor.compile_worker` child processes, the parent is compiling kernels. **Mitigation:** Set `TORCHINDUCTOR_FORCE_DISABLE=1` env var to skip compilation (faster start but slower per-step inference). After first run, compiled kernels are cached in `~/.cache/torch_inductor/` so subsequent runs skip this phase entirely.

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

- [`telegram-timeout-fix.md`](references/telegram-timeout-fix.md) — Full diagnosis of the Telegram agent-turn timeout problem with `--run`, evidence from post #6 (PID trees, timelines), and the split workflow rationale.