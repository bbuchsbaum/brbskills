#!/usr/bin/env python3
"""Compare literal anchors in UTF-8 text or Markdown; never assess meaning.

Usage: compare_anchors.py BEFORE AFTER [--json] [--lock LITERAL ...]
Successful comparisons exit 0, including when review candidates are found.
Input errors exit 2. No network access, automatic edits, or style scoring.
"""

import argparse
from bisect import bisect_right
from collections import defaultdict
import json
from pathlib import Path
import re
import sys


LIMITATIONS = [
    "Matching inventories do not establish semantic equivalence. Changed actors, "
    "relationships, scope, ordering, or attachment of the same numbers can go undetected.",
    "Markers are a small English inventory, not a parser. Their senses and scopes "
    "are not resolved; differences are review candidates, not errors.",
    "Numeric extraction covers common decimal/scientific forms, comparators, and "
    "selected units. It does not interpret ranges, dates, locale formats, formulas, "
    "written-out numbers, or conversions. Numeric/unit whitespace is ignored.",
    "Markdown extraction is heuristic: ordinary backtick spans, backtick/tilde "
    "fences, inline links, and one-line reference definitions are supported. "
    "Indented code, HTML, nested labels, and full CommonMark parsing are not supported.",
    "Raw URLs use http, https, or ftp. Trailing prose punctuation is trimmed "
    "heuristically. Link destinations are compared literally, not fetched or resolved.",
    "Code contents and locked literals are compared exactly after normalizing "
    "line endings. Locks are case-sensitive, include overlapping occurrences, and "
    "apply throughout the document. Code, URLs, and link destinations are masked "
    "for numeric and prose-marker extraction.",
]

# These are signals to inspect, never a list of prohibited words.
MARKERS = {
    "modality": "can cannot could may might must shall should will would",
    "negation": "no not never neither nor without",
    "quantifier": "all any each every some none only both either",
    "conditional": "if unless except otherwise",
}
MARKER_GROUP = {word: group for group, words in MARKERS.items()
                for word in words.split()}
MARKER_RE = re.compile(
    r"\b\w+n['’]t\b|\b(?:"
    + "|".join(sorted(MARKER_GROUP, key=len, reverse=True)) + r")\b", re.IGNORECASE)
FENCE_OPEN = re.compile(r"^ {0,3}(`{3,}|~{3,})[^\n]*(?:\n|$)", re.MULTILINE)
TICKS = re.compile(r"`+")
INLINE_LINK = re.compile(r"!?\[[^\]\n]*\]\(\s*")
REFERENCE = re.compile(r"^ {0,3}\[[^\]\n]+\]:[ \t]*", re.MULTILINE)
URL_RE = re.compile(r"\b(?:https?|ftp)://[^\s<>\"`]+", re.IGNORECASE)
UNITS = (
    "kg mg µg μg ug g km cm mm µm μm um nm m "
    "mL ml µL μL uL L l ns µs μs us ms s sec secs min mins h hr hrs "
    "day days week weeks Hz kHz MHz GHz °C °F K mV V mA A mW W mT T "
    "kPa MPa Pa mol mmol µmol μmol umol B kB KB MB GB TB KiB MiB GiB TiB"
).split()
UNIT_PATTERN = "|".join(re.escape(unit) for unit in sorted(UNITS, key=len, reverse=True))
NUMBER_RE = re.compile(
    r"(?:(?:[<>]=?|[≤≥≈=])\s*|(?<![\w.])\s*)"
    r"[+\-−]?(?:[$€£]\s*)?"
    r"(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?|\.\d+)"
    r"(?:[eE][+\-−]?\d+)?"
    r"(?:\s*(?:%|‰|" + UNIT_PATTERN + r")(?!\w))?"
    r"(?!\w|\.\d)"
)


def mask(text, ranges):
    """Keep offsets and newlines stable while hiding extracted spans."""
    chars = list(text)
    for start, end in ranges:
        for pos in range(start, end):
            if chars[pos] != "\n":
                chars[pos] = " "
    return "".join(chars)


class Document:
    def __init__(self, text):
        self.text = text
        self.lines = [0] + [m.end() for m in re.finditer("\n", text)]
        self.anchors = defaultdict(lambda: defaultdict(list))

    def add(self, category, key, start, end):
        first = bisect_right(self.lines, start) - 1
        last = bisect_right(self.lines, max(start, end - 1)) - 1
        left, right = max(0, start - 70), min(len(self.text), end + 70)
        context = re.sub(r"\s+", " ", self.text[left:right]).strip()
        if len(context) > 240:
            context = context[:237] + "..."
        self.anchors[category][key].append({
            "line": first + 1,
            "end_line": last + 1,
            "column": start - self.lines[first] + 1,
            "text": self.text[start:end],
            "context": context,
        })


def extract_code(doc):
    text, ranges, offset = doc.text, [], 0
    while True:
        opener = FENCE_OPEN.search(text, offset)
        if not opener:
            break
        fence = opener.group(1)
        closer_re = re.compile(r"^ {0,3}" + re.escape(fence[0])
                               + "{" + str(len(fence)) + r",}[ \t]*(?:\n|$)",
                               re.MULTILINE)
        closer = closer_re.search(text, opener.end())
        content_end = closer.start() if closer else len(text)
        doc.add("fenced_code", text[opener.end():content_end],
                opener.end(), content_end)
        offset = closer.end() if closer else len(text)
        ranges.append((opener.start(), offset))
    visible, offset = mask(text, ranges), 0
    while True:
        opener = TICKS.search(visible, offset)
        if not opener:
            break
        closer = TICKS.search(visible, opener.end())
        while closer and len(closer.group()) != len(opener.group()):
            closer = TICKS.search(visible, closer.end())
        if closer:
            doc.add("inline_code", text[opener.end():closer.start()],
                    opener.end(), closer.start())
            ranges.append((opener.start(), closer.end()))
            offset = closer.end()
        else:
            offset = opener.end()
    return mask(text, ranges)


