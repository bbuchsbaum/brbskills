# Local helper: exact behaviour and limits

Requires Python 3.10 or later; runtime uses only the standard library. All commands operate locally. No network requests, MRI processing, scheduler submission, database, MCP server or LLM API is used. The optional `jsonschema` package enables an additional independent schema test; it is not needed to run the helper or the remaining tests.

## Initialization and configuration

```bash
python <skill-dir>/scripts/cobidas.py init --project . --profile task --profile glm
```

Creates `reporting/cobidas/` in the project and refuses to overwrite an existing directory; never store project records inside the installed skill. `study.json` declares the workspace, study identity and scopes. Edit the initial acquisition/analysis labels, assign modules per scope and add scopes for different cohorts, protocols or analysis revisions. `workspace` is relative to the reporting root; the initial `../..` resolves to the project root. Changing it changes the interpretation of evidence paths and the audit digest. Keep it coordinator-owned and trusted.

Profiles (duplicate `--profile` values are ignored): `core`, `fmri`, `task`, `glm`, `group`, `rest`, `connectivity`, `prediction`, `rsa`, `naturalistic`, `structural`, `diffusion`, `multi_echo`, `longitudinal`, `surface`. `core` always applies. `glm` implies `task` and `fmri`; `task`, `multi_echo` and `naturalistic` imply `fmri`; `rest` implies `fmri` and `connectivity`; `connectivity` implies `fmri`. For fMRI RSA/decoding, explicitly include `fmri` plus `rsa`/`prediction`, because those analysis families are not inherently restricted to fMRI.

Profiles use OR selection: a field is expected when its scope kind matches and at least one listed profile is active. Keep first-level GLM and group analyses in separate analysis scopes when their membership and operations differ. Not every operation applies to every analysis branch: record genuine applicability reasons. An omitted applicable operation should instead be a known negative (`performed: false`).

`catalog.json` is a project-local copy of the bundled 89-field catalogue. Freeze it with the project. Its `required` flags and profile rules are local review requirements, not published COBIDAS designations. Edit a local catalogue only deliberately, with review and version control; narrowing it just to get a clean audit defeats reporting. A full official audit needs the separate Appendix D mapping.

## Record import

```bash
python <skill-dir>/scripts/cobidas.py record --root reporting/cobidas --file stage-record.json
```

Accepts one JSON object or an array. Required scientific values, successful states and reviewer names are never filled automatically. The helper adds only an absent globally unique event ID, import timestamp, empty relationship arrays, and hashes of accessible local evidence. Supply `recorded_at` for an existing trustworthy record when available; an import timestamp is not an execution or decision timestamp. Keep actual execution/decision times inside the original receipt or an explicit event `notes`/decision description. Do not backdate a reconstructed record.

Use the examples in `assets/record-examples.json` as shapes, not study facts. They contain `REPLACE_...` placeholders and nonexistent example paths. They require editing and import-time stamping before satisfying the event schema. The helper does not detect every disguised placeholder: that is an agent/reviewer responsibility.

Evidence requires a relative `path`, `kind` and `locator`; the helper computes SHA-256 and rejects a supplied mismatching hash. Absolute paths and resolved paths outside the workspace, including escaping symlinks, are rejected. Files larger than 64 MiB are not hashed: reference a small verified manifest or use the existing provenance system instead. A manifest hash establishes the manifest's identity, **not** the identity or existence of its transitive data objects. A source locator is retained but not interpreted or validated against file semantics.

Immutable remote URI + version pointers are accepted structurally, but the offline helper cannot verify them and blocks those facts from declarative builds. Use an authorized local snapshot or a legitimate local verification receipt produced by a trusted existing system; do not claim the helper fetched the remote source.

Each event is published as a separate complete JSON file using same-directory temporary writing and atomic hard-link creation. Concurrent workers with distinct IDs do not append to a shared file. Existing IDs are never overwritten. A multi-record import is prevalidated but not a database transaction: an unexpected I/O error or concurrent duplicate may leave some records committed. Inspect IDs and import the missing records; do not erase history. Filesystems without reliable local hard-link/atomic semantics are unsupported. Have one coordinator write configuration, audits and prose. Each generated output file is written atomically, but a set of outputs is not a multiwriter-safe transaction. Files are created with the process umask permissions and LF line endings.

