# cobidas import

Imported on 2026-09-30 from `~/Downloads/cobidas-skill-0.1.0.zip` at the user's
request. [Original file hashes](cobidas-original-SHA256SUMS) record the input,
not the revised bundle; the archive's contents were verified against them before
import. No license was supplied with the bundle.

The archive held the skill in a nested `cobidas/` folder beside bundle-level
files. The shared source is now `skills/cobidas/`. The bundle-level `README.md`,
`VALIDATION.md` and `examples/` were carried into that folder. The bundle-level
`install.py`, `SHA256SUMS` and `test-results.txt` were not carried in: this
repository generates its own Codex and Claude folders, per-bundle checksums and
ZIP downloads, and records its own test evidence. Generated folders share the
workflow and resources, with Codex UI metadata (`agents/openai.yaml`) only in the
Codex bundle.

## Review and repairs

- Helper (`scripts/cobidas.py`): reproduced and fixed RecursionError on long
  supersession or `depends_on` chains and exponential audit time on overlapping
  supersession; duplicate `--profile` values producing an unauditable
  `study.json`; owner-only (0600) output files; an audit digest that embedded
  absolute paths, so moving a project staled its drafts; a crash on an oversized
  non-event file; an import-time process-wide umask swap; tracebacks or vague errors for malformed records; schema
  patterns accepting a trailing newline; paragraph IDs able to close the
  provenance HTML comment; CRLF TSV output that broke LF-normalized checksums. All outputs use one atomic writer. 17 regression and
  fixture-drift tests added; no original test changed.
- The synthetic fixture was regenerated for the repaired helper; `.gitattributes`
  pins LF endings because the audit digest covers the helper's bytes.
- Entry point cut from 1,127 to 722 words (whole file; 679 body words per `check`) and the description from about
  480 to 207 characters, keeping all eight invariants; question-budget detail moved
  to `references/workflow.md`. The skill-level README is now a short overview.
- Scientific references checked against COBIDAS Appendix C and Tables D.1–D.7:
  corrected the claim that COBIDAS lacks ASL/DSC rows and the framing of
  Appendix C versions; added missing acquisition, slice-timing reference, FD-variant,
  CompCor/high-pass, HRF, autocorrelation, group-estimator, cluster-forming and TFCE,
  circularity, cross-validation and diffusion items. The skill is kept independent
  of this repository's other skills and fMRI conventions: integration guidance maps
  any existing workflow or provenance system, and host-packaging sources were dropped. FEAT grand-mean scaling now names the in-mask median. Two evaluation scenarios were added (FD definition mismatch,
  CompCor without its high-pass basis).

## Verification boundary

The skill's offline suite (`skills/cobidas/tests/test_cobidas.py`) runs in CI
with the other per-skill suites; its external JSON Schema check uses `jsonschema`
from `requirements-dev.txt`. Local synthetic tests and packaging checks are
evidence about the helper and portability, not proof of skill selection,
reporting completeness, or scientific validity. The source baseline is OHBM
COBIDAS MRI v1.0 (2016-05-19). Fresh end-to-end Codex/Claude evaluations remain
unrun.
