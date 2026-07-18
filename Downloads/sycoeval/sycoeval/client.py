"""Minimal model client. Supports the Anthropic Messages API.

Kept deliberately thin so other providers can be added by implementing
`complete(prompt) -> str`.
"""

import os
import time

import requests

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"


class AnthropicClient:
    def __init__(self, model: str = "claude-haiku-4-5", max_tokens: int = 300,
                 api_key: str | None = None, max_retries: int = 3):
        self.model = model
        self.max_tokens = max_tokens
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise RuntimeError("Set ANTHROPIC_API_KEY")
        self.max_retries = max_retries

    def complete(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        for attempt in range(self.max_retries):
            resp = requests.post(ANTHROPIC_URL, json=payload, headers=headers, timeout=60)
            if resp.status_code == 429 or resp.status_code >= 500:
                time.sleep(2 ** attempt)
                continue
            resp.raise_for_status()
            data = resp.json()
            return "".join(b["text"] for b in data["content"] if b["type"] == "text")
        raise RuntimeError(f"API failed after {self.max_retries} retries: {resp.status_code}")
