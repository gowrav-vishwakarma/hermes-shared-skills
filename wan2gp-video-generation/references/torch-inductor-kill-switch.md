# Torch Inductor Compile Worker Kill-Switch

**Session: 2026-05-07** — fairy tale chipmunk video generation

## Problem

When using the **distilled** model type (`ltx2_22B_distilled_gguf_q6_k`), Torch's inductor compiler spawns **32 subprocess workers** that each consume ~350MB RAM, totalling **60-80GB RAM** plus heavy swap thrashing. This happens on EVERY `wgp.py --process` invocation.

**Symptoms:**
- System swap usage jumps from <2GB to 6-8GB within seconds
- 32 `torch._inductor.compile_worker` subprocesses appear
- GPU shows 100% utilization initially, but actual computation stalls
- Generation freezes at step 3/8 of the first denoising pass
- Background process wrapper kills jobs that exceed timeout
- Subsequent runs on the thrashed system fail identically

**Duration of thrash:** 5-10 minutes after the process completes, even with workers killed.

## Why the first run works, subsequent runs fail

The first run after boot/clean slate completes in ~3 minutes because system RAM is available. After that, the 60GB+ of swap thrashing takes minutes to recover from. Each new run on a thrashed system gets killed by the background wrapper before it can finish.

## Mitigation: Limit Compile Workers

**Always set these env vars BEFORE each `wgp.py` run:**
```bash
source /home/gowrav/.hermes/profiles/gvs/.env
export TORCHINDUCTOR_COMPILE_THREADS=1
export OMP_NUM_THREADS=1
cd $WAN_APP_DIR
$WAN_PYTHON wgp.py --process "$POSTS_DIR/.../video_generation.json" --output-dir "$POSTS_DIR/.../"
```

`TORCHINDUCTOR_COMPILE_THREADS=1` limits the compiler to a single worker (no 60GB RAM spike).
`OMP_NUM_THREADS=1` prevents OpenMP from spawning additional threads.

## Recovery Procedure (when system is already thrashed)

1. Kill compile workers: `pkill -9 -f "compile_worker"`
2. Kill wgp.py: `pkill -9 -f "wgp.py"`
3. Wait 2-3 minutes for swap to drain: `free -h | grep Swap`
   - Goal: swap used < 2GB before starting next generation
4. Run with compile thread limit as above

## Alternative: Use --model gguf

The `--model gguf` flag uses llama.cpp's C++ runtime and **completely avoids** Torch's CUDA kernel compilation, sidestepping the compile worker issue entirely. Trade-off: may have slightly lower quality than distilled mode.

## Detection Commands

```bash
# Check for compile workers
ps aux | grep "compile_worker" | grep -v grep

# Check swap usage
free -h | grep Swap

# Check GPU activity
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader

# Check if generation is actually progressing vs stuck
ls -lh /path/to/post/
```
