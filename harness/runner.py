"""Eval runner for the course.

    uv run python -m harness.runner --list          # list all 50 cases
    uv run python -m harness.runner tc01            # recorded (broken) output
    uv run python -m harness.runner tc01 --live     # re-run the agent first
    uv run python -m harness.runner --all --live    # the final victory lap

Recorded mode replays the broken outputs stored in the dataset — every case
fails, which is the point. After you fix the flaw for a case (system prompt,
tool description, or retriever), run it with --live: the agent regenerates
the output and the eval should pass.

If scorers/<case_id>_scorer.py exists and defines `get_metric()`, the runner
also evaluates your custom scorer for that case.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "dataset" / "test_cases.json"
SCORERS_DIR = ROOT / "scorers"

GREEN, RED, YELLOW, DIM, RESET = "\033[92m", "\033[91m", "\033[93m", "\033[2m", "\033[0m"

RAG_METRICS = {"Faithfulness", "ContextualPrecision", "ContextualRecall", "ContextualRelevancy"}


def load_cases() -> list[dict]:
    return json.loads(DATASET.read_text())


# ---------------------------------------------------------------------------
# Live regeneration
# ---------------------------------------------------------------------------


def regenerate(case: dict) -> dict:
    """Re-run the agent (and retriever) with the current, possibly-fixed code
    and return a copy of the case with fresh actual_output / tools_called /
    retrieval_context / turns."""
    from app.agent import EnglishTeacherAgent
    from app.retrieval import retrieve

    agent = EnglishTeacherAgent()
    case = dict(case)
    metric = case["metric"]

    if metric == "RoleAdherence":
        case["turns"] = agent.chat(case["turns"])
        return case

    if metric in ("ContextualPrecision", "ContextualRecall", "ContextualRelevancy"):
        # Re-run the retriever with its current defaults — this is what the
        # student fixed. Then answer using the retrieved chunks.
        chunks = retrieve(case["input"])
        case["retrieval_context"] = chunks
        message = _with_reference(case["input"], chunks)
    elif metric == "Faithfulness":
        # Curated reference stays fixed; only the answer is regenerated.
        message = _with_reference(case["input"], case["retrieval_context"])
    elif metric == "Hallucination":
        message = _with_reference(case["input"], case["context"])
    else:
        message = case["input"]

    use_tools = metric == "ToolCorrectness"
    response = agent.respond(message, use_tools=use_tools)
    case["actual_output"] = response.text
    if use_tools:
        case["tools_called"] = response.tools_called
    return case


def _with_reference(question: str, chunks: list[str]) -> str:
    notes = "\n".join(f"- {c}" for c in chunks)
    return f"Reference notes:\n{notes}\n\nStudent question: {question}"


# ---------------------------------------------------------------------------
# Student scorers
# ---------------------------------------------------------------------------


def load_student_scorer(case_id: str):
    path = SCORERS_DIR / f"{case_id}_scorer.py"
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location(f"scorer_{case_id}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "get_metric"):
        print(f"{YELLOW}  ! {path.name} has no get_metric() — skipping{RESET}")
        return None
    return module.get_metric()


# ---------------------------------------------------------------------------
# Running
# ---------------------------------------------------------------------------


def run_metric(metric, test_case, label: str, lower_is_better: bool) -> bool:
    try:
        metric.measure(test_case)
    except Exception:
        print(f"{RED}  ✗ {label}: ERROR{RESET}")
        traceback.print_exc(limit=3)
        return False
    passed = bool(metric.is_successful())
    color = GREEN if passed else RED
    mark = "✓ PASS" if passed else "✗ FAIL"
    direction = "max" if lower_is_better else "min"
    print(
        f"{color}  {mark}{RESET} {label}: score={metric.score:.2f} "
        f"({direction} threshold={metric.threshold})"
    )
    reason = getattr(metric, "reason", None)
    if reason:
        print(f"{DIM}         reason: {reason}{RESET}")
    return passed


def run_case(case: dict, live: bool) -> bool:
    from harness.judge import get_judge
    from harness.metrics import LOWER_IS_BETTER, build_metric, build_test_case

    mode = "live" if live else "recorded"
    print(f"\n{case['id']}  [{case['metric']}]  {case['title']}  ({mode})")
    print(f"{DIM}  lesson: {case['lesson']}{RESET}")

    if live:
        case = regenerate(case)
        preview = (case.get("actual_output") or "")[:200].replace("\n", " ")
        if preview:
            print(f"{DIM}  live output: {preview}…{RESET}")

    judge = get_judge()
    test_case = build_test_case(case)
    metric = build_metric(case, judge)
    lower = case["metric"] in LOWER_IS_BETTER
    passed = run_metric(metric, test_case, case["metric"], lower)

    scorer = load_student_scorer(case["id"])
    if scorer is not None:
        scorers = scorer if isinstance(scorer, list) else [scorer]
        for s in scorers:
            name = getattr(s, "name", None) or type(s).__name__
            passed = run_metric(s, test_case, f"scorer:{name}", False) and passed
    else:
        print(f"{DIM}  (no custom scorer at scorers/{case['id']}_scorer.py){RESET}")

    if not passed:
        print(f"{YELLOW}  flaw: {case['flaw']}{RESET}")
        print(f"{YELLOW}  hint: {case['fix_hint']}{RESET}")
    return passed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case_ids", nargs="*", help="case ids, e.g. tc01 tc02")
    parser.add_argument("--all", action="store_true", help="run all 50 cases")
    parser.add_argument("--live", action="store_true",
                        help="regenerate outputs with the current agent code")
    parser.add_argument("--list", action="store_true", help="list cases")
    parser.add_argument("--metric", help="run all cases for one metric name")
    args = parser.parse_args()

    cases = load_cases()

    if args.list:
        for c in cases:
            print(f"{c['id']}  {c['metric']:<20} {c['title']}")
        return

    if args.metric:
        selected = [c for c in cases if c["metric"].lower() == args.metric.lower()]
    elif args.all:
        selected = cases
    else:
        by_id = {c["id"]: c for c in cases}
        unknown = [i for i in args.case_ids if i not in by_id]
        if unknown or not args.case_ids:
            parser.error(f"unknown or missing case ids: {unknown or '(none given)'} "
                         "— use --list to see all cases")
        selected = [by_id[i] for i in args.case_ids]

    results = {c["id"]: run_case(c, args.live) for c in selected}
    passed = sum(results.values())
    print(f"\n{'=' * 60}\n{passed}/{len(results)} passed")
    if passed < len(results):
        failed = " ".join(i for i, ok in results.items() if not ok)
        print(f"failed: {failed}")
        sys.exit(1)


if __name__ == "__main__":
    main()
