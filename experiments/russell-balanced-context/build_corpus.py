#!/usr/bin/env python3
"""Interleave Russell with Darwin, Huxley, and James into nested token doses.

Russell fills every other block; the alternate blocks rotate Darwin, Huxley,
James. Reads saved HTML only; no network requests or model calls are made.
"""

import hashlib
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup
import tiktoken


ROOT = Path(__file__).resolve().parent
RUSSELL_SOURCE = ROOT.parent / "russell-context" / "source.html"
SEPARATOR = "* * *"
BLOCK_TARGET = 450
BUDGETS = (8000, 16000, 24000)
ORDER = ("russell", "darwin", "russell", "huxley", "russell", "james")
encoding = tiktoken.get_encoding("o200k_base")


def tokens(text):
    return len(encoding.encode(text))


def flat(element):
    return " ".join(element.get_text().split())


def russell(soup):
    """Chapters I-XV prose paragraphs, headings dropped."""
    paragraphs, active = [], False
    for element in soup.body.find_all(recursive=False):
        text = flat(element)
        if element.name == "h2" and text.startswith("CHAPTER I."):
            active = True
        if element.name == "h2" and text == "BIBLIOGRAPHICAL NOTE":
            break
        if active and text and element.name == "p":
            paragraphs.append(text)
    return paragraphs


def darwin(soup):
    """Chapter I prose; the italic chapter synopsis is dropped."""
    start = next(h for h in soup.find_all("h2") if flat(h).startswith("CHAPTER I —"))
    paragraphs = []
    for element in start.find_all_next(["h2", "p"]):
        if element.name == "h2":
            break
        text = flat(element)
        italic = "".join(flat(i) for i in element.find_all("i"))
        if text and italic != text:
            paragraphs.append(text)
    return paragraphs


def huxley(soup):
    """ "On a Piece of Chalk" prose; date line and footnotes dropped."""
    start = next(h for h in soup.find_all("h4") if flat(h) == "ON A PIECE OF CHALK")
    paragraphs = []
    for element in start.find_all_next(["h3", "p"]):
        if element.name == "h3":
            break
        text = flat(element)
        if text and text != "[1868]" and not text.startswith("[Footnote"):
            paragraphs.append(re.sub(r"\[\d+\]", "", text))
    return paragraphs


def james(soup):
    """Lecture I prose."""
    start = next(h for h in soup.find_all("h2") if flat(h).startswith("Lecture I. —"))
    paragraphs = []
    for element in start.find_all_next(["h2", "p"]):
        if element.name == "h2":
            break
        text = flat(element)
        if text:
            paragraphs.append(text)
    return paragraphs


SOURCES = {
    "russell": {
        "path": RUSSELL_SOURCE,
        "extract": russell,
        "author": "Bertrand Russell",
        "title": "The Problems of Philosophy",
        "year": 1912,
        "url": "https://www.gutenberg.org/files/5827/5827-h/5827-h.htm",
        "retrieved_date": "2026-10-28",
        "excerpt": "Chapters I-XV in order; chapter headings dropped",
    },
    "darwin": {
        "path": ROOT / "sources" / "darwin-944.html",
        "extract": darwin,
        "author": "Charles Darwin",
        "title": "The Voyage of the Beagle",
        "year": 1839,
        "url": "https://www.gutenberg.org/cache/epub/944/pg944-images.html",
        "retrieved_date": "2026-10-30",
        "excerpt": "Chapter I (St. Jago - Cape de Verd Islands); italic synopsis dropped",
    },
    "huxley": {
        "path": ROOT / "sources" / "huxley-10060.html",
        "extract": huxley,
        "author": "Thomas Henry Huxley",
        "title": "On a Piece of Chalk, in Discourses: Biological & Geological",
        "year": 1868,
        "url": "https://www.gutenberg.org/cache/epub/10060/pg10060-images.html",
        "retrieved_date": "2026-10-30",
        "excerpt": "Essay I only; date line, footnotes, and footnote markers dropped",
    },
    "james": {
        "path": ROOT / "sources" / "james-5116.html",
        "extract": james,
        "author": "William James",
        "title": "Pragmatism: A New Name for Some Old Ways of Thinking",
        "year": 1907,
        "url": "https://www.gutenberg.org/cache/epub/5116/pg5116-images.html",
        "retrieved_date": "2026-10-30",
        "excerpt": "Lecture I (The Present Dilemma in Philosophy)",
    },
}


