# Codex deployment

Use the session's exposed subagent controls. Request `gpt-6-luna` with `low`
reasoning for detectors and `gpt-6-astra` with `medium` reasoning for the editor.
These model/effort pairs are user choices; do not replace them with a different
model because its role name sounds suitable.

When the tool exposes `model`, `reasoning_effort`, and `fork_turns`, supply the
requested model and effort explicitly and use `fork_turns: "none"`. Give the
agent its packet and reference contents or readable paths. Avoid fixed-model
roles such as a scout or expert when they override the requested settings.
Use only argument names exposed by the current runtime.

The parent coordinates assignments and applies edits. If it is already running
Astra medium, it may act as editor. Otherwise, spawn one Astra medium editor and
return the recheck findings to that same agent. A prose instruction cannot change
the parent's model. Detectors receive fresh context for the recheck.

Run within the available concurrency slots, reserving the coordinator's slot
where the runtime counts it. Queue additional assignments and release completed
threads where supported. Do not launch parallel CLI processes to evade the cap.
Confirm the selected model and effort from runtime metadata when available;
report any mismatch. Request an authorized alternative if the requested setup
cannot run.

Codex also supports custom agent files with `model` and
`model_reasoning_effort`. Installing one is unnecessary when per-spawn controls
are available. This skill does not alter user or project configuration.

Source checked 2026-11-02: [official Codex subagent documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents).
The live runtime's available models, parameters, and limits determine execution.
