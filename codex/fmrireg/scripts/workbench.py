#!/usr/bin/env python3
"""Local state, preference and admission checks for fMRI skills (Python >=3.10).

No R execution, network access, arbitrary-code evaluation or cloud API calls.
Approval records describe consent; they are not security capabilities.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
from datetime import datetime, timezone
from typing import Any, Iterator

VERSION = "1.0"
STAGES = ("discovery", "first_level", "group", "report")
KEY = re.compile(r"^[a-z][a-z0-9_.-]*$")
REQUIRED = {
    "discovery": ("data_boundary", "source_inventory", "metadata_resolution"),
    "first_level": ("data_boundary", "input_alignment", "native_preflight", "design_qc"),
    "group": ("data_boundary", "input_alignment", "group_design", "multiplicity_plan"),
    "report": ("data_boundary", "map_semantics", "spatial_qc", "inference_metadata", "privacy_review"),
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def canonical(x: Any) -> str:
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha(x: Any) -> str:
    return hashlib.sha256(canonical(x).encode("utf-8")).hexdigest()


def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(f"Nonfinite JSON: {x}")))


def atomic_write(path: Path, obj: Any) -> None:
    text = json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


@contextlib.contextmanager
def locked(path: Path) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_name(path.name + ".lock")
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as e:
        raise ValueError(f"Locked: {path}. Inspect the writer; never delete a live lock.") from e
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(json.dumps({"pid": os.getpid(), "time": now()}))
        yield
    finally:
        lock.unlink(missing_ok=True)


def plan_digest(plan: dict) -> str:
    return sha({k: v for k, v in plan.items() if k != "approval"})


def new_plan(analysis_id: str, scope: list[str]) -> dict:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", analysis_id):
        raise ValueError("analysis_id must be a short safe identifier")
    if not scope or len(set(scope)) != len(scope) or set(scope) - set(STAGES):
        raise ValueError(f"scope must be unique entries from {STAGES}")
    return {
        "schema_version": VERSION, "analysis_id": analysis_id, "scope": scope,
        "stage_configs": {s: {} for s in scope},
        "decisions": [{"key": "scientific_question", "stage": "shared", "value": None,
                       "status": "unresolved", "material": True}],
        "checks": [{"id": c, "stage": s, "status": "not_checked", "blocking": True,
                    "evidence": ""} for s in scope for c in REQUIRED[s]],
        "fingerprints": {},
        "budget": {"approved": False, "cpu_hours": None, "max_workers": 1, "max_memory_gb": None},
        "data_policy": {"model_visible": "unresolved", "sharing": "none"},
        "approval": {},
    }


def _positive(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) and x > 0


def plan_errors(plan: dict, stage: str | None = None, purpose: str = "full") -> list[str]:
    errors: list[str] = []
    if not isinstance(plan, dict):
        return ["Plan must be an object"]
    if plan.get("schema_version") != VERSION:
        errors.append("Unsupported schema_version")
    scope = plan.get("scope", [])
    if not isinstance(scope, list) or not scope or any(x not in STAGES for x in scope) or len(scope) != len(set(scope)):
        return errors + ["Invalid scope"]
    targets = [stage] if stage else scope
    if any(s not in scope for s in targets):
        return errors + ["Requested stage is not in plan scope"]
    if purpose not in ("pilot", "full"):
        return errors + ["purpose must be pilot or full"]
    for k in ("stage_configs", "fingerprints", "budget", "data_policy", "approval"):
        if not isinstance(plan.get(k), dict):
            errors.append(f"{k} must be an object")
    for k in ("checks", "decisions"):
        if not isinstance(plan.get(k), list):
            errors.append(f"{k} must be a list")
    if errors:
        return errors
    if plan["data_policy"].get("model_visible") not in ("aggregate_only", "approved_subject_level", "synthetic"):
        errors.append("Model-visible data boundary is unresolved")
    for d in plan["decisions"]:
        if not isinstance(d, dict):
            errors.append("Decision must be an object")
            continue
        if d.get("stage") in ["shared", *targets] and d.get("material", True):
            if d.get("status") not in ("confirmed", "observed") or d.get("value") is None:
                errors.append(f"Unresolved material decision: {d.get('key', '?')}")
    check_index = {}
    for c in plan["checks"]:
        if not isinstance(c, dict):
            errors.append("Check must be an object")
            continue
        key = (c.get("stage"), c.get("id"))
        if key in check_index:
            errors.append(f"Duplicate check: {key}")
        check_index[key] = c
        if c.get("stage") in ["shared", *targets] and c.get("blocking", True) and c.get("status") != "pass":
            errors.append(f"Blocking check not passed: {c.get('stage')}.{c.get('id')}")
    for s in targets:
        if not isinstance(plan["stage_configs"].get(s), dict) or not plan["stage_configs"].get(s):
            errors.append(f"Empty stage configuration: {s}")
        required = list(REQUIRED[s])
        if purpose == "full" and s in ("first_level", "group"):
            required.append("pilot_qc")
        for c in required:
            item = check_index.get((s, c), {})
            if item.get("status") != "pass" or not str(item.get("evidence", "")).strip():
                errors.append(f"Need documented passing check: {s}.{c}")
    if any(s != "discovery" for s in targets):
        b = plan["budget"]
        if b.get("approved") is not True or not _positive(b.get("cpu_hours")) or not _positive(b.get("max_memory_gb")):
            errors.append("Execution resource budget is unapproved or incomplete")
        w = b.get("max_workers")
        if not isinstance(w, int) or isinstance(w, bool) or w < 1:
            errors.append("max_workers must be a positive integer")
        for k in ("inputs", "code", "environment"):
            fp = plan["fingerprints"].get(k, {})
            if not isinstance(fp, dict) or not re.fullmatch(r"[0-9a-f]{64}", str(fp.get("sha256", ""))) or not fp.get("path"):
                errors.append(f"Missing content fingerprint: {k}")
    return list(dict.fromkeys(errors))


def verify_files(plan: dict) -> list[str]:
    errors = []
    for k, fp in plan.get("fingerprints", {}).items():
        if not isinstance(fp, dict) or not fp.get("path") or not fp.get("sha256"):
            errors.append(f"Malformed fingerprint: {k}")
            continue
        try:
            if file_sha(Path(fp["path"])) != fp["sha256"]:
                errors.append(f"Changed sealed file: {k}")
        except OSError:
            errors.append(f"Missing/unreadable sealed file: {k}")
    return errors


def authorize(plan: dict, stage: str, purpose: str, reviewed_digest: str,
              confirmed: bool, evidence: str) -> dict:
    if not confirmed or not evidence.strip():
        raise ValueError("Explicit user confirmation and evidence are required")
    errors = plan_errors(plan, stage, purpose) + verify_files(plan)
    if plan_digest(plan) != reviewed_digest:
        errors.append("Plan changed since the supplied reviewed digest")
    if errors:
        raise ValueError("; ".join(errors))
    out = copy.deepcopy(plan)
    out["approval"][f"{stage}:{purpose}"] = {
        "digest": reviewed_digest, "confirmed_at": now(), "evidence": evidence,
        "source": "explicit_user", "stage": stage, "purpose": purpose,
    }
    return out


def approval_errors(plan: dict, stage: str, purpose: str) -> list[str]:
    errors = plan_errors(plan, stage, purpose) + verify_files(plan)
    ap = plan.get("approval", {}).get(f"{stage}:{purpose}", {})
    if ap.get("source") != "explicit_user" or not ap.get("evidence"):
        errors.append("No explicit approval for this stage/purpose")
    if ap.get("digest") != plan_digest(plan):
        errors.append("Approval missing or stale for current plan")
    return errors


def empty_preferences() -> dict:
    return {"schema_version": VERSION, "preferences": [], "events": []}


def validate_preferences(doc: dict) -> None:
    if not isinstance(doc, dict) or doc.get("schema_version") != VERSION or not isinstance(doc.get("preferences"), list):
        raise ValueError("Invalid preferences envelope")
    seen = set()
    for r in doc["preferences"]:
        if not isinstance(r, dict):
            raise ValueError("Preference must be an object")
        key, when = r.get("key", ""), r.get("when", {})
        if not isinstance(key, str) or not KEY.fullmatch(key) or not key.startswith(("communication.", "first_level.", "group.", "reporting.", "compute.", "x.")):
            raise ValueError(f"Invalid/inert namespace: {key}; authorization cannot be stored as a preference")
        if not isinstance(when, dict) or any(not isinstance(k, str) or isinstance(v, (dict, list)) or v is None for k, v in when.items()):
            raise ValueError("when must be a dictionary of non-null scalar exact matches")
        if "value" not in r or r.get("source") != "explicit_user" or not r.get("evidence") or not r.get("confirmed_at"):
            raise ValueError(f"Unconfirmed/incomplete preference: {key}")
        identity = (key, canonical(when))
        if identity in seen:
            raise ValueError(f"Duplicate scoped preference: {key}")
        seen.add(identity)
        canonical(r)  # Reject NaN, infinity and non-JSON values.


def mutate_preference(doc: dict, key: str, when: dict, value: Any = None,
                      remove: bool = False, confirmed: bool = False, evidence: str = "") -> dict:
    if not confirmed or not evidence.strip():
        raise ValueError("Explicit user confirmation and evidence are required")
    validate_preferences(doc)
    out = copy.deepcopy(doc)
    out["preferences"] = [r for r in out["preferences"] if not (r["key"] == key and canonical(r.get("when", {})) == canonical(when))]
    if not remove:
        out["preferences"].append({"key": key, "value": value, "when": when,
                                   "source": "explicit_user", "confirmed_at": now(), "evidence": evidence})
    out.setdefault("events", []).append({"operation": "remove" if remove else "set", "key": key,
                                          "when": when, "at": now(), "evidence": evidence})
    validate_preferences(out)
    return out


def resolve_preferences(user: dict, project: dict, context: dict,
                        current: dict | None = None, locked_values: dict | None = None) -> dict:
    if not all(isinstance(x, dict) for x in (context, current or {}, locked_values or {})):
        raise ValueError("context/current/locked must be JSON objects")
    values, sources, conflicts = {}, {}, []
    for layer, doc in (("user", user), ("project", project)):
        validate_preferences(doc)
        grouped: dict[str, list] = {}
        for r in doc["preferences"]:
            if all(k in context and canonical(context[k]) == canonical(v) for k, v in r.get("when", {}).items()):
                grouped.setdefault(r["key"], []).append(r)
        for key, rows in grouped.items():
            n = max(len(r.get("when", {})) for r in rows)
            best = [r for r in rows if len(r.get("when", {})) == n]
            if len({canonical(r["value"]) for r in best}) > 1:
                conflicts.append(f"Ambiguous {layer} preference: {key}")
                values.pop(key, None); sources.pop(key, None)
            else:
                values[key], sources[key] = best[0]["value"], {"layer": layer, "record": best[0]}
    for key, value in (current or {}).items():
        values[key], sources[key] = value, {"layer": "current_approved"}
    for key, value in (locked_values or {}).items():
        if key in values and canonical(values[key]) != canonical(value):
            conflicts.append(f"Locked protocol conflict requiring amendment: {key}")
            values.pop(key, None); sources.pop(key, None)
        else:
            values[key], sources[key] = value, {"layer": "locked_protocol"}
    return {"values": values, "sources": sources, "conflicts": conflicts}


def audit_inventory(doc: dict) -> dict:
    """Selected-row ambiguity checks only; not a BIDS validator/import certificate."""
    errors, warnings = [], []
    rows = doc.get("runs", [])
    if not isinstance(rows, list):
        raise ValueError("inventory.runs must be a list")
    selected = [r for r in rows if r.get("selected") is True]
    if not selected:
        errors.append("No explicitly selected run representations")
    seen, by_subject = {}, {}
    key_fields = ("subject", "session", "task", "acquisition", "direction", "run", "part", "recording")
    for row in selected:
        label = row.get("path", "<unidentified>")
        if not row.get("subject") or not row.get("task") or not row.get("path"):
            errors.append(f"Missing identity: {label}")
        key = tuple(row.get(k) for k in key_fields)
        if key in seen:
            errors.append(f"Multiple selected representations for acquisition: {label}")
        seen[key] = row
        by_subject.setdefault(row.get("subject"), []).append(row)
        if not _positive(row.get("tr")):
            errors.append(f"Missing/nonconstant scalar TR; explicit timing adapter needed: {label}")
        n = row.get("nvols")
        if not isinstance(n, int) or isinstance(n, bool) or n < 1:
            errors.append(f"Missing/invalid nvols: {label}")
        if row.get("confound_rows") is not None and row.get("confound_rows") != n:
            errors.append(f"Confound rows differ from volumes: {label}")
        for field in ("event_file", "confound_file", "mask", "grid_id", "timing_origin"):
            if not row.get(field):
                warnings.append(f"Unverified {field}: {label}")
    shortcut_issues = list(errors)
    for sub, rr in by_subject.items():
        trs = {r.get("tr") for r in rr}
        if len(trs) != 1:
            shortcut_issues.append(f"Mixed TR within subject {sub}")
        runs = [r.get("run") for r in rr]
        if None in runs or "" in runs or len(runs) != len(set(runs)):
            shortcut_issues.append(f"Missing/repeated run labels within subject {sub}")
        for field in ("pipeline", "space", "resolution", "grid_id", "mask"):
            if len({r.get(field) for r in rr}) > 1:
                shortcut_issues.append(f"Mixed {field} within subject {sub}")
    shortcut_issues.extend(warnings)
    return {"selected_count": len(selected), "errors": errors, "warnings": warnings,
            "from_bids_shortcut_blockers": list(dict.fromkeys(shortcut_issues)),
            "from_bids_certified": False,
            "note": "Passing these limited checks never certifies BIDS validity, joins, preprocessing, or importer safety."}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("init", help="Write a new blocked plan (never overwrite)")
    q.add_argument("plan", type=Path); q.add_argument("--analysis-id", required=True)
    q.add_argument("--scope", nargs="+", choices=STAGES, required=True)
    for name in ("digest", "validate", "check", "approve", "seal"):
        q = sub.add_parser(name)
        q.add_argument("plan", type=Path)
        if name in ("validate", "check", "approve"):
            q.add_argument("--stage", choices=STAGES, required=name != "validate")
            q.add_argument("--purpose", choices=("pilot", "full"), default="full")
        if name == "approve":
            q.add_argument("--digest", required=True)
            q.add_argument("--confirmed-by-user", action="store_true")
            q.add_argument("--evidence", required=True)
        if name == "seal":
            q.add_argument("--file", action="append", required=True, metavar="LABEL=PATH")
    q = sub.add_parser("audit-inventory"); q.add_argument("inventory", type=Path)
    q = sub.add_parser("prefs"); ps = q.add_subparsers(dest="op", required=True)
    for name in ("list", "set", "remove"):
        z = ps.add_parser(name); z.add_argument("--file", type=Path, required=True)
        if name != "list":
            z.add_argument("--key", required=True); z.add_argument("--when-json", default="{}")
            z.add_argument("--confirmed-by-user", action="store_true"); z.add_argument("--evidence", required=True)
        if name == "set": z.add_argument("--value-json", required=True)
    z = ps.add_parser("resolve")
    z.add_argument("--user", type=Path); z.add_argument("--project", type=Path)
    z.add_argument("--current", type=Path); z.add_argument("--locked", type=Path)
    z.add_argument("--context-json", required=True)
    return p


def main(argv: list[str] | None = None) -> int:
    a = parser().parse_args(argv)
    try:
        code = 0
        if a.cmd == "init":
            with locked(a.plan):
                if a.plan.exists(): raise ValueError("Refusing to overwrite an existing plan")
                atomic_write(a.plan, new_plan(a.analysis_id, a.scope))
            out = {"created": str(a.plan), "status": "blocked_pending_decisions_and_checks"}
        elif a.cmd in ("seal", "approve"):
            with locked(a.plan):
                plan = load(a.plan)
                if a.cmd == "seal":
                    for arg in a.file:
                        k, sep, path = arg.partition("=")
                        if not sep or not KEY.fullmatch(k): raise ValueError("Expected LABEL=PATH")
                        f = Path(path).expanduser().resolve(strict=True)
                        if f == a.plan.resolve(): raise ValueError("Do not fingerprint the plan inside itself")
                        plan.setdefault("fingerprints", {})[k] = {"path": str(f), "sha256": file_sha(f)}
                    plan["approval"] = {}
                else:
                    plan = authorize(plan, a.stage, a.purpose, a.digest, a.confirmed_by_user, a.evidence)
                atomic_write(a.plan, plan)
            out = {"digest": plan_digest(plan), "approval": plan.get("approval", {})}
        elif a.cmd in ("digest", "validate", "check"):
            plan = load(a.plan)
            errors = [] if a.cmd == "digest" else (
                approval_errors(plan, a.stage, a.purpose) if a.cmd == "check"
                else plan_errors(plan, a.stage, a.purpose))
            out = {"digest": plan_digest(plan), "errors": errors, "ok": not errors}
            code = 2 if errors else 0
        elif a.cmd == "audit-inventory":
            out = audit_inventory(load(a.inventory)); code = 2 if out["errors"] else 0
        elif a.cmd == "prefs":
            if a.op == "resolve":
                read_pref = lambda p: load(p) if p and p.exists() else empty_preferences()
                out = resolve_preferences(read_pref(a.user), read_pref(a.project), json.loads(a.context_json),
                                          load(a.current) if a.current else {}, load(a.locked) if a.locked else {})
                code = 2 if out["conflicts"] else 0
            elif a.op == "list":
                out = load(a.file) if a.file.exists() else empty_preferences(); validate_preferences(out)
            else:
                with locked(a.file):
                    doc = load(a.file) if a.file.exists() else empty_preferences()
                    out = mutate_preference(doc, a.key, json.loads(a.when_json),
                                            json.loads(a.value_json) if a.op == "set" else None,
                                            a.op == "remove", a.confirmed_by_user, a.evidence)
                    atomic_write(a.file, out)
        print(json.dumps(out, indent=2, ensure_ascii=False, allow_nan=False))
        return code
    except (ValueError, TypeError, KeyError, OSError) as e:
        print(json.dumps({"ok": False, "error": str(e)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
