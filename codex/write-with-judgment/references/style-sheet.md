# A compact project style sheet

Use an existing style sheet when present. For a one-off edit, keep choices internal. Create or update a persistent sheet only when the user's task or established project workflow authorizes it. Store accepted decisions, not a transcript of editorial deliberation.

Keep the sheet near the relevant project or document according to its workflow. Do not save an author's text or inferred personal preferences in an unrelated global location.

Use only the fields the project needs:

```yaml
project: Short project title
audience: Intended reader and assumed knowledge
purpose: What the reader should understand or do
english_variety: Preserve established variety, or specify one
governing_style: Venue instructions and applicable edition
citation_system: Existing or required system
edit_scope: Copyedit, rewrite, substantive edit, summary, or draft
terminology:
  - term: Exact term
    meaning: Distinction this term preserves
    avoid_for_this_concept: Any misleading substitute
protected_literals:
  - Exact command, identifier, or wording that must remain intact
voice:
  - Effective feature observed in the text or explicitly requested
decisions:
  - convention: Chosen treatment
    scope: Where it applies
    basis: User instruction, venue requirement, verified source, or editorial choice
exceptions:
  - treatment: Deliberate departure
    reason: Reader-facing purpose
    scope: Relevant section or passage
open_questions:
  - Only unresolved matters that materially affect the writing
```

Record an unusual spelling or purposeful repetition so later passes do not repeatedly undo it. Keep terminology definitions short enough to consult while writing. Do not fill every field for completeness.

Distinguish explicit choices from tentative inference. Resolve a current instruction against the current document; do not apply an old project preference to a different genre automatically. If a recurring preference is uncertain, preserve established usage and raise the issue only when it materially affects the result.
