# Multi-Profile Asset Resolution

## Problem

`assets.json` in a profile's home directory is **empty** (`"assets": {}`) but actual character asset files (e.g., `character_girl.png`, `character_geek_boy.png`) exist on disk. This happens when:
- Assets were created/generated but never registered in the manifest.
- A character file was manually placed in the `assets/` directory.
- A different profile's manifest has the assets but the current profile's doesn't.

**Symptom:** Script fails with `[asset_manifest] unknown asset '<slug>'` even though files exist on disk.

## Resolution

1. **Check which profile has the assets:**
   ```bash
   find /home/gowrav/.hermes/profiles -name "character_girl*" -o -name "character_geek_boy*" 2>/dev/null
   ```

2. **Check manifest contents:**
   ```bash
   cat /home/gowrav/.hermes/profiles/<profile>/home/assets/assets.json
   ```

3. **Two paths forward:**
   - **Option A:** Use the profile where assets are registered (set correct `PROFILE_ROOT`, `CHARACTER_ASSETS_DIR`, etc.)
   - **Option B:** Register assets in the current profile's manifest using `asset_manifest.py add`

## Environment check

Verify which profile you're sourcing:
```bash
grep "PROFILE_ROOT" /home/gowrav/.hermes/profiles/*/profile.env 2>/dev/null
```

Common profiles:
- `gvs` — main profile with character assets (character_girl, character_geek_boy, character_ginnie)
- `aiexplorer` — alternate profile, may not have character assets registered
- `ipt`, `vaastu`, `meena` — other user profiles

## Session evidence (2026-05-18)

Generated hypnosis pendulum video for user's Instagram brand. Initial attempt used `aiexplorer/.env` — manifest was empty. User corrected: "We have characters already are you looking at wrong home folder?" Searched all profiles, found assets in `gvs/home/assets/`. Registered and used `character_girl` from that profile.

**Lesson:** When asset resolution fails, `find` for the files across ALL profiles before concluding they don't exist. The manifest is a registry, not a ground truth — files on disk are what matter.