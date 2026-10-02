#!/usr/bin/env python3
"""Generate the specimen snapshots in this folder (schema 2, see docs/plans/agent-dashboard-2.md).

Every fixture is anchored at GENERATED; render.cjs shifts all timestamps so that
`generated` equals the moment of rendering, which keeps relative times realistic.
Run: python3 make_fixtures.py  (writes *.json next to this file)
"""
from __future__ import annotations

import json
import sys
import zlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

TZ = timezone(timedelta(hours=-4))
NOW = datetime(2026, 9, 30, 10, 12, 3, 120000, tzinfo=TZ)
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "scripts"))
from dash import destructive  # noqa: E402  the backend's classifier, so fixtures match it
STYLE = {"theme": "dark", "density": "dense", "accent": "#6366f1", "notes": ""}
EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def iso(dt: datetime) -> str:
    return dt.isoformat(timespec="milliseconds")


def ago(**kw) -> datetime:
    return NOW - timedelta(**kw)


QUICK = {"Read": (0.015, 0.22), "Edit": (0.04, 0.9), "Write": (0.03, 0.45), "Grep": (0.08, 0.7)}


def quick_duration(tool, summary, n):
    """Deterministic, realistic duration for fast tools (instead of a flat 100 ms)."""
    lo, hi = QUICK.get(tool, (0.05, 0.5))
    u = (zlib.crc32(f"{tool}|{summary}|{n}".encode()) % 1000) / 1000
    return round(lo + (hi - lo) * u * u, 3)


class Session:
    """Accumulates hook-style events and derives stats/files from them."""

    def __init__(self, sid, agent, label, cwd, started, root):
        self.sid, self.agent, self.label, self.cwd, self.root = (
            sid,
            agent,
            label,
            cwd,
            root,
        )
        self.started = started
        self.events: list[dict] = []
        self.next_id = 1000 + int(sid[:4], 16) % 4000
        self.files: dict[str, dict] = {}
        self.turns = 0
        self.subagents = 0

    def ev(self, ts, kind, **kw):
        e = {
            "id": self.next_id,
            "ts": iso(ts),
            "kind": kind,
            "tool": None,
            "summary": None,
            "detail": None,
            "ok": None,
            "duration_ms": None,
            "subagent": None,
        }
        e.update(kw)
        self.next_id += 1
        self.events.append(e)
        if kind == "tool" and e["tool"] in EDIT_TOOLS | {"Read"} and e["summary"]:
            f = self.files.setdefault(
                e["summary"],
                {"path": e["summary"], "edits": 0, "reads": 0, "last": None},
            )
            f["edits" if e["tool"] in EDIT_TOOLS else "reads"] += 1
            f["last"] = e["ts"]
        if kind == "tool" and e["tool"] in ("Task", "Agent"):
            self.subagents += 1
        if kind == "prompt":
            self.turns += 1
        return ts

    def tools(self, t, steps, sub=None):
        """steps: (tool, summary, seconds_after_prev, duration_s, ok[, detail])."""
        for step in steps:
            tool, summary, gap, dur, ok = step[:5]
            detail = step[5] if len(step) > 5 else None
            if dur == 0.1:
                dur = quick_duration(tool, summary, len(self.events))
            t = t + timedelta(seconds=gap)
            self.ev(
                t,
                "tool",
                tool=tool,
                summary=summary,
                ok=ok,
                duration_ms=None if dur is None else int(dur * 1000),
                detail=detail,
                subagent=sub,
            )
            t = t + timedelta(seconds=dur or 0)
        return t

    def span(self, start, end, steps, sub=None):
        """Like tools(), but scale the gaps so the steps finish at `end`."""
        busy = sum(step[3] or 0 for step in steps)
        gaps = sum(step[2] for step in steps) or 1
        scale = max((end - start).total_seconds() - busy, 0) / gaps
        scaled = [(s[0], s[1], s[2] * scale, *s[3:]) for s in steps]
        return self.tools(start, scaled, sub=sub)

    def snapshot(self, **kw):
        self.events.sort(key=lambda e: e["ts"])
        base = self.events[0]["id"] if self.events else 0
        for i, e in enumerate(self.events):
            e["id"] = base + i
        tool_events = [e for e in self.events if e["kind"] == "tool"]
        stats = {
            "tool_calls": len(tool_events),
            "edits": sum(e["tool"] in EDIT_TOOLS for e in tool_events),
            "commands": sum(e["tool"] == "Bash" for e in tool_events),
            "failures": sum(e["ok"] is False for e in tool_events),
            "turns": self.turns,
            "subagents": self.subagents,
            "files_touched": len(self.files),
        }
        files = sorted(self.files.values(), key=lambda f: f["last"], reverse=True)[:40]
        last_seen = max([e["ts"] for e in self.events] + [iso(self.started)])
        prompts = [e for e in self.events if e["kind"] == "prompt"]
        snap = {
            "id": self.sid,
            "short": self.sid[:4],
            "agent": self.agent,
            "label": self.label,
            "cwd": self.cwd,
            "started": iso(self.started),
            "last_seen": last_seen,
            "ended": None,
            "activity": "working",
            "activity_since": last_seen,
            "current": None,
            "last_prompt": {
                "ts": prompts[-1]["ts"],
                "text": prompts[-1]["detail"][:280],
            }
            if prompts
            else None,
            "attention": [],
            "plan": None,
            "stats": stats,
            "tests": [],
            "files": files,
            "events": self.events[-300:],
            "inbox": [],
            "paused": False,
            # null: no --watch-inbox record (rewake not installed, or a turn is running)
            "wakeable": None,
        }
        snap.update(kw)
        if "wakeable" not in kw and (snap["agent"] != "claude" or snap["activity"] == "ended"):
            snap["wakeable"] = False
        return snap


def prompt(s: Session, t, text):
    return s.ev(t, "prompt", summary=text[:80], detail=text)


def turn_end(s: Session, t, detail=None):
    return s.ev(t, "turn_end", detail=detail)


def plan(
    title, goal, tasks, status="on_track", note=None, updated=None, context=None, **kw
):
    out = {
        "title": title,
        "goal": goal,
        "context": context,
        "status": status,
        "status_note": note,
        "status_updated": iso(updated or NOW),
        "tasks": [],
        "questions": [],
        "blockers": [],
        "metrics": [],
        "deliverables": [],
        "log": [],
    }
    for i, t in enumerate(tasks, 1):
        title_, status_, started, finished, *rest = t
        out["tasks"].append(
            {
                "id": i,
                "title": title_,
                "detail": rest[1] if len(rest) > 1 else None,
                "status": status_,
                "note": rest[0] if rest else None,
                "started": iso(started) if started else None,
                "finished": iso(finished) if finished else None,
            }
        )
    out.update(kw)
    return out


def metric(name, value, history, total=None, unit=None, good="up"):
    return {
        "name": name,
        "value": value,
        "total": total,
        "unit": unit,
        "good": good,
        "updated": iso(history[-1][0]) if history else None,
        "history": [
            [iso(ts) if isinstance(ts, datetime) else ts, v] for ts, v in history
        ],
    }


