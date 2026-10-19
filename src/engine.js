/* Strata engine: slices outlines into layered lines, dots or bars and returns SVG path data. */
const Strata = (() => {
  const LETTER = new Set(['Numbers', 'Uppercase', 'Lowercase']);
  const LS = 0.86, BASE = 76;            // letters: scale + baseline inside the 100 box
  const r2 = v => Math.round(v * 100) / 100;

  function bbox(groups) {
    let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
    for (const g of groups) for (const r of g) for (let i = 0; i < r.length; i += 2) {
      if (r[i] < x0) x0 = r[i]; if (r[i] > x1) x1 = r[i];
      if (r[i + 1] < y0) y0 = r[i + 1]; if (r[i + 1] > y1) y1 = r[i + 1];
    }
    return [x0, y0, x1, y1];
  }
  const xf = (rings, s, tx, ty) => rings.map(r => { const a = new Array(r.length); for (let i = 0; i < r.length; i += 2) { a[i] = r[i] * s + tx; a[i + 1] = r[i + 1] * s + ty; } return a; });

  // place one symbol in the 100 x 100 tile; returns groups of rings
  function tile(sym, G) {
    const rings = sym.ch ? G[sym.ch].r : sym.r;
    if (!rings.length) return [];
    if (LETTER.has(sym.c)) {
      const [x0, , x1] = bbox([rings]);
      return [xf(rings, LS, 50 - (x0 + x1) / 2 * LS, BASE)];
    }
    const [x0, y0, x1, y1] = bbox([rings]);
    const md = Math.max(x1 - x0, y1 - y0);
    let s = md < 56 ? 56 / md : 1;
    if (md * s > 86) s = 86 / md;
    return [xf(rings, s, 50 - (x0 + x1) / 2 * s, 50 - (y0 + y1) / 2 * s)];
  }

  // lay out a string; returns {groups, width}
  function word(text, G, tracking = 0) {
    const groups = []; let x = 0;
    for (const ch of text) {
      const g = G[ch] || G[ch.toUpperCase()];
      if (!g) { x += 22 * LS; continue; }
      if (g.r.length) groups.push(xf(g.r, LS, x, BASE));
      x += g.a * LS + tracking;
    }
    return { groups, width: Math.max(1, x - tracking) };
  }

  function rotGroups(groups, th, cx, cy) {
    if (!th) return groups;
    const c = Math.cos(-th), s = Math.sin(-th);
    return groups.map(g => g.map(r => { const a = new Array(r.length); for (let i = 0; i < r.length; i += 2) { const x = r[i] - cx, y = r[i + 1] - cy; a[i] = x * c - y * s + cx; a[i + 1] = x * s + y * c + cy; } return a; }));
  }

  function scan(groups, y) {
    let all = [];
    for (const g of groups) {
      const xs = [];
      for (const r of g) {
        const n = r.length;
        for (let i = 0; i < n; i += 2) {
          const x1 = r[i], y1 = r[i + 1], j = (i + 2) % n, x2 = r[j], y2 = r[j + 1];
          if ((y1 <= y && y2 > y) || (y2 <= y && y1 > y)) xs.push(x1 + (y - y1) * (x2 - x1) / (y2 - y1));
        }
      }
      xs.sort((a, b) => a - b);
      for (let i = 0; i + 1 < xs.length; i += 2) all.push([xs[i], xs[i + 1]]);
    }
    if (groups.length > 1 && all.length > 1) {      // union overlapping letters
      all.sort((a, b) => a[0] - b[0]);
      const m = [all[0].slice()];
      for (let i = 1; i < all.length; i++) { const l = m[m.length - 1]; if (all[i][0] <= l[1]) l[1] = Math.max(l[1], all[i][1]); else m.push(all[i].slice()); }
      all = m;
    }
    return all;
  }

  /* o: {n, ratio, angle, cap, fx, snap}; returns {d, grad:[x1,y1,x2,y2]} */
  function build(groups, o, cx = 50, cy = 50) {
    if (!groups.length) return { d: '', grad: [cx, 0, cx, 100] };
    const th = (o.angle || 0) * Math.PI / 180;
    const R = rotGroups(groups, th, cx, cy);
    const [, ymin, , ymax] = bbox(R);
    const pitch = 100 / o.n, H = pitch * o.ratio;
    const k0 = Math.floor((ymin - cy) / pitch) - 1, k1 = Math.ceil((ymax - cy) / pitch) + 1;
    const rowsFor = off => { const rows = []; for (let k = k0; k <= k1; k++) { const y = cy + off + k * pitch; const segs = scan(R, y); if (segs.length) rows.push({ k, y, segs }); } return rows; };

    let rows, best = 1e9;
    const cands = o.snap === false ? [0] : [0, -1, 1, -2, 2, -3, 3, 4].map(i => i * pitch / 8);
    for (const off of cands) {
      const rs = rowsFor(off);
      let score = Math.abs(off) / pitch * 0.4;
      for (const r of rs) for (const [a, b] of r.segs) { const w = b - a; if (w < 2 * H) score += 1 + (2 * H - w) / H; }
      if (score < best - 1e-6) { best = score; rows = rs; }
    }

    const c = Math.cos(th), s = Math.sin(th);
    const P = (x, y) => { const dx = x - cx, dy = y - cy; return r2(dx * c - dy * s + cx) + ' ' + r2(dx * s + dy * c + cy); };
    const span = Math.max(1e-6, ymax - ymin);
    const out = [];
    const round = o.cap !== 'square';
    for (const row of rows) {
      let h = H, shift = 0;
      if (o.fx === 'fade') h = H * (1 - 0.8 * Math.min(1, Math.max(0, (row.y - ymin) / span)));
      if (o.fx === 'shift') shift = (row.k % 2 ? 1 : -1) * pitch * 0.42;
      if (h < 0.18) continue;
      const r = h / 2, y = row.y;
      for (let [a, b] of row.segs) {
        a += shift; b += shift;
        if (o.fx === 'dots') {
          const j0 = Math.ceil((a - cx) / pitch - 1e-6), j1 = Math.floor((b - cx) / pitch + 1e-6);
          for (let j = j0; j <= j1; j++) {
            const x = cx + j * pitch + (row.k % 2 ? pitch / 2 : 0) * 0;
            if (x < a - 0.01 || x > b + 0.01) continue;
            if (round) out.push(`M${P(x - r, y)}A${r2(r)} ${r2(r)} 0 1 0 ${P(x + r, y)}A${r2(r)} ${r2(r)} 0 1 0 ${P(x - r, y)}Z`);
            else out.push(`M${P(x - r, y - r)}L${P(x + r, y - r)}L${P(x + r, y + r)}L${P(x - r, y + r)}Z`);
          }
          continue;
        }
        let w = b - a;
        if (w < h * 0.95) continue;
        if (w < h) { const m = (a + b) / 2; a = m - h / 2; b = m + h / 2; w = h; }
        if (round) out.push(`M${P(a + r, y - r)}L${P(b - r, y - r)}A${r2(r)} ${r2(r)} 0 0 1 ${P(b - r, y + r)}L${P(a + r, y + r)}A${r2(r)} ${r2(r)} 0 0 1 ${P(a + r, y - r)}Z`);
        else out.push(`M${P(a, y - r)}L${P(b, y - r)}L${P(b, y + r)}L${P(a, y + r)}Z`);
      }
    }
    const g1 = P(cx, ymin).split(' ').map(Number), g2 = P(cx, ymax).split(' ').map(Number);
    return { d: out.join(''), grad: [...g1, ...g2] };
  }
  return { tile, word, build, LETTER };
})();
if (typeof module !== 'undefined') module.exports = Strata;
