---
name: acestep
description: Complete ACE-Step 1.5 music production skill — songwriting guidance (captions, lyrics, BPM/key/duration) plus full execution (generate, remix, repaint, extract stems, lego, complete). Use when users want to write songs, generate music, remix, extract stems, or do any audio work with ACE-Step.
allowed-tools: Read, Write, Bash
---

# ACE-Step Music Generation Skill

Generate music using ACE-Step V1.5 via the local API. The wrapper script auto-starts the API server if it's not running — no manual setup required.

## Environment variables

All paths come from `$PROFILE_ROOT/.env`, which is auto-sourced into agent shells. The wrapper script is a strict consumer of `$ACESTEP_DIR` and exits immediately if it is missing. Recovery: `set -a; source $PROFILE_ROOT/.env; set +a`.

Used by this skill:

- `PROFILE_HOME` -- profile workspace
- `PROFILE_SKILLS` -- `$PROFILE_ROOT/skills`; used in command examples
- `ACESTEP_DIR` -- ACE-Step install directory (contains `start_api_server.sh`)
- `ACESTEP_API_URL` -- (optional) defaults to `http://127.0.0.1:8001`
- `ACESTEP_OUTPUT_DIR` -- (optional) defaults to `$HOME/acestep_output`; for the meena profile this resolves to `$PROFILE_HOME/acestep_output`

## Paths

- **Script**: `$PROFILE_SKILLS/working-acestep/scripts/acestep-hermes.sh` — this is the ONLY script you call. It handles server management, API calls, and everything else internally.
- **Output directory**: `$ACESTEP_OUTPUT_DIR` (i.e. `$PROFILE_HOME/acestep_output/`). When delivering files to the user, always quote the absolute path returned by the script.

## Quick Start

```bash
SKILL_DIR="$PROFILE_SKILLS/working-acestep"

# Generate from description (Simple mode — LM auto-generates caption/lyrics)
bash "$SKILL_DIR/scripts/acestep-hermes.sh" generate -d "a melancholic Hindi love ballad with piano"

# Generate with caption + lyrics (Custom mode — recommended for quality)
bash "$SKILL_DIR/scripts/acestep-hermes.sh" generate -c "pop, female vocal, piano ballad" \
  -l "[Verse 1]
Walking through the rain today
Thinking of the words you'd say

[Chorus]
I still remember you" \
  --duration 120 --bpm 72

# Instrumental
bash "$SKILL_DIR/scripts/acestep-hermes.sh" generate "Jazz saxophone trio, warm, smoky bar"

# Random inspiration
bash "$SKILL_DIR/scripts/acestep-hermes.sh" random
```

## Creative Workflow (Iterative, Not One-Click)

ACE-Step is designed for **iterative human-AI collaboration**, not one-click generation. The core cycle:

1. **Generate** a prototype (Simple mode for exploration, Custom for control)
2. **Cover/Remix** — keep the structure, change style/lyrics/emotion
3. **Repaint** — fix or replace specific time segments
4. **Lego/Complete** — add or remove instrument layers
5. **Repeat** — iterate until satisfied

Use `--batch 2` to generate multiple variations per attempt, then pick the best direction to refine.

**Seed strategy**: Fix `--seed` when tuning parameters (isolates the effect of your change). Leave seed random when exploring creative space.

## Workflow for Vocal Songs

1. Use the **Songwriting Guide** section below for captions, lyrics, BPM/key/duration
2. Write complete, well-structured lyrics with section tags
3. Generate using Custom mode with `-c` (caption) and `-l` (lyrics)

Only use Simple mode (`-d`) or Random for quick exploration or instrumentals.

---

## All Commands

