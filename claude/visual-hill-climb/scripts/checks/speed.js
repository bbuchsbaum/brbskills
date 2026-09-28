// Example local speed budget at 1x CPU; fixed windows, not Lighthouse TBT:
//   load <= 1500 ms, first contentful paint <= 1000 ms, longest task <= 600 ms,
//   observed blocking sum (time past 50 ms per task) <= 1000 ms,
//   and after a resize (the other width) longest task <= 1000 ms, blocking <= 800 ms.
// usage: node speed.js "<file>;..." [widths=390,1440]
// On a shared/loaded machine absolute times drift 2-3x: always run the previous round's
// build back to back and compare, not just against the budget.
const L = require("../lib.js");
(async () => {
  const { files, widths } = L.inputs(process.argv[2], process.argv[3]);
  const b = await L.launch(); let bad = 0;
  const tbt = a => a.reduce((s, d) => s + Math.max(0, d - 50), 0);
  try {
    for (const f of files) for (const w of widths) {
      const ctx = await b.newContext({ viewport: { width: w, height: 800 } });
      try {
      await ctx.addInitScript(() => {
        window.__supported = PerformanceObserver.supportedEntryTypes.includes("longtask");
        window.__lt = [];
        try { new PerformanceObserver(l => l.getEntries().forEach(e => window.__lt.push(e.duration))).observe({ type: "longtask", buffered: true }); } catch (e) { window.__supported = false; }
      });
      const p = await ctx.newPage();
      const errors = []; p.on("pageerror", e => errors.push(e.message));
      const t0 = Date.now(); const response = await p.goto(L.url(f), { waitUntil: "load", timeout: 30000 });
      if (response && !response.ok()) throw new Error("HTTP " + response.status()); const tl = Date.now() - t0;
      await p.waitForTimeout(2500);
      const r = await p.evaluate(() => ({ supported: window.__supported, lt: window.__lt.slice(), fcp: Math.round((performance.getEntriesByName("first-contentful-paint")[0] || {}).startTime || -1) }));
      await p.evaluate(() => { window.__lt.length = 0; });
      await p.setViewportSize({ width: widths.find(x => x !== w) || w, height: 800 });
      await p.waitForTimeout(1500);
      const rz = await p.evaluate(() => window.__lt.slice());
      const mx = Math.max(0, ...r.lt), rmx = Math.max(0, ...rz), lb = tbt(r.lt), rb = tbt(rz);
      if (!r.supported) throw new Error("longtask observation unsupported");
      if (errors.length) throw new Error("Page errors: " + errors.join("; "));
      const ok = mx <= 600 && tl <= 1500 && r.fcp >= 0 && r.fcp <= 1000 && lb <= 1000 && rmx <= 1000 && rb <= 800;
      if (!ok) bad++;
      console.log(`speed ${f.split("/").slice(-2).join("/")} @${w}: load=${tl}ms FCP=${r.fcp}ms longest=${mx}ms observed-blocking=${lb}ms resize-longest=${rmx}ms resize-observed-blocking=${rb}ms -> ${ok ? "PASS" : "FAIL"}`);
      } finally { await ctx.close(); }
    }
  } finally { await b.close(); }
  process.exitCode = bad ? 1 : 0;
})().catch(L.fail);
