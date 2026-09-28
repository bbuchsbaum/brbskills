# visual-hill-climb import

Imported on 2026-09-27 from `~/.claude/skills/visual-hill-climb` at the user's request.
`~/.codex/skills/visual-hill-climb` was a symlink to that directory, not a separate
implementation. Both installed paths were inspected; neither installation was
changed. [Original file hashes](visual-hill-climb-original-manifest.json) record the
input, not the revised bundle. No license was supplied in the source skill.

The shared source is now `skills/visual-hill-climb/`; generated Codex and Claude
folders share workflow/resources, with Codex UI metadata only in its own bundle.

## Review and repairs

- Scoped discovery to iterative visual critique, shortened the entrypoint, and
  moved setup details into a conditional reference. Retained non-web/scientific
  fidelity paths and fixed-content constraints.
- Bounded rounds, explicit pending/self-review states, and no automatic persistent
  memory updates. Removed assumed Artifact APIs, cache-version selection, implicit
  hosting, rigid branch requirements, and extra model-process fallbacks.
- Reproduced the original gate returning exit 0 after its first command failed;
  the runner now propagates failure and rejects missing required specimens. Fixed
  bundled check paths and empty input handling.
- Reproduced historical-table contamination (score 99 accepted). Score parsing now
  requires the rubric's first Scores table, complete dimensions in [1,10], and all
  required narrative sections. Malformed critiques do not replace published data.
- Captures refuse overwrite and validate names/paths. Prepared PNGs retain original
  bytes and receive structural/CRC/compressed-stream checks. Capture conditions and
  reviewer roles are part of the comparison contract.
- Progress page works offline with embedded inert critique text, no CDN/fonts,
  explicit pending states, full score axis, and empty-image handling. Keyboard
  slider and mobile layout were exercised in the browser.
- Renamed the metric claims to initial layout-shift sum and fixed-window blocking
  sum: these helpers do not calculate standard session-window CLS or Lighthouse TBT.
  The distinction follows [CLS documentation](https://web.dev/articles/cls).
  The browser launcher uses Playwright's default pinned browser unless an explicit
  compatible test-browser override is supplied, consistent with
  [Playwright launch guidance](https://playwright.dev/docs/api/class-browsertype#browser-type-launch).

An independent read-only reviewer exercised synthetic fixtures and identified
three additional gaps: score-only truncated reviews counted as complete, capture
conditions were omitted from the frozen comparison contract, and signature-only
PNG validation admitted corrupt images. Those paths received fixes and regression
coverage. Historical anecdotes in `reference/lessons.md` remain attributed source
material; the underlying original climb artifacts were not supplied.

## Verification boundary

See the bundled `tests/VALIDATION.md` for commands, results, and limits. Local
synthetic tests and packaging checks are evidence about helpers and portability,
not proof of skill selection, aesthetic improvement, accessibility conformance,
or scientific validity. Fresh end-to-end Codex/Claude evaluations remain unrun.
The new CI workflow is authored here; a hosted result requires a future push/run.

## Installed update — 2026-09-27

Installation preflight found a nested Git directory carried over from the original
local skill. The packaging inventory now excludes `.git`, with a regression test.
The imported source metadata was preserved outside the skill source so it cannot
be staged as an embedded repository. Installed updates retain a backup and preserve
the existing Codex-to-Claude symlink.