```bash
# SKILL_DIR = "$PROFILE_SKILLS/working-acestep" (same as Quick Start)

# === Generation ===
bash "$SKILL_DIR/scripts/acestep-hermes.sh" generate [options]     # Text-to-music
bash "$SKILL_DIR/scripts/acestep-hermes.sh" cover <audio> [options] # Cover/remix
bash "$SKILL_DIR/scripts/acestep-hermes.sh" random [options]        # Random generation

# === Stem Extraction ===
bash "$SKILL_DIR/scripts/acestep-hermes.sh" extract-all <audio_file> [--output-dir DIR]
# Extracts all 12 stems into DIR/stems/ (default: $ACESTEP_OUTPUT_DIR/stems/)

# === Server Management ===
bash "$SKILL_DIR/scripts/acestep-hermes.sh" ensure-server   # Start server if not running
bash "$SKILL_DIR/scripts/acestep-hermes.sh" stop-server     # Stop server and free GPU memory
bash "$SKILL_DIR/scripts/acestep-hermes.sh" health          # Check API health
bash "$SKILL_DIR/scripts/acestep-hermes.sh" models          # List available models
bash "$SKILL_DIR/scripts/acestep-hermes.sh" status <job_id> # Check job status

# === Config ===
bash "$SKILL_DIR/scripts/acestep-hermes.sh" config          # Show config
bash "$SKILL_DIR/scripts/acestep-hermes.sh" config --set <key> <value>
```

---

## Task Types

### 1. Text-to-Music (generate)

Generate music from text description and/or lyrics.

**Simple mode** — provide a natural language description, LM generates everything:
```bash
bash "$SKILL_DIR/scripts/acestep-hermes.sh" generate -d "upbeat K-pop dance track with catchy hooks"
bash "$SKILL_DIR/scripts/acestep-hermes.sh" generate -d "a soft Bengali love song for a quiet evening"
```

**Custom mode** — provide caption + lyrics directly (higher quality control):
```bash
bash "$SKILL_DIR/scripts/acestep-hermes.sh" generate \
  -c "indie folk, acoustic guitar, male vocal, warm, intimate" \
  -l "[Verse 1]
Under autumn leaves we walked
Hand in hand we never talked

[Chorus]
But silence said it all
Silence said it all" \
  --duration 150 --bpm 95 --key-scale "G Major"
```

**Instrumental**:
```bash
bash "$SKILL_DIR/scripts/acestep-hermes.sh" generate "Lo-fi hip hop, chill beats, piano, vinyl crackle" --duration 180
```

### 2. Cover / Remix

Transform existing audio into a new style while preserving melodic structure. Source audio is quantized into semantic codes (melody, rhythm, chords, orchestration) — you then change the style via caption/lyrics while the structure stays.

```bash
# Basic cover — change style
bash "$SKILL_DIR/scripts/acestep-hermes.sh" cover /path/to/song.mp3 \
  -c "jazz piano arrangement, smooth" \
  -l "[Verse] New lyrics here..."

# Remix — change emotion and lyrics while keeping melody
bash "$SKILL_DIR/scripts/acestep-hermes.sh" cover /path/to/song.mp3 \
  -c "dark synthwave, aggressive, distorted bass" \
  -l "[Verse 1]
New dark lyrics here..." \
  --cover-strength 0.5

# Strength control (0.0-1.0): higher = closer to original structure
bash "$SKILL_DIR/scripts/acestep-hermes.sh" cover /path/to/song.mp3 \
  -c "orchestral symphonic version" \
  --cover-strength 0.7 --duration 120
```

**Cover as creative tool**: Generate a prototype first, then use Cover to iterate — change style, rewrite lyrics, shift emotion — while keeping the melodic skeleton you liked.

### 3. Repaint

Regenerate a specific time segment (3-90 seconds) while keeping the rest intact. The model uses surrounding audio as context.

```bash
# Fix a section (30s to 60s)
bash "$SKILL_DIR/scripts/acestep-hermes.sh" generate \
  --src-audio /path/to/song.mp3 \
  --task-type repaint \
  -c "smooth piano transition" \
  --repaint-start 30 --repaint-end 60
```

Use cases: fix problematic sections, change lyrics in a segment, add transitions.

**Advanced**: Chain multiple repaints to extend a song indefinitely — repaint the ending to continue, each segment referencing the previous context for natural transitions.

