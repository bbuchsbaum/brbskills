# Verification record

Checked 2026-10-06 against rMVPA 0.1.3, source commit
`fd7ac599476ae9128487a8879e3774e47145dcb1`, built from a clean Git archive into
a temporary R library. R 4.5.1 on macOS arm64; neuroim2 and sda available.
The user's older 0.1.3 installation was left untouched.

## Executed evidence

- `tests/run_examples.R`: all five examples passed, extracted directly from the
  reference Markdown. Checked matrix/image round-trip alignment, separate CV
  labels, a regional classifier with 48 prediction rows, descriptive RSA,
  banded-ridge prediction shape/finite values, and a retained global pattern fit.
- `scripts/inspect_runtime.R`: no-argument and help modes, valid exported symbols,
  and an absent symbol tested; the latter reports a clear error and exits 2.
  Invoked by absolute path from outside the skill directory.
- System skill validator: passed. Entrypoint has a 197-character description and
  approximately 540 words; these are size measurements, not quality evidence.
- Root unit tests: 24 passed. Alliance offline tests: 41 passed. Workbench tests:
  42 passed plus its bundle audit. lme4 structure/algebra validator: 14 passed.
  ShellCheck passed. These are repository regression checks, not rMVPA tests.
- Independent explicitly invoked Codex forward checks: decoding, RSA null scope,
  and pattern confirmation; see [forward results](forward-results.md) for artifacts,
  authoring corrections, and scope. They do not measure automatic skill discovery.

Bundle verification passed: source synchronization, root check, independent ZIP
packaging, checksum verification, and extracted-folder validation for both products.
Both share the same instructions/resources; only Codex includes `agents/openai.yaml`.

The source examples and forward evaluations are small synthetic checks. They do
not qualify the package's numerical algorithms, permutation calibration,
whole-brain performance, native datasets, or implicit skill selection. Claude Code
execution, a no-skill comparison, and the remaining behavioral scenarios have not
been run. No cross-model effectiveness claim is made. The more specialized routes
(domain adaptation, ReNA, ITEM, plugins, and group confirmation) are source/help
guided; the five examples do not execute those families.

Reproduce the examples with R, rMVPA, neuroim2 and sda installed:

```sh
Rscript --vanilla scripts/inspect_runtime.R mvpa_model rsa_model pattern_model
Rscript --vanilla tests/run_examples.R
```

Run from this skill directory; `run_examples.R` also resolves its files when
called by absolute path from another working directory. Use `R_LIBS_USER` or an
equivalent isolated library configuration to test a pinned source installation.
No user-library changes are required.

The source-reviewed REMAP default-path limitation is documented in the cross-domain
reference. It is a traced data-dependency finding, not a measured bias/calibration
study or a package repair. rMVPA source was not changed by this work.
Uncommitted changes appeared in the external rMVPA checkout during authoring;
they are outside this frozen-source validation and were left untouched.
