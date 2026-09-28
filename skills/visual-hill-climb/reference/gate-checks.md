# Gate checks

The gate (`checks/run.sh <round>`) is the set of automated checks every build must pass
before a candidate is accepted. Failed candidates may appear on the local progress
page with their failures clearly labeled. Add checks for reproducible defects when practical.

## Rules

- **A check joins the gate only after it has failed on a build with the defect.** Use the previous failing build or a minimal negative fixture on a clean baseline.
  A passing previous build alone does not invalidate a useful new adversarial check.
- Every check prints one line per page × width ending `-> PASS` or `-> FAIL <evidence>`.
- Use numerical, interaction, or image comparisons appropriate to the defect.
  Account for rendering variability; a screenshot diff alone cannot judge design quality.
- Record the checker's hash (every check file) when the gate runs, alongside the PASS/FAIL counts.
- Never loosen a check to make a build pass. Change a budget only with a stated reason
  (e.g. "timings on this machine drift 2–3x under load"), and compare back to back instead.
- A probe that exercises the wrong path is worse than none: test the path the claim is about
  (a hash URL masks a storage test; a scripted `.click()` masks pointer-event bugs).

## Catalogue (pick what the domain needs)

| Kind | What it asserts | Notes |
|---|---|---|
| Overflow / clipping | nothing runs past its container at the swept widths (e.g. 256–1720 px) | sweep widths, not just 3 |
| Line / break quality | no lone operators or closers, no identifier split when a legal break exists | domain-specific grammar |
| Indent / alignment model | siblings share a column, children right of parents, wrapped rows in the declared column | check wrapped rows, not only line starts |
| Layout shift | initial layout-shift sum ≤ 0.05 | include a slow-font variant |
| Font fallbacks | block heights unchanged when web fonts are removed | the honest test of metric matching |
| Speed | load, FCP, longest task, observed blocking sum, resize cost | these fixed-window probes are not Lighthouse TBT |
| Contrast | WCAG ratios per theme × variant, including syntax/role colours | also role separation (ΔE) |
| Accessibility | landmarks, names, focus order, keyboard, reduced motion, forced colours | |
| Deep links / navigation | anchors land at the right offset, back/forward/reload keep the place | real input events |
| Print | no lost content, identity elements on page 1, sane page breaks | print from wide AND narrow windows |
| Page errors | no uncaught errors on load, resize, print, theme switch | cheapest, highest-yield check |
| Themes | every theme renders its own palette (no light leaks in dark) | |
| Page weight | bytes per page and per asset within budget | adopters care |
| Rendered vs declared | a visual property (dash, colour, visibility) holds in the rasterised output | rasterise at delivery dpi and measure; attributes alone cannot establish visibility |
| Overlay integrity | vector overlays (outlines, labels) do not lighten or recolour data pixels | rasterise with and without overlays and diff |
| Legend honesty | every legend stop / swatch matches the source scale or the sampled pixels it names | sample independently of the builder |
| Value fidelity | rendered colour = scale(value) at interior pixels; sign/hue on the right side | re-project from source data |
| Glyph ambiguity | no characters the chosen font renders ambiguously (e.g. `\|` as `l`) | cheap, catches recurring typos |
| Export staleness | shipped PNG/PDF are byte-identical to what the source produces now | also proves determinism |
| Determinism | re-running the build gives identical bytes (strip timestamps, pin PDF dates) | GPU renders may differ; say which outputs are deterministic |

`scripts/checks/cls.js` and `speed.js` are generic starting points; the rest are written for
the project as defects are found.

Check expectations need an independent basis; documented specification constants may
be shared, while implementation logic is not an oracle. Changing a check
after it fails is a correction: lead the notes with it and rerun every negative control (lessons #13).
Record the checker's hash when the gate runs, not when the build runs.

The bundled `cls.js` reports a sum of unexpected shifts in a short initial window,
not session-window CLS or a Core Web Vitals certification. `speed.js` reports local
load/FCP and observed long-task blocking in fixed windows, not Lighthouse TBT. Both
fail on empty inputs, missing files, unsupported observers, or runtime errors.
Thresholds are example budgets; choose task-appropriate budgets before the baseline.