### 4. Extract (Stem Separation)

Isolate a specific instrument track from mixed audio. Requires the **base model** (`acestep-v15-base`).

**Single stem:**
```bash
# Extract vocals only
bash "$SKILL_DIR/scripts/acestep-hermes.sh" generate \
  --src-audio /path/to/song.mp3 \
  --task-type extract \
  --track vocals
```

**All 12 stems at once:**
```bash
bash "$SKILL_DIR/scripts/acestep-hermes.sh" extract-all /path/to/song.mp3
# Output: $ACESTEP_OUTPUT_DIR/stems/<filename>/vocals.wav, drums.wav, bass.wav, ...
```

Available tracks: `vocals`, `backing_vocals`, `drums`, `bass`, `guitar`, `keyboard`, `percussion`, `strings`, `synth`, `fx`, `brass`, `woodwinds`

### 5. Lego (Base Model Only)

Add a new instrument track to existing audio.

```bash
bash "$SKILL_DIR/scripts/acestep-hermes.sh" generate \
  --src-audio /path/to/backing.mp3 \
  --task-type lego \
  --track guitar \
  -c "lead guitar melody with bluesy feel"
```

### 6. Complete (Base Model Only)

Auto-complete partial tracks with specified instruments.

```bash
bash "$SKILL_DIR/scripts/acestep-hermes.sh" generate \
  --src-audio /path/to/partial.mp3 \
  --task-type complete \
  --track "drums,bass,guitar" \
  -c "rock style arrangement"
```

---

## Reference Audio (Timbre/Style Transfer)

Control the **acoustic features** (timbre, mixing style, vocal character) of generated music by providing a reference audio file. This acts globally — it sets the sonic palette, not the melody.

```bash
bash "$SKILL_DIR/scripts/acestep-hermes.sh" generate \
  -c "pop ballad, emotional" \
  -l "[Verse] Lyrics here..." \
  --ref-audio /path/to/reference.mp3
```

Reference audio controls timbre texture, mixing style, performance style, and overall atmosphere. It does NOT control melody or structure — use Cover for that.

## Model Selection — Quality Pitfall

**`turbo` model can introduce pitch shifts and artifacts** — especially noticeable on clean/orchestral material. If the user complains about pitch issues, wavering, or "unprofessional" audio, switch to `sft` model: `--steps 50 --guidance 7`. This takes ~6x longer but produces clean, precise audio.

| Model | Steps | Quality | Use When |
|-------|-------|---------|----------|
| turbo (default) | 8 | Fast but can have pitch artifacts | Quick exploration, rough demos |
| sft | 50 | **Clean, precise, no pitch shifts** | User-facing delivery, cinematic/orchestral, anything needing precision |
| base | 50 | Clean | Extract/Lego/Complete tasks |

When in doubt for final delivery: use `--steps 50 --guidance 7` (sft mode).

**VRAM PITFALL — sft model + batch > 1 fails:** The sft model (50 steps) loads ~22.5GB on a 24GB GPU, leaving only ~0.4GB free. **Always use `--batch 1` with sft model.** Attempting `--batch 2` with sft will fail with "Insufficient free VRAM" error. If you need multiple variations with sft, generate them sequentially (separate calls) rather than in batch.

## Model Selection

ACE-Step has two "brains": an **LM** (planner) and a **DiT** (executor). Choose based on your needs:

**LM models** (controls planning quality):

| Model | Speed | Use When |
|-------|-------|----------|
| No LM (`--no-thinking`) | Fastest | You're doing Cover mode, or want raw speed |
| 0.6B | Fast | Low VRAM (<8GB), quick prototyping |
| 1.7B (default) | Medium | **Daily use** — best balance |
| 4B | Slow | Complex tasks, long-tail styles, highest quality planning |

**DiT models** (controls audio quality):

