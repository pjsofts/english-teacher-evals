"""Instructor example — GEval scorer for tc01 (AnswerRelevancy).

A stricter, product-specific relevancy bar: the reply must answer the exact
question and contain nothing else. Copy to scorers/tc01_scorer.py to
activate.
"""

from deepeval.metrics import GEval
from deepeval.test_case import SingleTurnParams

from harness.judge import get_judge


def get_metric():
    return GEval(
        name="No-Tangent Answer",
        evaluation_steps=[
            "Verify the output states the past tense of 'go' correctly ('went').",
            "Count the sentences that are NOT needed to answer the question "
            "(trivia, history, travel tips).",
            "Score 1.0 only if every sentence serves the answer; deduct for "
            "each off-topic sentence.",
        ],
        evaluation_params=[SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT],
        threshold=0.8,
        model=get_judge(),
        async_mode=False,
    )
