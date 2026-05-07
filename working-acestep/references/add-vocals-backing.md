# Adding Vocals to an Existing Backing Track

## The Problem

ACE-Step's **Lego mode** does NOT add vocals (or any instrument) on top of an existing backing track. It generates a completely new song, using the source audio only as a structural reference. Output will have different duration, structure, and instrumentation.

## The Correct Workflow

### Step 1: Generate a Vocal Track
Generate a new track with matching metadata (BPM, key, style, duration) and your lyrics.

```bash
bash "$SKILL_DIR/scripts/acestep-hermes.sh" generate \
  -c "hip-hop rap, aggressive male vocal, hard 808 bass, trap drums" \
  -l "[Verse 1]\n...\n[Chorus]\n..." \
  --bpm 95 --key-scale "A minor" --duration 100 \
  --steps 50 --guidance 7 --batch 2
```

### Step 2: Extract Stems from Vocal Track
```bash
bash "$SKILL_DIR/scripts/acestep-hermes.sh" extract-all /path/to/vocal_track.wav \
  --output-dir /path/to/output/stems_vocal
```

### Step 3: Extract Stems from Original Backing
```bash
bash "$SKILL_DIR/scripts/acestep-hermes.sh" extract-all /path/to/backing.wav \
  --output-dir /path/to/output/stems_original
```

### Step 4: Mix Extracted Vocals Over Original Instrumentals
Use ffmpeg to combine the extracted vocal stem with the original backing:

```bash
cd /path/to/output

# Check durations match
ffprobe -v error -show_entries format=duration -of csv=p=0 stems_vocal/vocals.wav
ffprobe -v error -show_entries format=duration -of csv=p=0 stems_original/vocals.wav  # should be 0 or near 0 for instrumental backing

# Mix: original backing + extracted vocals
ffmpeg -y -i stems_original/vocals.wav -i stems_vocal/vocals.wav \
  -filter_complex "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=0:weights=1 1" \
  -b:a 192k final_track.mp3
```

### Step 5: Verify
Listen to check:
- Vocal level vs backing balance
- No phase issues or artifacts
- Timing alignment (vocals should sync with backing structure)

## Session Example (2026-05-06)
- Original backing: 100s, BPM 95, A minor, hip-hop rap
- Generated vocal track with matching metadata
- Extracted stems from both
- Mixed using ffmpeg amix filter
- Output: 192kbps MP3, ~5MB