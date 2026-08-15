"""Confident AI / deepeval pytest integration.

Running this file through `deepeval test run` executes all 50 cases as one
test run and — if you are logged in to Confident AI — uploads the results to
the dashboard automatically:

    uv run deepeval test run tests/test_evals.py

Filters (env vars):

    CASES=tc01,tc02  uv run deepeval test run tests/test_evals.py   # subset
    LIVE=1           uv run deepeval test run tests/test_evals.py   # live mode

Recorded mode (default) replays the broken outputs from the dataset — the
run shows up on the dashboard as 50 failures, your day-one baseline. LIVE=1
regenerates every output with your current (fixed) code first.
"""

from __future__ import annotations

import os

import pytest
from deepeval import assert_test

from harness.judge import get_judge
from harness.metrics import build_metric, build_test_case
from harness.runner import load_cases, regenerate

CASES = load_cases()
_selected = os.environ.get("CASES")
if _selected:
    wanted = {i.strip() for i in _selected.split(",")}
    CASES = [c for c in CASES if c["id"] in wanted]

LIVE = os.environ.get("LIVE") == "1"
_judge = get_judge()


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_case(case: dict) -> None:
    if LIVE:
        case = regenerate(case)
    assert_test(
        test_case=build_test_case(case),
        metrics=[build_metric(case, _judge)],
        run_async=False,
    )
