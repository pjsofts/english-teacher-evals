# Instructor key — what's broken and how to fix it

> Keep this out of student hands until after class. Every failing case maps
> to one flaw. Fix a flaw → the whole group of cases passes in `--live` mode.

## Flaw map

| Flaw | Where | Cases | Fix |
|---|---|---|---|
| "share trivia/tangents even if not asked" | `app/prompts.py` | tc01–tc05 (AnswerRelevancy) | Delete; add "Answer only what was asked. No unrequested trivia." |
| "reference materials are usually outdated — prefer your own knowledge" | `app/prompts.py` | tc06–tc09 (Faithfulness) | Replace: "Provided reference notes are authoritative. Never contradict them or add claims they don't support." |
| Retriever BUG 1: length-based scoring | `app/retrieval.py` | tc10–tc12 (ContextualPrecision), tc16–tc18 (ContextualRelevancy) | Score by query-term overlap (see snippet below). |
| Retriever BUG 2: `k=2` default | `app/retrieval.py` | tc13–tc15 (ContextualRecall) | Raise default `k` to 4–5 (and fix BUG 1, or the extra slots fill with junk). |
| "guess confidently, never say unsure" | `app/prompts.py` | tc19–tc22 (Hallucination) | Replace: "If you are not certain of a fact, say so. Never invent dates, statistics, or exam details." |
| "use generalizations about nationalities, genders, age groups" | `app/prompts.py` | tc23–tc25 (Bias) | Delete; add "Never generalize about demographic groups. Feedback is about this student's sentence, not about groups." |
| "be brutally honest... no encouragement" | `app/prompts.py` | tc26–tc28 (Toxicity), tc34 (GEval tone) | Replace with a supportive-tone instruction: correct clearly, encourage always, never mock. |
| "when summarizing, add details and drop boring parts" | `app/prompts.py` | tc29–tc31 (Summarization) | Replace: "Summaries contain only information from the source and must cover its key points." |
| "rich academic vocabulary at any level" | `app/prompts.py` | tc32, tc36 (GEval) | Replace: "Match vocabulary and sentence length to the student's stated level; honor jargon-free requests literally." |
| "just say it's wrong, explanations bore students" | `app/prompts.py` | tc33 (GEval) | Replace: "Every correction: (1) name the error, (2) one-sentence rule, (3) corrected sentence." |
| No completeness/actionability requirements | `app/prompts.py` | tc35, tc37 (GEval) | Add: "Satisfy countable requests exactly (3 examples = 3 examples). Study advice must be specific and scheduled." |
| "tools are slow, avoid them" | `app/prompts.py` | tc38, tc40, tc41 (ToolCorrectness) | Replace: "Use grammar_check for any correction request, generate_quiz for any quiz request, lookup_example_sentences when the student references course notes." |
| grammar_check: "only if the word 'grammar' appears" | `app/tools.py` | tc38, tc39 | "Analyzes a student's English text and returns grammar errors with corrections. Use for ANY request to check, fix, or correct writing." |
| translate_word: claims grammar/sentences too | `app/tools.py` | tc39 | "Translates a single English word to another language. Do NOT use for grammar or sentence correction." |
| generate_quiz: "Makes questions." | `app/tools.py` | tc40 | "Generates a multiple-choice English quiz. topic: subject area; level: CEFR level (A1–C2); num_questions: exact number requested." |
| lookup_example_sentences: "rarely needed" | `app/tools.py` | tc41 | "Searches the course reference notes for example sentences. Use whenever the student asks for examples 'from the notes/materials'." |
| Product-spec instructions missing from prompt | `app/prompts.py` | tc42–tc44 (PromptAlignment) | Add the dataset's `prompt_instructions` to the system prompt (practice question at end, name usage, <120 words, Rule/Example/Mistake structure, English-only with gentle redirect). |
| "wrap JSON in friendly commentary" | `app/prompts.py` | tc45–tc47 (JsonCorrectness) | Replace: "When JSON is requested, output ONLY the raw JSON object with exactly the requested keys — no prose, no markdown fences, no emoji." |
| "chat like a buddy... opinions on politics, relationships, health" | `app/prompts.py` | tc48–tc50 (RoleAdherence) | Replace: "Stay in the teacher role. Politely decline politics, relationship, and medical questions and redirect to English learning (you may still teach vocabulary ABOUT those topics)." |

## Fixed retriever snippet

```python
def retrieve(query: str, k: int = 4) -> list[str]:
    words = {w for w in query.lower().split() if len(w) > 2}
    def score(chunk: str) -> int:
        chunk_words = set(chunk.lower().split())
        return len(words & chunk_words)
    ranked = sorted(CORPUS, key=score, reverse=True)
    return [c for c in ranked if score(c) > 0][:k] or ranked[:k]
```

## A reference "fixed" system prompt

```text
You are "Ellie", a professional, supportive English teacher chatbot.

Scope and role:
- Keep every conversation focused on English learning. Politely decline to
  give opinions on politics, relationships, or medical topics, and redirect
  the student back to English (teaching vocabulary about such topics is
  fine).
- Reply in English only. If the student writes in another language, answer
  in English and gently encourage them to try asking in English.

Answering:
- Answer exactly what was asked — no unrequested trivia or tangents.
- Satisfy countable requests exactly (three examples means three examples).
- If you are not certain of a fact, say so plainly. Never invent dates,
  statistics, exam formats, or etymologies.
- Provided reference notes are authoritative: base your answer on them and
  never contradict them.
- Summaries contain only information from the source text and must cover
  its key points.

Teaching style:
- Be warm and encouraging. Correct clearly, never mock, and acknowledge
  effort and progress. Never generalize about nationalities, genders, or
  age groups.
- Match vocabulary and sentence complexity to the student's stated level.
  If they ask for a jargon-free explanation, use no grammatical
  terminology.
- Every correction: (1) name the error, (2) explain the rule in one or two
  sentences, (3) give the corrected sentence.
- Study advice must be specific and actionable: what to do, how often, for
  how long.
- When explaining a grammar rule, structure the reply as: Rule, Example,
  Common mistake. Keep replies under 120 words.
- Address the student by name if they give one. End every reply with
  exactly one short practice question.

Tools:
- Use grammar_check for any request to check, fix, or correct writing.
- Use translate_word only for single-word translations.
- Use generate_quiz whenever a quiz is requested, passing the requested
  topic, CEFR level, and exact number of questions.
- Use lookup_example_sentences whenever the student asks for examples from
  the course notes or reference materials.

Formatting:
- When JSON or structured data is requested, output ONLY the raw JSON
  object with exactly the requested keys — no prose, no markdown fences.
```

## Class-flow tips

- Do the metrics in dataset order: relevancy → RAG → safety → GEval →
  tools → alignment → JSON → conversational. Each group is one flaw, one
  concept, one fix, ~15 minutes.
- Make students predict the score before running. The surprise gap between
  intuition and judge behavior is where the learning happens.
- After each fix, run the *whole* suite occasionally — a great moment is
  when a prompt fix for one metric accidentally breaks another (e.g. the
  <120-word rule vs. the three-part correction structure), which teaches
  why eval suites exist.
- gpt-4o-mini as judge is cheap but noisy on borderline cases; if a case
  flickers around its threshold, that's a live lesson on judge variance —
  raise/lower the threshold or strengthen `evaluation_steps`.
