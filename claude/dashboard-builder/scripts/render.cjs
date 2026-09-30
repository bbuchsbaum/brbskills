#!/usr/bin/env node
// Render every specimen snapshot through the shipped page and check it in a real browser.
//
//   node render.cjs [--out DIR] [--only name[,name]] [--skip-server]
//
// File mode: each fixture in tests/fixtures/*.json is written to a temporary `.dashboard/`
// as index.html + data.js (`window.__hub(<json>);`), opened via file://, and captured at
// 1440x900 and 390x844 in dark and light. Timestamps are shifted so that `generated`
// equals the moment of rendering; every other ISO time moves by the same offset and keeps
// its UTC offset, so relative times ("3m ago", elapsed timers) look live.
// Server mode: Playwright request interception mocks GET /api/hub and the POST endpoints
// and checks the composer, inline answers, pause/resume and board posts send the right
// requests with the X-Dash-Token header taken from the URL fragment.
// Screenshots go to --out (default: a new temp directory), never into the skill folder.
const path = require('path'), fs = require('fs'), os = require('os');
const { pathToFileURL } = require('url');
const { createRequire } = require('module');
const { spawnSync } = require('child_process');

const SKILL = path.resolve(__dirname, '..');
const PAGE = path.join(SKILL, 'assets', 'dashboard.html');
const FIXTURES = path.join(SKILL, 'tests', 'fixtures');
const SIZES = [[1440, 900, 'desktop'], [390, 844, 'mobile']];
const THEMES = ['dark', 'light'];
// Specimens checked for overflow and errors but kept out of the screenshot gallery.
const GATE_ONLY = new Set(['stress']);

function loadPlaywright() {
  const tries = [process.env.PLAYWRIGHT_MODULE, 'playwright',
    '/opt/homebrew/lib/node_modules/@playwright/cli/node_modules/playwright',
    '/opt/homebrew/lib/node_modules/playwright', '/usr/local/lib/node_modules/playwright'].filter(Boolean);
  const local = createRequire(path.join(process.cwd(), 'package.json'));
  for (const candidate of tries) {
    try { return local(candidate); } catch (_) { /* next installation */ }
  }
  throw new Error('Playwright not found; set PLAYWRIGHT_MODULE to an installed package. No browser was launched.');
}
function audit(when) {
  const guard = path.join(os.homedir(), '.local/share/agent-policy/browser-automation-guard.mjs');
  if (!fs.existsSync(guard)) return;
  const result = spawnSync(process.execPath, [guard, '--audit'], { encoding: 'utf8' });
  if (result.status !== 0) throw new Error(`Browser audit (${when}) failed: ${result.stderr || result.stdout || result.error}`);
  process.stdout.write(`[audit ${when}] ${result.stdout.trim().split('\n').slice(-1)[0] || 'ok'}\n`);
}
async function launch(chromium) {
  if (process.env.PLAYWRIGHT_EXECUTABLE_PATH) return chromium.launch({ executablePath: process.env.PLAYWRIGHT_EXECUTABLE_PATH });
  try { return await chromium.launch(); }
  catch (error) {
    if (!error.message.includes("Executable doesn't exist")) throw error;
    const cache = process.env.PLAYWRIGHT_BROWSERS_PATH || path.join(os.homedir(), process.platform === 'darwin' ? 'Library/Caches/ms-playwright' : '.cache/ms-playwright');
    const candidates = fs.existsSync(cache) ? fs.readdirSync(cache).filter((s) => /^chromium_headless_shell-\d+$/.test(s)).sort((a, b) => Number(b.split('-').pop()) - Number(a.split('-').pop())) : [];
    for (const version of candidates) {
      const rootDir = path.join(cache, version);
      for (const sub of fs.readdirSync(rootDir)) for (const bin of ['chrome-headless-shell', 'headless_shell']) {
        const executablePath = path.join(rootDir, sub, bin);
        if (fs.existsSync(executablePath) && fs.statSync(executablePath).isFile()) return chromium.launch({ executablePath });
      }
    }
    throw error;
  }
}

// The backend's own destructive() verdict for a command, so the gate renders exactly what a hook would record.
function backendDanger(cmd) {
  const code = 'import sys, json; sys.path.insert(0, sys.argv[1]); import dash; print(json.dumps(dash.destructive(sys.argv[2])))';
  const r = spawnSync('python3', ['-c', code, path.join(SKILL, 'scripts'), cmd], { encoding: 'utf8' });
  if (r.status !== 0) throw new Error(`dash.destructive failed: ${r.stderr}`);
  return JSON.parse(r.stdout);
}

// ---- time shifting -------------------------------------------------------------------
const ISO = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$/;
function formatAt(ms, offset) {
  if (offset === 'Z') return new Date(ms).toISOString();
  const sign = offset[0] === '-' ? -1 : 1, [h, m] = offset.slice(1).split(':').map(Number);
  const local = new Date(ms + sign * (h * 60 + m) * 60000).toISOString();
  return local.slice(0, -1) + offset;
}
function shift(value, delta) {
  if (typeof value === 'string' && ISO.test(value)) return formatAt(Date.parse(value) + delta, value.match(ISO)[2]);
  if (Array.isArray(value)) return value.map((v) => shift(v, delta));
  if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, shift(v, delta)]));
  return value;
}
const live = (snap) => shift(snap, Date.now() - Date.parse(snap.generated));
const dataJs = (snap) => `window.__hub(${JSON.stringify(snap).replace(/<\//g, '<\\/')});\n`;

// ---- page checks ---------------------------------------------------------------------
async function pageChecks(page, snap, tag, failures) {
  const r = await page.evaluate((ids) => {
    const out = { overflow: document.documentElement.scrollWidth - innerWidth, missing: [], clipped: [], bad: [] };
    for (const id of ids) if (!document.querySelector(`[data-lane="${CSS.escape(id)}"]`)) out.missing.push(id);
    for (const el of document.body.querySelectorAll('*')) {
      if (el.closest('[hidden]') || el.closest('svg') || el.closest('.sr-only')) continue;
      const cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.display === 'inline' || cs.display === 'contents') continue;
      const hasText = Array.from(el.childNodes).some((n) => n.nodeType === 3 && n.nodeValue.trim());
      if (!hasText || !el.clientWidth) continue;
      if (cs.overflowX === 'visible' && el.scrollWidth > el.clientWidth + 1) out.clipped.push(`${el.tagName.toLowerCase()}.${el.className} "${el.textContent.trim().slice(0, 40)}"`);
      const rect = el.getBoundingClientRect();
      if (rect.right > innerWidth + 1) out.clipped.push(`offscreen ${el.tagName.toLowerCase()}.${el.className} in ${el.parentElement.tagName.toLowerCase()}.${el.parentElement.className} "${el.textContent.trim().slice(0, 30)}"`);
    }
    const text = document.body.innerText;
    for (const w of ['NaN', 'undefined', 'Invalid Date', '[object Object]', 'null']) if (new RegExp(`\\b${w.replace(/[[\]]/g, '\\$&')}\\b`).test(text)) out.bad.push(w);
    return out;
  }, snap.sessions.filter((s) => s.activity !== 'ended' || snap.sessions.every((x) => x.activity === 'ended')).map((s) => s.id));
  if (r.overflow > 1) failures.push(`${tag}: horizontal overflow ${r.overflow}px`);
  if (r.missing.length) failures.push(`${tag}: sessions not rendered: ${r.missing.join(', ')}`);
  for (const c of [...new Set(r.clipped)].slice(0, 5)) failures.push(`${tag}: text overflows its box: ${c}`);
  for (const b of r.bad) failures.push(`${tag}: page text contains "${b}"`);
}

