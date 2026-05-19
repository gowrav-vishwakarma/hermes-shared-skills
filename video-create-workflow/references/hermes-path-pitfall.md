# Hermes Path Pitfall (`~` / `$HOME` / phantom nesting)

## Problem

Hermes terminal subprocesses set `HOME` to `$PROFILE_HOME` (e.g. `profiles/aiexplorer/home`), **not** `/home/gowrav`.

Anything that expands `~` or `$HOME` in the shell or via Python `Path.expanduser()` uses that profile home.

## What goes wrong

| You write | It becomes |
|-----------|------------|
| `~/.hermes/profiles/aiexplorer/cron/output/...` | `home/.hermes/profiles/aiexplorer/cron/output/...` (**phantom**) |
| `$HOME/.hermes/profiles/aiexplorer/...` | same phantom path |
| `source $PROFILE_HOME/.env` | fails — `.env` is at `$PROFILE_ROOT/.env` |
| `--output-dir $PROFILE_ROOT/cron/output/...` | wrong folder (profile root, not posts) |
| `new_post.py` then `--output-dir $POSTS_DIR/...` | **correct** (`home/posts/...`) |

Phantom paths look like:

```
.../profiles/<name>/home/.hermes/profiles/<name>/...
```

## Rules

1. **Source env once per shell** (absolute path):

   ```bash
   set -a; source /home/gowrav/.hermes/profiles/<name>/.env; set +a
   ```

   Or after env is loaded: `set -a; source $PROFILE_ROOT/.env; set +a`

   Never: `source $PROFILE_HOME/.env`

2. **Never use `~/.hermes/...` or `$HOME/.hermes/...` in terminal commands or `--output-dir`.**

3. **Video/image outputs** — always:

   ```bash
   POST_DIR=$(python3 "$PROFILE_SKILLS/video-create-workflow/scripts/new_post.py" --tag my_slug)
   # use $POST_DIR for --output-dir, anchors, and mp4 paths
   ```

4. **Do not use `cron/output/` for reels or posts.** That directory is for Hermes cron job markdown logs (`cronjob` tool, `deliver=local`). GPU renders belong under `$POSTS_DIR`.

5. **Prefer env vars over tildes:** `$POSTS_DIR`, `$PROFILE_ROOT`, `$CHARACTER_ASSETS_DIR`, paths printed by helper scripts.

Generator scripts reject phantom paths and unsafe `~/.hermes` expansion — if you see `[env] phantom path detected`, fix the path and use `new_post.py` + `$POSTS_DIR`.

## Related

- [`working-acestep/references/hermes-home-pitfall.md`](../../working-acestep/references/hermes-home-pitfall.md) — `$HOME/.local/bin` / `uv` on PATH
- Hermes core: `get_subprocess_home()` in `hermes_constants.py`
