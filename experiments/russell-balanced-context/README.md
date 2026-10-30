# Russell balanced context experiment

A companion to [`russell-context`](../russell-context/README.md). Russell's
abstract, a priori exposition alternates with concrete, observational prose from
three near-contemporaries. The aim is to test whether the mix primes clearer
writing than Russell alone. This directory prepares context material; no model
experiment has been run and no improvement in writing quality has been
demonstrated.

## Sources

| Slot | Author and work | Gutenberg | Excerpt |
| --- | --- | ---: | --- |
| R | Bertrand Russell, *The Problems of Philosophy* (1912) | [5827](https://www.gutenberg.org/files/5827/5827-h/5827-h.htm) | Chapters I-XV, read from `../russell-context/source.html` |
| D | Charles Darwin, *The Voyage of the Beagle* (1839) | [944](https://www.gutenberg.org/ebooks/944) | Chapter I |
| H | T. H. Huxley, "On a Piece of Chalk" (1868), *Discourses: Biological & Geological* | [10060](https://www.gutenberg.org/ebooks/10060) | Essay I |
| J | William James, *Pragmatism* (1907) | [5116](https://www.gutenberg.org/ebooks/5116) | Lecture I |

The Darwin, Huxley, and James HTML were retrieved on 2026-10-30 and are saved in `sources/`.

## Corpus

Blocks follow the order `R D R H R J`, repeating, separated by `* * *` with no author
labels. A block is a run of whole paragraphs from one source, sized to the
paragraph count nearest 450 tokens. Each source is read in its original order.
Doses are nested prefixes of one block sequence, each ending on a completed
Russell/counterweight pair, so the 8k dose falls short of its cap rather than
breaking a pair.

| File | Tokens | Words | Russell | Darwin | Huxley | James |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `balanced-8k.txt` | 7,103 | 5,941 | 3,467 | 1,084 | 1,452 | 1,055 |
| `balanced-16k.txt` | 15,605 | 13,023 | 7,489 | 2,682 | 2,799 | 2,536 |
| `balanced-24k.txt` | 23,781 | 19,921 | 11,421 | 4,138 | 4,094 | 3,975 |

Tokens use `o200k_base`; per-author columns count block text without separators.
The 8k dose ends after the third Huxley block, so Huxley is slightly
overrepresented there. Headings, Darwin's italic chapter synopsis, Huxley's date
line, footnotes, and footnote markers are removed. Punctuation and spelling,
including James's capitalized emphasis and "tho", are retained. `manifest.json`
records source hashes, block order, and per-author shares. To rebuild:

```sh
python -m pip install -r experiments/russell-balanced-context/requirements.txt
python experiments/russell-balanced-context/build_corpus.py
```

The rebuild reads saved HTML only and makes no network or model calls. Copy the
outputs to `skills/russell-balanced-context/references/` and `manifest.json` to
`provenance.json` there, then run the repository sync.

## Comparisons

Run this corpus alongside the conditions in the
[Russell experiment](../russell-context/README.md#first-experiment), using the
same layout, controls, blinding, and outcome measures. Useful contrasts:

- **Matched total tokens:** balanced-8k against russell-8k, and balanced-24k against
  russell-24k. This tests the mix against Russell alone at the same context cost.
- **Matched Russell content:** balanced-16k's Russell blocks are the first 43 of
  russell-8k's 45 paragraphs (headings aside). This isolates what the counterweight adds.
- **Counterweight only:** if the mix helps, build a Darwin/Huxley/James corpus without
  Russell before crediting the interleaving.

Record topic leakage separately for each source: sense-data and tables, chalk and
foraminifera, St. Jago and the voyage, and pragmatism and temperament. Shifts in
voice between blocks may also read to a model as a stitched or corrupted document.
Whether author labels change that is a separate condition and is not built here.
