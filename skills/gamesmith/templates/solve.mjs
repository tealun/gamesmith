#!/usr/bin/env node
// Chunk solver (template): beam search over inputs on the REAL core to accept or reject every chunk.
//   node solve.mjs                 all chunks; exit 1 if one misses a line in solver.json
//   node solve.mjs <chunkId>       one chunk, with its input timeline and per-action timing windows
//   node solve.mjs 'demo_*'        every chunk with that prefix
// Lines: (1) clears without damage or wall bonks; (2) actions per second of the cheapest clear >= minActionsPerSec;
// (3) the tightest timing window on the most forgiving clear >= minWindowMs.
import { readFileSync, readdirSync } from 'node:fs';
import { Sim, DT, buildConfig } from './sim.mjs';

/** Read the config tables that sit next to this file (chunk libraries are chunks_<scene>.json). */
export function loadConfig(dir = new URL('./', import.meta.url).pathname) {
  const r = f => JSON.parse(readFileSync(dir + f, 'utf8'));
  return buildConfig({ player: r('player.json'), entities: r('entities.json'), levels: r('levels.json'), solver: r('solver.json'),
    chunks: readdirSync(dir).filter(f => /^chunks_.*\.json$/.test(f)).sort().map(r) });
}

const STEPS = 6;                                   // one decision every 0.05 s
const RELEASE = { tap: 11, hold: 24 };             // ~90 ms tap, ~200 ms hold (in simulation steps)
const SHIFT = 30, PROBE = 3;                       // timing windows probed up to ±0.25 s in 25 ms steps

function key(n) {
  const p = n.g.p;
  return [Math.round(p.y / 3), Math.round(p.vy / 40), p.jumpsUsed, p.grounded ? 1 : 0, n.release > 0 ? 1 : 0].join(',');
}
/** Advance one decision; null when anything is lost (damage or bonk). */
function advance(n, a) {
  const g = n.g.clone();
  let release = n.release;
  if (a) { g.pressJump(); release = RELEASE[a]; }
  for (let i = 0; i < STEPS; i++) {
    if (release > 0 && --release === 0) g.releaseJump();
    const hp = g.p.hp, bonks = g.bonks;
    g.step();
    if (g.p.hp < hp || g.bonks !== bonks) return null;
  }
  return { g, release, steps: n.steps + STEPS, acts: a ? [...n.acts, { step: n.steps, t: +(n.steps * DT).toFixed(2), a }] : n.acts };
}
export function search(start, goal, { beam = 300, want = 3 } = {}) {
  let nodes = [start], best = start.g.p.x;
  const found = [];
  while (nodes.length && found.length < want) {
    const next = new Map();
    for (const n of nodes) for (const a of [null, 'tap', 'hold']) {
      const m = advance(n, a);
      if (!m) continue;
      best = Math.max(best, m.g.p.x);
      if (m.g.p.x >= goal) { found.push(m); continue; }
      const k = key(m), old = next.get(k);
      if (!old || m.acts.length < old.acts.length || (m.acts.length === old.acts.length && m.g.coins > old.g.coins)) next.set(k, m);
    }
    // keep the beam diverse: a quota for each of the four lowest action counts, so natural routes survive
    const sorted = [...next.values()].sort((x, y) => x.acts.length - y.acts.length || y.g.coins - x.g.coins);
    const low = sorted.length ? sorted[0].acts.length : 0, quota = Math.floor(beam / 4), taken = new Map();
    nodes = [];
    for (const m of sorted) { const c = m.acts.length - low, t = taken.get(c) ?? 0; if (c < 4 && t < quota) { nodes.push(m); taken.set(c, t + 1); } }
    for (const m of sorted) { if (nodes.length >= beam) break; if (m.acts.length - low >= 4) nodes.push(m); }
  }
  // a whole beam can arrive in the same decision: keep the cheapest few (most coins first)
  found.sort((x, y) => x.acts.length - y.acts.length || y.g.coins - x.g.coins);
  return { found: found.slice(0, want), best };
}
/** Replay acts exactly until `until` steps; null if anything is lost on the way. */
function playTo(cfg, chunk, speed, acts, until) {
  const g = new Sim(cfg, chunk, { speed }), order = [...acts].sort((x, y) => x.step - y.step);
  let i = 0, rel = 0, k = 0;
  while (k < until) {
    while (i < order.length && order[i].step <= k) { g.pressJump(); rel = RELEASE[order[i++].a]; }
    if (rel > 0 && --rel === 0) g.releaseJump();
    const hp = g.p.hp, bonks = g.bonks;
    g.step(); k++;
    if (g.p.hp < hp || g.bonks !== bonks) return null;
  }
  return { g, release: rel, steps: k, acts: [] };
}
/** Window of each action for a player who adapts: shift it early/late, then look for a way on through the next 1.5 s. */
export function windows(cfg, chunk, speed, acts) {
  const goalAll = new Sim(cfg, chunk).goalX;
  return acts.map((act, i) => {
    const ok = d => {
      const at = act.step + d; if (at < 0) return false;
      const n = playTo(cfg, chunk, speed, [...acts.slice(0, i), { ...act, step: at }], at + 1);
      if (!n) return false;
      const goal = Math.min(goalAll, n.g.p.x + speed * 1.5);
      return n.g.p.x >= goal || search(n, goal, { beam: 40, want: 1 }).found.length > 0;
    };
    let lo = 0, hi = 0;
    while (lo < SHIFT && ok(-(lo + PROBE))) lo += PROBE;
    while (hi < SHIFT && ok(hi + PROBE)) hi += PROBE;
    return Math.round((lo + hi + 1) * DT * 1000);
  });
}
export function solveChunk(cfg, chunk, speed) {
  const g = new Sim(cfg, chunk, { speed });
  const { found, best } = search({ g, release: 0, steps: 0, acts: [] }, g.goalX);
  if (!found.length) return { ok: false, reachedPx: Math.round(best - 300) };
  let pick = found[0], pickW = [], pickMin = -1;
  for (const f of found) {
    const w = windows(cfg, chunk, speed, f.acts), m = w.length ? Math.min(...w) : 9999;
    if (m > pickMin) { pick = f; pickW = w; pickMin = m; }
  }
  const secs = (chunk.lengthPx - chunk.safeHeadPx - chunk.safeTailPx) / speed;
  return { ok: true, acts: found[0].acts, perSec: found[0].acts.length / secs, windowMs: pickMin, route: pick.acts, windows: pickW, coins: pick.g.coins };
}

