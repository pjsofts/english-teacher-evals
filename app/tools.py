"""Tool definitions and implementations for the English-teacher agent.

⚠️  COURSE NOTE — SOME TOOL DESCRIPTIONS ARE DELIBERATELY FLAWED.
The ToolCorrectness test cases (tc38-tc41) fail because of these
descriptions, not because of the tool code. Fixing them means rewriting the
`description` strings so the model picks the right tool with the right
arguments. The Python implementations themselves are fine.
"""

from __future__ import annotations

import json

# ---------------------------------------------------------------------------
# Tool schemas (OpenAI function-calling format)
# ---------------------------------------------------------------------------
# FLAWS:
#   - grammar_check under-triggers: description says to use it only when the
#     literal word "grammar" appears.
#   - translate_word over-triggers: description claims it handles grammar and
#     sentence questions too, stealing grammar_check's job.
#   - generate_quiz is uselessly vague and its parameter descriptions don't
#     say what values are valid.
#   - lookup_example_sentences discourages the model from ever using it.

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "grammar_check",
            "description": (
                "Checks text. Only use this if the student writes the exact "
                "word 'grammar' in their message."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Some text."},
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "translate_word",
            "description": (
                "Use this for any question about words, meanings, grammar, "
                "sentences, or anything language related."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "word": {"type": "string", "description": "A word."},
                    "target_language": {
                        "type": "string",
                        "description": "A language.",
                    },
                },
                "required": ["word", "target_language"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_quiz",
            "description": "Makes questions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Topic."},
                    "level": {"type": "string", "description": "Level."},
                    "num_questions": {
                        "type": "integer",
                        "description": "A number.",
                    },
                },
                "required": ["topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_example_sentences",
            "description": (
                "Searches reference notes for example sentences. Rarely "
                "needed — you usually know better examples yourself."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Query."},
                },
                "required": ["query"],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Implementations (these are fine — simple canned/deterministic logic so the
# course does not depend on external services)
# ---------------------------------------------------------------------------

_COMMON_FIXES = {
    "i goed": "I went",
    "he go": "he goes",
    "she dont": "she doesn't",
    "more better": "better",
    "informations": "information",
    "i am agree": "I agree",
    "peoples": "people",
}


def grammar_check(text: str) -> str:
    findings = []
    lowered = text.lower()
    for wrong, right in _COMMON_FIXES.items():
        if wrong in lowered:
            findings.append({"error": wrong, "correction": right})
    return json.dumps({"text": text, "issues": findings})


def translate_word(word: str, target_language: str) -> str:
    mini_dict = {
        ("cat", "spanish"): "gato",
        ("book", "spanish"): "libro",
        ("run", "french"): "courir",
        ("house", "german"): "Haus",
    }
    result = mini_dict.get((word.lower(), target_language.lower()))
    return json.dumps(
        {"word": word, "target_language": target_language,
         "translation": result or f"[no entry for '{word}' in mini dictionary]"}
    )


def generate_quiz(topic: str, level: str = "B1", num_questions: int = 3) -> str:
    questions = [
        {
            "question": f"({level}) Practice question {i + 1} about {topic}: "
                        f"choose the correct option.",
            "options": ["option A", "option B", "option C", "option D"],
            "answer": "option A",
        }
        for i in range(num_questions)
    ]
    return json.dumps({"topic": topic, "level": level, "questions": questions})


def lookup_example_sentences(query: str) -> str:
    from app.retrieval import retrieve

    return json.dumps({"query": query, "results": retrieve(query, k=3)})


TOOL_IMPLEMENTATIONS = {
    "grammar_check": grammar_check,
    "translate_word": translate_word,
    "generate_quiz": generate_quiz,
    "lookup_example_sentences": lookup_example_sentences,
}
