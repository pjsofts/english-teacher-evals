"""Template for a custom scorer.

Copy this file to scorers/<case_id>_scorer.py (e.g. scorers/tc01_scorer.py)
and the runner will automatically evaluate it alongside the built-in metric
for that case.

Your file must define `get_metric()` returning a deepeval metric (or a list
of them). Two common shapes:

1. A GEval scorer — describe your quality bar in plain language and let the
   judge score it (great for tone, completeness, level-appropriateness).

2. A code-based scorer — subclass BaseMetric and compute the score yourself
   (great for deterministic checks: word counts, JSON validity, banned
   phrases, "ends with a question").

Rule of thumb from the course: if a regex can check it, don't pay a judge
to check it.
"""

from deepeval.metrics import BaseMetric, GEval
from deepeval.test_case import LLMTestCase, SingleTurnParams

from harness.judge import get_judge


# --- Shape 1: LLM-judged scorer ------------------------------------------------

def make_geval_scorer() -> GEval:
    return GEval(
        name="My Custom Check",
        criteria=(
            "Describe here, in plain language, what a good output looks like "
            "for this case and what should be penalized."
        ),
        evaluation_params=[SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT],
        threshold=0.7,
        model=get_judge(),
        async_mode=False,
    )


# --- Shape 2: deterministic code-based scorer ---------------------------------

class EndsWithQuestionMetric(BaseMetric):
    """Example: passes only if the reply ends with a question mark."""

    def __init__(self, threshold: float = 1.0):
        self.threshold = threshold

    def measure(self, test_case: LLMTestCase) -> float:
        text = (test_case.actual_output or "").strip()
        self.score = 1.0 if text.endswith("?") else 0.0
        self.success = self.score >= self.threshold
        self.reason = (
            "reply ends with a practice question"
            if self.success
            else "reply does not end with a question"
        )
        return self.score

    async def a_measure(self, test_case: LLMTestCase) -> float:
        return self.measure(test_case)

    def is_successful(self) -> bool:
        return self.success

    @property
    def __name__(self):
        return "EndsWithQuestion"


def get_metric():
    # Return one metric or a list. Swap in whichever shape fits your case.
    return make_geval_scorer()
