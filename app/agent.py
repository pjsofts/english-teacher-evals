"""The English-teacher agent: an OpenAI-compatible chat model (via
OpenRouter) with function-calling tools and a manual tool loop.

The agent code here is intentionally boring and correct — all the failures
in the dataset come from prompts.py, tools.py descriptions, and
retrieval.py, which is exactly what the course teaches you to fix.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from openai import OpenAI

from app.config import AGENT_MODEL, BASE_URL, api_key
from app.prompts import SYSTEM_PROMPT
from app.tools import TOOL_IMPLEMENTATIONS, TOOL_SCHEMAS

MAX_TOOL_ROUNDS = 5


@dataclass
class AgentResponse:
    text: str
    tools_called: list[dict] = field(default_factory=list)
    # each entry: {"name": ..., "input_parameters": {...}, "output": ...}


class EnglishTeacherAgent:
    def __init__(self, model: str | None = None, system_prompt: str | None = None):
        self.client = OpenAI(base_url=BASE_URL, api_key=api_key())
        self.model = model or AGENT_MODEL
        self.system_prompt = system_prompt or SYSTEM_PROMPT

    def respond(
        self,
        user_message: str,
        history: list[dict] | None = None,
        use_tools: bool = True,
    ) -> AgentResponse:
        """Answer one user message. `history` is prior [{role, content}] turns."""
        messages = [{"role": "system", "content": self.system_prompt}]
        messages += history or []
        messages.append({"role": "user", "content": user_message})

        tools_called: list[dict] = []
        for _ in range(MAX_TOOL_ROUNDS):
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOL_SCHEMAS if use_tools else None,
            )
            msg = completion.choices[0].message
            if not msg.tool_calls:
                return AgentResponse(text=msg.content or "", tools_called=tools_called)

            messages.append(msg)
            for call in msg.tool_calls:
                name = call.function.name
                try:
                    args = json.loads(call.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                impl = TOOL_IMPLEMENTATIONS.get(name)
                output = impl(**args) if impl else f"error: unknown tool {name}"
                tools_called.append(
                    {"name": name, "input_parameters": args, "output": output}
                )
                messages.append(
                    {"role": "tool", "tool_call_id": call.id, "content": output}
                )

        return AgentResponse(
            text="(agent stopped: too many tool rounds)", tools_called=tools_called
        )

    def chat(self, turns: list[dict]) -> list[dict]:
        """Replay a conversation's user turns, generating assistant turns.

        `turns` is [{"role": "user"|"assistant", "content": ...}] — assistant
        entries in the input are ignored and regenerated. Returns the full
        regenerated conversation. Used by the runner for conversational
        (RoleAdherence) test cases in --live mode.
        """
        history: list[dict] = []
        for turn in turns:
            if turn["role"] != "user":
                continue
            response = self.respond(turn["content"], history=history)
            history.append({"role": "user", "content": turn["content"]})
            history.append({"role": "assistant", "content": response.text})
        return history