| Model | Steps | Use When |
|-------|-------|----------|
| turbo (default) | 8 | **Daily use** — fast, balanced creativity and semantics |
| turbo-shift1 | 8 | Richer details, weaker semantics |
| turbo-shift3 | 8 | Clearer timbre, may sound "dry" |
| sft | 50 | Best details + semantic parsing, supports CFG tuning |
| base | 50 | Extract/Lego/Complete tasks, fine-tuning base |
| XL variants | same | Higher audio quality, needs 12GB+ VRAM |

**Shift** controls attention allocation during denoising: higher shift = stronger structure/semantics (outline first), lower shift = more details (draw and fix simultaneously).

## Generate Options Reference

| Option | Description |
|--------|-------------|
| `-c`, `--caption` | Music style/genre description |
| `-d`, `--description` | Simple mode: natural language description (LM auto-generates) |
| `-l`, `--lyrics` | Lyrics text with structure tags |
| `--duration` | Duration in seconds (10-600) |
| `--bpm` | Beats per minute (30-300) |
| `--key-scale`, `--key` | Musical key (e.g. "C Major", "Am", "F# minor") |
| `--time-signature`, `--time-sig` | Time signature (e.g. "4/4", "3/4") |
| `--language`, `--vocal-language` | Vocal language code (en, zh, ja, ko, hi, bn, etc.) |
| `--ref-audio` | Reference audio for timbre/style transfer (global, not melody) |
| `--batch` | Number of variations to generate (1-8, default 2 — matches Gradio UI) |
| `--seed` | Random seed for reproducibility |
| `-t`, `--thinking` | Enable LM thinking (default: true) |
| `--no-thinking` | Disable LM thinking (faster) |
| `--no-format` | Disable LM format enhancement |
| `--src-audio` | Source audio file path (for cover/repaint/extract/lego/complete) |
| `--task-type` | Task type: text2music, cover, repaint, extract, lego, complete |
| `--track` | Track name for extract/lego (e.g. "vocals", "drums") |
| `--cover-strength` | Cover strength 0.0-1.0 (higher = closer to source) |
| `--repaint-start` | Repainting start time in seconds |
| `--repaint-end` | Repainting end time in seconds |
| `--steps` | Inference steps (default 8 for turbo, 50 for sft/base) |
| `--shift` | Timestep shift (higher = stronger semantics, lower = more details) |
| `--infer-method` | `ode` (deterministic, default) or `sde` (adds randomness) |
| `--guidance` | CFG guidance scale (sft/base models only) |
| `--no-wait` | Submit job and return immediately |

## Output

Results are saved to `$ACESTEP_OUTPUT_DIR/`:
```
$ACESTEP_OUTPUT_DIR/
├── <job_id>.json         # Full result metadata
├── <job_id>_1.wav        # Audio file (first variation)
├── <job_id>_2.wav        # Audio file (second variation, if batch > 1)
└── stems/                # Stem extraction output
    └── <filename>/
        ├── vocals.wav
        ├── drums.wav
        ├── bass.wav
        └── ...
```

The JSON result contains the actual caption, lyrics, BPM, key, duration, seed values, and model info used for generation. When LM enhancement is enabled, the final synthesized content may differ from your input — check the JSON for actual values.

## Troubleshooting

### Terminal shows "command not found" for brackets/exclamation marks
When lyrics contain `[`, `]`, `!`, or `—`, bash may interpret them and print confusing error lines like `[Pre-Chorus]: command not found` or `Command 'Main' not found`. These are DISPLAY ERRORS from bash parsing the lyrics in the terminal — **the generation itself still succeeds**. Do not be alarmed. If you encounter these, check the output files to confirm success.

### Pitch shifts / audio artifacts
The `turbo` model (8 steps) can produce noticeable pitch shifts or wavering in generated audio. If the output has pitch drift:
- Use the **sft model** instead: `--steps 50 --guidance 7.0`
- Or use the **base model**: `--steps 50`
- Both are slower but produce clean, precise audio with no pitch artifacts.

