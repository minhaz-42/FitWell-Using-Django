import os
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# This client is local-only: it forwards chat requests to a locally-run Qwen-compatible
# server. Remote API keys / URLs were intentionally removed to keep the project
# offline/local-only per repository configuration.

# Local server port and path. The server started by `start_qwen_server.sh` listens
# on port 21002 by default and exposes `/v1/chat/completions`.
LOCAL_QWEN_PORT = os.getenv("QWEN_LOCAL_PORT", os.getenv("QWEN_PORT", "21002"))
LOCAL_QWEN_URL = f"http://localhost:{LOCAL_QWEN_PORT}/v1/chat/completions"
# Timeout (seconds) for HTTP requests to the local Qwen server. Make configurable
# via the environment so long-running model responses can be tolerated.
QWEN_REQUEST_TIMEOUT = float(os.getenv("QWEN_LOCAL_TIMEOUT", os.getenv("QWEN_TIMEOUT", "60")))


def _extract_text_from_response(resp_json: dict) -> str:
    """Extract text from known response shapes (simple best-effort)."""
    # OpenAI-like
    try:
        return resp_json["choices"][0]["message"]["content"].strip()
    except Exception:
        pass

    try:
        return resp_json["choices"][0]["text"].strip()
    except Exception:
        pass

    # Fallback: stringify the JSON
    return str(resp_json)


def chat(messages: List[Dict[str, str]], model: str = "qwen", temperature: float = 0.7, max_tokens: int = 150) -> str:
    """Synchronous chat call to the local Qwen server with retries.

    This client assumes a locally-running Qwen-compatible server is available
    at `LOCAL_QWEN_URL`. If the server is not reachable an error string is returned.
    """
    import requests
    import time

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    headers = {"Content-Type": "application/json"}
    
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            logger.debug(f"Calling Qwen API (attempt {attempt + 1}/{max_retries})...")
            resp = requests.post(LOCAL_QWEN_URL, json=payload, headers=headers, timeout=QWEN_REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            text = _extract_text_from_response(data)
            logger.debug(f"Qwen response received: {text[:100]}...")
            return text
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Connection error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                logger.error(f"Failed to connect to Qwen server at {LOCAL_QWEN_URL} after {max_retries} attempts")
                raise Exception(f"Qwen server not responding at {LOCAL_QWEN_URL}. Make sure it's running with: bash start_qwen_server.sh")
        except requests.exceptions.Timeout as e:
            logger.warning(f"Timeout error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                raise Exception(f"Qwen server timed out. Check if model is loading or use start_qwen_server.sh")
        except Exception as e:
            logger.exception(f"Error calling local Qwen server (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                raise Exception(f"Qwen API error: {str(e)}")


async def async_chat(messages: List[Dict[str, str]], model: str = "qwen", temperature: float = 0.7, max_tokens: int = 150) -> str:
    """Async chat call to the local Qwen server using `httpx`."""
    import httpx

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {"Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=QWEN_REQUEST_TIMEOUT) as client:
            resp = await client.post(LOCAL_QWEN_URL, json=payload, headers=headers, timeout=QWEN_REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            return _extract_text_from_response(data)
    except Exception as e:
        logger.exception("Error calling local Qwen server async: %s", e)
        return f"(Local Qwen error) {str(e)}"