def git(branch, head, subject, dirty):
    return {"branch": branch, "head": head, "subject": subject, "dirty": dirty}


def flag_destructive(snap):
    """Add `destructive` as the backend does: Bash in-flight calls, copied to permission items."""
    cur = snap.get("current")
    flag = destructive(cur["summary"]) if cur and cur["tool"] == "Bash" else None
    if cur:
        cur["destructive"] = flag
    for a in snap.get("attention") or []:
        a["destructive"] = flag if a["kind"] == "permission" else None
    return snap


def hub(
    name,
    root,
    sessions,
    rev,
    git_=None,
    conflicts=None,
    mote=None,
    style=None,
    server=False,
):
    return {
        "schema": 2,
        "generated": iso(NOW),
        "revision": rev,
        "project": {"name": name, "root": root, "git": git_},
        "server": {"running": server, "started": iso(ago(hours=1)) if server else None},
        "style": style or STYLE,
        "sessions": [flag_destructive(s) for s in sessions],
        "conflicts": conflicts or [],
        "mote": mote,
    }


# --------------------------------------------------------------------------- solo-rcheck
def solo_rcheck():
    root = "/Users/bbuchsbaum/code/neuroim2"
    s = Session(
        "8f3c2a1e-51d4-4c1b-9d0e-7a61b2c4f9aa",
        "claude",
        "Clear R CMD check NOTEs",
        root,
        ago(minutes=52),
        root,
    )
    s.ev(s.started, "session", summary="startup", detail="SessionStart")
    t = prompt(
        s,
        ago(minutes=51, seconds=40),
        "R CMD check --as-cran is giving 4 NOTEs and 7 test failures on the fix/check-notes branch. "
        "Get it clean for the 0.9.1 CRAN resubmission. Don't touch the public API of read_vol().",
    )
    t = s.tools(
        t,
        [
            ("Bash", "git status --short", 4, 0.3, True),
            ("Read", "DESCRIPTION", 3, 0.1, True),
            ("Read", "NAMESPACE", 2, 0.1, True),
            ("Bash", "Rscript -e 'devtools::document()'", 5, 11, True),
            (
                "Bash",
                "R CMD build . && R CMD check --as-cran --no-manual neuroim2_0.9.1.tar.gz",
                3,
                412,
                False,
                "Status: 7 ERRORs in tests, 4 NOTEs",
            ),
            ("Read", "neuroim2.Rcheck/00check.log", 2, 0.2, True),
            ("Grep", "\\\\dontrun", 3, 0.4, True),
            ("Read", "R/read_vol.R", 3, 0.1, True),
            ("Read", "R/neurovol.R", 2, 0.1, True),
            ("Read", "R/plot_methods.R", 2, 0.1, True),
            ("Task", "Explore: where are globals used in ggplot calls?", 6, 48, True),
        ],
    )
    t = s.tools(
        t,
        [
            ("Grep", "aes\\(", 1, 0.3, True),
            ("Read", "R/plot_methods.R", 1, 0.1, True),
            ("Read", "R/plot_slices.R", 1, 0.1, True),
        ],
        sub="Explore",
    )
    t = turn_end(
        s, t + timedelta(seconds=20), "Reproduced: 4 NOTEs, 7 failures. Plan recorded."
    )
    t = prompt(
        s,
        t + timedelta(minutes=3),
        "Go ahead with the plan. Run the tests after each fix.",
    )
    t = s.span(
        t,
        ago(minutes=11, seconds=20),
        [
            (
                "Bash",
                "python3 dash.py task 1 done --note '4 NOTEs, 7 failing tests'",
                2,
                0.4,
                True,
            ),
            ("Edit", "R/read_vol.R", 8, 0.1, True),
            ("Edit", "R/read_vol.R", 12, 0.1, True),
            ("Bash", "Rscript -e 'devtools::document()'", 4, 10, True),
            ("Edit", "man/read_vol.Rd", 5, 0.1, True),
            ("Edit", "R/neurovol.R", 20, 0.1, True),
            ("Edit", "R/neurovol.R", 9, 0.1, True),
            ("Edit", "R/neurovec.R", 14, 0.1, True),
            (
                "Bash",
                "Rscript -e 'devtools::test()'",
                6,
                74,
                False,
                "[ FAIL 4 | WARN 1 | SKIP 3 | PASS 410 ]",
            ),
            ("Edit", "R/plot_methods.R", 10, 0.1, True),
            ("Write", "R/globals.R", 12, 0.1, True),
            (
                "Bash",
                "Rscript -e 'devtools::test()'",
                5,
                71,
                False,
                "[ FAIL 3 | WARN 0 | SKIP 3 | PASS 411 ]",
            ),
            ("Read", "tests/testthat/test-neurovol.R", 4, 0.1, True),
            ("Edit", "tests/testthat/test-neurovol.R", 15, 0.1, True),
            ("Edit", "R/neurovol.R", 22, 0.1, True),
            (
                "Bash",
                "Rscript -e 'devtools::test(filter = \"neurovol\")'",
                5,
                19,
                False,
                "[ FAIL 2 | PASS 58 ]",
            ),
            ("Read", "R/axis.R", 6, 0.1, True),
            ("Read", "R/space.R", 3, 0.1, True),
            ("Read", "R/space.R", 40, 0.1, True),
            ("Edit", "R/space.R", 30, 0.1, True),
            (
                "Bash",
                "Rscript -e 'devtools::test()'",
                5,
                70,
                False,
                "[ FAIL 2 | WARN 0 | SKIP 3 | PASS 412 ]",
            ),
            (
                "Bash",
                "python3 dash.py metric 'Tests passing' 412 --total 414",
                4,
                0.3,
                True,
            ),
        ],
    )
    s.ev(
        ago(minutes=10, seconds=40),
        "message",
        summary="From dashboard",
        detail="Skip the Windows-only path test for now; mark it skip_on_os('windows').",
    )
    t = s.span(
        ago(minutes=10, seconds=30),
        ago(minutes=3, seconds=30),
        [
            ("Edit", "tests/testthat/test-io.R", 18, 0.1, True),
            ("Read", "R/read_vol.R", 12, 0.1, True),
            (
                "Bash",
                "Rscript -e 'devtools::test()'",
                5,
                70,
                False,
                "[ FAIL 2 | WARN 0 | SKIP 3 | PASS 412 ]",
            ),
            ("Edit", "NEWS.md", 20, 0.1, True),
        ],
    )
    cur_start = ago(minutes=3, seconds=12)
    s.ev(
        cur_start - timedelta(seconds=4),
        "note",
        summary="Re-running full check to confirm NOTE count",
    )
    # R CMD check entry per the backend contract: failed = ERRORs + WARNINGs + NOTEs, passed null.
    tests = [
        {
            "ts": iso(ago(minutes=44)),
            "runner": "R CMD check",
            "passed": None,
            "failed": 5,
            "skipped": None,
            "command": "R CMD check --as-cran --no-manual neuroim2_0.9.1.tar.gz",
        }
    ]
    for mins, passed, failed in [
        (41, 407, 7),
        (31, 410, 4),
        (24, 411, 3),
        (15, 412, 2),
        (6, 412, 2),
    ]:
        tests.append(
            {
                "ts": iso(ago(minutes=mins)),
                "runner": "testthat",
                "passed": passed,
                "failed": failed,
                "skipped": 3,
                "command": "devtools::test()",
            }
        )
    p = plan(
        "Clear R CMD check NOTEs for CRAN",
        "R CMD check --as-cran: 0 ERRORs, 0 WARNINGs, 0 NOTEs; all tests pass",
        [
            (
                "Reproduce NOTEs and failures locally",
                "done",
                ago(minutes=51),
                ago(minutes=43),
                "4 NOTEs, 7 failing tests",
            ),
            (
                "Document missing arguments in read_vol()",
                "done",
                ago(minutes=42),
                ago(minutes=38),
                "Added @param mask, @param mode",
            ),
            (
                "Replace \\dontrun{} with \\donttest{} in examples",
                "done",
                ago(minutes=38),
                ago(minutes=34),
            ),
            (
                "Silence 'no visible binding' NOTE in plot methods",
                "done",
                ago(minutes=34),
                ago(minutes=30),
                "utils::globalVariables in R/globals.R",
            ),
            (
                "Fix failing testthat cases in test-neurovol.R",
                "doing",
                ago(minutes=30),
                None,
                "2 left: axis permutation for LPI space",
            ),
            ("Re-run R CMD check --as-cran", "todo", None, None),
            ("Update NEWS.md and cran-comments.md", "todo", None, None),
        ],
        status="on_track",
        note="2 failures remain, both in axis permutation; cause located in R/space.R",
        updated=ago(minutes=9),
        context="Resubmission after CRAN reviewer comments on 0.9.0",
        metrics=[
            metric(
                "Check NOTEs",
                1,
                [
                    (ago(minutes=43), 4),
                    (ago(minutes=34), 3),
                    (ago(minutes=30), 2),
                    (ago(minutes=9), 1),
                ],
                good="down",
            ),
            metric(
                "Tests passing (excl. skipped)",
                412,
                [
                    (ago(minutes=47), 407),
                    (ago(minutes=31), 410),
                    (ago(minutes=24), 411),
                    (ago(minutes=15), 412),
                    (ago(minutes=6), 412),
                ],
                total=414,
            ),
            metric(
                "Coverage",
                78.4,
                [
                    (ago(minutes=45), 76.9),
                    (ago(minutes=20), 78.1),
                    (ago(minutes=10), 78.4),
                ],
                unit="%",
            ),
        ],
        log=[
            {"ts": iso(ago(minutes=43)), "text": "Baseline: 4 NOTEs, 7 test failures"},
            {"ts": iso(ago(minutes=30)), "text": "NOTEs down to 2 after globals.R"},
            {
                "ts": iso(ago(minutes=9)),
                "text": "Cause of the last 2 failures: space permutation ignores LPI",
            },
        ],
    )
    snap = s.snapshot(
        activity="working",
        activity_since=iso(ago(minutes=48)),
        current={
            "tool": "Bash",
            "summary": "R CMD check --as-cran --no-manual neuroim2_0.9.1.tar.gz",
            "started": iso(cur_start),
        },
        plan=p,
        tests=tests,
        inbox=[
            {
                "id": "m1",
                "ts": iso(ago(minutes=11)),
                "kind": "message",
                "text": "Skip the Windows-only path test for now; mark it skip_on_os('windows').",
                "qid": None,
                "status": "delivered",
                "delivered": iso(ago(minutes=10, seconds=40)),
                "via": "PostToolUse",
            }
        ],
    )
    return hub(
        "neuroim2",
        root,
        [snap],
        1841,
        git("fix/check-notes", "a1b2c3d", "Document read_vol() arguments", 7),
    )


