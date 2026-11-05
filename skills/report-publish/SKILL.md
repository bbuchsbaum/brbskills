---
name: report-publish
description: "Publish an HTML report folder (local or on an ssh host) to a private reportbox archive with per-project passwords, an index and version history, and return the link. For sharing with reviewers; not for private viewing."
metadata:
  version: "0.1.0"
  reviewed: "2026-11-05"
---

# Report publish

reportbox is a self-hosted Cloudflare archive of static HTML reports. Each project has
an index at `/p/<project>/`, a `latest/` alias and immutable report versions. Reviewers
type the project password once (it is remembered for 30 days), or use a share link that
skips the password. Use this skill when someone other than the user must see a report.
For the user's own quick look at a remote report, use a local viewer such as `report-view`.

Requirements: the `reportbox` CLI (one stdlib Python 3.9+ file, `cli/reportbox.py` in the
reportbox repository), already configured on this machine with `reportbox setup` or
`REPORTBOX_URL`/`REPORTBOX_TOKEN`. Check with `reportbox ls`. If it is not configured,
stop and ask the user. Never ask for, print, or store the admin token yourself.

## Publish

```sh
reportbox ls                                   # projects; confirm the target exists
reportbox publish PATH --project P --title "..." [--notes "..."] [--source "..."]
```

- `PATH` is a report folder (with `index.html`, or exactly one `.html`) or an `.html` file.
  It may be `HOST:PATH` on any ssh host; single-quote remote variables, e.g.
  `'trillium:$SCRATCH/study/report'`. ssh never prompts, so if it fails, ask the user to
  authenticate in their own terminal.
- Point at a clean report folder, not a data directory. For neuromosaic, render into its
  own folder or stage one with `neuromosaic::write_report_bundle(report, dir)`. If the
  default `--max-mb 500` guard refuses the folder, fix the folder rather than raising the limit.
- Write a specific title (analysis, contrast, version) and short notes on what changed:
  they become the index entry reviewers scan. `--source` defaults to `host:path`; prefer a
  git SHA or job ID when you have one.
- Report the printed `report:` and `index:` URLs. Only unchanged files are deduplicated;
  every publish creates a new version, and earlier versions stay listed.

## Projects and access

Create a project only when the user asks for a new audience or study:
`reportbox project create NAME --title "..."` prints a generated password **once**. Give it
to the user; do not write it into files, commits, chat messages to third parties, or memory notes.

- Share link: `reportbox link create P --label "who it is for" [--days N]`. Anyone holding
  the link gets in until it expires or is revoked (`link list`, `link revoke P ID`).
- New password: `reportbox passwd P` (signs everyone out). `reportbox signout P` signs
  everyone out without changing it.
- Remove a version: `reportbox rm ID`; reclaim storage later with `reportbox gc`.

Changing passwords, revoking links, deleting versions or projects, and creating share links
for new people all change who can see research results. Confirm them with the user first.

## Announcing

When the user wants others notified, post the index or report URL to the agreed channel
(Slack, email). Never put the password in the same message as the link; send it separately
or rely on a share link instead.

## Data rules

Reports go to a third-party host (Cloudflare), behind the project password. Publish only
reports the user intends to share, and never participant-identifiable data. Reports are
treated as trusted content: their JavaScript runs unsandboxed, so never publish HTML from
third parties.
