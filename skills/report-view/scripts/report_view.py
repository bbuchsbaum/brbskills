#!/usr/bin/env python3
"""Pull an HTML report (local or over ssh) into a local cache, serve it on
127.0.0.1, and open it in the default browser. Stdlib only.

Usage:
  report_view.py [--host HOST] [--max-mb N] [--no-open] [--port P] PATH
  report_view.py HOST:PATH            # same as --host HOST PATH
  report_view.py --list               # cached reports and running servers
  report_view.py --stop [all|DIR]     # stop servers this tool started
  report_view.py --prune DAYS         # delete cached copies older than DAYS

PATH may be an .html file or a directory (index.html, or a single .html).
Remote paths may use ~ or remote env vars ($SCRATCH, $PROJECT): they are
resolved on the remote host. The whole directory containing the report is
mirrored, so point at a clean report/bundle directory, not a data directory.
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import http.server
import json
import re
import os
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

CACHE = Path(os.environ.get("REPORT_VIEW_CACHE", "~/.cache/report-view")).expanduser()
SERVERS = CACHE / ".servers"


def die(msg: str, code: int = 1) -> None:
    print(f"report-view: {msg}", file=sys.stderr)
    sys.exit(code)


REMOTE_PATH_RE = re.compile(r"^[A-Za-z0-9_./~${}@+=,:%-]+$")
HOST_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.@-]*$")


def ssh_base(host: str) -> list[str]:
    # BatchMode: never prompt (MFA hosts need the user to connect first).
    return ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", host]


def remote_resolve(host: str, path: str) -> tuple[str, str]:
    """Return (report_dir, html_name) on the remote host."""
    # Expand ~ and $VARS remotely, but only within a double-quoted word built from a
    # conservative character set, so the path can never become extra shell commands.
    if not REMOTE_PATH_RE.match(path):
        die(f"refusing remote path {path!r}: use only letters, digits, and _ . / ~ $ {{ }} @ + = , : % -")
    if not HOST_RE.match(host):
        die(f"refusing ssh host {host!r}")
    if path == "~" or path.startswith("~/"):
        path = "$HOME" + path[1:]
    script = (
        f'p="{path}"; '
        'if [ -d "$p" ]; then d=$(cd "$p" && pwd); '
        '  if [ -f "$d/index.html" ]; then f=index.html; '
        '  else n=$(ls "$d"/*.html 2>/dev/null | wc -l); '
        '    if [ "$n" = 1 ]; then f=$(basename "$d"/*.html); '
        '    else echo "ERR ambiguous: $n html files in $d" ; exit 3; fi; fi; '
        'elif [ -f "$p" ]; then d=$(cd "$(dirname "$p")" && pwd); f=$(basename "$p"); '
        'else echo "ERR not found: $p"; exit 2; fi; '
        'printf "%s\\n%s\\n" "$d" "$f"'
    )
    r = subprocess.run(ssh_base(host) + [script], capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip()
    if r.returncode == 255:
        die(
            f"cannot reach {host} non-interactively ({out.splitlines()[-1] if out else 'ssh failed'}).\n"
            f"  Ask the user to authenticate once (password/MFA), e.g.:  ! ssh {host} true\n"
            f"  (with a ControlMaster/ControlPersist entry in ~/.ssh/config the session is then reused;\n"
            f"   for remoteslurm-managed hosts:  ! remoteslurm connect {host})"
        )
    if r.returncode != 0 or out.startswith("ERR"):
        die(out or f"remote resolve failed (exit {r.returncode})")
    lines = r.stdout.strip().splitlines()
    return lines[-2], lines[-1]


def local_resolve(path: str) -> tuple[Path, str]:
    p = Path(path).expanduser().resolve()
    if p.is_dir():
        if (p / "index.html").is_file():
            return p, "index.html"
        htmls = sorted(p.glob("*.html"))
        if len(htmls) != 1:
            die(f"ambiguous: {len(htmls)} .html files in {p}; pass the file")
        return p, htmls[0].name
    if p.is_file():
        return p.parent, p.name
    die(f"not found: {p}")
    raise AssertionError


def rsync_size_mb(host: str, rdir: str) -> float:
    r = subprocess.run(
        [
            "rsync",
            "-a",
            "--dry-run",
            "--stats",
            "-e",
            "ssh -o BatchMode=yes",
            f"{host}:{rdir}/",
            "/nonexistent-report-view-probe/",
        ],
        capture_output=True,
        text=True,
    )
    for line in r.stdout.splitlines():
        if line.startswith("Total file size:"):
            num = line.split(":", 1)[1].split("bytes")[0].strip().replace(",", "")
            return int(num) / 1e6
    die(f"could not size remote directory: {(r.stderr or r.stdout).strip()}")
    raise AssertionError


def pull(host: str, rdir: str, max_mb: float) -> Path:
    mb = rsync_size_mb(host, rdir)
    if mb > max_mb:
        die(
            f"{host}:{rdir} is {mb:.0f} MB (> --max-mb {max_mb:.0f}). It may hold source data.\n"
            "  Point at a clean bundle (neuromosaic::write_report_bundle()) or raise --max-mb."
        )
    dest = CACHE / host / rdir.lstrip("/")
    dest.mkdir(parents=True, exist_ok=True)
    print(f"report-view: pulling {mb:.1f} MB from {host}:{rdir}", file=sys.stderr)
    r = subprocess.run(
        [
            "rsync",
            "-a",
            "--delete",
            "-e",
            "ssh -o BatchMode=yes",
            f"{host}:{rdir}/",
            f"{dest}/",
        ]
    )
    if r.returncode != 0:
        die(f"rsync failed (exit {r.returncode})")
    os.utime(dest)
    return dest


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".js": "text/javascript",
        ".mjs": "text/javascript",
        ".wasm": "application/wasm",
        ".json": "application/json",
        ".gz": "application/gzip",
    }

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def guess_type(self, path):  # never let mimetypes add Content-Encoding
        ext = os.path.splitext(str(path))[1].lower()
        return self.extensions_map.get(ext) or super().guess_type(path)

    def log_message(self, *args) -> None:
        pass


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def server_key(root: Path) -> Path:
    return SERVERS / (hashlib.sha1(str(root).encode()).hexdigest()[:12] + ".json")


def alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def stop_record(rec_path: Path) -> None:
    try:
        rec = json.loads(rec_path.read_text())
    except (OSError, ValueError):
        rec_path.unlink(missing_ok=True)
        return
    pid = rec.get("pid")
    # Only kill a PID we recorded AND that is still our serve process.
    if pid and alive(pid):
        ps = subprocess.run(
            ["ps", "-o", "command=", "-p", str(pid)], capture_output=True, text=True
        )
        if "report_view.py" in ps.stdout and "--_serve" in ps.stdout:
            os.kill(pid, signal.SIGTERM)
            print(
                f"report-view: stopped server pid {pid} for {rec.get('root')}",
                file=sys.stderr,
            )
    rec_path.unlink(missing_ok=True)


def serve(root: Path, html: str, port: int | None, open_browser: bool) -> None:
    SERVERS.mkdir(parents=True, exist_ok=True)
    rec_path = server_key(root)
    if rec_path.exists():
        rec = json.loads(rec_path.read_text())
        if alive(rec.get("pid", 0)) and (port is None or port == rec["port"]):
            url = f"http://127.0.0.1:{rec['port']}/{html}"
            print(url)
            if open_browser:
                webbrowser.open(url)
            return
        stop_record(rec_path)
    port = port or free_port()
    proc = subprocess.Popen(
        [sys.executable, os.path.abspath(__file__), "--_serve", str(root), str(port)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    for _ in range(50):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                break
        except OSError:
            time.sleep(0.1)
    else:
        proc.kill()
        die(f"server did not start on port {port}")
    rec_path.write_text(
        json.dumps(
            {
                "pid": proc.pid,
                "port": port,
                "root": str(root),
                "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }
        )
    )
    url = f"http://127.0.0.1:{port}/{html}"
    print(url)
    print(
        f"report-view: serving {root} (pid {proc.pid}); stop with --stop",
        file=sys.stderr,
    )
    if open_browser:
        webbrowser.open(url)


def run_server(root: str, port: int) -> None:
    handler = functools.partial(Handler, directory=root)
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    httpd.serve_forever()


def list_cmd() -> None:
    SERVERS.mkdir(parents=True, exist_ok=True)
    for rec_path in sorted(SERVERS.glob("*.json")):
        rec = json.loads(rec_path.read_text())
        state = "running" if alive(rec["pid"]) else "dead"
        print(
            f"server  {state:7} port {rec['port']:<5} pid {rec['pid']:<6} {rec['root']}"
        )
    if CACHE.exists():
        for host in sorted(
            p for p in CACHE.iterdir() if p.is_dir() and p.name != ".servers"
        ):
            for d in sorted({h.parent for h in host.rglob("*.html")}):
                mb = sum(f.stat().st_size for f in d.rglob("*") if f.is_file()) / 1e6
                age = (time.time() - d.stat().st_mtime) / 86400
                print(f"cache   {age:5.1f}d {mb:8.1f} MB  {d}")


def prune_cmd(days: float) -> None:
    if not CACHE.exists():
        return
    running = set()
    for rec_path in SERVERS.glob("*.json"):
        rec = json.loads(rec_path.read_text())
        if alive(rec["pid"]):
            running.add(rec["root"])
    cutoff = time.time() - days * 86400
    for host in (p for p in CACHE.iterdir() if p.is_dir() and p.name != ".servers"):
        for d in sorted({h.parent for h in host.rglob("*.html")}):
            if str(d) in running or d.stat().st_mtime > cutoff:
                continue
            # Only delete inside our own cache tree.
            if CACHE.resolve() in d.resolve().parents:
                shutil.rmtree(d)
                print(f"report-view: pruned {d}", file=sys.stderr)


def main() -> None:
    if len(sys.argv) >= 2 and sys.argv[1] == "--_serve":
        run_server(sys.argv[2], int(sys.argv[3]))
        return
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("path", nargs="?")
    ap.add_argument("--host")
    ap.add_argument("--max-mb", type=float, default=500)
    ap.add_argument("--port", type=int)
    ap.add_argument("--no-open", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--stop", nargs="?", const="all")
    ap.add_argument("--prune", type=float, metavar="DAYS")
    a = ap.parse_args()

    if a.list:
        return list_cmd()
    if a.stop:
        SERVERS.mkdir(parents=True, exist_ok=True)
        if a.stop == "all":
            for rec_path in SERVERS.glob("*.json"):
                stop_record(rec_path)
        else:
            stop_record(server_key(Path(a.stop).expanduser().resolve()))
        return
    if a.prune is not None:
        return prune_cmd(a.prune)
    if not a.path:
        ap.error("PATH is required")

    host, path = a.host, a.path
    if (
        host is None
        and ":" in path
        and not Path(path).exists()
        and not path.startswith("/")
    ):
        host, path = path.split(":", 1)
    if host:
        rdir, html = remote_resolve(host, path)
        root = pull(host, rdir, a.max_mb)
    else:
        root, html = local_resolve(path)
    serve(root.resolve(), html, a.port, not a.no_open)


if __name__ == "__main__":
    main()
