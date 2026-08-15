"""Shared model configuration.

The course runs everything (agent + eval judge) through OpenRouter with an
OpenAI-compatible client. Set one env var and you are done:

    export OPENROUTER_API_KEY=sk-or-...

Optional overrides:

    AGENT_MODEL       (default: openai/gpt-4o-mini)
    JUDGE_MODEL       (default: openai/gpt-4o-mini)
    OPENAI_BASE_URL   (default: https://openrouter.ai/api/v1)
"""

from __future__ import annotations

import os
from pathlib import Path


def _load_dotenv() -> None:
    """Load KEY=value lines from the project's .env (no dependency needed).

    Existing environment variables win over .env values.
    """
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


_load_dotenv()

def api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError(
            "No API key found. Set OPENROUTER_API_KEY (or OPENAI_API_KEY) "
            "in the environment or in .env before running the agent or evals."
        )
    return key


def _is_openrouter() -> bool:
    try:
        return api_key().startswith("sk-or-")
    except RuntimeError:
        return True


# Auto-detect the provider from the key: OpenRouter keys start with sk-or-
# and use vendor-prefixed model ids; a plain OpenAI key goes straight to
# api.openai.com with the bare model id. Env vars override either way.
if _is_openrouter():
    _default_base, _default_model = "https://openrouter.ai/api/v1", "openai/gpt-4o-mini"
else:
    _default_base, _default_model = "https://api.openai.com/v1", "gpt-4o-mini"

BASE_URL = os.environ.get("OPENAI_BASE_URL", _default_base)
AGENT_MODEL = os.environ.get("AGENT_MODEL", _default_model)
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", _default_model)
