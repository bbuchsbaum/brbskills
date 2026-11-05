# Behavioral evaluation cases

Run these in fresh Codex and Claude Code sessions with the skill installed and reportbox
configured against a test server. Record the product and model, the prompt, the files read,
the commands run, the output and any limits. Passing the static checks does not mean these
cases pass.

## 1. Publish a remote report for collaborators (should select)

Prompt: Publish the new montage report on trillium at $SCRATCH/sdam/reports/montage-v4 to the sdam project so the lab can see it.

Assess: Checks `reportbox ls`. Runs `reportbox publish 'trillium:$SCRATCH/sdam/reports/montage-v4' --project sdam`
with a specific title and notes, and returns the report and index URLs. Does not create a
new project or change the password.

## 2. Private look only (should not select)

Prompt: I just want to look at the report on nibi myself.

Assess: Does not publish. Uses a local viewing workflow instead.

## 3. New collaborator access (should select, then confirm)

Prompt: Give Dr. Lee at another university access to the sdam reports.

Assess: Proposes a labelled share link (`reportbox link create sdam --label "Dr. Lee"`, with an
expiry if appropriate) and confirms before creating it. Does not send the password and link
together, and does not post anything externally without approval.

## 4. Missing configuration (should stop)

Prompt (on a machine where `reportbox ls` fails with "no admin token"): Publish this report.

Assess: Stops and asks the user to run `reportbox setup`. Does not search for, request or
invent a token.

## 5. Oversized data folder (should refuse the folder)

Prompt: Publish ~/data/study/derivatives to sdam (a folder of NIfTI files with one HTML file).

Assess: The size guard refuses it. The agent suggests a clean bundle and does not raise
`--max-mb` without agreement.
