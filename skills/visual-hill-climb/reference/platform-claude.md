# Claude Code adapter

Use the same task-local HTML progress page and helpers as other environments.
Open it from disk and reload after updates. Critiques are embedded as plain text,
so no server, hosted artifact, or third-party script is required.

If an artifact or publishing tool is actually exposed, use it only within the
user's sharing authorization after inspecting the files to be shared. Consult its
current tool schema for limits; do not assume Claude Code includes an Artifact
tool. The local evidence remains authoritative. Do not prune recorded rounds to
fit an assumed hosting limit.

If fresh-context subagents are available and permitted, pass each critic its filled
prompt and evidence paths without the builder's reasoning. Use background execution
only when supported. Respect actual capacity and serialize expensive probes.
Collect complete critique files before updating the page. Missing sections need a
follow-up, not guessed scores. If delegation is unavailable, label self-review and
leave independent scores pending. External model services require existing scope
and authorization; they are optional, not a workaround for runtime limits.
