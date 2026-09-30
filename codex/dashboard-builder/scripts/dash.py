#!/usr/bin/env python3
"""Agent dashboard hub: sessions, narrative progress, messages and a local page.

One hub per project lives in <project>/.dashboard/. Every agent session in the
project is a lane; Claude Code hooks (dash_hook.py) record ground truth, and
these commands record the narrative. The page (index.html) reads data.js from
disk, or talks to `dash.py serve` for two-way messaging.

Hub: --dir, else $DASHBOARD_DIR, else the nearest ancestor .dashboard/hub.json,
else (init only) <git toplevel or cwd>/.dashboard. The folder must be named .dashboard.

Session: --session, else $DASH_SESSION, else $CLAUDE_SESSION_ID, else the session
whose in-flight Bash command (seen by the hook) is this very dash.py call, else the
only live session. `init` creates a new session when none matches.

  dash.py init "Title" --goal "..." [--context "..."] [--task "title|detail"]... [--force]
  dash.py join --agent codex [--label "..."]          print a new session id
  dash.py task ID STATUS [--note "..."]              STATUS: todo doing done blocked skipped
  dash.py add-task "title" [--detail "..."] [--after ID]
  dash.py ask "question" --default "what I'll do if you don't answer"
  dash.py answer QID "answer"
  dash.py block "what is stuck" [--needs "..."]
  dash.py unblock BID [--note "..."]
  dash.py deliver PATH [--label "..."] [--note "..."]
  dash.py metric NAME VALUE [--total N] [--unit "..."] [--good up|down]
  dash.py status on_track|at_risk|blocked|done [--note "..."]
  dash.py log "message"
  dash.py show [--json] | path | open | sessions | inbox | end
  dash.py send SID "text" [--kind answer --qid Q1]
  dash.py serve [--open] | stop | url | render
  dash.py install-hooks [--scope user|project] [--settings PATH] [--dry-run] [--uninstall] [--with-rewake]

Every call for a session prints messages the user sent from the dashboard that the
agent has not seen yet. Treat them like chat messages from the user.
"""

import contextlib
import fcntl
import json
import math
import os
import re
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
SCRIPT = Path(__file__).resolve()
STYLE = Path.home() / ".config" / "dashboard-builder" / "style.md"
NAME = ".dashboard"
SCHEMA = 2
TASK_STATES = ("todo", "doing", "done", "blocked", "skipped")
OVERALL = ("on_track", "at_risk", "blocked", "done")
SID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
PAGE_MARKS = (
    re.compile(r"<!--\s*dashboard-page v(\d+)\.(\d+)(?:\.(\d+))?(\s+placeholder)?\s*-->"),
    re.compile(r'<meta\s+name="dashboard-page"\s+content="agent-dashboard (\d+)\.(\d+)(?:\.(\d+))?()"'),
)

LOG_KEEP = 200
EVENTS_SHOW = 300
EVENTS_ROTATE = 5000
TESTS_KEEP = 50
FILES_SHOW = 40
FILES_KEEP = 500
INBOX_SHOW = 50
ATTENTION_KEEP = 10
SESSIONS_SHOW = 16
TEXT_MAX = 4000

STALL_AFTER = 600
ENDED_AFTER = 6 * 3600
PENDING_WINDOW = 30
CONFLICT_WINDOW = 2 * 3600
CONFLICT_LIVE = 30 * 60
POST_WINDOW = 24 * 3600
POST_SCAN = 40
ENDED_SHOW = 24 * 3600
GIT_TTL = 10
MOTE_TTL = 20
MOTE_TIMEOUT = 3
REGEN_DEBOUNCE = 1.0
BODY_MAX = 16 * 1024
IDLE_EXIT = 2 * 3600

EDIT_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")
READ_TOOLS = ("Read",)


class DashError(Exception):
    """A user-facing failure; the CLI prints it and exits 1."""


def die(msg):
    raise DashError(msg)


# ---------------------------------------------------------------- time, io


def iso(t=None):
    t = time.time() if t is None else t
    return datetime.fromtimestamp(t).astimezone().isoformat(timespec="milliseconds")


def now():
    return iso()


def epoch(ts):
    """ISO-8601 string to epoch seconds; None when unknown."""
    if not ts or not isinstance(ts, str):
        return None
    try:
        s = ts.strip().replace("Z", "+00:00")
        # fromisoformat before 3.11 accepts only 3 or 6 fraction digits.
        m = re.match(r"^(.*T\d\d:\d\d:\d\d)(\.\d+)?(.*)$", s)
        if m and m.group(2):
            frac = (m.group(2)[1:] + "000000")[:6]
            s = f"{m.group(1)}.{frac}{m.group(3)}"
        d = datetime.fromisoformat(s)
        if d.tzinfo is None:
            d = d.astimezone()
        return d.timestamp()
    except (ValueError, TypeError):
        return None


def local_iso(ts):
    e = epoch(ts)
    return iso(e) if e is not None else None


def atomic_write(path, text, mode=0o644):
    path = Path(path)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(tmp)
        raise


