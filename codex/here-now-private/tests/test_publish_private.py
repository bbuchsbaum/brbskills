"""Offline tests for publish_private.py against an in-memory fake of the here.now API."""
import hashlib, importlib.util, json, pathlib, sys, tempfile, unittest
from unittest import mock

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('publish_private', HERE.parent / 'scripts' / 'publish_private.py')
pp = importlib.util.module_from_spec(spec); spec.loader.exec_module(pp)


class FakeHereNow:
    """Minimal model of the endpoints the publisher uses; records an event log."""
    def __init__(self):
        self.versions, self.current, self.pending, self.mode, self.events = {}, None, None, 'anyone_with_link', []
        self.slug, self.n = 'fake-site-1234', 0

    def factory(self, client_name):
        return self

    def _stage(self, files):
        self.n += 1; v = f'v{self.n}'; self.pending = v; self.versions[v] = {}
        return {'slug': self.slug, 'siteUrl': f'https://{self.slug}.here.now/',
                'upload': {'versionId': v, 'uploads': [{'path': f['path'], 'url': f'https://x.r2.cloudflarestorage.com/{v}/{f["path"]}'} for f in files]}}

    def api(self, method, path, body=None):
        self.events.append((method, path.split('/')[-1] if path.count('/') > 2 else path))
        if path == '/accounts': return {}
        if method == 'POST' and path == '/publish': return self._stage(body['files'])
        if method == 'PUT' and path == f'/publish/{self.slug}':
            if body['baseVersionId'] != self.current: raise RuntimeError('version_conflict')
            return self._stage(body['files'])
        if method == 'POST' and path.endswith('/finalize'):
            assert body['versionId'] == self.pending; self.current, self.pending = self.pending, None; return {}
        if method == 'GET' and path == f'/publish/{self.slug}':
            return {'currentVersionId': self.current, 'pendingVersionId': self.pending, 'expiresAt': None, 'siteUrl': f'https://{self.slug}.here.now/'}
        if method == 'PATCH' and path.endswith('/metadata'):
            assert self.current is not None, 'password before finalize'
            if body.get('password'): self.mode = 'password'
            return {}
        if method == 'GET' and path.endswith('/access'): return {'access': {'mode': self.mode}}
        raise AssertionError(f'unexpected {method} {path}')

    def raw(self, method, url, body=None, upload=None, headers=None, auth=True):
        if method == 'PUT' and not auth:
            v, rel = url.split('.com/', 1)[1].split('/', 1)
            self.events.append(('upload', rel, self.mode)); self.versions[v][rel] = upload.read_bytes(); return b''
        if method == 'GET' and '/files/' in url:
            return self.versions[self.current][url.split('/files/', 1)[1]]
        raise AssertionError(f'unexpected raw {method}')


def curl401(*a, **k):
    return mock.Mock(stdout='401')


class PublishPrivateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp()); self.home = self.tmp / 'herenow'; self.home.mkdir()
        self.site = self.tmp / 'site'; (self.site / 'pages').mkdir(parents=True)
        (self.site / 'index.html').write_text('<p>report</p>'); (self.site / 'pages' / 'a.html').write_text('<p>a</p>')
        (self.site / 'summary.csv').write_text('x,y\n1,2\n')
        (self.site / '.omc' / 'state').mkdir(parents=True); (self.site / '.omc' / 'state' / 'log.jsonl').write_text('secret')
        (self.site / '.DS_Store').write_text('x')
        self.state = self.tmp / 'publication'; self.fake = FakeHereNow()
        self.patches = [mock.patch.object(pp, 'HOME', self.home), mock.patch.object(pp.subprocess, 'run', side_effect=curl401), mock.patch.object(pp.time, 'sleep')]
        for p in self.patches: p.start()

    def tearDown(self):
        for p in self.patches: p.stop()

    def run_pub(self, *extra):
        return pp.main([str(self.site), '--state', str(self.state), '--password-file', 'test', '--display-name', 'T', *extra], client_factory=self.fake.factory)

    def test_new_site_password_before_content_and_hidden_skipped(self):
        self.run_pub('--create-password')
        uploads = [e for e in self.fake.events if e[0] == 'upload']
        content = [e for e in uploads if e[1] != 'index.html' or e[2] == 'password']
        self.assertTrue(all(e[2] == 'password' for e in uploads[1:]), 'content uploaded before password')
        self.assertEqual(uploads[0], ('upload', 'index.html', 'anyone_with_link'))  # holding page only
        published = set(self.fake.versions[self.fake.current])
        self.assertEqual(published, {'index.html', 'pages/a.html', 'summary.csv'})
        r = json.loads((self.state / 'receipt.json').read_text())
        self.assertEqual(r['state'], 'published_and_verified'); self.assertEqual(r['verified_files'], 3)
        self.assertEqual(set(r['unauthenticated_status']), {'', 'index.html', 'pages/a.html'})
        self.assertEqual((self.home / 'test.password').stat().st_mode & 0o777, 0o600)
        self.assertNotIn(b'secret', b''.join(self.fake.versions[self.fake.current].values()))
        self.assertTrue(content)

    def test_unchanged_rerun_is_noop_and_change_makes_new_version(self):
        self.run_pub('--create-password'); v = self.fake.current
        self.run_pub(); self.assertEqual(self.fake.current, v)
        (self.site / 'summary.csv').write_text('x,y\n1,3\n'); self.run_pub()
        self.assertNotEqual(self.fake.current, v)
        self.assertEqual(self.fake.versions[self.fake.current]['summary.csv'], b'x,y\n1,3\n')
        self.assertTrue((self.state / f'receipt-{v}.json').exists())

    def test_drift_refused(self):
        self.run_pub('--create-password')
        self.fake.current = 'edited-elsewhere'; self.fake.versions['edited-elsewhere'] = {}
        (self.site / 'summary.csv').write_text('changed')
        with self.assertRaises(AssertionError): self.run_pub()

    def test_missing_password_file_stops(self):
        with self.assertRaises(SystemExit): self.run_pub()
        self.assertEqual(self.fake.events, [])

    def test_refuses_upload_when_not_password_protected(self):
        self.run_pub('--create-password')
        self.fake.mode = 'anyone_with_link'; (self.site / 'summary.csv').write_text('changed')
        with self.assertRaises(AssertionError): self.run_pub()
        self.assertFalse(any(e[0] == 'upload' and e[2] != 'password' and e[1] == 'summary.csv' for e in self.fake.events))

    def test_hosted_mismatch_detected(self):
        orig = self.fake.raw
        def corrupt(method, url, **k):
            data = orig(method, url, **k)
            return data + b'x' if method == 'GET' and url.endswith('summary.csv') else data
        self.fake.raw = corrupt
        with self.assertRaises(AssertionError): self.run_pub('--create-password')

    def test_requires_index_html(self):
        (self.site / 'index.html').unlink()
        with self.assertRaises(AssertionError): self.run_pub('--create-password')


if __name__ == '__main__':
    unittest.main()