# --------------------------------------------------------------------------- trio-mote
def trio_mote():
    root = "/Users/bbuchsbaum/code/rMVPA"
    a = Session(
        "a91e77c0-3b2f-4d8e-8f10-2c9b44e1d0f3",
        "claude",
        "Searchlight RSA refactor",
        root,
        ago(hours=1, minutes=24),
        root,
    )
    a.ev(a.started, "session", summary="startup")
    t = prompt(
        a,
        ago(hours=1, minutes=23),
        "Refactor the RSA searchlight so model RDMs are precomputed once per sphere size. "
        "Keep results bit-identical to the current implementation on the MVPA test fixtures.",
    )
    t = a.tools(
        t,
        [
            ("Read", "R/rsa_model.R", 3, 0.1, True),
            ("Read", "R/searchlight.R", 2, 0.1, True),
            ("Read", "R/rsa_iterate.R", 2, 0.1, True),
            ("Read", "tests/testthat/test_rsa.R", 2, 0.1, True),
            ("Task", "Plan: precompute strategy for model RDMs", 5, 95, True),
        ],
    )
    t = turn_end(a, t + timedelta(seconds=30))
    t = prompt(a, ago(minutes=58), "Looks right. Implement it, bead bd-4f1.")
    t = a.tools(
        t,
        [
            ("Bash", "mote claim bd-4f1", 3, 0.5, True),
            ("Bash", "mote reserve R/rsa_model.R R/searchlight.R", 2, 0.4, True),
        ],
    )
    for i in range(9):
        t = a.tools(
            t,
            [
                (
                    "Edit",
                    ["R/rsa_model.R", "R/searchlight.R", "R/rsa_model.R"][i % 3],
                    150,
                    0.1,
                    True,
                )
            ],
        )
    t = a.tools(
        t,
        [
            (
                "Bash",
                "Rscript -e 'devtools::test(filter=\"rsa\")'",
                5,
                88,
                False,
                "[ FAIL 1 | PASS 143 ]",
            ),
            ("Read", "tests/testthat/test_rsa.R", 3, 0.1, True),
            ("Edit", "R/rsa_model.R", 30, 0.1, True),
            (
                "Bash",
                "Rscript -e 'devtools::test(filter=\"rsa\")'",
                4,
                86,
                True,
                "[ FAIL 0 | PASS 144 ]",
            ),
            (
                "Bash",
                "Rscript bench/rsa_searchlight_bench.R",
                8,
                212,
                True,
                "median 41.2 s -> 12.7 s",
            ),
        ],
    )
    for f in [
        "R/rsa_model.R",
        "R/rsa_model.R",
        "R/rsa_iterate.R",
        "R/rsa_iterate.R",
        "R/rsa_iterate.R",
    ]:
        t = a.tools(t, [("Read" if "iterate" in f else "Edit", f, 230, 0.1, True)])
    a.ev(
        ago(minutes=2, seconds=30),
        "message",
        summary="From dashboard",
        detail="Post the benchmark numbers to the board when done.",
    )
    snap_a = a.snapshot(
        activity="working",
        activity_since=iso(ago(minutes=58)),
        current={
            "tool": "Edit",
            "summary": "R/rsa_model.R",
            "started": iso(ago(seconds=4)),
        },
        plan=plan(
            "Precompute model RDMs in RSA searchlight",
            "Same results on fixtures; searchlight ≥ 2× faster",
            [
                ("Design precompute cache", "done", ago(minutes=80), ago(minutes=60)),
                (
                    "Implement cache in rsa_model()",
                    "done",
                    ago(minutes=58),
                    ago(minutes=30),
                ),
                (
                    "Bit-identical check on fixtures",
                    "done",
                    ago(minutes=30),
                    ago(minutes=22),
                    "144/144 pass",
                ),
                (
                    "Benchmark",
                    "done",
                    ago(minutes=22),
                    ago(minutes=18),
                    "41.2 s → 12.7 s",
                ),
                ("Extend cache to rsa_iterate()", "doing", ago(minutes=17), None),
            ],
            metrics=[
                metric(
                    "Searchlight median",
                    12.7,
                    [(ago(minutes=75), 41.2), (ago(minutes=18), 12.7)],
                    unit="s",
                    good="down",
                )
            ],
        ),
        tests=[
            {
                "ts": iso(ago(minutes=24)),
                "runner": "testthat",
                "passed": 143,
                "failed": 1,
                "skipped": 0,
                "command": 'devtools::test(filter="rsa")',
            },
            {
                "ts": iso(ago(minutes=21)),
                "runner": "testthat",
                "passed": 144,
                "failed": 0,
                "skipped": 0,
                "command": 'devtools::test(filter="rsa")',
            },
        ],
        inbox=[
            {
                "id": "m7",
                "ts": iso(ago(minutes=3)),
                "kind": "message",
                "text": "Post the benchmark numbers to the board when done.",
                "qid": None,
                "status": "delivered",
                "delivered": iso(ago(minutes=2, seconds=30)),
                "via": "PostToolUse",
            }
        ],
    )

    b = Session(
        "3d07b5e2-9a4c-4e11-b7a0-6f2d1c88e412",
        "claude",
        "Fix vignette build",
        root,
        ago(hours=2, minutes=5),
        root,
    )
    b.ev(b.started, "session", summary="startup")
    t = prompt(
        b,
        ago(hours=2, minutes=4),
        "pkgdown build fails on the searchlight vignette. Find out why.",
    )
    t = b.tools(
        t,
        [
            (
                "Bash",
                "Rscript -e 'pkgdown::build_article(\"searchlight\")'",
                5,
                64,
                False,
                "Error: object 'rsa_des' not found",
            ),
            ("Read", "vignettes/searchlight.Rmd", 3, 0.1, True),
            ("Edit", "vignettes/searchlight.Rmd", 40, 0.1, True),
            (
                "Bash",
                "Rscript -e 'pkgdown::build_article(\"searchlight\")'",
                5,
                71,
                True,
            ),
        ],
    )
    t = turn_end(b, t + timedelta(seconds=15), "Vignette builds; waiting for review.")
    t = prompt(b, ago(minutes=36), "Also the RSA vignette, same problem?")
    t = b.tools(
        t,
        [
            ("Read", "vignettes/rsa.Rmd", 3, 0.1, True),
            ("Edit", "vignettes/rsa.Rmd", 30, 0.1, True),
            ("Read", "R/rsa_model.R", 10, 0.1, True),
            ("Edit", "R/rsa_model.R", 45, 0.1, True),
            ("Bash", "Rscript -e 'pkgdown::build_article(\"rsa\")'", 5, 58, True),
        ],
    )
    t = turn_end(
        b,
        t + timedelta(seconds=12),
        "Both vignettes build. Fixed a roxygen example in R/rsa_model.R.",
    )
    snap_b = b.snapshot(
        wakeable=True,  # an idle session with a live --watch-inbox watcher
        activity="idle",
        activity_since=iso(t),
        current=None,
        tests=[],
        plan=None,
        inbox=[
            {
                "id": "m9",
                "ts": iso(ago(minutes=1)),
                "kind": "message",
                "text": "Hold off on R/rsa_model.R — the refactor session owns it. Revert your edit there.",
                "qid": None,
                "status": "queued",
                "delivered": None,
                "via": None,
            }
        ],
    )

    c = Session(
        "c2d4e6f8-1a3b-4c5d-8e9f-0a1b2c3d4e5f",
        "codex",
        "Port contrast_rsa to C++",
        root,
        ago(minutes=41),
        root,
    )
    # Codex has no hooks: only narrative events from dash.py calls, unknown stats stay null.
    for mins, text in [
        (40, "Plan: port contrast_rsa() inner loop to RcppArmadillo (bd-512)"),
        (31, "Task 1 doing: port inner loop"),
        (20, "Task 1 done: inner loop ported; build needed each_col fix"),
        (19, "Delivered dashboard message m4 via cli"),
        (5, "Task 2 done: equivalence tests 37/37 to 1e-12"),
        (4, "Task 3 doing: benchmark vs R implementation"),
    ]:
        c.ev(ago(minutes=mins), "note", summary=text)
    snap_c = c.snapshot(
        activity="working",
        activity_since=iso(ago(minutes=40)),
        current=None,
        last_prompt=None,
        stats={k: None for k in ("tool_calls", "edits", "commands", "failures", "turns", "subagents", "files_touched")},
        files=[],
        plan=plan(
            "Port contrast_rsa to C++",
            "Same output to 1e-12; ≥5× faster",
            [
                ("Port inner loop", "done", ago(minutes=31), ago(minutes=20)),
                ("Equivalence tests", "done", ago(minutes=20), ago(minutes=5), "37/37"),
                ("Benchmark", "doing", ago(minutes=4), None),
            ],
            metrics=[metric("Equivalence tests", 37, [(ago(minutes=5), 37)], total=37)],
        ),
        tests=[],
        inbox=[
            {
                "id": "m4",
                "ts": iso(ago(minutes=26)),
                "kind": "message",
                "text": "Use arma::mat views, no copies.",
                "qid": None,
                "status": "delivered",
                "delivered": iso(ago(minutes=19)),
                "via": "cli",
            }
        ],
    )
    mote = {
        "store": f"{root}/.mote",
        "fetched": iso(ago(seconds=20)),
        "error": None,
        "counts": {"open": 31, "doing": 4, "blocked": 2, "review": 1},
        "doing": [
            {
                "id": "bd-4f1",
                "title": "Precompute model RDMs in RSA searchlight",
                "assignee": "claude-a91e",
                "tags": ["perf", "rsa"],
                "priority": 1,
            },
            {
                "id": "bd-512",
                "title": "Port contrast_rsa inner loop to RcppArmadillo",
                "assignee": "codex-c2d4",
                "tags": ["perf", "cpp"],
                "priority": 1,
            },
            {
                "id": "bd-4c9",
                "title": "Fix vignette builds after rsa_design rename",
                "assignee": "claude-3d07",
                "tags": ["docs"],
                "priority": 2,
            },
            {
                "id": "bd-3a0",
                "title": "Nested CV for ridge-regression searchlight",
                "assignee": "chief",
                "tags": ["model"],
                "priority": 2,
            },
        ],
        "ready": [
            {
                "id": "bd-51a",
                "title": "Expose sphere radius sweep in run_searchlight()",
                "assignee": None,
                "tags": ["api"],
                "priority": 2,
            },
            {
                "id": "bd-50e",
                "title": "Add feature-selection vignette",
                "assignee": None,
                "tags": ["docs"],
                "priority": 3,
            },
            {
                "id": "bd-4ff",
                "title": "Deprecate mvpa_dataset(mask=) positional arg",
                "assignee": None,
                "tags": ["api"],
                "priority": 3,
            },
        ],
        "blocked": [
            {
                "id": "bd-4e2",
                "title": "CRAN release 0.2.0",
                "assignee": "chief",
                "tags": ["release"],
                "priority": 1,
            },
            {
                "id": "bd-49b",
                "title": "GPU backend for crossnobis",
                "assignee": None,
                "tags": ["perf"],
                "priority": 4,
            },
        ],
        "reservations": [
            {
                "actor": "claude-a91e",
                "paths": ["R/rsa_model.R", "R/searchlight.R"],
                "issue": "bd-4f1",
                "created": iso(NOW + timedelta(minutes=34) - timedelta(hours=1)),
                "expires": iso(NOW + timedelta(minutes=34)),
            },
            {
                "actor": "codex-c2d4",
                "paths": ["src/contrast_rsa.cpp"],
                "issue": "bd-512",
                "created": None,
                "expires": iso(NOW + timedelta(minutes=12)),
            },
        ],
        "actors": [
            {
                "actor": "claude-a91e",
                "status": "active",
                "expires": iso(NOW + timedelta(minutes=9)),
            },
            {
                "actor": "codex-c2d4",
                "status": "active",
                "expires": iso(NOW + timedelta(minutes=7)),
            },
            {
                "actor": "claude-3d07",
                "status": "idle",
                "expires": iso(NOW + timedelta(minutes=2)),
            },
            {"actor": "chief", "status": "away", "expires": None},
        ],
        "posts": [
            {
                "id": "post-88",
                "topic": "perf",
                "from": "claude-a91e",
                "ts": iso(ago(minutes=17)),
                "excerpt": "Searchlight RSA benchmark: median 41.2 s → 12.7 s on the 3 mm fixture, results bit-identical.",
                "replies": 2,
            },
            {
                "id": "post-87",
                "topic": "coordination",
                "from": "codex-c2d4",
                "ts": iso(ago(minutes=22)),
                "excerpt": "Touching R/rsa_model.R only for the .Call wrapper — will rebase on bd-4f1 when it lands.",
                "replies": 1,
            },
            {
                "id": "post-85",
                "topic": "release",
                "from": "chief",
                "ts": iso(ago(hours=3)),
                "excerpt": "0.2.0 is blocked until both perf beads land and vignettes build on CI.",
                "replies": 4,
            },
        ],
    }
    # Conflict shape per the backend: every source that puts two agents on one path.
    def last_edit(snap, path):
        return next((f["last"] for f in snap["files"] if f["path"] == path and f["edits"]), None)

    a_edit, b_edit = last_edit(snap_a, "R/rsa_model.R"), last_edit(snap_b, "R/rsa_model.R")
    conflicts = [
        {
            "path": "R/rsa_model.R",
            # Posts are context, not claims: only the two editors are parties (dash.build_conflicts).
            "sessions": ["a91e", "3d07"],
            "sources": ["edit", "reservation", "post"],
            "live": True,
            "last_edit": max(a_edit, b_edit),
            "mote_reserved_by": "claude-a91e",
            "detail": [
                {"session": "a91e", "kind": "edit", "ts": a_edit, "ref": None, "expires": None},
                {"session": "3d07", "kind": "edit", "ts": b_edit, "ref": None, "expires": None},
                {"session": "a91e", "kind": "reservation", "ts": iso(NOW - timedelta(minutes=26)), "ref": "bd-4f1",
                 "expires": iso(NOW + timedelta(minutes=34))},
                {"session": "c2d4", "kind": "post", "ts": iso(ago(minutes=22)), "ref": "post-87", "expires": None},
            ],
        }
    ]
    return hub(
        "rMVPA",
        root,
        [snap_a, snap_b, snap_c],
        5217,
        git("perf/rsa-cache", "9e41d07", "Cache model RDMs per sphere size", 12),
        conflicts,
        mote,
        server=True,
    )


