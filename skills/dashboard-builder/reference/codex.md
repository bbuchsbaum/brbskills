# Codex integration

Read this when running the dashboard from Codex.

Codex sessions have no hook capture in this skill yet, so a Codex lane shows only the
narrative the agent records; the page marks its activity as not captured.

1. Join the project hub and keep the printed id for every later call:
   ```bash
   DASH join --agent codex --label "Short label"      # prints the session id
   DASH --session <id> init "Title" --goal "..." --task "..."
   ```
   Exporting `DASH_SESSION=<id>` in each shell command works too.
2. Record milestones, decisions, blockers, metrics and deliverables as in the main skill.
   Because tool activity is not captured, a short `DASH log` at meaningful boundaries is the
   user's only window into the work; keep it factual.
3. Messages from the page are printed by any `DASH` call for your session. Run
   `DASH --session <id> inbox` at milestones and before ending a turn, and treat what it prints
   as chat messages from the user.
4. Pause from the page cannot block Codex tool calls. If `inbox` shows a pause request, stop
   and report.
5. End with `DASH --session <id> status done` after verification, or `DASH --session <id> end`
   when leaving the lane.
