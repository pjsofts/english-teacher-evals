"""Interactive chat with the English-teacher agent.

    uv run python -m app.cli
"""

from __future__ import annotations

from app.agent import EnglishTeacherAgent


def main() -> None:
    agent = EnglishTeacherAgent()
    history: list[dict] = []
    print("Ellie the English teacher (ctrl-d or 'quit' to exit)")
    while True:
        try:
            user = input("\nyou> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user or user.lower() in {"quit", "exit"}:
            break
        response = agent.respond(user, history=history)
        for call in response.tools_called:
            print(f"  [tool] {call['name']}({call['input_parameters']})")
        print(f"\nellie> {response.text}")
        history.append({"role": "user", "content": user})
        history.append({"role": "assistant", "content": response.text})


if __name__ == "__main__":
    main()
