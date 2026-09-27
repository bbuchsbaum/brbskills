# fMRI Workbench import

Imported from the user-provided `fmri-workbench.zip` on 2026-09-27.

- Archive SHA-256: `39a231f8575bd186ab4ab7c9eb9c5a50085f869ef291dd2f68a4896c333b75b0`.
- 146 files, 456,181 uncompressed bytes; safe relative paths, no duplicate entries
  or symlinks. The ZIP contains no supplied checksum manifest.
- [Per-file inventory](fmri-workbench-original-SHA256SUMS) records hashes computed
  from the original ZIP; these establish import identity, not independent authenticity.
- The complete archive is retained under `collections/fmri-workbench/`, including
  its MIT license, design, shared resources, original validation receipts, 14 agent
  evaluation scenarios, tests, installer, and original plugin manifests.

## Modular packaging

The archive supplies five independently installable skills: `fmri`, `fmri-bids`,
`fmrireg`, `fmrigds`, and `neuromosaic`. They are exposed at `codex/<name>/` and
`claude/<name>/`, with a separate ZIP per skill and product. Runtime files stay
inside each skill; collection documents, evals, and build tools are not required
to use a downloaded leaf skill. The `fmri` coordinator requires whichever stage
skills the requested workflow uses; it does not install them automatically.

Instructions, scientific code, metadata, and licenses are preserved from the
archive. Codex bundles retain `agents/openai.yaml`; Claude bundles omit that
Codex-only file. Both carry the same portable `SKILL.md` and supporting resources.
Root sync refreshes collection-wide resources from `shared/` before generating
downloads. Root check rejects stale shared copies and duplicate skill names.

The original collection tools can still run from the collection directory.
For repository-wide packaging use the root tools; the retained plugin manifests
are upstream inputs, not evidence of native plugin validation or publication.

## Validation boundary

The archive's [validation report](../../collections/fmri-workbench/VALIDATION.md)
and `quality/` receipts describe its original authoring environment. Import-time
results are recorded below separately. No source-review claim is upgraded to a
live R API, scientific, or model-behavior result by repackaging.

No subject data, fitting, network analysis, global skill installation, or provider
evaluation is required by the local import checks. R compatibility smokes, the
full package-to-package round trip, real-data validation, and fresh Codex/Claude
behavior evaluations remain separate, unrun gates for this import.

### Import checks executed on 2026-09-27

- All 146 original files match their recorded archive hashes byte for byte.
- All 42 imported Python tests passed, including isolated leaf installation,
  explicit-consent state, stale-input detection, and inventory/profile checks.
- All 18 repository tests passed, including new collection discovery, duplicate
  name rejection, shared-resource drift/refresh, portable metadata preservation,
  and isolated per-skill packaging cases.
- The collection structural audit and root synchronization check passed for all
  six repository skills. Eleven imported Python files passed syntax parsing.
- All 12 imported R files passed `Rscript --vanilla` syntax parsing. R emitted
  startup locale warnings and fell back to `C`; no R analysis code was executed.
- All ten new skill/product ZIPs passed extraction, full checksum inventories,
  internal-link validation, license retention, and Codex-metadata separation.
  In isolated directories, every bundled state helper displayed help, created a
  synthetic blocked plan, and rejected that plan for execution readiness. Neither
  a sibling skill nor collection-level shared files were present for these checks.

The installed Codex skill-creator `quick_validate.py` was also tried on `fmri`.
It rejects the `compatibility` key, which is an optional field in the
[Agent Skills specification](https://agentskills.io/specification). The imported
field is retained. Repository and collection validators accept and check the
standard field; the installed Codex helper did **not** pass. Native product loading
remains untested, and hosted CI has not run.

Reproduce from the brbskills root:

```bash
python -m pip install -r requirements-dev.txt
python scripts/skills.py check
python -m unittest discover -s tests -v
python collections/fmri-workbench/tools/audit_bundle.py
python -m unittest discover -s collections/fmri-workbench/tests -v
python scripts/skills.py package fmri fmri-bids fmrireg fmrigds neuromosaic
```
