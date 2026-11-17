
import os
import asyncio
from pathlib import Path
from functools import lru_cache

from dotenv import load_dotenv
from google import genai

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")
PROXY_URL = "http://127.0.0.1:10808"

os.environ["HTTP_PROXY"] = PROXY_URL
os.environ["HTTPS_PROXY"] = PROXY_URL

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")


@lru_cache(maxsize=1)
def get_client():
    if not API_KEY:
        raise RuntimeError("GEMINI_API_KEY is missing from .env")

    return genai.Client(api_key=API_KEY)


async def generate_text(prompt: str) -> str:
    if not prompt.strip():
        raise ValueError("Prompt cannot be empty")

    client = get_client()

    for attempt in range(3):
        try:
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=MODEL,
                contents=prompt
            )

            if not response.text:
                raise RuntimeError("Gemini returned an empty response")

            return response.text

        except Exception as e:
            error = str(e)

            if attempt == 2 or not any(
                code in error for code in ("503", "429", "UNAVAILABLE")
            ):
                raise

            await asyncio.sleep(2 ** (attempt + 1))
