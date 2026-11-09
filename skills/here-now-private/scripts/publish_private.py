#!/usr/bin/env python3
"""Private-first here.now publisher for research reports.

Order of operations (resumable through <state>/intent.json):
  1. new site: publish a holding page, set the visitor password, confirm access mode = password
     (content is never public, not even briefly); existing site: check the live version has not drifted
  2. stage the full site against the live baseVersionId, upload, finalize
  3. verify every hosted file (size + sha256) through the owner API
  4. probe the public URL without credentials: every probe path must return 401
  5. confirm no expiry and no pending version; write <state>/receipt.json

Standard library only. API key from $HERENOW_API_KEY or ~/.herenow/credentials. Passwords live in
~/.herenow/<name>.password (0600); never printed or logged.

usage: publish_private.py SITE_DIR --state DIR --password-file NAME --display-name TEXT
         [--create-password] [--probe PATH ...] [--client NAME] [--slug SLUG]
"""
import argparse, concurrent.futures, hashlib, json, mimetypes, os, pathlib, secrets, string, subprocess, sys, time, urllib.request
from urllib.parse import quote, urlsplit

API = 'https://here.now/api/v1'
HOME = pathlib.Path.home() / '.herenow'


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new is not None and urlsplit(newurl).hostname != urlsplit(req.full_url).hostname:
            new.remove_header('Authorization')
        return new


OPENER = urllib.request.build_opener(SafeRedirect())


class Client:
    def __init__(self, client):
        self.key = os.environ.get('HERENOW_API_KEY') or (HOME / 'credentials').read_text().strip()
        self.client = client

    def raw(self, method, url, body=None, upload=None, headers=None, auth=True):
        h = dict(headers or {})
        if auth:
            assert url.startswith(API + '/')
            h['Authorization'] = 'Bearer ' + self.key
            h['X-HereNow-Client'] = self.client
        else:
            assert urlsplit(url).scheme == 'https' and urlsplit(url).hostname.endswith('.r2.cloudflarestorage.com')
        data = upload.read_bytes() if upload is not None else (json.dumps(body, separators=(',', ':')).encode() if body is not None else None)
        if body is not None:
            h['Content-Type'] = 'application/json'
        try:
            with OPENER.open(urllib.request.Request(url, data=data, headers=h, method=method), timeout=180) as r:
                return r.read()
        except Exception as e:  # never echo URLs with signatures or headers
            raise RuntimeError(f'HTTP {method} {urlsplit(url).hostname} failed: {type(e).__name__}') from None

    def api(self, method, path, body=None):
        return json.loads(self.raw(method, API + path, body))


def inventory(folder):
    out = {}
    for p in sorted(folder.rglob('*')):
        # Hidden files/dirs (.herenow, .omc agent logs, .DS_Store, .git ...) are never published.
        if p.is_file() and not any(part.startswith('.') for part in p.relative_to(folder).parts):
            ct = mimetypes.guess_type(p.name)[0] or 'application/octet-stream'
            if p.suffix in ('.csv', '.R', '.py', '.txt', '.md'):
                ct = {'.csv': 'text/csv'}.get(p.suffix, 'text/plain') + '; charset=utf-8'
            out[str(p.relative_to(folder))] = {'size': p.stat().st_size, 'hash': hashlib.sha256(p.read_bytes()).hexdigest(), 'contentType': ct}
    return out