def take_block(paragraphs, cursor):
    """Consecutive paragraphs from cursor, stopping nearest BLOCK_TARGET tokens."""
    block = [paragraphs[cursor]]
    cursor += 1
    while cursor < len(paragraphs):
        size = tokens("\n\n".join(block))
        grown = tokens("\n\n".join(block + [paragraphs[cursor]]))
        if abs(grown - BLOCK_TARGET) >= abs(size - BLOCK_TARGET):
            break
        block.append(paragraphs[cursor])
        cursor += 1
    return block, cursor


def main():
    streams, raws = {}, {}
    for name, source in SOURCES.items():
        raws[name] = source["path"].read_bytes()
        streams[name] = source["extract"](BeautifulSoup(raws[name], "html.parser"))
        if not streams[name]:
            raise ValueError(f"No paragraphs extracted for {name}")

    # Build one block sequence; each dose is a prefix ending on a counterweight block.
    cursors = dict.fromkeys(streams, 0)
    sequence = []
    while True:
        name = ORDER[len(sequence) % len(ORDER)]
        if cursors[name] >= len(streams[name]):
            break
        block, cursors[name] = take_block(streams[name], cursors[name])
        sequence.append((name, "\n\n".join(block), len(block)))
        draft = f"\n\n{SEPARATOR}\n\n".join(text for _, text, _ in sequence) + "\n"
        if tokens(draft) > max(BUDGETS) + BLOCK_TARGET * 4:
            break

    outputs = {}
    for budget in BUDGETS:
        best = None
        for end in range(2, len(sequence) + 1, 2):
            text = f"\n\n{SEPARATOR}\n\n".join(t for _, t, _ in sequence[:end]) + "\n"
            if tokens(text) > budget:
                break
            best = end
        if best is None or best == len(sequence):
            raise ValueError(f"Sources too short for {budget} tokens")
        selected = sequence[:best]
        text = f"\n\n{SEPARATOR}\n\n".join(t for _, t, _ in selected) + "\n"
        name = f"balanced-{budget // 1000}k.txt"
        (ROOT / name).write_text(text, encoding="utf-8")
        shares = {}
        for author in streams:
            author_tokens = sum(tokens(t) for a, t, _ in selected if a == author)
            shares[author] = {
                "blocks": sum(a == author for a, _, _ in selected),
                "paragraphs": sum(n for a, _, n in selected if a == author),
                "tokens": author_tokens,
            }
        outputs[name] = {
            "tokens": tokens(text),
            "whitespace_words": len(text.split()),
            "bytes": len(text.encode("utf-8")),
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "target_token_cap": budget,
            "blocks": len(selected),
            "block_authors": [a for a, _, _ in selected],
            "author_shares": shares,
        }

    manifest = {
        "title": "Russell interleaved with Darwin, Huxley, and James",
        "design": "Russell fills alternate blocks (about half the tokens); the other blocks rotate Darwin, Huxley, James (about one sixth each). Order: R D R H R J, repeating.",
        "separator": SEPARATOR,
        "block_target_tokens": BLOCK_TARGET,
        "block_rule": "Consecutive whole paragraphs from one source, stopping at the paragraph count nearest the target; a single long paragraph may exceed it.",
        "sample_selection": "Nested prefixes of one block sequence, each ending on a completed Russell/counterweight pair; each source is read in original order with no repetition or padding.",
        "extraction": "Collapse HTML whitespace and flatten inline markup; keep paragraph text, punctuation, and spelling. Exclude headings, Gutenberg markers, CSS, and HTML.",
        "token_encoding": encoding.name,
        "token_count_scope": "File text only, separators included; excludes chat framing, instructions, draft, history, tools, and output. Other tokenizers may differ.",
        "sources": {
            name: {
                **{k: v for k, v in source.items() if k not in ("path", "extract")},
                "source_file": str(source["path"].relative_to(ROOT.parent)),
                "source_sha256": hashlib.sha256(raws[name]).hexdigest(),
                "paragraphs_available": len(streams[name]),
            }
            for name, source in SOURCES.items()
        },
        "outputs": outputs,
    }
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: {
                    "tokens": v["tokens"],
                    "shares": {a: s["tokens"] for a, s in v["author_shares"].items()},
                }
                for k, v in outputs.items()
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
