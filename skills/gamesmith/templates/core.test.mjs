// Rule tests for the template core (node --test core.test.mjs). One test per rule; one regression test per playtest bug,
// named after the symptom and the date it was found.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { Sim, DT } from './sim.mjs';
import { solveChunk, loadConfig } from './solve.mjs';

const cfg = loadConfig();
const empty = (lengthPx = 1600) => ({ id: 'test_d1_00', difficulty: 1, lengthPx, safeHeadPx: 0, safeTailPx: 0, entities: [] });
const run = (g, sec) => { for (let i = 0; i < Math.round(sec / DT); i++) g.step(); };

test('input buffer: a jump pressed just before landing fires on landing', () => {
  const g = new Sim({ ...cfg, player: { ...cfg.player, maxJumps: 1 } }, empty());   // no air jump: the press must wait
  g.pressJump(); g.step(); g.releaseJump();
  while (g.p.vy > 0 || g.p.y > 20) g.step();          // falling, a few px above the ground
  g.pressJump(); g.releaseJump(); g.step();
  assert.equal(g.events.filter(e => e.type === 'jump').length, 1, 'not yet: still in the air');
  run(g, 0.05);
  assert.equal(g.events.filter(e => e.type === 'jump').length, 2);
});

test('coyote time: a jump just after running off an edge is still a ground jump', () => {
  const chunk = { ...empty(), entities: [{ type: 'terrain', ref: 'T01_block', x: 0, w: 320, h: 64 }] };
  const g = new Sim(cfg, chunk);
  g.p.x = 300; g.p.y = 64;                              // standing on the block
  while (g.p.grounded) g.step();                        // runs off the edge
  run(g, 0.04);                                         // 40 ms < coyoteMs
  g.pressJump(); g.step();
  assert.equal(g.p.jumpsUsed, 1);
  assert.ok(g.p.vy > cfg.player.jumpVelocity * 0.9);
});

test('a block side bonks instead of hurting', () => {
  const g = new Sim(cfg, { ...empty(), entities: [{ type: 'terrain', ref: 'T01_block', x: 64, w: 64, h: 128 }] });
  run(g, 1);
  assert.ok(g.bonks > 0);
  assert.equal(g.p.hp, cfg.player.hp);
});

test('the solver rejects a chunk that cannot be cleared', () => {
  const wall = { ...empty(), entities: [{ type: 'terrain', ref: 'T01_block', x: 320, w: 64, h: 640 }] };
  assert.equal(solveChunk(cfg, wall, 620).ok, false);
});

test('every demo chunk clears unhurt', () => {
  for (const c of cfg.chunks) assert.ok(solveChunk(cfg, c, cfg.solver.speed[c.difficulty]).ok, c.id);
});

// Guard for an ES5 build pitfall: some mini-game builds compile [...new Set(x)] into [Set] (an array holding the Set).
test('no spread or for-of over a Set/Map in shipped code', () => {
  const shipped = ['sim.mjs'];                          // code that goes into the engine build (the core)
  const bad = [];
  for (const f of shipped) {
    readFileSync(new URL(f, import.meta.url), 'utf8').split('\n').forEach((line, i) => {
      if (/\[\.\.\.new (Set|Map)\b|\.\.\.(\w+\.)?(keys|values|entries)\(\)|for\s*\(\s*const\s+\w+\s+of\s+\w+\.(keys|values|entries)\(\)/.test(line)) bad.push(`${f}:${i + 1}`);
    });
  }
  assert.deepEqual(bad, []);
});