def load_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def dump(obj):
    return json.dumps(obj, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


@contextlib.contextmanager
def locked(path, blocking=True):
    """Exclusive flock on `path`. With blocking=False, yields False if held elsewhere."""
    with open(path, "a") as lk:
        try:
            fcntl.flock(lk, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
        except BlockingIOError:
            yield False
            return
        try:
            yield True
        finally:
            fcntl.flock(lk, fcntl.LOCK_UN)


def tail_lines(path, n):
    """The last n lines of a text file without reading all of it."""
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            end = pos = f.tell()
            buf = b""
            while pos > 0 and buf.count(b"\n") <= n:
                step = min(65536, pos)
                pos -= step
                f.seek(pos)
                buf = f.read(step) + buf
            if end == 0:
                return []
    except OSError:
        return []
    lines = buf.decode("utf-8", "replace").splitlines()
    if pos > 0:
        lines = lines[1:]  # first line is partial
    return lines[-n:]


# ---------------------------------------------------------------- redaction

_SECRET_PATTERNS = [
    (re.compile(r"(?i)\b([a-z][a-z0-9+.-]*://)[^\s/:@]+:[^\s/@]+@"), r"\1[REDACTED]@"),
    (
        re.compile(
            r"(?i)(--?(?:token|secret|password|passwd|api[_-]?key|auth))(\s+)(?!-)\S+"
        ),
        r"\1\2[REDACTED]",
    ),
    (
        re.compile(r"(?i)(aws_secret_access_key|aws_session_token)\s*[=:]\s*\S+"),
        r"\1=[REDACTED]",
    ),
    (
        re.compile(r"(?i)(token|secret|passw(?:or)?d|api[_-]?key|auth)(\s*[=:]\s*)\S+"),
        r"\1\2[REDACTED]",
    ),
    (re.compile(r"(?i)\bBearer\s+\S+"), "Bearer [REDACTED]"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{10,}"), "[REDACTED]"),
    (re.compile(r"\b(?:ghp|gho|ghs|ghu|ghr)_\w+|\bgithub_pat_\w+"), "[REDACTED]"),
    (re.compile(r"\bxox[abprs]-[A-Za-z0-9-]+"), "[REDACTED]"),
    (re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"), "[REDACTED]"),
]


def redact(text):
    if not isinstance(text, str):
        text = "" if text is None else str(text)
    for rx, rep in _SECRET_PATTERNS:
        text = rx.sub(rep, text)
    return text


def excerpt(text, n=300, oneline=False):
    """Redacted, whitespace-tidied, truncated text; None when empty."""
    if text is None:
        return None
    t = redact(text).strip()
    if oneline:
        t = " ".join(t.split())
    if not t:
        return None
    return t if len(t) <= n else t[: n - 1].rstrip() + "…"


# ---------------------------------------------------------------- test parsers


def _ints(pairs):
    out = {}
    for num, word in pairs:
        out[word.lower()] = out.get(word.lower(), 0) + int(num)
    return out


def parse_tests(text, command=""):
    """Recognise a test runner summary in command output.

    Returns {runner, passed, failed, skipped, detail} or None. Unknown counts are None."""
    if not text:
        return None
    text = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", text)  # ANSI colour
    cmd = command or ""

    # testthat: [ FAIL 2 | WARN 0 | SKIP 3 | PASS 120 ]
    m = None
    for m in re.finditer(
        r"\[\s*FAIL\s+(\d+)\s*\|\s*WARN\s+(\d+)\s*\|\s*SKIP\s+(\d+)\s*\|\s*PASS\s+(\d+)\s*\]",
        text,
    ):
        pass
    if m:
        return {
            "runner": "testthat",
            "passed": int(m[4]),
            "failed": int(m[1]),
            "skipped": int(m[3]),
            "detail": f"{m[2]} warnings" if int(m[2]) else None,
        }

    # R CMD check: Status: 1 ERROR, 2 WARNINGs, 1 NOTE | Status: OK
    m = None
    for m in re.finditer(r"(?m)^Status:\s*(OK|.*(?:ERROR|WARNING|NOTE).*)$", text):
        pass
    if m:
        s = m[1].strip()
        if s == "OK":
            return {
                "runner": "R CMD check",
                "passed": None,
                "failed": 0,
                "skipped": None,
                "detail": "Status: OK",
            }
        c = {k: 0 for k in ("error", "warning", "note")}
        for num, word in re.findall(r"(\d+)\s+(ERROR|WARNING|NOTE)S?", s):
            c[word.lower()] += int(num)
        return {
            "runner": "R CMD check",
            "passed": None,
            "failed": c["error"] + c["warning"] + c["note"],
            "skipped": None,
            "detail": f"Status: {s}",
        }

    # cargo test: test result: ok. 12 passed; 0 failed; 1 ignored; ...
    found = re.findall(
        r"test result: \w+\. (\d+) passed; (\d+) failed; (\d+) ignored", text
    )
    if found:
        return {
            "runner": "cargo",
            "passed": sum(int(x[0]) for x in found),
            "failed": sum(int(x[1]) for x in found),
            "skipped": sum(int(x[2]) for x in found),
            "detail": None,
        }

    # jest: Tests:       2 failed, 1 skipped, 40 passed, 43 total
    m = None
    for m in re.finditer(r"(?m)^Tests:\s+(.*\d+ total)\s*$", text):
        pass
    if m:
        c = _ints(re.findall(r"(\d+) (failed|skipped|passed|todo|pending)", m[1]))
        return {
            "runner": "jest",
            "passed": c.get("passed", 0),
            "failed": c.get("failed", 0),
            "skipped": c.get("skipped", 0) + c.get("todo", 0) + c.get("pending", 0),
            "detail": None,
        }

    # vitest: Tests  3 failed | 40 passed | 2 skipped (45)
    m = None
    for m in re.finditer(r"(?m)^\s*Tests\s+((?:\d+ \w+(?: \| )?)+)\s*\(\d+\)", text):
        pass
    if m:
        c = _ints(re.findall(r"(\d+) (failed|skipped|passed|todo)", m[1]))
        return {
            "runner": "vitest",
            "passed": c.get("passed", 0),
            "failed": c.get("failed", 0),
            "skipped": c.get("skipped", 0) + c.get("todo", 0),
            "detail": None,
        }

    # pytest: ===== 41 passed, 2 failed, 3 skipped in 1.23s =====  (or -q form without =)
    m = None
    for m in re.finditer(
        r"(?m)^[=\s]*((?:\d+ (?:passed|failed|errors?|skipped|xfailed|xpassed|deselected|warnings?|rerun)(?:, )?)+) in [\d.]+s",
        text,
    ):
        pass
    if m:
        c = _ints(
            re.findall(r"(\d+) (passed|failed|errors?|skipped|xfailed|xpassed)", m[1])
        )
        if c:
            return {
                "runner": "pytest",
                "passed": c.get("passed", 0) + c.get("xpassed", 0),
                "failed": c.get("failed", 0) + c.get("error", 0) + c.get("errors", 0),
                "skipped": c.get("skipped", 0) + c.get("xfailed", 0),
                "detail": None,
            }

    # unittest: Ran 12 tests in 0.034s ... OK (skipped=2) / FAILED (failures=1, errors=2)
    m = re.search(r"(?m)^Ran (\d+) tests? in [\d.]+s\s*$", text)
    if m:
        ran = int(m[1])
        tail = text[m.end() :]
        verdict = re.search(r"(?m)^(OK|FAILED)(?:\s*\(([^)]*)\))?\s*$", tail)
        c = (
            dict((k, int(v)) for k, v in re.findall(r"(\w+)=(\d+)", verdict[2] or ""))
            if verdict
            else {}
        )
        failed = (
            c.get("failures", 0) + c.get("errors", 0) + c.get("unexpected_successes", 0)
        )
        skipped = c.get("skipped", 0) + c.get("expected_failures", 0)
        return {
            "runner": "unittest",
            "passed": max(ran - failed - skipped, 0),
            "failed": failed,
            "skipped": skipped,
            "detail": None if verdict else "no verdict",
        }

    # go test: --- PASS/FAIL/SKIP lines (-v), else package ok/FAIL lines
    if re.search(r"\bgo\s+test\b", cmd) or re.search(
        r"(?m)^(ok|FAIL)\s+\S+\s+[\d.]+s", text
    ):
        v = re.findall(r"(?m)^\s*--- (PASS|FAIL|SKIP): ", text)
        if v:
            return {
                "runner": "go",
                "passed": v.count("PASS"),
                "failed": v.count("FAIL"),
                "skipped": v.count("SKIP"),
                "detail": None,
            }
        ok = len(re.findall(r"(?m)^ok\s+\S+", text))
        bad = len(re.findall(r"(?m)^FAIL\s+\S+\s", text))
        if ok or bad:
            return {
                "runner": "go",
                "passed": ok,
                "failed": bad,
                "skipped": None,
                "detail": "counts are packages",
            }
    return None


# ---------------------------------------------------------------- hub discovery


class Hub:
    def __init__(self, d):
        self.d = Path(d)
        self.root = self.d.parent
        self.sessions = self.d / "sessions"

    def sdir(self, sid):
        if not isinstance(sid, str) or not SID_RE.match(sid):
            die(f"invalid session id {sid!r}")
        return self.sessions / sid

    def exists(self, sid):
        return (self.sdir(sid) / "session.json").is_file()

    def alias(self, sid):
        """The Claude session that adopted a CLI session created by `init`, else sid."""
        if self.exists(sid):
            return sid
        return (load_json(self.d / "aliases.json", {}) or {}).get(sid, sid)

    def session_ids(self):
        try:
            return sorted(
                p.name
                for p in self.sessions.iterdir()
                if SID_RE.match(p.name) and (p / "session.json").is_file()
            )
        except OSError:
            return []


def _named(d):
    d = Path(d).expanduser().resolve()
    if d.name != NAME:
        die(f"the dashboard folder must be named {NAME} (got {d})")
    return d


def git_toplevel(cwd):
    import subprocess

    try:
        p = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return Path(p.stdout.strip()) if p.returncode == 0 and p.stdout.strip() else None


def find_hub(dir_arg=None, create=False, cwd=None):
    """Locate (and optionally create) the hub. Migrates a v1 .dashboard in place."""
    cwd = Path(cwd or os.getcwd()).resolve()
    explicit = dir_arg or os.environ.get("DASHBOARD_DIR")
    d = None
    if explicit:
        d = _named(explicit)
    else:
        for base in (cwd, *cwd.parents):
            if (base / NAME / "hub.json").is_file() or (
                base / NAME / "state.json"
            ).is_file():
                d = base / NAME
                break
        if d is None and create:
            d = (git_toplevel(cwd) or cwd) / NAME
    if d is None:
        die(
            "no dashboard hub found here or in a parent folder (run `dash.py init` first)"
        )
    if not (d / "hub.json").is_file():
        if (d / "state.json").is_file():
            migrate_v1(d)
        elif create:
            d.mkdir(parents=True, exist_ok=True)
            os.chmod(d, 0o700)  # session data and the server token live here
            with locked(d / ".lock"):
                if not (d / "hub.json").is_file():
                    atomic_write(
                        d / "hub.json",
                        json.dumps(
                            {
                                "schema": SCHEMA,
                                "project": str(d.parent),
                                "created": now(),
                            },
                            indent=2,
                        )
                        + "\n",
                    )
        else:
            die(f"no dashboard hub at {d} (run `dash.py init` first)")
    hub = Hub(d)
    hub.sessions.mkdir(exist_ok=True)
    if create:
        with contextlib.suppress(OSError):
            os.chmod(d, 0o700)  # also tightens hubs made by older versions
    return hub


def migrate_v1(d):
    """Import a v1 single-run state.json as one session plan."""
    with locked(d / ".lock"):
        if (d / "hub.json").is_file():
            return
        old = load_json(d / "state.json", {}) or {}
        if not isinstance(old, dict):
            die(
                f"{d}/state.json is not a v1 dashboard; move it away and run init again"
            )
        sid = "v1-" + re.sub(r"[^A-Za-z0-9]", "", str(old.get("run_id") or "run"))[:8]
        sd = d / "sessions" / sid
        sd.mkdir(parents=True, exist_ok=True)
        t = now()
        plan = {
            "title": old.get("title") or "Imported v1 run",
            "goal": old.get("goal") or "",
            "context": old.get("context") or "",
            "status": old.get("status") if old.get("status") in OVERALL else "on_track",
            "status_note": old.get("status_note") or "",
            "status_updated": old.get("updated") or t,
            "started": old.get("started") or t,
            "finished": old.get("finished"),
            "tasks": [
                {
                    "id": x.get("id"),
                    "title": x.get("title", ""),
                    "detail": x.get("detail") or "",
                    "status": x.get("status", "todo"),
                    "note": x.get("note"),
                    "started": x.get("started"),
                    "finished": x.get("finished"),
                }
                for x in old.get("tasks", [])
            ],
            "questions": [
                {
                    "id": q.get("id"),
                    "text": q.get("q", ""),
                    "default": q.get("default"),
                    "asked": q.get("asked"),
                    "answer": q.get("answer"),
                    "answered": q.get("answered"),
                    "answered_via": "chat" if q.get("answer") is not None else None,
                }
                for q in old.get("questions", [])
            ],
            "blockers": [
                {
                    "id": b.get("id"),
                    "text": b.get("what", ""),
                    "needs": b.get("needs") or None,
                    "opened": b.get("since"),
                    "closed": b.get("cleared"),
                    "note": b.get("note"),
                }
                for b in old.get("blockers", [])
            ],
            "metrics": [
                {
                    "name": k,
                    "value": m.get("value"),
                    "total": m.get("total"),
                    "unit": m.get("unit"),
                    "good": m.get("good"),
                    "updated": m.get("at"),
                    "history": [
                        [h.get("at"), h.get("value")] for h in m.get("history", [])
                    ],
                }
                for k, m in (old.get("metrics") or {}).items()
            ],
            "deliverables": [
                {
                    "path": x.get("path"),
                    "label": x.get("label"),
                    "ts": x.get("at"),
                    "note": x.get("note") or None,
                }
                for x in old.get("deliverables", [])
            ],
            "log": [
                {"ts": x.get("at"), "text": x.get("msg", "")}
                for x in old.get("log", [])
            ][-LOG_KEEP:],
        }
        sess = new_session(
            sid,
            agent=old.get("agent") or "cli",
            label=plan["title"],
            cwd=old.get("project") or str(d.parent),
        )
        sess["started"] = old.get("started") or t
        sess["last_seen"] = old.get("updated") or t
        atomic_write(
            sd / "plan.json", json.dumps(plan, indent=2, ensure_ascii=False) + "\n"
        )
        atomic_write(sd / "session.json", dump(sess) + "\n")
        os.replace(d / "state.json", sd / "v1-state.json")
        with contextlib.suppress(FileNotFoundError):
            os.unlink(d / "state.js")
        atomic_write(
            d / "hub.json",
            json.dumps(
                {
                    "schema": SCHEMA,
                    "project": str(d.parent),
                    "created": t,
                    "migrated_from": "v1",
                },
                indent=2,
            )
            + "\n",
        )
    print(f"dash: migrated the v1 dashboard in {d} to session {sid}", file=sys.stderr)


# ---------------------------------------------------------------- sessions


def new_session(sid, agent="cli", label="", cwd=""):
    t = now()
    return {
        "id": sid,
        "agent": agent or "cli",
        "label": label or "",
        "cwd": cwd or "",
        "started": t,
        "last_seen": t,
        "ended": None,
        "end_reason": None,
        "hooks": False,
        "turn": None,
        "turn_since": t,
        "activity_since": t,
        "inflight": {},
        "last_prompt": None,
        "attention": [],
        "stats": {
            "tool_calls": 0,
            "edits": 0,
            "commands": 0,
            "failures": 0,
            "turns": 0,
            "subagents": 0,
            "files_touched": 0,
        },
        "subagent_ids": [],
        "files": {},
        "tests": [],
        "next_event": 1,
        "events_in_file": 0,
        "next_message": 1,
    }


class SessionEdit:
    """Lock a session directory, load session.json, save it on clean exit.

    Use .event(...) to append timeline events inside the lock."""

    def __init__(self, hub, sid, create=None):
        self.hub, self.sid, self.create = hub, sid, create
        self.sd = hub.sdir(sid)
        self.changed = True

    def __enter__(self):
        if not self.sd.is_dir():
            if not self.create:
                die(f"no session {self.sid!r} in {self.hub.d}")
            self.sd.mkdir(parents=True, exist_ok=True)
        self._lock = locked(self.sd / ".lock")
        self._lock.__enter__()
        try:
            s = load_json(self.sd / "session.json")
            if not isinstance(s, dict):
                if not self.create:
                    die(f"no session {self.sid!r} in {self.hub.d}")
                s = new_session(self.sid, **self.create)
            self.s = s
        except BaseException:
            self._lock.__exit__(*sys.exc_info())
            raise
        return self

    def event(
        self,
        kind,
        summary=None,
        tool=None,
        detail=None,
        ok=None,
        duration_ms=None,
        subagent=None,
        ts=None,
    ):
        s = self.s
        ev = {
            "id": s.get("next_event", 1),
            "ts": ts or now(),
            "kind": kind,
            "tool": tool,
            "summary": summary,
            "detail": detail,
            "ok": ok,
            "duration_ms": duration_ms,
            "subagent": subagent,
        }
        s["next_event"] = ev["id"] + 1
        path = self.sd / "events.jsonl"
        if s.get("events_in_file", 0) >= EVENTS_ROTATE:
            with contextlib.suppress(FileNotFoundError):
                os.replace(path, self.sd / "events.1.jsonl")
            s["events_in_file"] = 0
        with open(path, "a", encoding="utf-8") as f:
            f.write(dump(ev) + "\n")
        s["events_in_file"] = s.get("events_in_file", 0) + 1
        return ev

    def __exit__(self, et, ev, tb):
        try:
            if et is None and self.changed:
                atomic_write(self.sd / "session.json", dump(self.s) + "\n")
        finally:
            self._lock.__exit__(et, ev, tb)
        return False


def plan_path(hub, sid):
    return hub.sdir(sid) / "plan.json"


def read_events(sd, n=EVENTS_SHOW):
    lines = tail_lines(sd / "events.jsonl", n)
    if len(lines) < n:
        lines = tail_lines(sd / "events.1.jsonl", n - len(lines)) + lines
    out = []
    for ln in lines:
        try:
            e = json.loads(ln)
        except ValueError:
            continue
        if isinstance(e, dict):
            out.append(e)
    return out


def read_inbox(sd):
    """Merged inbox: [{id, ts, kind, text, qid, status, delivered, via}] oldest first."""
    items, order = {}, []
    try:
        with open(sd / "inbox.jsonl", encoding="utf-8") as f:
            for ln in f:
                try:
                    r = json.loads(ln)
                except ValueError:
                    continue
                if not isinstance(r, dict) or "id" not in r:
                    continue
                if r.get("op") == "add":
                    items[r["id"]] = {
                        "id": r["id"],
                        "ts": r.get("ts"),
                        "kind": r.get("kind", "message"),
                        "text": r.get("text", ""),
                        "qid": r.get("qid"),
                        "status": "queued",
                        "delivered": None,
                        "via": None,
                    }
                    order.append(r["id"])
                elif r.get("op") == "status" and r["id"] in items and r.get("status") == "queued":
                    items[r["id"]].update(status="queued", delivered=None, via=None)
                elif r.get("op") == "status" and r["id"] in items:
                    items[r["id"]].update(
                        status=r.get("status", "delivered"),
                        delivered=r.get("delivered"),
                        via=r.get("via"),
                    )
    except OSError:
        pass
    return [items[i] for i in order]


def queued(sd):
    return [m for m in read_inbox(sd) if m["status"] == "queued"]


def frame(msg, plan=None):
    t = epoch(msg.get("ts"))
    when = datetime.fromtimestamp(t).strftime("%H:%M") if t else "earlier"
    if msg.get("kind") == "answer" and msg.get("qid"):
        q = next(
            (
                x
                for x in (plan or {}).get("questions", [])
                if str(x.get("id")) == msg["qid"]
            ),
            None,
        )
        qt = f' "{q.get("text")}"' if q else ""
        return f"[Dashboard answer from the user to {msg['qid']}{qt}] {msg['text']}"
    return f"[Dashboard message from the user, sent {when} via the local dashboard] {msg['text']}"


def take_messages(ed, via):
    """Inside a SessionEdit: mark queued messages delivered and return framed text (or None)."""
    msgs = queued(ed.sd)
    if not msgs:
        return None
    t = now()
    with open(ed.sd / "inbox.jsonl", "a", encoding="utf-8") as f:
        for m in msgs:
            f.write(
                dump(
                    {
                        "op": "status",
                        "id": m["id"],
                        "status": "delivered",
                        "delivered": t,
                        "via": via,
                    }
                )
                + "\n"
            )
    ed.taken = getattr(ed, "taken", []) + [m["id"] for m in msgs]
    for m in msgs:
        ed.event(
            "message",
            summary=f"Delivered {m['id']} via {via}",
            detail=excerpt(m["text"], 200),
            ok=True,
        )
    plan = load_json(ed.sd / "plan.json")
    return "\n\n".join(frame(m, plan) for m in msgs)


def queue_message(hub, sid, kind, text, qid=None):
    """Queue a message from the user. Answers also resolve the plan question."""
    if kind not in ("message", "answer"):
        die("kind must be message or answer")
    if not isinstance(text, str) or not text.strip():
        die("message text is empty")
    text = text.strip()
    if len(text) > TEXT_MAX:
        die(f"message is longer than {TEXT_MAX} characters")
    if kind == "answer":
        if not isinstance(qid, str) or not re.match(r"^Q\d{1,6}$", qid.strip().upper()):
            die("answer needs a question id like Q2")
        qid = qid.strip().upper()
    else:
        qid = None
    if not hub.exists(sid):
        die(f"no session {sid!r}")
    with SessionEdit(hub, sid) as ed:
        if kind == "answer":
            pp = ed.sd / "plan.json"
            plan = load_json(pp)
            q = next(
                (
                    x
                    for x in (plan or {}).get("questions", [])
                    if str(x.get("id")).upper() == qid
                ),
                None,
            )
            if q is None:
                die(f"no question {qid} in this session")
            if q.get("answer") is not None:
                die(f"{qid} is already answered")
            t = now()
            q.update(answer=text, answered=t, answered_via="dashboard")
            plan.setdefault("log", []).append(
                {"ts": t, "text": f"{qid} answered from the dashboard: {text}"}
            )
            plan["log"] = plan["log"][-LOG_KEEP:]
            atomic_write(pp, json.dumps(plan, indent=2, ensure_ascii=False) + "\n")
        mid = f"m{ed.s.get('next_message', 1)}"
        ed.s["next_message"] = ed.s.get("next_message", 1) + 1
        rec = {
            "op": "add",
            "id": mid,
            "ts": now(),
            "kind": kind,
            "text": text,
            "qid": qid,
        }
        with open(ed.sd / "inbox.jsonl", "a", encoding="utf-8") as f:
            f.write(dump(rec) + "\n")
        ed.event(
            "message",
            summary=f"Queued {mid}" + (f" (answer to {qid})" if qid else ""),
            detail=excerpt(text, 200),
            ok=None,
        )
    bump(hub)
    return mid


def set_paused(hub, sid, paused):
    if not hub.exists(sid):
        die(f"no session {sid!r}")
    with SessionEdit(hub, sid) as ed:
        flag = ed.sd / "paused"
        if paused and not flag.exists():
            flag.write_text(now() + "\n")
            ed.event("session", summary="Paused from the dashboard", ok=None)
        elif not paused and flag.exists():
            flag.unlink()
            ed.event("session", summary="Resumed from the dashboard", ok=None)
        else:
            ed.changed = False
    bump(hub)


# ---------------------------------------------------------------- activity


def base_activity(s, paused, plan, t):
    """(activity, since) for a session at epoch t."""
    last = epoch(s.get("last_seen")) or t
    if s.get("ended"):
        return "ended", s["ended"]
    if t - last > ENDED_AFTER:
        return "ended", iso(last + ENDED_AFTER)
    if paused:
        return "paused", paused
    perm = [a for a in s.get("attention", []) if a.get("kind") == "permission"]
    if perm:
        return "waiting_permission", perm[-1].get("ts")
    open_q = bool(plan) and any(
        q.get("answer") is None for q in plan.get("questions", [])
    )
    if not s.get("hooks"):
        # Narrative-only session (Codex, CLI): liveness comes from dash.py calls.
        if plan and plan.get("status") == "done":
            return "idle", plan.get("status_updated") or s.get("last_seen")
        if t - last > STALL_AFTER:
            return "idle", iso(last + STALL_AFTER)
        return "working", s.get("activity_since") or s.get("started")
    if s.get("turn") == "active":
        if not s.get("inflight") and t - last > STALL_AFTER:
            return "stalled", iso(last + STALL_AFTER)
        return "working", s.get("turn_since")
    if open_q or any(a.get("kind") in ("input", "idle") for a in s.get("attention", [])):
        return "waiting_user", s.get("turn_since")
    return "idle", s.get("turn_since")


def wakeable(sd, s, activity, t):
    """True while a live --watch-inbox watcher waits for this idle session; False when it cannot
    be woken (no hooks, ended, or its watcher died); None when unknown (no watcher record)."""
    if not s.get("hooks") or activity == "ended":
        return False
    w = load_json(sd / "watch.json")
    if not isinstance(w, dict):
        return None
    poll = w.get("poll") if isinstance(w.get("poll"), (int, float)) else 2
    fresh = t - (epoch(w.get("heartbeat")) or 0) <= max(10.0, 3 * poll)
    return bool(fresh and pid_alive(w.get("pid")))


def paused_since(sd):
    try:
        return (sd / "paused").read_text().strip() or now()
    except OSError:
        return None


# ---------------------------------------------------------------- git, style, mote


def git_info(hub):
    """Branch, short head, subject and dirty count, cached for GIT_TTL seconds; None on failure."""
    import subprocess

    cache = hub.d / "git.json"
    c = load_json(cache)
    if isinstance(c, dict) and time.time() - c.get("at", 0) < GIT_TTL:
        return c.get("git")
    info = None
    try:

        def run(*args):
            return subprocess.run(
                ["git", *args], cwd=hub.root, capture_output=True, text=True, timeout=2
            )

        st = run("status", "--porcelain=v1", "-b")
        if st.returncode == 0:
            lines = st.stdout.splitlines()
            branch = None
            if lines and lines[0].startswith("## "):
                head = lines[0][3:]
                if head.startswith("No commits yet on "):
                    branch = head[len("No commits yet on ") :]
                elif head.startswith("HEAD (no branch)"):
                    branch = "HEAD"
                else:
                    branch = head.split("...")[0].strip()
                lines = lines[1:]
            lg = run("log", "-1", "--format=%h%x1f%s")
            hd, subj = (
                (lg.stdout.strip().split("\x1f", 1) + [None])[:2]
                if lg.returncode == 0 and lg.stdout.strip()
                else (None, None)
            )
            info = {
                "branch": branch,
                "head": hd,
                "subject": excerpt(subj, 200) if subj else None,
                "dirty": len([ln for ln in lines if ln.strip()]),
            }
    except (OSError, subprocess.SubprocessError, ValueError):
        info = None
    with contextlib.suppress(OSError):
        atomic_write(cache, dump({"at": time.time(), "git": info}))
    return info


def read_style(path=None):
    path = path or STYLE
    out = {"theme": None, "density": None, "accent": None, "notes": None}
    try:
        text = Path(path).read_text()
    except OSError:
        return out
    m = re.search(r"^theme:\s*[\"']?(dark|light|system)\b", text, re.M)
    out["theme"] = m[1] if m else None
    m = re.search(r"^density:\s*[\"']?(dense|airy)\b", text, re.M)
    out["density"] = m[1] if m else None
    m = re.search(
        r"^accent:\s*[\"']?(#[0-9a-fA-F]{8}|#[0-9a-fA-F]{6}|#[0-9a-fA-F]{4}|#[0-9a-fA-F]{3})(?=[\"'\s]|$)",
        text,
        re.M,
    )
    out["accent"] = m[1] if m else None
    m = re.search(
        r"^notes:\s*(?:\"((?:[^\"\\]|\\.)*)\"|'([^']*)'|([^#\n]*))", text, re.M
    )
    if m:
        out["notes"] = (
            m[1] if m[1] is not None else m[2] if m[2] is not None else m[3] or ""
        ).strip()[:500]
    return out


def find_mote_store(root):
    root = Path(root)
    for base in (root, *root.parents):
        if (base / ".mote").is_dir():
            return base / ".mote"
    return None


def mote_bin():
    import shutil

    return shutil.which("mote")


def _bead(x):
    return {
        "id": x.get("id"),
        "title": excerpt(x.get("title"), 200, oneline=True) or "",
        "assignee": x.get("assignee"),
        "tags": list(x.get("tags") or [])[:8],
        "priority": x.get("priority"),
    }


_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def ulid_time(ident):
    """Creation time encoded in a mote id such as rv-01M3SFA4WA9FG6T7NSA5TERS5S (a ULID); None otherwise.

    Mote's reservation listings carry no creation field, but every id is a ULID minted when
    the reservation was made."""
    if not isinstance(ident, str):
        return None
    u = ident.rsplit("-", 1)[-1].upper()
    if len(u) != 26 or any(c not in _CROCKFORD for c in u) or u[0] > "7":
        return None
    ms = 0
    for c in u[:10]:
        ms = ms * 32 + _CROCKFORD.index(c)
    return iso(ms / 1000)


def mote_run(binary, store, args, timeout):
    """(parsed JSON, None) or (None, error text) for one read-only mote command."""
    import subprocess

    try:
        p = subprocess.Popen(
            [binary, "--store", str(store), "--quiet", *args],
            cwd=str(Path(store).parent),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            start_new_session=True,  # so a timeout can kill the whole group
        )
    except OSError as e:
        return None, str(e)
    try:
        out, err = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        with contextlib.suppress(OSError):
            os.killpg(p.pid, 9)
        with contextlib.suppress(subprocess.SubprocessError, OSError):
            p.communicate(timeout=1)
        return None, f"timed out after {timeout}s"
    if p.returncode != 0:
        return None, f"exit {p.returncode}: {excerpt(err.decode('utf-8', 'replace'), 120, True)}"
    try:
        return json.loads(out.decode("utf-8", "replace") or "null"), None
    except ValueError:
        return None, "invalid JSON"


def mote_fetch(store, binary, timeout=MOTE_TIMEOUT):
    """Read-only mote snapshot. Commands run one at a time (a large store replays its op log
    on every call, and parallel calls contend); each has its own timeout. Failures become `error`."""
    cmds = {
        "board": ["board", "--json"],
        "beads": ["ls", "--json"],
        "ready": ["ready", "--json"],
        "posts": ["discuss", "list", "--json"],
    }
    results, errors = {}, []
    for k, c in cmds.items():
        val, err = mote_run(binary, store, c, timeout)
        if err:
            errors.append(f"{k}: {err}")
        else:
            results[k] = val
    snap = {
        "store": str(store),
        "fetched": now(),
        "error": "; ".join(errors) or None,
        "counts": None,
        "doing": [],
        "ready": [],
        "blocked": [],
        "reservations": [],
        "actors": [],
        "posts": [],
    }
    b = results.get("board")
    if isinstance(b, dict):
        sc = b.get("status_counts") or {}
        snap["counts"] = {
            k: int(sc.get(k, 0) or 0) for k in ("open", "doing", "blocked", "review")
        }
        for r in (b.get("active_reservations") or [])[:40]:
            snap["reservations"].append(
                {
                    "actor": r.get("actor") or r.get("holder"),
                    "paths": [str(p) for p in (r.get("paths") or [])][:20],
                    "issue": r.get("entity"),
                    "created": ulid_time(r.get("reservation_id")),
                    "expires": local_iso(r.get("lease_until_ts") or r.get("deadline")),
                }
            )
        status_map = {"live": "active", "recent": "idle", "expired": "away"}
        acts = []
        for a in b.get("actors") or []:
            st = (a.get("presence") or {}).get("state")
            if st in ("live", "recent"):
                acts.append(
                    {
                        "actor": a.get("actor"),
                        "status": status_map[st],
                        "expires": local_iso(
                            (a.get("presence") or {}).get("latest_lease_until_ts")
                        ),
                    }
                )
        snap["actors"] = acts[:12]
    beads = results.get("beads")
    if isinstance(beads, list):
        beads = [x for x in beads if isinstance(x, dict)]
        by = lambda st: [x for x in beads if x.get("status") == st]  # noqa: E731
        snap["doing"] = [_bead(x) for x in by("doing")[:20]]
        snap["blocked"] = [_bead(x) for x in by("blocked")[:12]]
        if snap["counts"] is None:
            snap["counts"] = {k: len(by(k)) for k in ("open", "doing", "blocked", "review")}
    ready = results.get("ready")
    if isinstance(ready, list):
        snap["ready"] = [_bead(x) for x in ready[:12] if isinstance(x, dict)]
    posts = results.get("posts")
    if isinstance(posts, list):
        recent = [p for p in posts if isinstance(p, dict) and not p.get("retracted")
                  and time.time() - (epoch(p.get("sent_ts")) or 0) <= POST_WINDOW]
        recent.sort(key=lambda p: p.get("sent_ts") or "", reverse=True)
        mentions = []
        for p in recent[:POST_SCAN]:
            found = path_mentions(p.get("body"))
            if found:
                mentions.append({"id": p.get("post_id"), "from": p.get("from"),
                                 "ts": local_iso(p.get("sent_ts")), "paths": found})
        snap["_mentions"] = mentions
        replies = {}
        for p in posts:
            if isinstance(p, dict) and p.get("reply_to"):
                replies[p["reply_to"]] = replies.get(p["reply_to"], 0) + 1
        roots = [
            p
            for p in posts
            if isinstance(p, dict) and not p.get("reply_to") and not p.get("retracted")
        ]
        roots.sort(key=lambda p: p.get("sent_ts") or "", reverse=True)
        snap["posts"] = [
            {
                "id": p.get("post_id"),
                "topic": p.get("topic"),
                "from": p.get("from"),
                "ts": local_iso(p.get("sent_ts")),
                "excerpt": excerpt(p.get("body"), 240, oneline=True) or "",
                "replies": replies.get(p.get("post_id"), 0),
            }
            for p in roots[:10]
        ]
    return snap


def mote_refresh(hub):
    """Refresh mote.json if stale; one refresher at a time. Returns True if refreshed."""
    store = find_mote_store(hub.root)
    binary = mote_bin()
    if not store or not binary:
        return False
    with locked(hub.d / ".mote-refresh.lock", blocking=False) as got:
        if not got:
            return False
        cur = load_json(hub.d / "mote.json")
        if (
            isinstance(cur, dict)
            and time.time() - (epoch(cur.get("fetched")) or 0) < MOTE_TTL
            and cur.get("store") == str(store)
        ):
            return False
        try:
            snap = mote_fetch(store, binary)
        except Exception as e:  # never let mote break the dashboard
            snap = {
                "store": str(store),
                "fetched": now(),
                "error": f"refresh failed: {e}",
                "counts": None,
                "doing": [],
                "ready": [],
                "blocked": [],
                "reservations": [],
                "actors": [],
                "posts": [],
            }
        atomic_write(hub.d / "mote.json", dump(snap) + "\n")
    bump(hub)
    regen(hub)
    return True


def mote_kick(hub):
    """Start a background mote refresh when the cache is stale. Never blocks."""
    try:
        if not find_mote_store(hub.root) or not mote_bin():
            return
        cur = load_json(hub.d / "mote.json")
        if (
            isinstance(cur, dict)
            and time.time() - (epoch(cur.get("fetched")) or 0) < MOTE_TTL
        ):
            return
        stamp = hub.d / ".mote-kick"
        try:
            if time.time() - stamp.stat().st_mtime < MOTE_TTL:
                return
        except OSError:
            pass
        stamp.touch()
        import subprocess

        subprocess.Popen(
            [sys.executable, str(SCRIPT), "--dir", str(hub.d), "_mote-refresh"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            close_fds=True,
        )
    except Exception:
        pass


def mote_snapshot(hub):
    """The cached mote snapshot, private keys (leading _) included; None without mote."""
    if not find_mote_store(hub.root) or not mote_bin():
        return None
    cur = load_json(hub.d / "mote.json")
    return cur if isinstance(cur, dict) and cur.get("fetched") else None


_PATH_WORD = re.compile(r"[A-Za-z0-9_.@-]+(?:/[A-Za-z0-9_.@-]+)*")


def path_mentions(text, cap=10):
    """Repo-relative path-like words in post text (existence is checked at snapshot time)."""
    out = []
    for w in _PATH_WORD.findall(re.sub(r"[A-Za-z][A-Za-z0-9+.-]*://\S+", " ", text or "")):
        w = w.strip(".-")
        if ("/" in w or re.search(r"\.[A-Za-z]{1,6}$", w)) and not w.startswith(("/", "..")) \
                and "://" not in w and len(w) <= 200 and w not in out:
            out.append(w)
            if len(out) >= cap:
                break
    return out


def _covers(res_path, path):
    rp = str(res_path)
    return path == rp.rstrip("/") or path.startswith(rp.rstrip("/") + "/")


def _actor_session(actor, views):
    """Map a mote actor to a session short id when the name carries it (e.g. claude-8f3c)."""
    if not isinstance(actor, str):
        return None
    for v in views:
        if actor in (v["id"], v["short"]) or actor.endswith("-" + v["short"]) or actor.endswith("-" + v["id"]):
            return v["short"]
    return None


def build_conflicts(hub, views, edits, mote, t):
    """Paths touched by at least two agents through recent edits, mote reservations or board posts."""
    root = Path(hub.root)
    reservations = [r for r in (mote or {}).get("reservations") or []
                    if (epoch(r.get("expires")) or t + 1) > t]
    candidates = set(edits)
    for r in reservations:
        candidates.update(str(p).rstrip("/") for p in r.get("paths") or [])
    mentions, checked = [], 0
    for m in (mote or {}).get("_mentions") or []:
        if t - (epoch(m.get("ts")) or 0) > POST_WINDOW:
            continue
        keep = []
        for pth in m.get("paths") or []:
            if checked >= 200:
                break
            checked += 1
            with contextlib.suppress(OSError, ValueError):
                if (root / pth).exists() and os.path.realpath(root / pth).startswith(os.path.realpath(root)):
                    keep.append(pth.rstrip("/"))
        if keep:
            mentions.append(dict(m, paths=keep))
            candidates.update(keep)
    activity = {v["short"]: v["activity"] for v in views}
    out = []
    for path in sorted(candidates):
        detail = []
        for short, ts in edits.get(path, []):
            detail.append({"session": short, "kind": "edit", "ts": ts, "expires": None, "ref": None})
        for r in reservations:
            if any(_covers(rp, path) for rp in r.get("paths") or []):
                who = _actor_session(r.get("actor"), views) or r.get("actor")
                detail.append({"session": who, "kind": "reservation", "ts": r.get("created"),
                               "expires": r.get("expires"), "ref": r.get("issue")})
        for m in mentions:
            if path in m["paths"]:
                who = _actor_session(m.get("from"), views) or m.get("from")
                detail.append({"session": who, "kind": "post", "ts": m.get("ts"), "expires": None, "ref": m.get("id")})
        agents = []
        for d in detail:
            if d["session"] and d["session"] not in agents:
                agents.append(d["session"])
        if len(agents) < 2:
            continue
        edit_ts = [d["ts"] for d in detail if d["kind"] == "edit"]
        live = any(t - (epoch(x) or 0) <= CONFLICT_LIVE for x in edit_ts) or any(
            d["kind"] == "reservation" and activity.get(d["session"]) == "working" for d in detail)
        res = [d for d in detail if d["kind"] == "reservation"]
        out.append({
            "path": path,
            "sessions": [a for a in agents if a in activity],
            "sources": [k for k in ("edit", "reservation", "post") if any(d["kind"] == k for d in detail)],
            "live": live,
            "last_edit": max(edit_ts, key=lambda x: epoch(x) or 0) if edit_ts else None,
            "mote_reserved_by": next((r.get("actor") for r in reservations
                                      if any(_covers(rp, path) for rp in r.get("paths") or [])), None) if res else None,
            "detail": detail,
        })
    out.sort(key=lambda c: (not c["live"], -(epoch(c["last_edit"]) or 0), c["path"]))
    return out[:50]


# ---------------------------------------------------------------- snapshot


def bump(hub):
    """Advance the hub-wide revision counter."""
    with locked(hub.d / ".lock"):
        p = hub.d / "revision"
        try:
            n = int(p.read_text().strip() or 0)
        except (OSError, ValueError):
            n = 0
        atomic_write(p, f"{n + 1}\n")
    return n + 1


def revision(hub):
    try:
        return int((hub.d / "revision").read_text().strip() or 0)
    except (OSError, ValueError):
        return 0


def project_plan(plan):
    if not isinstance(plan, dict):
        return None

    def pick(d, keys):
        return {k: d.get(k) for k in keys}

    return {
        "title": plan.get("title", ""),
        "goal": plan.get("goal", ""),
        "context": plan.get("context", ""),
        "status": plan.get("status", "on_track"),
        "status_note": plan.get("status_note", ""),
        "status_updated": plan.get("status_updated"),
        "tasks": [
            pick(t, ("id", "title", "detail", "status", "note", "started", "finished"))
            for t in plan.get("tasks", [])
        ],
        "questions": [
            pick(
                q,
                (
                    "id",
                    "text",
                    "default",
                    "asked",
                    "answer",
                    "answered",
                    "answered_via",
                ),
            )
            for q in plan.get("questions", [])
        ],
        "blockers": [
            pick(b, ("id", "text", "needs", "opened", "closed"))
            for b in plan.get("blockers", [])
        ],
        "metrics": [
            pick(m, ("name", "value", "total", "unit", "good", "updated", "history"))
            for m in plan.get("metrics", [])
        ],
        "deliverables": [
            pick(x, ("path", "label", "ts", "note"))
            for x in plan.get("deliverables", [])
        ],
        "log": [pick(x, ("ts", "text")) for x in plan.get("log", [])][-100:],
    }


def session_view(hub, sid, t=None):
    """The contract view of one session, or None if unreadable."""
    t = time.time() if t is None else t
    sd = hub.sdir(sid)
    s = load_json(sd / "session.json")
    if not isinstance(s, dict):
        return None
    plan = load_json(sd / "plan.json")
    paused = paused_since(sd)
    activity, since = base_activity(s, paused, plan, t)
    inflight = list((s.get("inflight") or {}).values())
    cur = max(inflight, key=lambda x: x.get("epoch", 0)) if inflight else None
    files = sorted(
        ((p, f) for p, f in (s.get("files") or {}).items()),
        key=lambda x: x[1].get("last") or "",
        reverse=True,
    )[:FILES_SHOW]
    label = s.get("label") or (plan or {}).get("title") or ""
    return {
        "id": sid,
        "short": sid.split("-", 1)[1][:4]
        if sid.startswith(("cli-", "v1-")) and "-" in sid
        else sid[:4],
        "agent": s.get("agent") or "cli",
        "label": label,
        "cwd": s.get("cwd") or "",
        "started": s.get("started"),
        "last_seen": s.get("last_seen"),
        "ended": s.get("ended"),
        "activity": activity,
        "activity_since": since,
        "current": {
            "tool": cur.get("tool"),
            "summary": cur.get("summary"),
            "started": cur.get("started"),
            "destructive": cur.get("destructive"),
        }
        if cur and activity not in ("ended",)
        else None,
        "last_prompt": s.get("last_prompt"),
        "attention": [
            {"kind": a.get("kind"), "text": a.get("text"), "ts": a.get("ts"),
             "destructive": a.get("destructive")}
            for a in s.get("attention", [])
        ][-ATTENTION_KEEP:],
        "plan": project_plan(plan),
        "stats": dict(s.get("stats") or {}),
        "tests": [
            {
                k: x.get(k)
                for k in ("ts", "runner", "passed", "failed", "skipped", "command")
            }
            for x in s.get("tests", [])
        ][-TESTS_KEEP:],
        "files": [
            {
                "path": p,
                "edits": f.get("edits", 0),
                "reads": f.get("reads", 0),
                "last": f.get("last"),
            }
            for p, f in files
        ],
        "events": [
            {
                k: e.get(k)
                for k in (
                    "id",
                    "ts",
                    "kind",
                    "tool",
                    "summary",
                    "detail",
                    "ok",
                    "duration_ms",
                    "subagent",
                )
            }
            for e in read_events(sd)
        ],
        "inbox": read_inbox(sd)[-INBOX_SHOW:],
        "paused": paused is not None,
        "wakeable": wakeable(sd, s, activity, t),
        "_edits": {
            p: f.get("last_edit")
            for p, f in (s.get("files") or {}).items()
            if f.get("last_edit")
        },
    }


def server_state(hub):
    info = load_json(hub.d / "server.json")
    if isinstance(info, dict) and pid_alive(info.get("pid")):
        return {"running": True, "started": info.get("started")}
    return {"running": False, "started": None}


def pid_alive(pid):
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def build_snapshot(hub, t=None):
    t = time.time() if t is None else t
    meta = load_json(hub.d / "hub.json", {}) or {}
    root = meta.get("project") or str(hub.root)
    views = []
    for sid in hub.session_ids():
        try:
            v = session_view(hub, sid, t)
        except Exception:
            v = None
        if v is None:
            continue
        if (
            v["activity"] == "ended"
            and t - (epoch(v["ended"] or v["last_seen"]) or 0) > ENDED_SHOW
        ):
            continue
        views.append(v)
    views.sort(key=lambda v: (v["activity"] == "ended", -(epoch(v["last_seen"]) or 0)))
    views = views[:SESSIONS_SHOW]
    mote = mote_snapshot(hub)
    edited = {}
    for v in views:
        for p, ts in v.pop("_edits").items():
            if t - (epoch(ts) or 0) <= CONFLICT_WINDOW:
                edited.setdefault(p, []).append((v["short"], ts))
    conflicts = build_conflicts(hub, views, edited, mote, t)
    if mote is not None:
        mote = {k: v for k, v in mote.items() if not k.startswith("_")}
    return {
        "schema": SCHEMA,
        "generated": iso(t),
        "revision": revision(hub),
        "project": {"name": Path(root).name, "root": root, "git": git_info(hub)},
        "server": server_state(hub),
        "style": read_style(),
        "sessions": views,
        "conflicts": conflicts,
        "mote": mote,
    }


def write_datajs(hub, snap):
    body = dump(snap).replace(
        "</", "<\\/"
    )  # a string must not close the <script> element
    atomic_write(hub.d / "data.js", f"window.__hub({body});\n")


def regen(hub, significant=True):
    """Rebuild data.js. Insignificant updates are skipped within REGEN_DEBOUNCE of the last write."""
    if not significant:
        try:
            if time.time() - (hub.d / "data.js").stat().st_mtime < REGEN_DEBOUNCE:
                schedule_flush(hub)
                return False
        except OSError:
            pass
    with locked(hub.d / ".render.lock"):
        write_datajs(hub, build_snapshot(hub))
    return True


def schedule_flush(hub):
    """Make sure a skipped update still reaches data.js: one detached trailing rebuild."""
    import subprocess

    pending = hub.d / ".flush-pending"
    try:
        fd = os.open(pending, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        os.close(fd)
    except FileExistsError:
        try:
            if time.time() - pending.stat().st_mtime < 30:
                return  # a flusher is already waiting
            os.utime(pending)
        except OSError:
            return
    except OSError:
        return
    try:
        subprocess.Popen(
            [sys.executable, str(SCRIPT), "--dir", str(hub.d), "_flush"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            close_fds=True,
        )
    except OSError:
        with contextlib.suppress(OSError):
            pending.unlink()


def cmd_flush(a):
    hub = find_hub(a.dir)
    try:
        wait = REGEN_DEBOUNCE - (time.time() - (hub.d / "data.js").stat().st_mtime)
    except OSError:
        wait = 0
    time.sleep(max(0.0, min(wait, REGEN_DEBOUNCE)) + 0.05)
    with contextlib.suppress(OSError):
        (hub.d / ".flush-pending").unlink()
    regen(hub)


# ---------------------------------------------------------------- hook handling


def rel_path(hub, p):
    if not isinstance(p, str) or not p:
        return None
    try:
        ap = Path(p)
        if not ap.is_absolute():
            return p
        r = os.path.relpath(ap, hub.root)
        return p if r.startswith("..") else r
    except ValueError:
        return p


# ---------------------------------------------------------------- destructive commands

_SEPARATORS = {";", "&&", "||", "|", "&", "|&", "(", ")", "((", "))", ";;", "\n"}
_WRAPPERS = {"sudo", "env", "nohup", "time", "command", "exec", "nice", "ionice", "stdbuf", "timeout",
             "xargs", "doas", "builtin", "caffeinate", "srun", "chronic", "unbuffer"}
# Wrapper options that take a separate value (`sudo -u bob`, `nice -n 10`, `srun -n 1`).
_WRAPPER_VALUE_OPTS = {
    "sudo": {"-u", "-g", "-C", "-D", "-h", "-p", "-r", "-t", "-U", "-T"},
    "doas": {"-u", "-C"},
    "env": {"-u", "-C", "-S", "--unset", "--chdir", "--split-string"},
    "nice": {"-n", "--adjustment"},
    "ionice": {"-c", "-n", "-p", "-P", "-u", "--class", "--classdata"},
    "stdbuf": {"-i", "-o", "-e"},
    "timeout": {"-s", "-k", "--signal", "--kill-after"},
    "xargs": {"-I", "-i", "-n", "-P", "-L", "-l", "-d", "-E", "-e", "-s", "-a", "--max-args", "--max-procs",
              "--delimiter", "--arg-file", "--replace", "--max-lines", "--max-chars", "--eof"},
    "srun": {"-n", "-N", "-c", "-t", "-p", "-A", "-J", "-o", "-e", "-w", "-x", "-G", "-C", "-D", "-q",
             "--ntasks", "--nodes", "--cpus-per-task", "--time", "--partition", "--account", "--job-name",
             "--output", "--error", "--mem", "--mem-per-cpu", "--gres", "--gpus", "--constraint",
             "--chdir", "--qos", "--nodelist", "--exclude"},
    "caffeinate": {"-t", "-w"},
}
_SHELLS = {"bash", "sh", "zsh", "dash", "ksh", "fish"}
_SQL_CLIENTS = {"psql", "mysql", "mariadb", "sqlite3", "duckdb", "sqlcmd", "clickhouse-client", "bq", "snowsql", "cqlsh"}
_INTERPRETERS = {"python", "python3", "r", "rscript", "node", "ruby", "perl"}
_SQL = [
    (re.compile(r"(?is)\bdrop\s+(table|database|schema|view|index)\b"), "SQL DROP"),
    (re.compile(r"(?is)\btruncate\s+(table\s+)?[\w.\"`\[]"), "SQL TRUNCATE"),
    (re.compile(r"(?is)\bdelete\s+from\s+[\w.\"`\[\]]+(?![^;]*\bwhere\b)"), "SQL DELETE without WHERE"),
]
_CODE = [
    (re.compile(r"(?s)\bunlink\s*\((?:[^()]|\([^()]*\))*\brecursive\s*=\s*(TRUE|T)\b"), "R unlink(recursive = TRUE)"),
    (re.compile(r"\bfs::dir_delete\s*\("), "R fs::dir_delete"),
    (re.compile(r"\bshutil\s*\.\s*rmtree\s*\("), "Python shutil.rmtree"),
    (re.compile(r"\bfs\s*\.\s*(rmSync|rm)\s*\([^)]*recursive\s*:\s*true"), "Node fs.rm(recursive)"),
]


def _strip_comments(command):
    """Drop unquoted shell comments (`#` starting a word) up to the end of each line."""
    out, quote, i, n = [], None, 0, len(command)
    while i < n:
        c = command[i]
        if quote:
            if c == "\\" and quote == '"' and i + 1 < n:
                out.append(command[i : i + 2])
                i += 2
                continue
            if c == quote:
                quote = None
        elif c == "\\" and i + 1 < n:
            out.append(command[i : i + 2])
            i += 2
            continue
        elif c in "'\"":
            quote = c
        elif c == "#" and (i == 0 or command[i - 1].isspace() or command[i - 1] in ";&|()"):
            j = command.find("\n", i)
            i = n if j < 0 else j
            continue
        out.append(c)
        i += 1
    return "".join(out)


def _split_segments(command):
    """Simple commands of a shell line: lists of words, split at separators and subshells."""
    import shlex

    text = _strip_comments(command).replace("`", " ; ").replace("$(", " ( ")
    try:
        lx = shlex.shlex(text, posix=True, punctuation_chars=";&|()<>")
        lx.whitespace_split = True
        lx.commenters = ""
        toks = list(lx)
    except ValueError:
        toks = text.split()
    segs, cur, skip_next = [], [], False
    for tok in toks:
        if skip_next:  # redirect target
            skip_next = False
            continue
        if tok in _SEPARATORS or (tok and all(c in ";&|()" for c in tok)):
            if cur:
                segs.append(cur)
            cur = []
        elif tok and all(c in "<>&|" for c in tok) and ("<" in tok or ">" in tok):
            skip_next = True
            if cur and cur[-1].isdigit():  # file-descriptor number of `2>` / `2>&1`
                cur.pop()
        else:
            cur.append(tok)
    if cur:
        segs.append(cur)
    return segs


def _shorts(words):
    """Letters of short-option clusters (-rf) and the set of long options (--force)."""
    short, long_ = set(), set()
    for w in words:
        if w.startswith("--"):
            long_.add(w.split("=", 1)[0])
        elif w.startswith("-") and len(w) > 1 and not w[1].isdigit():
            short.update(w[1:])
    return short, long_


def _strip_wrappers(words):
    i = 0
    while i < len(words):
        w = words[i]
        base = w.rsplit("/", 1)[-1]
        if re.match(r"^[A-Za-z_]\w*=", w):
            i += 1
        elif base in _WRAPPERS:
            i += 1
            takes = _WRAPPER_VALUE_OPTS.get(base, set())
            while i < len(words) and words[i].startswith("-"):  # wrapper options (timeout 10, xargs -0)
                i += 2 if words[i] in takes else 1
            if base == "timeout" and i < len(words) and re.match(r"^\d", words[i]):
                i += 1
        else:
            break
    return words[i:]


def _hit(label, words, severity="high"):
    import shlex

    match = shlex.join(words)
    if len(match) > 160:  # mark the cut so readers never take a clipped path for the target
        match = match[:159] + "…"
    return {"label": label, "match": match, "severity": severity}


def _segment_destructive(words, depth):
    words = _strip_wrappers(words)
    if not words:
        return None
    cmd = words[0].rsplit("/", 1)[-1].lower()
    args = words[1:]
    short, long_ = _shorts(args)
    if cmd in _SHELLS and "-c" in args[:3]:
        i = args.index("-c")
        return destructive(args[i + 1], depth + 1) if i + 1 < len(args) else None
    if cmd == "eval":
        return destructive(" ".join(args), depth + 1)
    if cmd == "ssh":
        rest = [a for a in args if not a.startswith("-")]
        return destructive(" ".join(rest[1:]), depth + 1) if len(rest) > 1 else None
    if cmd in ("echo", "printf", "print", ":", "true"):
        return None
    if cmd == "rm" and ("r" in short or "R" in short or "--recursive" in long_):
        return _hit("rm -rf" if ("f" in short or "--force" in long_) else "rm -r", words)
    if cmd == "mv" and len(args) >= 2 and args[-1] == "/dev/null":
        return _hit("mv to /dev/null", words)
    if cmd == "find" and ("-delete" in args or any(a in ("-exec", "-execdir", "-ok") and i + 1 < len(args)
                                                   and args[i + 1].rsplit("/", 1)[-1] == "rm"
                                                   for i, a in enumerate(args))):
        return _hit("find -delete" if "-delete" in args else "find -exec rm", words)
    if cmd == "rsync" and any(l.startswith("--delete") for l in long_) and not ("n" in short or "--dry-run" in long_):
        return _hit("rsync --delete", words)
    if cmd == "git":
        i = 0
        while i < len(args) and args[i].startswith("-"):  # global options: -C dir, -c k=v, --no-pager
            i += 2 if args[i] in ("-C", "-c", "--git-dir", "--work-tree", "--namespace") else 1
        if i >= len(args):
            return None
        sub, rest = args[i], args[i + 1:]
        rs, rl = _shorts(rest)
        if sub == "push":
            if "--force" in rl or "f" in rs or "--mirror" in rl or any(a.startswith("+") and len(a) > 1 for a in rest):
                return _hit("git push --force", words)
            if "--force-with-lease" in rl or "--force-if-includes" in rl:
                return _hit("git push --force-with-lease", words, "medium")
            if "--delete" in rl or ("d" in rs) or any(a.startswith(":") and len(a) > 1 for a in rest):
                return _hit("git push --delete", words)
        if sub == "reset" and ("--hard" in rl or "--merge" in rl or "--keep" in rl):
            return _hit("git reset --hard", words)
        if sub == "clean" and ("f" in rs or "--force" in rl) and not ("n" in rs or "--dry-run" in rl):
            return _hit("git clean -f", words)
        if sub == "checkout" and ("--" in rest or "." in rest):
            return _hit("git checkout -- (discard changes)", words)
        if sub == "restore" and rest and not ({"--staged", "-S"} & set(rest) and not ({"--worktree", "-W"} & set(rest))):
            if any(not a.startswith("-") for a in rest):
                return _hit("git restore (discard changes)", words)
        if sub == "stash" and rest[:1] and rest[0] in ("drop", "clear"):
            return _hit(f"git stash {rest[0]}", words)
        if sub == "branch" and ("D" in rs or ("--delete" in rl and ("--force" in rl or "f" in rs))):
            return _hit("git branch -D", words)
        return None
    if cmd in ("chmod", "chown", "chgrp") and ("R" in short or "--recursive" in long_):
        return _hit(f"{cmd} -R", words, "medium")
    if cmd.startswith("mkfs") or cmd in ("wipefs", "shred"):
        return _hit(cmd, words)
    if cmd == "dd" and any(a.startswith("of=") for a in args):
        return _hit("dd of=", words)
    if cmd == "scancel" and ("u" in short or "--user" in long_ or "--me" in long_):
        return _hit("scancel all jobs of a user", words)
    if cmd == "kubectl" and "delete" in args:
        return _hit("kubectl delete", words)
    if cmd in _SQL_CLIENTS or cmd in _INTERPRETERS:
        body = " ".join(args)
        for rx, label in _SQL:
            if rx.search(body):
                return _hit(label, words)
        for rx, label in _CODE:
            if rx.search(body):
                return _hit(label, words)
    return None


def destructive(command, depth=0):
    """{label, match, severity} for the first destructive simple command in a shell line, else None.

    Works on the full (redacted) command, so a trailing `&& rm -rf x` is seen even when the
    display summary is truncated. Quoted arguments of echo/printf/git commit are not commands."""
    if not isinstance(command, str) or not command.strip() or depth > 3:
        return None
    command = redact(command).replace("\\\n", " ")
    lines = command.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        i += 1
        m = re.search(r"<<-?\s*(['\"]?)([A-Za-z_]\w*)\1", line)
        if m:  # heredoc: its body is data, except for interpreters and SQL clients
            body = []
            while i < len(lines) and lines[i].strip() != m.group(2):
                body.append(lines[i])
                i += 1
            i += 1
            head = _strip_wrappers(line[: m.start()].split())
            cmd = head[0].rsplit("/", 1)[-1].lower() if head else ""
            if cmd in _SQL_CLIENTS or cmd in _INTERPRETERS:
                text = "\n".join(body)
                for rx, label in _SQL + _CODE:
                    if rx.search(text):
                        return _hit(label, head + ["<<" + m.group(2)])
            line = line[: m.start()] + line[m.end():]
        for words in _split_segments(line):
            hit = _segment_destructive(words, depth)
            if hit:
                return hit
    return None


def tool_destructive(tool, inp):
    if tool == "Bash" and isinstance(inp, dict) and isinstance(inp.get("command"), str):
        return destructive(inp["command"])
    return None


def tool_summary(hub, tool, inp):
    inp = inp if isinstance(inp, dict) else {}
    if tool == "Bash":
        return excerpt(inp.get("command"), 160, oneline=True) or excerpt(
            inp.get("description"), 160
        )
    for k in ("file_path", "notebook_path", "path"):
        if isinstance(inp.get(k), str):
            return excerpt(rel_path(hub, inp[k]), 160)
    if tool in ("Grep", "Glob"):
        return excerpt(inp.get("pattern"), 160, oneline=True)
    if tool == "WebFetch":
        return excerpt(inp.get("url"), 160)
    if tool == "WebSearch":
        return excerpt(inp.get("query"), 160, oneline=True)
    if tool in ("Task", "Agent"):
        return excerpt(
            " · ".join(
                str(x) for x in (inp.get("subagent_type"), inp.get("description")) if x
            ),
            160,
        )
    if tool == "TodoWrite" and isinstance(inp.get("todos"), list):
        return f"{len(inp['todos'])} todos"
    for v in inp.values():
        if isinstance(v, str) and v.strip():
            return excerpt(v, 160, oneline=True)
    return None


def shell_tokens(command):
    """Shell words with operators split out, from the redacted command; capped in count and length."""
    import shlex

    command = redact(command)
    try:
        lx = shlex.shlex(command, posix=True, punctuation_chars=True)
        lx.whitespace_split = True
        toks = list(lx)
    except ValueError:
        toks = command.split()
    return [x[:300] for x in toks[:400]]


def _is_op(tok):
    return bool(tok) and all(c in "();<>|&" for c in tok)


_PY = re.compile(r"^(?:.*/)?python[\d.]*$")
_HARMLESS = {"cd", "echo", "true", ":", "tail", "head", "cat", "sleep"}


def _this_dash(word, cwd):
    """True if word is the path of an installed copy of this skill's dash.py."""
    if not word.endswith("dash.py"):
        return False
    path = Path(os.path.expanduser(word))
    if not path.is_absolute():
        if not cwd:
            return False
        path = Path(cwd) / path
    try:
        real = path.resolve()
    except (OSError, RuntimeError):
        return False
    return real.name == "dash.py" and (real.parent / "dash_hook.py").is_file() and (real.parent.parent / "SKILL.md").is_file()


def dash_only(command, cwd=None):
    """True when a Bash command does nothing but run dash.py (plus harmless glue like cd, echo, redirects)."""
    toks = shell_tokens(command)
    segs, cur, redir = [], [], False
    for tok in toks + [";"]:
        if _is_op(tok):
            if cur:
                segs.append((cur, redir))
            cur, redir = [], (">" in tok or "<" in tok)
        else:
            cur.append(tok)
    ran_dash = False
    for words, after_redirect in segs:
        if after_redirect:
            words = words[1:]  # the redirect target
        if not words or (len(words) == 1 and words[0].isdigit()):
            continue
        i = 0
        while i < len(words) and (re.match(r"^[A-Za-z_]\w*=", words[i]) or words[i] == "env" or _PY.match(words[i])):
            i += 1
        if i >= len(words):
            continue
        w = words[i]
        nxt = words[i + 1] if i + 1 < len(words) else None
        if _this_dash(w, cwd) or (w.startswith("$") and nxt == "inbox" and "dash.py" in command):
            ran_dash = True
        elif w not in _HARMLESS:
            return False
    return ran_dash


def _response_text(resp):
    """stdout/stderr text and an exit code (None if unknown) from a tool_response of any shape."""
    if isinstance(resp, str):
        return resp, "", None
    if not isinstance(resp, dict):
        return "", "", None
    out = resp.get("stdout") if isinstance(resp.get("stdout"), str) else ""
    if not out:
        for k in ("output", "content", "result"):
            if isinstance(resp.get(k), str):
                out = resp[k]
                break
    err = resp.get("stderr") if isinstance(resp.get("stderr"), str) else ""
    code = None
    for k in ("returncode", "exit_code", "exitCode", "returnCode", "return_code", "code", "status"):
        if isinstance(resp.get(k), int) and not isinstance(resp.get(k), bool):
            code = resp[k]
            break
    if code is None and resp.get("interrupted") is True:
        code = 130
    if code is None and resp.get("is_error") is True:
        code = 1
    return out, err, code


def _last_line(text):
    for ln in reversed((text or "").splitlines()):
        if ln.strip():
            return ln
    return None


def _touch_file(s, hub, path, edit, ts):
    rp = rel_path(hub, path)
    if not rp:
        return
    files = s.setdefault("files", {})
    f = files.get(rp)
    if f is None:
        f = files[rp] = {"edits": 0, "reads": 0}
        s["stats"]["files_touched"] = s["stats"].get("files_touched", 0) + 1
    f["edits" if edit else "reads"] = f.get("edits" if edit else "reads", 0) + 1
    f["last"] = ts
    if edit:
        f["last_edit"] = ts
    if len(files) > FILES_KEEP:
        for p, _ in sorted(files.items(), key=lambda x: x[1].get("last") or "")[
            : len(files) - FILES_KEEP
        ]:
            del files[p]


def _clear_attention(s, kinds):
    s["attention"] = [a for a in s.get("attention", []) if a.get("kind") not in kinds]


def _deny_reason():
    return (
        "The user paused this session from the dashboard. Stop working now: do not call more tools, "
        "briefly say where you stopped, and end your turn. The user will resume it from the dashboard "
        "or by sending a new message."
    )


def handle_hook(hub, p):
    """Record one Claude Code hook event. Returns the JSON object to print, or None."""
    return hook_output(hub, p)[0]


def hook_output(hub, p):
    """(output or None, session id, delivered message ids).

    If recording fails after messages were taken, they go back to the queue before the error
    propagates; the caller returns them too if it cannot emit the output."""
    holder = []
    try:
        out = _handle_hook(hub, p, holder)
    except BaseException:
        if holder and getattr(holder[-1], "taken", None):
            rollback_messages(hub, holder[-1].sid, holder[-1].taken)
        raise
    ids = getattr(holder[-1], "taken", []) if holder else []
    return out, (holder[-1].sid if holder else None), (ids if out else [])


def rollback_messages(hub, sid, ids):
    """Put delivered-but-never-emitted messages back in the queue."""
    if not ids:
        return
    with SessionEdit(hub, sid) as ed:
        with open(ed.sd / "inbox.jsonl", "a", encoding="utf-8") as f:
            for mid in ids:
                f.write(dump({"op": "status", "id": mid, "status": "queued"}) + "\n")
        for mid in ids:
            ed.event("message", summary=f"Returned {mid} to the queue (delivery failed)", ok=False)


def _handle_hook(hub, p, holder):
    if not isinstance(p, dict):
        return None
    ev = p.get("hook_event_name")
    sid = p.get("session_id")
    if not isinstance(ev, str) or not isinstance(sid, str) or not SID_RE.match(sid):
        return None
    if ev not in HOOK_EVENTS:
        return None
    t = now()
    te = time.time()
    agent_id = p.get("agent_id") if isinstance(p.get("agent_id"), str) else None
    agent_type = p.get("agent_type") if isinstance(p.get("agent_type"), str) else None
    sub = agent_type or (agent_id[:8] if agent_id else None)
    tool = p.get("tool_name") if isinstance(p.get("tool_name"), str) else None
    inp = p.get("tool_input") if isinstance(p.get("tool_input"), dict) else {}
    tuid = p.get("tool_use_id") if isinstance(p.get("tool_use_id"), str) else None
    out = None
    significant = True
    create = {
        "agent": "claude",
        "label": "",
        "cwd": p.get("cwd") if isinstance(p.get("cwd"), str) else "",
    }
    if not hub.sdir(sid).is_dir():
        adopt_cli_session(hub, sid)
    holder.append(SessionEdit(hub, sid, create=create))
    with holder[-1] as ed:
        s = ed.s
        plan = load_json(ed.sd / "plan.json")
        paused = paused_since(ed.sd)
        before = base_activity(s, paused, plan, te)[0]
        s["hooks"] = True
        s["last_seen"] = t
        rewoken = s.pop("rewake_pending", None) if ev not in ("Notification", "SessionStart") else None
        if rewoken and ev == "UserPromptSubmit" and not _prompt_is_rewake(p):
            # The idle wake-up never produced a turn: hand those messages over again.
            s["redeliver"] = rewoken
        if agent_id and agent_id not in s.setdefault("subagent_ids", []):
            s["subagent_ids"] = (s["subagent_ids"] + [agent_id])[-200:]
            s["stats"]["subagents"] = s["stats"].get("subagents", 0) + 1

        if ev == "SessionStart":
            src = p.get("source") if isinstance(p.get("source"), str) else "startup"
            title = p.get("session_title") or p.get("title")
            if isinstance(title, str) and title.strip():
                s["label"] = excerpt(title, 80, oneline=True)
            if isinstance(p.get("cwd"), str):
                s["cwd"] = p["cwd"]
            s["ended"] = None
            s["end_reason"] = None
            if s.get("turn") is None:
                s["turn"], s["turn_since"] = "idle", t
            env_file = os.environ.get("CLAUDE_ENV_FILE")
            if env_file:
                # Bash calls in this session then carry DASH_SESSION for dash.py.
                line = f"export DASH_SESSION={sid}\n"
                with contextlib.suppress(OSError):
                    have = Path(env_file).read_text() if Path(env_file).exists() else ""
                    if line not in have:
                        with open(env_file, "a", encoding="utf-8") as f:
                            f.write(
                                ("" if not have or have.endswith("\n") else "\n") + line
                            )
            ed.event(
                "session",
                summary=f"Session {src}",
                detail=excerpt(
                    p.get("model") if isinstance(p.get("model"), str) else None, 80
                ),
            )

        elif ev == "UserPromptSubmit":
            text = p.get("prompt") if isinstance(p.get("prompt"), str) else p.get("prompt_text")
            text = text if isinstance(text, str) else ""
            s["last_prompt"] = {"ts": t, "text": excerpt(text, 280) or ""}
            if not s.get("label"):
                s["label"] = excerpt(text, 60, oneline=True) or ""
            s["turn"], s["turn_since"] = "active", t
            s["stats"]["turns"] = s["stats"].get("turns", 0) + 1
            s["inflight"] = {}
            _clear_attention(s, ("permission", "idle", "input"))
            ed.event("prompt", summary=excerpt(text, 160, oneline=True))
            msg = take_messages(ed, "UserPromptSubmit")
            again = redeliver(ed, s.pop("redeliver", None))
            msg = "\n\n".join(x for x in (again, msg) if x) or None
            if msg:
                out = {
                    "hookSpecificOutput": {
                        "hookEventName": "UserPromptSubmit",
                        "additionalContext": msg,
                    }
                }

        elif ev == "PreToolUse":
            significant = bool(paused)  # otherwise debounced; the trailing flush publishes it
            if s.get("turn") != "active":
                s["turn"], s["turn_since"] = "active", t
            cmd = (
                inp.get("command")
                if tool == "Bash" and isinstance(inp.get("command"), str)
                else None
            )
            if paused and not (cmd and dash_only(cmd, p.get("cwd"))):
                ed.event(
                    "tool",
                    tool=tool,
                    summary=tool_summary(hub, tool, inp),
                    detail="Denied: session paused",
                    ok=False,
                    subagent=sub,
                )
                out = {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": _deny_reason(),
                    }
                }
            else:
                key = tuid or f"t{te}"
                entry = {
                    "tool": tool,
                    "summary": tool_summary(hub, tool, inp),
                    "started": t,
                    "epoch": te,
                    "subagent": sub,
                    "destructive": tool_destructive(tool, inp),
                }
                if cmd and "dash.py" in cmd:
                    entry["argv"] = shell_tokens(cmd)
                infl = s.setdefault("inflight", {})
                infl[key] = entry
                if len(infl) > 50:
                    for k in sorted(infl, key=lambda k: infl[k].get("epoch", 0))[
                        : len(infl) - 50
                    ]:
                        del infl[k]

        elif ev in ("PostToolUse", "PostToolUseFailure"):
            significant = False
            failed = ev == "PostToolUseFailure"
            entry = (s.get("inflight") or {}).pop(tuid, None) if tuid else None
            if entry is None and s.get("inflight"):
                # No tool_use_id: drop the oldest in-flight call of this tool.
                cands = [k for k, v in s["inflight"].items() if v.get("tool") == tool]
                if cands:
                    entry = s["inflight"].pop(
                        min(cands, key=lambda k: s["inflight"][k].get("epoch", 0))
                    )
            dur = p.get("duration_ms")
            if not isinstance(dur, (int, float)) or isinstance(dur, bool):
                dur = (
                    int((te - entry["epoch"]) * 1000)
                    if entry and entry.get("epoch")
                    else None
                )
            else:
                dur = int(dur)
            resp = p.get("tool_response")
            if resp is None:
                resp = p.get("tool_output")
            stdout, stderr, code = _response_text(resp)
            err = p.get("error") or p.get("tool_error")
            if isinstance(err, dict):
                err = err.get("message") or json.dumps(err)
            err = err if isinstance(err, str) else ""
            m = re.match(r"^Exit code (\d+)\s*\n?", err)
            if m:  # failed Bash: "Exit code 1\n<output>"
                code, err = int(m.group(1)), err[m.end():]

            ok = not failed and (code is None or code == 0)
            s["stats"]["tool_calls"] = s["stats"].get("tool_calls", 0) + 1
            if not ok:
                s["stats"]["failures"] = s["stats"].get("failures", 0) + 1
            detail = None
            if tool == "Bash":
                s["stats"]["commands"] = s["stats"].get("commands", 0) + 1
                if ok:
                    detail = excerpt(_last_line(stdout), 200, oneline=True)
                else:
                    body = err or stderr or _last_line(stdout) or ""
                    if code and not body.startswith("Exit code"):
                        body = f"Exit code {code}\n{body}"
                    detail = excerpt(body, 300)
            elif not ok:
                detail = excerpt(err or stderr, 300)
            if tool in EDIT_TOOLS:
                s["stats"]["edits"] = s["stats"].get("edits", 0) + 1
            path = inp.get("file_path") or inp.get("notebook_path")
            if tool in EDIT_TOOLS and ok:
                _touch_file(s, hub, path, True, t)
            elif tool in READ_TOOLS and ok:
                _touch_file(s, hub, path, False, t)
            _clear_attention(s, ("permission",))
            summ = tool_summary(hub, tool, inp)
            ed.event(
                "tool",
                tool=tool,
                summary=summ,
                detail=detail,
                ok=ok,
                duration_ms=dur,
                subagent=sub,
            )
            if tool == "Bash":
                cmd = inp.get("command") if isinstance(inp.get("command"), str) else ""
                res = parse_tests("\n".join(x for x in (stdout, stderr, err) if x), cmd)
                if res:
                    s["tests"] = (
                        s.get("tests", [])
                        + [
                            {
                                "ts": t,
                                "runner": res["runner"],
                                "passed": res["passed"],
                                "failed": res["failed"],
                                "skipped": res["skipped"],
                                "command": excerpt(cmd, 160, oneline=True),
                            }
                        ]
                    )[-TESTS_KEEP:]
                    bits = [
                        f"{res[k]} {k}"
                        for k in ("passed", "failed", "skipped")
                        if res[k] is not None
                    ]
                    ed.event(
                        "test",
                        tool="Bash",
                        summary=f"{res['runner']}: " + ", ".join(bits),
                        detail=res.get("detail"),
                        ok=res["failed"] == 0,
                        subagent=sub,
                    )
                    significant = True
            msg = take_messages(ed, ev)
            if msg:
                significant = True
                out = {
                    "hookSpecificOutput": {
                        "hookEventName": ev,
                        "additionalContext": msg,
                    }
                }

        elif ev == "Notification":
            text = p.get("message") if isinstance(p.get("message"), str) else ""
            ntype = (
                p.get("notification_type")
                if isinstance(p.get("notification_type"), str)
                else ""
            )
            low = text.lower()
            if ntype == "permission_prompt" or (not ntype and "permission" in low):
                kind = "permission"
            elif ntype == "idle_prompt" or (
                not ntype and ("waiting for your input" in low or "idle" in low)
            ):
                kind = "idle"
            elif ntype == "elicitation_dialog":
                kind = "input"
            else:
                kind = "notice"
            item = {"kind": kind, "text": excerpt(text, 200) or kind, "ts": t}
            if kind == "permission":
                # The tool awaiting permission is the latest in-flight call (recorded at PreToolUse).
                infl = list((s.get("inflight") or {}).values())
                last = max(infl, key=lambda x: x.get("epoch", 0)) if infl else None
                item["destructive"] = last.get("destructive") if last else None
            s.setdefault("attention", []).append(item)
            s["attention"] = s["attention"][-ATTENTION_KEEP:]
            ed.event(
                "notify",
                summary=excerpt(text, 160, oneline=True) or kind,
                detail=ntype or None,
            )

        elif ev == "Stop":
            s["inflight"] = {}
            _clear_attention(s, ("permission",))
            active = bool(p.get("stop_hook_active"))
            msg = None if active else take_messages(ed, "Stop")
            if msg:
                out = {"decision": "block", "reason": msg}
                ed.event(
                    "turn_end",
                    summary="Turn continued for a dashboard message",
                    ok=True,
                )
            else:
                s["turn"], s["turn_since"] = "idle", t
                last = p.get("last_assistant_message")
                ed.event(
                    "turn_end",
                    summary="Turn finished",
                    detail=excerpt(last, 200) if isinstance(last, str) else None,
                    ok=True,
                )

        elif ev == "SubagentStop":
            significant = False
            if agent_id and agent_id not in s["subagent_ids"]:
                s["subagent_ids"].append(agent_id)
                s["stats"]["subagents"] = s["stats"].get("subagents", 0) + 1
            for k in [
                k
                for k, v in (s.get("inflight") or {}).items()
                if sub and v.get("subagent") == sub
            ]:
                del s["inflight"][k]
            ed.event(
                "session",
                summary=f"Subagent finished: {sub or 'subagent'}",
                subagent=sub,
                ok=True,
            )

        elif ev == "SessionEnd":
            reason = p.get("reason") if isinstance(p.get("reason"), str) else None
            s["ended"], s["end_reason"] = t, reason
            s["inflight"] = {}
            s["turn"], s["turn_since"] = "idle", t
            _clear_attention(s, ("permission", "idle", "input"))
            ed.event(
                "session", summary="Session ended" + (f" ({reason})" if reason else "")
            )

        else:
            ed.changed = False
            return None
        after = base_activity(s, paused, plan, te)[0]
        if after != before:
            s["activity_since"] = t
            significant = True
    try:  # the output above is already committed; never lose it to a late failure
        bump(hub)
        regen(hub, significant)
        mote_kick(hub)
    except Exception as err:
        log_error(hub, err)
    return out


def log_error(hub, err):
    """Append a traceback to .dashboard/hook-errors.log, keeping the file bounded."""
    import traceback

    try:
        path = hub.d / "hook-errors.log"
        with contextlib.suppress(OSError):
            if path.stat().st_size > 64 * 1024:
                keep = path.read_bytes()[-32 * 1024 :]
                path.write_bytes(keep)
        with open(path, "a", encoding="utf-8") as f:
            f.write(now() + " " + "".join(traceback.format_exception(type(err), err, err.__traceback__))[-4000:] + "\n")
    except Exception:
        pass


def adopt_cli_session(hub, sid):
    """Link a brand-new Claude session to the CLI session its own `dash.py init` just created.

    Happens when the hub did not exist at SessionStart, so the hooks had no session to bind to."""
    with locked(hub.d / ".lock"):
        if hub.sdir(sid).is_dir():
            return None
        t = time.time()
        cands = []
        for other in hub.session_ids():
            o = load_json(hub.sdir(other) / "session.json")
            if isinstance(o, dict) and not o.get("hooks") and (o.get("adoptable_until") or 0) > t:
                cands.append(other)
        if len(cands) != 1:
            return None
        old = cands[0]
        os.rename(hub.sdir(old), hub.sdir(sid))
        o = load_json(hub.sdir(sid) / "session.json")
        o.update(id=sid, agent="claude", adopted_from=old, adoptable_until=None)
        atomic_write(hub.sdir(sid) / "session.json", dump(o) + "\n")
        aliases = load_json(hub.d / "aliases.json", {}) or {}
        aliases[old] = sid
        atomic_write(hub.d / "aliases.json", dump(aliases) + "\n")
    return old


def _prompt_is_rewake(p):
    """True when a prompt is the wake-up turn itself (Claude Code 2.1.286 starts it with a
    synthetic prompt carrying the Stop hook's output), not the user typing later."""
    text = p.get("prompt") if isinstance(p.get("prompt"), str) else p.get("prompt_text")
    return isinstance(text, str) and (
        "[Dashboard message from the user" in text or "[Dashboard answer from the user" in text
    )


def redeliver(ed, ids):
    if not ids:
        return None
    plan = load_json(ed.sd / "plan.json")
    msgs = [m for m in read_inbox(ed.sd) if m["id"] in ids]
    for m in msgs:
        ed.event("message", summary=f"Redelivered {m['id']} (idle wake-up did not start a turn)", ok=True)
    return "\n\n".join(frame(m, plan) for m in msgs) or None


# ---------------------------------------------------------------- session resolution


def _argv_match(argv, tokens):
    """argv must follow a dash.py (or $VAR) word and run to the end of that shell command."""
    n = len(argv)
    if n == 0 or not tokens:
        return False
    for i, tok in enumerate(tokens):
        if not (tok.endswith("dash.py") or (tok.startswith("$") and not _is_op(tok))):
            continue
        if tokens[i + 1 : i + 1 + n] != argv:
            continue
        rest = tokens[i + 1 + n :]
        if not rest or _is_op(rest[0]) or (rest[0].isdigit() and len(rest) > 1 and _is_op(rest[1])):
            return True
    return False


def pending_match(hub, argv, t=None):
    """Sessions whose recent in-flight Bash command is this dash.py call."""
    t = time.time() if t is None else t
    mine = [redact(x)[:300] for x in argv]
    hits = []
    for sid in hub.session_ids():
        s = load_json(hub.sdir(sid) / "session.json")
        if not isinstance(s, dict) or s.get("ended"):
            continue
        for e in (s.get("inflight") or {}).values():
            if (
                e.get("tool") == "Bash"
                and e.get("argv")
                and t - e.get("epoch", 0) <= PENDING_WINDOW
                and _argv_match(mine, e["argv"])
            ):
                hits.append((e.get("epoch", 0), sid))
    hits.sort(reverse=True)
    return [sid for _, sid in hits]


def live_sessions(hub, t=None):
    t = time.time() if t is None else t
    out = []
    for sid in hub.session_ids():
        sd = hub.sdir(sid)
        s = load_json(sd / "session.json")
        if isinstance(s, dict) and base_activity(s, None, None, t)[0] != "ended":
            out.append(sid)
    return out


def resolve_session(hub, a, argv=None):
    """(sid, source) or (None, reason)."""
    for src, val in (
        ("--session", getattr(a, "session", None)),
        ("DASH_SESSION", os.environ.get("DASH_SESSION")),
        ("CLAUDE_SESSION_ID", os.environ.get("CLAUDE_SESSION_ID")),
    ):
        if val:
            if not SID_RE.match(val):
                die(f"invalid session id from {src}: {val!r}")
            return hub.alias(val), src
    argv = sys.argv[1:] if argv is None else argv
    m = pending_match(hub, argv)
    if len(set(m)) > 1:
        return None, "the same dash.py command is in flight in sessions " + ", ".join(sorted(set(m)))
    if m:
        return m[0], "pending-command"
    live = live_sessions(hub)
    if len(live) == 1:
        return live[0], "only-live"
    return None, (
        "no live sessions" if not live else "several live sessions: " + ", ".join(live)
    )


def session_for(hub, a):
    sid, src = resolve_session(hub, a)
    if sid is None:
        listing = "\n".join(f"  {x}" for x in live_sessions(hub)) or "  (none)"
        die(
            f"cannot tell which session this is ({src}). Pass --session ID or set DASH_SESSION.\n"
            f"Live sessions:\n{listing}"
        )
    if not hub.exists(sid):
        die(
            f"no session {sid!r} in {hub.d} (run `dash.py init` or `dash.py join` first)"
        )
    return sid


def random_id(prefix):
    import secrets

    prefix = re.sub(r"[^A-Za-z0-9]", "", prefix or "cli")[:12] or "cli"
    return f"{prefix}-{secrets.token_hex(4)}"


def create_session(hub, sid, agent, label, cwd):
    with SessionEdit(
        hub, sid, create={"agent": agent, "label": label, "cwd": cwd}
    ) as ed:
        ed.s["last_seen"] = now()
        if ed.s.get("events_in_file", 0) == 0:
            ed.event("session", summary=f"Session joined ({agent})")


# ---------------------------------------------------------------- page


def page_version(html):
    """(major, minor, patch) from the page's version marker; (-1,) for the placeholder; None if absent."""
    for rx in PAGE_MARKS:
        m = rx.search(html or "")
        if m:
            if m.group(4):
                return (-1,)
            return tuple(int(x or 0) for x in m.groups()[:3])
    return None


PLACEHOLDER = """<!doctype html>
<!-- dashboard-page v2.0 placeholder -->
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Agent dashboard</title>
<style>
:root{color-scheme:light dark;--bg:#fff;--fg:#1a1a1a;--mute:#666;--line:#ddd}
@media (prefers-color-scheme:dark){:root{--bg:#141414;--fg:#eee;--mute:#999;--line:#333}}
body{margin:0;padding:16px;background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,sans-serif}
.s{border-top:1px solid var(--line);padding:8px 0}.m{color:var(--mute)}
</style></head><body>
<h1>Agent dashboard</h1><p class="m">Placeholder page: the full page ships with the skill.</p>
<div id="out" class="m">Waiting for data.js…</div>
<script>
function esc(s){return String(s==null?"":s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]))}
window.__hub=function(h){document.getElementById("out").innerHTML=h.sessions.map(s=>
'<div class="s"><b>'+esc(s.label||s.short)+'</b> <span class="m">'+esc(s.agent)+' · '+esc(s.activity)+
(s.current?' · '+esc(s.current.tool)+' '+esc(s.current.summary):'')+'</span></div>').join("")||"No sessions yet."};
function load(){var x=document.createElement("script");x.src="data.js?t="+Date.now();x.onload=x.onerror=function(){x.remove()};document.head.appendChild(x)}
load();setInterval(load,3000);
</script></body></html>
"""


def install_page(hub):
    """Copy the shipped page (and bundled assets) when missing or older."""
    import shutil

    src = SKILL / "assets" / "dashboard.html"
    html = src.read_text(encoding="utf-8") if src.is_file() else PLACEHOLDER
    new_v = page_version(html) or (-1,)
    dst = hub.d / "index.html"
    try:
        cur = dst.read_text(encoding="utf-8")
    except OSError:
        cur = None
    cur_v = page_version(cur) if cur is not None else None
    # Keep a newer installed page; replace older, unversioned (v1) or same-version-but-changed pages.
    if cur_v is not None and (cur_v > new_v or (cur_v == new_v and cur == html)):
        return dst
    atomic_write(dst, html)
    fonts = SKILL / "assets" / "fonts"
    if src.is_file() and fonts.is_dir() and re.search(r"""(?:url\(|src=)["']?fonts/""", html):
        target = hub.d / "fonts"
        shutil.rmtree(target, ignore_errors=True)
        shutil.copytree(fonts, target)
    return dst


def exclude_from_git(d):
    """Keep .dashboard/ out of commits without touching the tracked .gitignore."""
    import subprocess

    def git(*args):
        return subprocess.run(
            ["git", *args], cwd=d, capture_output=True, text=True, check=True, timeout=5
        ).stdout.strip()

    try:
        top = git("rev-parse", "--show-toplevel")
        # --git-path resolves to the common dir, which is what git reads in worktrees too.
        ex = Path(git("rev-parse", "--git-path", "info/exclude"))
    except (subprocess.SubprocessError, OSError):
        return
    if not ex.is_absolute():
        ex = d / ex
    rel = os.path.relpath(d, top)
    if rel.startswith(".."):
        return
    # Git exclude patterns are globs, including literal brackets in directory names.
    rel = "".join("\\" + c if c in "\\*?[]" else c for c in rel)
    line = f"/{rel}/"
    have = ex.read_text().splitlines() if ex.exists() else []
    if line not in have:
        ex.parent.mkdir(parents=True, exist_ok=True)
        with ex.open("a") as f:
            f.write(("\n" if have and have[-1] else "") + line + "\n")


# ---------------------------------------------------------------- narrative commands


class PlanEdit:
    """Load, change and save a session plan under the session lock.
    Set .msg inside the block to add a log line and a timeline note."""

    def __init__(self, hub, sid):
        self.hub, self.sid = hub, sid
        self.msg = None

    def __enter__(self):
        self.ed = SessionEdit(self.hub, self.sid)
        self.ed.__enter__()
        self.p = load_json(self.ed.sd / "plan.json")
        if not isinstance(self.p, dict):
            self.ed.__exit__(None, None, None)
            die(
                f'session {self.sid} has no plan yet (run `dash.py init "Title"` first)'
            )
        return self

    def __exit__(self, et, ev, tb):
        try:
            if et is None:
                t = now()
                if self.msg:
                    self.p.setdefault("log", []).append({"ts": t, "text": self.msg})
                    self.p["log"] = self.p["log"][-LOG_KEEP:]
                    self.ed.event("note", summary=excerpt(self.msg, 200, oneline=True))
                atomic_write(
                    self.ed.sd / "plan.json",
                    json.dumps(self.p, indent=2, ensure_ascii=False) + "\n",
                )
                self.ed.s["last_seen"] = t
        finally:
            self.ed.__exit__(et, ev, tb)
        if et is None:
            bump(self.hub)
            regen(self.hub)
        return False


def _max_num(items, prefix):
    n = 0
    for it in items or []:
        tail = str(it.get("id", "")).upper() if isinstance(it, dict) else ""
        tail = tail[len(prefix):] if tail.startswith(prefix) else tail
        if tail.isdigit():
            n = max(n, int(tail))
    return n


def session_next_id(sess, items, prefix):
    """Next Q/B id for a session. The counter lives in session.json and survives `init --force`,
    so an id is never reused within a session (an old inbox answer to Q1 cannot hit a new Q1)."""
    seq = sess.setdefault("seq", {})
    n = max(int(seq.get(prefix, 0) or 0), _max_num(items, prefix)) + 1
    seq[prefix] = n
    return f"{prefix}{n}"


def next_id(items, prefix):
    n = 0
    for it in items:
        tail = str(it.get("id", "")).upper()
        tail = tail[len(prefix) :] if tail.startswith(prefix) else tail
        if tail.isdigit():
            n = max(n, int(tail))
    return f"{prefix}{n + 1}"


def find(items, ident, kind):
    ident = str(ident).strip().upper()
    for it in items:
        if str(it.get("id")).upper() == ident:
            return it
    die(f"no {kind} with id {ident!r}")


def reopen(p, status="on_track"):
    if p.get("status") == "done":
        p.update(status=status, status_note="", status_updated=now())
        p["finished"] = None


def cmd_init(a):
    hub = find_hub(a.dir, create=True)
    page = install_page(hub)
    exclude_from_git(hub.d)
    sid, src = resolve_session(hub, a)
    created = False
    if sid is None and src.startswith("the same dash.py command"):
        die(f"cannot tell which session this is ({src}); pass --session ID")
    if sid is None or src == "only-live":  # a new plan never lands in someone else's lane
        sid = random_id(a.agent or "cli")
        created = True
    if not hub.exists(sid):
        agent = a.agent or ("claude" if src == "CLAUDE_SESSION_ID" else "cli")
        create_session(hub, sid, agent, a.label or a.title, os.getcwd())
        if created and os.environ.get("CLAUDECODE"):
            # Run from a Claude Code session whose hooks have not seen this hub yet: its next
            # hook event adopts this session (see adopt_cli_session).
            with SessionEdit(hub, sid) as ed:
                ed.s["adoptable_until"] = time.time() + 120
    t = now()
    tasks = []
    for i, spec in enumerate(a.task or [], 1):
        title, _, detail = spec.partition("|")
        if not title.strip():
            die(f"task {i} has no title")
        tasks.append(
            {
                "id": i,
                "title": title.strip(),
                "detail": detail.strip(),
                "status": "todo",
                "note": None,
                "started": None,
                "finished": None,
            }
        )
    with SessionEdit(hub, sid) as ed:
        pp = ed.sd / "plan.json"
        if pp.exists() and not a.force:
            die(f"session {sid} already has a plan (use --force to start over)")
        old = load_json(pp)
        if isinstance(old, dict):  # carry id counters over the reset
            seq = ed.s.setdefault("seq", {})
            for prefix, key in (("Q", "questions"), ("B", "blockers")):
                seq[prefix] = max(int(seq.get(prefix, 0) or 0), _max_num(old.get(key), prefix))
        plan = {
            "title": a.title,
            "goal": a.goal or "",
            "context": a.context or "",
            "status": "on_track",
            "status_note": "",
            "status_updated": t,
            "started": t,
            "finished": None,
            "tasks": tasks,
            "questions": [],
            "blockers": [],
            "metrics": [],
            "deliverables": [],
            "log": [{"ts": t, "text": "Dashboard started"}],
        }
        atomic_write(pp, json.dumps(plan, indent=2, ensure_ascii=False) + "\n")
        if a.label:
            ed.s["label"] = a.label
        elif not ed.s.get("label"):
            ed.s["label"] = a.title
        if a.agent:
            ed.s["agent"] = a.agent
        ed.s["last_seen"] = t
        ed.event("note", summary=f"Plan started: {excerpt(a.title, 160, oneline=True)}")
    bump(hub)
    regen(hub)
    mote_kick(hub)
    print(page)
    if created:
        print(f"DASH_SESSION={sid}")
        print(
            f"dash: new session {sid}. Pass --session {sid} or export DASH_SESSION={sid} on later calls "
            f"if more than one session is live.",
            file=sys.stderr,
        )
    return hub, sid


def cmd_join(a):
    hub = find_hub(a.dir, create=True)
    install_page(hub)
    exclude_from_git(hub.d)
    sid = a.session or random_id(a.agent)
    create_session(hub, sid, a.agent, a.label or "", os.getcwd())
    bump(hub)
    regen(hub)
    print(sid)
    return hub, sid


def cmd_task(a, hub, sid):
    if a.status not in TASK_STATES:
        die(f"status must be one of {TASK_STATES}")
    with PlanEdit(hub, sid) as e:
        t = find(e.p["tasks"], a.id, "task")
        old, t["status"] = t.get("status"), a.status
        if a.status not in ("done", "skipped"):
            reopen(e.p)
        stamp = now()
        if a.status == "doing":
            if old in ("done", "skipped") or not t.get("started"):
                t["started"] = stamp
        if a.status in ("done", "skipped"):
            t["started"] = t.get("started") or stamp
            t["finished"] = stamp
        else:
            t["finished"] = None
        if a.note is not None:
            t["note"] = a.note
        e.msg = f"Task {t['id']} {t['title']}: {old} → {a.status}" + (
            f" ({a.note})" if a.note else ""
        )


def cmd_add_task(a, hub, sid):
    with PlanEdit(hub, sid) as e:
        reopen(e.p)
        tasks = e.p["tasks"]
        new = {
            "id": int(next_id(tasks, "")),
            "title": a.title,
            "detail": a.detail or "",
            "status": "todo",
            "note": None,
            "started": None,
            "finished": None,
        }
        if a.after is not None:
            tasks.insert(tasks.index(find(tasks, a.after, "task")) + 1, new)
        else:
            tasks.append(new)
        e.msg = f"Added task {new['id']}: {a.title}"
    print(new["id"])


def cmd_ask(a, hub, sid):
    with PlanEdit(hub, sid) as e:
        q = {
            "id": session_next_id(e.ed.s, e.p["questions"], "Q"),
            "text": a.question,
            "default": a.default,
            "asked": now(),
            "answer": None,
            "answered": None,
            "answered_via": None,
        }
        e.p["questions"].append(q)
        e.msg = f"{q['id']} asked: {a.question} (default: {a.default})"
    print(q["id"])


def cmd_answer(a, hub, sid):
    with PlanEdit(hub, sid) as e:
        q = find(e.p["questions"], a.id, "question")
        q.update(answer=a.answer, answered=now(), answered_via="chat")
        e.msg = f"{q['id']} answered: {a.answer}"


def cmd_block(a, hub, sid):
    with PlanEdit(hub, sid) as e:
        reopen(e.p, "at_risk")
        b = {
            "id": session_next_id(e.ed.s, e.p["blockers"], "B"),
            "text": a.what,
            "needs": a.needs or None,
            "opened": now(),
            "closed": None,
            "note": None,
        }
        e.p["blockers"].append(b)
        e.msg = f"{b['id']} blocked: {a.what}"
    print(b["id"])


def cmd_unblock(a, hub, sid):
    with PlanEdit(hub, sid) as e:
        b = find(e.p["blockers"], a.id, "blocker")
        b["closed"] = now()
        if a.note:
            b["note"] = a.note
        e.msg = f"{b['id']} cleared" + (f": {a.note}" if a.note else "")


def cmd_deliver(a, hub, sid):
    url = a.path.startswith(("http://", "https://"))
    p = a.path if url else str(Path(a.path).expanduser().resolve())
    with PlanEdit(hub, sid) as e:
        item = {
            "path": p,
            "label": a.label or Path(a.path).name,
            "ts": now(),
            "note": a.note or None,
        }
        e.p["deliverables"] = [x for x in e.p["deliverables"] if x.get("path") != p] + [
            item
        ]
        e.msg = f"Delivered {item['label']}"


def number(v):
    try:
        f = float(v)
    except ValueError:
        die(f"{v!r} is not a number (put units in --unit)")
    if not math.isfinite(f):
        die(f"{v!r} is not a finite number")
    return int(f) if f.is_integer() else f


def cmd_metric(a, hub, sid):
    value = number(a.value)
    total = number(a.total) if a.total is not None else None
    with PlanEdit(hub, sid) as e:
        ms = e.p["metrics"]
        m = next((x for x in ms if x.get("name") == a.name), None)
        if m is None:
            m = {
                "name": a.name,
                "value": None,
                "total": None,
                "unit": None,
                "good": None,
                "updated": None,
                "history": [],
            }
            ms.append(m)
        prev = m.get("value")
        m["value"] = value
        if total is not None:
            m["total"] = total
        if a.unit is not None:
            m["unit"] = a.unit
        if a.good is not None:
            m["good"] = a.good
        m["updated"] = now()
        m["history"] = (m.get("history", []) + [[m["updated"], value]])[-50:]
        if prev is None:
            e.msg = f"{a.name}: {value}"
        elif prev != value:
            e.msg = f"{a.name}: {prev} → {value}"


def cmd_status(a, hub, sid):
    if a.status not in OVERALL:
        die(f"status must be one of {OVERALL}")
    with PlanEdit(hub, sid) as e:
        if a.status == "done" and (
            any(t["status"] not in ("done", "skipped") for t in e.p["tasks"])
            or any(b.get("closed") is None for b in e.p["blockers"])
        ):
            die("cannot finish with unfinished tasks or open blockers")
        t = now()
        e.p.update(status=a.status, status_note=a.note or "", status_updated=t)
        e.p["finished"] = t if a.status == "done" else None
        e.msg = f"Status: {a.status}" + (f" ({a.note})" if a.note else "")


def cmd_log(a, hub, sid):
    with PlanEdit(hub, sid) as e:
        e.msg = a.message


def cmd_show(a, hub, sid):
    v = session_view(hub, sid)
    if v is None:
        die(f"session {sid} is unreadable")
    v.pop("_edits", None)
    if a.json:
        print(json.dumps(v, indent=2, ensure_ascii=False))
        return
    p = v["plan"]
    head = f"{v['label'] or sid}  [{v['activity']}]  session {sid}  ({hub.d})"
    print(head)
    if not p:
        print('  no plan (run `dash.py init "Title"`)')
        return
    done = sum(t["status"] == "done" for t in p["tasks"])
    print(f"  {p['title']}  [{p['status']}]  {done}/{len(p['tasks'])} done")
    for t in p["tasks"]:
        print(f"  {t['id']:>3} {t['status']:<8} {t['title']}")
    for q in p["questions"]:
        if q["answer"] is None:
            print(f"  {q['id']} OPEN {q['text']}  → default: {q['default']}")
    for b in p["blockers"]:
        if b["closed"] is None:
            print(f"  {b['id']} BLOCKED {b['text']}")


def cmd_end(a, hub, sid):
    with SessionEdit(hub, sid) as ed:
        t = now()
        ed.s["ended"], ed.s["end_reason"], ed.s["last_seen"] = t, "dash.py end", t
        ed.s["inflight"] = {}
        ed.event("session", summary="Session ended (dash.py end)")
    bump(hub)
    regen(hub)


def cmd_inbox(a, hub, sid):
    pass  # the caller prints pending messages for every session-scoped command


def print_inbox(hub, sid, explicit=False):
    if not hub.exists(sid):
        return
    with SessionEdit(hub, sid) as ed:
        if not queued(ed.sd):
            ed.changed = False
            text = None
        else:
            text = take_messages(ed, "cli")
    if text:
        bump(hub)
        regen(hub)
        print("\n" + text if not explicit else text)
    elif explicit:
        print("dash: no new dashboard messages")


def cmd_path(a):
    hub = find_hub(a.dir)
    print(hub.d / "index.html")


def desktop_open(target):
    import subprocess

    opener = "open" if sys.platform == "darwin" else "xdg-open"
    try:
        subprocess.run([opener, str(target)], check=True, timeout=15)
    except (OSError, subprocess.SubprocessError) as error:
        die(f"could not open {target}: {error}")


def cmd_open(a):
    hub = find_hub(a.dir)
    page = hub.d / "index.html"
    if not page.is_file():
        die(f"no dashboard page at {page}")
    desktop_open(page)
    print(page)


def cmd_sessions(a):
    hub = find_hub(a.dir)
    t = time.time()
    for sid in hub.session_ids():
        v = session_view(hub, sid, t)
        if v:
            print(
                f"{sid}\t{v['agent']}\t{v['activity']}\t{v['last_seen']}\t{v['label']}"
            )


def cmd_send(a):
    hub = find_hub(a.dir)
    mid = queue_message(hub, a.sid, a.kind, a.text, a.qid)
    regen(hub)
    print(mid)


def cmd_render(a):
    hub = find_hub(a.dir)
    install_page(hub)
    regen(hub)
    print(hub.d / "data.js")


def cmd_mote_refresh(a):
    hub = find_hub(a.dir)
    mote_refresh(hub)


# ---------------------------------------------------------------- server


def server_url(hub):
    info = load_json(hub.d / "server.json")
    if not isinstance(info, dict) or not pid_alive(info.get("pid")):
        return None
    try:
        token = (hub.d / ".token").read_text().strip()
    except OSError:
        return None
    return f"http://127.0.0.1:{info['port']}/#k={token}"


def _last_activity(hub):
    last = 0.0
    for sid in hub.session_ids():
        s = load_json(hub.sdir(sid) / "session.json")
        if isinstance(s, dict):
            last = max(last, epoch(s.get("last_seen")) or 0)
    return last


FILE_MAX = 50 * 1024 * 1024
FONT_TYPES = {
    ".woff2": "font/woff2",
    ".woff": "font/woff",
    ".ttf": "font/ttf",
    ".otf": "font/otf",
    ".css": "text/css; charset=utf-8",
}


def make_handler(hub, token, port, state):
    from http.server import BaseHTTPRequestHandler
    import hmac

    hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
    origins = {f"http://{h}" for h in hosts}
    route = re.compile(
        r"^/api/sessions/([A-Za-z0-9][A-Za-z0-9._-]{0,127})/(messages|pause|resume)$"
    )

    class Handler(BaseHTTPRequestHandler):
        server_version = "dash"
        sys_version = ""
        protocol_version = "HTTP/1.1"
        timeout = 30  # seconds a client may stall a connection

        def log_message(self, *args):
            pass

        def _send(self, code, body, ctype="application/json; charset=utf-8"):
            data = body if isinstance(body, bytes) else dump(body).encode()
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Cross-Origin-Resource-Policy", "same-origin")
            if getattr(self, "_closing", False):  # request body left unread: end the connection
                self.send_header("Connection", "close")
                self.close_connection = True
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(data)

        def _err(self, code, msg):
            self._send(code, {"ok": False, "error": msg})

        def _guard(self, api):
            if self.headers.get("Host") not in hosts:
                self._err(403, "bad host")
                return False
            origin = self.headers.get("Origin")
            if origin is not None and origin not in origins:
                self._err(403, "cross-origin request refused")
                return False
            if api:
                got = self.headers.get("X-Dash-Token")
                if not got:
                    self._err(401, "missing token")
                    return False
                if not hmac.compare_digest(got.encode(), token.encode()):
                    self._err(403, "wrong token")
                    return False
            return True

        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if not self._guard(path.startswith("/api/")):
                return
            try:
                if path in ("/", "/index.html"):
                    page = hub.d / "index.html"
                    self._send(200, page.read_bytes(), "text/html; charset=utf-8")
                elif path == "/api/hub":
                    mote_kick(hub)
                    self._send(200, build_snapshot(hub))
                elif path == "/api/file":
                    self._file(self.path.split("?", 1)[1] if "?" in self.path else "")
                elif (
                    re.match(r"^/fonts/[A-Za-z0-9._-]+$", path)
                    and Path(path).suffix in FONT_TYPES
                ):
                    self._send(
                        200,
                        (hub.d / path.lstrip("/")).read_bytes(),
                        FONT_TYPES[Path(path).suffix],
                    )
                else:
                    self._err(404, "not found")
            except OSError:
                self._err(404, "not found")

        do_HEAD = do_GET

        def _file(self, query):
            """Token-gated project file (e.g. a deliverable), sandboxed so it cannot script the dashboard."""
            import mimetypes
            import stat as st
            from urllib.parse import parse_qs, quote

            vals = parse_qs(query).get("path") or []
            if len(vals) != 1 or not os.path.isabs(vals[0]) or "\x00" in vals[0]:
                self._err(400, "give one absolute path")
                return
            real = os.path.realpath(vals[0])
            if not file_allowed(hub, real):
                self._err(403, "outside the project")
                return
            try:
                fd = os.open(real, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
            except OSError:
                self._err(404, "not found")
                return
            with os.fdopen(fd, "rb") as f:
                info = os.fstat(f.fileno())
                if not st.S_ISREG(info.st_mode):
                    self._err(404, "not a regular file")
                    return
                if info.st_size > FILE_MAX:
                    self._err(413, "file larger than 50 MB")
                    return
                ctype = mimetypes.guess_type(real)[0] or "application/octet-stream"
                if ctype.startswith("text/") or ctype in ("application/json", "application/javascript"):
                    ctype += "; charset=utf-8"
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(info.st_size))
                self.send_header("Content-Disposition",
                                 f"inline; filename*=UTF-8''{quote(os.path.basename(real))}")
                self.send_header("Content-Security-Policy", "sandbox allow-scripts allow-popups allow-downloads")
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Referrer-Policy", "no-referrer")
                self.send_header("Cross-Origin-Resource-Policy", "same-origin")
                self.end_headers()
                if self.command == "HEAD":
                    return
                while True:
                    chunk = f.read(1 << 20)
                    if not chunk:
                        break
                    self.wfile.write(chunk)

        def do_POST(self):
            path = self.path.split("?", 1)[0]
            self._closing = True  # until the body has been read
            if not self._guard(True):
                self.close_connection = True  # the body was not read
                return
            try:
                n = int(self.headers.get("Content-Length", ""))
            except ValueError:
                self._err(411, "Content-Length required")
                self.close_connection = True
                return
            if n < 0 or n > BODY_MAX:
                self._err(413, "body too large")
                self.close_connection = True
                return
            ctype = (
                (self.headers.get("Content-Type") or "").split(";")[0].strip().lower()
            )
            self._closing = False
            if ctype != "application/json":
                self.rfile.read(n)
                self._err(415, "JSON only")
                return
            try:
                body = json.loads(self.rfile.read(n).decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                self._err(400, "invalid JSON")
                return
            if not isinstance(body, dict):
                self._err(400, "expected a JSON object")
                return
            state["last_post"] = time.time()
            try:
                m = route.match(path)
                if m:
                    sid, action = m.groups()
                    if not hub.exists(sid):
                        self._err(404, "no such session")
                        return
                    if action == "messages":
                        mid = queue_message(
                            hub,
                            sid,
                            body.get("kind", "message"),
                            body.get("text"),
                            body.get("qid"),
                        )
                        regen(hub)
                        self._send(200, {"ok": True, "id": mid})
                    else:
                        set_paused(hub, sid, action == "pause")
                        regen(hub)
                        self._send(200, {"ok": True, "paused": action == "pause"})
                elif path == "/api/mote/post":
                    self._send(*mote_post(hub, body))
                else:
                    self._err(404, "not found")
            except DashError as e:
                self._err(400, str(e))

        def do_PUT(self):
            self._err(405, "method not allowed")

        do_DELETE = do_PATCH = do_PUT

    return Handler


def _under(path, base):
    return path == base or path.startswith(base.rstrip(os.sep) + os.sep)


def file_allowed(hub, real):
    """A resolved path may be served if it is in the project (or a recorded deliverable), never the hub."""
    if _under(real, os.path.realpath(hub.d)):
        return False
    if _under(real, os.path.realpath(hub.root)):
        return True
    for sid in hub.session_ids():
        plan = load_json(hub.sdir(sid) / "plan.json")
        for d in (plan or {}).get("deliverables", []) if isinstance(plan, dict) else []:
            p = d.get("path") if isinstance(d, dict) else None
            if isinstance(p, str) and os.path.isabs(p) and os.path.realpath(p) == real:
                return True
    return False


def mote_post(hub, body):
    import subprocess

    store = find_mote_store(hub.root)
    binary = mote_bin()
    if not store or not binary:
        return 404, {"ok": False, "error": "no mote store here"}
    text = body.get("text")
    topic = body.get("topic") or "general"
    if not isinstance(text, str) or not text.strip() or len(text) > TEXT_MAX:
        return 400, {"ok": False, "error": f"text must be 1-{TEXT_MAX} characters"}
    if not isinstance(topic, str) or not re.match(
        r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,63}$", topic
    ):
        return 400, {"ok": False, "error": "invalid topic"}
    try:
        p = subprocess.run(
            [
                binary,
                "--store",
                str(store),
                "--quiet",
                "discuss",
                "post",
                "--topic",
                topic,
                "--body",
                "-",
                "--json",
            ],
            input=text.strip(),
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(store.parent),
        )
    except (OSError, subprocess.SubprocessError) as e:
        return 502, {"ok": False, "error": f"mote failed: {e}"}
    if p.returncode != 0:
        return 502, {
            "ok": False,
            "error": excerpt(p.stderr, 200) or f"mote exit {p.returncode}",
        }
    try:
        post_id = json.loads(p.stdout).get("post_id")
    except (ValueError, AttributeError):
        post_id = None
    with contextlib.suppress(OSError):
        os.unlink(hub.d / "mote.json")
    mote_kick(hub)
    return 200, {"ok": True, "id": post_id}


def serve_foreground(hub, open_browser=False, announce=True):
    import secrets
    import signal
    import threading
    from http.server import ThreadingHTTPServer

    with contextlib.suppress(OSError):
        os.chmod(hub.d, 0o700)
    lock = open(hub.d / ".server.lock", "a")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        die(
            "a dashboard server is already running for this hub (`dash.py url` prints its address)"
        )
    token = secrets.token_urlsafe(32)
    atomic_write(hub.d / ".token", token + "\n", mode=0o600)
    install_page(hub)
    state = {"last_post": 0.0}
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), None)
    port = httpd.server_address[1]
    httpd.RequestHandlerClass = make_handler(hub, token, port, state)
    httpd.daemon_threads = True
    started = now()
    t0 = time.time()
    atomic_write(
        hub.d / "server.json",
        dump({"port": port, "pid": os.getpid(), "started": started}) + "\n",
        mode=0o600,
    )
    bump(hub)
    regen(hub)
    idle = float(os.environ.get("DASH_SERVER_IDLE") or IDLE_EXIT)

    def watchdog():
        while True:
            time.sleep(max(0.2, min(30.0, idle / 4)))
            last = max(t0, state["last_post"], _last_activity(hub))
            if time.time() - last > idle:
                httpd.shutdown()
                return

    threading.Thread(target=watchdog, daemon=True).start()
    signal.signal(
        signal.SIGTERM,
        lambda *_: threading.Thread(target=httpd.shutdown, daemon=True).start(),
    )
    url = f"http://127.0.0.1:{port}/#k={token}"
    if announce:  # a detached server logs to server.log, which must not hold the token
        print(url, flush=True)
    if open_browser:
        with contextlib.suppress(DashError):
            desktop_open(url)
    try:
        httpd.serve_forever(poll_interval=0.2)
    finally:
        httpd.server_close()
        info = load_json(hub.d / "server.json")
        if isinstance(info, dict) and info.get("pid") == os.getpid():
            with contextlib.suppress(OSError):
                os.unlink(hub.d / "server.json")
        with contextlib.suppress(Exception):
            bump(hub)
            regen(hub)
        lock.close()


def cmd_serve(a):
    import subprocess

    hub = find_hub(a.dir)
    url = server_url(hub)
    if url:
        die(f"a dashboard server is already running for this hub: {url}")
    if a.foreground:
        serve_foreground(hub, a.open, announce=not a.detached)
        return
    with contextlib.suppress(OSError):
        os.unlink(hub.d / "server.json")
    fd = os.open(hub.d / "server.log", os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    log = os.fdopen(fd, "a")
    proc = subprocess.Popen(
        [sys.executable, str(SCRIPT), "--dir", str(hub.d), "serve", "--foreground", "--detached"],
        stdin=subprocess.DEVNULL,
        stdout=log,
        stderr=log,
        start_new_session=True,
        close_fds=True,
    )
    deadline = time.time() + 10
    while time.time() < deadline:
        info = load_json(hub.d / "server.json")
        if isinstance(info, dict) and info.get("pid") == proc.pid:
            url = server_url(hub)
            print(url)
            if a.open:
                desktop_open(url)
            return
        if proc.poll() is not None:
            die(f"the server exited early; see {hub.d / 'server.log'}")
        time.sleep(0.05)
    die("the server did not start within 10 s")


def cmd_stop(a):
    import signal
    import subprocess

    hub = find_hub(a.dir)
    info = load_json(hub.d / "server.json")
    if not isinstance(info, dict) or not pid_alive(info.get("pid")):
        with contextlib.suppress(OSError):
            os.unlink(hub.d / "server.json")
        print("dash: no server running")
        return
    pid = info["pid"]
    try:
        cmdline = subprocess.run(
            ["ps", "-p", str(pid), "-o", "command="],
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        cmdline = ""
    if "dash.py" not in cmdline or "serve" not in cmdline:
        with contextlib.suppress(OSError):
            os.unlink(hub.d / "server.json")
        die(f"pid {pid} is not a dashboard server; removed the stale server.json")
    os.kill(pid, signal.SIGTERM)
    for _ in range(100):
        if not pid_alive(pid):
            break
        time.sleep(0.05)
    print("dash: server stopped")


def cmd_url(a):
    hub = find_hub(a.dir)
    url = server_url(hub)
    if not url:
        die("no server running (start one with `dash.py serve`)")
    print(url)


# ---------------------------------------------------------------- hook installation

HOOK_EVENTS = (
    "SessionStart",
    "UserPromptSubmit",
    "PreToolUse",
    "PostToolUse",
    "PostToolUseFailure",
    "Notification",
    "Stop",
    "SubagentStop",
    "SessionEnd",
)
TOOL_EVENTS = ("PreToolUse", "PostToolUse", "PostToolUseFailure")
HOOK_MARK = "dash_hook.py"


def hook_python():
    """A stable, fast-starting interpreter path for hook commands.

    Prefer python3 on PATH (e.g. /opt/homebrew/bin/python3, which survives upgrades), but not
    macOS's /usr/bin/python3 shim (slow to start) or a virtualenv that may disappear."""
    import shutil

    def usable(path):
        if not path or path == "/usr/bin/python3":
            return False
        return not (Path(path).parent.parent / "pyvenv.cfg").exists()

    found = shutil.which("python3")
    if usable(found):
        return found
    if sys.prefix == getattr(sys, "base_prefix", sys.prefix) and usable(sys.executable):
        return sys.executable
    return found or "python3"


def hook_entries(with_rewake=False):
    import shlex

    hook = SCRIPT.parent / "dash_hook.py"
    cmd = f"{shlex.quote(hook_python())} {shlex.quote(str(hook))}"
    out = {}
    for ev in HOOK_EVENTS:
        group = {"hooks": [{"type": "command", "command": cmd, "timeout": 10}]}
        if ev in TOOL_EVENTS:
            group = {"matcher": "*", **group}
        out[ev] = [group]
    if with_rewake:
        out["Stop"][0]["hooks"].append(
            {
                "type": "command",
                "command": cmd + " --watch-inbox",
                "async": True,
                "asyncRewake": True,
                "timeout": 7200,
            }
        )
    return out


def _is_ours(h):
    return isinstance(h, dict) and HOOK_MARK in str(h.get("command", ""))


def merge_hooks(settings, uninstall=False, with_rewake=False):
    """Return a new settings dict with our hooks removed and (unless uninstall) added once."""
    s = json.loads(json.dumps(settings))
    hooks = s.get("hooks")
    if hooks is None:
        hooks = {}
    if not isinstance(hooks, dict):
        die("settings `hooks` is not an object; refusing to edit it")
    for ev in list(hooks):
        groups = hooks[ev]
        if not isinstance(groups, list):
            continue
        kept = []
        for g in groups:
            if isinstance(g, dict) and isinstance(g.get("hooks"), list):
                g = dict(g, hooks=[h for h in g["hooks"] if not _is_ours(h)])
                if not g["hooks"]:
                    continue
            kept.append(g)
        if kept:
            hooks[ev] = kept
        else:
            del hooks[ev]
    if not uninstall:
        for ev, groups in hook_entries(with_rewake).items():
            hooks.setdefault(ev, []).extend(groups)
    if hooks:
        s["hooks"] = hooks
    else:
        s.pop("hooks", None)
    return s


def our_hooks(settings):
    """[{event, matcher, hook}] for every dashboard hook entry in a settings dict."""
    out = []
    hooks = settings.get("hooks") if isinstance(settings, dict) else None
    for ev, groups in (hooks.items() if isinstance(hooks, dict) else []):
        for g in groups if isinstance(groups, list) else []:
            if not isinstance(g, dict):
                continue
            for h in g.get("hooks") if isinstance(g.get("hooks"), list) else []:
                if _is_ours(h):
                    out.append({"event": ev, "matcher": g.get("matcher"), "hook": h})
    return out


def _hook_script(command):
    import shlex

    try:
        words = shlex.split(command)
    except ValueError:
        words = command.split()
    return next((w for w in words if w.endswith(HOOK_MARK)), None)


def hooks_status(settings, target):
    """Print what is installed; 0 when every event is hooked, else 1. Never prints other keys."""
    mine = our_hooks(settings)
    evset = {x["event"] for x in mine if "--watch-inbox" not in x["hook"].get("command", "")}
    events = [e for e in HOOK_EVENTS if e in evset] + sorted(evset - set(HOOK_EVENTS))

    missing = [e for e in HOOK_EVENTS if e not in events]
    rewake = any("--watch-inbox" in x["hook"].get("command", "") for x in mine)
    scripts = sorted({_hook_script(x["hook"].get("command", "")) or "?" for x in mine})
    here = str(SCRIPT.parent / "dash_hook.py")
    installed = bool(mine) and not missing
    print(f"settings: {target}")
    print(f"installed: {'yes' if installed else ('partial' if mine else 'no')}")
    print(f"events: {', '.join(events) or '-'}")
    if mine and missing:
        print(f"missing: {', '.join(missing)}")
    print(f"rewake: {'on (experimental)' if rewake else 'off'}")
    for sc in scripts:
        state = "this installation" if sc == here else ("missing file" if not Path(sc).is_file() else "another copy")
        print(f"script: {sc} ({state})")
    if not mine:
        print("dash: hooks not installed; run `dash.py install-hooks`", file=sys.stderr)
    return 0 if installed else 1


def cmd_install_hooks(a):
    if a.settings:
        target = Path(a.settings).expanduser()
    elif a.scope == "project":
        top = git_toplevel(Path.cwd()) or Path.cwd()
        target = top / ".claude" / "settings.local.json"
    else:
        target = Path.home() / ".claude" / "settings.json"
    target = target.resolve()  # edit a symlinked settings file in place, keeping the link
    try:
        raw = target.read_text()
        cur = json.loads(raw) if raw.strip() else {}
    except FileNotFoundError:
        raw, cur = None, {}
    except ValueError as e:
        die(f"{target} is not valid JSON ({e}); fix it first")
    if not isinstance(cur, dict):
        die(f"{target} does not hold a JSON object")
    if a.status:
        return hooks_status(cur, target)
    new = merge_hooks(cur, a.uninstall, a.with_rewake)
    text = json.dumps(new, indent=2, ensure_ascii=False) + "\n"
    if a.dry_run:
        # Only our hook entries: the settings file may hold secrets (env, tokens).
        before = {json.dumps(x, sort_keys=True) for x in our_hooks(cur)}
        after = {json.dumps(x, sort_keys=True) for x in our_hooks(new)}
        print(json.dumps({"settings": str(target),
                          "add": [json.loads(x) for x in sorted(after - before)],
                          "remove": [json.loads(x) for x in sorted(before - after)]}, indent=2))
        print(f"dash: dry run; {target} not changed", file=sys.stderr)
        return
    if new == cur:
        print(f"dash: {target} already up to date")
        return
    if raw is not None:
        backup = target.with_name(
            f"{target.name}.bak-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}"
        )
        backup.write_text(raw)
        os.chmod(backup, 0o600)
        print(f"dash: backup {backup}")
    target.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(
        target, text, mode=0o600 if raw is None else (os.stat(target).st_mode & 0o777)
    )
    print(
        f"dash: {'removed hooks from' if a.uninstall else 'installed hooks in'} {target}"
        + (
            " (with experimental asyncRewake idle wake-up)"
            if a.with_rewake and not a.uninstall
            else ""
        )
    )


# ---------------------------------------------------------------- CLI

SESSION_CMDS = {
    "task": cmd_task,
    "add-task": cmd_add_task,
    "ask": cmd_ask,
    "answer": cmd_answer,
    "block": cmd_block,
    "unblock": cmd_unblock,
    "deliver": cmd_deliver,
    "metric": cmd_metric,
    "status": cmd_status,
    "log": cmd_log,
    "show": cmd_show,
    "inbox": cmd_inbox,
    "end": cmd_end,
}


def parser():
    import argparse

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--dir", default=argparse.SUPPRESS, help="hub folder, named .dashboard"
    )
    common.add_argument(
        "--session", default=argparse.SUPPRESS, help="session id (default: see above)"
    )
    p = argparse.ArgumentParser(
        description=__doc__,
        parents=[common],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    def cmd(name, **kw):
        return sub.add_parser(name, parents=[common], **kw)

    x = cmd("init")
    x.add_argument("title")
    x.add_argument("--goal")
    x.add_argument("--context")
    x.add_argument("--task", action="append")
    x.add_argument("--agent", default=os.environ.get("DASHBOARD_AGENT", ""))
    x.add_argument("--label")
    x.add_argument("--force", action="store_true")
    x = cmd("join")
    x.add_argument("--agent", default=os.environ.get("DASHBOARD_AGENT") or "cli")
    x.add_argument("--label")
    x = cmd("task")
    x.add_argument("id")
    x.add_argument("status")
    x.add_argument("--note")
    x = cmd("add-task")
    x.add_argument("title")
    x.add_argument("--detail")
    x.add_argument("--after")
    x = cmd("ask")
    x.add_argument("question")
    x.add_argument("--default", required=True)
    x = cmd("answer")
    x.add_argument("id")
    x.add_argument("answer")
    x = cmd("block")
    x.add_argument("what")
    x.add_argument("--needs")
    x = cmd("unblock")
    x.add_argument("id")
    x.add_argument("--note")
    x = cmd("deliver")
    x.add_argument("path")
    x.add_argument("--label")
    x.add_argument("--note")
    x = cmd("metric")
    x.add_argument("name")
    x.add_argument("value")
    x.add_argument("--total")
    x.add_argument("--unit")
    x.add_argument("--good", choices=("up", "down"))
    x = cmd("status")
    x.add_argument("status")
    x.add_argument("--note")
    x = cmd("log")
    x.add_argument("message")
    x = cmd("show")
    x.add_argument("--json", action="store_true")
    for name in (
        "inbox",
        "end",
        "path",
        "open",
        "sessions",
        "stop",
        "url",
        "render",
        "_mote-refresh",
        "_flush",
    ):
        cmd(name)
    x = cmd("send")
    x.add_argument("sid")
    x.add_argument("text")
    x.add_argument("--kind", choices=("message", "answer"), default="message")
    x.add_argument("--qid")
    x = cmd("serve")
    x.add_argument("--open", action="store_true")
    x.add_argument("--foreground", action="store_true", help=argparse.SUPPRESS)
    x.add_argument("--detached", action="store_true", help=argparse.SUPPRESS)
    x = cmd("install-hooks")
    x.add_argument("--scope", choices=("user", "project"), default="user")
    x.add_argument("--settings", help="settings file to edit (overrides --scope)")
    x.add_argument("--dry-run", action="store_true")
    x.add_argument("--uninstall", action="store_true")
    x.add_argument("--status", action="store_true", help="report what is installed; exit 1 if not")
    x.add_argument(
        "--with-rewake",
        action="store_true",
        help="experimental idle wake-up (asyncRewake)",
    )
    return p


HUB_CMDS = {
    "path": cmd_path,
    "open": cmd_open,
    "sessions": cmd_sessions,
    "send": cmd_send,
    "serve": cmd_serve,
    "stop": cmd_stop,
    "url": cmd_url,
    "render": cmd_render,
    "_mote-refresh": cmd_mote_refresh,
    "_flush": cmd_flush,
    "install-hooks": cmd_install_hooks,
}


def main(argv=None):
    a = parser().parse_args(argv)
    a.dir = getattr(a, "dir", None)
    a.session = getattr(a, "session", None)
    try:
        if a.cmd in ("init", "join"):
            hub, sid = (cmd_init if a.cmd == "init" else cmd_join)(a)
            print_inbox(hub, sid)
        elif a.cmd in SESSION_CMDS:
            hub = find_hub(a.dir)
            sid = session_for(hub, a)
            SESSION_CMDS[a.cmd](a, hub, sid)
            if not (a.cmd == "show" and a.json):
                print_inbox(hub, sid, explicit=a.cmd == "inbox")
            mote_kick(hub)
        else:
            return HUB_CMDS[a.cmd](a) or 0
    except DashError as e:
        print(f"dash: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
