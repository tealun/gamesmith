#!/usr/bin/env node
// Draw the plugin icon in code and save it as assets/gamesmith-icon.png (512×512 PNG; the plugin directory reads
// `icon` from plugin.json at submission). Run only when the icon changes; needs Playwright with Chromium.
// The picture follows the skill's own visual language: a block hero mid-jump over a red-edged hazard, a gold coin
// on the jump arc, and a yellow-edged platform it can land on.
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const out = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../assets/gamesmith-icon.png');

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 512, height: 512 }, deviceScaleFactor: 1 });
await page.setContent('<!doctype html><body style="margin:0;background:transparent"><canvas id="c" width="512" height="512"></canvas></body>');
await page.evaluate(() => {
  const g = document.getElementById('c').getContext('2d');
  const rr = (x, y, w, h, r) => { g.beginPath(); g.roundRect(x, y, w, h, r); };
  // background tile
  const bg = g.createLinearGradient(0, 0, 0, 512);
  bg.addColorStop(0, '#1b2a6b'); bg.addColorStop(1, '#0a0f2e');
  rr(0, 0, 512, 512, 96); g.fillStyle = bg; g.fill();
  g.save(); rr(0, 0, 512, 512, 96); g.clip();
  g.strokeStyle = 'rgba(111,211,255,0.10)'; g.lineWidth = 2;
  for (let i = 32; i < 512; i += 48) { g.beginPath(); g.moveTo(i, 0); g.lineTo(i, 512); g.stroke(); g.beginPath(); g.moveTo(0, i); g.lineTo(512, i); g.stroke(); }
  // ground
  g.fillStyle = '#0d1640'; g.fillRect(0, 392, 512, 120);
  g.shadowColor = '#6fd3ff'; g.shadowBlur = 18; g.strokeStyle = '#6fd3ff'; g.lineWidth = 6;
  g.beginPath(); g.moveTo(0, 392); g.lineTo(512, 392); g.stroke();
  // hazard: dark spikes with a red edge
  g.shadowColor = '#ff4d6d'; g.shadowBlur = 22; g.fillStyle = '#2a0f18'; g.strokeStyle = '#ff4d6d'; g.lineWidth = 6; g.lineJoin = 'round';
  g.beginPath(); g.moveTo(196, 392); g.lineTo(222, 336); g.lineTo(248, 392); g.lineTo(274, 336); g.lineTo(300, 392); g.closePath(); g.fill(); g.stroke();
  // platform with a yellow edge
  g.shadowColor = '#ffe14d'; g.shadowBlur = 18; g.fillStyle = '#243a7a'; g.strokeStyle = '#ffe14d';
  rr(352, 300, 120, 92, 14); g.fill(); g.stroke();
  // jump arc
  g.shadowBlur = 0; g.setLineDash([14, 14]); g.strokeStyle = 'rgba(255,255,255,0.55)'; g.lineWidth = 5;
  g.beginPath(); g.moveTo(92, 330); g.quadraticCurveTo(250, 40, 412, 290); g.stroke(); g.setLineDash([]);
  // coin on the arc
  g.shadowColor = '#ffd34d'; g.shadowBlur = 26; g.fillStyle = '#ffd34d';
  g.beginPath(); g.arc(330, 168, 26, 0, Math.PI * 2); g.fill();
  g.shadowBlur = 0; g.fillStyle = '#fff3b0'; g.beginPath(); g.arc(322, 160, 9, 0, Math.PI * 2); g.fill();
  // hero: a rounded orange block mid-jump, tilted forward, with eyes
  g.save(); g.translate(176, 168); g.rotate(-0.18);
  g.shadowColor = '#ff9f1c'; g.shadowBlur = 24; g.fillStyle = '#ff9f1c'; rr(-56, -56, 112, 112, 26); g.fill();
  g.shadowBlur = 0; g.lineWidth = 7; g.strokeStyle = '#7a3b00'; rr(-56, -56, 112, 112, 26); g.stroke();
  g.fillStyle = '#ffffff'; g.beginPath(); g.arc(-14, -10, 15, 0, 7); g.arc(28, -10, 15, 0, 7); g.fill();
  g.fillStyle = '#1a1a2e'; g.beginPath(); g.arc(-8, -8, 7, 0, 7); g.arc(34, -8, 7, 0, 7); g.fill();
  g.fillStyle = '#7a3b00'; g.beginPath(); g.arc(10, 22, 12, 0, Math.PI); g.fill();
  g.restore();
  // speed lines
  g.strokeStyle = 'rgba(111,211,255,0.7)'; g.lineWidth = 6; g.lineCap = 'round';
  for (const [x, y, l] of [[44, 140, 56], [60, 178, 40], [40, 214, 50]]) { g.beginPath(); g.moveTo(x, y); g.lineTo(x + l, y); g.stroke(); }
  g.restore();
});
await page.locator('#c').screenshot({ path: out, omitBackground: true });
await browser.close();
console.log('wrote', out);
