import os
import uvicorn
import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# Lightweight local server for Qwen 1.5 0.5B Chat model

MODEL_PATH = os.getenv('QWEN_LOCAL_MODEL_PATH', os.path.join(os.getcwd(), 'models'))
DEVICE = os.getenv('QWEN_DEVICE', 'cpu')
PORT = int(os.getenv('QWEN_LOCAL_PORT', '21002'))

app = FastAPI(title='Local Qwen Server')

# Global model and tokenizer
tokenizer = None
model = None
device = None

class ChatRequest(BaseModel):
    model: Optional[str] = None
    messages: List[Dict[str, str]]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 500

class ChatResponse(BaseModel):
    choices: List[Dict[str, Any]]


@app.on_event('startup')
def load_model():
    """Load model at startup"""
    global tokenizer, model, device
    
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
    except Exception as e:
        raise RuntimeError("Missing transformers library") from e
    
    # Determine device
    device = 'cuda' if torch.cuda.is_available() and DEVICE.startswith('cuda') else 'cpu'
    print(f"[STARTUP] Using device: {device}")
    
    # Resolve model path - handle nested directories
    resolved_path = MODEL_PATH
    if not os.path.exists(os.path.join(resolved_path, 'config.json')):
        print(f"[STARTUP] config.json not found in {resolved_path}, searching...")
        found = None
        for root, dirs, files in os.walk(resolved_path):
            if 'config.json' in files:
                found = root
                break
            if root.count(os.sep) - resolved_path.count(os.sep) > 3:
                dirs[:] = []
        if found:
            resolved_path = found
            print(f"[STARTUP] Found model at: {resolved_path}")
        else:
            raise RuntimeError(f"Model not found in {MODEL_PATH}")
    
    print(f"[STARTUP] Loading tokenizer from {resolved_path}...")
    tokenizer = AutoTokenizer.from_pretrained(resolved_path, trust_remote_code=True)
    
    print(f"[STARTUP] Loading model from {resolved_path}...")
    model = AutoModelForCausalLM.from_pretrained(
        resolved_path,
        trust_remote_code=True,
    )
    model = model.to(device)
    model.eval()
    print(f"[STARTUP] Model loaded successfully on {device}")


@app.get('/health')
def health():
    return {
        "status": "ok" if model is not None else "loading",
        "device": device,
    }


@app.post('/v1/chat/completions', response_model=ChatResponse)
def chat(req: ChatRequest):
    """Chat endpoint compatible with OpenAI format"""
    try:
        # Build prompt from messages using chat template
        text = tokenizer.apply_chat_template(
            req.messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        print(f"[CHAT] Built prompt:\n{text}\n")
        
        # Tokenize
        inputs = tokenizer(text, return_tensors='pt', truncation=True, max_length=2048)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        input_len = inputs['input_ids'].shape[1]
        print(f"[CHAT] Input shape: {inputs['input_ids'].shape}")
        
        # Generate
        max_tokens = req.max_tokens or 500
        temp = max(0.1, min(req.temperature or 0.7, 2.0))
        
        print(f"[CHAT] Generating with temp={temp}, max_tokens={max_tokens}...")
        with torch.no_grad():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                do_sample=True,
                temperature=temp,
                top_p=0.95,
                top_k=50,
                pad_token_id=tokenizer.eos_token_id,
            )
        
        print(f"[CHAT] Output shape: {output_ids.shape}")
        
        # Decode - only get the new tokens (everything after the input)
        response_text = tokenizer.decode(
            output_ids[0][input_len:],
            skip_special_tokens=True
        ).strip()
        
        print(f"[CHAT] Generated response ({len(response_text)} chars):\n{response_text}\n")
        
        if not response_text or len(response_text) < 2:
            print(f"[CHAT] WARNING: Empty response, using fallback")
            response_text = "I'm ready to help with nutrition and health questions. What would you like to know?"
        
        return ChatResponse(choices=[{
            "message": {
                "content": response_text
            }
        }])
        
    except Exception as e:
        import traceback
        print(f"[ERROR] {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
    print(f"[MAIN] Starting Qwen server on 0.0.0.0:{PORT}")
    uvicorn.run(app, host='0.0.0.0', port=PORT, log_level='info')

