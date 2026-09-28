// node scripts/shoot.js ROUND -> immutable shots/ROUND/{name}-{fold,full}.png
const path = require('node:path'), fs = require('node:fs');
const L = require('./lib.js');
(async () => {
  const round = L.identifier(process.argv[2]);
  const cfg = L.config(), out = path.join(L.H, 'out', round);
  if (!Array.isArray(cfg.shots) || !cfg.shots.length) throw new Error('No shots configured');
  const names = new Set();
  const shots = cfg.shots.map(shot => {
    const name = L.identifier(shot.name);
    if (names.has(name)) throw new Error('Duplicate shot: ' + name);
    names.add(name);
    const viewport = L.viewport(typeof shot.vp === 'string' ? (cfg.viewports || {})[shot.vp] : shot.vp);
    const wait = shot.wait === undefined ? 800 : shot.wait;
    if (!Number.isFinite(wait) || wait < 0) throw new Error('Invalid capture wait');
    return { ...shot, name, viewport, wait, file: L.localFile(out, shot.file) };
  });
  const root = path.join(L.H, 'shots');
  fs.mkdirSync(root, { recursive: true });
  if (fs.realpathSync(root) !== path.resolve(root)) throw new Error('shots must not be a symlink');
  const dir = path.join(root, round);
  fs.mkdirSync(dir); // refuses existing evidence, including partial prior captures
  const browser = await L.launch();
  try {
    for (const shot of shots) {
      const context = await browser.newContext({ viewport: shot.viewport, colorScheme: shot.dark ? 'dark' : 'light', deviceScaleFactor: 1 });
      try {
        const page = await context.newPage();
        const errors = [];
        page.on('pageerror', e => errors.push(e.message));
        await page.goto(L.url(shot.file), { waitUntil: 'load', timeout: 30000 });
        await page.waitForFunction(() => !document.fonts || document.fonts.status === 'loaded', { }, { timeout: 30000 });
        await page.waitForTimeout(shot.wait);
        if (errors.length) throw new Error('Page errors: ' + errors.join('; '));
        await page.screenshot({ path: path.join(dir, shot.name + '-fold.png') });
        await page.screenshot({ path: path.join(dir, shot.name + '-full.png'), fullPage: true });
        console.log('shot ' + shot.name);
      } finally { await context.close(); }
    }
  } finally { await browser.close(); }
})().catch(L.fail);
