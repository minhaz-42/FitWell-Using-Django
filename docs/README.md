# NutriAI — Local development notes

This repository can run a local Qwen-compatible model server for offline development. The following steps will get you started.

Prerequisites
- Python 3.10+ and either a `conda` environment or a virtualenv. A `.venv` in the repo is supported.
- Sufficient memory/disk for model weights (models can be multi-GB).

Quick start

1. Activate your environment

```bash
# conda
conda activate nutriai
# or venv
source ".venv/bin/activate"
```

2. Install Python dependencies

```bash
pip install -r requirements.txt
```

3. Configure environment variables

- Copy `.env` and fill values if necessary. Example entries (local-only):

```
QWEN_LOCAL_MODEL_PATH="/absolute/path/to/models/Qwen"
QWEN_LOCAL_PORT=21002
QWEN_DEVICE=cpu
```

Alternatively set them in your shell. The project will load `.env` automatically if `python-dotenv` is installed.

4. Start the local Qwen server

```bash
chmod +x ./start_qwen_server.sh
./start_qwen_server.sh
# or run in background
nohup ./start_qwen_server.sh > local_qwen.log 2>&1 & echo $!
```

The server exposes:
- POST `/v1/chat/completions` (chat endpoint)
- GET `/health` (health & model load status)

5. Verify with curl

```bash
curl -sS http://localhost:21002/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen","messages":[{"role":"user","content":"Hello"}]}' | jq .

curl http://localhost:21002/health | jq .
```

Notes & troubleshooting
- If the server fails with import errors for `transformers` or `torch`, install them in your environment. On macOS you may prefer a CPU-only torch wheel from the official PyTorch index.
- The project will automatically detect nested model directories like `models--Qwen--.../snapshots/<hash>/` and use the first directory that contains `config.json` or `model.safetensors`.
Note: This repository is configured for local-only model usage. Remove remote API keys/URLs to avoid accidentally sending data to external services.

Resetting / reinstalling the local model
- To back up the current `models/Qwen` and optionally download a new model (e.g. for testing), use the helper script:

```bash
chmod +x ./tools/reset_local_model.sh
# Backup only
./tools/reset_local_model.sh --backup-only

# Backup then download a small test model (safe for local dev):
./tools/reset_local_model.sh --model sshleifer/tiny-gpt2 --target ./models/Qwen

# WARNING: Downloading a full Qwen checkpoint can be very large (many GB). If you
# have the original source (Hugging Face repo id or vendor URL), provide that as
# the --model argument. Ensure you have sufficient disk and that the venv has
# `transformers`/`safetensors` installed before downloading.
```

Want help?
- Tell me whether you want me to: (A) add automatic dependency installs, (B) run tests and add CI, or (C) tune the server for low-memory machines.
