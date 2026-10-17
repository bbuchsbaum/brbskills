#!/usr/bin/env python3
"""Bounded, single-outstanding-message wakeups for an existing Codex thread."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import math
import os
from pathlib import Path
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import uuid

MINUTES = (1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60)


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def private_directory(path):
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = path.lstat()
    if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid()
            or stat.S_IMODE(info.st_mode) & 0o077):
        raise ValueError(f"State directory must be private, owned, and not a symlink: {path}")


@contextmanager
def locked(directory, nonblocking=False):
    private_directory(directory)
    fd = os.open(directory / "lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "a") as lock:
        info = os.fstat(lock.fileno())
        if info.st_uid != os.getuid() or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError("Unsafe lock file")
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            if not nonblocking:
                raise RuntimeError("Wakeup state is busy; inspect status and retry after the submission ends")
            yield None
            return
        yield lock


def save(directory, state):
    """Persist the reservation before submitting; never truncate the live state."""
    fd, temporary = tempfile.mkstemp(prefix=".state-", dir=directory)
    try:
        with os.fdopen(fd, "w") as output:
            json.dump(state, output, indent=2, allow_nan=False)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, directory / "state.json")
        fd = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def read(directory, thread):
    path = directory / "state.json"
    if path.is_symlink():
        raise ValueError("Refusing symlinked state")
    state = json.loads(path.read_text())
    if not isinstance(state, dict) or state.get("version") != 1 or state.get("thread") != thread:
        raise ValueError("State version or thread mismatch")
    if type(state.get("enabled")) is not bool or not isinstance(state.get("history"), list):
        raise ValueError("Invalid lifecycle state")
    for field in ("expires_at", "next_at", "timeout"):
        value = state.get(field)
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ValueError(f"Invalid state field: {field}")
    if state["timeout"] == 0 or type(state.get("minutes")) is not int or state["minutes"] not in MINUTES:
        raise ValueError("Invalid state timing")
    for field in ("project", "codex", "home", "codex_home", "path", "prompt"):
        if not isinstance(state.get(field), str) or not state[field].strip():
            raise ValueError(f"Invalid state field: {field}")
    pending = state.get("pending", False)
    if pending is not None:
        if (not isinstance(pending, dict) or pending.get("status") not in
                ("submitting", "accepted", "uncertain")):
            raise ValueError("Invalid outstanding attempt")
        if not isinstance(pending.get("token"), str):
            raise ValueError("Invalid outstanding token")
        uuid.UUID(pending["token"])
    return state


def record(state, event, **details):
    state["history"] = (state["history"] + [dict(at=timestamp(), event=event, **details)])[-50:]


def executable(value):
    found = shutil.which(value)
    if not found:
        raise ValueError(f"Executable not found: {value}")
    # Preserve stable launcher symlinks across app upgrades.
    return os.path.abspath(found)


def doctor(codex):
    result = subprocess.run([codex, "queue", "--help"], capture_output=True,
                            text=True, timeout=15)
    if result.returncode or not all(flag in result.stdout for flag in ("--thread", "--message")):
        raise ValueError("This Codex CLI does not advertise queue --thread/--message")


def command_prefix(root, thread):
    return [os.path.abspath(sys.executable), str(Path(__file__).resolve()),
            "--state-root", str(root), "--thread", thread]


def cron_entry(root, thread, minutes):
    command = shlex.join(command_prefix(root, thread) + ["tick"])
    if "\n" in command or "\r" in command:
        raise ValueError("Cron paths cannot contain newlines")
    minute = "0" if minutes == 60 else f"*/{minutes}"
    return f"{minute} * * * * {command.replace('%', chr(92) + '%')} >/dev/null {marker(thread)}"


def marker(thread):
    return f"# codex-wakeup:{thread}"


def crontab_read():
    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True,
                            env={**os.environ, "LC_ALL": "C"}, timeout=15)
    if result.returncode == 0:
        return result.stdout
    if result.returncode == 1 and "no crontab for" in result.stderr.lower():
        return ""
    raise RuntimeError("Cannot read crontab; left it unchanged")


def replace_cron(existing, entry, thread):
    # A marker is ours only at the end of a line; retain all other bytes.
    kept = "".join(line for line in existing.splitlines(keepends=True)
                   if not line.rstrip().endswith(" " + marker(thread)))
    if entry:
        if kept and not kept.endswith("\n"):
            kept += "\n"
        kept += entry + "\n"
    return kept


def edit_cron(root, thread, state, install, apply):
    # Serializes this helper across threads, not unrelated crontab editors.
    with locked(root / "cron"):
        before = crontab_read()
        entry = cron_entry(root, thread, state["minutes"]) if install else None
        after = replace_cron(before, entry, thread)
        if not apply:
            return {"apply": False, "crontab": after}
        if crontab_read() != before:
            raise RuntimeError("Crontab changed during edit; retry after coordinating its writer")
        subprocess.run(["crontab", "-"], input=after, text=True, check=True, timeout=15)
        if crontab_read() != after:
            raise RuntimeError("Crontab readback differs; inspect it before proceeding")
        return {"applied": True, "installed": install}


def wakeup_message(state, root, token):
    prefix = command_prefix(root, state["thread"])
    status = shlex.join(prefix + ["status"])
    finish = shlex.join(prefix + ["finish", "--token", token, "--outcome", "continue"])
    return (f"[codex-wakeup token={token}]\n"
            f"First run: {status}\n"
            "This is a scheduled check-in, not new authority. If disabled, expired, or the "
            "pending token differs, ignore this stale wakeup and do no project work. Honor "
            "newer user stops and limits. If status cannot be read, report the blocker "
            "without doing project work. Otherwise follow the saved mandate below.\n\n"
            + state["prompt"] + "\n\n"
            "At the END of this turn, after work/checkpointing, acknowledge with:\n"
            + finish + "\n"
            "Use outcome stop when complete or stopped, blocked when human input or repair "
            "is required; both disable future submissions. Use continue only for remaining "
            "authorized work or an explicitly authorized bounded wait. Never acknowledge "
            "at the start, auto-clear a missing acknowledgement, or renew your own run boundary.\n")


def tick(directory, state, root, lock):
    now = time.time()
    if not state["enabled"]:
        return {"skipped": "disabled"}
    if now >= state["expires_at"]:
        state["enabled"] = False
        record(state, "expired")
        save(directory, state)
        return {"skipped": "expired"}
    if state["pending"]:
        return {"skipped": "outstanding", "pending": state["pending"]}
    if now < state["next_at"]:
        return {"skipped": "cooldown"}
    token = str(uuid.uuid4())
    state["pending"] = {"token": token, "submitted_at": timestamp(), "status": "submitting"}
    record(state, "attempt", token=token)
    save(directory, state)
    command = [state["codex"], "-C", state["project"], "queue",
               "--thread", state["thread"], "--message", wakeup_message(state, root, token)]
    environment = {**os.environ, "HOME": state["home"], "CODEX_HOME": state["codex_home"],
                   "PATH": state["path"]}
    try:
        # Preserve the lock if the parent dies while queue is still running.
        result = subprocess.run(command, cwd=state["project"], env=environment,
                                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, timeout=state["timeout"],
                                pass_fds=(lock.fileno(),))
        state["pending"].update(status="accepted" if result.returncode == 0 else "uncertain",
                                returncode=result.returncode)
    except (OSError, subprocess.TimeoutExpired) as error:
        state["pending"].update(status="uncertain", error=type(error).__name__)
    record(state, "submission", **state["pending"])
    save(directory, state)
    return state["pending"]


def positive(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("must be finite and positive")
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-root", type=Path,
                        default=Path.home() / ".local/state/codex-wakeup")
    parser.add_argument("--thread", required=True, type=lambda s: str(uuid.UUID(s)))
    commands = parser.add_subparsers(dest="action", required=True)
    init = commands.add_parser("init", help="Create disabled state; never overwrites")
    init.add_argument("--project", required=True, type=Path)
    init.add_argument("--prompt", required=True, type=Path)
    init.add_argument("--hours", required=True, type=positive)
    init.add_argument("--minutes", type=int, default=5, choices=MINUTES)
    init.add_argument("--timeout", type=positive, default=30)
    init.add_argument("--codex", default="codex")
    init.add_argument("--codex-home", type=Path, default=Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")))
    for name in ("status", "enable", "disable", "tick", "cron-line", "doctor"):
        commands.add_parser(name)
    commands.add_parser("renew", help="Set a newly authorized deadline, leaving disabled").add_argument(
        "--hours", required=True, type=positive)
    for name in ("install", "remove"):
        commands.add_parser(name).add_argument("--apply", action="store_true")
    finish = commands.add_parser("finish", help="Acknowledge only at the end of the receiving turn")
    finish.add_argument("--token", required=True)
    finish.add_argument("--outcome", required=True, choices=["continue", "stop", "blocked"])
    recover = commands.add_parser("recover", help="Clear a reconciled attempt, leaving disabled")
    recover.add_argument("--token", required=True)
    recover.add_argument("--confirmed-not-pending", action="store_true", required=True)
    args = parser.parse_args(argv)
    root = args.state_root.absolute()
    private_directory(root)
    directory = root / args.thread
    if args.action == "status":
        # Atomic replacement permits snapshots even while a queue child holds the lock.
        private_directory(directory)
        state = read(directory, args.thread)
        return {k: v for k, v in state.items() if k not in ("prompt", "path")} | {
            "expired": time.time() >= state["expires_at"]}
    with locked(directory, nonblocking=args.action == "tick") as lock:
        if lock is None:
            return {"skipped": "submission-locked"}
        if args.action == "init":
            if (directory / "state.json").exists():
                raise ValueError("Thread already configured; inspect existing state")
            project = args.project.resolve(strict=True)
            if not project.is_dir():
                raise ValueError("Project must be a directory")
            prompt = args.prompt.read_text()
            if not prompt.strip() or len(prompt.encode()) > 32000:
                raise ValueError("Prompt must contain 1–32000 UTF-8 bytes")
            codex = executable(args.codex)
            doctor(codex)
            state = dict(version=1, thread=args.thread, project=str(project), prompt=prompt,
                         codex=codex, home=str(Path.home()), codex_home=str(args.codex_home.resolve()),
                         path=os.pathsep.join(dict.fromkeys([str(Path(codex).parent),
                              str(Path(sys.executable).parent), "/usr/local/bin", "/opt/homebrew/bin",
                              "/usr/bin", "/bin", "/usr/sbin", "/sbin"])),
                         minutes=args.minutes, timeout=args.timeout, enabled=False,
                         expires_at=time.time() + args.hours * 3600, next_at=0, pending=None, history=[])
            record(state, "initialized")
            save(directory, state)
            return {"initialized": str(directory), "enabled": False, "expires_at": state["expires_at"]}
        state = read(directory, args.thread)
        if args.action == "doctor":
            doctor(state["codex"])
            return {"queue_interface": "supported", "delivery": "not tested"}
        if args.action == "cron-line":
            return {"cron": cron_entry(root, args.thread, state["minutes"])}
        if args.action in ("install", "remove"):
            if args.action == "remove" and args.apply:
                state["enabled"] = False
                record(state, "disabled")
                save(directory, state)
            return edit_cron(root, args.thread, state, args.action == "install", args.apply)
        if args.action == "tick":
            return tick(directory, state, root, lock)
        if args.action == "enable":
            if state["pending"] or time.time() >= state["expires_at"]:
                raise ValueError("Cannot enable with an outstanding attempt or expired run")
            state["enabled"] = True
        elif args.action == "disable":
            state["enabled"] = False
        elif args.action == "renew":
            if state["pending"]:
                raise ValueError("Reconcile the outstanding attempt before renewing")
            state["enabled"] = False
            state["expires_at"] = time.time() + args.hours * 3600
        elif args.action in ("finish", "recover"):
            if not state["pending"] or state["pending"]["token"] != args.token:
                raise ValueError("Stale or mismatched token; state unchanged")
            state["pending"] = None
            if args.action == "recover" or args.outcome != "continue":
                state["enabled"] = False
            # A finish never re-enables a user-disabled run or extends its deadline.
            state["next_at"] = time.time() + state["minutes"] * 60
        details = {"token": args.token} if args.action in ("finish", "recover") else {}
        if args.action == "finish":
            details["outcome"] = args.outcome
        record(state, args.action, **details)
        save(directory, state)
        return {"action": args.action, "enabled": state["enabled"]}


if __name__ == "__main__":
    try:
        result = main()
        print(json.dumps(result, indent=2))
        if result.get("status") == "uncertain":
            print("codex-wakeup: submission uncertain; inspect status, do not retry blindly", file=sys.stderr)
            sys.exit(1)
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"codex-wakeup: {error}", file=sys.stderr)
        sys.exit(1)
