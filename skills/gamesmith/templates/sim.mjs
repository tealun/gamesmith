// Minimal engine-independent runner core (template). Pure JS/ESM: no engine, no platform globals, fixed step,
// deterministic. Copy the idea, not the numbers: your own game replaces this file with its real rules.
//
//   const g = new Sim(cfg, chunk, { speed: 620 });
//   g.pressJump(); for (let i = 0; i < 12; i++) g.step(); g.releaseJump();
//   g.events → [{ t, type: 'jump' | 'land' | 'bonk' | 'hurt' | 'coin' | 'clear' }]
//
// Coordinates: x grows to the right, y is height above the ground (0), entities are { x, y, w, h } boxes.

export const DT = 1 / 120;
export const START_X = 300;                       // chunk starts this far ahead of the player
const PW = 40, PH = 60, COIN_R = 16;

export class Sim {
  constructor(cfg, chunk, opts = {}) {
    this.P = cfg.player;
    this.kinds = Object.fromEntries(cfg.entities.entities.map(e => [e.id, e]));
    this.chunk = chunk;
    this.speed = opts.speed ?? this.P.speed;
    this.t = 0;
    this.p = { x: 0, y: 0, vy: 0, grounded: true, lastGround: 0, jumpsUsed: 0, holding: false, holdStart: -1, bufferUntil: -1, hp: this.P.hp, invUntil: -1 };
    // entities are shared and never mutated (cheap clones for the solver); collected coins live in a Set of indexes
    this.ents = chunk.entities.map(e => {
      const k = this.kinds[e.ref];
      return { kind: k.kind, ref: e.ref, x: START_X + e.x, y: e.y ?? 0, w: e.w ?? k.w ?? 0, h: e.h ?? k.h ?? 0 };
    });
    this.got = new Set();
    this.coins = 0;
    this.bonks = 0;
    this.events = [];
    this.cleared = false;
  }

  clone() {
    const c = Object.create(Sim.prototype);
    Object.assign(c, this);
    c.p = { ...this.p };
    c.got = new Set(this.got);
    c.events = [];
    return c;
  }

  get goalX() { return START_X + this.chunk.lengthPx; }
  get dead() { return this.p.hp <= 0; }

  pressJump() { this.p.bufferUntil = this.t + this.P.inputBufferMs / 1000; this.p.holding = true; }
  releaseJump() { this.p.holding = false; }

  emit(type) { this.events.push({ t: +this.t.toFixed(3), type }); }

  step() {
    const p = this.p, P = this.P;
    this.t += DT;
    // jump: input buffer + coyote time + air jumps
    if (p.bufferUntil >= this.t) {
      const canGround = p.grounded || (this.t - p.lastGround <= P.coyoteMs / 1000 && p.jumpsUsed === 0);
      if (canGround) { p.vy = P.jumpVelocity; p.jumpsUsed = 1; p.grounded = false; p.bufferUntil = -1; p.holdStart = this.t; this.emit('jump'); }
      else if (p.jumpsUsed < P.maxJumps) { p.vy = P.jumpVelocity * P.airJumpRatio; p.jumpsUsed = Math.max(p.jumpsUsed, 1) + 1; p.bufferUntil = -1; p.holdStart = this.t; this.emit('jump'); }
    }
    // vertical: gravity is lighter while the button is held on the way up (hold to jump higher)
    if (!p.grounded) {
      const held = p.holding && p.vy > 0 && this.t - p.holdStart < P.holdMaxMs / 1000;
      p.vy -= P.gravity * (held ? P.holdGravityFactor : 1) * DT;
      const oldY = p.y;
      p.y += p.vy * DT;
      for (const e of this.ents) {
        if (e.kind !== 'block' || p.x + PW <= e.x || p.x >= e.x + e.w) continue;
        const top = e.y + e.h;
        if (p.vy <= 0 && oldY >= top - 1e-6 && p.y < top) { p.y = top; this.land(); }
        else if (p.vy > 0 && oldY + PH <= e.y + 1e-6 && p.y + PH > e.y) { p.y = e.y - PH; p.vy = 0; }   // head bump
      }
      if (p.y <= 0) { p.y = 0; this.land(); }
    }
    // horizontal: run forward; the side of a block bonks (no damage, but a fair chunk flows without one)
    p.x += this.speed * DT;
    let support = p.y === 0;
    for (const e of this.ents) {
      if (e.kind !== 'block') continue;
      const overlapX = p.x + PW > e.x && p.x < e.x + e.w, top = e.y + e.h;
      if (overlapX && p.y < top - 1e-6 && p.y + PH > e.y) { p.x = e.x - PW; this.bonks++; this.emit('bonk'); }
      if (overlapX && Math.abs(p.y - top) < 1e-6) support = true;
    }
    if (p.grounded && !support) { p.grounded = false; p.lastGround = this.t; p.vy = 0; }   // ran off an edge: coyote time starts
    // spikes and coins
    for (let i = 0; i < this.ents.length; i++) {
      const e = this.ents[i];
      if (e.kind === 'spike' && this.t > p.invUntil && p.x + PW > e.x && p.x < e.x + e.w && p.y < e.y + e.h && p.y + PH > e.y) {
        p.hp--; p.invUntil = this.t + P.invincibleMs / 1000; this.emit('hurt');
      } else if (e.kind === 'coin' && !this.got.has(i)) {
        const cx = Math.max(p.x, Math.min(e.x, p.x + PW)), cy = Math.max(p.y, Math.min(e.y, p.y + PH));
        if ((cx - e.x) ** 2 + (cy - e.y) ** 2 <= COIN_R * COIN_R) { this.got.add(i); this.coins++; this.emit('coin'); }
      }
    }
    if (!this.cleared && p.x >= this.goalX) { this.cleared = true; this.emit('clear'); }
  }

  land() {
    const p = this.p;
    if (!p.grounded) this.emit('land');
    p.vy = 0; p.grounded = true; p.jumpsUsed = 0; p.lastGround = this.t;
  }
}

/** Assemble the config object the core expects from the JSON tables (one place, shared by tools and the engine shell). */
export function buildConfig(tables) {
  return { player: tables.player, entities: tables.entities, chunks: tables.chunks.flatMap(c => c.chunks), levels: tables.levels, solver: tables.solver };
}