# --------------------------------------------------------------------------- needs-you
def needs_you():
    root = "/Users/bbuchsbaum/code/fmrireg"
    s = Session(
        "5b8e0c3a-7d21-4f6e-a9b3-1e2f3a4b5c6d",
        "claude",
        "HRF basis sweep on ds004212",
        root,
        ago(minutes=38),
        root,
    )
    s.ev(s.started, "session", summary="startup")
    t = prompt(
        s,
        ago(minutes=37),
        "Run the HRF basis comparison (SPM canonical, FIR-12, B-spline 5) on ds004212 and write the report.",
    )
    t = s.tools(
        t,
        [
            ("Read", "R/hrf.R", 3, 0.1, True),
            ("Read", "inst/scripts/hrf_sweep.R", 3, 0.1, True),
            (
                "Bash",
                "ls /data/ds004212/derivatives/fmriprep",
                5,
                0.3,
                False,
                "ls: /data/ds004212/derivatives/fmriprep: Permission denied",
            ),
            ("Edit", "inst/scripts/hrf_sweep.R", 30, 0.1, True),
            (
                "Bash",
                "Rscript inst/scripts/hrf_sweep.R --subjects 01-04 --dry-run",
                5,
                14,
                True,
            ),
            ("Write", "reports/hrf_sweep_plan.md", 12, 0.1, True),
        ],
    )
    perm_ts = ago(minutes=2, seconds=41)
    s.ev(
        perm_ts,
        "notify",
        summary="permission",
        detail="Claude needs your permission to use Bash",
    )
    p = plan(
        "HRF basis comparison on ds004212",
        "Report comparing 3 HRF bases on 24 subjects, with CV log-likelihood",
        [
            ("Dry run on 4 subjects", "done", ago(minutes=30), ago(minutes=20)),
            (
                "Stage fMRIPrep derivatives",
                "blocked",
                ago(minutes=20),
                None,
                "Read access denied",
            ),
            ("Fit 3 bases × 24 subjects", "todo", None, None),
            ("Write comparison report", "todo", None, None),
        ],
        status="blocked",
        note="Cannot read /data/ds004212 derivatives",
        updated=ago(minutes=19),
    )
    p["questions"] = [
        {
            "id": "Q1",
            "text": "Use 6 mm or 8 mm smoothing for the group maps?",
            "default": "6 mm, matching the preregistration",
            "asked": iso(ago(minutes=16)),
            "answer": None,
            "answered": None,
            "answered_via": None,
        },
        {
            "id": "Q2",
            "text": "Include sub-19 (framewise displacement > 0.5 mm in 22% of volumes)?",
            "default": None,
            "asked": iso(ago(minutes=9)),
            "answer": None,
            "answered": None,
            "answered_via": None,
        },
        {
            "id": "Q0",
            "text": "Report format?",
            "default": "HTML",
            "asked": iso(ago(minutes=33)),
            "answer": "Quarto HTML",
            "answered": iso(ago(minutes=31)),
            "answered_via": "dashboard",
        },
    ]
    p["blockers"] = [
        {
            "id": "B1",
            "text": "No read access to /data/ds004212/derivatives/fmriprep",
            "needs": "Run: sudo chmod -R g+r /data/ds004212/derivatives (or add me to group 'mri')",
            "opened": iso(ago(minutes=19)),
            "closed": None,
        }
    ]
    snap = s.snapshot(
        activity="waiting_permission",
        activity_since=iso(perm_ts),
        current={
            "tool": "Bash",
            "summary": "rsync -a --delete /data/ds004212/derivatives/fmriprep/ scratch/fmriprep/",
            "started": iso(perm_ts - timedelta(seconds=1)),
        },
        attention=[
            {
                "kind": "permission",
                "text": "Claude needs your permission to use Bash",
                "ts": iso(perm_ts),
            }
        ],
        plan=p,
    )
    s2 = Session(
        "e4f5a6b7-c8d9-4e0f-a1b2-c3d4e5f60718",
        "claude",
        "Refit design matrices",
        root,
        ago(minutes=25),
        root,
    )
    s2.ev(s2.started, "session", summary="startup")
    t = prompt(
        s2,
        ago(minutes=24),
        "Refactor design_matrix() so nuisance regressors can be passed as a tibble.",
    )
    t = s2.tools(
        t,
        [
            ("Read", "R/design_matrix.R", 3, 0.1, True),
            ("Edit", "R/design_matrix.R", 60, 0.1, True),
            (
                "Bash",
                "Rscript -e 'devtools::test(filter=\"design\")'",
                5,
                31,
                True,
                "[ FAIL 0 | PASS 88 ]",
            ),
        ],
    )
    t = turn_end(
        s2, t + timedelta(seconds=10), "Done — want me to update the vignette too?"
    )
    idle_ts = t + timedelta(seconds=60)
    s2.ev(
        idle_ts,
        "notify",
        summary="idle_prompt",
        detail="Claude is waiting for your input",
    )
    snap2 = s2.snapshot(
        activity="waiting_user",
        activity_since=iso(idle_ts),
        attention=[
            {
                "kind": "idle_prompt",
                "text": "Claude is waiting for your input",
                "ts": iso(idle_ts),
            }
        ],
        tests=[
            {
                "ts": iso(t - timedelta(seconds=10)),
                "runner": "testthat",
                "passed": 88,
                "failed": 0,
                "skipped": 0,
                "command": 'devtools::test(filter="design")',
            }
        ],
    )
    return hub(
        "fmrireg",
        root,
        [snap, snap2],
        733,
        git("main", "7c1d2e9", "Add B-spline HRF basis", 3),
        server=True,
    )


