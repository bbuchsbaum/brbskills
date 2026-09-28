# Validation record — 2026-09-27

This record distinguishes helper evidence from untested model behavior.

## Executed locally

- **14 offline regression tests passed** in the source and in each independently
  extracted Codex/Claude ZIP. They cover contaminated/malformed/truncated scores,
  pending reviews, frozen capture settings, path escapes, missing/corrupt images,
  immutable image preparation, publication preservation on validation failure,
  missing gate specimens, early gate failures, and empty web-check input.
- **Browser smoke passed** on macOS: capture of filenames needing URL encoding,
  overwrite refusal, PNG preparation, positive initial-window checks, runtime-error
  and unsupported-observer negative controls, offline/empty/pending/complete page
  states, inert markup, keyboard slider, and 390/1440px light/dark layouts. No
  external requests or uncaught page errors occurred in the progress-page test.
  Desktop/light and mobile/dark screenshots were visually inspected. This is not
  a comprehensive accessibility audit.
- Playwright 1.62.1 was exercised with the existing Chromium 140.0.7339.186 via an
  explicit test-browser override, then with its matching Chromium 151.0.7922.34
  installed only in task-local temporary storage. The latter checks the default
  pinned-browser launch path. Browser ownership audits ran before/after testing.
- Independent read-only review used real synthetic helper invocations. Its three
  evidence-integrity findings received fixes; a separate rerun confirmed rejection
  of truncated critiques, changed capture conditions, and corrupt PNG fixtures.
  The review found no residual blocker in that bounded scope.
- Repository sync/check, skill frontmatter validation, 20 root tests, 41 Alliance
  offline tests, 42 fMRI Workbench tests, collection audit, 14 existing lme4 static/
  algebra checks, ShellCheck, and both ZIP packages passed. The lme4 validator is
  not an R runtime or statistical qualification test.

## Reproduce

From the repository root (Python 3.10+, Node.js 20+, Bash):

```bash
python3 skills/visual-hill-climb/tests/test_helpers.py
shellcheck skills/visual-hill-climb/scripts/prep_shots.sh skills/visual-hill-climb/assets/run.sh.example
# Requires installed Playwright and its Chromium; run local browser-policy audits first/after.
node skills/visual-hill-climb/tests/browser_smoke.cjs
python3 scripts/skills.py check
python3 scripts/skills.py package visual-hill-climb
```

`PLAYWRIGHT_MODULE` can select an absolute installed module directory. Optional
`VHC_EVIDENCE_DIR` retains browser logs/screenshots; otherwise the test creates a
unique temporary evidence directory. It uses only synthetic local inputs, starts
no server, and closes its own contexts/browser on success and failure.

## Limits

- PNG checks establish chunk/CRC/compressed-stream integrity and expected byte
  count. They do not prove every decoder accepts a file or that its content is
  correct. Browser rendering provides separate evidence for the web specimens.
- Critique validation establishes required structure and valid numbers, not the
  quality, truth, or independence of the prose. The parent must verify those.
- Fresh end-to-end Codex/Claude sessions, automatic trigger selection, aesthetic
  quality gains, scientific claims, Windows behavior, and hosted CI remain unrun.
  [Evaluation cases](evaluation-cases.md) specify those future behavioral checks.
- Recorded original-climb anecdotes were not independently reconstructed.
  Description length/word count and successful packaging do not measure effectiveness.
