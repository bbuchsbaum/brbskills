#!/usr/bin/env python3
"""Extract Gutenberg 5827 and build paragraph-preserving, nested token doses.

Run beside source.html; no network requests or model calls are made.
"""

import hashlib
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup
import tiktoken


ROOT = Path(__file__).resolve().parent
SOURCE_URL = "https://www.gutenberg.org/files/5827/5827-h/5827-h.htm"


def main():
    raw = (ROOT / "source.html").read_bytes()
    soup = BeautifulSoup(raw, "html.parser")
    blocks = []
    chapters = []
    active = False
    for element in soup.body.find_all(recursive=False):
        text = " ".join(element.get_text().split())
        if element.name == "h2" and text.startswith("CHAPTER I."):
            active = True
        if element.name == "h2" and text == "BIBLIOGRAPHICAL NOTE":
            break
        if not active or not text:
            continue
        if element.name not in ("p", "h2"):
            raise ValueError(f"Unrecognized content block: {element.name}")
        if element.name == "h2":
            chapters.append(text)
        blocks.append(text)
    if len(chapters) != 15:
        raise ValueError(f"Expected 15 chapters, found {len(chapters)}")

    encoding = tiktoken.get_encoding("o200k_base")
    outputs = {}

    def save(name, selected, target=None):
        text = "\n\n".join(selected) + "\n"
        (ROOT / name).write_text(text, encoding="utf-8")
        outputs[name] = {
            "tokens": len(encoding.encode(text)),
            "whitespace_words": len(text.split()),
            "bytes": len(text.encode("utf-8")),
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "target_token_cap": target,
        }

    save("russell-full.txt", blocks)
    for budget in (2000, 8000, 24000):
        selected = []
        for index, block in enumerate(blocks):
            candidate = selected + [block]
            if len(encoding.encode("\n\n".join(candidate) + "\n")) > budget:
                break
            # Avoid ending a sample on a chapter heading with no prose.
            if re.match(r"CHAPTER [IVX]+\.", block):
                next_block = blocks[index + 1]
                if len(encoding.encode("\n\n".join(candidate + [next_block]) + "\n")) > budget:
                    break
            selected.append(block)
        save(f"russell-{budget // 1000}k.txt", selected, budget)

    manifest = {
        "title": "The Problems of Philosophy",
        "author": "Bertrand Russell",
        "publication_year": 1912,
        "source_url": SOURCE_URL,
        "retrieved_date": "2026-10-28",
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "extraction": "Chapters I-XV only; preserve paragraph order and punctuation; collapse HTML whitespace; flatten inline markup. Exclude contents, preface, bibliographical note, Gutenberg markers, CSS, and HTML.",
        "sample_selection": "Nested prefixes in original chapter order, ending at paragraph boundaries; no repetition or padding.",
        "token_encoding": encoding.name,
        "token_count_scope": "File text only; excludes chat framing, instructions, draft, history, tools, and output. Other tokenizers may differ.",
        "chapters": chapters,
        "outputs": outputs,
    }
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(outputs, indent=2))


if __name__ == "__main__":
    main()
