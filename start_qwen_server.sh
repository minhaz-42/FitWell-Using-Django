#!/bin/bash

# Start Qwen 1.5 0.5B Chat local server on port 21002
cd "/Users/tanvir/Desktop/Piash project/nutriaiproject"

echo "Starting Qwen Local Server..."
echo "Model path: /Users/tanvir/Desktop/Piash project/nutriaiproject/models/Qwen"
echo "Server will run on: http://localhost:21002"

# Set environment variables
export QWEN_LOCAL_MODEL_PATH="/Users/tanvir/Desktop/Piash project/nutriaiproject/models/Qwen"
export QWEN_LOCAL_PORT="21002"
export QWEN_DEVICE="cpu"

# Start the server
python core/local_qwen_server.py
