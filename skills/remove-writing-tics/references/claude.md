# Claude Code deployment

Use **Haiku 5.5** (`claude-haiku-5-5`) for both detector scans and **Opus 5.5**
(`claude-opus-5-5`) for editing. No Claude effort override is requested; preserve
the runtime's configured effort. Verify the resolved model when metadata permits.

Claude Code's per-invocation Agent `model` accepts family aliases. Use `haiku`
and `opus` only when they resolve to the requested 5.5 versions in this session;
provider mappings and parent-model inheritance can change that resolution.
Do not put a full model ID into a field that accepts aliases only.

For exact version selection, custom subagent definitions accept full model IDs
in their `model` fields. Supply the detector/editor instructions and catalogue
explicitly; a skill folder alone does not register these subagents. Prefer an
existing correctly configured agent or session-scoped definitions. Claude Code
supports session definitions through `--agents` when launching a session, with
each role specifying `description`, `prompt`, and `model`. Use the installed
client's documented controls; do not start a second session merely to bypass a
restriction in the current one or silently install global agents.

If the existing session cannot select the requested versions, explain what
configuration or authorized substitution is needed before running those roles.
An Opus 5.5 parent may edit directly; otherwise use one Opus 5.5 subagent and
resume it for the final corrections. Give detectors fresh, limited context and
read-only duties. No worker needs to delegate or change files.

Queue assignments within the session's concurrency limit, with at most 20 active
detectors. Use the available wait/completion mechanism rather than repeated
polling. Do not increase the configured limit as part of a prose edit.

Sources checked 2026-11-02:
[subagent controls](https://code.claude.com/docs/en/sub-agents) and
[model IDs and aliases](https://code.claude.com/docs/en/model-config).
Availability remains account-, provider-, and client-dependent.
