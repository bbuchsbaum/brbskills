#!/usr/bin/env python3
"""Fingerprint and cross-check local fMRIPrep records; never authorize or submit.

Checks only declared record consistency and referenced file bytes. Scientific
validity, authentic consent, scheduler ownership and compute readiness need
independent evidence. See references/records.md for the v1 encoding contract.
"""
from __future__ import annotations

import argparse
import errno
import hashlib
import json
import math
from pathlib import Path
import sys

SCOPES = {'prepare', 'probe', 'pilot', 'cohort', 'publish', 'cleanup'}
# Submission states: before the submit call (no job ID may exist yet), after it.
PRE_SUBMIT_STATES = {'prepared', 'not_submitted'}
POST_SUBMIT_STATES = {'submitted', 'terminal'}
SUBMISSION_STATES = PRE_SUBMIT_STATES | POST_SUBMIT_STATES | {'unknown'}
MAX_RECORD_BYTES = 16 * 1024 * 1024


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, f'duplicate JSON key: {key!r}')
        value[key] = item
    return value


def load(path):
    def invalid(value):
        raise ValueError(f'non-finite JSON number: {value}')
    def finite_float(value):
        number = float(value)
        require(math.isfinite(number), 'non-finite JSON number')
        return number
    # Bounded read: st_size is 0 for FIFOs/devices and a file may grow after stat.
    with Path(path).open('rb') as stream:
        data = stream.read(MAX_RECORD_BYTES + 1)
    require(len(data) <= MAX_RECORD_BYTES, f'record exceeds {MAX_RECORD_BYTES} bytes: {path}')
    # utf-8-sig tolerates a leading BOM; any other non-UTF-8 byte is rejected.
    return json.loads(data.decode('utf-8-sig'),
                      object_pairs_hook=unique_object, parse_constant=invalid, parse_float=finite_float)


def fingerprint(record):
    require(isinstance(record, dict), 'record must be an object')
    require(type(record.get('schema_version')) is int and record['schema_version'] == 1,
            'schema_version must be 1')
    require(record.get('kind') in {'plan', 'execution'}, 'kind must be plan or execution')
    require(isinstance(record.get('content'), dict) and record['content'], 'content must be nonempty')
    payload = {key: record[key] for key in ('schema_version', 'kind', 'content')}
    encoded = json.dumps(payload, sort_keys=True, separators=(',', ':'),
                         ensure_ascii=False, allow_nan=False).encode('utf-8')
    return 'sha256:' + hashlib.sha256(encoded).hexdigest()


