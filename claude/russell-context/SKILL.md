---
name: russell-context
description: Draft or revise prose after loading Bertrand Russell's prose into context. Use for Russell context injection experiments, Russell-primed writing, or requests to use Russell passages as a style reference.
---

# Russell context

Load actual prose from Bertrand Russell's *The Problems of Philosophy* (1912)
before doing the user's drafting or revision task. Default to passive exposure;
add explicit imitation instructions only when requested. Improved writing quality
is an experimental hypothesis, not an established benefit of this skill.

## Load the prose first

Select one reference, relative to this skill directory:

| Requested dose | Reference | Tokens (`o200k_base`) |
| --- | --- | ---: |
| 2k / small | [russell-2k.txt](references/russell-2k.txt) | 1,961 |
| 8k / default | [russell-8k.txt](references/russell-8k.txt) | 7,961 |
| 24k / large | [russell-24k.txt](references/russell-24k.txt) | 23,940 |
| full | [russell-full.txt](references/russell-full.txt) | 50,047 |

Before drafting or revising, read the selected file's complete text into your own
model-visible tool output. Resolve the path from this SKILL.md location, not the
project's working directory. A file path, link, hash, token count, or script that
reads without printing the prose does not load its contents into model context.

Use sequential chunks small enough for the reading tool's output limit. Verify
that each chunk is complete and that the chunks cover the entire selected file;
if output is truncated, reread that range in smaller chunks. Do not replace the
prose with a summary, stylistic analysis, search hits, or quotations. Do not
delegate this read: the model doing the writing needs to receive the text.

Load only the selected dose, not every reference. Counts exclude instructions,
conversation, task material, and output; other tokenizers may differ. If the user
requests a context percentage, use known usable context and reserve room for the
task and output. Do not invent the window size or repeat prose to meet a target.
If the corpus is too short or a complete read cannot fit, explain the limitation
and establish a feasible dose before claiming that condition was applied.

## Do the writing task

After the complete read, draft or revise as requested. Preserve the task's facts,
meaning, audience, and genre. Do not introduce Russell's philosophical claims,
examples, or borrowed phrases into unrelated prose. For passive exposure, proceed
without an added style-analysis or imitation stage. When explicit imitation is
requested, use his precision, sentence movement, and progression of thought as
examples while respecting the user's assignment.

At the first use, briefly report the selected dose and whether its complete text
was loaded; then deliver the requested writing. Reuse the loaded prose while it
remains in context. After compaction, or if only a summary remains, reload it before
the next substantive drafting or revision pass. Do not claim exact persistent
context occupancy merely because the file was read earlier.

## Source and experimental limits

The bundled files contain nested, paragraph-preserving prefixes or all 15 chapters
of [Project Gutenberg ebook 5827](https://www.gutenberg.org/files/5827/5827-h/5827-h.htm).
HTML whitespace and inline markup were flattened; front and back matter were
excluded. See [provenance.json](references/provenance.json) for extraction details,
counts, and hashes; read it only when checking provenance or integrity.

These samples are not curated rankings of Russell's best prose. Dose comparisons
also change chapter content. Distinguish quality, stylistic resemblance, factual
fidelity, topic leakage, and phrase copying when evaluating results.