async function fileMode(browser, name, raw, out, failures) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'dash-render-'));
  const hubDir = path.join(dir, '.dashboard');
  fs.mkdirSync(hubDir);
  fs.copyFileSync(PAGE, path.join(hubDir, 'index.html'));
  try {
    for (const theme of GATE_ONLY.has(name) ? ['dark'] : THEMES) for (const [w, h, size] of SIZES) {
      const tag = `${name} ${size} ${theme}`;
      const snap = live(raw);
      fs.writeFileSync(path.join(hubDir, 'data.js'), dataJs(snap));
      const ctx = await browser.newContext({ viewport: { width: w, height: h }, colorScheme: theme, deviceScaleFactor: 1 });
      try {
        await ctx.addInitScript((t) => { try { localStorage.setItem('dash.theme', t); } catch (_) { /* file origin */ } }, theme);
        await ctx.route(/^https?:\/\//, (route) => { failures.push(`${tag}: network request ${route.request().url()}`); return route.abort(); });
        const page = await ctx.newPage();
        page.on('pageerror', (e) => failures.push(`${tag}: ${e.message}`));
        page.on('console', (m) => { if (m.type() === 'error') failures.push(`${tag}: console ${m.text()}`); });
        await page.goto(pathToFileURL(path.join(hubDir, 'index.html')).href);
        await page.waitForFunction(() => document.documentElement.dataset.ready === '1', null, { timeout: 5000 });
        await page.evaluate(() => document.fonts.ready);
        if (await page.evaluate(() => document.documentElement.dataset.theme) !== theme) failures.push(`${tag}: theme not applied`);
        await pageChecks(page, snap, tag, failures);
        if (name === 'done') {
          const want = pathToFileURL(snap.sessions[0].plan.deliverables[1].path).href;
          const got = await page.getByRole('link', { name: 'Coverage report' }).getAttribute('href');
          if (got !== want) failures.push(`${tag}: deliverable link ${got} != ${want}`);
        }
        // File mode is read-only: no live-looking write controls at all.
        const writeControls = await page.locator('textarea[data-composer], form[data-form=answer], form[data-form=mote], [data-act=pause], [data-act=resume], [data-act=reply]').count();
        if (writeControls) failures.push(`${tag}: ${writeControls} write controls rendered in file mode`);
        if (name === 'stress') {
          // Every lane, all needs, a long burst list and the whole timeline must still fit.
          await page.evaluate(() => { for (const b of document.querySelectorAll('[data-act=needs-more],[data-act=ended]')) b.click(); });
          await page.waitForTimeout(100);
          for (const b of await page.locator('.burst-btn').all()) await b.click();
          await pageChecks(page, snap, tag + ' (expanded)', failures);
        }
        if (name === 'needs-you') {
          // One noun, one number: the header tally must agree with the Needs-you band.
          const h = await page.locator('.need-tally b').innerText().catch(() => 'missing');
          const b = await page.locator('.needs-h .n').innerText().catch(() => 'missing');
          if (h !== b) failures.push(`${tag}: header says ${h} need you, band says ${b}`);
          // The destructive warning is shown exactly once (hero on the selected session, card otherwise).
          const dangers = await page.locator('.danger').allInnerTexts();
          if (dangers.length !== 1 || !/--delete/.test(dangers[0])) failures.push(`${tag}: destructive --delete shown ${dangers.length} times (want exactly once)`);
          // One line: the label and the destination it acts on.
          if (!/→ scratch\/fmriprep\//.test(dangers[0] || '')) failures.push(`${tag}: destructive line hides the destination ("${dangers[0]}")`);
          if (size === 'desktop' && await page.locator('.danger').evaluate((el) => el.getBoundingClientRect().height) > 32) failures.push(`${tag}: destructive line wraps on desktop`);
          // The band points to the selected session's needs in one line and packs the rest into one grid.
          if (await page.locator('.chip-need').count() || !(await page.locator('#needs .pointer').count())) failures.push(`${tag}: needs band repeats the selected session's needs as chips`);
          const bandH = await page.locator('#needs').evaluate((el) => el.getBoundingClientRect().height);
          if (size === 'desktop' && bandH > 200) failures.push(`${tag}: needs band ${Math.round(bandH)}px tall (want ≤ 200)`);
          if (await page.locator('.hn-grid .who').count()) failures.push(`${tag}: hero need cards repeat their own session's name`);
          // The blocked row names its step, and a hero with a big figure doesn't repeat the duration beside the label.
          if (!/Stage fMRIPrep derivatives/.test(await page.locator('.now-foot').innerText())) failures.push(`${tag}: "Blocked" row has no subject`);
          if (/^for /.test(await page.locator('.now-since').innerText())) failures.push(`${tag}: permission hero shows two durations`);
          // Two session cards fill the row instead of leaving half of it empty.
          if (size === 'desktop') {
            const fill = await page.evaluate(() => { const l = document.getElementById('lanes'), c = [...l.querySelectorAll('.lane')], cs = getComputedStyle(l);
              return l.getBoundingClientRect().right - parseFloat(cs.paddingRight) - Math.max(...c.map((x) => x.getBoundingClientRect().right)); });
            if (fill > 6) failures.push(`${tag}: session cards leave ${Math.round(fill)}px of the row empty`);
          }
          // The page's own heuristic (no backend field): the target comes from the matched simple command.
          let rv = snap.revision + 100;
          const dvar = async (cmd, want, bad, backend) => {
            const v = JSON.parse(JSON.stringify(snap)); v.revision = ++rv;
            v.sessions[0].current.summary = cmd; delete v.sessions[0].current.destructive; for (const a of v.sessions[0].attention) delete a.destructive;
            if (backend) { const f = backendDanger(cmd); v.sessions[0].current.destructive = f; for (const a of v.sessions[0].attention) if (a.kind === 'permission') a.destructive = f; }
            fs.writeFileSync(path.join(hubDir, 'data.js'), dataJs(v));
            await page.waitForFunction((r) => document.documentElement.dataset.rev === String(r), v.revision, { timeout: 6000 }).catch(() => failures.push(`${tag}: variant not loaded`));
            const t = await page.locator('.danger').innerText().catch(() => '');
            if (!want.test(t) || (bad && bad.test(t))) failures.push(`${tag}: destructive line for "${cmd}" reads "${t}"`);
          };
          if (size === 'desktop' && theme === 'dark') {
            await dvar('rsync -a --delete src/ dst/ && echo ok', /→ dst\//, /→ ok/);
            await dvar('rsync -a --delete src/ dst/ 2>&1 | tee sync.log', /→ dst\//, /sync\.log/);
            await dvar('rm -rf a b c', /→ a, b, c/);
            await dvar(`Rscript -e "unlink('derivatives', recursive = TRUE)"`, /unlink/, /→/);
            await dvar(`python -c "import shutil; shutil.rmtree('out')"`, /rmtree/, /→/);
            // Prose and grep patterns are not code: no warning. chmod -R is medium, as in dash.py.
            await dvar(`echo 'shutil.rmtree is bad'`, /^$/);
            await dvar(`git log --grep='unlink(x, recursive = TRUE)'`, /^$/);
            await dvar('chmod -R 755 out', /^Risky/);
            // The real backend field (dash.destructive): quote-aware targets, no redirect digits.
            await dvar('rm -rf out 2>/dev/null', /→ out · /, /→ out, 2/, true);
            await dvar('rm -rf "my dir"', /→ my dir · /, /my, dir/, true);
            await dvar('rsync -a --delete src/ dst/ 2>&1 | tee sync.log', /→ dst\/ · /, /→ 2/, true);
            await dvar('rsync -a --delete src/ dst/ # sync mirror', /→ dst\/ · /, /mirror/, true);
          }
          // A permission prompt from 4 h ago is reported, not asserted as live.
          const old4 = shift(raw, Date.now() - 4 * 3600e3 - Date.parse(raw.generated)); old4.revision = ++rv;
          fs.writeFileSync(path.join(hubDir, 'data.js'), dataJs(old4));
          await page.waitForFunction((r) => document.documentElement.dataset.rev === String(r), old4.revision, { timeout: 6000 }).catch(() => failures.push(`${tag}: 4 h data not loaded`));
          if (!/^Last reported/.test(await page.locator('.now-label').innerText()) || await page.locator('.dot.live').count()) failures.push(`${tag}: 4 h old permission wait reads as live`);
          const b4 = await page.locator('[data-stale]').innerText().catch(() => '');
          if (/long command/.test(b4) || !/awaiting approval/.test(b4)) failures.push(`${tag}: stale permission banner wording ("${b4.slice(0, 200)}")`);
          // The dimmed "Blocked" pill stays readable: at least 4.5:1 against its own ground.
          const cr = await page.locator('.now-foot.dim .pill.badge').evaluate((el) => {
            const rgb = (c) => (c.match(/[\d.]+/g) || []).slice(0, 3).map(Number), L = (c) => { const v = rgb(c).map((x) => { x /= 255; return x <= .03928 ? x / 12.92 : ((x + .055) / 1.055) ** 2.4; }); return .2126 * v[0] + .7152 * v[1] + .0722 * v[2]; };
            const cs = getComputedStyle(el), a = L(cs.color), b = L(cs.backgroundColor); return (Math.max(a, b) + .05) / (Math.min(a, b) + .05); }).catch(() => 0);
          if (cr < 4.5) failures.push(`${tag}: dimmed plan pill contrast ${cr.toFixed(2)}`);
          const back = live(raw); back.revision = old4.revision + 1;
          fs.writeFileSync(path.join(hubDir, 'data.js'), dataJs(back));
          await page.waitForFunction((r) => document.documentElement.dataset.rev === String(r), back.revision, { timeout: 6000 }).catch(() => failures.push(`${tag}: fresh data not reloaded`));
        }
        if (name === 'stalled') {
          const hero = await page.locator('.now').innerText();
          if (!/Silent since/.test(hero) || /may be inside|may be a long command/.test(hero)) failures.push(`${tag}: stalled copy contradicts the finished last command`);
          // The explanation is never cut off, and the project name keeps its words.
          if (await page.locator('.now-sum').evaluate((el) => el.scrollHeight > el.clientHeight + 1)) failures.push(`${tag}: stalled explanation is clipped`);
          if (await page.locator('.proj').evaluate((el) => el.scrollWidth > el.clientWidth + 1)) failures.push(`${tag}: project name truncated`);
          // The silence is stated once in the hero: by the big figure.
          const bigS = (await page.locator('.now-el').innerText()).split('\n')[0].trim().split(' ')[0];
          const nS = ((await page.locator('.now').innerText()).match(new RegExp(`\\b${bigS}\\b`, 'g')) || []).length;
          if (nS !== 1) failures.push(`${tag}: stalled hero states "${bigS}" ${nS} times`);
          // The stalled timer is a duration, never clock-like ("14:06").
          if (/^\d+:\d\d/.test(await page.locator('.now-el').innerText())) failures.push(`${tag}: stalled timer reads like a clock time`);
          // 26 h later a stall is reported, not live, and stops ticking.
          const s26 = shift(raw, Date.now() - 26 * 3600e3 - Date.parse(raw.generated)); s26.revision += 9;
          fs.writeFileSync(path.join(hubDir, 'data.js'), dataJs(s26));
          await page.waitForFunction((r) => document.documentElement.dataset.rev === String(r), s26.revision, { timeout: 6000 }).catch(() => failures.push(`${tag}: 26 h stalled data not loaded`));
          if (!/^Last reported stalled/.test(await page.locator('.now-label').innerText())) failures.push(`${tag}: 26 h stall reads live`);
          const back26 = live(raw); back26.revision = s26.revision + 1;
          fs.writeFileSync(path.join(hubDir, 'data.js'), dataJs(back26));
          await page.waitForFunction((r) => document.documentElement.dataset.rev === String(r), back26.revision, { timeout: 6000 }).catch(() => {});
        }
        if (name === 'done') {
          if (!(await page.locator('.now .now-deliv a').count())) failures.push(`${tag}: deliverables not in the hero of an ended session`);
          if (await page.locator('#digest:not([hidden])').count()) failures.push(`${tag}: since-you-left shown for an ended session`);
        }
        // A 41 s old session: the digest would only repeat the hero.
        if (name === 'fresh' && await page.locator('#digest:not([hidden])').count()) failures.push(`${tag}: since-you-left repeats the hero of a brand-new session`);
        // A session that started while you were away (e4f5, 25 min old) is summarised, not hidden.
        if (name === 'needs-you' && !/started 2\dm ago/.test(await page.locator('#lanes').innerText())) failures.push(`${tag}: a session that started while away is not summarised`);
        // Card names stay short enough to hear: near 200 characters even on the stress fixture.
        const longName = await page.evaluate(() => [...document.querySelectorAll('.lane')].map((l) => l.getAttribute('aria-label') || '').sort((x, y) => y.length - x.length)[0] || '');
        if (longName.length > 210) failures.push(`${tag}: a card's accessible name is ${longName.length} characters ("${longName}")`);
        // The mobile sticky header takes at most two rows.
        if (size === 'mobile' && await page.locator('#top').evaluate((el) => el.getBoundingClientRect().height) > 84) failures.push(`${tag}: mobile header taller than two rows`);
        if (await page.locator('.clock').count()) failures.push(`${tag}: header clock shown next to "data as of"`);
        if (name === 'trio-mote' && size === 'mobile' && !/working/.test(await page.locator('.tally').innerText())) failures.push(`${tag}: mobile header count lost its word`);
        if (!GATE_ONLY.has(name)) await page.screenshot({ path: path.join(out, `${name}-${size}-${theme}.png`), fullPage: true });
        if (name === 'trio-mote' && size === 'desktop') {
          await page.keyboard.press('j'); await page.keyboard.press('j');
          await page.waitForFunction(() => document.querySelector('.lane.is-sel .lane-label').textContent.includes('Port'), null, { timeout: 2000 });
          await pageChecks(page, snap, tag + ' (codex selected)', failures);
          await page.screenshot({ path: path.join(out, `${name}-${size}-${theme}-codex.png`), fullPage: true });
        }
        if (name === 'trio-mote') {
          // Side-by-side comparison: every live session card carries its own "since you left" line.
          if (!(await page.locator('.shell.cmp').count())) failures.push(`${tag}: three sessions not shown as a comparison`);
          const since = await page.locator('.lane .lane-since').count();
          if (since !== 3) failures.push(`${tag}: ${since} session cards with a since-you-left line (want 3)`);
          if (await page.locator('#digest:not([hidden])').count()) failures.push(`${tag}: separate digest strip shown although the cards carry it`);
          // File mode can't send, so it never claims a wake-up, even for a session with a live watcher (3d07).
          await page.locator('[data-lane="3d07b5e2-9a4c-4e11-b7a0-6f2d1c88e412"]').click();
          const idle = await page.locator('.now').innerText();
          if (/wake/i.test(idle.replace(/when it next wakes/g, '')) || !/server view/.test(idle) || !/was running as of/.test(idle) || /can.t be woken|resumes when you type/.test(idle)) failures.push(`${tag}: file-mode idle hero wording wrong ("${idle.slice(0, 160)}")`);
          if (/wakes on message/.test(await page.locator('#lanes').innerText())) failures.push(`${tag}: file mode claims a card wakes on message`);
          // Dismiss keeps the reader in place: no scroll, focus on the Sessions heading.
          await page.evaluate(() => window.scrollTo(0, 0));
          const y0 = await page.evaluate(() => scrollY);
          await page.evaluate(() => document.querySelector('[data-act=digest-dismiss]').click());
          await page.waitForTimeout(50);
          if (await page.locator('.lane .lane-since').count()) failures.push(`${tag}: dismissing the summary left since-you-left lines`);
          if (!(await page.evaluate(() => document.activeElement && document.activeElement.id === 'sessions-h'))) failures.push(`${tag}: dismiss did not focus the Sessions heading`);
          const y1 = await page.evaluate(() => scrollY);
          if (Math.abs(y1 - y0) > 4) failures.push(`${tag}: dismiss scrolled the page ${y1 - y0}px`);
          // 12 min without events: the Edit (a quick tool) is stale; quiet Codex is idle, not blamed; the hub isn't blamed.
          const q12 = shift(raw, Date.now() - 12 * 60000 - Date.parse(raw.generated)); q12.revision += 5;
          fs.writeFileSync(path.join(hubDir, 'data.js'), dataJs(q12));
          await page.waitForFunction((r) => document.documentElement.dataset.rev === String(r), q12.revision, { timeout: 6000 }).catch(() => failures.push(`${tag}: 12 min data not loaded`));
          const ban = await page.locator('[data-stale]').innerText().catch(() => '');
          if (!/Searchlight/.test(ban) || /Port contrast/.test(ban) || !/inside Edit/.test(ban)) failures.push(`${tag}: 12 min banner misattributes ("${ban.slice(0, 200)}")`);
          if (!/no dash\.py report/.test(await page.locator('[data-lane="c2d4e6f8-1a3b-4c5d-8e9f-0a1b2c3d4e5f"]').innerText().catch(() => ''))) failures.push(`${tag}: quiet Codex not shown as "no dash.py report"`);
          if (!(await page.locator('.tally .t-stale').count())) failures.push(`${tag}: stale Edit counted as working`);
          if (!/An Edit call/.test(ban)) failures.push(`${tag}: banner grammar ("${ban.slice(0, 160)}")`);
          // Codex with a task in progress and no report is "Quiet", not idle, in its card, the header and the conflict row.
          const cx = await page.locator('[data-lane="c2d4e6f8-1a3b-4c5d-8e9f-0a1b2c3d4e5f"]').innerText().catch(() => '');
          if (!/Quiet/.test(cx) || /Idle/.test(cx) || !(await page.locator('.tally .t-quiet').count())) failures.push(`${tag}: quiet Codex with a doing task reads idle ("${cx.slice(0, 80)}")`);
          if (!/Port contrast[\s\S]*quiet/.test(await page.locator('#needs .k-conflict').innerText())) failures.push(`${tag}: conflict row calls the quiet Codex session idle`);
          // The stale hero names the last reported tool, not a running one, and its big figure is the silence.
          await page.locator('[data-lane="a91e77c0-3b2f-4d8e-8f10-2c9b44e1d0f3"]').click();
          const sh = await page.locator('.now').innerText();
          if (/running/.test(sh) || !/last reported/.test(sh) || /≥/.test(await page.locator('.now-el').innerText())) failures.push(`${tag}: stale Edit hero wording ("${sh.slice(0, 160)}")`);
          // A fresh data.js proves the hub is alive: the banner must not suggest it stopped.
          const q12b = JSON.parse(JSON.stringify(q12)); q12b.revision += 1; q12b.generated = new Date().toISOString();
          fs.writeFileSync(path.join(hubDir, 'data.js'), dataJs(q12b));
          await page.waitForFunction((r) => document.documentElement.dataset.rev === String(r), q12b.revision, { timeout: 6000 }).catch(() => failures.push(`${tag}: fresh-generated data not loaded`));
          const banB = await page.locator('[data-stale]').innerText().catch(() => '');
          if (/hub may have stopped/.test(banB) || !/hub is running|rebuilt/.test(banB)) failures.push(`${tag}: hub blamed although data.js is fresh ("${banB.slice(-160)}")`);
          // 26 h later, a Codex session waiting for you is reported, not asserted as live.
          const w26 = shift(raw, Date.now() - 26 * 3600e3 - Date.parse(raw.generated)); w26.revision = q12b.revision + 1;
          w26.sessions.find((x) => x.agent === 'codex').activity = 'waiting_user';
          fs.writeFileSync(path.join(hubDir, 'data.js'), dataJs(w26));
          await page.waitForFunction((r) => document.documentElement.dataset.rev === String(r), w26.revision, { timeout: 6000 }).catch(() => failures.push(`${tag}: 26 h Codex data not loaded`));
          if (!/Last reported waiting/.test(await page.locator('[data-lane="c2d4e6f8-1a3b-4c5d-8e9f-0a1b2c3d4e5f"]').innerText().catch(() => ''))) failures.push(`${tag}: 26 h Codex waiting reads live`);
          // A mixed stale set (an Edit session and a Codex session waiting) gets no single tool-shaped reason.
          const mixed = await page.locator('[data-stale]').innerText().catch(() => '');
          if (/long command|inside a tool call/.test(mixed)) failures.push(`${tag}: mixed stale banner gives one wrong reason ("${mixed.slice(0, 200)}")`);
          if (size === 'desktop' && theme === 'dark') {
            // The hub sentence is re-decided as time passes: data rebuilt 9m 52s ago stops proving the hub alive at 10 min.
            const edge = shift(raw, Date.now() - 12 * 60000 - Date.parse(raw.generated)); edge.revision = w26.revision + 1;
            edge.generated = new Date(Date.now() - (10 * 60 - 8) * 1000).toISOString();
            fs.writeFileSync(path.join(hubDir, 'data.js'), dataJs(edge));
            await page.waitForFunction((r) => document.documentElement.dataset.rev === String(r), edge.revision, { timeout: 6000 }).catch(() => failures.push(`${tag}: hub-edge data not loaded`));
            const before = await page.locator('[data-stale]').innerText().catch(() => '');
            await page.waitForTimeout(11000);
            const after = await page.locator('[data-stale]').innerText().catch(() => '');
            if (!/so it is running/.test(before) || /so it is running/.test(after) || !/may have stopped/.test(after)) failures.push(`${tag}: hub sentence not re-decided over time ("${after.slice(-200)}")`);
          }
          // Adversarial long tokens in the board, topics and bead chips must wrap or truncate, not widen the page.
          const long = JSON.parse(JSON.stringify(snap)); long.revision += 7;
          long.mote.doing[0].tags = ['x'.repeat(140)]; long.mote.posts[0].topic = 't'.repeat(140);
          long.mote.posts[0].from = 'f'.repeat(120); long.mote.reservations[0].issue = 'bd-' + '9'.repeat(120);
          fs.writeFileSync(path.join(hubDir, 'data.js'), dataJs(long));
          await page.waitForFunction((r) => document.documentElement.dataset.rev === String(r), long.revision, { timeout: 6000 }).catch(() => failures.push(`${tag}: long-token data not loaded`));
          await page.evaluate(() => { for (const b of document.querySelectorAll('.rg-h[aria-expanded=false]')) b.click(); });
          await page.waitForTimeout(50);
          await pageChecks(page, long, tag + ' (long tokens)', failures);
        }
        if (size === 'mobile') {
          // Visual order must equal DOM (and so focus) order: brief, sessions, selected session, board.
          const order = await page.evaluate(() => ['#brief', '#lanes', '#main', '#rail'].map((q) => document.querySelector(q))
            .filter((el) => el && !el.hidden && getComputedStyle(el).display !== 'none' && el.getBoundingClientRect().height > 0)
            .map((el) => ({ id: el.id, y: el.getBoundingClientRect().top + scrollY })));
          for (let i = 1; i < order.length; i++) if (order[i].y < order[i - 1].y) failures.push(`${tag}: #${order[i].id} drawn above #${order[i - 1].id} but follows it in the DOM`);
        }
        if (name === 'slurm-long' && size === 'desktop' && theme === 'dark') {
          // File mode trusts the backend: 30-minute-old data with a long tool still running is not stale.
          const old = shift(raw, Date.now() - 30 * 60000 - Date.parse(raw.generated));
          old.revision += 1;
          fs.writeFileSync(path.join(hubDir, 'data.js'), dataJs(old));
          await page.waitForFunction((r) => document.documentElement.dataset.rev === String(r), old.revision, { timeout: 6000 }).catch(() => failures.push(`${tag}: old data not loaded`));
          if (await page.locator('[data-stale]').count()) failures.push(`${tag}: stale banner for a session running a long tool`);
          if (!(await page.locator('.now-el [data-el]').count()) || await page.locator('.now-el .lb, .now-el.dim').count()) failures.push(`${tag}: long-tool timer froze on quiet data`);
          // The agent's "≈1 h 20 m remaining" was written 82 min ago: it has passed and must say so.
          const liveHero = await page.locator('.now').innerText();
          if (/1 h 20 m remaining/.test(liveHero) || !/has passed/.test(liveHero)) failures.push(`${tag}: elapsed ETA shown as current ("${liveHero.slice(-160)}")`);
          if (!/data as of/.test(await page.locator('.conn').innerText())) failures.push(`${tag}: file mode does not say "data as of"`);
          // The real stale case: reported working, no tool running, no events past the stall threshold.
          const dead = JSON.parse(JSON.stringify(old)); dead.revision += 1; dead.sessions[0].current = null;
          fs.writeFileSync(path.join(hubDir, 'data.js'), dataJs(dead));
          await page.waitForSelector('[data-stale]', { timeout: 6000 }).catch(() => failures.push(`${tag}: no stale banner for a working session with no tool and no events`));
          if (!/as of|last event/.test(await page.locator('.now-state').innerText())) failures.push(`${tag}: stale session not labelled with its last event`);
          if (/^Working/.test(await page.locator('.now-label').innerText())) failures.push(`${tag}: stale hero still says "Working"`);
          const bigD = (await page.locator('.now-el').innerText()).split('\n')[0].trim();
          const nD = ((await page.locator('.now').innerText()).split(bigD).length - 1);
          if (nD !== 1) failures.push(`${tag}: stale hero states "${bigD}" ${nD} times`);
          await page.waitForTimeout(200);
          if (!/shown as stale/.test(await page.locator('#live-needs').textContent())) failures.push(`${tag}: going stale not announced`);
          await page.screenshot({ path: path.join(out, `${name}-${size}-${theme}-stale.png`), fullPage: false });
          // A tool "running" for 26 h with no hook events is past the trust ceiling: stale, dated, lower bounds, no pulse.
          const ancient = shift(raw, Date.now() - 26 * 3600e3 - Date.parse(raw.generated)); ancient.revision = dead.revision + 1;
          fs.writeFileSync(path.join(hubDir, 'data.js'), dataJs(ancient));
          await page.waitForFunction((r) => document.documentElement.dataset.rev === String(r), ancient.revision, { timeout: 6000 }).catch(() => failures.push(`${tag}: 26 h data not loaded`));
          if (!(await page.locator('[data-stale]').count())) failures.push(`${tag}: no stale banner for a tool silent for 26 h`);
          if (await page.locator('.dot.live').count()) failures.push(`${tag}: live pulse on 26 h old data`);
          const hero = await page.locator('.now').innerText();
          // Stale: the big figure is the silence, the verb is "last reported", and times carry the date.
          const big = await page.locator('.now-el').innerText();
          if (/^Working/.test(hero) || /running/.test(hero) || !/1d 2h/.test(big) || /≥/.test(big) || !/(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d+/.test(hero)) failures.push(`${tag}: 26 h stale hero wrong ("${hero.slice(0, 200)}")`);
          if (big.split('\n')[0].trim().split(' ')[0] !== (await page.locator('.slim-t').innerText()).trim()) failures.push(`${tag}: rail tile disagrees with the hero ("${await page.locator('.slim-t').innerText()}" vs "${big}")`);
          if (!/(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d+/.test(await page.locator('.conn').innerText())) failures.push(`${tag}: "data as of" has no date for yesterday's data`);
          // Stale sessions are counted apart ("1 stale"), never inside a green "working" total.
          if (!(await page.locator('.tally .t-stale').count()) || await page.locator('.tally .t-working').count()) failures.push(`${tag}: header does not split the stale session from working`);
          // Every live duration is frozen at a lower bound: plan doing time and the current turn too.
          const doingD = await page.locator('.task.doing .d').innerText().catch(() => '');
          const turnD = await page.locator('.turn .gap').first().innerText().catch(() => '');
          if (!/≥/.test(doingD) || !/≥/.test(turnD)) failures.push(`${tag}: plan/turn durations keep counting on stale data ("${doingD}", "${turnD}")`);
          if (!/(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d+/.test(await page.locator('.ev-t').first().innerText())) failures.push(`${tag}: yesterday's timeline times carry no date`);
          // An ETA from 26 h ago is not a countdown.
          if (/remaining|would have finished|≈ estimate/.test(hero) || !/no data since/.test(hero)) failures.push(`${tag}: stale ETA reads as a countdown or in the wrong tense`);
          await pageChecks(page, ancient, tag + ' (26 h)', failures);
          // The single-session tile keeps its lower bound on one line.
          const tile = await page.locator('.slim-t').evaluate((el) => ({ h: el.getBoundingClientRect().height, t: el.textContent }));
          if (tile.h > 18) failures.push(`${tag}: stale tile timer wraps ("${tile.t}", ${tile.h}px)`);
        }
        if (name === 'solo-rcheck' && size === 'desktop') {
          // The 64 px tile shows one coarse unit ("3m"), never "3m 12s" spilling over its edge.
          const tt = await page.locator('.slim-t').evaluate((el) => ({ t: el.textContent.trim(), over: el.scrollWidth > el.clientWidth + 1 }));
          if (/\s/.test(tt.t) || tt.over) failures.push(`${tag}: rail tile timer too wide ("${tt.t}")`);
        }
        if (name === 'solo-rcheck' && size === 'desktop' && theme === 'dark') {
          // Live update through data.js polling, same wall clock, new revision.
          const next = JSON.parse(JSON.stringify(snap));
          next.revision += 1;
          const s = next.sessions[0];
          s.events.push({ id: s.events[s.events.length - 1].id + 1, ts: new Date().toISOString(), kind: 'tool', tool: 'Read', summary: 'R/probe_update.R', detail: null, ok: true, duration_ms: 90, subagent: null });
          s.label = 'Updated through data.js';
          fs.writeFileSync(path.join(hubDir, 'data.js'), dataJs(next));
          await page.waitForFunction(() => document.body.innerText.includes('Updated through data.js') && document.body.innerText.includes('probe_update.R'), null, { timeout: 6000 })
            .catch(() => failures.push(`${tag}: data.js update not rendered within 6 s`));
          // Bursts must be real keyboard targets.
          const burst = page.locator('.burst-btn').first();
          if (await burst.count()) {
            await burst.focus();
            if (!(await burst.evaluate((el) => document.activeElement === el && el.getBoundingClientRect().height > 0))) failures.push(`${tag}: burst button not focusable`);
            await page.keyboard.press('Enter');
            if (!(await page.locator('.burst-list').count())) failures.push(`${tag}: burst did not expand from the keyboard`);
          } else failures.push(`${tag}: no burst rows rendered`);
          await page.keyboard.press('?');
          if (!(await page.locator('#keys').isVisible())) failures.push(`${tag}: ? did not open shortcuts`);
          await page.screenshot({ path: path.join(out, `${name}-${size}-${theme}-interact.png`), fullPage: false });
          // WCAG 2.1.4: single-key shortcuts can be turned off, and then do nothing.
          await page.locator('[data-act=keys-toggle]').click();
          await page.locator('#top [data-act=keys]').focus();
          const th0 = await page.evaluate(() => document.documentElement.dataset.theme);
          await page.keyboard.press('t');
          if (await page.evaluate(() => document.documentElement.dataset.theme) !== th0) failures.push(`${tag}: "t" still fires with shortcuts off`);
          await page.locator('[data-act=keys-toggle]').click();
          await page.keyboard.press('Escape');
        }
      } catch (e) { failures.push(`${tag}: ${e.message.split('\n')[0]}`); }
      finally { await ctx.close(); }
    }
  } finally { fs.rmSync(dir, { recursive: true, force: true }); }
}

// ---- server mode ----------------------------------------------------------------------
async function serverMode(browser, fixtures, out, failures) {
  const ORIGIN = 'http://127.0.0.1:47811';
  const TOKEN = 'tok-3f9a2c-test';
  const html = fs.readFileSync(PAGE, 'utf8');
  const tag = 'server';
  let hub = live(fixtures['needs-you']);
  const posts = [];
  let msgN = 100, failNext = false, slowNext = 0, freezeGen = false;
  const fileReqs = [];
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, colorScheme: 'dark' });
  try {
    await ctx.route(/^https?:\/\//, async (route) => {
      const req = route.request(), url = new URL(req.url());
      if (url.origin !== ORIGIN) { failures.push(`${tag}: unexpected request ${req.url()}`); return route.abort(); }
      if (url.pathname === '/' && req.method() === 'GET') return route.fulfill({ status: 200, contentType: 'text/html', body: html });
      if (!url.pathname.startsWith('/api/')) return route.fulfill({ status: 404, body: 'not found' });
      const tok = req.headers()['x-dash-token'];
      if (tok !== TOKEN) return route.fulfill({ status: 401, contentType: 'application/json', body: '{"error":"bad token"}' });
      if (url.pathname === '/api/file' && req.method() === 'GET') {
        fileReqs.push(url.searchParams.get('path'));
        return route.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: '<h1 id="rep">Coverage report</h1><script>try{parent.document.title="pwned"}catch(e){document.body.dataset.isolated="1"}</script>' });
      }
      if (url.pathname === '/api/hub' && req.method() === 'GET') {
        if (!freezeGen) hub.generated = new Date().toISOString();
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(hub) });
      }
      if (req.method() === 'POST') {
        let body = null;
        try { body = JSON.parse(req.postData() || 'null'); } catch (_) { failures.push(`${tag}: non-JSON POST body`); }
        if ((req.headers()['content-type'] || '').indexOf('application/json') !== 0) failures.push(`${tag}: POST without JSON content type`);
        posts.push({ path: url.pathname, body, token: tok });
        if (slowNext) { const d = slowNext; slowNext = 0; await new Promise((r) => setTimeout(r, d)); }
        if (failNext) { failNext = false; return route.fulfill({ status: 500, contentType: 'application/json', body: '{"error":"inbox write failed"}' }); }
        const id = 'm' + (++msgN);
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true, id, status: 'queued' }) });
      }
      return route.fulfill({ status: 405, body: '' });
    });
    const page = await ctx.newPage();
    page.on('pageerror', (e) => failures.push(`${tag}: ${e.message}`));
    page.on('console', (m) => { if (m.type() === 'error' && !/status of (401|500)/.test(m.text())) failures.push(`${tag}: console ${m.text()}`); });
    await page.goto(`${ORIGIN}/#k=${TOKEN}`);
    await page.waitForFunction(() => document.documentElement.dataset.ready === '1', null, { timeout: 5000 });
    if (page.url().includes('#k=') || page.url().includes(TOKEN)) failures.push(`${tag}: token left in the URL bar (${page.url()})`);
    if (await page.evaluate(() => sessionStorage.getItem('dash.token')) !== TOKEN) failures.push(`${tag}: token not stored in sessionStorage`);
    await page.waitForFunction(() => { const t = document.querySelector('textarea[data-composer]'); return t && !t.disabled; }, null, { timeout: 5000 })
      .catch(() => failures.push(`${tag}: composer not enabled in server mode`));
    const permSid = hub.sessions[0].id;

    // 1. composer: Enter sends kind=message
    const ta = page.locator('textarea[data-composer]');
    await ta.fill('Use the scratch copy, not the raw BIDS folder.');
    await ta.press('Enter');
    await page.waitForFunction(() => document.querySelector('.inbox .st.queued'), null, { timeout: 3000 }).catch(() => {});
    const m1 = posts.find((p) => p.path === `/api/sessions/${permSid}/messages`);
    if (!m1 || m1.body.kind !== 'message' || m1.body.text !== 'Use the scratch copy, not the raw BIDS folder.' || m1.token !== TOKEN) failures.push(`${tag}: composer POST wrong: ${JSON.stringify(m1)}`);
    if (!(await page.locator('.inbox .st.queued').count())) failures.push(`${tag}: optimistic queued status not shown`);
    if (await ta.inputValue() !== '') failures.push(`${tag}: composer not cleared after send`);
    // server confirms delivery via inbox
    hub = JSON.parse(JSON.stringify(hub)); hub.revision += 1;
    hub.sessions[0].inbox = [{ id: 'm101', ts: new Date().toISOString(), kind: 'message', text: m1 ? m1.body.text : '', qid: null, status: 'delivered', delivered: new Date().toISOString(), via: 'PostToolUse' }];
    await page.waitForFunction(() => document.querySelector('.inbox .st.delivered'), null, { timeout: 5000 })
      .catch(() => failures.push(`${tag}: delivered status from snapshot inbox not shown`));
    if (await page.locator('.inbox .msg').count() !== 1) failures.push(`${tag}: pending message not reconciled with inbox (duplicates)`);

    // 1b. a rejected send keeps the draft and offers a retry
    failNext = true;
    await ta.fill('This one fails first.');
    await ta.press('Enter');
    await page.waitForSelector('.inbox .st.failed [data-act=retry]', { timeout: 3000 }).catch(() => failures.push(`${tag}: failed send shows no Retry`));
    if (await ta.inputValue() !== 'This one fails first.') failures.push(`${tag}: draft cleared although the send failed`);
    await page.locator('.inbox [data-act=retry]').click().catch(() => {});
    await page.waitForFunction(() => !document.querySelector('.inbox .st.failed'), null, { timeout: 3000 }).catch(() => failures.push(`${tag}: retry did not resend`));
    await page.waitForFunction(() => !document.querySelector('.inbox .st.sending'), null, { timeout: 3000 }).catch(() => {});
    if (posts.filter((p) => p.body && p.body.text === 'This one fails first.').length !== 2) failures.push(`${tag}: retry POST count wrong`);
    await ta.fill('');

    // 1c. no duplicate sends while one is in flight
    slowNext = 700;
    await ta.fill('Only once, please.');
    await ta.press('Enter');
    await ta.press('Enter');
    await page.waitForTimeout(1100);
    const once = posts.filter((p) => p.body && p.body.text === 'Only once, please.').length;
    if (once !== 1) failures.push(`${tag}: double Enter sent ${once} POSTs (last posts: ${JSON.stringify(posts.slice(-3).map((p) => p.body && p.body.text))}; value=${JSON.stringify(await ta.inputValue())})`);

    // 2. inline answer with explicit text, and use-default
    const q1 = page.locator('form[data-form=answer][data-qid=Q1]');
    await q1.locator('input').fill('8 mm');
    await q1.getByRole('button', { name: 'Answer' }).click();
    await page.waitForTimeout(300);
    const a1 = posts.find((p) => p.body && p.body.kind === 'answer' && p.body.qid === 'Q1');
    if (!a1 || a1.body.text !== '8 mm' || a1.path !== `/api/sessions/${permSid}/messages`) failures.push(`${tag}: answer POST wrong: ${JSON.stringify(a1)}`);
    if (await page.locator('form[data-form=answer][data-qid=Q2] button', { hasText: 'Use default' }).count()) failures.push(`${tag}: Use default shown for a question without default`);
    if (await page.locator('form[data-form=answer][data-qid=Q1]').count()) failures.push(`${tag}: answered question still shows answer controls`);
    const band = await page.locator('#needs').innerText();
    if (!/Q1 answered “8 mm”/.test(band)) failures.push(`${tag}: answered question not noted as answered`);
    const nTop = await page.locator('.need-tally b').innerText().catch(() => '0'), nBand = await page.locator('.needs-h .n').innerText().catch(() => '0');
    if (nTop !== '4' || nBand !== '4' || !/^\(4\)/.test(await page.title())) failures.push(`${tag}: answered question still counted (top ${nTop}, band ${nBand}, title ${await page.title()})`);
    // wakeable null: a reply waits for the next prompt, and the card says so
    if (!/next prompt/.test(await page.locator('#needs .need.k-waiting').innerText())) failures.push(`${tag}: non-wakeable waiting card does not say "next prompt"`);
    // wakeable null is unknown: never claim it can't be woken
    if (/can.t be woken/.test(await page.locator('body').innerText())) failures.push(`${tag}: page claims a session can't be woken`);

    // 3. draft, focus and caret survive a new revision
    await ta.fill('Keep my draft');
    await ta.evaluate((el) => { el.focus(); el.setSelectionRange(2, 7); });
    hub = JSON.parse(JSON.stringify(hub)); hub.revision += 1;
    const s0 = hub.sessions[0];
    s0.events.push({ id: s0.events[s0.events.length - 1].id + 1, ts: new Date().toISOString(), kind: 'note', tool: null, summary: 'Revision probe arrived', detail: null, ok: null, duration_ms: null, subagent: null });
    s0.label = '<img src=x onerror="window.__injected=1">HRF sweep';
    await page.waitForFunction(() => document.body.innerText.includes('Revision probe arrived'), null, { timeout: 5000 })
      .catch(() => failures.push(`${tag}: revision update not rendered`));
    const f = await page.evaluate(() => ({ v: document.activeElement.value, a: document.activeElement.selectionStart, b: document.activeElement.selectionEnd, c: !!document.activeElement.dataset.composer }));
    if (!f.c || f.v !== 'Keep my draft' || f.a !== 2 || f.b !== 7) failures.push(`${tag}: update lost composer focus/draft/caret ${JSON.stringify(f)}`);
    if (await page.evaluate(() => Boolean(window.__injected) || !!document.querySelector('img[src="x"]'))) failures.push(`${tag}: snapshot text injected HTML`);
    await pageChecks(page, hub, tag, failures);
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: path.join(out, 'server-needs-you-desktop-dark.png'), fullPage: true });

    // 4. pause / resume
    await page.keyboard.press('Escape');
    await page.locator('.sess-actions button[data-act=pause]').click();
    await page.waitForTimeout(250);
    if (!posts.some((p) => p.path === `/api/sessions/${permSid}/pause`)) failures.push(`${tag}: pause POST missing`);
    hub = JSON.parse(JSON.stringify(hub)); hub.revision += 1; hub.sessions[0].paused = true; hub.sessions[0].activity = 'paused';
    await page.waitForSelector('.sess-actions button[data-act=resume]:not([disabled])', { timeout: 5000 }).catch(() => failures.push(`${tag}: resume button did not appear`));
    await page.locator('.sess-actions button[data-act=resume]').click().catch(() => {});
    await page.waitForTimeout(250);
    if (!posts.some((p) => p.path === `/api/sessions/${permSid}/resume`)) failures.push(`${tag}: resume POST missing`);
    // 4b. a failed pause says so and stays visible
    hub = JSON.parse(JSON.stringify(hub)); hub.revision += 1; hub.sessions[0].paused = false; hub.sessions[0].activity = 'waiting_permission';
    await page.waitForSelector('.sess-actions button[data-act=pause]:not([disabled])', { timeout: 5000 }).catch(() => failures.push(`${tag}: pause button did not return`));
    failNext = true;
    await page.locator('.sess-actions button[data-act=pause]').click().catch(() => {});
    await page.waitForSelector('.pause-note', { timeout: 3000 }).catch(() => {});
    const pn = await page.locator('.pause-note').innerText().catch(() => '');
    if (!/Pause failed/.test(pn)) failures.push(`${tag}: refused pause not reported as failed ("${pn}")`);

    // 5. board post (trio-mote has a mote store)
    hub = live(fixtures['trio-mote']); hub.revision += 1000;
    await page.waitForFunction(() => document.querySelector('form[data-form=mote] textarea:not([disabled])'), null, { timeout: 5000 })
      .catch(() => failures.push(`${tag}: board composer not enabled`));
    await page.locator('#mote\\:topic').fill('perf');
    await page.locator('#mote\\:post').fill('contrast_rsa C++ port: 6.1x faster, 37/37 equivalent.');
    await page.getByRole('button', { name: 'Post', exact: true }).click();
    await page.waitForTimeout(300);
    const mp = posts.find((p) => p.path === '/api/mote/post');
    if (!mp || mp.body.topic !== 'perf' || !/6\.1x/.test(mp.body.text) || mp.token !== TOKEN) failures.push(`${tag}: board POST wrong: ${JSON.stringify(mp)}`);
    // conflicts: every involved agent is listed, live ones get Message and Pause
    const conflict = page.locator('#needs .need.k-conflict');
    const parties = await conflict.locator('.parties li').count();
    if (parties !== 3) failures.push(`${tag}: conflict lists ${parties} agents, expected 3 (two editors and the Codex post)`);
    if (!/Port contrast_rsa/.test(await conflict.innerText())) failures.push(`${tag}: conflict omits the Codex agent named in the board post`);
    if (await conflict.locator('[data-act=reply]').count() !== 3 || await conflict.locator('[data-act=pause]').count() !== 2) failures.push(`${tag}: conflict actions wrong (want Message x3, Pause x2 for Claude sessions)`);
    // idle session delivery hint
    await page.locator('[data-lane="3d07b5e2-9a4c-4e11-b7a0-6f2d1c88e412"]').click();
    const hint = await page.locator('.composer-wrap .hint').innerText();
    if (!/Wakes the session/.test(hint)) failures.push(`${tag}: wakeable idle session hint missing ("${hint}")`);
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: path.join(out, 'server-trio-desktop-dark.png'), fullPage: true });
    // wakeable false: the watcher record is stale, so nothing on the page may promise a wake-up
    hub = JSON.parse(JSON.stringify(hub)); hub.revision += 1;
    hub.sessions.find((x) => x.short === '3d07').wakeable = false;
    const cx = hub.sessions.find((x) => x.agent === 'codex'); cx.wakeable = true; cx.activity = 'idle';
    await page.waitForFunction(() => /isn.t responding/.test(document.querySelector('.composer-wrap .hint').innerText), null, { timeout: 5000 })
      .catch(() => failures.push(`${tag}: wakeable false hint missing`));
    const wf = await page.locator('#main').innerText() + await page.locator('#lanes').innerText();
    if (/wakes (it|on message|the session)|Wakes the session/.test(wf)) failures.push(`${tag}: wake claimed with wakeable false or for a Codex session`);
    await page.waitForTimeout(100);
    // Stale server data with wakeable true: the watcher can't be confirmed; never "No inbox watcher is recorded".
    hub = JSON.parse(JSON.stringify(hub)); hub.revision += 1; hub.sessions.find((x) => x.short === '3d07').wakeable = true;
    hub.generated = new Date(Date.now() - 5 * 60000).toISOString(); freezeGen = true;
    await page.waitForFunction(() => /can.t be confirmed/.test(document.querySelector('.composer-wrap .hint').innerText), null, { timeout: 5000 })
      .catch(() => failures.push(`${tag}: stale wakeable:true hint not worded as unconfirmed`));
    if (/No inbox watcher is recorded/.test(await page.locator('#main').innerText())) failures.push(`${tag}: stale wakeable:true says no watcher is recorded`);
    // Five-minute-old server data: no lane may claim a silence of mere seconds.
    const lanesS = await page.locator('#lanes').innerText();
    if (/no events for (\d+s|[0-4]m)\b/.test(lanesS)) failures.push(`${tag}: stale server lanes understate the silence ("${lanesS.replace(/\s+/g, ' ').slice(0, 200)}")`);
    freezeGen = false;

    // 5b. deliverables open through the token-gated /api/file, HTML inside a sandboxed frame
    hub = live(fixtures['done']); hub.revision += 2000;
    await page.waitForSelector('.now-deliv .linkbtn', { timeout: 5000 }).catch(() => failures.push(`${tag}: server-mode deliverable button missing`));
    const [popup] = await Promise.all([ctx.waitForEvent('page', { timeout: 5000 }), page.locator('.now-deliv .linkbtn').first().click()]).catch(() => [null]);
    if (!popup) failures.push(`${tag}: deliverable did not open a tab`);
    else {
      const frame = await popup.waitForSelector('iframe[sandbox]', { timeout: 5000 }).catch(() => null);
      if (!frame) failures.push(`${tag}: HTML deliverable not framed in a sandbox`);
      else {
        const inner = await (await frame.contentFrame()).waitForSelector('#rep', { timeout: 5000 }).catch(() => null);
        if (!inner) failures.push(`${tag}: deliverable content not shown`);
        if (await popup.title() === 'pwned') failures.push(`${tag}: deliverable script reached the opener tab`);
      }
      if (fileReqs[fileReqs.length - 1] !== hub.sessions[0].plan.deliverables[0].path) failures.push(`${tag}: /api/file asked for ${fileReqs[fileReqs.length - 1]}`);
      await popup.close();
    }
    if (!(await page.locator('.now-deliv [data-act=copy]').count())) failures.push(`${tag}: Copy path missing next to deliverables`);

    // 6. wrong token shows a clear error and disables writing
    await page.evaluate(() => sessionStorage.setItem('dash.token', 'wrong'));
    await page.goto(`${ORIGIN}/`);
    await page.waitForFunction(() => document.body.innerText.includes('rejected'), null, { timeout: 5000 })
      .catch(() => failures.push(`${tag}: rejected token not explained`));
  } catch (e) { failures.push(`${tag}: ${e.message.split('\n')[0]}`); }
  finally { await ctx.close(); }
}

