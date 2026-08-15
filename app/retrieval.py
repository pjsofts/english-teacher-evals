"""Toy retriever over a small corpus of English-teaching reference notes.

⚠️  COURSE NOTE — THE RETRIEVER IS DELIBERATELY BUGGY.
The contextual RAG test cases (ContextualPrecision / ContextualRecall /
ContextualRelevancy, tc10-tc18) fail because of `retrieve()` below, not
because of the corpus. Two bugs:

  BUG 1: chunks are scored by LENGTH, not by relevance to the query, so long
         irrelevant chunks outrank short relevant ones.
  BUG 2: the default k is 2, which is too small to recall everything an
         answer needs.

Fixing the retriever = scoring by query-term overlap (or anything sensible)
and returning enough chunks. The corpus itself is correct and sufficient.
"""

from __future__ import annotations

CORPUS = [
    # --- present perfect ---
    "The present perfect is formed with 'have/has' + past participle: "
    "'I have finished my homework.'",
    "Use the present perfect for life experience without a specific time: "
    "'She has visited Japan twice.'",
    "Use the past simple, not the present perfect, when a finished time is "
    "mentioned: 'I saw him yesterday' (NOT 'I have seen him yesterday').",
    # --- conditionals ---
    "The second conditional uses 'if + past simple, would + base verb' for "
    "unreal present situations: 'If I had more time, I would read more.'",
    "The first conditional uses 'if + present simple, will + base verb' for "
    "real future possibilities: 'If it rains, we will stay home.'",
    "The third conditional uses 'if + past perfect, would have + past "
    "participle' for unreal past situations: 'If I had studied, I would "
    "have passed.'",
    # --- articles ---
    "Use 'a' before consonant sounds and 'an' before vowel sounds: 'a "
    "university' (yu- sound) but 'an hour' (silent h).",
    "Use 'the' when both speaker and listener know which specific thing is "
    "meant: 'Close the door.'",
    "Do not use an article before uncountable nouns in general statements: "
    "'Water is essential' (NOT 'The water is essential' when speaking "
    "generally).",
    # --- phrasal verbs ---
    "'Give up' means to stop trying: 'Don't give up on learning English.'",
    "'Look after' means to take care of someone: 'She looks after her "
    "little brother.'",
    "'Run into' means to meet unexpectedly: 'I ran into my teacher at the "
    "supermarket.'",
    # --- IELTS / exams ---
    "The IELTS Writing test has two tasks: Task 1 (150 words, describing "
    "data or a letter) and Task 2 (250 words, an essay). Task 2 counts "
    "twice as much as Task 1.",
    "The IELTS Speaking test lasts 11-14 minutes and has three parts: "
    "introduction questions, a 2-minute individual long turn, and a "
    "two-way discussion.",
    # --- long, mostly irrelevant chunks (the buggy scorer loves these) ---
    "The history of the English language is conventionally divided into Old "
    "English (roughly 450-1150), Middle English (roughly 1150-1500), and "
    "Modern English (1500 to the present). Old English was a Germanic "
    "language brought to Britain by Anglo-Saxon settlers, heavily inflected "
    "and largely unintelligible to modern readers, while Middle English "
    "absorbed enormous amounts of Norman French vocabulary after 1066.",
    "There are many varieties of English spoken around the world, including "
    "British English, American English, Australian English, Indian English, "
    "and numerous creoles and pidgins; estimates of the total number of "
    "English speakers worldwide range from 1.5 to 2 billion people when "
    "second-language speakers are included, making it the most widely "
    "learned language on the planet by a considerable margin.",
    "Spelling reform movements have repeatedly attempted and failed to "
    "simplify English orthography over the last four centuries; notable "
    "advocates included Noah Webster, whose dictionaries popularized "
    "American spellings such as 'color' and 'center', and George Bernard "
    "Shaw, who left money in his will to fund the design of a new phonetic "
    "alphabet for English.",
]


def retrieve(query: str, k: int = 2) -> list[str]:
    """Return the top-k chunks for a query.

    BUG 1: scores by chunk length instead of query relevance.
    BUG 2: default k=2 is too small for multi-part answers.
    """
    scored = sorted(CORPUS, key=lambda chunk: len(chunk), reverse=True)
    return scored[:k]
