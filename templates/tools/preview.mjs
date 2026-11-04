#!/usr/bin/env node
// Engine-free preview (template): render every chunk with the solver's most forgiving route in a headless browser
// and save PNGs, so an AI assistant in a cloud container (no editor) can "see" content and reviewers get stable shots.
//   node tools/preview.mjs <output dir> [chunkId]
// Needs Playwright with Chromium. In a real project, bundle your view layer (esbuild) + a canvas stand-in for the
// engine sprite host instead of the inline drawing below, and add modes such as `ui` (all screens) and `shots`.
import { readFileSync, readdirSync, mkdirSync } from 'node:fs';
import { createRequire } from 'node:module';
import path from 'node:path';
import { Sim, DT, START_X, buildConfig } from '../core/sim.mjs';
import { solveChunk } from './solve.mjs';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const out = path.resolve(process.argv[2] || 'preview_out'), only = process.argv[3];
const D = new URL('../config/', import.meta.url).pathname;
const r = f => JSON.parse(readFileSync(D + f, 'utf8'));
const cfg = buildConfig({ player: r('player.json'), entities: r('entities.json'), levels: r('levels.json'), solver: r('solver.json'),
  chunks: readdirSync(D + 'chunks').filter(f => f.endsWith('.json')).map(f => r('chunks/' + f)) });

/** Replay a route and sample the player's path (chunk-relative). */
function trace(chunk, speed, acts) {
  const g = new Sim(cfg, chunk, { speed }), pts = [];
  let i = 0, rel = 0, k = 0;
  const RELEASE = { tap: 11, hold: 24 };
  while (g.p.x < g.goalX && k < 20000) {
    while (i < acts.length && acts[i].step <= k) { g.pressJump(); rel = RELEASE[acts[i++].a]; }
    if (rel > 0 && --rel === 0) g.releaseJump();
    g.step(); k++;
    if (k % 4 === 0) pts.push([g.p.x - START_X, g.p.y]);
  }
  return pts;
}

mkdirSync(out, { recursive: true });
const browser = await chromium.launch(), page = await browser.newPage({ viewport: { width: 1600, height: 400 } });
const errs = [];
page.on('pageerror', e => errs.push(e.message));
page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
await page.setContent('<!doctype html><body style="margin:0;background:#111"><canvas id="c" width="1600" height="400"></canvas></body>');
for (const c of cfg.chunks) {
  if (only && c.id !== only) continue;
  const speed = cfg.solver.speed[c.difficulty] ?? cfg.player.speed, res = solveChunk(cfg, c, speed);
  const kinds = Object.fromEntries(cfg.entities.entities.map(e => [e.id, e]));
  const ents = c.entities.map(e => ({ ...e, kind: kinds[e.ref].kind, w: e.w ?? kinds[e.ref].w ?? 0, h: e.h ?? kinds[e.ref].h ?? 0, y: e.y ?? 0 }));
  const path_ = res.ok ? trace(c, speed, res.route) : [];
  await page.evaluate(({ c, ents, path_, ok }) => {
    const cv = document.getElementById('c'), g = cv.getContext('2d'), sx = cv.width / c.lengthPx, GY = 360, Y = y => GY - y * sx;
    g.fillStyle = '#0d1b2a'; g.fillRect(0, 0, cv.width, cv.height);
    g.fillStyle = 'rgba(255,255,255,0.06)'; g.fillRect(0, 0, c.safeHeadPx * sx, GY); g.fillRect((c.lengthPx - c.safeTailPx) * sx, 0, c.safeTailPx * sx, GY);
    g.strokeStyle = '#6fd3ff'; g.lineWidth = 2; g.beginPath(); g.moveTo(0, GY); g.lineTo(cv.width, GY); g.stroke();
    for (const e of ents) {
      if (e.kind === 'coin') { g.fillStyle = '#ffd34d'; g.beginPath(); g.arc(e.x * sx, Y(e.y), 6, 0, 7); g.fill(); continue; }
      g.fillStyle = e.kind === 'spike' ? '#2a0f18' : '#1e3a5f';
      g.strokeStyle = e.kind === 'spike' ? '#ff4d6d' : '#6fd3ff';          // visual language: red edge = danger
      g.fillRect(e.x * sx, Y(e.y + e.h), e.w * sx, e.h * sx); g.strokeRect(e.x * sx, Y(e.y + e.h), e.w * sx, e.h * sx);
    }
    g.strokeStyle = '#ff9f1c'; g.lineWidth = 2; g.beginPath();
    path_.forEach(([x, y], i) => (i ? g.lineTo : g.moveTo).call(g, x * sx, Y(y + 30)));
    g.stroke();
    g.fillStyle = '#fff'; g.font = '20px sans-serif'; g.fillText(`${c.id}  d${c.difficulty}  ${ok ? 'solver route' : 'NO ROUTE'}`, 12, 28);
  }, { c, ents, path_, ok: res.ok });
  const file = path.join(out, `${c.id}.png`);
  await page.screenshot({ path: file });
  console.log('preview', file, res.ok ? `(${res.acts.length} actions, window ${res.windowMs} ms)` : '(no route)');
}
await browser.close();
if (errs.length) { console.error('page errors:\n' + errs.join('\n')); process.exit(1); }
