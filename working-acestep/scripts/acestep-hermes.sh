#!/usr/bin/env bash
#
# ACE-Step Hermes Wrapper
#
# Thin wrapper that auto-starts the ACE-Step API server if not running,
# then delegates to the existing acestep.sh script for actual operations.
# Also adds batch stem extraction (extract-all).
#
# Usage:
#   acestep-hermes.sh ensure-server
#   acestep-hermes.sh generate [options]
#   acestep-hermes.sh cover <audio> [options]
#   acestep-hermes.sh random [options]
#   acestep-hermes.sh extract-all <audio_file> [--output-dir DIR]
#   acestep-hermes.sh status <job_id>
#   acestep-hermes.sh health
#   acestep-hermes.sh models
#   acestep-hermes.sh config [options]

set -euo pipefail

# Required env vars (loaded from $PROFILE_ROOT/.env):
#   ACESTEP_DIR         -- ACE-Step install directory
#   ACESTEP_OUTPUT_DIR  -- (optional) override; default $HOME/acestep_output
#   ACESTEP_API_URL     -- (optional) override; default http://127.0.0.1:8001
: "${ACESTEP_DIR:?ACESTEP_DIR must be set in profile .env (run: set -a; source \$PROFILE_ROOT/.env; set +a)}"

ACESTEP_SH="${ACESTEP_DIR}/.claude/skills/acestep/scripts/acestep.sh"
SERVER_LAUNCHER="${ACESTEP_DIR}/start_api_server.sh"
API_URL="${ACESTEP_API_URL:-http://127.0.0.1:8001}"
OUTPUT_DIR="${ACESTEP_OUTPUT_DIR:-${HOME}/acestep_output}"
export OUTPUT_DIR  # Pass to acestep.sh so songs go to same folder
SERVER_LOG="${OUTPUT_DIR}/.server.log"
STARTUP_TIMEOUT=180

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

ALL_TRACKS=(vocals backing_vocals drums bass guitar keyboard percussion strings synth fx brass woodwinds)

SERVER_PID_FILE="${OUTPUT_DIR}/.server.pid"
TEMP_AUDIO_FILES=()

cleanup_temp_audio() {
    for f in "${TEMP_AUDIO_FILES[@]}"; do
        rm -f "$f" 2>/dev/null
    done
}
trap cleanup_temp_audio EXIT

stage_audio_to_tmp() {
    local src="$1"
    if [ ! -f "$src" ]; then
        echo -e "${RED}Error: file not found: $src${NC}" >&2
        return 1
    fi
    local ext="${src##*.}"
    local tmp_file
    tmp_file=$(mktemp "/tmp/acestep_src_XXXXXX.${ext}")
    cp "$src" "$tmp_file"
    TEMP_AUDIO_FILES+=("$tmp_file")
    echo "$tmp_file"
}

check_health() {
    local status
    status=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 "${API_URL}/health" 2>/dev/null) || true
    [ "$status" = "200" ]
}

get_server_pid() {
    local port
    port=$(echo "$API_URL" | grep -oP ':\K[0-9]+$' || echo "8001")
    # Find the main python/uvicorn process listening on the API port
    lsof -ti :"$port" 2>/dev/null | head -1
}

stop_server() {
    if ! check_health; then
        echo -e "${YELLOW}ACE-Step API server is not running.${NC}"
        return 0
    fi

    local pid
    pid=$(get_server_pid)

    if [ -z "$pid" ]; then
        echo -e "${RED}Server appears running but could not find PID on port.${NC}"
        echo "Try manually: lsof -i :8001 or pkill -f acestep-api"
        return 1
    fi

    echo -e "${YELLOW}Stopping ACE-Step API server (PID: $pid)...${NC}"

    # Kill the process tree (server + child workers)
    kill -- -"$(ps -o pgid= -p "$pid" | tr -d ' ')" 2>/dev/null || kill "$pid" 2>/dev/null || true

    # Wait for it to actually stop
    local elapsed=0
    while [ $elapsed -lt 15 ]; do
        if ! check_health; then
            echo -e "${GREEN}Server stopped. GPU memory freed.${NC}"
            return 0
        fi
        sleep 1
        elapsed=$((elapsed + 1))
    done

    # Force kill if graceful didn't work
    echo -e "${YELLOW}Graceful stop timed out, force killing...${NC}"
    kill -9 "$pid" 2>/dev/null || true
    sleep 2

    if ! check_health; then
        echo -e "${GREEN}Server stopped (forced). GPU memory freed.${NC}"
    else
        echo -e "${RED}Failed to stop server. Try: kill -9 $pid${NC}"
        return 1
    fi
}

