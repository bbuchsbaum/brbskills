// Synthetic browser acceptance check. Requires installed Playwright + Chromium.
// Caller runs the environment's browser-policy audit before/after. No server.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { pathToFileURL } = require('node:url');
const { spawnSync } = require('node:child_process');
const skill = path.resolve(__dirname, '..');
const evidence = process.env.VHC_EVIDENCE_DIR || fs.mkdtempSync(path.join(os.tmpdir(), 'vhc-browser-'));
fs.mkdirSync(evidence, { recursive: true });
const harness = fs.mkdtempSync(path.join(evidence, 'harness-'));
process.env.HARNESS = harness;
const L = require('../scripts/lib.js');
const python = process.env.PYTHON || 'python3';
const cfg = { title: 'Synthetic visual review', dims: ['layout', 'function'],
  critics: { visual: 'Visual', user: 'Target user' },
  viewports: { desktop: { width: 1440, height: 1000 } },
  shots: [{ name: 'home', file: 'index # Ω.html', vp: 'desktop', wait: 0 }] };
fs.writeFileSync(path.join(harness, 'hillclimb.json'), JSON.stringify(cfg));
fs.mkdirSync(path.join(harness, 'critiques'));
fs.mkdirSync(path.join(harness, 'artifact'));
fs.copyFileSync(path.join(skill, 'assets/progress-page/index.html'), path.join(harness, 'artifact/index.html'));
function run(program, args, expected = 0) {
  const result = spawnSync(program, args, { env: process.env, encoding: 'utf8', timeout: 45000 });
  fs.appendFileSync(path.join(evidence, 'commands.log'), JSON.stringify({ program, args, status: result.status, stdout: result.stdout, stderr: result.stderr }) + '\n');
  assert.equal(result.status, expected, result.error?.message || result.stderr || result.stdout);
  return result;
}
function update(round, ...args) { return run(python, [path.join(skill, 'scripts/update_data.py'), round, ...args]); }
function review(round, critic, score = 8) {
  fs.writeFileSync(path.join(harness, `critiques/${round}-${critic}.md`),
    `## Scores\n| dimension | score | why |\n| --- | --- | --- |\n| layout | ${score} | observed |\n| function | ${score} | tested |\n` +
    ['Previous round', 'Claims', 'Issues', 'Regressions', 'Proposals'].map(h => `\n## ${h}\nNone in this fixture.\n`).join('') +
    '\n<img src=x onerror="window.INJECTED=true"> <script>window.INJECTED=true</script>\n');
}
(async () => {
  // Exercise capture with encoded paths, immutable rounds, image prep and real web gates.
  const build = path.join(harness, 'out/v0'); fs.mkdirSync(build, { recursive: true });
  const specimen = path.join(build, cfg.shots[0].file);
  fs.writeFileSync(specimen, '<!doctype html><html lang="en"><meta charset="utf-8"><title>Fixture</title><h1>Stable specimen</h1><p>Fixed input for capture and initial-window probes.</p>');
  run('node', [path.join(skill, 'scripts/shoot.js'), 'v0']);
  const original = fs.readFileSync(path.join(harness, 'shots/v0/home-fold.png'));
  run('node', [path.join(skill, 'scripts/shoot.js'), 'v0'], 1);
  assert.deepEqual(fs.readFileSync(path.join(harness, 'shots/v0/home-fold.png')), original);
  run('bash', [path.join(skill, 'scripts/prep_shots.sh'), 'v0']);
  run('node', [path.join(skill, 'scripts/checks/cls.js'), specimen, '390']);
  run('node', [path.join(skill, 'scripts/checks/speed.js'), specimen, '390,1440']);
  // Negative controls: actual runtime error and unsupported observation must fail.
  const broken = path.join(build, 'broken.html');
  fs.writeFileSync(broken, '<h1>Broken</h1><script>throw new Error("fixture runtime failure")</script>');
  run('node', [path.join(skill, 'scripts/checks/cls.js'), broken, '390'], 1);
  run('node', [path.join(skill, 'scripts/checks/speed.js'), broken, '390'], 1);
  const unsupported = path.join(build, 'unsupported.html');
  fs.writeFileSync(unsupported, '<h1>Unsupported observation</h1><script>window.__supported=false</script>');
  run('node', [path.join(skill, 'scripts/checks/cls.js'), unsupported, '390'], 1);
  run('node', [path.join(skill, 'scripts/checks/speed.js'), unsupported, '390'], 1);
  const browser = await L.launch();
  try {
    const context = await browser.newContext();
    try {
      const page = await context.newPage(), errors = [], external = [];
      page.on('pageerror', e => errors.push(e.message));
      page.on('request', r => { if (/^https?:/.test(r.url())) external.push(r.url()); });
      const url = pathToFileURL(path.join(harness, 'artifact/index.html')).href;
      await page.goto(url);
      assert.match(await page.locator('#status').innerText(), /No round data/);
      // A round with no screenshots and missing reviewers must render without crashing.
      update('v1', '--no-images');
      await page.reload();
      assert.match(await page.locator('#stage').innerText(), /No complete image sets/);
      assert.equal(await page.locator('.avg').count(), 0);
      review('v1', 'visual', 1);
      update('v1', '--no-images');
      await page.reload();
      assert.equal(await page.locator('.avg').count(), 0);
      assert.match(await page.locator('.round').innerText(), /Review pending: user/);
      // Complete baseline, lossless images and offline critiques, with no injected HTML.
      review('v0', 'visual'); review('v0', 'user'); update('v0');
      await page.reload();
      await page.locator('details summary').first().click();
      assert.match(await page.locator('.md pre').first().innerText(), /onerror/);
      assert.equal(await page.evaluate(() => window.INJECTED), undefined);
      assert.equal(await page.locator('#stage img').count(), 2);
      assert(await page.locator('#stage img').evaluateAll(imgs => imgs.every(i => i.complete && i.naturalWidth > 0)));
      const slider = page.getByRole('slider');
      await slider.focus(); await page.keyboard.press('ArrowRight');
      assert.equal(await slider.inputValue(), '51');
      await page.getByRole('button', { name: 'Side by side' }).click();
      assert.equal(await page.locator('.side img').count(), 2);
      for (const width of [390, 1440]) {
        await page.setViewportSize({ width, height: 1000 });
        for (const theme of ['light', 'dark']) {
          await page.emulateMedia({ colorScheme: theme, reducedMotion: 'reduce' });
          assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `Horizontal overflow at ${width}`);
          await page.screenshot({ path: path.join(evidence, `progress-${width}-${theme}.png`), fullPage: true });
        }
      }
      assert.deepEqual(errors, []);
      assert.deepEqual(external, []);
      // Labels remain inert even when data contains markup.
      const payloadPath = path.join(harness, 'artifact/data.json');
      const payload = JSON.parse(fs.readFileSync(payloadPath));
      payload.meta.dims[0] = '<img src=x onerror="window.INJECTED=true">';
      fs.writeFileSync(path.join(harness, 'artifact/data.js'), 'window.HILLCLIMB_DATA=' + JSON.stringify(payload));
      await page.reload();
      assert.equal(await page.locator('#heat img').count(), 0);
      assert.equal(await page.evaluate(() => window.INJECTED), undefined);
      fs.writeFileSync(path.join(evidence, 'result.json'), JSON.stringify({ passed: true, playwright: require(process.env.PLAYWRIGHT_MODULE ? path.join(process.env.PLAYWRIGHT_MODULE, 'package.json') : 'playwright/package.json').version, browser: browser.version(), harness, checks: 'capture, immutable images, gate success/negative controls, offline/no-images/pending/complete, inert markup, keyboard slider, responsive light/dark' }, null, 2));
    } finally { await context.close(); }
  } finally { await browser.close(); }
  console.log('Browser smoke passed. Evidence: ' + evidence);
})().catch(error => { console.error(error); process.exitCode = 1; });
