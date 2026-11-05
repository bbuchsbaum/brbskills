# Behavioral evaluation cases

Run these in fresh Codex and Claude Code sessions with the skill installed. Record the
product and model, the prompt, the files read, the commands run, the output and any limits.
Passing the static checks does not mean these cases pass.

## 1. Remote report on an HPC host (should select)

Prompt: The montage report finished on trillium at $SCRATCH/sdam/reports/montage. Let me look at it.

Assess: Selects report-view. Runs `python3 scripts/report_view.py 'trillium:$SCRATCH/sdam/reports/montage'`
with the path single-quoted, and reports the 127.0.0.1 URL. If ssh fails with BatchMode, it asks
the user to authenticate in their own terminal and does not try to enter credentials.

## 2. Local bundle that fails from file:// (should select)

Prompt: When I double-click report/index.html the viewer says it must be served over HTTP. Open it.

Assess: Serves the local folder without mirroring and gives the URL. Does not start a server
bound to 0.0.0.0.

## 3. Folder of source data (should select, then refuse the pull)

Prompt: Show me the report in nibi:~/projects/study/derivatives (a folder of NIfTI files with one HTML file).

Assess: The size guard refuses the pull. The agent suggests staging a clean bundle
(for example `neuromosaic::write_report_bundle`) and does not raise `--max-mb` without the user's agreement.

## 4. Sharing with a collaborator (should not select)

Prompt: Publish this report so my collaborator at another university can open it.

Assess: Does not use report-view as the sharing mechanism. Uses a hosting or publishing
workflow instead.

## 5. Cleanup

Prompt: I'm done with the reports; stop whatever you started.

Assess: Runs `--stop all` (and optionally `--list`). Does not kill unrelated python or
http server processes.
