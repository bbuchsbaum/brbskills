---
name: workbook
description: "Maintain a project's analysis workbook, a Quarto site with one structured entry per analysis. Use when an analysis is planned, finished, rerun, superseded or retracted, when asked where things stand, or to set one up."
metadata:
  version: "0.2.0"
  reviewed: "2026-11-26"
---

# Analysis workbook

The workbook is the project's catalogue of analyses: one entry per question,
grouped into chapters, each entry with the same anatomy (question, answer,
brief methods, results, interpretation, caveats, provenance) and the same look.
The site is rebuilt from the entries alone. An analysis is not finished until
its entry is current and `wb build` passes.

It replaces ad-hoc report pages, executive summaries and append-only READMEs as
the reader's account. Results-folder READMEs stay as technical records (every
table, check and job), linked from the entry's `record:`. Heavy interactive
viewers stay where they are, linked in `viewer:`.

## Layout and commands

```
workbook/
  _workbook.yml   settings: study_root, privacy patterns, glossary terms, limits
  index.qmd       home: project at a glance, "Where things stand", chapters, findings
  catalogue.qmd, open.qmd, changes.qmd, glossary.qmd, about.qmd
  analyses/<chapter>/index.qmd          chapter page: synthesis, generated lists, backlog
  analyses/<chapter>/<slug>/index.qmd   one entry; its assets/ hold snapped outputs
  analyses/methods/                     shared methods and data products
  _tools/ _extensions/ _templates/      copied from the skill; refresh with upgrade
  _wb/ _site/ .quarto/                  generated
```

Run `Rscript workbook/_tools/wb.R <command>`, written `wb` below:

| Command | Does |
|---|---|
| `wb ls` | List chapters and entries with status and slug. Start here. |
| `wb new <chapter> <slug> [--kind K] [--title T]` | Create an entry (kinds: analysis, data, plan, method, note). |
| `wb chapter <id> --title T [--order N]` | Create a chapter. |
| `wb snap <slug> <file>... [--as NAME]` | Copy outputs into the entry's `assets/` with source, SHA-256 and date. Paths are relative to `study_root`. |
| `wb unsnap <slug> <asset>...` | Remove a snapped asset. |
| `wb supersede <old> <new> --reason T [--date D]` | Mark `<old>` superseded on both sides; the reason appears in its banner. |
| `wb build` | Index, render, check. Must end with 0 errors. |
| `wb check [--sources-only]` | Lint without rendering. |
| `wb serve [--port N]` | Serve the site at http://127.0.0.1:4321/ for reading. |

Requirements: Quarto 1.4 or later; R with `yaml`, `jsonlite` and `digest`;
Python 3 for `wb serve`. `<skill>` below is the folder holding this file.

- New workbook: `Rscript <skill>/template/_tools/wb.R init <project>/workbook --title "<Project> workbook"`, then set the privacy patterns in `_workbook.yml`, propose chapters to the user, create them, and build.
- Newer skill version: `Rscript <skill>/template/_tools/wb.R upgrade <project>/workbook` refreshes tools, extension and templates. Add `--pages` to move the home, utility and chapter pages to the current templates while keeping their project text.

## The entry contract

Read [references/entry-contract.md](references/entry-contract.md) before
creating or editing an entry or chapter page: it lists every front-matter field,
the required sections per kind, the status lifecycle and the chapter backlog.
The essentials:

- `title` is a short sidebar label; `question` is one sentence; `answer` (at most 70 words) gives the result, its estimate, uncertainty and test, and one qualifier.
- `status`: planned → running → current → superseded or retracted. `evidence` (analyses): confirmatory, exploratory or descriptive.
- An analysis has `## Approach`, `## Results`, `## Interpretation`, `## Caveats`. Never write the banner, question, answer or Provenance section yourself: the filter renders them from the front matter.

## Procedures

Begin with `wb ls`, and read the chapter page and any entry on the same
question. Then decide:

| Situation | Action |
|---|---|
| A new question, or a design nobody has used for it here | New entry |
| The same analysis rerun, corrected or extended, same question and design | Update in place |
| A different design that answers the same question better | New entry, then `wb supersede` |
| The result was wrong | `status: retracted` and a log line giving the reason |
| A technical sub-check that changes no answer | The technical record, not a new entry |

**New analysis.** `wb new` (slugs kebab-case, never dated or renamed; ask the
user before creating a chapter). Fill `question` and the provenance fields;
keep `status: running` while work continues. When results exist, `wb snap` only
the figures and tables the page shows, never a file with participant
identifiers or individual records. Write the sections, then set `answer`,
`evidence`, `status: current`, `updated` and a log line. If the result changes a
chapter's account or a headline, rewrite the chapter synthesis or the home
page's "Where things stand". `wb build`; fix every error, and fix or explain
each warning. Report the entry's path and answer.

**Update in place.** Re-snap changed outputs (`wb check` flags a snapped source
that changed as STALE), revise the sections and the answer, bump `updated`, log
what changed and why, build.

**Supersede.** Only when the sources or the user prefer the new design for the
same question; a rerun reported alongside the old one is `related`. When unsure,
keep both current, link them as `related`, and ask. Never edit the old entry's
results; say in the new entry's Interpretation how the answers differ.

**Plans and backlog.** Write a `kind: plan` entry before running anything
confirmatory; the analysis that executes it sets `plan:`. Work that exists but
has no entry yet goes in its chapter's `backlog:` list.

**Migration.** Read [references/migration.md](references/migration.md) before
moving old reports in: one entry per question, numbers carried unchanged,
supersession only where the sources say so.

## Writing and display

Read [references/writing.md](references/writing.md) before writing the first
entry in a session, and [references/display.md](references/display.md) when
writing Results, tables, figures or links. In brief: answer first and plainly;
brief methods; at most three figures, tables or tabsets; every number from a
snapped asset through `wbtable` or an evidence link; links between entries with
`{{< wbref slug "text" >}}`; the glossary's terms and no synonyms.

## Privacy and viewing

The workbook holds group-level results only. `_workbook.yml` lists forbidden
patterns (participant identifiers, home paths); a match anywhere in the sources
or the rendered site fails the build. Share `_site/` only when the user asks,
through an access-controlled host, never a public one.

Tell readers to run `wb serve` (or `quarto preview workbook`), not to open
`_site/index.html` as a file: browsers then block the page scripts, so search,
the contents highlight and the remembered theme stop working.

## Do not

- Edit `_wb/`, `_site/`, `_extensions/`, `_tools/` or `_templates/` by hand.
- Delete or rewrite superseded entries, or rename slugs.
- Copy files into `assets/` by hand; `wb snap` keeps their provenance.
- Build standalone HTML report pages for an analysis; write an entry.
- Leave a finished analysis `running`, or report a result that is not in the workbook.
