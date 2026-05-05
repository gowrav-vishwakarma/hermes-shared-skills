# Hermes HOME Override Pitfall

## Problem
In the Hermes environment, `HOME` is set to `<profile-root>/home` (e.g., `~/.hermes/profiles/<profile>/home`) instead of the real system home (e.g., `/home/<user>`).

Scripts that do `export PATH="$HOME/.local/bin:$PATH"` (like `start_api_server.sh` and `acestep-hermes.sh`) end up looking for `uv` in the wrong directory, causing:
- "uv package manager not found!" errors
- Server startup failures

## Evidence
```bash
echo $HOME
# ~/.hermes/profiles/<profile>/home  (Hermes profile home, not real home)

ls $HOME/.local/bin/uv 2>/dev/null  # NOT FOUND
ls /home/<user>/.local/bin/uv      # EXISTS (real system home)
```

## Fix
Always export the real system user's bin to PATH before running acestep commands:
```bash
# Replace <user> with the actual system username
export PATH="/home/<user>/.local/bin:$PATH"
```

Then run the wrapper or server launcher.

## Affected Tools
- **acestep**: `acestep-hermes.sh` → `start_api_server.sh` checks `$HOME/.local/bin/uv`
- **pipx / cargo**: Any tool installed via pipx/cargo at `~/.local/bin/` or `~/.cargo/bin/`

## Prevention
Before any skill that calls scripts relying on `$HOME/.local/bin`:
1. `echo $HOME` to verify it points to the real user home
2. If wrong, `export PATH="/home/<user>/.local/bin:$PATH"` first
3. Then proceed with the skill's commands
