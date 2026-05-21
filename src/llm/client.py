"""Unified LLM client supporting OpenAI and compatible APIs."""
import os
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

import httpx


@dataclass
class LLMConfig:
    """Configuration for the LLM client."""
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"
    temperature: float = 0.1
    max_tokens: int = 500
    timeout: int = 30


class LLMClient:
    """Unified LLM client for making API calls."""

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        if not self.config.api_key:
            self.config.api_key = os.environ.get(
                "OPENAI_API_KEY",
                os.environ.get("LLM_API_KEY", "sk-placeholder"),
            )
        # Cost per 1K tokens (approximate USD)
        self.cost_input_per_1k = 0.00015  # gpt-4o-mini
        self.cost_output_per_1k = 0.0006

    async def complete(
        self,
        prompt: str,
        system_prompt: str = "You are a helpful assistant.",
        return_json: bool = False,
    ) -> str:
        """Send a completion request to the LLM API."""
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        if return_json:
            payload["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            try:
                resp = await client.post(
                    f"{self.config.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"].strip()
                # Track usage
                usage = data.get("usage", {})
                self._last_usage = {
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                }
                return content
            except httpx.HTTPStatusError as e:
                return f"[Error: API returned {e.response.status_code}]"
            except Exception as e:
                return f"[Error: {str(e)}]"

    def estimate_cost(self, prompt_chars: int) -> Dict[str, float]:
        """Estimate the cost of processing a given prompt length."""
        est_input_tokens = prompt_chars / 4  # rough estimate
        est_output_tokens = 50  # average output
        input_cost = (est_input_tokens / 1000) * self.cost_input_per_1k
        output_cost = (est_output_tokens / 1000) * self.cost_output_per_1k
        return {
            "estimated_input_tokens": est_input_tokens,
            "estimated_output_tokens": est_output_tokens,
            "estimated_cost": round(input_cost + output_cost, 6),
        }

    def get_usage(self) -> Dict[str, int]:
        """Get the last request's token usage."""
        return getattr(self, "_last_usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