ensure_server() {
    if check_health; then
        echo -e "${GREEN}ACE-Step API server is running.${NC}"
        return 0
    fi

    echo -e "${YELLOW}ACE-Step API server is not running. Starting...${NC}"
    mkdir -p "$OUTPUT_DIR"

    if [ ! -f "$SERVER_LAUNCHER" ]; then
        echo -e "${RED}Error: Server launcher not found at: $SERVER_LAUNCHER${NC}"
        echo "Please verify your ACE-Step installation at: $ACESTEP_DIR"
        exit 1
    fi

    # Start server in background, piping stdin from /dev/null to avoid interactive prompts
    nohup bash -c "cd '$ACESTEP_DIR' && yes n | bash '$SERVER_LAUNCHER'" > "$SERVER_LOG" 2>&1 &
    local server_pid=$!
    echo "Server PID: $server_pid (log: $SERVER_LOG)"

    echo -n "Waiting for server to be ready"
    local elapsed=0
    while [ $elapsed -lt $STARTUP_TIMEOUT ]; do
        if check_health; then
            echo ""
            echo -e "${GREEN}Server is ready! (took ${elapsed}s)${NC}"
            return 0
        fi
        # Check if the process died
        if ! kill -0 "$server_pid" 2>/dev/null; then
            echo ""
            echo -e "${RED}Server process exited unexpectedly. Check log: $SERVER_LOG${NC}"
            tail -20 "$SERVER_LOG" 2>/dev/null || true
            exit 1
        fi
        echo -n "."
        sleep 3
        elapsed=$((elapsed + 3))
    done

    echo ""
    echo -e "${RED}Timeout: server did not become ready within ${STARTUP_TIMEOUT}s.${NC}"
    echo "Check log: $SERVER_LOG"
    tail -20 "$SERVER_LOG" 2>/dev/null || true
    exit 1
}

ensure_config() {
    local config_file="${ACESTEP_DIR}/.claude/skills/acestep/scripts/config.json"
    if [ ! -f "$config_file" ]; then
        local example="${ACESTEP_DIR}/.claude/skills/acestep/scripts/config.example.json"
        if [ -f "$example" ]; then
            cp "$example" "$config_file"
        else
            cat > "$config_file" <<'EOFCFG'
{
  "api_url": "http://127.0.0.1:8001",
  "api_key": "",
  "api_mode": "native",
  "generation": {
    "thinking": true,
    "use_format": false,
    "use_cot_caption": true,
    "use_cot_language": true,
    "batch_size": 2,
    "audio_format": "wav",
    "vocal_language": "en"
  }
}
EOFCFG
        fi
    fi
}

