"""Synthetic record-integrity evidence, not permission or execution qualification."""
import contextlib
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/records.py'
ASSETS = Path(__file__).resolve().parents[1] / 'assets'
spec = importlib.util.spec_from_file_location('records', SCRIPT)
records = importlib.util.module_from_spec(spec)
spec.loader.exec_module(records)


class RecordTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='fmriprep records ')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        artifact = self.root / 'manifest.json'
        artifact.write_text('{"synthetic":true}\n')
        self.ref = {'$file': artifact.name, 'sha256': records.file_identity(artifact)}
        self.plan = {'schema_version': 1, 'kind': 'plan', 'example_only': False,
                     'content': {'inputs': {'snapshot': 'synthetic-v1', 'manifest': self.ref},
                                 'software': {'version': 'fixture', 'identity': 'fake-image-v1'},
                                 'recipe': {'sdc': 'acquired', 'template': 'T1w'},
                                 'required_outputs': self.ref}}
        self.plan['content_id'] = records.fingerprint(self.plan)
        self.plan['authorizations'] = [{'scientific_id': self.plan['content_id'], 'scopes': ['pilot'],
                                       'source': 'synthetic test authorization, not real consent',
                                       'limits': {'subjects': ['01']}, 'recorded_at': '2026-09-28T00:00:00Z'}]
        self.execution = {'schema_version': 1, 'kind': 'execution', 'example_only': False, 'content': {
            'scientific_id': self.plan['content_id'], 'target': {'site': 'synthetic'},
            'provisioning': {'kind': 'fixture'}, 'runtime': {'kind': 'fake'},
            'scheduler': {'kind': 'none'}, 'resources': {'cpus': 8},
            'paths': [{'role': 'bids', 'application': '/data', 'access': 'ro'}],
            'payload': {'argv': ['fake', '/data', '/out', 'participant'], 'env': {}, 'cwd': '/fixture'},
            'scripts': [self.ref], 'assets': {'manifest': self.ref}, 'network': {'allowed': False},
            'storage': {'retained': True}}}
        self.execution['content_id'] = records.fingerprint(self.execution)
        self.receipt = {'schema_version': 1, 'kind': 'receipt', 'example_only': False,
                        'scientific_id': self.plan['content_id'], 'execution_id': self.execution['content_id'],
                        'attempt_id': 'synthetic-1', 'script': self.ref,
                        'process': {'status': 'not_started'},
                        'submission': {'state': 'unknown', 'token': 'synthetic-token', 'target': 'fixture',
                                       'owner': 'test', 'intent_at': '2026-09-28T00:00:00Z'}}

    def check(self, receipts=None, scope='pilot'):
        return records.check(self.plan, self.execution, receipts or [], self.root, scope)

    def test_valid_consistency_is_not_execution_or_consent_evidence(self):
        result = self.check([self.receipt])
        self.assertEqual(result['record_consistency'], 'passed')
        self.assertEqual(result['execution_readiness'], 'not_assessed')
        self.assertEqual(result['authorization_authenticity'], 'not_assessed')

    def test_external_known_digest_and_order_independence(self):
        import hashlib
        small = {'content': {'x': 1}, 'kind': 'plan', 'schema_version': 1}
        literal = b'{"content":{"x":1},"kind":"plan","schema_version":1}'
        self.assertEqual(records.fingerprint(small), 'sha256:' + hashlib.sha256(literal).hexdigest())
        small['content_id'] = 'ignored'
        small['evidence'] = [{'time': 'later'}]
        self.assertEqual(records.fingerprint(small), 'sha256:' + hashlib.sha256(literal).hexdigest())

    def test_scientific_changes_invalidate_old_approval(self):
        for key, value in [('recipe', {'sdc': 'syn'}), ('software', {'version': 'changed'}),
                           ('inputs', {'snapshot': 'changed'}), ('required_outputs', {'space': 'changed'})]:
            with self.subTest(key=key):
                plan = copy.deepcopy(self.plan)
                plan['content'][key] = value
                plan['content_id'] = records.fingerprint(plan)
                self.assertNotEqual(plan['content_id'], self.plan['content_id'])
                execution = copy.deepcopy(self.execution)
                execution['content']['scientific_id'] = plan['content_id']
                execution['content_id'] = records.fingerprint(execution)
                with self.assertRaisesRegex(ValueError, 'authorization'):
                    records.check(plan, execution, [], self.root, 'pilot')

    def test_resource_change_only_changes_execution(self):
        before = self.plan['content_id']
        old_execution = self.execution['content_id']
        self.execution['content']['resources']['cpus'] = 16
        self.assertEqual(records.fingerprint(self.plan), before)
        self.assertNotEqual(records.fingerprint(self.execution), old_execution)
        with self.assertRaisesRegex(ValueError, 'content_id'):
            self.check()

    def test_wrong_plan_link(self):
        self.execution['content']['scientific_id'] = 'sha256:' + '0' * 64
        self.execution['content_id'] = records.fingerprint(self.execution)
        with self.assertRaisesRegex(ValueError, 'another plan'):
            self.check()

    def test_unknown_snapshot_and_examples_rejected(self):
        self.plan['content']['inputs']['snapshot'] = None
        self.plan['content_id'] = records.fingerprint(self.plan)
        with self.assertRaisesRegex(ValueError, 'unresolved'):
            self.check()
        self.plan['example_only'] = True
        with self.assertRaisesRegex(ValueError, 'examples'):
            self.check()

    def test_changed_referenced_bytes_rejected(self):
        (self.root / 'manifest.json').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            self.check()

    def test_artifact_traversal_and_symlink_escape(self):
        with self.assertRaisesRegex(ValueError, 'escapes'):
            records.verify_files({'$file': '../outside', 'sha256': 'irrelevant'}, self.root)
        with tempfile.TemporaryDirectory() as outside:
            p = Path(outside) / 'outside'; p.write_text('data')
            (self.root / 'alias').symlink_to(p)
            with self.assertRaisesRegex(ValueError, 'escapes'):
                records.verify_files({'$file': 'alias', 'sha256': records.file_identity(p)}, self.root)

    def test_duplicate_attempts_and_wrong_receipt_identity(self):
        with self.assertRaisesRegex(ValueError, 'duplicate attempt'):
            self.check([self.receipt, self.receipt])
        self.receipt['execution_id'] = 'sha256:' + '0' * 64
        with self.assertRaisesRegex(ValueError, 'receipt identity'):
            self.check([self.receipt])

    def test_distinct_attempts_cannot_reuse_submission_token(self):
        other = copy.deepcopy(self.receipt); other['attempt_id'] = 'synthetic-2'
        with self.assertRaisesRegex(ValueError, 'duplicate submission token'):
            self.check([self.receipt, other])

    def test_submitted_requires_acknowledged_job(self):
        self.receipt['submission']['state'] = 'submitted'
        with self.assertRaisesRegex(ValueError, 'job_id'):
            self.check([self.receipt])
        self.receipt['submission']['job_id'] = 'fake-123'
        self.assertEqual(self.check([self.receipt])['receipts_checked'], 1)

    def test_receipt_script_must_belong_to_execution(self):
        other = self.root / 'other.sh'; other.write_text('exit 0\n')
        self.receipt['script'] = {'$file': other.name, 'sha256': records.file_identity(other)}
        with self.assertRaisesRegex(ValueError, 'script is not bound'):
            self.check([self.receipt])

    def test_invalid_environment_key(self):
        self.execution['content']['payload']['env'] = {'BAD=KEY': 'value'}
        self.execution['content_id'] = records.fingerprint(self.execution)
        with self.assertRaisesRegex(ValueError, 'env'):
            self.check()

    def test_scope_and_missing_intent(self):
        with self.assertRaisesRegex(ValueError, 'authorization'):
            self.check(scope='cohort')
        del self.receipt['submission']['token']
        with self.assertRaisesRegex(ValueError, 'intent'):
            self.check([self.receipt])

    def test_duplicate_keys_and_nonfinite_numbers_rejected(self):
        for source in ['{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}', '{"x":1e999}']:
            p = self.root / 'bad.json'; p.write_text(source)
            with self.assertRaises(ValueError):
                records.load(p)

    def test_cli_failure_exit_and_no_record_mutation(self):
        p = self.root / 'plan.json'; p.write_text(json.dumps(self.plan))
        before = p.read_bytes()
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(records.main(['fingerprint', str(p)]), 0)
        self.assertEqual(out.getvalue().strip(), self.plan['content_id'])
        self.assertEqual(before, p.read_bytes())
        p.write_text('[]')
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(records.main(['fingerprint', str(p)]), 2)

    def write_records(self, receipts=()):
        paths = []
        for name, value in (('plan.json', self.plan), ('execution.json', self.execution)):
            (self.root / name).write_text(json.dumps(value)); paths.append(str(self.root / name))
        args = ['check', *paths, '--artifact-root', str(self.root), '--scope', 'pilot']
        for i, receipt in enumerate(receipts):
            path = self.root / f'receipt-{i}.json'; path.write_text(json.dumps(receipt))
            args += ['--receipt', str(path)]
        return args

    def run_cli(self, args):
        with contextlib.redirect_stdout(io.StringIO()) as out, \
             contextlib.redirect_stderr(io.StringIO()) as err:
            code = records.main(args)
        return code, out.getvalue(), err.getvalue()

    def test_cli_check_success_and_failure_exit_codes(self):
        code, out, _ = self.run_cli(self.write_records([self.receipt]))
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)['record_consistency'], 'passed')
        (self.root / 'manifest.json').write_text('changed')
        code, _, err = self.run_cli(self.write_records([self.receipt]))
        self.assertEqual(code, 2)
        self.assertIn('hash mismatch', err)

    def test_cli_symlink_loop_and_deep_nesting_exit_2_without_traceback(self):
        (self.root / 'loop-a').symlink_to(self.root / 'loop-b')
        (self.root / 'loop-b').symlink_to(self.root / 'loop-a')
        deep = self.root / 'deep.json'; deep.write_text('[' * 100000 + ']' * 100000)
        for args in (['fingerprint', str(self.root / 'loop-a')], ['fingerprint', str(deep)],
                     self.write_records() + ['--artifact-root', str(self.root / 'loop-a')]):
            with self.subTest(args=args[:2]):
                code, _, err = self.run_cli(args)
                self.assertEqual(code, 2)
                self.assertNotIn('Traceback', err)
        with self.assertRaisesRegex(ValueError, 'symlink loop'):
            records.verify_files({'$file': 'loop-a', 'sha256': 'x'}, self.root)

    def test_oversized_bom_and_non_utf8_inputs(self):
        p = self.root / 'record.json'
        p.write_bytes(b'\xef\xbb\xbf' + json.dumps(self.plan).encode())
        self.assertEqual(records.fingerprint(records.load(p)), self.plan['content_id'])
        with patch.object(records, 'MAX_RECORD_BYTES', 10):
            with self.assertRaisesRegex(ValueError, 'exceeds'):
                records.load(p)
        p.write_bytes(b'{"x": "\xff"}')
        code, _, err = self.run_cli(['fingerprint', str(p)])
        self.assertEqual(code, 2)
        self.assertNotIn('Traceback', err)

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'FIFOs are POSIX-specific')
    def test_size_cap_is_enforced_by_bounded_read_not_stat(self):
        # st_size is 0 for a FIFO; the cap must still reject oversized content.
        fifo = self.root / 'record.fifo'
        os.mkfifo(fifo)
        payload = b'[' + b'0,' * 40 + b'0]'

        def feed():
            with contextlib.suppress(BrokenPipeError):
                with open(fifo, 'wb') as stream:
                    stream.write(payload)

        writer = threading.Thread(target=feed)
        writer.start()
        try:
            with patch.object(records, 'MAX_RECORD_BYTES', 32):
                with self.assertRaisesRegex(ValueError, 'exceeds'):
                    records.load(fifo)
        finally:
            writer.join(timeout=5)
        self.assertFalse(writer.is_alive())

    def test_identity_keys_with_surrounding_whitespace_rejected(self):
        for field, value in (('job_id', 'fake-1 '), ('target', 'fixture '),
                             ('token', ' synthetic-token'), ('owner', 'test\t')):
            with self.subTest(field=field):
                receipt = copy.deepcopy(self.receipt)
                receipt['submission'][field] = value
                with self.assertRaisesRegex(ValueError, 'surrounding whitespace'):
                    self.check([receipt])
        receipt = copy.deepcopy(self.receipt)
        receipt['attempt_id'] = 'synthetic-1 '
        with self.assertRaisesRegex(ValueError, 'surrounding whitespace'):
            self.check([receipt])

    def test_cli_error_message_is_one_line(self):
        p = self.root / 'dup.json'
        p.write_text('{"a\\nb": 1, "a\\nb": 2}')
        code, _, err = self.run_cli(['fingerprint', str(p)])
        self.assertEqual(code, 2)
        self.assertEqual(len(err.strip().splitlines()), 1)

    def test_non_object_records_and_receipts_rejected(self):
        with self.assertRaisesRegex(ValueError, 'objects'):
            records.check([], self.execution, [], self.root, 'pilot')
        with self.assertRaisesRegex(ValueError, 'receipt must be'):
            self.check(['not a receipt'])

    def test_empty_argv_and_env_strings_are_literal_values(self):
        self.execution['content']['payload']['argv'] = ['fake', '--flag', '']
        self.execution['content']['payload']['env'] = {'PYTHONNOUSERSITE': ''}
        self.execution['content_id'] = records.fingerprint(self.execution)
        self.receipt['execution_id'] = self.execution['content_id']
        self.assertEqual(self.check([self.receipt])['record_consistency'], 'passed')
        self.execution['content']['payload']['argv'] = ['fake', None]
        self.execution['content_id'] = records.fingerprint(self.execution)
        with self.assertRaisesRegex(ValueError, 'unresolved'):
            self.check()
        # Blank strings elsewhere in execution content remain unresolved.
        self.execution['content']['payload']['argv'] = ['fake']
        self.execution['content']['target']['site'] = ' '
        self.execution['content_id'] = records.fingerprint(self.execution)
        with self.assertRaisesRegex(ValueError, 'unresolved'):
            self.check()

    def test_job_id_must_match_submission_state(self):
        for state in ('prepared', 'not_submitted'):
            with self.subTest(state=state):
                receipt = copy.deepcopy(self.receipt)
                receipt['submission'].update(state=state, job_id='fake-1')
                with self.assertRaisesRegex(ValueError, 'inconsistent'):
                    self.check([receipt])
        self.receipt['submission']['job_id'] = 'fake-1'  # unknown may carry a captured ID
        self.assertEqual(self.check([self.receipt])['receipts_checked'], 1)

    def test_duplicate_job_id_for_target_rejected(self):
        first = copy.deepcopy(self.receipt)
        first['submission'].update(state='submitted', job_id='fake-9')
        second = copy.deepcopy(first)
        second['attempt_id'] = 'synthetic-2'
        second['submission']['token'] = 'other-token'
        with self.assertRaisesRegex(ValueError, 'duplicate job_id'):
            self.check([first, second])
        second['submission']['target'] = 'other-cluster'
        self.assertEqual(self.check([first, second])['receipts_checked'], 2)

    def test_receipt_requires_process_status_and_typed_states(self):
        for bad in (None, {}, {'status': ''}):
            with self.subTest(process=bad):
                self.receipt['process'] = bad
                with self.assertRaisesRegex(ValueError, 'process status'):
                    self.check([self.receipt])
        self.receipt['process'] = {'status': 'not_started'}
        self.receipt['qc'] = {'decision': 'hold'}
        with self.assertRaisesRegex(ValueError, 'qc'):
            self.check([self.receipt])

    def test_script_binding_normalizes_path_and_ignores_annotations(self):
        self.receipt['script'] = {'$file': './' + self.ref['$file'], 'sha256': self.ref['sha256'],
                                  'note': 'rendered job'}
        self.assertEqual(self.check([self.receipt])['receipts_checked'], 1)
        self.receipt['script'] = {'$file': self.ref['$file'], 'sha256': 'sha256:' + '0' * 64}
        with self.assertRaisesRegex(ValueError, 'not bound'):
            self.check([self.receipt])

    def test_receipt_artifact_hash_mismatch_outside_script(self):
        other = self.root / 'outputs.json'; other.write_text('{}')
        self.receipt['outputs'] = {'status': 'checked',
                                   'manifest': {'$file': other.name, 'sha256': records.file_identity(other)}}
        self.assertEqual(self.check([self.receipt])['receipts_checked'], 1)
        other.write_text('{"changed": true}')
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            self.check([self.receipt])

    def test_bundled_examples_rejected_but_completed_shape_passes(self):
        loaded = {name: records.load(ASSETS / f'{name}.example.json')
                  for name in ('plan', 'execution', 'receipt')}
        with self.assertRaisesRegex(ValueError, 'examples'):
            records.check(loaded['plan'], loaded['execution'], [], self.root, 'pilot')

        def fill(value):
            if isinstance(value, dict):
                if '$file' in value:
                    path = self.root / value['$file']
                    path.parent.mkdir(parents=True, exist_ok=True); path.write_text('synthetic\n')
                    return {'$file': value['$file'], 'sha256': records.file_identity(path)}
                return {k: fill(v) for k, v in value.items()}
            if isinstance(value, list):
                return [fill(v) for v in value]
            return 'synthetic' if value is None else value

        plan = copy.deepcopy(loaded['plan'])
        plan.update(content=fill(plan['content']), example_only=False)
        plan['content_id'] = records.fingerprint(plan)
        plan['authorizations'] = [{'scientific_id': plan['content_id'], 'scopes': ['pilot'],
                                   'source': 'synthetic', 'limits': {'subjects': ['01']},
                                   'recorded_at': '2026-09-28T00:00:00Z'}]
        execution = copy.deepcopy(loaded['execution'])
        execution.update(content=fill(execution['content']), example_only=False)
        execution['content']['scientific_id'] = plan['content_id']
        execution['content']['payload']['argv'] = ['fmriprep']
        execution['content_id'] = records.fingerprint(execution)
        receipt = fill(loaded['receipt'])
        receipt.update(example_only=False, scientific_id=plan['content_id'],
                       execution_id=execution['content_id'])
        receipt['submission']['job_id'] = None  # consistent with not_submitted
        result = records.check(plan, execution, [receipt], self.root, 'pilot')
        self.assertEqual(result['record_consistency'], 'passed')


if __name__ == '__main__':
    unittest.main()
