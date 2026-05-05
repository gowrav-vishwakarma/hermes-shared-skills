# Short-Duration Generation Guide

When generating tracks under ~2 minutes, the LM can struggle to fit complex lyrical structures into the time budget.

## Symptoms of Over-Structured Lyrics
- Generation fails or returns only 1 file instead of batch
- Track is shorter than requested `--duration`
- LM auto-truncates lyrics (check JSON metadata)

## Fix: Compress Structure Tags

**Bad** (too many sections for 100s):
```
[Intro - soft ambient pads and piano
Em(add9) – Cmaj7
Em(add9) – Cmaj7

[Theme A - strings enter, gradual build
Em(add9) – Cmaj7
Am – B7
... (8 sections)
```

**Good** (1 tag per chord or group):
```
[Intro - ambient pads and piano
Em(add9) – Cmaj7

[Theme A - strings build
Em(add9) – Cmaj7 – Am – B7

[Theme B - full orchestra
Em – D/F# – G – Cmaj7 – Am – B7
... (4 sections)
```

## Rules
- **100s max:** 4-5 section tags max, each containing 2-4 chords
- **60-90s:** 3-4 section tags, each with 2-3 chords
- **120s+:** Can use 6-8 sections
- Group multiple chords in one tag with `–` separators
- Use shorter section descriptions (remove verbose parentheticals)
- Check JSON metadata after generation to verify actual duration

## Duration Estimation (per section)
- Intro/Outro: 5-10s each
- Each theme/chapter: 15-25s
- Climax: 20-30s
- Bridge: 15-20s