cmd_extract_all() {
    local src_audio=""
    local out_dir=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            --output-dir) out_dir="$2"; shift 2 ;;
            -*) echo -e "${RED}Unknown option: $1${NC}"; exit 1 ;;
            *) src_audio="$1"; shift ;;
        esac
    done

    if [ -z "$src_audio" ]; then
        echo -e "${RED}Error: audio file path required${NC}"
        echo "Usage: $0 extract-all <audio_file> [--output-dir DIR]"
        exit 1
    fi

    if [ ! -f "$src_audio" ]; then
        echo -e "${RED}Error: file not found: $src_audio${NC}"
        exit 1
    fi

    local basename
    basename=$(basename "$src_audio" | sed 's/\.[^.]*$//')
    [ -z "$out_dir" ] && out_dir="${OUTPUT_DIR}/stems/${basename}"
    mkdir -p "$out_dir"

    local tmp_audio
    tmp_audio=$(stage_audio_to_tmp "$src_audio")

    echo -e "${CYAN}Extracting all 12 stems from: $src_audio${NC}"
    echo -e "Output directory: $out_dir"
    echo ""

    ensure_server
    ensure_config

    local failed=()
    local succeeded=0

    for track in "${ALL_TRACKS[@]}"; do
        echo ""
        echo -e "${CYAN}--- Extracting: $track ---${NC}"

        local job_response
        job_response=$(curl -s -X POST "${API_URL}/release_task" \
            -H "Content-Type: application/json" \
            -d "$(jq -n \
                --arg src "$tmp_audio" \
                --arg track "$track" \
                '{
                    task_type: "extract",
                    src_audio_path: $src,
                    instruction: ("Extract the " + ($track | ascii_upcase) + " track from the audio:"),
                    prompt: "",
                    lyrics: "",
                    thinking: false,
                    batch_size: 1,
                    audio_format: "wav"
                }'
            )")

        local job_id
        job_id=$(echo "$job_response" | jq -r '.data.task_id // .task_id // empty' 2>/dev/null)

        if [ -z "$job_id" ]; then
            echo -e "${RED}Failed to submit extract job for: $track${NC}"
            echo "$job_response"
            failed+=("$track")
            continue
        fi

        echo "Job ID: $job_id"

        # Poll for completion
        local status=0
        local poll_count=0
        local max_polls=120
        while [ "$status" != "1" ] && [ "$status" != "2" ] && [ $poll_count -lt $max_polls ]; do
            sleep 5
            local result_response
            result_response=$(curl -s -X POST "${API_URL}/query_result" \
                -H "Content-Type: application/json" \
                -d "$(jq -n --arg id "$job_id" '{"task_id_list": [$id]}')")
            status=$(echo "$result_response" | jq -r '.data[0].status // 0' 2>/dev/null)
            printf "\r  Processing %s... (%ds)" "$track" "$((poll_count * 5))"
            poll_count=$((poll_count + 1))
        done
        echo ""

        if [ "$status" = "1" ]; then
            # Download the audio
            local result_str
            result_str=$(curl -s -X POST "${API_URL}/query_result" \
                -H "Content-Type: application/json" \
                -d "$(jq -n --arg id "$job_id" '{"task_id_list": [$id]}')")
            local audio_path
            audio_path=$(echo "$result_str" | jq -r '.data[0].result' 2>/dev/null | jq -r '.[0].file // empty' 2>/dev/null)

            if [ -n "$audio_path" ]; then
                local dest_file="${out_dir}/${track}.wav"
                curl -s -o "$dest_file" "${API_URL}${audio_path}"
                if [ -f "$dest_file" ] && [ -s "$dest_file" ]; then
                    echo -e "  ${GREEN}Saved: $dest_file${NC}"
                    succeeded=$((succeeded + 1))
                else
                    echo -e "  ${RED}Download failed for: $track${NC}"
                    failed+=("$track")
                fi
            else
                echo -e "  ${RED}No audio path in result for: $track${NC}"
                failed+=("$track")
            fi
        elif [ "$status" = "2" ]; then
            echo -e "  ${RED}Extract failed for: $track${NC}"
            failed+=("$track")
        else
            echo -e "  ${RED}Timeout waiting for: $track${NC}"
            failed+=("$track")
        fi
    done

    echo ""
    echo "========================================"
    echo -e "${GREEN}Extraction complete: $succeeded/12 stems saved${NC}"
    echo "Output: $out_dir"
    if [ ${#failed[@]} -gt 0 ]; then
        echo -e "${YELLOW}Failed tracks: ${failed[*]}${NC}"
    fi
    echo "========================================"
}

show_help() {
    echo "ACE-Step Hermes Wrapper"
    echo ""
    echo "Auto-starts the ACE-Step API server and delegates to acestep.sh."
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  generate [opts]                  Generate music from text (delegates to acestep.sh)"
    echo "  cover <audio> [opts]             Cover/remix from source audio"
    echo "  random [opts]                    Generate random music"
    echo "  extract-all <audio> [--output-dir DIR]  Extract all 12 stems from audio"
    echo "  ensure-server                    Start API server if not running"
    echo "  stop-server                      Stop API server and free GPU memory"
    echo "  health                           Check API health"
    echo "  models                           List available models"
    echo "  status <job_id>                  Check job status"
    echo "  config [opts]                    Manage configuration"
    echo ""
    echo "Generate options: -c/--caption, -d/--description, -l/--lyrics,"
    echo "  --duration, --bpm, --key-scale, --time-sig, --language,"
    echo "  --batch, --seed, --no-thinking, --no-format,"
    echo "  --src-audio, --task-type, --track, --cover-strength,"
    echo "  --repaint-start, --repaint-end"
    echo ""
    echo "Available tracks for extract/lego:"
    echo "  ${ALL_TRACKS[*]}"
    echo ""
    echo "Output: $OUTPUT_DIR"
}

# --- Main ---

if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

command="$1"
shift

case "$command" in
    ensure-server)
        ensure_server
        ;;
    stop-server|stop)
        stop_server
        ;;
    extract-all)
        cmd_extract_all "$@"
        ;;
    health)
        ensure_config
        bash "$ACESTEP_SH" health
        ;;
    models)
        ensure_server
        ensure_config
        bash "$ACESTEP_SH" models
        ;;
    status)
        ensure_config
        bash "$ACESTEP_SH" status "$@"
        ;;
    config)
        ensure_config
        bash "$ACESTEP_SH" config "$@"
        ;;
    generate)
        ensure_server
        ensure_config
        gen_args=()
        while [[ $# -gt 0 ]]; do
            case $1 in
                --src-audio|--ref-audio)
                    if [ -f "$2" ]; then
                        gen_args+=("$1" "$(stage_audio_to_tmp "$2")")
                    else
                        gen_args+=("$1" "$2")
                    fi
                    shift 2 ;;
                *) gen_args+=("$1"); shift ;;
            esac
        done
        bash "$ACESTEP_SH" generate "${gen_args[@]}"
        ;;
    cover)
        ensure_server
        ensure_config
        cover_args=()
        cover_first_pos=true
        while [[ $# -gt 0 ]]; do
            case $1 in
                --src-audio|--ref-audio)
                    if [ -f "$2" ]; then
                        cover_args+=("$1" "$(stage_audio_to_tmp "$2")")
                    else
                        cover_args+=("$1" "$2")
                    fi
                    shift 2 ;;
                -*)
                    cover_args+=("$1"); shift ;;
                *)
                    if $cover_first_pos && [ -f "$1" ]; then
                        cover_args+=("$(stage_audio_to_tmp "$1")")
                        cover_first_pos=false
                    else
                        cover_args+=("$1")
                    fi
                    shift ;;
            esac
        done
        bash "$ACESTEP_SH" cover "${cover_args[@]}"
        ;;
    random)
        ensure_server
        ensure_config
        bash "$ACESTEP_SH" random "$@"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}Unknown command: $command${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