# --------------------------------------------------------------------------- slurm-long
def slurm_long():
    root = "/Users/bbuchsbaum/code/hcp-surface-decoding"
    s = Session(
        "71aa0e3c-2b4d-4f6a-8c9e-0d1f2a3b4c5d",
        "claude",
        "fMRIPrep campaign · 64 subjects",
        root,
        ago(hours=2, minutes=11),
        root,
    )
    s.ev(s.started, "session", summary="startup")
    t = prompt(
        s,
        ago(hours=2, minutes=10),
        "Run fMRIPrep 24.1 on all 64 subjects of the HCP-D subset on the cluster, 8 at a time. "
        "Retry failures once, then summarise QC. I'm going to be away until lunch.",
    )
    t = s.tools(
        t,
        [
            ("Read", "config/fmriprep.toml", 3, 0.1, True),
            (
                "mcp__remoteslurm__campaign_preflight",
                "fmriprep-hcpd · 64 subjects",
                5,
                38,
                True,
            ),
            (
                "mcp__remoteslurm__campaign_start",
                "fmriprep-hcpd · array 1-64%8",
                6,
                12,
                True,
                "campaign c-0930a started",
            ),
            (
                "Bash",
                "python3 dash.py metric 'Subjects done' 0 --total 64",
                3,
                0.3,
                True,
            ),
        ],
    )
    t = s.tools(
        ago(hours=1, minutes=35),
        [
            (
                "mcp__remoteslurm__campaign_events",
                "c-0930a",
                0,
                3,
                True,
                "8 running, 56 pending",
            ),
            (
                "mcp__remoteslurm__campaign_failures",
                "c-0930a",
                60 * 25,
                4,
                True,
                "sub-1043: OOM (48G)",
            ),
            ("mcp__remoteslurm__campaign_retry", "sub-1043 --mem 64G", 5, 6, True),
        ],
    )
    t = s.tools(
        ago(minutes=52),
        [
            (
                "mcp__remoteslurm__campaign_events",
                "c-0930a",
                0,
                3,
                True,
                "38 done, 8 running, 18 pending",
            ),
            (
                "Bash",
                "python3 dash.py metric 'Subjects done' 38 --total 64",
                50,
                0.3,
                True,
            ),
        ],
    )
    cur = ago(minutes=47, seconds=18)
    snap = s.snapshot(
        activity="working",
        activity_since=iso(ago(hours=2, minutes=10)),
        current={
            "tool": "mcp__remoteslurm__campaign_drive",
            "summary": "campaign c-0930a · wait until all 64 terminal (timeout 3 h)",
            "started": iso(cur),
        },
        plan=plan(
            "fMRIPrep 24.1 on HCP-D subset",
            "64/64 subjects preprocessed or failed twice with a logged reason; QC summary written",
            [
                (
                    "Preflight container, bind paths and FreeSurfer licence",
                    "done",
                    ago(hours=2, minutes=9),
                    ago(hours=2, minutes=5),
                ),
                (
                    "Submit array 1-64%8",
                    "done",
                    ago(hours=2, minutes=5),
                    ago(hours=2, minutes=4),
                ),
                (
                    "Drive campaign to completion",
                    "doing",
                    ago(hours=2, minutes=4),
                    None,
                    "38/64 done, 1 retried",
                ),
                ("Retry failures once with more memory", "todo", None, None),
                ("QC summary (MRIQC-lite + carpet plots)", "todo", None, None),
            ],
            status="on_track",
            note="≈ 1 h 20 m remaining at current throughput",
            updated=ago(minutes=52),
            metrics=[
                metric(
                    "Subjects done",
                    38,
                    [
                        (ago(hours=2, minutes=4), 0),
                        (ago(hours=1, minutes=35), 0),
                        (ago(hours=1, minutes=10), 19),
                        (ago(minutes=52), 38),
                    ],
                    total=64,
                ),
                metric(
                    "Failed jobs",
                    1,
                    [(ago(hours=1, minutes=10), 1), (ago(minutes=52), 1)],
                    good="down",
                ),
                metric("Core-hours", None, [], unit="h"),
            ],
        ),
    )
    return hub(
        "hcp-surface-decoding",
        root,
        [snap],
        96,
        git("main", "04be1aa", "Add HCP-D participant list", 0),
    )