### Exit code 5 / `uv` not found
Hermes sets `$HOME` to the profile home, so `uv` may not be on PATH. Fix by prepending the real path:
```bash
# System user's real home bin (where uv is installed), not profile-relative
# Find the real home: getent passwd $(whoami) | cut -d: -f6
export PATH="$(getent passwd $(whoami) | cut -d: -f6)/.local/bin:$PATH"
bash "$SKILL_DIR/scripts/acestep-hermes.sh" generate ...
```

### `$PROFILE_SKILLS` expands to wrong path from Python/code
Hermes sets `$HOME` to the profile home, so shell expansion of `~` or `$PROFILE_SKILLS` can produce **double-nested** paths like `/home/user/.hermes/profiles/vaastu/home/.hermes/shared-skills/...` instead of the real path. This happens when running commands from Python subprocess.

**Fix: use the hard-coded absolute path and run from a neutral directory:**
```bash
# WRONG — may resolve to /home/user/.hermes/profiles/vaastu/home/.hermes/...
bash "$PROFILE_SKILLS/working-acestep/scripts/acestep-hermes.sh" generate ...

# CORRECT — always hard-code absolute path, cd to /tmp first
cd /tmp
bash /home/gowrav/.hermes/shared-skills/working-acestep/scripts/acestep-hermes.sh generate ...
```
If `$ACESTEP_DIR` is not set in your `.env`, this path is your fallback:
`/home/gowrav/.hermes/shared-skills/working-acestep/scripts/acestep-hermes.sh`

### Debugging API errors
If the wrapper gives unclear errors, call the REST API directly for transparent output:
```bash
curl -s -X POST http://127.0.0.1:8001/release_task \
  -H "Content-Type: application/json" \
  -d '{"task_type": "text2music", "prompt": "your description", "thinking": true, "batch_size": 2, "audio_format": "mp3"}'
```

### VRAM pre-flight check fails with batch > 1 and long duration
The API pre-checks VRAM availability before starting. If the server is sharing GPU memory with other tasks, batch 2 + long duration (120s+) with sft model can fail:
```
VRAM pre-flight failed: Insufficient free VRAM: need ~1.7 GB, only 0.4 GB available.
```
**Fix:** Always stop the server (`stop-server`) before regenerating when batch 2 fails, then retry with batch 1. The sft model at 50 steps for 120s needs ~1.7GB free — stop competing processes to free VRAM.
### First generation slow
Models are lazy-loaded on first request. First generation takes longer (model download + init). Subsequent calls are fast.

### Caption rewriting is unavoidable
**The ACE-Step API server has a built-in text conditioning layer that rewrites every caption** before it reaches the DiT model. This happens regardless of `--no-format`, `--no-thinking`, or any other flag. The server's conditioning pipeline paraphrases natural-language captions into structured descriptions — you cannot pass a verbatim caption through to the model. This is an API-level behavior, not a wrapper bug.

**Implications:**
- Your exact prompt text will NOT appear in the generation — the server rewrites it
- Always write captions as **comma-separated style tags** (genre, instruments, mood, tempo, key) rather than narrative prose. This format maps better to what the model actually receives anyway
- Don't waste time trying to force exact prompt preservation — it won't work

### `--no-format` optimization
**`--no-format` disables the LM's format enhancement phase**, skipping the slow caption paraphrasing step before GPU work begins. This makes caption-based generation significantly faster than Simple mode (`-d`) since it avoids the LM inference entirely. Use `--no-format` with `-c` for fast generation with style control. Note: the server's conditioning layer still rewrites the caption at the API level — `--no-format` only speeds up the local wrapper.

## Notes

