# Display conventions

Read when writing an entry's Results or any figure, table or cross-link. Paths in
angle brackets are placeholders.

## Figures

`![Caption sentence.](assets/<figure name>.png){#fig-name}`: PNG or SVG, at most
about 1 MB each; the site zooms on click. Every caption says what is plotted,
the n, and what the error bars or bands mean.

## Tables

`{{< wbtable assets/<table name>.tsv cols="a,b,c" labels="A,B,C" caption="..." >}}`
renders a snapped TSV and always links the full file. Narrow tables keep their
natural width; wide ones scroll inside their column, with a visible cue.

- `cols`, `labels`: comma-separated; use `|` as the separator instead when a label
  contains a comma (`labels="Region|p (Holm, primary)"`).
- Numbers: `digits=3` (decimal places) or `sig=3` (significant figures) for every
  column; `fmt="acc=3 mean=s2 p_holm=p"` per column (`N` decimals, `sN`
  significant figures, `p` p-value style: three decimals, `< 0.001` below);
  `pcols="p,p_holm"` is shorthand for `p`. Columns of whole numbers are never
  padded with decimals.
- Rows: `where="family=alone & window=total_8s"` keeps rows meeting every
  condition (operators `= != < > <= >=`; join conditions with `&`). A filter that
  matches nothing is a build error. `max-rows=N` (default 25) shows the first N
  rows and says how many there are.
- Numbers go in `wbtable` tables, never in hand-made Markdown tables. A small
  Markdown table without numbers (which file to load for which purpose) is fine.

## Evidence in prose

Every number on the page must come from a snapped asset. Follow a number in
prose with an evidence link to the asset that holds it, written like
`[table](assets/<table name>.tsv)`. A study file that is not snapped is cited by
its study-relative path in a code span, never as a link: the site cannot reach
it. A number that exists only in an old write-up's prose is quoted with its
source named in the log.

## Links between entries

`{{< wbref slug >}}` renders the target's title; in running prose give link
text, `{{< wbref slug "4 mm betas" >}}`. Never link another entry by file path.
Shortcodes do not work inside a chapter's `backlog` items; use plain text there.

## Layout devices

- Variants of one result (two tasks, two windows): a `::: {.panel-tabset}` block
  with `###` tab headings. A tabset counts as one display item.
- Asides: `::: {.callout-note}`, sparingly.
- No raw HTML or JavaScript, and no executable code chunks: the workbook only
  reports what analysis scripts produced.
