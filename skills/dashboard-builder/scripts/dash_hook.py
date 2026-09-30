#!/usr/bin/env python3
"""Claude Code hook entry for the agent dashboard.

Reads one hook payload on stdin. Without a .dashboard/hub.json at or above the
payload cwd it exits at once. It never fails the agent: every error is logged to
.dashboard/hook-errors.log and the exit status is 0, except for intentional
deny/block JSON output and the experimental --watch-inbox wake-up (exit 2).

  dash_hook.py                 handle one hook event
  dash_hook.py --watch-inbox   async Stop hook: wake an idle session for a dashboard message
"""
import contextlib
import json
import os
import sys

ERROR_LOG_MAX = 64 * 1024


def find_hub(cwd):
    explicit = os.environ.get("DASHBOARD_DIR")
    if explicit and os.path.isfile(os.path.join(explicit, "hub.json")):
        return os.path.abspath(explicit)
    p = os.path.abspath(cwd)
    while True:
        d = os.path.join(p, ".dashboard")
        if os.path.isfile(os.path.join(d, "hub.json")):
            return d
        parent = os.path.dirname(p)
        if parent == p:
            return None
        p = parent


def log_error(hub, err):
    try:
        import traceback
        import time

        path = os.path.join(hub, "hook-errors.log")
        try:
            if os.path.getsize(path) > ERROR_LOG_MAX:
                with open(path, "rb") as f:
                    f.seek(-ERROR_LOG_MAX // 2, os.SEEK_END)
                    keep = f.read()
                with open(path, "wb") as f:
                    f.write(keep)
        except OSError:
            pass
        with open(path, "a", encoding="utf-8") as f:
            f.write(
                time.strftime("%Y-%m-%dT%H:%M:%S%z ")
                + "".join(
                    traceback.format_exception(type(err), err, err.__traceback__)
                )[-4000:]
                + "\n"
            )
    except Exception:
        pass


def load_dash():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import dash

    return dash


def watch_inbox(payload, hub):
    """Poll the session inbox while it is idle; exit 2 with the framed message to wake it."""
    import time

    dash = load_dash()
    h = dash.Hub(hub)
    sid = payload.get("session_id")
    if not isinstance(sid, str) or not dash.SID_RE.match(sid) or not h.exists(sid):
        return 0
    limit = float(os.environ.get("DASH_WATCH_LIMIT") or 7200)
    poll = float(os.environ.get("DASH_WATCH_POLL") or 2)
    sd = h.sdir(sid)
    with dash.locked(sd / ".watch.lock", blocking=False) as got:
        if not got:
            return 0  # another watcher already covers this session
        started = dash.now()

        def beat():
            dash.atomic_write(sd / "watch.json", json.dumps(
                {"pid": os.getpid(), "started": started, "heartbeat": dash.now(), "poll": poll}) + "\n")

        try:
            beat()
            with contextlib.suppress(Exception):
                dash.bump(h)
                dash.regen(h)  # the page can now say the idle session is wakeable
            return _watch_loop(dash, h, sid, sd, poll, limit, beat)
        finally:
            with contextlib.suppress(OSError, ValueError):
                if (dash.load_json(sd / "watch.json") or {}).get("pid") == os.getpid():
                    os.unlink(sd / "watch.json")
            with contextlib.suppress(Exception):
                dash.bump(h)
                dash.regen(h)


def _watch_loop(dash, h, sid, sd, poll, limit, beat):
    import time

    t0 = time.time()
    time.sleep(min(poll, 1.0))  # let the Stop hook finish recording turn_end
    while time.time() - t0 < limit:
        beat()
        s = dash.load_json(sd / "session.json") or {}
        if s.get("ended") or not (sd / "session.json").is_file():
            return 0
        if s.get("turn") == "active":
            return 0  # a new turn started; hooks deliver from here
        if dash.queued(sd):
            with dash.SessionEdit(h, sid) as ed:
                if ed.s.get("turn") == "active":
                    ed.changed = False
                    return 0
                text = dash.take_messages(ed, "rewake")
                if text:
                    # Confirmed by the next tool/Stop event; redelivered at the next prompt otherwise.
                    ed.s["rewake_pending"] = ed.taken
            if text:
                try:
                    sys.stderr.write(text + "\n")
                    sys.stdout.write(text + "\n")
                    sys.stderr.flush()
                    sys.stdout.flush()
                except BaseException:
                    dash.rollback_messages(h, sid, ed.taken)
                    raise
                return 2
        time.sleep(poll)
    return 0


def main():
    watch = "--watch-inbox" in sys.argv[1:]
    try:
        payload = json.loads(sys.stdin.read() or "null")
    except Exception:
        return 0
    if not isinstance(payload, dict):
        return 0
    cwd = payload.get("cwd")
    hub = find_hub(cwd if isinstance(cwd, str) and cwd else os.getcwd())
    if hub is None:
        return 0
    try:
        if watch:
            return watch_inbox(payload, hub)
        dash = load_dash()
        h = dash.Hub(hub)
        out, sid, delivered = dash.hook_output(h, payload)
        if out:
            try:
                sys.stdout.write(json.dumps(out) + "\n")
                sys.stdout.flush()
            except BaseException:
                dash.rollback_messages(h, sid, delivered)  # never emitted: queue them again
                raise
    except BaseException as err:  # never break the agent
        if isinstance(err, KeyboardInterrupt):
            return 0
        log_error(hub, err)
    return 0


if __name__ == "__main__":
    code = 0
    try:
        code = main()
        sys.stdout.flush()
        sys.stderr.flush()
    except BaseException:
        pass
    os._exit(code)