- **Model requirements**: Extract, Lego, and Complete modes require the **base model** (`acestep-v15-base`). Generate, Cover, and Repaint work with the default **turbo model**. If you want ALL features from one server, configure it to load the base model — it handles everything (just uses 50 steps instead of 8, so slower). Set `--steps 50` and `--guidance 7.0` when using base/sft models.
- **First run**: The API server auto-starts on first use. Initial startup takes ~30-60 seconds while models load. Subsequent calls are instant.
- **Stop server when done**: The server holds GPU memory as long as it runs. Always run `stop-server` when finished to free VRAM for other tasks.
- **Thinking mode**: Enabled by default for better quality. Use `--no-thinking` for faster generation when quality planning isn't needed (e.g., simple background music).
- **Duration**: For songs with lyrics, let the LM auto-detect duration (omit `--duration`). For instrumentals, specify explicitly.
- **Duration is NOT enforced**: The API often generates longer output than the `--duration` parameter specifies (e.g., requesting 20s produced 107s). **Always trim the output audio** with `ffmpeg -i input.wav -t D -c:a aac output.mp3` after generation. Check the JSON metadata (`$ACESTEP_OUTPUT_DIR/<job_id>.json`) for the actual duration.
- **Lyrics input**: Always pass COMPLETE lyrics. However, see pitfall below about truncation.
- **Lyrics truncation**: When lyrics are very long relative to `--duration`, the LM may auto-truncate them, producing a shorter song than requested. Check the JSON metadata after generation to verify actual duration. If truncation occurs, reduce lyric length or increase `--duration`.
- **Batch exploration**: Use `--batch 4` (or 2-8) to generate multiple variations at once. Pick the best direction, then iterate with Cover/Repaint. This is far more effective than single-shot generation.
- **Reference audio**: Use `--ref-audio` to transfer the sonic palette (timbre, mixing, atmosphere) from an existing track without affecting melody/structure.

## Troubleshooting

### Skill name mismatch (skills_list vs skill_view)
- **Problem**: `skills_list` shows the skill as `acestep`, but `skill_view(name='acestep')` returns "Skill not found". The actual skill directory is `working-acestep`.
- **Fix**: Always use `skill_view(name='working-acestep')` to load the skill. Do NOT use `skill_view(name='acestep')` — it will fail.
- **Why**: This is a manifest/directory naming mismatch. The skill is registered as "acestep" in the manifest but lives in the `working-acestep` directory, which is what `skill_view` resolves against.

# Songwriting Guide

Professional music creation knowledge for writing captions, lyrics, and choosing parameters.

## Caption: The Most Important Input

**Caption is the most important factor affecting generated music.**

Supports multiple formats: simple style words, comma-separated tags, complex natural language descriptions.

### Common Dimensions

| Dimension | Examples |
|-----------|----------|
| **Style/Genre** | pop, rock, jazz, electronic, hip-hop, R&B, folk, classical, lo-fi, synthwave |
| **Emotion/Atmosphere** | melancholic, uplifting, energetic, dreamy, dark, nostalgic, euphoric, intimate |
| **Instruments** | acoustic guitar, piano, synth pads, 808 drums, strings, brass, electric bass |
| **Timbre Texture** | warm, bright, crisp, muddy, airy, punchy, lush, raw, polished |
| **Era Reference** | 80s synth-pop, 90s grunge, 2010s EDM, vintage soul, modern trap |
| **Production Style** | lo-fi, high-fidelity, live recording, studio-polished, bedroom pop |
| **Vocal Characteristics** | female vocal, male vocal, breathy, powerful, falsetto, raspy, choir |
| **Speed/Rhythm** | slow tempo, mid-tempo, fast-paced, groovy, driving, laid-back |
| **Structure Hints** | building intro, catchy chorus, dramatic bridge, fade-out ending |

### Caption Writing Principles

1. **Specific beats vague** — "sad piano ballad with female breathy vocal" > "a sad song"
2. **Combine multiple dimensions** — style+emotion+instruments+timbre anchors direction precisely
3. **Use references well** — "in the style of 80s synthwave" conveys complex aesthetic quickly
4. **Texture words are useful** — warm, crisp, airy, punchy influence mixing and timbre
5. **Don't pursue perfection** — Caption is a starting point, iterate based on results
6. **Granularity determines freedom** — Less detail = more model creativity; more detail = more control
7. **Avoid conflicting words** — "classical strings" + "hardcore metal" degrades output
   - **Fix: Repetition reinforcement** — Repeat the elements you want more
   - **Fix: Conflict to evolution** — "Start with soft strings, middle becomes metal rock, end turns to hip-hop"