def destination(text, start):
    """Return a simple Markdown destination span, retaining literal escapes."""
    if start >= len(text):
        return None
    if text[start] == "<":
        end = text.find(">", start + 1)
        return (start + 1, end) if end >= 0 and "\n" not in text[start:end] else None
    depth, pos = 0, start
    while pos < len(text):
        char = text[pos]
        if char == "\\" and pos + 1 < len(text):
            pos += 2
            continue
        if char.isspace() or (char == ")" and depth == 0):
            break
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        pos += 1
    return (start, pos) if pos > start and depth == 0 else None


def extract_links(doc, text):
    ranges = []
    for pattern in (INLINE_LINK, REFERENCE):
        for match in pattern.finditer(text):
            span = destination(text, match.end())
            if span:
                start, end = span
                doc.add("link_destination", doc.text[start:end], start, end)
                ranges.append(span)
    visible = mask(text, ranges)
    for match in URL_RE.finditer(visible):
        url = match.group().rstrip(".,;:!?'")
        for opening, closing in (("(", ")"), ("[", "]"), ("{", "}")):
            while url.endswith(closing) and url.count(closing) > url.count(opening):
                url = url[:-1]
        end = match.start() + len(url)
        doc.add("raw_url", url, match.start(), end)
        ranges.append((match.start(), match.end()))
    return mask(text, ranges)


def extract(text, locks):
    doc = Document(text)
    prose = extract_links(doc, extract_code(doc))
    for match in NUMBER_RE.finditer(prose):
        start = match.start()
        while start < match.end() and prose[start].isspace():
            start += 1
        key = re.sub(r"\s+", "", prose[start:match.end()])
        doc.add("numeric_expression", key, start, match.end())
    for match in MARKER_RE.finditer(prose):
        word = match.group().lower().replace("’", "'")
        group = MARKER_GROUP.get(word, "negation")
        doc.add("marker_" + group, word, match.start(), match.end())
    for literal in dict.fromkeys(locks):
        start = text.find(literal)
        while start >= 0:
            doc.add("locked_literal", literal, start, start + len(literal))
            start = text.find(literal, start + 1)
    return doc


def compare(before, after, locks, before_path, after_path):
    old, new = extract(before, locks), extract(after, locks)
    findings = []
    for category in sorted(set(old.anchors) | set(new.anchors)):
        old_items, new_items = old.anchors[category], new.anchors[category]
        for key in sorted(set(old_items) | set(new_items)):
            left, right = old_items.get(key, []), new_items.get(key, [])
            if len(left) != len(right):
                findings.append({
                    "status": "review_candidate", "category": category,
                    "anchor": key, "before_count": len(left), "after_count": len(right),
                    "before": left, "after": right,
                })
    return {
        "schema_version": "1.0",
        "advisory": True,
        "semantic_equivalence_not_assessed": True,
        "inputs": {"before": str(before_path), "after": str(after_path)},
        "comparison": "Literal multisets and English marker inventories; no semantic verdict.",
        "findings": findings,
        "limitations": LIMITATIONS,
    }


def print_report(report):
    print("Advisory anchor comparison — semantic equivalence not assessed.")
    if not report["findings"]:
        print("No extracted inventory differences found. Meaning may still have changed.")
    for item in report["findings"]:
        label = json.dumps(item["anchor"], ensure_ascii=False)
        if len(label) > 140:
            label = label[:137] + "..."
        print(f"\nReview candidate: {item['category']} {label}")
        print(f"  Occurrences: {item['before_count']} before; {item['after_count']} after")
        for side in ("before", "after"):
            for occurrence in item[side]:
                location = str(occurrence["line"])
                if occurrence["end_line"] != occurrence["line"]:
                    location += "-" + str(occurrence["end_line"])
                print(f"  {side}, line {location}, column {occurrence['column']}: "
                      f"{occurrence['context']}")
    print("\nLimits:")
    for limitation in report["limitations"]:
        print("- " + limitation)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("before", type=Path, help="Original UTF-8 text or Markdown file")
    parser.add_argument("after", type=Path, help="Revised UTF-8 text or Markdown file")
    parser.add_argument("--json", action="store_true", help="Emit structured JSON")
    parser.add_argument("--lock", action="append", default=[], metavar="LITERAL",
                        help="Compare exact occurrences of a literal (repeatable)")
    args = parser.parse_args(argv)
    if any(not literal for literal in args.lock):
        parser.error("--lock requires a nonempty literal")
    try:
        before = args.before.read_text(encoding="utf-8")
        after = args.after.read_text(encoding="utf-8")
        if "\x00" in before or "\x00" in after:
            raise ValueError("input contains NUL bytes; supply UTF-8 text or Markdown")
    except (OSError, UnicodeError, ValueError) as error:
        if args.json:
            print(json.dumps({"schema_version": "1.0", "input_error": str(error),
                              "semantic_equivalence_not_assessed": True}))
        else:
            print(f"Input error: {error}", file=sys.stderr)
        return 2
    report = compare(before, after, args.lock, args.before, args.after)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_report(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
