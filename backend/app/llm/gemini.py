import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from backend.app.core.config import settings

import asyncio

async def generate_with_gemini(prompt: str) -> str:
    """Call the Gemini API directly, non-blocking."""
    def _sync_call():
        api_key = settings.GEMINI_API_KEY
        if not api_key or api_key == "your_actual_key_here":
            raise ValueError(
                "Valid GEMINI_API_KEY not found. Add your API key to .env."
            )

        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{settings.GEMINI_MODEL}:generateContent?key={api_key}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
        }
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json"
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=90) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Gemini API request failed ({exc.code}): {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"Could not reach the Gemini API: {exc.reason}") from exc

        try:
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"Gemini returned an unexpected response: {data}") from exc

    return await asyncio.to_thread(_sync_call)