8. **Don't put BPM/key/tempo in Caption** — Use dedicated parameters instead

## Lyrics: The Temporal Script

Lyrics controls how music unfolds over time. It carries:
- Lyric text itself
- **Structure tags** ([Verse], [Chorus], [Bridge]...)
- **Vocal style hints** ([raspy vocal], [whispered]...)
- **Instrumental sections** ([guitar solo], [drum break]...)
- **Energy changes** ([building energy], [explosive drop]...)

### Structure Tags

| Category | Tag | Description |
|----------|-----|-------------|
| **Basic Structure** | `[Intro]` | Opening, establish atmosphere |
| | `[Verse]` / `[Verse 1]` | Verse, narrative progression |
| | `[Pre-Chorus]` | Pre-chorus, build energy |
| | `[Chorus]` | Chorus, emotional climax |
| | `[Bridge]` | Bridge, transition or elevation |
| | `[Outro]` | Ending, conclusion |
| **Dynamic Sections** | `[Build]` | Energy gradually rising |
| | `[Drop]` | Electronic music energy release |
| | `[Breakdown]` | Reduced instrumentation, space |
| **Instrumental** | `[Instrumental]` | Pure instrumental, no vocals |
| | `[Guitar Solo]` | Guitar solo |
| | `[Piano Interlude]` | Piano interlude |
| **Special** | `[Fade Out]` | Fade out ending |
| | `[Silence]` | Silence |

### Combining Tags

Use `-` for finer control, but keep it concise:

```
[Chorus - anthemic]        ← good
[Chorus - anthemic - stacked harmonies - high energy - powerful - epic]  ← too much
```

Put complex style descriptions in Caption, not in tags.

### Caption-Lyrics Consistency

**Models are not good at resolving conflicts.** Think of Caption as "overall setting" and Lyrics as "shot script" — they must tell the same story.

Bad: Caption says "violin solo, classical, intimate chamber" but Lyrics has `[Guitar Solo - electric - distorted]`
Good: Caption says "violin solo, classical, intimate chamber" and Lyrics has `[Violin Solo - expressive]`

Checklist:
- Instruments in Caption <-> Instrumental section tags in Lyrics
- Emotion in Caption <-> Energy tags in Lyrics
- Vocal description in Caption <-> Vocal control tags in Lyrics

Also avoid conflicts between Caption and metadata: don't write "slow ballad" in Caption while setting `--bpm 160`.

### Vocal Control Tags

| Tag | Effect |
|-----|--------|
| `[raspy vocal]` | Raspy, textured vocals |
| `[whispered]` | Whispered |
| `[falsetto]` | Falsetto |
| `[powerful belting]` | Powerful, high-pitched singing |
| `[spoken word]` | Rap/recitation |
| `[harmonies]` | Layered harmonies |
| `[call and response]` | Call and response |
| `[ad-lib]` | Improvised embellishments |

### Energy and Emotion Tags

| Tag | Effect |
|-----|--------|
| `[high energy]` | High energy, passionate |
| `[low energy]` | Low energy, restrained |
| `[building energy]` | Increasing energy |
| `[explosive]` | Explosive energy |
| `[melancholic]` | Melancholic |
| `[euphoric]` | Euphoric |
| `[dreamy]` | Dreamy |
| `[aggressive]` | Aggressive |

### Lyric Writing Tips

1. **6-10 syllables per line** — Model aligns syllables to beats; keep similar counts for lines in same position
2. **Uppercase = stronger intensity** — `WE ARE THE CHAMPIONS!` (shouting) vs `walking through the streets` (normal)
3. **Parentheses = background vocals** — `We rise together (together)`
4. **Extend vowels** — `Feeeling so aliiive` (use cautiously, effects unstable)
5. **Clear section separation** — Blank lines between sections

### Avoiding "AI-flavored" Lyrics