def main(argv=None, client_factory=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('site', type=pathlib.Path)
    ap.add_argument('--state', type=pathlib.Path, required=True, help='directory for intent.json / receipt.json (keep with the project)')
    ap.add_argument('--password-file', required=True, help='name under ~/.herenow, e.g. alice-window-rsa -> ~/.herenow/alice-window-rsa.password')
    ap.add_argument('--create-password', action='store_true', help='generate a 20-char password if the file does not exist')
    ap.add_argument('--display-name', required=True)
    ap.add_argument('--probe', nargs='*', default=None, help='paths that must return 401 unauthenticated (default: "" plus every *.html)')
    ap.add_argument('--client', default='claude-code/here-now-private')
    ap.add_argument('--slug', help='adopt an existing owned site (first run only)')
    a = ap.parse_args(argv)
    os.umask(0o077)
    site = a.site.resolve()
    assert (site / 'index.html').is_file(), 'site root must contain index.html'
    st_dir = a.state; st_dir.mkdir(parents=True, exist_ok=True); I = st_dir / 'intent.json'
    pwf = HOME / (a.password_file + '.password')
    if not pwf.exists():
        if not a.create_password:
            sys.exit(f'{pwf} missing; pass --create-password or create it (0600)')
        alphabet = string.ascii_letters + string.digits
        pwf.write_text(''.join(secrets.choice(alphabet) for _ in range(20)) + '\n'); pwf.chmod(0o600)
    pw = pwf.read_text().strip(); assert len(pw) >= 12, 'password too short'
    c = (client_factory or Client)(a.client)

    def save(s):
        t = I.with_suffix('.tmp'); t.write_text(json.dumps(s, indent=2) + '\n'); t.replace(I)

    def finalize(slug, version):
        try:
            c.api('POST', f'/publish/{slug}/finalize', {'versionId': version})
        except RuntimeError:
            pass
        for _ in range(120):
            live = c.api('GET', f'/publish/{slug}')
            if live.get('currentVersionId') == version and not live.get('pendingVersionId'):
                return live
            time.sleep(5)
        raise RuntimeError('finalize still pending; rerun later (state is saved)')

    def upload(stage, folder):
        def send(t):
            p = folder / t['path']; assert p.is_file()
            for k in range(3):
                try:
                    c.raw('PUT', t['url'], upload=p, headers=t.get('headers', {}), auth=False); return
                except RuntimeError:
                    if k == 2: raise
                    time.sleep(2 + 3 * k)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
            list(ex.map(send, stage['upload']['uploads']))

    inv = inventory(site)
    bundle = hashlib.sha256(json.dumps(inv, sort_keys=True).encode()).hexdigest()
    state = json.loads(I.read_text()) if I.exists() else {}
    if state.get('state') == 'published_and_verified':
        if state.get('bundle_hash') == bundle:
            print(json.dumps(state)); return
        (st_dir / f"receipt-{state['version']}.json").write_text(json.dumps(state, indent=2) + '\n')
        state = {'state': 'protected', 'slug': state['slug'], 'siteUrl': state['siteUrl'], 'base_version': state['version']}; save(state)
    c.api('GET', '/accounts')
    if not state and a.slug:
        live = c.api('GET', f'/publish/{a.slug}')
        state = {'state': 'holding_live', 'slug': a.slug, 'siteUrl': live['siteUrl'], 'base_version': live['currentVersionId']}; save(state)
    if not state:
        H = st_dir / 'holding'; H.mkdir(exist_ok=True)
        (H / 'index.html').write_text('<!doctype html><title>Preparing</title><p>This page is being prepared.</p>')
        stage = c.api('POST', '/publish', {'files': [dict(path=n, **v) for n, v in inventory(H).items()], 'displayName': a.display_name, 'ttlSeconds': None})
        state = {'state': 'holding_staged', 'slug': stage['slug'], 'siteUrl': stage['siteUrl'], 'stage': stage}; save(state)
    if state['state'] == 'holding_staged':
        upload(state['stage'], st_dir / 'holding'); live = finalize(state['slug'], state['stage']['upload']['versionId'])
        state = {'state': 'holding_live', 'slug': state['slug'], 'siteUrl': state['siteUrl'], 'base_version': live['currentVersionId']}; save(state)
    slug = state['slug']
    if state['state'] == 'holding_live':
        c.api('PATCH', f'/publish/{slug}/metadata', {'password': pw, 'displayName': a.display_name, 'ttlSeconds': None})
        assert c.api('GET', f'/publish/{slug}/access')['access']['mode'] == 'password'
        state['state'] = 'protected'; save(state)
    if state['state'] == 'protected':
        assert c.api('GET', f'/publish/{slug}/access')['access']['mode'] == 'password', 'site is not password-protected; refusing to upload'
        live = c.api('GET', f'/publish/{slug}')
        assert live['currentVersionId'] == state['base_version'] and not live.get('pendingVersionId'), 'live site drifted or has a pending version; reconcile first'
        stage = c.api('PUT', f'/publish/{slug}', {'files': [dict(path=n, **v) for n, v in inv.items()], 'baseVersionId': state['base_version'], 'ttlSeconds': None})
        state.update(state='report_staged', stage=stage, version=stage['upload']['versionId']); save(state)
    if state['state'] == 'report_staged':
        upload(state['stage'], site); state['state'] = 'report_uploaded'; save(state)
    if state['state'] == 'report_uploaded':
        finalize(slug, state['version']); state['state'] = 'verification_pending'; save(state)
    assert c.api('GET', f'/publish/{slug}/access')['access']['mode'] == 'password'

    def verify(item):
        n, v = item
        for k in range(3):
            try:
                data = c.raw('GET', API + f'/publish/{slug}/files/' + quote(n, safe='/')); break
            except RuntimeError:
                if k == 2: raise
                time.sleep(1 + k)
        assert len(data) == v['size'] and hashlib.sha256(data).hexdigest() == v['hash'], f'hosted mismatch: {n}'
        return n
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        verified = list(ex.map(verify, inv.items()))
    probes = a.probe if a.probe is not None else [''] + [n for n in inv if n.endswith('.html')]
    codes = {}
    for path in probes:
        r = subprocess.run(['curl', '--http1.1', '-sS', '--connect-timeout', '10', '--max-time', '30', '-o', os.devnull, '-w', '%{http_code}', state['siteUrl'] + path], capture_output=True, text=True, check=True)
        codes[path] = int(r.stdout.strip()); assert codes[path] == 401, f'unauthenticated {path!r} returned {codes[path]}'
    live = c.api('GET', f'/publish/{slug}')
    assert live['currentVersionId'] == state['version'] and not live.get('expiresAt') and not live.get('pendingVersionId')
    state = {k: v for k, v in state.items() if k != 'stage'}
    state.update(state='published_and_verified', verified_files=len(verified), bundle_hash=bundle, access='password', password_file=str(pwf.name), expiresAt=live.get('expiresAt'), unauthenticated_status=codes)
    save(state); (st_dir / 'receipt.json').write_text(json.dumps(state, indent=2) + '\n'); print(json.dumps(state))


if __name__ == '__main__':
    main()
