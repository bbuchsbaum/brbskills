#!/usr/bin/env python3
"""Local, offline COBIDAS reporting helper. Python 3.10+, standard library only.

This validates evidence structure and local source identity, not scientific
validity, semantic entailment, remote objects, or the entire official checklist.
Never executes evidence content or an analysis command. See references/helper.md.
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
from datetime import datetime, timezone
from typing import Any
import uuid

VERSION = "0.1.0"
SKILL = Path(__file__).resolve().parents[1]
MAX_EVIDENCE_BYTES = 64 * 1024 * 1024


class RecordError(ValueError):
    """Invalid input or evidence; callers should not silently recover by guessing."""


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def load(path: Path) -> Any:
    try:
        def reject_constant(s: str) -> None:
            raise RecordError(f"Non-finite JSON number: {s}")
        def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
            obj: dict[str, Any] = {}
            for k, v in pairs:
                if k in obj:
                    raise RecordError(f"Duplicate JSON key: {k}")
                obj[k] = v
            return obj
        return json.loads(path.read_text(encoding="utf-8"),
                          parse_constant=reject_constant, object_pairs_hook=no_duplicates)
    except (OSError, ValueError) as exc:
        raise RecordError(f"Cannot read {path}: {exc}") from exc


def write_text(path: Path, data: str, *, exclusive: bool = False) -> None:
    """Expose a complete UTF-8 file atomically; exclusive mode refuses ID reuse."""
    path.parent.mkdir(parents=True, exist_ok=True)
    # os.open applies the process umask (mkstemp would force 0600 on shared storage).
    tmp = str(path.parent / f".writing-{uuid.uuid4().hex}")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if exclusive:
            try:
                os.link(tmp, path)  # Same filesystem, atomic no-overwrite publication.
            except FileExistsError as exc:
                raise RecordError(f"Immutable record already exists: {path}") from exc
            except OSError as exc:
                raise RecordError(f"Atomic hard-link creation unsupported at {path}: {exc}") from exc
        else:
            os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def write(path: Path, value: Any, *, exclusive: bool = False) -> None:
    write_text(path, json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
               exclusive=exclusive)


def validate(value: Any, schema: dict, root: dict | None = None, where: str = "$") -> None:
    """Enforce the JSON Schema subset used by the bundled, pinned schemas.

    Not a general-purpose JSON Schema implementation. External jsonschema is
    used separately in tests; it is not a runtime dependency.
    """
    root = schema if root is None else root
    if "$ref" in schema:
        ref = schema["$ref"]
        if not ref.startswith("#/"):
            raise RecordError("Only local schema references are supported")
        target = root
        for part in ref[2:].split("/"):
            target = target[part.replace("~1", "/").replace("~0", "~")]
        validate(value, target, root, where)
        return
    def matches(part: dict) -> bool:
        try:
            validate(value, part, root, where)
            return True
        except RecordError:
            return False
    if "oneOf" in schema and sum(matches(s) for s in schema["oneOf"]) != 1:
        raise RecordError(f"{where}: does not match exactly one permitted record shape")
    for part in schema.get("allOf", []):
        validate(value, part, root, where)
    if "not" in schema and matches(schema["not"]):
        raise RecordError(f"{where}: prohibited value or property combination")
    if "if" in schema:
        branch = "then" if matches(schema["if"]) else "else"
        if branch in schema:
            validate(value, schema[branch], root, where)
    if "const" in schema and canonical(value) != canonical(schema["const"]):
        raise RecordError(f"{where}: expected {schema['const']!r}")
    if "enum" in schema and canonical(value) not in [canonical(v) for v in schema["enum"]]:
        raise RecordError(f"{where}: value is outside the permitted enumeration")
    kind = schema.get("type")
    checks = {"object": isinstance(value, dict), "array": isinstance(value, list),
              "string": isinstance(value, str), "null": value is None,
              "boolean": isinstance(value, bool),
              "integer": isinstance(value, int) and not isinstance(value, bool),
              "number": isinstance(value, (int, float)) and not isinstance(value, bool)}
    if kind and not checks.get(kind, False):
        raise RecordError(f"{where}: expected {kind}")
    if isinstance(value, dict):
        for name in schema.get("required", []):
            if name not in value:
                raise RecordError(f"{where}: missing {name}")
        if len(value) < schema.get("minProperties", 0):
            raise RecordError(f"{where}: empty object is not permitted")
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False and set(value) - set(props):
            raise RecordError(f"{where}: unexpected fields {sorted(set(value) - set(props))}")
        for name in value.keys() & props.keys():
            validate(value[name], props[name], root, where + "." + name)
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            raise RecordError(f"{where}: too few items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise RecordError(f"{where}: too many items")
        if schema.get("uniqueItems") and len({canonical(v) for v in value}) != len(value):
            raise RecordError(f"{where}: duplicate items")
        if "items" in schema:
            for i, item in enumerate(value):
                validate(item, schema["items"], root, f"{where}[{i}]")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            raise RecordError(f"{where}: empty string")
        # JSON Schema (ECMA-262) "$" does not match before a trailing newline; Python's does.
        pattern = re.sub(r"(?<!\\)\$$", r"\\Z", schema.get("pattern", ""))
        if pattern and not re.search(pattern, value):
            raise RecordError(f"{where}: invalid string format")
        if schema.get("format") == "date-time":
            try:
                dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    raise ValueError("timezone required")
            except ValueError as exc:
                raise RecordError(f"{where}: require an ISO 8601 timestamp with timezone") from exc
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise RecordError(f"{where}: below minimum")


def validate_event(event: Any, schema: dict) -> None:
    """Validate against the branch selected by `kind`, so errors name the bad field.

    Branches are mutually exclusive through their `kind` constants, so this is
    equivalent to the schema's top-level oneOf.
    """
    kinds = [s["$ref"].rsplit("/", 1)[1] for s in schema["oneOf"]]
    kind = event.get("kind") if isinstance(event, dict) else None
    if not isinstance(kind, str) or kind not in kinds:
        raise RecordError(f"$.kind: expected one of {kinds}")
    validate(event, schema["$defs"][kind], schema)


def profile_closure(profiles: list[str], catalog: dict) -> set[str]:
    active = set(profiles) | {"core"}
    unknown = active - set(catalog["profiles"])
    if unknown:
        raise RecordError(f"Unknown profiles: {sorted(unknown)}")
    while True:
        expanded = active | {v for k in active for v in catalog.get("implications", {}).get(k, [])}
        if expanded == active:
            return active
        active = expanded


def context(root: Path) -> tuple[dict, dict, Path, dict[str, dict]]:
    config = load(root / "study.json")
    validate(config, load(SKILL / "schemas/study.schema.json"))
    catalog = load(root / "catalog.json")
    if catalog.get("version") != VERSION:
        raise RecordError("Unsupported catalogue version; migrate explicitly before using this helper")
    fields = catalog.get("fields", [])
    if not fields or len({f["key"] for f in fields}) != len(fields):
        raise RecordError("Empty catalogue or duplicate field keys")
    scopes = {s["id"]: s for s in config["scopes"]}
    if len(scopes) != len(config["scopes"]) or sum(s["kind"] == "study" for s in scopes.values()) != 1:
        raise RecordError("Require unique scope IDs and exactly one study scope")
    for scope in scopes.values():
        profile_closure(scope["profiles"], catalog)
    workspace = (root / config["workspace"]).resolve()
    if not workspace.is_dir():
        raise RecordError(f"Workspace does not exist: {workspace}")
    return config, catalog, workspace, scopes


def local_path(workspace: Path, name: str) -> Path:
    if not isinstance(name, str):
        raise RecordError("Evidence paths must be strings")
    candidate = Path(name)
    if candidate.is_absolute() or not name.strip() or "\0" in name:
        raise RecordError("Evidence paths must be nonempty project-relative paths")
    resolved = (workspace / candidate).resolve()
    if not resolved.is_relative_to(workspace):
        raise RecordError(f"Evidence path escapes the workspace: {name}")
    return resolved


def file_hash(path: Path, label: str | None = None) -> str:
    """SHA-256 of a regular file; `label` keeps absolute paths out of messages."""
    label = label or str(path)
    if not path.is_file():
        raise RecordError(f"Evidence is not a regular file: {label}")
    if path.stat().st_size > MAX_EVIDENCE_BYTES:
        raise RecordError(f"Evidence exceeds {MAX_EVIDENCE_BYTES} bytes; use a verified small manifest")
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def evidence_lists(event: dict) -> list[list[dict]]:
    if event["kind"] == "activity":
        return [event["inputs"], event["outputs"], event["validation"]["evidence"]]
    return [event.get("evidence", [])]


def initialize(project: Path, profiles: list[str]) -> Path:
    project = project.resolve()
    if not project.is_dir():
        raise RecordError("Project directory must already exist")
    catalog = load(SKILL / "assets/fields.json")
    profiles = list(dict.fromkeys(profiles))  # study.schema requires unique profiles.
    profile_closure(profiles, catalog)
    root = project / "reporting" / "cobidas"
    if root.exists():
        raise RecordError(f"Refusing to overwrite an existing reporting root: {root}")
    root.mkdir(parents=True)
    (root / "events").mkdir()
    config = {"schema_version": VERSION, "workspace": "../..", "project_id": project.name,
              "report_title": "MRI methods", "scopes": [
                  {"id": "study", "kind": "study", "label": "Study", "profiles": profiles},
                  {"id": "acq-main", "kind": "acquisition", "label": "Edit acquisition membership", "profiles": profiles},
                  {"id": "analysis-main", "kind": "analysis", "label": "Edit analysis revision and membership", "profiles": profiles}]}
    write(root / "study.json", config, exclusive=True)
    write(root / "catalog.json", catalog, exclusive=True)
    (root / "official-checklist.tsv").write_bytes((SKILL / "assets/official-checklist-template.tsv").read_bytes())
    return root


def import_records(root: Path, data: Any) -> list[str]:
    _, catalog, workspace, scopes = context(root)
    items = data if isinstance(data, list) else [data]
    schema = load(SKILL / "schemas/event.schema.json")
    field_map = {f["key"]: f for f in catalog["fields"]}
    prepared = []
    for original in items:
        if not isinstance(original, dict):
            raise RecordError("Each input record must be an object")
        event = copy.deepcopy(original)
        event.setdefault("id", "event-" + uuid.uuid4().hex)
        event.setdefault("recorded_at", now())
        # Shape defaults only; never guess scientific values or a successful status.
        if event.get("kind") == "fact":
            event.setdefault("activity_ids", [])
            event.setdefault("supersedes", [])
            event.setdefault("evidence", [])
        if event.get("kind") == "activity":
            event.setdefault("depends_on", [])
        try:
            for items_ in evidence_lists(event):
                for evidence in items_:
                    if "path" in evidence:
                        actual = file_hash(local_path(workspace, evidence["path"]))
                        if evidence.get("sha256", actual) != actual:
                            raise RecordError(f"Supplied evidence hash does not match: {evidence['path']}")
                        evidence["sha256"] = actual
        except (KeyError, TypeError, AttributeError) as exc:
            raise RecordError(f"Malformed record {event.get('id')!r}: {exc!r}") from exc
        validate_event(event, schema)
        if event["scope"] not in scopes:
            raise RecordError(f"Unknown scope: {event['scope']}")
        if event["kind"] == "fact":
            field = field_map.get(event["key"])
            if not field:
                raise RecordError(f"Unknown field key: {event['key']}")
            if scopes[event["scope"]]["kind"] not in field["scope_kinds"]:
                raise RecordError(f"Field does not belong to scope kind: {event['key']}")
        prepared.append(event)
    if len({e["id"] for e in prepared}) != len(prepared):
        raise RecordError("Duplicate event ID in import batch")
    # Preflight; concurrent writers are still protected by atomic exclusive publication.
    for event in prepared:
        if (root / "events" / (event["id"] + ".json")).exists():
            raise RecordError(f"Immutable record ID already exists: {event['id']}")
    for event in prepared:
        write(root / "events" / (event["id"] + ".json"), event, exclusive=True)
    return [e["id"] for e in prepared]


def audit(root: Path, *, emit: bool = True) -> dict:
    config, catalog, workspace, scopes = context(root)
    schema = load(SKILL / "schemas/event.schema.json")
    events: dict[str, dict] = {}
    errors: list[str] = []
    invalid_inputs: list[dict] = []
    for path in sorted((root / "events").glob("*.json")):
        try:
            if path.is_symlink():
                raise RecordError("Event files must not be symlinks")
            event = load(path)
            validate_event(event, schema)
            if path.stem != event["id"] or event["id"] in events:
                raise RecordError("Event filename / ID mismatch or duplicate ID")
            if event["scope"] not in scopes:
                raise RecordError(f"Unknown scope {event['scope']}")
            events[event["id"]] = event
        except (RecordError, KeyError) as exc:
            errors.append(f"{path.name}: {exc}")
            try:
                fingerprint = "invalid" if path.is_symlink() else file_hash(path, path.name)
            except (RecordError, OSError):
                fingerprint = "unhashable"
            invalid_inputs.append({"file": path.name, "sha256": fingerprint})
    fields = {f["key"]: f for f in catalog["fields"]}
    evidence_status: dict[str, list[dict]] = {}
    cache: dict[str, tuple[str, str]] = {}
    for eid, event in events.items():
        checks = []
        for group in evidence_lists(event):
            for ev in group:
                if "uri" in ev:
                    checks.append({"uri": ev["uri"], "version": ev["version"], "status": "unverified_remote"})
                    continue
                name = ev["path"]
                if name not in cache:
                    try:
                        cache[name] = ("read", file_hash(local_path(workspace, name), name))
                    except RecordError as exc:
                        cache[name] = ("unavailable", str(exc))
                    except OSError as exc:  # strerror only: no absolute paths in the digest.
                        cache[name] = ("unavailable", f"{name}: {exc.strerror or type(exc).__name__}")
                state, observed = cache[name]
                status = ("verified" if observed == ev["sha256"] else "stale") if state == "read" else "unavailable"
                checks.append({"path": name, "status": status, "expected_sha256": ev["sha256"],
                               "observed_sha256": observed if state == "read" else None,
                               "detail": "" if state == "read" else observed})
        evidence_status[eid] = checks
    def sources_ok(eid: str) -> bool:
        return all(c["status"] == "verified" for c in evidence_status[eid])
    activity_status: dict[str, dict] = {}
    def own_problem(event: dict) -> str:
        if event["status"] != "succeeded":
            return f"Activity is {event['status']}"
        if event["validation"]["status"] != "passed":
            return "Validation did not pass"
        if not event["inputs"] or not event["outputs"] or not event["validation"]["evidence"]:
            return "Missing input, output or validation evidence"
        if any(not sw["name"].strip() or not sw["version"].strip() for sw in event["software"]):
            return "Empty software identity"
        if not sources_ok(event["id"]):
            return "Activity evidence is stale, unavailable or remotely unverified"
        return ""
    def activity_check(eid: str) -> dict:
        """Memoized depth-first check; iterative so long dependency chains cannot overflow."""
        if eid in activity_status:
            return activity_status[eid]
        if events.get(eid, {}).get("kind") != "activity":
            return {"status": "invalid", "reason": "Missing activity"}
        frames = [[eid, 0]]  # (activity, index of next dependency)
        on_path = {eid}
        def finish(reason: str) -> None:
            node = frames.pop()[0]
            on_path.discard(node)
            activity_status[node] = {"status": "unverified" if reason else "verified", "reason": reason}
        while frames:
            node, i = frames[-1]
            event = events[node]
            if i == 0 and (problem := own_problem(event)):
                finish(problem)
                continue
            if i == len(event["depends_on"]):
                finish("")
                continue
            parent = event["depends_on"][i]
            if parent in activity_status:
                outcome = activity_status[parent]
            elif parent in on_path:
                outcome = {"status": "invalid", "reason": "Dependency cycle"}
            elif events.get(parent, {}).get("kind") != "activity":
                outcome = {"status": "invalid", "reason": "Missing activity"}
            else:
                frames.append([parent, 0])
                on_path.add(parent)
                continue  # Revisit this dependency once the parent is resolved.
            if outcome["status"] != "verified":
                finish(f"Dependency {parent}: {outcome['reason']}")
            else:
                frames[-1][1] += 1
        return activity_status[eid]
    for eid, event in events.items():
        if event["kind"] == "activity":
            activity_check(eid)
    facts = {eid: e for eid, e in events.items() if e["kind"] == "fact"}
    suppressed: set[str] = set()
    invalid_facts: set[str] = set()
    def identity(e: dict) -> tuple[str, str, str]:
        return e["scope"], e["key"], e["phase"]
    # A fact whose supersession history reaches a cycle (including a self-edge) is
    # invalid. Peel facts whose recorded predecessors are all cycle-free; the rest cycle.
    blocking = {eid: {p for p in f["supersedes"] if p in facts} for eid, f in facts.items()}
    successors: dict[str, list[str]] = {}
    for eid, priors in blocking.items():
        for prior in priors:
            successors.setdefault(prior, []).append(eid)
    ready = [eid for eid, priors in blocking.items() if not priors]
    acyclic: set[str] = set()
    while ready:
        eid = ready.pop()
        acyclic.add(eid)
        for later in successors.get(eid, []):
            blocking[later].discard(eid)
            if not blocking[later]:
                ready.append(later)
    for eid, fact in facts.items():
        field = fields.get(fact["key"])
        if not field or scopes[fact["scope"]]["kind"] not in field["scope_kinds"]:
            errors.append(f"{eid}: unknown or wrongly scoped field")
            invalid_facts.add(eid)
        for prior in fact["supersedes"]:
            if prior not in facts or identity(facts[prior]) != identity(fact) or prior == eid:
                errors.append(f"{eid}: invalid supersedes edge to {prior}")
                invalid_facts.add(eid)
        if eid not in acyclic:
            errors.append(f"{eid}: supersession cycle")
            invalid_facts.add(eid)
    for eid, fact in facts.items():
        if eid not in invalid_facts:
            suppressed.update(fact["supersedes"])
    heads: dict[tuple[str, str, str], list[str]] = {}
    for eid, fact in facts.items():
        if eid not in suppressed:
            heads.setdefault(identity(fact), []).append(eid)
    eligible: dict[str, dict] = {}
    coverage = []
    for scope in config["scopes"]:
        active = profile_closure(scope["profiles"], catalog)
        for field in catalog["fields"]:
            if scope["kind"] not in field["scope_kinds"] or not active.intersection(field["profiles"]):
                continue
            ids = sorted(heads.get((scope["id"], field["key"], "actual"), []))
            row = {"scope": scope["id"], "key": field["key"], "section": field["section"],
                   "required_local": field["required"], "status": "missing", "fact_ids": ids,
                   "reason": "No current actual fact", "prompt": field["prompt"]}
            if len(ids) > 1:
                row.update(status="conflict", reason="Multiple current actual facts; resolve with explicit supersedes")
            elif len(ids) == 1:
                eid = ids[0]
                fact = facts[eid]
                status, reason = "known", ""
                if eid in invalid_facts:
                    status, reason = "invalid", "Invalid field or supersession history"
                elif not sources_ok(eid):
                    status, reason = "stale_or_unverified", "Inspect evidence checks for changed, missing or remote sources"
                elif fact["status"] != "known":
                    status, reason = fact["status"], fact["reason"]
                elif fact["basis"] == "inferred":
                    status, reason = "inferred_only", "Inference is not direct methods evidence"
                elif field["required_value_keys"] and (
                    not isinstance(fact["value"], dict) or
                    any(k not in fact["value"] for k in field["required_value_keys"])):
                    status, reason = "invalid", "Missing required structured value keys"
                elif fact["key"] == "scope.members":
                    v = fact["value"]
                    if (not isinstance(v["n_units"], int) or isinstance(v["n_units"], bool) or v["n_units"] < 0
                        or not isinstance(v["unit"], str) or not v["unit"].strip()
                        or v["manifest"] not in [ev.get("path") for ev in fact["evidence"]]):
                        status, reason = "invalid", "Membership needs a nonnegative count, unit and cited local manifest"
                if status == "known" and field["requires_execution"]:
                    if not fact["activity_ids"]:
                        status, reason = "execution_unverified", "No producing activity linked"
                    else:
                        for aid in fact["activity_ids"]:
                            outcome = activity_check(aid)
                            if outcome["status"] != "verified":
                                status, reason = "execution_unverified", f"{aid}: {outcome['reason']}"
                                break
                            if events[aid]["scope"] != fact["scope"]:
                                status, reason = "execution_unverified", "Producing activity must have the same explicit analysis scope"
                                break
                if status == "known" and fact.get("missing_details"):
                    status, reason = "known_incomplete", "Missing subdetails: " + "; ".join(fact["missing_details"])
                row.update(status=status, reason=reason)
                if status in ("known", "known_incomplete"):
                    eligible[eid] = fact
            coverage.append(row)
    expected_pairs = {(r["scope"], r["key"]) for r in coverage}
    for eid, fact in facts.items():
        if fact["phase"] == "actual" and eid not in suppressed and (fact["scope"], fact["key"]) not in expected_pairs:
            errors.append(f"{eid}: actual fact is outside the scope's active profiles; enable its module explicitly")
    for kind in ("acquisition", "analysis"):
        if not any(s["kind"] == kind for s in scopes.values()):
            errors.append(f"No {kind} scope declared; MRI reporting scope is incomplete")
    gaps = [r for r in coverage if is_gap(r)]
    snapshot = {"helper_version": VERSION, "checker_identity": {
                    "script_sha256": file_hash(Path(__file__).resolve()),
                    "schemas": {name: file_hash(SKILL / "schemas" / (name + ".schema.json"))
                                for name in ("event", "study", "draft")}},
                "config": config, "catalog": catalog,
                "events": events, "invalid_inputs": invalid_inputs, "evidence_status": evidence_status}
    result = {"format_version": VERSION, "generated_at": now(), "audit_digest": digest(snapshot),
              "authority": catalog["authority"], "limitations": [
                  "Local catalogue coverage is not an exhaustive official COBIDAS audit.",
                  "Structural integrity and byte identity do not prove truth, completeness or semantic entailment.",
                  "Membership counts, source locators and scientific values require independent verification.",
                  "Known-incomplete facts support only their populated values; declared missing subdetails remain audit gaps.",
                  "Only directly referenced local evidence bytes are checked; remote objects and manifest members are not fetched.",
                  "Snapshot consistency requires quiescent sources; no concurrent file-mutation or manuscript-write guarantee."],
              "errors": sorted(set(errors)), "coverage": coverage,
              "eligible_facts": eligible, "evidence_checks": evidence_status,
              "activities": activity_status, "summary": {
                  "expected_local_fields": len(coverage), "eligible_known_fields": len(eligible),
                  "complete_known_fields": sum(r["status"] == "known" for r in coverage),
                  "known_incomplete_fields": sum(r["status"] == "known_incomplete" for r in coverage),
                  "not_applicable_fields": sum(r["status"] == "not_applicable" for r in coverage),
                  "gap_fields": len(gaps), "integrity_errors": len(set(errors))}}
    if emit:
        emit_audit(root, result)
    return result


def is_gap(row: dict) -> bool:
    return row["required_local"] and row["status"] not in ("known", "not_applicable")


def emit_audit(root: Path, result: dict) -> None:
    coverage = result["coverage"]
    gaps = [r for r in coverage if is_gap(r)]
    errors = result["errors"]
    write(root / "audit.json", result)
    header = ("# Reporting gaps — local audit, not COBIDAS certification\n\n"
              f"Audit digest: `{result['audit_digest']}`\n\n"
              "Known values still require scientific and source-level review. N/A reasons are not adjudicated by this helper.\n\n")
    detail = "\n".join(f"- **{r['scope']} / {r['key']}** — {r['status']}: {r['reason']}. {r['prompt']}" for r in gaps)
    if errors:
        detail += "\n\n## Integrity errors\n\n" + "\n".join("- " + e for e in sorted(set(errors)))
    write_text(root / "gaps.md", header + (detail or "No gaps in the local catalogue. Perform the separate official row-level audit.\n") + "\n")
    tsv(root / "coverage.tsv", ["scope", "key", "section", "required_local", "status", "fact_ids", "reason", "prompt"], coverage)


def tsv(path: Path, names: list[str], rows: list[dict]) -> None:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=names, delimiter="\t", lineterminator="\n", extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v for k, v in row.items()})
    write_text(path, stream.getvalue())


def build(root: Path, draft: dict) -> dict:
    validate(draft, load(SKILL / "schemas/draft.schema.json"))
    result = audit(root, emit=False)
    if draft["audit_digest"] != result["audit_digest"]:
        raise RecordError("Stale draft: audit digest changed; reconcile evidence and regenerate the claim bindings")
    if result["errors"]:
        raise RecordError("Integrity errors block a manuscript build; inspect audit output")
    ids = [p["id"] for p in draft["paragraphs"]]
    if len(set(ids)) != len(ids):
        raise RecordError("Paragraph IDs must be unique")
    eligible = result["eligible_facts"]
    for paragraph in draft["paragraphs"]:
        bad = set(paragraph["claim_ids"]) - set(eligible)
        if bad:
            raise RecordError(f"{paragraph['id']}: unsupported, noncurrent or nonactual claim IDs: {sorted(bad)}")
    warning = ("> DRAFT — investigator review required. This is evidence-bound prose, not a certified report.\n"
               f"> {result['summary']['gap_fields']} local reporting fields remain unresolved. "
               "See gaps.md and the separate official checklist.\n"
               "> The helper has not verified that every sentence is entailed by its cited facts.\n\n"
               f"Audit digest: `{result['audit_digest']}`\n\n")
    for destination, filename, title in [("methods", "methods.md", "Methods"),
                                         ("supplement", "supplementary_methods.md", "Supplementary methods")]:
        parts = ["# " + title + "\n\n" + warning]
        last_section = None
        for p in draft["paragraphs"]:
            if p["destination"] != destination:
                continue
            if p["section"] != last_section:
                parts.append("## " + p["section"] + "\n\n")
                last_section = p["section"]
            parts.append(p["text"] + "\n\n<!-- paragraph: " + p["id"] + "; facts: " + ", ".join(p["claim_ids"]) + " -->\n\n")
        write_text(root / filename, "".join(parts))
    rows = []
    for p in draft["paragraphs"]:
        for eid in p["claim_ids"]:
            fact = eligible[eid]
            for ev in fact["evidence"]:
                rows.append({"paragraph_id": p["id"], "destination": p["destination"], "section": p["section"],
                             "fact_id": eid, "scope": fact["scope"], "key": fact["key"], "basis": fact["basis"],
                             "source": ev.get("path", ev.get("uri")), "locator": ev["locator"],
                             "sha256_or_version": ev.get("sha256", ev.get("version")), "activity_ids": fact["activity_ids"]})
    tsv(root / "claim-evidence.tsv", ["paragraph_id", "destination", "section", "fact_id", "scope", "key", "basis", "source", "locator", "sha256_or_version", "activity_ids"], rows)
    used = {eid for p in draft["paragraphs"] for eid in p["claim_ids"]}
    unused = sorted(set(eligible) - used)
    write_text(root / "unreported.md", "# Verified local facts not cited by the current draft\n\n" +
        ("\n".join(f"- `{eid}`: {eligible[eid]['scope']} / {eligible[eid]['key']}" for eid in unused) or "None.") +
        "\n\nThis detects uncited facts, not omitted subdetails within a cited structured fact.\n")
    write(root / "draft.snapshot.json", draft)
    # Emit reports from the same snapshot; do not silently take a later audit.
    emit_audit(root, result)
    return {"audit_digest": result["audit_digest"], "paragraphs": len(draft["paragraphs"]),
            "gap_fields": result["summary"]["gap_fields"], "unused_eligible_facts": len(unused),
            "status": "draft_requires_review"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=VERSION)
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="Initialize a new project reporting directory")
    init.add_argument("--project", type=Path, required=True)
    init.add_argument("--profile", action="append", default=[])
    for name in ("record", "audit", "build"):
        sub = commands.add_parser(name)
        sub.add_argument("--root", type=Path, required=True)
        if name == "record":
            sub.add_argument("--file", type=Path, required=True)
        if name == "audit":
            sub.add_argument("--strict", action="store_true", help="Exit 1 for local gaps or integrity errors")
        if name == "build":
            sub.add_argument("--draft", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            result: Any = {"root": str(initialize(args.project, args.profile))}
        elif args.command == "record":
            result = {"recorded_ids": import_records(args.root.resolve(), load(args.file))}
        elif args.command == "audit":
            report = audit(args.root.resolve())
            result = {"audit_digest": report["audit_digest"], **report["summary"]}
            print(json.dumps(result, indent=2))
            return 1 if args.strict and (report["summary"]["gap_fields"] or report["errors"]) else 0
        else:
            result = build(args.root.resolve(), load(args.draft))
        print(json.dumps(result, indent=2))
        return 0
    except (RecordError, OSError, KeyError, TypeError) as exc:
        print(f"cobidas: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
