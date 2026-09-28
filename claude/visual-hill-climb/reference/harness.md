# Harness setup and helper contracts

Requires Python 3.10+, Bash, and (for web helpers) Node.js 20+ with Playwright
and a compatible installed Chromium. Non-web builds use the project's render tools.

## Layout and setup

Choose an absolute writable `HARNESS` path owned by this task. Copy `scripts/`
from this skill into it (including `checks/`), copy
[hillclimb.example.json](../assets/hillclimb.example.json) to `hillclimb.json`,
[run.sh.example](../assets/run.sh.example) to `checks/run.sh`, and
[the page](../assets/progress-page/index.html) to `artifact/index.html`.
Resolve the skill location first; do not assume an installation path.

```text
harness/
  hillclimb.json, RUBRIC.md, RESUME.md, FROZEN.md (when needed)
  build.sh, specimens/, fixtures/       # project-specific; not supplied
  scripts/                             # bundled helpers, with scripts/checks/
  checks/run.sh                        # adapt required specimen filenames
  out/v0/, shots/v0/                    # immutable build and lossless PNGs
  critiques/v0-visual.md, ...           # one completed file per critic
  changes-v0.txt, logs/, audit/          # notes, exit status, critic scratch
  artifact/index.html, data.js, data.json, img/, critiques/
```

Run commands from the harness, or export `HARNESS` explicitly. Node resolves
Playwright from the copied scripts' ancestors. `PLAYWRIGHT_MODULE` may name an
absolute installed module path. Use the installed version's bundled Chromium;
helpers never scan for a newer cache, attach to a browser, or install anything.
An explicit `PLAYWRIGHT_EXECUTABLE_PATH` is only for a compatible installed test
browser, never system Chrome or a user profile. Record versions and overrides.
Python helpers use the standard library. Image preparation copies lossless PNGs;
there is no ImageMagick/sips dependency. Large images increase page size.

Before browser work, run the environment's browser-policy audit if available,
select one allowed browser backend, and establish ownership. Audit again after
closing task-owned contexts/browsers. A blocked audit or missing dependency means
browser evidence is unavailable, never passed. Do not clean other sessions.

## Config and sequence

`dims` is a nonempty array of unique dimension names; `critics` maps stable IDs to
labels. Use the same dimensions for every critic, choosing only applicable ones.
`shots` is a nonempty array with unique `name` IDs and optional display `label`.
IDs use letters, digits, `_` and `-`, starting with a letter or digit.
For web captures each shot also needs a relative `file` under `out/<round>/` and
`vp` (a named viewport or width/height object). `dark` sets preferred color scheme;
it does not test a site's theme toggle. `wait` is a nonnegative delay in ms; add
project-specific readiness checks for async content. Files with URL fragments
are not supported by capture; use project tests for routed/live applications.

```bash
bash build.sh v0                         # supplied by the project
bash checks/run.sh v0                    # retain output AND nonzero status
node scripts/shoot.js v0                 # web targets only
bash scripts/prep_shots.sh v0
python3 scripts/update_data.py v0 --title Baseline --status 'Review pending' \
  --changes-file changes-v0.txt
# After complete critique files arrive:
python3 scripts/update_data.py v0 --no-images --status 'Review complete'
```

For non-web work, skip both Node capture and browser gates. The project's build
writes every `<name>-fold.png` (detail) and `<name>-full.png` (whole artifact) to
`shots/<round>/`. Use suitable project checks for figures, print, or slides.
The bundled web gate is a starting example, not a universal acceptance gate.

Capture and image preparation refuse existing round destinations. Failed captures
may leave partial evidence; diagnose it and use a new ID. Preparation validates
all configured PNGs before copying. `update_data.py` is a **single-writer** command:
wait for a critic to finish, then update serially. It validates all critiques before
writing, atomically replaces each data file, and embeds plain-text critiques in
`data.js` for offline reading. The JSON/JS pair is not a joint transaction; reload
after the command completes. It does not copy screenshots (`--no-images` allows an absent
image set; otherwise all prepared images must exist).

Open `artifact/index.html` directly; reload after updates. No server or CDN is
needed. Missing reviewers are shown as pending and do not produce an overall
mean. The page does not infer gate acceptance from scores; put the real gate
status in notes/status. Do not publish private source paths or evidence by default.
