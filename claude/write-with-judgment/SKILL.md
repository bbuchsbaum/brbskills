---
name: write-with-judgment
description: "Draft, revise, review, or summarize prose (scientific manuscripts, technical docs, agent-facing instructions and tool text, essays, letters, literary work) while preserving meaning, evidence, and voice."
---

# Write with judgment

Improve what the reader can understand, infer, do, or feel, while preserving the
commitments the task requires: work out what the passage is for, find what stops
it working, fix that, and check what the revision changed.

## 1. Infer the job

Read the request and the whole relevant passage first. Infer audience, purpose,
genre, English variety, venue rules, length, and the permitted edit from context;
ask one focused question only when an open choice would materially change the
result. Continue the unambiguous work.

| Request | Permitted edit |
| --- | --- |
| Proofread, copyedit, light polish | Correct errors and improve readability; keep claims, structure where practical, and effective voice. |
| Rewrite, improve, strengthen | Reorganize and rephrase as needed; keep the position and evidential strength. |
| Critique, substantive revision | Examine and repair the argument; identify changed claims and missing evidence. |
| Shorten, summarize, adapt | Omit according to purpose; keep decisive qualifications and the scope of retained claims. |
| Draft from a brief | Compose from supplied or verified material; invent detail only where a creative brief permits it. |

Internally, separate **must survive**, **may change**, and **needs verification**.
"Stronger" never means more certain. Outside a creative brief, "concrete" never
means invented: mark missing facts as visible gaps. Flag unsupported claims rather
than making them more credible.

Follow the user's instructions and any required venue style first. Then protect
truth, required meaning, quotations, citations, literal identifiers, and intended
effect before optimizing wording. A citation travels with the claim it supports;
if a permitted cut removes a cited claim, say so. English variety, citation style,
and prose conventions are independent choices: settling one does not settle the
others.

## 2. Load the genre guidance

Read only what the passage needs; load several when a document mixes genres.

- [scientific.md](references/scientific.md): manuscripts, abstracts, grants,
  reviews, response letters: paper architecture, section jobs, claim calibration.
- [technical.md](references/technical.md): READMEs and software documentation,
  procedures, specifications, and text an agent or program must parse without
  asking (tool descriptions, prompts, error and status messages).
- [genres.md](references/genres.md): essays, letters and reports, fiction and
  poetry, summaries.

## 3. Diagnose, then revise

Name the main obstacle before choosing a remedy: missing premise, buried point,
ambiguous actor, misplaced condition, unstable terminology, needless abstraction,
redundancy, wrong tone, broken rhythm. Fix the highest-level obstacle first. For
substantial prose, name each paragraph's job and check how it advances from the
last. When voice matters, identify two or three effective features of the actual
text and keep their effect.

- Keep conditions beside the actions they govern and qualifications beside the
  claims they limit.
- One term per concept; different terms for different concepts.
- Judge economy by reader effort, not word count.
- Treat familiar style advice as conditional.

When rules conflict or a paragraph will not cohere, read
[decisions.md](references/decisions.md). For light polish, or when unsure whether
to intervene at all, read [examples.md](references/examples.md), which includes
deliberate non-edits.

For a debatable edit, ask: **if I reverted this, what would the reader lose?** If
the answer is only a different preference, keep the original. When the user asked
to tighten, shorten, or restyle, economy and rhythm count as gains; the test then
protects meaning and voice and does not block the requested edit. Large
problems justify large changes. Never use length caps, passive counts,
readability grades, or banned-word lists as measures of quality.

## 4. Verify separately

Compare the source (or brief) with the revision: roles, logic, modal force, scope,
numbers, and which claim each citation supports. Compare relationships, not just
whether the same words remain. When equivalence is uncertain, ask: could the
original be true while the revision is false, or the reverse? When the revision changes claims,
conditions, numbers, or instructions that someone will publish or act on, read
[verification.md](references/verification.md), which also covers the optional
`scripts/compare_anchors.py` check and when to use a fresh reviewer. Stop when the
remaining changes are matters of taste.

## 5. Deliver

Lead with the usable text. Add a brief note only for a substantive change, an
unresolved ambiguity, missing evidence, or a substantial compression (roughly a
fifth or more of a section). When asked to explain edits, label each as a
correction, house-style choice, suggestion, or substantive change. Leaving good
writing unchanged is a valid result; say so in one line with the reason.

For recurring projects, maintain a style sheet when the user or project workflow
authorizes one ([style-sheet.md](references/style-sheet.md)). For disputed conventions, consult
[sources.md](references/sources.md) and current primary guidance. Never claim
comprehensive Chicago or certified ASD-STE100 compliance.
