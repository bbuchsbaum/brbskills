# Validation record

Commands run from the repository root unless stated otherwise.

## brbskills import revision — 2026-09-30

**56 helper tests passed, none skipped** (39 original, 17 added for repaired defects
fixture drift and LF output; no original test was changed):

```bash
python -m unittest discover -s skills/cobidas/tests -v
```

Also passed: `python scripts/skills.py sync` and `check` (description 207 characters,
body 679 words, 106 lines; local links resolve; Claude and Codex bundles match their
sources); the repository test suite (24 tests). `examples/make_demo.py` regenerated
the fixture into a fresh directory, and an audit of the committed fixture reports
the same shape as before: two draft paragraphs, one unused eligible fact,
**56 unresolved local fields** (one partially known HRF record) and 0 integrity
errors. `audit --strict` exits 1 on that fixture, as intended.

Scientific reference text was checked against the COBIDAS MRI v1.0 report
(Appendix C and Tables D.1–D.7), fMRIPrep documentation and Crossref DOIs. Items
recalled but not rechecked against a primary source are marked "verify" in the text.

## Original bundle — 2026-09-29 (as supplied)

The source bundle reported 39 passing tests, compiled Python, parsing JSON, resolving
links, an 89-group local catalogue and a tested non-destructive installer. The
installer is not part of this repository, which generates its own downloads.

## Not established by these tests

No real Claude Code or Codex session was run with this skill. Host discovery,
automatic triggering, factual recovery by an LLM, context cost and real-study
manuscript accuracy remain to be evaluated with the 20 adversarial scenarios and
hard-failure criteria in `references/evaluation.md`.

No package-specific BIDS/fMRIPrep/AFNI/FSL/SPM/R parser is claimed. No actual study
was audited against every official Appendix D row; the official checklist file is a
template. Structural checks and evidence hashes do not verify semantic entailment,
membership counts, source truth, scientific validity, data-release authorization or
genuine investigator approval.

The fixture's synthetic records describe states such as "successful" only to
exercise the receipt contract; no human data, MRI processing or numerical fitting
was performed. Atomic event publication is tested on a normal local filesystem, not
every HPC/NFS/object-store configuration. Multi-record imports and multi-file
manuscript writes are not transactions; one coordinator owns configuration, audit
and prose output.
