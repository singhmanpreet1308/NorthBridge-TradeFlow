
"""Minimal client for the Euri chat-completions API (OpenAI-compatible).

Configuration is read from environment variables or Phase 6 .env:
    EURI_API_KEY   - required, never hard-code it
    EURI_BASE_URL  - default https://api.euron.one/api/v1/euri
    EURI_MODEL     - default gpt-4.1-mini
"""

import os
from pathlib import Path

import requests

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass


DEFAULT_BASE_URL = "https://api.euron.one/api/v1/euri"
DEFAULT_MODEL = "gpt-4.1-mini"


def chat_completion(messages, temperature=0.0, max_tokens=900, timeout=60):
    """Send chat messages and return {"status", "content" | "message"}."""

    api_key = os.getenv("EURI_API_KEY")

    if not api_key:
        return {
            "status": "error",
            "message": "EURI_API_KEY is not set (add it to Phase 6 .env).",
        }

    base_url = os.getenv("EURI_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    model = os.getenv("EURI_MODEL", DEFAULT_MODEL)

    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        response.raise_for_status()

        content = response.json()["choices"][0]["message"]["content"]

        return {"status": "success", "content": content, "model": model}

    except requests.Timeout:
        return {"status": "error", "message": "LLM request timed out."}

    except requests.ConnectionError:
        return {"status": "error", "message": "Cannot connect to the LLM API."}

    except requests.HTTPError as exc:
        # Never echo the request (it contains the API key)
        code = exc.response.status_code if exc.response is not None else None
        return {"status": "error", "message": f"LLM API returned HTTP {code}."}

    except (KeyError, IndexError, ValueError):
        return {"status": "error", "message": "Unexpected LLM response format."}