def file_identity(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return 'sha256:' + digest.hexdigest()


def verify_files(value, root):
    if isinstance(value, dict):
        if '$file' in value:
            rel = value['$file']
            require(isinstance(rel, str) and rel, '$file must be a nonempty relative path')
            path = Path(rel)
            require(not path.is_absolute() and '..' not in path.parts, '$file escapes artifact root')
            try:
                target = (root / path).resolve(strict=True)
            except RuntimeError:  # symlink loop on Python < 3.13
                raise ValueError(f'$file symlink loop: {rel}') from None
            except OSError as exc:
                if exc.errno == errno.ELOOP:  # symlink loop on Python >= 3.13
                    raise ValueError(f'$file symlink loop: {rel}') from None
                raise
            require(target.is_relative_to(root) and target.is_file(), '$file escapes root or is not a file')
            require(value.get('sha256') == file_identity(target), f'artifact hash mismatch: {rel}')
        for item in value.values():
            verify_files(item, root)
    elif isinstance(value, list):
        for item in value:
            verify_files(item, root)


def resolved(value, literal_strings=False):
    # False, zero, and intentionally empty lists/maps can be meaningful. Inside
    # payload argv/env, an empty string is a literal value, so only null fails.
    if value is None or (not literal_strings and isinstance(value, str) and not value.strip()):
        return False
    if isinstance(value, dict):
        return all(resolved(v, literal_strings) for v in value.values())
    if isinstance(value, list):
        return all(resolved(v, literal_strings) for v in value)
    return True


def content_resolved(kind, content):
    if kind != 'execution' or not isinstance(content.get('payload'), dict):
        return resolved(content)
    payload = content['payload']
    literal = {k: v for k, v in payload.items() if k in ('argv', 'env')}
    rest = {k: v for k, v in content.items() if k != 'payload'}
    rest['payload'] = {k: v for k, v in payload.items() if k not in literal}
    return resolved(rest) and resolved(literal, literal_strings=True)


def file_ref(value):
    """Normalized binding of a {"$file", "sha256"} reference; annotations ignored."""
    if not isinstance(value, dict) or not isinstance(value.get('$file'), str):
        return None
    return (Path(value['$file']).as_posix(), value.get('sha256'))


def exact_token(value):
    """Nonempty string with no surrounding whitespace, so identity keys compare exactly."""
    return isinstance(value, str) and bool(value) and value == value.strip()


def check(plan, execution, receipts, root, scope):
    root = Path(root).resolve(strict=True)
    require(root.is_dir(), 'artifact root must be a directory')
    require(scope in SCOPES, 'unknown scope')
    require(isinstance(plan, dict) and isinstance(execution, dict), 'records must be JSON objects')
    require(isinstance(receipts, list), 'receipts must be a list')
    for record, kind, fields in (
        (plan, 'plan', ('inputs', 'software', 'recipe', 'required_outputs')),
        (execution, 'execution', ('scientific_id', 'target', 'provisioning', 'runtime',
                                 'scheduler', 'resources', 'paths', 'payload', 'scripts', 'assets', 'network', 'storage')),
    ):
        require(record.get('kind') == kind, f'expected {kind} record')
        require(record.get('example_only') is False, 'examples are not resolved records')
        require(record.get('content_id') == fingerprint(record), f'{kind} content_id mismatch')
        content = record['content']
        require(all(key in content for key in fields), f'{kind} missing required content fields')
        require(all(bool(content[key]) for key in fields), f'{kind} has empty required content fields')
        require(content_resolved(kind, content), f'{kind} has unresolved null/empty values')
        verify_files(content, root)
    scientific_id = plan['content_id']
    execution_id = execution['content_id']
    require(execution['content']['scientific_id'] == scientific_id, 'execution references another plan')
    authorizations = plan.get('authorizations', [])
    require(isinstance(authorizations, list), 'authorizations must be a list')
    applicable = [a for a in authorizations if isinstance(a, dict)
                  and a.get('scientific_id') == scientific_id
                  and isinstance(a.get('scopes'), list) and scope in a['scopes']
                  and isinstance(a.get('source'), str) and a['source'].strip()
                  and isinstance(a.get('limits'), dict) and a['limits']
                  and isinstance(a.get('recorded_at'), str) and a['recorded_at'].strip()]
    require(applicable, 'no matching recorded authorization with source and limits')
    argv = execution['content']['payload'].get('argv')
    env = execution['content']['payload'].get('env')
    require(isinstance(argv, list) and argv and all(isinstance(a, str) and '\0' not in a for a in argv),
            'payload argv must be a nonempty string array without NUL')
    require(isinstance(env, dict) and all(isinstance(k, str) and k and '=' not in k and '\0' not in k
                                         and isinstance(v, str) and '\0' not in v for k, v in env.items()),
            'payload env must be a string map without NUL')
    scripts = execution['content']['scripts']
    require(isinstance(scripts, list) and scripts and all(isinstance(s, dict) and '$file' in s for s in scripts),
            'scripts must identify rendered payload/job artifacts')
    bound_scripts = {file_ref(s) for s in scripts}
    seen = set()
    tokens = set()
    jobs = set()
    for receipt in receipts:
        require(isinstance(receipt, dict), 'receipt must be a JSON object')
        require(type(receipt.get('schema_version')) is int and receipt.get('schema_version') == 1 and receipt.get('kind') == 'receipt', 'invalid receipt envelope')
        require(receipt.get('example_only') is False, 'example receipt is not an attempt')
        require(receipt.get('scientific_id') == scientific_id and receipt.get('execution_id') == execution_id,
                'receipt identity mismatch')
        attempt = receipt.get('attempt_id')
        require(isinstance(attempt, str) and attempt.strip(), 'missing attempt_id')
        require(exact_token(attempt), 'attempt_id must not have surrounding whitespace')
        require(attempt not in seen, 'duplicate attempt_id')
        seen.add(attempt)
        intent = receipt.get('submission', {})
        require(isinstance(intent, dict), 'submission must be an object')
        require(all(isinstance(intent.get(k), str) and intent[k].strip()
                    for k in ('token', 'target', 'owner', 'intent_at')), 'incomplete submission intent')
        require(all(exact_token(intent[k]) for k in ('token', 'target', 'owner')),
                'submission token/target/owner must not have surrounding whitespace')
        token_key = (intent['target'], intent['owner'], intent['token'])
        require(token_key not in tokens, 'duplicate submission token for target and owner')
        tokens.add(token_key)
        state = intent.get('state')
        require(state in SUBMISSION_STATES, 'invalid submission state')
        job_id = intent.get('job_id')
        if state in POST_SUBMIT_STATES:
            require(isinstance(job_id, str) and job_id.strip(), 'missing job_id')
        elif state in PRE_SUBMIT_STATES:
            require(job_id is None, f'job_id is inconsistent with submission state {state}')
        else:  # unknown: a job ID may or may not have been captured
            require(job_id is None or (isinstance(job_id, str) and job_id.strip()), 'invalid job_id')
        require(job_id is None or exact_token(job_id), 'job_id must not have surrounding whitespace')
        if job_id is not None:
            job_key = (intent['target'], job_id)
            require(job_key not in jobs, 'duplicate job_id for target among supplied receipts')
            jobs.add(job_key)
        process = receipt.get('process')
        require(isinstance(process, dict) and isinstance(process.get('status'), str)
                and process['status'].strip(), 'receipt missing process status')
        for field in ('outputs', 'qc', 'publication'):
            value = receipt.get(field)
            require(value is None or (isinstance(value, dict) and isinstance(value.get('status'), str)
                                      and value['status'].strip()),
                    f'receipt {field} must be absent/null or carry a status')
        require(file_ref(receipt.get('script')) is not None, 'missing script reference')
        require(file_ref(receipt['script']) in bound_scripts, 'receipt script is not bound to execution content')
        verify_files(receipt, root)
    return {'record_consistency': 'passed', 'execution_readiness': 'not_assessed',
            'authorization_authenticity': 'not_assessed', 'receipts_checked': len(receipts)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    one = sub.add_parser('fingerprint', help='Print identity; does not modify the record')
    one.add_argument('record', type=Path)
    two = sub.add_parser('check', help='Check declared bindings and local artifact hashes; not a launch gate')
    two.add_argument('plan', type=Path)
    two.add_argument('execution', type=Path)
    two.add_argument('--receipt', action='append', default=[], type=Path)
    two.add_argument('--artifact-root', required=True, type=Path)
    two.add_argument('--scope', required=True, choices=sorted(SCOPES))
    args = parser.parse_args(argv)
    try:
        if args.command == 'fingerprint':
            print(fingerprint(load(args.record)))
        else:
            print(json.dumps(check(load(args.plan), load(args.execution),
                                   [load(p) for p in args.receipt], args.artifact_root, args.scope), indent=2))
    # RuntimeError covers RecursionError (deeply nested JSON) and symlink loops.
    except (ValueError, OSError, TypeError, AttributeError, KeyError, UnicodeError, RuntimeError) as exc:
        print(f'records: {exc}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
