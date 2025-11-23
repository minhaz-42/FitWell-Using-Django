#!/bin/bash

# Activate environment: prefer the repository venv if present, otherwise fall back to conda
if [ -f "./.venv/bin/activate" ]; then
    # Use the repo virtualenv to avoid accidentally using system/conda Python
    source "./.venv/bin/activate"
elif command -v conda >/dev/null 2>&1; then
    eval "$(conda shell.bash hook)"
    conda activate nutriai || true
fi

# Default paths: prefer repo-relative model directory so the script works
# when the repo folder name contains spaces or differs from the example path.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export QWEN_LOCAL_MODEL_PATH="${QWEN_LOCAL_MODEL_PATH:-$SCRIPT_DIR/models/Qwen}"
export QWEN_LOCAL_PORT=${QWEN_LOCAL_PORT:-21002}
export QWEN_DEVICE="${QWEN_DEVICE:-cpu}"  # or "cuda" if you have GPU
export START_QWEN_LOCAL=1

# Export a local API URL so the client will automatically use it

# Print debug info
echo "Python: $(which python)"
echo "Model path: $QWEN_LOCAL_MODEL_PATH"
echo "Device: $QWEN_DEVICE"

# Check if model directory exists
if [ ! -d "$QWEN_LOCAL_MODEL_PATH" ]; then
    echo "Error: Model directory not found at $QWEN_LOCAL_MODEL_PATH"
    echo "Please update QWEN_LOCAL_MODEL_PATH in this script to point to your Qwen model folder"
    exit 1
fi

# Check for required files. If the top-level folder doesn't contain model files,
# try to find a nested directory that does (common when snapshots are stored
# in a subfolder like models--Qwen--...).
if [ ! -f "$QWEN_LOCAL_MODEL_PATH/config.json" ]; then
    echo "config.json not found in $QWEN_LOCAL_MODEL_PATH — attempting multiple discovery strategies..."
    FOUND_MODEL_DIR=""

    # Strategy 1: common snapshot pattern under immediate subfolders
    for cand in "$QWEN_LOCAL_MODEL_PATH"/*/snapshots/*/config.json "$QWEN_LOCAL_MODEL_PATH"/*/snapshots/*/*/config.json; do
        if [ -f "$cand" ]; then
            FOUND_MODEL_DIR=$(dirname "$cand")
            break
        fi
    done

    # Strategy 2: models--* pattern (some model archives use this naming)
    if [ -z "$FOUND_MODEL_DIR" ]; then
        for md in "$QWEN_LOCAL_MODEL_PATH"/models--*; do
            if [ -d "$md" ]; then
                for cand in "$md"/snapshots/*/config.json "$md"/snapshots/*/*/config.json; do
                    if [ -f "$cand" ]; then
                        FOUND_MODEL_DIR=$(dirname "$cand")
                        break 2
                    fi
                done
            fi
        done
    fi

    # Strategy 3: fallback to recursive find
    if [ -z "$FOUND_MODEL_DIR" ]; then
        FOUND_FILE=$(find "$QWEN_LOCAL_MODEL_PATH" -type f \( -name 'config.json' -o -name 'model.safetensors' -o -name 'pytorch_model.bin' \) -print -quit 2>/dev/null)
        if [ -n "$FOUND_FILE" ]; then
            FOUND_MODEL_DIR=$(dirname "$FOUND_FILE")
        fi
    fi

    if [ -n "$FOUND_MODEL_DIR" ]; then
        echo "Auto-detected model directory: $FOUND_MODEL_DIR"
        export QWEN_LOCAL_MODEL_PATH="$FOUND_MODEL_DIR"
    else
        echo "Error: config.json not found in model directory and no nested model file detected"
        echo "Expected files in $QWEN_LOCAL_MODEL_PATH:"
        ls -la "$QWEN_LOCAL_MODEL_PATH"
        exit 1
    fi
fi

# Start the server
echo "Starting Qwen server..."
echo "Using model path: $QWEN_LOCAL_MODEL_PATH"
echo "Listening on port: $QWEN_LOCAL_PORT"
echo "Local Qwen API will be available at: http://localhost:${QWEN_LOCAL_PORT}/v1/chat/completions"

PYTHON_CMD="$(command -v python || true)"
# Prefer the repo venv python if it exists
if [ -x "./.venv/bin/python" ]; then
    PYTHON_CMD="./.venv/bin/python"
fi

echo "Using python: $PYTHON_CMD"
# Run the server (foreground). If you want background, run this script with nohup or &.
"$PYTHON_CMD" core/local_qwen_server.py
rc=$?
if [ $rc -ne 0 ]; then
    echo "Local Qwen server failed to start (exit code $rc). Check logs above for errors."
    exit $rc
fi
rc=$?
if [ $rc -ne 0 ]; then
    echo "Local Qwen server failed to start (exit code $rc). Check logs above for errors."
    exit $rc
fi