## Audit semantics

```bash
python <skill-dir>/scripts/cobidas.py audit --root reporting/cobidas
python <skill-dir>/scripts/cobidas.py audit --root reporting/cobidas --strict
```

The helper checks record shapes; existing scope/field identities; explicit same-property supersession; cycles; local evidence byte identity; current actual heads; required structured membership keys; producing activity status, validation evidence and dependencies; and correspondence to active profiles. A producing activity must share the fact's explicit analysis scope. Materialize a thin, correctly scoped receipt from shared provenance rather than pointing an analysis fact at an unrelated activity.

The helper **does not** recompute sample counts, prove all scope members are homogeneous, inspect image headers, validate a JSON pointer, compare a claimed parameter with a model object, infer whether a confound was fitted, or judge a not-applicable reason. `scope.members` checks a nonnegative integer, unit and cited manifest; the agent must validate the underlying membership and count. General scientific `value` objects are deliberately extensible rather than pretending every method can be fully schema-validated. For partially recovered fields, `missing_details` records absent subcomponents while `value` holds only established ones. The resulting `known_incomplete` status remains a strict-audit gap, although supported subdetails may be cited in a draft. The agent must actually enumerate missing components; the helper cannot discover them.

Current facts with two unsuperseded heads are a conflict—even with identical values. Planned records do not close actual gaps. Known negative facts are valid values; unknown fields stay unknown. A failed or unvalidated activity cannot support an executed-methods claim. Preserved failures do not, by themselves, prevent reporting a different successful branch. Inference-only facts never support declarative prose. For retrospective records, no receipt means execution remains unverified, even with honest human testimony; use a qualified narrative and gap report rather than fake a receipt.

`audit.json` includes eligible facts and full local coverage. `gaps.md` and `coverage.tsv` expose unresolved fields. Exit 0 means the command ran, **not** the report is complete; `--strict` returns 1 when local gaps/integrity errors remain. Invalid input or operational errors return 2. A strict pass remains only a local coverage/integrity result, not OHBM certification or semantic verification.

The digest includes helper/schema fingerprints, configuration, catalogue, valid events, invalid-event fingerprints and source-check results. It does not depend on where the project is located: evidence errors are reported with project-relative paths, so a moved or re-cloned project audits to the same digest when its contents are unchanged. It intentionally changes when evidence bytes or relevant history change, even if a text draft looks unaffected. Evidence must be quiescent during audit/build: this is not an atomic filesystem snapshot, a cryptographically authenticated ledger or protection against a malicious actor modifying both evidence and hashes.

## Evidence-bound draft assembly

```bash
python <skill-dir>/scripts/cobidas.py build --root reporting/cobidas --draft draft.json
```

The **agent** writes sentences and binds each paragraph to current fact IDs. Paragraph IDs must match `^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$`. The helper does not author scientific prose or choose citations. It re-audits, requires the exact digest, rejects integrity errors, and checks that every declared fact reference is current and eligible. It then writes `methods.md`, `supplementary_methods.md`, `claim-evidence.tsv`, `unreported.md`, `draft.snapshot.json` and refreshed audit/coverage/gaps files, all from that snapshot.

Partial drafts are permitted and visibly labelled; known claims need not wait for an unrecoverable coil detail. Unknown/conflicting facts cannot be smuggled in through their IDs. However, a paragraph might cite a valid fact while adding an unsupported sentence: the helper cannot detect this. It also cannot determine whether every subdetail within a cited structured fact appears in the text. Reverse-audit prose, exact values, units, scope, citations and evidence manually or with a separately evaluated verifier. Never treat a passed build as human approval.

## Tests and maintenance

```bash
python -m unittest discover -s <skill-dir>/tests -v
```

The executable tests use fabricated JSON records only. They test the helper, not fMRIPrep/AFNI/R integration, numerical correctness of MRI analysis, real-study reporting completeness, or Claude/Codex behaviour. `references/evaluation.md` specifies the separate agent-level evaluation. Re-run both kinds of evaluation after changes; do not substitute a clean helper test run for actual agent testing.
