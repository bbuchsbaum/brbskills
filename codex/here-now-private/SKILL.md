---
name: here-now-private
description: Publishes research reports to here.now password-protected from the first upload, with resumable state, hosted-file hash checks and unauthenticated 401 probes. Use for private results or brain-map review sites.
compatibility: Python 3.10+ (standard library) and curl; a here.now API key in $HERENOW_API_KEY or ~/.herenow/credentials. Complements the vendor here-now skill.
---

# here.now private publishing

Use this for a results site that must stay private (analysis reports, neuromosaic or brain-map reviews, group
summaries). For public sites, custom domains, workspaces, Drives or other here.now features, use the vendor
`here-now` skill and its current docs instead; do not edit the vendor skill, because its installer overwrites it.

## Publish or update

```bash
python3 -I scripts/publish_private.py SITE_DIR --state STATE_DIR \
  --password-file NAME --display-name "Title" [--create-password] [--slug SLUG] [--probe PATH ...]
```

- `SITE_DIR` needs `index.html` at its root. Every non-hidden file under it is published; hidden paths
  (`.git`, `.DS_Store`, agent logs such as `.omc/`) are always skipped. Do not run tools from inside the site
  directory, and list its files before publishing.
- `STATE_DIR` belongs to the project, not the site. It holds `intent.json` (resume point) and `receipt.json`.
  After any failure, rerun the same command: it resumes from the saved step. Unchanged files are a no-op; changed
  files become a new version checked against the recorded live version.
- `--password-file NAME` reads `~/.herenow/NAME.password` (mode 0600). Reuse an existing file when the user wants
  the same password as an earlier site; `--create-password` generates one. Never print, log or post a password
  next to its link; tell the user which file holds it.
- `--slug` adopts an existing site the user owns (first run only). Default probes are the root plus every `.html`
  file.

## What the script guarantees
1. A new site gets a holding page, then the password, then a confirmed `password` access mode, before any
   content is uploaded. (The API cannot set a password on an unfinalized site.)
2. Uploads refuse to proceed if the site is not password-protected, or if the live version drifted from the
   recorded one or has a pending version.
3. After finalize, every hosted file's size and SHA-256 are read back through the owner API, each probe path
   returns 401 without credentials, and the site has no expiry.

If the API key is missing, stop and ask; never fall back to anonymous (public, 24-hour) publishing.

## Content and reporting
- Publish group-level results unless the user explicitly asks for individual-participant material; check pages
  and downloads for participant identifiers before publishing.
- Prefer self-contained pages (embedded figures) and summary tables as downloads.
- Report the site URL, the password file name, the version id, the verified file count and the probe results.
- If something unintended was published, republish without it and then delete the bad, non-live version with
  `DELETE /api/v1/publish/{slug}/versions/{versionId}` so it leaves the version history.
