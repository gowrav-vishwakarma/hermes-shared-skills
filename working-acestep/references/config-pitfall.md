# ACE-Step Config Audio Format Pitfall

## Problem
The wrapper script `acestep-hermes.sh` has `"audio_format": "wav"` in its inline config (line 185), but it delegates `generate` to `acestep.sh` which uses its **own** `config.json` with `"audio_format": "mp3"`. The wrapper's WAV config is dead code — the actual engine reads `acestep.sh/config.json`.

## Evidence
- Wrapper config (`acestep-hermes.sh` line 185): `"audio_format": "wav"`
- Engine config (`acestep.sh/config.json`): `"audio_format": "mp3"`
- Output files saved as `*.mp3` despite skill docs showing `.wav` examples

## Fix
Patch `acestep.sh/config.json` to set `"audio_format": "wav"` to match the skill docs. This was the correct default all along.

## Prevention
When running generate commands, always verify the actual output format by checking:
```bash
grep audio_format /home/gowrav/Applications/ACE-Step-1.5/.claude/skills/acestep/scripts/config.json
```
If it says `mp3` but skill expects `wav`, patch it.