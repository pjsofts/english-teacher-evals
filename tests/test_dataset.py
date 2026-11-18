"""Checks the course dataset itself. No API key needed."""
import json
from pathlib import Path

CASES = json.loads((Path(__file__).resolve().parents[1] / "dataset" / "test_cases.json").read_text())
FIELDS = {"id", "title", "metric", "lesson", "flaw", "fix_hint", "input", "actual_output", "threshold"}


def test_there_are_50_cases():
    assert len(CASES) == 50


def test_ids_are_unique():
    ids = [c["id"] for c in CASES]
    assert len(ids) == len(set(ids))


def test_every_case_has_all_fields():
    for c in CASES:
        assert FIELDS <= c.keys(), c["id"]


def test_cases_cover_14_metrics():
    assert len({c["metric"] for c in CASES}) == 14


def test_thresholds_are_between_0_and_1():
    for c in CASES:
        assert 0 <= c["threshold"] <= 1, c["id"]