// ---------------- CLI ----------------
if (import.meta.url === `file://${process.argv[1]}`) {
  const cfg = loadConfig();
  const only = process.argv[2], many = !!only && only.endsWith('*'), L = cfg.solver;
  let bad = 0, n = 0;
  for (const c of cfg.chunks) {
    if (only && (many ? !c.id.startsWith(only.slice(0, -1)) : c.id !== only)) continue;
    n++;
    const d = String(c.difficulty), speed = L.speed[d] ?? cfg.player.speed, t0 = Date.now(), res = solveChunk(cfg, c, speed), issues = [];
    if (!res.ok) issues.push(`cannot clear (stuck at ${res.reachedPx} px)`);
    else {
      if (res.perSec < (L.minActionsPerSec[d] ?? 0)) issues.push(`density ${res.perSec.toFixed(2)} < ${L.minActionsPerSec[d]}`);
      if (res.windowMs < (L.minWindowMs[d] ?? 0)) issues.push(`window ${res.windowMs} ms < ${L.minWindowMs[d]}`);
    }
    if (issues.length) bad++;
    console.log(`${issues.length ? 'BAD' : 'OK '} ${c.id} @${speed}  ${res.ok ? `actions ${res.acts.length} (${res.perSec.toFixed(2)}/s) window ${res.windowMs} ms coins ${res.coins}` : ''}  ${issues.join('; ')}  ${Date.now() - t0} ms`);
    if (only && !many && res.ok) console.log('most forgiving route: ' + res.route.map((x, i) => `${x.t}s ${x.a}(${res.windows[i]}ms)`).join('  '));
  }
  if (!n) { console.error(`no chunk matches ${only}`); process.exit(2); }
  if (!only || many) { console.log(bad ? `\n${bad} chunk(s) below the lines` : '\nall chunks pass'); process.exit(bad ? 1 : 0); }
}
