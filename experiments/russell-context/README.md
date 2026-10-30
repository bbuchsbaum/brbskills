# Russell context experiment

Clean prose from Bertrand Russell's *The Problems of Philosophy* (1912),
[Project Gutenberg ebook 5827](https://www.gutenberg.org/files/5827/5827-h/5827-h.htm),
retrieved 2026-10-28. This directory prepares context material; no model experiment
has been run and no improvement in writing quality has been demonstrated.

## Corpus

| File | Tokens (`o200k_base`) | Whitespace words |
| --- | ---: | ---: |
| `russell-2k.txt` | 1,961 | 1,694 |
| `russell-8k.txt` | 7,961 | 6,846 |
| `russell-24k.txt` | 23,940 | 20,523 |
| `russell-full.txt` | 50,047 | 42,550 |

The full text contains all 15 chapters. Contents, preface, bibliographical note,
Gutenberg markers, and HTML are excluded. Paragraphs, punctuation, spelling, and
chapter order are retained; HTML whitespace is collapsed and inline emphasis
becomes plain text. Smaller samples are nested prefixes ending at complete
paragraphs. They are reproducible doses, not a curated selection of Russell's
best passages. Longer doses also introduce different chapter content, so dose
and passage selection are partly confounded.

`source.html` preserves the downloaded source. `manifest.json` records its URL,
hash, extraction method, chapter list, and output hashes and counts. To rebuild:

```sh
python -m pip install -r experiments/russell-context/requirements.txt
python experiments/russell-context/build_corpus.py
```

The rebuild reads the saved HTML and does not download or call an LLM. Token
counts cover only each corpus file. Recount with the target model's tokenizer
when allocating an actual context budget.

## How much context?

Start with about **8,000 tokens**, as a practical hypothesis rather than a known
optimum. Compare no injection, 2k, 8k, 24k, and the full book before adopting a
default. Treat 50% of the context window as an additional condition if useful.
The entire book is only about 50k tokens under this tokenizer: it cannot supply
64k unique tokens for half of a 128k window, or 100k for half of a 200k window.
Do not repeat passages merely to hit a percentage; that changes the experiment.

Allocate the budget using:

`style corpus + instructions + history/tools + draft/source material + output reserve <= usable context`

Large context experiments have shown sensitivity to information position, but
that is not direct evidence about the best amount of style material. See
[Lost in the Middle](https://aclanthology.org/2024.tacl-1.9/). There is no evidence
here that 50% is optimal for prose revision. The risk of philosophical vocabulary
or argumentative manner leaking into unrelated work is a hypothesis to evaluate.

## First experiment

Use fresh conversations with identical instructions, model/version, generation
settings, output budget, task text, and placement. Put the reference passage
before the actual assignment. Insert the file contents, not just a path or link;
verify the application actually includes all the text rather than retrieving
snippets or summarizing it.

For **passive exposure**, use this layout, leaving the reference block empty in
the no-injection condition:

```text
<reference_prose>
[INSERT CORPUS FILE CONTENTS]
</reference_prose>

<assignment>
[IDENTICAL DRAFTING OR REVISION REQUEST, INCLUDING THE ORIGINAL DRAFT]
</assignment>
```

Test **explicit imitation** separately by adding the same instruction to every
condition, including the empty-reference control:

```text
Where reference prose is supplied, use its sentence movement, precision, and
explanatory progression as examples for the assignment. Preserve the assignment's
facts, meaning, audience, and genre. Do not borrow the reference's phrases,
examples, philosophical subject matter, or claims.
```

Use several independent outputs per condition across multiple tasks, including
both new drafts and revisions. Blind and shuffle the outputs before judging
clarity, precision, paragraph progression, rhythm, and overall preference.
For revisions, separately check preservation of meaning and factual claims.
Record unwanted archaism, topic leakage, and phrase copying. Stylistic resemblance
is a separate outcome from quality. If the first comparison looks promising,
repeat with alternative passages and an ordinary-prose control of similar length.
Russell's familiarity from model training also limits claims about learning a new
style from context.
