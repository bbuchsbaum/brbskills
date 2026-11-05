---
name: report-view
description: "View an HTML report rendered on a remote ssh host or in a local folder: mirror it into a local cache, serve it on 127.0.0.1, and open a browser. Private viewing only; not for sharing or publishing."
metadata:
  version: "0.1.0"
  reviewed: "2026-11-05"
---

# Report view

Use this to look at an HTML report (neuromosaic, Quarto, R Markdown, pkgdown or
any static site) that was rendered on a headless or remote machine, such as an
HPC login node, a cloud VM or a lab server. Nothing is uploaded to a third party.
If someone else needs to see the report, use a hosted site instead.

Requirements on the viewing machine: Python 3.9+, `rsync`, `ssh`, and a
`~/.ssh/config` alias or `user@host` for the remote host. The remote host needs
only `sh` and `rsync`.

## Command

Run the bundled script from this skill's directory:

```sh
python3 scripts/report_view.py HOST:PATH         # any ssh alias or user@host
python3 scripts/report_view.py --host HOST PATH  # same
python3 scripts/report_view.py PATH              # local file or folder: serve only
python3 scripts/report_view.py --list            # cached copies and running servers
python3 scripts/report_view.py --stop [all|DIR]  # stop servers this tool started
python3 scripts/report_view.py --prune DAYS      # delete cached copies older than DAYS
```

Options: `--max-mb N` (default 500; refuse larger pulls), `--port P`, and
`--no-open` (print the URL without opening a browser). The URL goes to stdout;
diagnostics go to stderr.

`PATH` may be an `.html` file or a folder containing `index.html` or exactly one
`.html` file. `~` and environment variables such as `$SCRATCH` are expanded
**on the remote host**. Single-quote such paths so the local shell leaves them
alone: `'trillium:$SCRATCH/study/report'`. The whole folder containing the report
is mirrored to `~/.cache/report-view/<host>/<remote path>`; set `REPORT_VIEW_CACHE`
to change the location. Running the command again re-syncs the folder and reuses
the running server.

## Workflow

1. **Locate a clean report folder.** Find the exact remote path from the render log,
   the job script, or a remote `ls`. Prefer a folder that holds only the report and
   its companion files. For neuromosaic, render `index.html` into its own folder, or
   stage one with `neuromosaic::write_report_bundle(report, dir)`. If the size guard
   refuses a folder of source data, point at a clean bundle instead of raising
   `--max-mb`.
2. **Run the command** and give the user the printed `http://127.0.0.1:<port>/...`
   URL. Serving over HTTP covers reports that load companion files and fail from
   `file://`, including neuromosaic `assets = "bundle"`. Self-contained reports
   also work.
3. **If the agent runs on a headless machine**, use `--no-open`. Tell the user to
   forward the port (`ssh -L PORT:127.0.0.1:PORT host`) or to run this skill on their
   own computer.
4. **Clean up** when the user is finished: `--stop all`. Prune old copies
   occasionally, for example `--prune 14`.

## Connection failures

ssh runs with `BatchMode=yes`, so it never waits for a password or MFA prompt.
If the host cannot be reached without one, the script exits and says so. Ask the
user to authenticate once in their own terminal (for example `ssh HOST true`, or the
site's connection helper). A `ControlMaster auto` and `ControlPersist` entry for the
host in `~/.ssh/config` lets later calls reuse that session. Never type, store or
request credentials yourself.

## Rules

- Servers bind to `127.0.0.1` only; never expose them on other interfaces.
- `--stop` stops only PIDs this tool recorded that are still its own serve process.
  Do not stop other web servers or browsers.
- The cache can be regenerated. Prune deletes only inside the cache, and skips
  copies that are being served.
- Remote paths containing shell control characters are refused. Treat report
  folders as trusted local content; the server does not sandbox the report's
  JavaScript.
