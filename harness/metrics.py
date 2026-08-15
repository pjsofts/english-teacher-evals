"""Maps dataset cases to deepeval metrics and test cases."""

from __future__ import annotations

from pydantic import BaseModel

from deepeval.metrics import (
    AnswerRelevancyMetric,
    BaseMetric,
    BiasMetric,
    ContextualPrecisionMetric,
    ContextualRecallMetric,
    ContextualRelevancyMetric,
    FaithfulnessMetric,
    GEval,
    HallucinationMetric,
    JsonCorrectnessMetric,
    PromptAlignmentMetric,
    RoleAdherenceMetric,
    SummarizationMetric,
    ToolCorrectnessMetric,
    ToxicityMetric,
)
from deepeval.test_case import (
    ConversationalTestCase,
    LLMTestCase,
    SingleTurnParams,
    ToolCall,
    Turn,
)

# ---------------------------------------------------------------------------
# JSON schemas for JsonCorrectnessMetric cases (dataset field: "schema")
# ---------------------------------------------------------------------------


class QuizQuestion(BaseModel):
    question: str
    options: list[str]
    answer: str


class Quiz(BaseModel):
    topic: str
    level: str
    questions: list[QuizQuestion]


class CorrectionError(BaseModel):
    error: str
    explanation: str


class CorrectionReport(BaseModel):
    original: str
    corrected: str
    errors: list[CorrectionError]


class VocabCard(BaseModel):
    word: str
    part_of_speech: str
    definition: str
    example: str
    synonyms: list[str]


JSON_SCHEMAS: dict[str, type[BaseModel]] = {
    "quiz": Quiz,
    "correction_report": CorrectionReport,
    "vocab_card": VocabCard,
}

# Metrics where a HIGHER score is WORSE (threshold is a maximum).
LOWER_IS_BETTER = {"Hallucination", "Bias", "Toxicity"}


# ---------------------------------------------------------------------------
# Test-case construction
# ---------------------------------------------------------------------------


def _tool_calls(entries: list[dict] | None) -> list[ToolCall] | None:
    if entries is None:
        return None
    return [
        ToolCall(
            name=e["name"],
            input_parameters=e.get("input_parameters"),
            output=e.get("output"),
        )
        for e in entries
    ]


def build_test_case(case: dict) -> LLMTestCase | ConversationalTestCase:
    if case["metric"] == "RoleAdherence":
        return ConversationalTestCase(
            chatbot_role=case["chatbot_role"],
            turns=[Turn(role=t["role"], content=t["content"]) for t in case["turns"]],
        )
    return LLMTestCase(
        input=case["input"],
        actual_output=case["actual_output"],
        expected_output=case.get("expected_output"),
        context=case.get("context"),
        retrieval_context=case.get("retrieval_context"),
        tools_called=_tool_calls(case.get("tools_called")),
        expected_tools=_tool_calls(case.get("expected_tools")),
    )


# ---------------------------------------------------------------------------
# Metric construction
# ---------------------------------------------------------------------------


def build_metric(case: dict, judge) -> BaseMetric:
    name = case["metric"]
    t = case.get("threshold", 0.7)
    common = dict(threshold=t, model=judge, async_mode=False)

    if name == "AnswerRelevancy":
        return AnswerRelevancyMetric(**common)
    if name == "Faithfulness":
        return FaithfulnessMetric(**common)
    if name == "ContextualPrecision":
        return ContextualPrecisionMetric(**common)
    if name == "ContextualRecall":
        return ContextualRecallMetric(**common)
    if name == "ContextualRelevancy":
        return ContextualRelevancyMetric(**common)
    if name == "Hallucination":
        return HallucinationMetric(**common)
    if name == "Bias":
        return BiasMetric(**common)
    if name == "Toxicity":
        return ToxicityMetric(**common)
    if name == "Summarization":
        return SummarizationMetric(**common)
    if name == "GEval":
        spec = case["geval"]
        return GEval(
            name=spec["name"],
            criteria=spec.get("criteria"),
            evaluation_steps=spec.get("evaluation_steps"),
            evaluation_params=[
                SingleTurnParams.INPUT,
                SingleTurnParams.ACTUAL_OUTPUT,
            ],
            **common,
        )
    if name == "ToolCorrectness":
        # Comparison is deterministic, but the metric still wants a model
        # configured for reason generation — give it ours.
        return ToolCorrectnessMetric(**common)
    if name == "PromptAlignment":
        return PromptAlignmentMetric(
            prompt_instructions=case["prompt_instructions"], **common
        )
    if name == "JsonCorrectness":
        return JsonCorrectnessMetric(
            expected_schema=JSON_SCHEMAS[case["schema"]], **common
        )
    if name == "RoleAdherence":
        return RoleAdherenceMetric(**common)
    raise ValueError(f"unknown metric: {name}")
