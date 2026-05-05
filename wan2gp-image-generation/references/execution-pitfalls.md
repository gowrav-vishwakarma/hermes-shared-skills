## Exit Code 1 — `models/_settings.json` Not Found (CWD Mismatch)

**Symptom:** `FileNotFoundError: [Errno 2] No such file or directory: 'models/_settings.json'` when running `wgp.py` directly. Exit code 1.

**Root cause:** `wgp.py` loads model configuration relative to the **current working directory**, not relative to the script location. If you run from any directory other than the WanGP app directory (`/home/gowrav/pinokio/api/wan.git/app/`), it cannot find `models/_settings.json`.

**Fix:** Always run with the correct working directory:
- **Terminal calls:** Use `workdir: "/home/gowrav/pinokio/api/wan.git/app"` in the terminal invocation.
- **execute_code / Python subprocess:** Pass `cwd="/home/gowrav/pinokio/api/wan.git/app"` in the execution options.
- **Shell commands:** `cd "$WAN_APP_DIR" && ./env/bin/python wgp.py --process ...`

**Session evidence (2026-05-04):** News anchor video generation failed with exit code 1 despite correct paths and env vars. Root cause was missing `cwd` parameter — the command ran from the default working directory instead of the WanGP app directory.

## Exit Code 127 — `$WAN_APP_DIR` Env Var Not Expanded

**Symptom:** `bash: /env/bin/python: No such file or directory` with exit code 127.

**Root cause:** The `$WAN_APP_DIR` environment variable was not set in the shell context where the command ran. The shell expanded it to an empty string, producing the non-existent path `/env/bin/python`.

**Fix:** 
- **Terminal calls:** Use `env_vars={"WAN_APP_DIR": "/home/gowrav/pinokio/api/wan.git/app"}` in the terminal invocation.
- **execute_code / Python subprocess:** Pass env var inline: `["env", "WAN_APP_DIR=/home/gowrav/pinokio/api/wan.git/app", "..."]` or use `env_vars={"WAN_APP_DIR": "..."}`.
- **Shell commands:** Inline the full path instead of relying on env var expansion: `/home/gowrav/pinokio/api/wan.git/app/env/bin/python /home/gowrav/pinokio/api/wan.git/app/wgp.py --process ...`

**Session evidence (2026-05-04):** Background process for news anchor video gen failed with exit code 127. Previous session had set `WAN_APP_DIR` in its shell, but the new session's shell didn't inherit it.
