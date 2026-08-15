"""The LLM judge used by every deepeval metric.

Runs gpt-4o-mini through OpenRouter (same key as the agent). Override with
JUDGE_MODEL / OPENAI_BASE_URL env vars — see app/config.py.
"""

from __future__ import annotations

from deepeval.models import GPTModel

from app.config import BASE_URL, JUDGE_MODEL, api_key


def get_judge() -> GPTModel:
    return GPTModel(
        model=JUDGE_MODEL,
        api_key=api_key(),
        base_url=BASE_URL,
        temperature=0,
        # OpenRouter model ids are not in deepeval's pricing table; pin the
        # gpt-4o-mini rates so cost tracking doesn't complain.
        cost_per_input_token=0.15 / 1_000_000,
        cost_per_output_token=0.60 / 1_000_000,
    )
