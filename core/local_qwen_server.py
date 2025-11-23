import os
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# Lightweight local server that wraps a Hugging Face-style model on disk and
# exposes a small REST API compatible with the qwen_client extractor.

MODEL_PATH = os.getenv('QWEN_LOCAL_MODEL_PATH', os.path.join(os.getcwd(), 'models'))
DEVICE = os.getenv('QWEN_DEVICE', 'cuda' if (os.getenv('CUDA_VISIBLE_DEVICES') or False) else 'cpu')
PORT = int(os.getenv('QWEN_LOCAL_PORT', '21002'))

app = FastAPI(title='Local Qwen-compatible server')

# runtime flags
MODEL_RESOLVED_PATH: Optional[str] = None
MODEL_LOADED: bool = False


class ChatRequest(BaseModel):
    model: Optional[str] = None
    messages: List[Dict[str, str]]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 150


class ChatResponse(BaseModel):
    choices: List[Dict[str, Any]]


def _build_prompt_from_messages(messages: List[Dict[str, str]]) -> str:
    # Simple concatenation: system messages first, then user/assistant alternating
    parts = []
    for m in messages:
        role = m.get('role', 'user')
        content = m.get('content', '')
        if role == 'system':
            parts.append(f"[System]: {content}\n")
        elif role == 'user':
            parts.append(f"User: {content}\n")
        else:
            parts.append(f"Assistant: {content}\n")
    parts.append("Assistant:")
    return '\n'.join(parts)


@app.on_event('startup')
def load_model():
    global tokenizer, model, device
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        import torch
    except Exception as e:
        raise RuntimeError("Missing transformers/torch. Install them in your conda env.") from e
    device = 'cuda' if torch.cuda.is_available() and DEVICE.startswith('cuda') else 'cpu'

    # If the configured MODEL_PATH doesn't itself contain model files (e.g. config.json),
    # walk the directory tree (limited depth) to find a nested folder that looks like
    # a model checkpoint. This handles layouts like:
    #   models/Qwen/models--Qwen--.../snapshots/<hash>/{config.json,model.safetensors}
    def _looks_like_model_dir(path: str) -> bool:
        for fname in ("config.json", "model.safetensors", "pytorch_model.bin", "tokenizer.json", "vocab.json"):
            if os.path.exists(os.path.join(path, fname)):
                return True
        return False

    resolved_model_path = MODEL_PATH
    if not _looks_like_model_dir(resolved_model_path):
        # Walk up to 3 levels deep to find a candidate model directory
        found = None
        for root, dirs, files in os.walk(resolved_model_path):
            if _looks_like_model_dir(root):
                found = root
                break
            # limit walk depth: compute relative depth
            rel = os.path.relpath(root, resolved_model_path)
            if rel == ".":
                depth = 0
            else:
                depth = rel.count(os.sep) + 1
            if depth >= 3:
                # don't descend deeper than 3 levels
                dirs[:] = []
        if found:
            resolved_model_path = found
            print(f"Auto-detected nested model directory: {resolved_model_path}")

    print(f"Loading model from {resolved_model_path} on device {device} — this can take a while")
    tokenizer = AutoTokenizer.from_pretrained(resolved_model_path, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(resolved_model_path, trust_remote_code=True)
    model.to(device)
    model.eval()
    # expose resolved path and loaded flag for health checks
    global MODEL_RESOLVED_PATH, MODEL_LOADED
    MODEL_RESOLVED_PATH = resolved_model_path
    MODEL_LOADED = True
    print("Model loaded")


@app.get('/health')
def health():
    """Lightweight health endpoint for orchestration and checks."""
    return {
        "status": "ok",
        "model_loaded": MODEL_LOADED,
        "model_path": MODEL_RESOLVED_PATH,
    }


@app.post('/v1/chat/completions', response_model=ChatResponse)
def chat(req: ChatRequest):
    try:
        prompt = _build_prompt_from_messages(req.messages)
        inputs = tokenizer(prompt, return_tensors='pt').to(device)
        gen = model.generate(**inputs, max_new_tokens=req.max_tokens or 150, do_sample=True, temperature=req.temperature or 0.7)
        out = tokenizer.decode(gen[0], skip_special_tokens=True)

        # Extract assistant portion (very simple heuristic)
        assistant_text = out.split('Assistant:')[-1].strip()

        return ChatResponse(choices=[{"message": {"content": assistant_text}}])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
    print(f"Starting local Qwen-compatible server on 0.0.0.0:{PORT}")
    uvicorn.run(app, host='0.0.0.0', port=PORT, log_level='info')
