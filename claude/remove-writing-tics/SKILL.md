---
name: remove-writing-tics
description: "Detects and removes stock phrases, rhetorical tics, and formulaic prose using parallel detectors, one editor, and a bounded recheck. Use for an avoidance-focused revision or a writing-tic audit."
---

# Remove writing tics

Apply the user's writing preferences to an existing draft. Use two roles:
inexpensive detectors and one stronger adjudicator/editor. For an audit-only
request, return findings without rewriting. Preserve facts, qualifications,
citations, literal identifiers, quotations, and the requested voice.

The [catalogue](references/catalogue.md) contains 300 examples supplied or
accepted during the skill's development. Treat identified habits as expressions
the user wants removed. Grammatical or defensible wording can still violate that
preference. Recognize close variants; replacing "earns its place" with "justifies
its presence" leaves the same habit. Preserve the underlying information.

## Deployment

Read the adapter for the current host: [Codex](references/codex.md) or
[Claude Code](references/claude.md). These are requested defaults, not measured
claims about which models write best:

| Host | Detectors, including recheck | Adjudicator/editor |
| --- | --- | --- |
| Codex | GPT-6 Luna, low effort | GPT-6 Astra, medium effort |
| Claude Code | Claude Haiku 5.5 | Claude Opus 5.5 |

Set models through actual runtime controls. If a requested model or delegation
is unavailable, explain the limitation and ask for a substitute; do not silently
inherit another model or claim independent checks. Honor an existing authorized
substitution. Do not change global configuration or bypass concurrency limits.

## 1. Scan

1. Number all passages, including headings, captions, and prose in lists/tables.
   Assign one or two adjacent paragraphs to each detector, usually 150–450 words.
   Use smaller assignments for dense prose; split unusually long paragraphs at
   sentence boundaries. Every target passage must have an owner.
2. Give each detector the [detector instructions](references/detector.md), the
   **complete catalogue**, its target passages, adjacent context, and the genre
   and purpose. Keep context passages separate from its assigned targets.
3. Spawn one fresh detector job per assignment. Run up to 20 concurrently when
   capacity and document size permit; 10–20 is appropriate for a long document,
   not a minimum. Queue remaining jobs within the host's available slots. Workers
   return reports, make no document edits, and do not spawn agents.
4. Reconcile returned passage IDs with the assignment list. Retry incomplete jobs
   once, then report uncovered passages. An empty findings list is valid;
   missing or truncated output is not a clean result. Check that quoted spans
   occur in the assigned text, and merge duplicate findings.

## 2. Edit and check

Give one editor the complete draft, catalogue, merged reports, user constraints,
and [editor instructions](references/editor.md). It adjudicates findings and
revises the document coherently, including repetitive patterns spread across
assignments. The coordinator alone applies returned edits to the user's files.

Send changed passages through fresh detector jobs using the same instructions
and catalogue. Include adjacent context. Give the resulting findings back to the
same editor for **one local correction pass**. It must compare those corrections
with the original for meaning and avoid equivalent stock replacements. It must
not begin another general rewrite.

Stop after that correction pass. Report unresolved flags and coverage gaps;
the final corrections have not received another independent scan. Never label
the document tic-free. For audit-only work, stop after the initial reports.

Return the revised text or requested file edits, with only useful notes about
unresolved matters and verification limits. Apply the same avoidance preferences
to the accompanying explanation. See [evaluation cases](tests/evaluation-cases.md)
when validating the skill; packaging checks do not establish editorial quality.
