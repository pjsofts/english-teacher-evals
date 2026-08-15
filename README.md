# Fix the Teacher — an AI-evals course with deepeval

A hands-on course project: an English-teacher agent ("Ellie") ships with a
**deliberately broken system prompt, broken tool descriptions, and a buggy
retriever**. A dataset of **50 test cases** — every one failing — covers **14
deepeval metrics**. You work through them one by one: read the failure,
understand the metric, fix the flaw, write your own scorer, and re-run until
it passes.

## Setup

```bash
uv sync
export OPENROUTER_API_KEY=sk-or-...   # used by both the agent and the eval judge
```

Everything runs through OpenRouter with `openai/gpt-4o-mini` (agent and
judge). Optional overrides: `AGENT_MODEL`, `JUDGE_MODEL`, `OPENAI_BASE_URL`.

Sanity check:

```bash
uv run python -m app.cli                    # chat with (broken) Ellie
uv run python -m harness.runner --list      # see all 50 cases
uv run python -m harness.runner tc01        # watch a case fail
```

## Project layout

```
app/
  prompts.py     ← the broken system prompt   (YOU FIX THIS)
  tools.py       ← broken tool descriptions   (YOU FIX THIS)
  retrieval.py   ← buggy toy retriever        (YOU FIX THIS)
  agent.py       ← the agent loop (correct — leave it alone)
  cli.py         ← chat REPL
dataset/
  test_cases.json  ← 50 failing cases, with recorded broken outputs
harness/
  runner.py      ← the eval runner
  metrics.py     ← case → deepeval metric mapping
  judge.py       ← the LLM judge (gpt-4o-mini via OpenRouter)
scorers/
  _template.py   ← copy to scorers/tcXX_scorer.py to add your own scorer
solutions/       ← instructor key (no peeking)
```

## The loop (repeat 50 times)

For each case `tcXX`:

1. **See it fail.** `uv run python -m harness.runner tcXX`
   Recorded mode replays the broken output stored in the dataset — read the
   score, the judge's reason, and the lesson line.
2. **Understand the metric.** What is it measuring? What inputs does it
   need (`retrieval_context`? `expected_tools`? `prompt_instructions`?)
   Which direction is better? (For Hallucination / Bias / Toxicity, *lower*
   is better and the threshold is a maximum.)
3. **Find the flaw.** Every case is caused by one bad instruction in
   `app/prompts.py`, one bad description in `app/tools.py`, or one bug in
   `app/retrieval.py`. The runner prints a hint after a failure.
4. **Write a scorer.** Copy `scorers/_template.py` to
   `scorers/tcXX_scorer.py` and encode *your own* quality bar for this case
   — either a `GEval` rubric or a deterministic code check. The runner
   picks it up automatically. Rule of thumb: if a regex can check it,
   don't pay a judge to check it.
5. **Fix and verify live.** Make the smallest fix that addresses the flaw,
   then: `uv run python -m harness.runner tcXX --live`
   Live mode re-runs the agent (and retriever) with your fixed code and
   evaluates the fresh output — both the built-in metric and your scorer
   should now pass.
6. **Watch for regressions.** Occasionally run
   `uv run python -m harness.runner --all --live` — a fix for one metric
   can break another. That tension is the whole reason eval suites exist.

## The 50 cases at a glance

| Cases | Metric | What it teaches | Where the flaw lives |
|---|---|---|---|
| tc01–tc05 | AnswerRelevancy | fraction of output statements that address the input | prompt: trivia/tangent instruction |
| tc06–tc09 | Faithfulness | output claims must be supported by `retrieval_context` | prompt: "ignore reference materials" |
| tc10–tc12 | ContextualPrecision | relevant chunks must rank above irrelevant ones | retriever: length-based scoring |
| tc13–tc15 | ContextualRecall | context must contain everything the expected answer needs | retriever: k too small |
| tc16–tc18 | ContextualRelevancy | fraction of retrieved chunks relevant to the query | retriever: length-based scoring |
| tc19–tc22 | Hallucination *(lower=better)* | output must not contradict ground-truth `context` | prompt: "guess confidently" |
| tc23–tc25 | Bias *(lower=better)* | no demographic generalizations | prompt: "use generalizations" |
| tc26–tc28 | Toxicity *(lower=better)* | no mocking/demeaning language | prompt: "be brutally honest" |
| tc29–tc31 | Summarization | summaries: faithful to source + cover key points | prompt: "add details, drop boring parts" |
| tc32–tc37 | GEval (custom) | write your own metric in plain language | various prompt gaps |
| tc38–tc41 | ToolCorrectness | tool selection is driven by descriptions + prompt attitude | tools.py descriptions + prompt tool-aversion |
| tc42–tc44 | PromptAlignment | output must follow explicit instruction lists | instructions missing from prompt |
| tc45–tc47 | JsonCorrectness | output must validate against a pydantic schema | prompt: "wrap JSON in commentary" |
| tc48–tc50 | RoleAdherence (conversational) | stay in role across a multi-turn chat | prompt: "chat like a buddy" |

## Runner reference

```bash
uv run python -m harness.runner --list                # list cases
uv run python -m harness.runner tc07 tc08             # specific cases, recorded
uv run python -m harness.runner tc07 --live           # regenerate then evaluate
uv run python -m harness.runner --metric Faithfulness # one metric's group
uv run python -m harness.runner --all --live          # full suite (exit 1 on failure)
```

Recorded mode never calls the agent — it replays the broken outputs in the
dataset (only the judge runs). Live mode calls the agent, and for the RAG
cases (tc10–tc18) re-runs `app/retrieval.py` too, so your retriever fix is
what's being graded. To regenerate the dataset file itself:
`uv run python scripts/build_dataset.py`.

## Writing scorers — the two shapes

**LLM-judged (GEval):** best for fuzzy qualities — tone, level-appropriateness,
completeness. You write `criteria` or step-by-step `evaluation_steps`; the
judge scores 0–1. Tip: `evaluation_steps` beat a vague `criteria` blob —
they reduce judge variance the same way a rubric helps a human grader.

**Code-based (`BaseMetric` subclass):** best for deterministic checks —
"is it valid JSON", "under 120 words", "ends with a question", "called the
right tool with the right argument". Free, instant, zero variance.

Both shapes, with working code, are in `scorers/_template.py`. Worked
examples: `solutions/example_scorers/`.

## Notes for instructors

- The full flaw map, a reference fixed prompt, a fixed retriever, and
  class-flow tips are in `solutions/SOLUTIONS.md`.
- Judge cost is tiny (gpt-4o-mini); a full 50-case recorded run is a few
  cents. Live runs add one agent call per case.
- Borderline scores can flicker between runs — that's judge variance, and
  it's worth teaching rather than hiding.
