# Maintaining this repository

Runtime instructions are in the selected `skills/*/SKILL.md`, not this file.
Change shared resources under `shared/`, then run `python3 tools/sync_shared.py`.
Run `python3 -m unittest discover -s tests -v` and `python3 tools/audit_bundle.py`.
R smoke tests and real agent evals are separate release gates; never report them
as passed unless their commands ran successfully. No subject data belongs in
this repository or its eval fixtures. Preserve standalone skill installation.
Do not add mandatory MCP, scheduling, or model-specific subagent dependencies.