(async () => {
  const args = process.argv.slice(2);
  let out = null, only = null, server = true;
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--out') out = args[++i];
    else if (args[i] === '--only') only = args[++i].split(',');
    else if (args[i] === '--skip-server') server = false;
    else throw new Error(`Unknown argument: ${args[i]}`);
  }
  out = path.resolve(out || fs.mkdtempSync(path.join(os.tmpdir(), 'dash-shots-')));
  if (out.startsWith(SKILL + path.sep) || out === SKILL) throw new Error('--out must be outside the skill folder');
  fs.mkdirSync(out, { recursive: true });
  const fixtures = {};
  for (const f of fs.readdirSync(FIXTURES).filter((f) => f.endsWith('.json')).sort()) fixtures[f.replace(/\.json$/, '')] = JSON.parse(fs.readFileSync(path.join(FIXTURES, f), 'utf8'));
  const names = Object.keys(fixtures).filter((n) => !only || only.includes(n));
  if (!names.length) throw new Error('No fixtures selected');
  const { chromium } = loadPlaywright();
  const failures = [];
  let browser;
  audit('before');
  try {
    browser = await launch(chromium);
    for (const name of names) await fileMode(browser, name, fixtures[name], out, failures);
    if (server) await serverMode(browser, fixtures, out, failures);
  } finally {
    try { if (browser) await browser.close(); } finally { audit('after'); }
  }
  console.log(`screenshots: ${out}`);
  if (failures.length) { console.error(failures.map((f) => `FAIL ${f}`).join('\n')); process.exitCode = 1; return; }
  console.log(`ok: ${names.length} specimens (${[...GATE_ONLY].join(', ')} gate-only) x ${THEMES.length} themes x ${SIZES.length} sizes${server ? ' + server-mode interactions' : ''}`);
})().catch((e) => { console.error(`render: ${e.message}`); process.exitCode = 1; });
