# Codex adapter

Open the task-local progress page with the available desktop opener, or give its
absolute clickable path if opening fails. The page works from disk, including
critiques; reload after updates. Hosting requires existing user authorization.

If fresh-context delegation is available and permitted, give each critic only its
filled prompt, rubric, user constraints, notes, immutable build, and evidence
paths. Do not fork the builder's conversation. Honor the runtime's actual capacity;
run critics sequentially when needed. Use tools and argument names exposed in the
current session, not assumed API fields. Critics own only their output directory.

Do not start separate CLI/model processes to bypass unavailable delegation or
concurrency limits. Fall back to clearly labeled self-review or record a blocker
if independent review is essential to the user's acceptance. Never invent scores
for a missing or truncated critique.
