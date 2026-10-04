# Verify preserved meaning

Scale this process to the material. For a sentence, compare directly. For a consequential paragraph, use a small claim table or a few reader questions. For a long document, track vulnerable claims and transitions rather than serializing every sentence.

## 1. Establish what preservation means for this task

For faithful editing, check the source and revision in both directions: Does the revision add anything unsupported? Does it lose anything the task requires? For summarization, require support for each retained claim and coverage of the requested essentials; full equivalence is not the objective. For substantive revision, assess changed claims against the brief and evidence and identify material changes. For new drafting, compare claims to the brief and sources.

Preserve assertions as assertions and attributed views as attributed views. Do not silently endorse a source's unverified claim by stripping its attribution. Do not treat a known falsehood as protected merely because the author wrote it; handle it according to the permitted edit.

## 2. Attach qualifications to claims

When useful, make a compact working record:

| Claim or action | Actor / population | Conditions and exceptions | Force and evidence | Quantity / comparison / citation |
| --- | --- | --- | --- | --- |
| What is asserted, recommended, or required? | Who or what does it concern? | When and under what scope? | Fact, possibility, recommendation, obligation, inference, or reported view? | What values and sources belong specifically to it? |

Keep citations in the same record as their claims. Matching citation strings is insufficient: a citation may have migrated to a stronger or unrelated sentence. Check quotations against their sources when altering surrounding syntax, punctuation, or ellipses could change their meaning. Preserve source wording inside direct quotations unless a permitted change is explicitly marked.

Inspect these dimensions whenever they appear:

- **Roles:** actor, action, object, beneficiary, cause, target, and direction of comparison.
- **Logic:** negation, conjunction, alternatives, quantification, conditions, exceptions, and necessary versus sufficient conditions.
- **Force:** possibility, permission, capability, obligation, probability, frequency, certainty, and attribution.
- **Scope:** time, population, subset, unit of analysis, adjustment set, operational definition, and reference group.
- **Evidence:** association versus causation, observed versus inferred, planned versus completed, exploratory versus confirmatory.
- **Literals:** names, values, signs, units, equations, thresholds, identifiers, code, URLs, and citations.

## 3. Ask what the reader would take away

Choose two to five questions tailored to the passage, then answer them from each version independently:

- Who is expected or permitted to do what?
- What conditions must hold, and what happens if they do not?
- Which result was observed in which population and comparison?
- What conclusion follows, and which conclusion remains unsupported?
- What uncertainty, limitation, or disagreement remains?

Compare answers rather than superficial wording. An edit that preserves all the numbers may still assign the result to the wrong group. An edit that preserves every modal word may attach them to the wrong action.

For an uncertain equivalence, try a counterexample: **Could the original be true while the revision is false? Could the revision be true while the original is false?** A concrete scenario often exposes a lost exception or a strengthened claim. Treat this as a fallible editorial test, not a formal proof.

For literary work, also ask what the reader anticipates, notices, or is left to infer. Semantic preservation includes perspective and intended ambiguity where the brief makes them important.

## 4. Use literal comparison as triage

Run the optional utility from this skill's directory:

```bash
python3 scripts/compare_anchors.py original.md revised.md --json
python3 scripts/compare_anchors.py original.md revised.md --lock 'robust regression' --lock 'MAX_RETRIES'
```

Compare files that contain only the relevant source and revision, excluding editorial commentary. The utility uses Python's standard library and makes no network calls or edits. It reports changes in selected numeric expressions, literal code, link destinations, protected strings, and a modest inventory of semantic markers. Read the output contexts and inspect the actual passage.

Treat every finding as **review needed**, never automatically as an error. Converting a numeral to a word or changing a source URL can be justified. Missing findings do not establish equivalence. The extractor is deliberately limited: it is not a full Markdown parser, language parser, citation resolver, equation checker, or unit-conversion system. It cannot identify every name, synonym, hidden assumption, omitted argument, or changed relationship. Direct quotations and citation-to-claim attachment require separate review.

A successful run returns status 0 even when it reports changes. Input errors return status 2. Never use the exit status as a publication or semantic-correctness gate. Read the explicit limitation in its output.

## 5. Separate editing from review when warranted

For a consequential revision or a difficult unresolved judgment, ask an independent reviewer to examine the **brief + original + candidate**. Withhold the editor's rationale. Ask for specific changed implications, unsupported additions, essential omissions, and losses of effective voice, supported by the relevant spans. Do not ask only whether the candidate reads better.

If no independent reviewer is available, reread the original and candidate in a separate comparison pass. Recheck any affected passage after repairing a defect. Stop when material issues are resolved; do not generate an endless sequence of aesthetic variants.

When reporting verification, describe what was checked and any remaining uncertainty. Never call model judgment a proof, a clean inventory a semantic pass, or a small pilot a demonstrated improvement over another editor.
