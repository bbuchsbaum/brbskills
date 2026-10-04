# Validation record — 2026-10-04

Consolidates three writing skills (write-with-judgment, sciwrite, technical-prose)
and restates the ASD-STE100 skill's rules as conditional judgments for
agent-facing text. See references/sources.md for provenance.

## Evidence boundary

Explicit-invocation trials of cases 1–6 in tests/evaluation-cases.md ran in two
fresh Claude Code subagents (Opus 5.5), three cases each, against the generated
`claude/write-with-judgment` bundle. Agents were told not to open tests/ and
received only the prompt and passage. Because each agent ran three cases, the
cases were not fully independent. These are bounded development checks. No
no-skill or predecessor-skill baseline was run, case 7 (selection) was not run,
and no Codex session was used. They do not establish improvement over ordinary
prompting or correct automatic selection.

## Results (first run, pre-fix version)

| Case | Result | Notes |
| --- | --- | --- |
| 1 Tool description | Pass | Replaced idiom, made the skip/abort branch explicit, kept "may abort", invented no threshold, listed open questions after the text. |
| 2 Hedged status | Pass | "Nightly job may have failed: last heartbeat 02:14, no completion record since." |
| 3 Two levels | Pass, weak | Kept each result at its level, the null as a null, p, and the hedge. Tightened little: the revert test blocked tightening edits the user had asked for. |
| 4 Discussion opening | Pass | Led with the finding; kept Lee & Park on the adult claim and the direction limit; flagged the cut cited background (about 30%). |
| 5 README | Pass | Removed praise words, separated an implementation detail from a guarantee, left a visible placeholder for validation behaviour, invented no benchmark. |
| 6 Literary non-edit | Pass | Unchanged, with a one-line reason. |

## Changes made from the trials

- Revert test: an explicit request to tighten or restyle now counts economy and
  rhythm as gains (case 3).
- Load triggers for decisions.md and examples.md, and a concrete trigger for
  verification.md, replacing "consequential".
- Citations travel with their claims; cutting a cited claim is reported. Missing
  facts become visible gaps. An unchanged result is reported in one line.
- technical.md: idioms may hide a real question; corrected the "unless" gloss;
  open questions are listed when the source does not settle one reading; output
  order for pasteable text.
- scientific.md: the procedure behind a result (for example, aggregation) is part
  of the claim; handling of untested explanations in results.

A fresh-context review then led to these changes:
- removed remaining field-specific rules (a brain-mapping "localization" check, an
  experimental-psychology list of anchors) and one author's pet words;
- restored two STE concerns (two-part-of-speech words, stacked hedges) and the
  on-request concern table;
- added poetry to genres.md;
- resolved the "concrete" vs creative-brief and compression-threshold
  contradictions;
- added a contents list to examples.md;
- cut SKILL.md by moving the details of the anchor script and reviewer step to
  verification.md.

The fixed version has not been re-run.

## Local verification

`python scripts/skills.py sync` and `check`, the 24 root repository tests, and
`tests/test_compare_anchors.py` (10 tests) passed. Source URLs in
references/sources.md resolved (HTTP 200) on 2026-10-04.

## Self-application pass — 2026-10-04

The skill was applied to its own SKILL.md and references as a targeted rewrite
(no rule, condition, or force intentionally changed). Edits: one name for the
edit-scope concept ("permitted edit"); "substantial compression" at roughly a
fifth in both SKILL.md and scientific.md; several multi-action sentences split;
opaque phrases glossed ("contrast formula", "implied safeguard", "otherwise");
a dangling modifier in the summary example and a stray comma in sources.md fixed.
`compare_anchors.py` flagged only the intended changes. A blind reviewer given
the originals and the candidates found five meaning drifts introduced by the first
draft (a widened definition of "brief", a weakened frequency claim, a broadened
safeguard rule, a moved quotation condition, and a split instruction), all reverted.
This was a text-only pass; the behavioural cases were not re-run.

## Judgment and scope revision — 2026-10-04

This revision changes several editorial instructions, rather than only their
wording. It separates critique from rewriting, makes verification depend on the
requested task, limits terminology consistency to technical referents, and
reports compression by the significance of omissions. Scientific introductions
are described by function rather than paragraph count; evidential verbs by the
relationship they assert. Technical guidance now allows distinct qualifications
and useful generic instructions. The sandbox example preserves the source's
unspecified disposal mechanism.

A separate read-only reviewer (gpt-6-astra) compared the brief, HEAD originals,
and candidates without the editor's rationale or tests. It found that repository
delivery guidance and technical.md's pasteable-output rule could override the
review-only mode. Both were explicitly scoped to drafting or revision. This was
a textual review, not a behavioral evaluation.

### Bounded forward check

One fresh Codex-managed subagent (gpt-6-astra) received only the skill path and
the prompts/passages for cases 8, 9, and 11. It read the generated Codex SKILL.md,
technical.md, and verification.md. It did not receive acceptance notes, diffs,
or the editing rationale. All three cases shared that one context. The parent
judged the outputs against the recorded acceptance criteria.

| Case | Result | Evidence |
| --- | --- | --- |
| 8 Critique | Pass | Identified the mean-to-every-clinic inference, suggested bounded conclusions or clinic-level analysis, and returned findings rather than a replacement paragraph. |
| 9 Retention | Pass | Kept the disposal condition and timing without adding an actor, mechanism, permanent retention guarantee, or subdirectory policy. |
| 11 Qualifications | Pass | Kept possibility, the subset of first-time users, and the unestablished benefit for returning users. |

Exact outputs:

**8:** “Every clinic benefited” does not follow from a fall in the overall mean:
some clinics could have unchanged or longer waits. The second sentence
acknowledges that the clinic-level evidence needed for this claim is missing.
Analyse changes by clinic or limit the conclusion to the overall mean. Also, the
timing alone does not establish that the booking system caused the decline.

**9:** Runs the script in a temporary workspace. When the run ends, files that
were not saved to `/results` are discarded.

**11:** The reminder may help some first-time users complete registration, but
the pilot does not establish a benefit for returning users.

These checks cover three decisions only. Cases 1–7, 10, and 12 were not rerun;
there were no fresh standalone Codex or Claude Code sessions, selection trials,
or baseline comparisons. The full product evaluation in CONTRIBUTING.md remains
unrun for this revision. Subsequent entrypoint edits condensed wording and
clarified repository delivery; the three cases were not repeated after those
edits. No general improvement or cross-model reliability is established.

### Local checks

Skill-creator validation, root `sync` and `check`, all 24 root tests, the 10 anchor
comparison tests, and `git diff --check` passed. The anchor utility's code was
unchanged. Both product downloads were regenerated from source; these checks
establish packaging and helper behavior, not editorial quality.
