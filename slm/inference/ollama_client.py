"""
Ollama Client — local LLM inference via Ollama.

Connects to a locally running Ollama instance to generate responses.
Supports any model available in Ollama (Phi-3, Mistral, Llama 3, etc.).

Prerequisites:
    1. Install Ollama: https://ollama.com/download
    2. Pull a model: ollama pull phi3:mini  (or mistral, llama3, etc.)
    3. Ollama runs automatically on localhost:11434
"""

import json
import os
from typing import Optional

import requests


DEFAULT_MODEL = os.environ.get("SLM_OLLAMA_MODEL", "phi3:mini")
DEFAULT_BASE_URL = os.environ.get("SLM_OLLAMA_URL", "http://localhost:11434")


class OllamaClient:
    """Client for local LLM inference via Ollama."""

    def __init__(
        self,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
    ):
        self.model = model or DEFAULT_MODEL
        self.base_url = base_url or DEFAULT_BASE_URL
        self.temperature = temperature
        self.max_tokens = max_tokens

    def is_available(self) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except requests.ConnectionError:
            return False

    def list_models(self) -> list[str]:
        """List available models in the local Ollama instance."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return [m["name"] for m in data.get("models", [])]
        except (requests.ConnectionError, requests.HTTPError):
            return []

    def chat(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """Send a chat completion request to Ollama.

        Args:
            messages: List of {"role": "system"|"user"|"assistant", "content": "..."}.
            model: Override the default model.
            temperature: Override the default temperature.

        Returns:
            The assistant's response text.
        """
        payload = {
            "model": model or self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature if temperature is not None else self.temperature,
                "num_predict": self.max_tokens,
            },
        }

        resp = requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()

        return data.get("message", {}).get("content", "")

    def generate(self, prompt: str, model: Optional[str] = None) -> str:
        """Simple text generation (non-chat format)."""
        payload = {
            "model": model or self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            },
        }

        resp = requests.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json().get("response", "")

    def pull_model(self, model: Optional[str] = None) -> bool:
        """Pull a model from the Ollama registry."""
        target = model or self.model
        print(f"Pulling model '{target}'... (this may take several minutes)")

        resp = requests.post(
            f"{self.base_url}/api/pull",
            json={"name": target, "stream": False},
            timeout=600,
        )
        return resp.status_code == 200