| Red Flag | Description |
|----------|-------------|
| **Adjective stacking** | "neon skies, electric hearts, endless dreams" — vague imagery filler |
| **Rhyme chaos** | Inconsistent patterns or forced rhymes breaking meaning |
| **Blurred boundaries** | Lyric content crosses structure tags |
| **No breathing room** | Lines too long to sing in one breath |
| **Mixed metaphors** | Water -> fire -> flying — listeners can't anchor |

**Metaphor discipline**: One core metaphor per song, explore its multiple aspects. E.g., choosing "water" — love flows around obstacles like water, can be gentle rain or flood, reflects the other's image, can't be grasped but exists.

### Writing Instrumental Music

For pure instrumental music (no vocals), use `[Instrumental]` in lyrics:

```
[Instrumental]
```

Or use structure tags to describe instrumental development:

```
[Intro - ambient]

[Main Theme - piano]

[Climax - powerful]

[Outro - fade out]
```

## Music Metadata

**Most of the time, let LM auto-infer.** Only set manually when you have clear requirements.

| Parameter | Range | Description |
|-----------|-------|-------------|
| `--bpm` | 30-300 | Slow 60-80, mid 90-120, fast 130-180 |
| `--key-scale` | Key | e.g. `C Major`, `Am`. Common keys (C, G, D, Am, Em) most stable |
| `--time-sig` | Time sig | `4/4` (most common), `3/4` (waltz), `6/8` (swing) |
| `--language` | Language | Usually auto-detected from lyrics |
| `--duration` | Seconds | See duration guide below |

### When to Set Manually

| Scenario | Set |
|----------|-----|
| Daily generation | Let LM auto-infer |
| Clear tempo requirement | `--bpm` |
| Specific style (waltz) | `--time-sig 3/4` |
| Match other material | `--bpm` + `--duration` |
| Specific key color | `--key-scale` |

## Duration Calculation

### Estimation Method

- **Intro/Outro**: 5-10 seconds each
- **Instrumental sections**: 5-15 seconds each
- **Typical structures**:
  - 2 verses + 2 choruses: 120-150s minimum
  - 2 verses + 2 choruses + bridge: 180-240s minimum
  - Full song with intro/outro: 210-270s (3.5-4.5 min)

### BPM and Duration Relationship

- **Slower BPM (60-80)**: Need MORE duration for same lyrics
- **Medium BPM (100-130)**: Standard duration
- **Faster BPM (150-180)**: Can fit more lyrics, but still need breathing room

**Rule of thumb**: When in doubt, estimate longer. A song too short feels rushed.

---

## Output Delivery — WAV + MP3 Pattern

**ACE-Step outputs WAV files (~30MB each). User wants WAV preserved AND an MP3 delivery copy.**

After generation completes, run this for every output file:

```bash
cd "$ACESTEP_OUTPUT_DIR"
JOB_ID="<job_id>"
ffmpeg -i "${JOB_ID}_1.wav" -b:a 320k -map_metadata 0 -y "${JOB_ID}_1.mp3"
ffmpeg -i "${JOB_ID}_2.wav" -b:a 320k -map_metadata 0 -y "${JOB_ID}_2.mp3"
```

Then deliver the `.mp3` files (typically ~6MB each) as media attachments to the user. **Never delete the WAV originals.** Keep both formats:
- WAV: high-quality archive (never delete)
- MP3: delivery-friendly copy for sharing

**Always send MP3s, never WAVs.** The user prefers ~6MB MP3 files over ~30MB WAV for delivery.

### Telegram Audio Delivery — OGG Voice Notes

MP3s at 320kbps can be ~8MB and Telegram struggles to display them inline. For **audio delivery over Telegram**, convert to OGG voice notes instead:

```bash
cd "$ACESTEP_OUTPUT_DIR"
JOB_ID="<job_id>"
for i in 1 2; do
  ffmpeg -y -i "${JOB_ID}_${i}.mp3" -acodec libopus -b:a 48k -ac 1 "${JOB_ID}_${i}.ogg"
done
```

Result: ~700KB OGG files that play natively as Telegram voice notes. Deliver `.ogg` files for Telegram audio — NOT `.mp3`.