# --------------------------------------------------------------------------- fresh
def fresh():
    root = "/Users/bbuchsbaum/code/mixeff"
    s = Session(
        "0c9d8e7f-6a5b-4c3d-9e2f-1a0b9c8d7e6f",
        "claude",
        "mixeff",
        root,
        ago(seconds=41),
        root,
    )
    s.ev(s.started, "session", summary="startup")
    t = prompt(
        s,
        ago(seconds=33),
        "Why does fit_lmm() warn about a singular fit on the sleepstudy example?",
    )
    s.tools(t, [("Read", "R/fit_lmm.R", 4, 0.1, True)])
    snap = s.snapshot(
        activity="working",
        activity_since=iso(ago(seconds=33)),
        current={
            "tool": "Grep",
            "summary": "isSingular|singular fit",
            "started": iso(ago(seconds=2)),
        },
    )
    return hub("mixeff", root, [snap], 4, git("main", "e02f7a1", "Initial import", 0))


# --------------------------------------------------------------------------- done
def done():
    root = "/Users/bbuchsbaum/code/neurosurf"
    s = Session(
        "9a8b7c6d-5e4f-4a3b-8c2d-1e0f9a8b7c6d",
        "claude",
        "neurosurf 0.4 release prep",
        root,
        ago(hours=1, minutes=33),
        root,
    )
    s.ev(s.started, "session", summary="startup")
    t = prompt(
        s,
        ago(hours=1, minutes=32),
        "Prepare neurosurf 0.4.0: check, coverage ≥ 80%, rebuild pkgdown, draft NEWS.",
    )
    t = s.tools(
        t,
        [
            (
                "Bash",
                "Rscript -e 'devtools::check()'",
                5,
                380,
                True,
                "0 errors ✔ | 0 warnings ✔ | 1 note ✖",
            ),
            (
                "Bash",
                "Rscript -e 'covr::package_coverage()'",
                5,
                140,
                True,
                "Coverage: 76.2%",
            ),
        ],
    )
    for i in range(6):
        t = s.tools(
            t,
            [
                (
                    "Write" if i == 0 else "Edit",
                    "tests/testthat/test-surface-geometry.R"
                    if i < 3
                    else "tests/testthat/test-smooth.R",
                    380,
                    0.1,
                    True,
                )
            ],
        )
    t = s.span(
        t,
        ago(minutes=24),
        [
            (
                "Bash",
                "Rscript -e 'covr::package_coverage()'",
                5,
                150,
                True,
                "Coverage: 82.9%",
            ),
            ("Bash", "Rscript -e 'pkgdown::build_site()'", 5, 210, True),
            ("Edit", "NEWS.md", 20, 0.1, True),
            (
                "Bash",
                "Rscript -e 'devtools::check()'",
                5,
                371,
                True,
                "0 errors ✔ | 0 warnings ✔ | 0 notes ✔",
            ),
        ],
    )
    t = turn_end(
        s,
        t + timedelta(seconds=20),
        "Release prep complete. Check clean, coverage 82.9%.",
    )
    end = t + timedelta(minutes=2)
    s.ev(end, "session", summary="end", detail="SessionEnd: prompt_input_exit")
    p = plan(
        "neurosurf 0.4.0 release prep",
        "Clean check, coverage ≥ 80%, site rebuilt, NEWS drafted",
        [
            (
                "R CMD check",
                "done",
                ago(hours=1, minutes=31),
                ago(hours=1, minutes=24),
                "1 NOTE: large installed size",
            ),
            (
                "Raise coverage to ≥ 80%",
                "done",
                ago(hours=1, minutes=24),
                ago(minutes=40),
                "76.2% → 82.9%",
            ),
            ("Rebuild pkgdown site", "done", ago(minutes=38), ago(minutes=33)),
            ("Draft NEWS.md", "done", ago(minutes=33), ago(minutes=31)),
            ("Final check", "done", ago(minutes=31), ago(minutes=24), "0/0/0"),
            ("Submit to CRAN", "skipped", None, None, "Out of scope — user submits"),
        ],
        status="done",
        note="Ready for submission",
        updated=ago(minutes=22),
        metrics=[
            metric(
                "Coverage",
                82.9,
                [
                    (ago(hours=1, minutes=22), 76.2),
                    (ago(minutes=55), 79.4),
                    (ago(minutes=41), 82.9),
                ],
                unit="%",
            ),
            metric(
                "Check NOTEs",
                0,
                [(ago(hours=1, minutes=24), 1), (ago(minutes=24), 0)],
                good="down",
            ),
        ],
        deliverables=[
            {
                "path": f"{root}/docs/index.html",
                "label": "pkgdown site",
                "ts": iso(ago(minutes=33)),
                "note": "Local build, not deployed",
            },
            {
                "path": f"{root}/reports/coverage report #2.html",
                "label": "Coverage report",
                "ts": iso(ago(minutes=40)),
                "note": "82.9% line coverage",
            },
            {
                "path": f"{root}/NEWS.md",
                "label": "NEWS.md",
                "ts": iso(ago(minutes=31)),
                "note": None,
            },
            {
                "path": "cran-comments.md",
                "label": "cran-comments.md",
                "ts": iso(ago(minutes=30)),
                "note": None,
            },
        ],
        log=[
            {
                "ts": iso(ago(minutes=24)),
                "text": "All gates green; stopping for user review.",
            }
        ],
    )
    snap = s.snapshot(
        activity="ended",
        activity_since=iso(end),
        ended=iso(end),
        plan=p,
        tests=[
            {
                "ts": iso(ago(hours=1, minutes=25)),
                "runner": "testthat",
                "passed": 301,
                "failed": 0,
                "skipped": 4,
                "command": "devtools::check()",
            },
            {
                "ts": iso(ago(minutes=40)),
                "runner": "testthat",
                "passed": 356,
                "failed": 0,
                "skipped": 4,
                "command": "covr::package_coverage()",
            },
            {
                "ts": iso(ago(minutes=25)),
                "runner": "testthat",
                "passed": 356,
                "failed": 0,
                "skipped": 4,
                "command": "devtools::check()",
            },
        ],
    )
    style = {"theme": "light", "density": "airy", "accent": "#0f766e", "notes": ""}
    return hub(
        "neurosurf",
        root,
        [snap],
        2210,
        git("release/0.4.0", "5f60c2b", "Bump version to 0.4.0", 0),
        style=style,
    )


