---
name: russell-balanced-context
description: Draft or revise prose after loading Russell's prose interleaved with Darwin, Huxley, and James. Use for balanced Russell context experiments or requests to prime writing with this mixed corpus.
---

# Russell balanced context

Load actual prose before doing the user's drafting or revision task: Bertrand
Russell's *The Problems of Philosophy* (1912) in alternate blocks, interleaved with
concrete, observational counterweights from Charles Darwin, T. H. Huxley, and
William James. Default to passive exposure; add explicit imitation instructions
only when requested. Improved writing quality is an experimental hypothesis, not
an established benefit of this skill.

## Load the prose first

Select one reference, relative to this skill directory:

| Requested dose | Reference | Tokens (`o200k_base`) |
| --- | --- | ---: |
| 8k / small / default | [balanced-8k.txt](references/balanced-8k.txt) | 7,103 |
| 16k / medium | [balanced-16k.txt](references/balanced-16k.txt) | 15,605 |
| 24k / large | [balanced-24k.txt](references/balanced-24k.txt) | 23,781 |

Each file alternates Russell with one counterweight block, rotating Darwin,
Huxley, James. Russell supplies about half the tokens and each counterweight about
a sixth. Blocks are separated by `* * *` and carry no author labels.

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
conversation, task material, and output; other tokenizers may differ. No larger
balanced dose is bundled. Do not invent the window size, repeat prose, or append
other corpora to meet a target; explain the limit and agree on a feasible dose
before claiming a condition was applied.

## Do the writing task

After the complete read, draft or revise as requested. Preserve the task's facts,
meaning, audience, and genre. Do not introduce the sources' claims, examples,
subjects (philosophy, chalk, the Beagle's voyage, pragmatism), or borrowed phrases
into unrelated prose. Do not name or attribute the unlabeled blocks unless asked.
For passive exposure, proceed without an added style-analysis or imitation stage.
When explicit imitation is requested, use the passages' precision, concrete
observation, sentence movement, and progression of thought as examples while
respecting the user's assignment.

At the first use, briefly report the selected dose and whether its complete text
was loaded; then deliver the requested writing. Reuse the loaded prose while it
remains in context. After compaction, or if only a summary remains, reload it before
the next substantive drafting or revision pass. Do not claim exact persistent
context occupancy merely because the file was read earlier.

## Source and experimental limits

All sources are Project Gutenberg texts: Russell, ebook 5827, chapters I-XV;
Darwin, *The Voyage of the Beagle* (ebook 944), chapter I; Huxley, "On a Piece of
Chalk" (1868) in ebook 10060; James, *Pragmatism* (ebook 5116), lecture I.
Each is read in original order, and doses are nested prefixes ending on a
completed Russell/counterweight pair. Headings, footnotes, and markup were
removed. See [provenance.json](references/provenance.json) for per-author block
order, token shares, and hashes; read it only when checking provenance or integrity.

These samples are not curated selections of the authors' best prose. Russell
blocks follow the same chapter order as the pure Russell corpus, so compare
against that corpus at matched Russell content as well as matched total tokens.
Distinguish quality, stylistic resemblance, factual fidelity, topic leakage, and
phrase copying when evaluating results.
