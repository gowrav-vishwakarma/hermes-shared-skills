---
name: midi-generator
description: Basic Pitch -- Spotify's lightweight neural network for Automatic Music Transcription (AMT). Converts audio files (.mp3, .ogg, .wav, .flac, .m4a) into MIDI files with pitch bends. Instrument-agnostic, supports polyphonic instruments. Best on one instrument at a time.
category: media
---

# Basic Pitch

## Overview

Basic Pitch is a Python library for **Automatic Music Transcription (AMT)** developed by Spotify's Audio Intelligence Lab. It converts audio to MIDI using a lightweight neural network that is efficient, easy to use, and competes with much larger AMT systems.

- **Research paper**: [ICASSP 2022](https://arxiv.org/abs/2203.09893)
- **Demo**: https://basicpitch.io
- **Repo**: https://github.com/spotify/basic-pitch
- **License**: Apache 2.0 (Copyright 2022 Spotify AB)
- **Best on**: One instrument at a time (mono source ideal)

## Local Setup

Basic pitch is installed in a dedicated uv-managed project at:

```
/home/gowrav/.hermes/shared-skills/basic-pitch/
```

- **Python**: 3.11 (pinned — required for TensorFlow 2.15 compatibility)
- **Runtime**: TensorFlow 2.15 (full model, most accurate)
- **Status**: Already installed and working

**IMPORTANT**: ALL commands MUST be run from this directory using `uv run`. Never activate the venv manually or run `basic-pitch` directly — always use `uv run` with `working_directory` set to `/home/gowrav/.hermes/shared-skills/basic-pitch/`.

### If reinstall is needed

```bash
cd /home/gowrav/.hermes/shared-skills/basic-pitch
uv sync
```

## Usage

**All commands below assume `working_directory: /home/gowrav/.hermes/shared-skills/basic-pitch/`.**

### Command Line

Basic transcription (generates MIDI):

```bash
uv run basic-pitch <output-directory> <input-audio-path>
```

Batch processing:

```bash
uv run basic-pitch <output-directory> <file1.mp3> <file2.ogg> <file3.wav>
```

Optional flags:
- `--sonify-midi` — saves a `.wav` rendering of the MIDI
- `--save-model-outputs` — saves raw model outputs as NPZ file
- `--save-note-events` — saves predicted note events as CSV
- `--model-serialization` — override model type (e.g., `tensorflow`, `coreml`, `tflite`, `onnx`)

Example:

```bash
uv run basic-pitch /output/dir /input/audio/song.mp3 --sonify-midi --save-note-events
```

To see all options:

```bash
uv run basic-pitch --help
```

### Programmatic (Python)

Run Python scripts through `uv run python` from the basic-pitch directory.

**Single prediction:**

```bash
uv run python -c "
from basic_pitch.inference import predict
from basic_pitch import ICASSP_2022_MODEL_PATH

model_output, midi_data, note_events = predict('/path/to/audio.mp3')
"
```

**Loop prediction (reuse model to avoid reload overhead):**

```bash
uv run python -c "
from basic_pitch.inference import predict, Model
from basic_pitch import ICASSP_2022_MODEL_PATH

basic_pitch_model = Model(ICASSP_2022_MODEL_PATH)

for audio_file in ['/path/to/audio1.mp3', '/path/to/audio2.ogg']:
    model_output, midi_data, note_events = predict(audio_file, basic_pitch_model)
"
```

**predict_and_save() — full orchestration:**

```bash
uv run python -c "
from basic_pitch.inference import predict_and_save
from basic_pitch import ICASSP_2022_MODEL_PATH

predict_and_save(
    input_audio_path_list=['/path/to/audio.mp3'],
    output_directory='/output/dir',
    save_midi=True,
    sonify_midi=True,
    save_model_outputs=True,
    save_notes=True,
    model_path=ICASSP_2022_MODEL_PATH,
)
"
```

## Input Specs

- **Supported formats**: `.mp3`, `.ogg`, `.wav`, `.flac`, `.m4a` (any librosa-compatible codec)
- **Channels**: Stereo audio is auto-downmixed to mono internally
- **Sample rate**: Any input rate — auto-resampled to **22050 Hz** before processing
- **Length**: No hard limit (disk space dependent); for very long files, process in windows
- **Best case**: Single instrument / mono source

## Model Runtime Priority

Basic Pitch loads models in this order:
1. TensorFlow (most accurate, recommended if available)
2. CoreML (macOS default)
3. TensorFlowLite (Linux default)
4. ONNX (Windows default)

Override with `--model-serialization tensorflow` on CLI, or use `Model(path)` in Python.

## Output Files

| Flag | Output |
|------|--------|
| (default) | `.mid` — MIDI file with notes + pitch bends |
| `--sonify-midi` | `.wav` — audio rendering of MIDI |
| `--save-model-outputs` | `.npz` — raw model prediction output |
| `--save-note-events` | `.csv` — predicted note events |

## Pitfalls & Tips

1. **Multi-instrument audio**: Basic Pitch works best on a single instrument. For full mixes, results may be messy — consider stem separation first.
2. **Always use `uv run` with `working_directory`**: Never call `basic-pitch` directly or activate the venv. Always use `uv run` with `working_directory` set to `/home/gowrav/.hermes/shared-skills/basic-pitch/`. It will not work from any other path.
3. **Output directory MUST exist first**: The CLI throws `ValueError: 🚨 /output/dir is not a directory` if the output path doesn't already exist as a directory. Always `mkdir -p <output_dir>` before invoking `uv run basic-pitch`.
4. **Python version**: This project is pinned to Python 3.11. Do not change the Python version — TensorFlow 2.15 requires Python <=3.11.
5. **setuptools**: Pinned to <75 because `resampy` depends on `pkg_resources` which was removed in setuptools 82+.
6. **GPU warnings are cosmetic**: CUDA/TensorRT/oneDNN errors on CPU-only machines can be safely ignored.
7. **Disk space**: Long audio files may need significant temporary disk space for processing.
8. **Output naming**: Output MIDI files are named `<input_filename>_basic_pitch.mid` by default.
9. **Model loading is slow**: TensorFlow import can take several seconds on every call. For batch work, use `predict_and_save()` or loop-based `Model()` to avoid reloading the model each time.