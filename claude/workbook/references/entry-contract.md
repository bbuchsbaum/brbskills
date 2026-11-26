# The entry contract

Read when creating or editing an entry, a chapter page or its backlog. The site
is generated from these fields and sections; `wb check` enforces them.

Contents: front matter · body sections · status lifecycle · chapter pages and backlog

## Front matter

Keep reference and path lists in one-line flow style (`[a, b]`) and `log` as a
block list (one `  - "..."` line per item), as the templates do; the tool edits
both.

| Field | Rule |
|---|---|
| `title` | Short noun phrase, at most 40 characters; it is the sidebar label. "WM transfer with 4 mm betas", not a question. |
| `question` | One sentence ending in "?", the question the entry answers. |
| `answer` | At most 70 words: the direct answer, the key estimate with its uncertainty and test, then one qualifier. "Pending." until there is a result. |
| `kind` | `analysis`, `data` (a data product), `plan`, `method` (a shared method), or `note`. |
| `status` | `planned`, `running`, `current`, `superseded` or `retracted` (see lifecycle). |
| `evidence` | Analyses only: `confirmatory` (test fixed before seeing outcomes), `exploratory` (choices made after looking), or `descriptive` (no inferential test). Required once current. |
| `date`, `updated` | ISO dates: first reported; last substantive change. |
| `chapter` | Must equal the chapter folder. |
| `categories` | Free tags. They appear in the provenance block and link to the catalogue filtered by that tag. |
| `plan`, `methods`, `supersedes`, `superseded_by`, `related` | Slugs of other entries. The page renders them as links with status pills, and the target pages list this entry under "Referenced by". |
| `code`, `outputs`, `record` | A path or a list of paths relative to `study_root`: scripts, results folders, technical records. Never absolute paths. |
| `jobs` | Cluster job identifiers, e.g. `["cluster 1234567"]`. |
| `viewer` | URL of an interactive viewer, if any. |
| `log` | Dated one-line changes, oldest first: `- "2026-11-26 — First reported."` |

## Body sections

Required level-2 headings, in this order:

- analysis: `Approach`, `Results`, `Interpretation`, `Caveats`
- data: `Contents`, `How it was made`, `How to use it`, `Caveats`
- plan: `Rationale`, `Design`, `Analysis plan`, `Decision rules`
- method: `Summary`, `Details`
- note: any

Extra sections (`## Next`, `## Notes`) may follow. Do not write a level-1
heading, a status banner, the question, the answer, or a Provenance section:
the workbook filter renders all of these from the front matter, which is what
keeps every page alike. Delete the `<!-- wb: ... -->` guidance comments once a
section is written; a section left empty renders as "Not written yet."

## Status lifecycle

```
planned ──► running ──► current ──► superseded
                           └──────► retracted
```

- `planned`: written down, nothing run. Usually a `kind: plan` entry.
- `running`: in progress; partial results allowed, shown with an "In progress" banner.
- `current`: the latest word on its question. Answer filled, sections written, evidence set.
- `superseded`: a later entry answers the same question better. Set by `wb supersede`; never delete the old entry.
- `retracted`: found to be wrong. Keep the page; add a log line saying why (the banner quotes it).

For a plan, `current` means the plan was executed; the analyses that cite it in
`plan:` appear on it automatically.

## Chapter pages and backlog

A chapter page (`analyses/<chapter>/index.qmd`) carries `wb-chapter: true`, an
`order`, and a two-to-five-sentence synthesis under "Where this line of work
stands", which the home page's chapter table quotes. Its entry lists are
generated.

Work that exists but has no entry yet (an old write-up awaiting migration, a
finished analysis nobody has written up) goes in the chapter's front matter:

```yaml
backlog:
  - "`results/old_analysis/README.md`: the earlier screen, not yet migrated"
```

The chapter page lists it under "Not yet in the workbook", the home page counts
it, and Open questions links it, so a partly covered chapter never looks
complete. Remove an item when its entry exists.