# --------------------------------------------------------------------------- stalled
def stalled():
    root = "/Users/bbuchsbaum/code/fmriprep-qc"
    s = Session(
        "b1c2d3e4-f5a6-4b7c-8d9e-0f1a2b3c4d5e",
        "claude",
        "Carpet-plot QC for 24 subjects",
        root,
        ago(minutes=46),
        root,
    )
    s.ev(s.started, "session", summary="startup")
    t = prompt(
        s,
        ago(minutes=45),
        "Generate carpet plots and FD traces for every subject and flag anything with mean FD > 0.3 mm.",
    )
    t = s.tools(
        t,
        [
            ("Read", "qc/carpet.py", 3, 0.1, True),
            ("Edit", "qc/carpet.py", 40, 0.1, True),
            ("Bash", "uv run pytest tests/test_carpet.py -q", 5, 9, True, "6 passed"),
            (
                "Bash",
                "uv run python -m qc.carpet --subjects all --jobs 8",
                5,
                1210,
                True,
                "24/24 written",
            ),
            ("Read", "qc/out/summary.tsv", 3, 0.1, True),
            (
                "Bash",
                "uv run python -m qc.flag --fd 0.3 qc/out/summary.tsv",
                4,
                3,
                True,
                "flagged: sub-07, sub-19",
            ),
            ("Edit", "qc/report.qmd", 30, 0.1, True),
        ],
    )
    last = ago(minutes=14, seconds=6)
    s.ev(
        last,
        "tool",
        tool="Bash",
        summary="quarto render qc/report.qmd",
        ok=True,
        duration_ms=48000,
    )
    snap = s.snapshot(
        activity="stalled",
        activity_since=iso(last),
        current=None,
        plan=plan(
            "Carpet-plot QC",
            "24 carpet plots + FD traces; flagged subjects listed in a report",
            [
                (
                    "Carpet plots for 24 subjects",
                    "done",
                    ago(minutes=44),
                    ago(minutes=20),
                ),
                (
                    "Flag mean FD > 0.3 mm",
                    "done",
                    ago(minutes=20),
                    ago(minutes=17),
                    "sub-07, sub-19",
                ),
                ("Render QC report", "doing", ago(minutes=16), None),
            ],
            updated=ago(minutes=17),
        ),
        tests=[
            {
                "ts": iso(ago(minutes=44)),
                "runner": "pytest",
                "passed": 6,
                "failed": 0,
                "skipped": 0,
                "command": "uv run pytest tests/test_carpet.py -q",
            }
        ],
    )
    mote = {
        "store": f"{root}/.mote",
        "fetched": iso(ago(minutes=3)),
        "error": "mote: store is locked by another process (pid 48211)",
        "counts": None,
        "doing": [],
        "ready": [],
        "blocked": [],
        "reservations": [],
        "actors": [],
        "posts": [],
    }
    return hub(
        "fmriprep-qc",
        root,
        [snap],
        318,
        git("qc-report", "88d0e1f", "Carpet plots per subject", 2),
        mote=mote,
    )


