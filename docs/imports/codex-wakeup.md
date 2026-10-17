# Codex wakeup packaging record

Date: 2026-10-17.

Source: user-provided partial `tools/codex-wakeup` Python listing and description
in the authoring conversation. The supplied helper used `fcntl` locking, a saved
prompt, `codex queue`, per-thread cron markers, and rotated logs. It included
machine/project defaults and a private release-directory fallback. Its `main()`
was truncated in the paste; the complete original file, prompt, and reported
successful-delivery logs were not supplied. No live installation was imported.

The new standalone `codex-wakeup` skill preserves the transport and scheduling
idea while making the project, thread UUID, executable, and run duration explicit.
The helper is a rewrite, with durable outstanding-token state, end-of-turn
acknowledgement, bounded queue timeout, expiry, disabled setup, and exact-marker
cron preview/apply/remove. It uses only Python's standard library. No global
installation, cron mutation, or live queue submission is part of packaging.

Mote remains authoritative for work; the helper records transport lifecycle only.
The skill complements the independently authored `mote-peer-work` protocol and
does not modify it. Both product bundles contain the same source; the Claude
bundle can manage Codex alarms but supplies no Claude delivery backend.

Local CLI help advertised the queue interface on `codex-cli 0.163.0`. The
[validation record](../../skills/codex-wakeup/tests/VALIDATION.md) distinguishes
offline tests from the still-required real-host trial. The original success
reports do not qualify the new acknowledgement protocol.
