# Migrating existing reports into the workbook

Old reports are usually organised by when work happened or by which script
produced them: a long README that grew by appending, an executive summary
rewritten from the top, a set of HTML pages each with its own style. The
workbook is organised by question. Migration means re-cutting that material
into one entry per question, without changing any result.

## Order of work

1. **Inventory.** List every distinct analysis in the old material, with its write-up, results folder, scripts, date and apparent status. One row per question, not per file. Note where two documents report the same question.
2. **Chapters.** Group the inventory into five to ten chapters by research question or line of work, not by folder or date. Propose the grouping to the user before creating chapters; it is the workbook's main structure and is costly to change later.
3. **Shared methods first.** Write the `methods` entries that many analyses cite (data products, preprocessing, atlases, cross-validation and inference conventions). Later entries link them instead of repeating them.
4. **Entries, oldest first within each chapter.** For each question, write one entry (procedure A in SKILL.md) with status `current`, `superseded` or `retracted` as the sources support. Migrating in date order lets `wb supersede` run as each replacement arrives.
5. **Backlog what remains.** Anything not migrated yet goes in its chapter's `backlog:` list (see SKILL.md), so the home page shows how much is left.
6. **Syntheses last.** Write each chapter's "Where this line of work stands" and the home page's "Where things stand" once the entries exist.
7. **Point the old documents at the workbook.** Only with the user's approval: add one line at the top of each old README or summary ("Superseded as the reader's account by workbook entry <slug>; kept as the technical record."). Do not delete old files or HTML sites; the user decides their fate.

## Rules

- **Numbers are carried, not recomputed.** Snap the TSVs and figures the old report used and render tables from them with `wbtable`. If the old prose gives a number that no file holds, quote it with its source in the log line ("answer taken from <README> §<heading>"), and warn in your report.
- **Do not upgrade the evidence.** If the old report said a choice was made after inspecting results, the entry is `exploratory`. If it is unclear whether a test was fixed in advance, use `exploratory` and say why in Caveats.
- **Supersession must be supported by the sources.** Mark `superseded` only when a source says so, or when a later analysis answers the identical question with an explicitly preferred design. When a judgement is needed (two analyses with different preprocessing both reported), leave both `current`, link them as `related`, and ask the user.
- **Split giant documents by question.** A heading in an old README that asks a new question becomes its own entry. A heading that checks, qualifies or re-cuts the parent's answer on the same data (a robustness check, a descriptive readout, a follow-up window) stays inside the parent entry, in Results or Caveats. When the brief you were given names the entries to write, follow the brief and list in your report the headings you would have split out.
- **Old README becomes the technical record.** Put its path in `record:` so the full detail stays one click away.
- **Interactive viewers stay where they are.** Link them in `viewer:` (a published URL) and mention their local path in the technical record. Do not copy viewer bundles into the workbook.
- **Log the migration.** First log line: `"<date> — Migrated from <source path>; first reported <original date>."` Set `date:` to the original report date, found in this order: a date in the report itself; the earliest dated document that reports the result (a review, a summary, a memory note); the source file's modification time. Say in the log which one you used. When migrating a supersession, pass the date it happened: `wb supersede <old> <new> --date <date>`.
- **Privacy.** Old reports may contain things the workbook must not: participant identifiers, per-participant tables, absolute paths, live share links with tokens. Leave them out. `wb build` enforces the patterns in `_workbook.yml`, but check by eye too.

## Checks before reporting

- `wb build` passes with no errors.
- Every old write-up in the inventory maps to an entry, or is listed in your report as intentionally not migrated, with the reason.
- Every entry's answer was checked against its snapped tables, not against the old prose alone.