# --------------------------------------------------------------------------- stress (gate only)
def stress():
    """Adversarial but contract-valid: long unbroken tokens, 8 sessions, a 16 KB message."""
    root = "/Users/bbuchsbaum/code/hcp-surface-decoding"
    deriv = ("derivatives/fmriprep-24.1.1/sub-HCD0001305_ses-V1MR/func/"
             "sub-HCD0001305_ses-V1MR_task-carit_acq-PA_run-1_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz")
    mcp = "mcp__remoteslurm-niagara-scinet-production__campaign_drive_until_terminal_with_retries"
    sub = "general-purpose-fmriprep-derivative-validator-with-bids-schema-checks"
    acts = ["working", "waiting_permission", "waiting_user", "stalled", "idle", "paused", "working", "ended"]
    sessions = []
    for i, act in enumerate(acts):
        sid = f"{i:x}{i:x}a{i}b{i}c{i}-0000-4000-8000-00000000000{i}"
        s = Session(sid, "codex" if i == 6 else "claude",
                    f"Session {i}: validate {deriv.split('/')[-1]}", root, ago(hours=1, minutes=i), root)
        s.ev(s.started, "session", summary="startup")
        t = prompt(s, ago(minutes=50 - i), "Check " + deriv + " " + "x" * 300)
        t = s.tools(t, [("Read", deriv, 3, 0.1, True), (mcp, deriv, 3, 12, False, "Traceback: " + "E" * 400),
                        ("Edit", deriv, 3, 0.1, True)], sub=sub if i % 2 else None)
        s.ev(t + timedelta(seconds=5), "note", summary=deriv + "/" + "n" * 200)
        s.ev(t + timedelta(seconds=6), "turn_end", detail="Wrote " + deriv)
        snap = s.snapshot(
            activity=act, activity_since=iso(ago(minutes=12)),
            current={"tool": mcp, "summary": deriv, "started": iso(ago(minutes=3))} if act in ("working", "waiting_permission") else None,
            attention=[{"kind": "permission", "text": "Claude needs your permission to use " + mcp, "ts": iso(ago(minutes=2))}] if act == "waiting_permission" else [],
            ended=iso(ago(minutes=5)) if act == "ended" else None,
            paused=act == "paused",
            plan=plan("Validate " + deriv, "Goal " + deriv,
                      [("Task " + deriv, "doing", ago(minutes=20), None, "note " + deriv)],
                      note="status " + deriv,
                      questions=[{"id": "Q1", "text": "Keep " + deriv + "?", "default": deriv, "asked": iso(ago(minutes=9)),
                                  "answer": None, "answered": None, "answered_via": None}],
                      blockers=[{"id": "B1", "text": "Missing " + deriv, "needs": "Access to " + deriv,
                                 "opened": iso(ago(minutes=8)), "closed": None}],
                      metrics=[metric("Metric " + "m" * 80, 1, [(ago(minutes=30), 0), (ago(minutes=5), 1)])],
                      deliverables=[{"path": f"{root}/{deriv}", "label": deriv, "ts": iso(ago(minutes=4)), "note": deriv}],
                      log=[{"ts": iso(ago(minutes=6)), "text": "Log " + deriv}]) if i < 3 else None,
            inbox=[{"id": f"m{i}", "ts": iso(ago(minutes=3)), "kind": "message", "text": ("long message " * 1400)[:16000],
                    "qid": None, "status": "queued", "delivered": None, "via": None}] if i == 0 else [],
        )
        sessions.append(snap)
    conflicts = [{"path": deriv, "sessions": [x["short"] for x in sessions[:3]], "sources": ["edit"], "live": False,
                  "last_edit": iso(ago(minutes=30)), "mote_reserved_by": None,
                  "detail": [{"session": x["short"], "kind": "edit", "ts": iso(ago(minutes=30)), "ref": None, "expires": None} for x in sessions[:3]]}]
    return hub("hcp-surface-decoding-with-a-rather-long-project-name", root, sessions, 9999,
               git("feature/" + "very-long-branch-name-" * 4, "0123abc", "subject", 3), conflicts)


FIXTURES = {
    "solo-rcheck": solo_rcheck,
    "trio-mote": trio_mote,
    "needs-you": needs_you,
    "slurm-long": slurm_long,
    "fresh": fresh,
    "done": done,
    "stalled": stalled,
    "stress": stress,  # overflow gate only, not in the screenshot gallery
}

if __name__ == "__main__":
    for name, fn in FIXTURES.items():
        (HERE / f"{name}.json").write_text(
            json.dumps(fn(), indent=1, ensure_ascii=False) + "\n"
        )
        print(f"wrote {name}.json")
