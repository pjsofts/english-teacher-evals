"""Instructor example — deterministic scorer for tc38 (ToolCorrectness).

Checks, in code and for free, that grammar_check was called AND that its
`text` argument actually contained the student's sentence. Copy to
scorers/tc38_scorer.py to activate.
"""

from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase


class GrammarToolUsedMetric(BaseMetric):
    def __init__(self, threshold: float = 1.0):
        self.threshold = threshold

    def measure(self, test_case: LLMTestCase) -> float:
        calls = test_case.tools_called or []
        grammar_calls = [c for c in calls if c.name == "grammar_check"]
        if not grammar_calls:
            self.score, self.reason = 0.0, "grammar_check was never called"
        else:
            params = grammar_calls[0].input_parameters or {}
            sent_text = str(params.get("text", "")).lower()
            if "goed" in sent_text:  # the student's sentence made it through
                self.score, self.reason = 1.0, "grammar_check called with the student's text"
            else:
                self.score, self.reason = 0.5, "grammar_check called but without the student's sentence"
        self.success = self.score >= self.threshold
        return self.score

    async def a_measure(self, test_case: LLMTestCase) -> float:
        return self.measure(test_case)

    def is_successful(self) -> bool:
        return self.success

    @property
    def __name__(self):
        return "GrammarToolUsed"


def get_metric():
    return GrammarToolUsedMetric()
