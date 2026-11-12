const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
const NS = 'http://www.w3.org/2000/svg';
const el = (tag, a = {}, p) => { const e = document.createElementNS(NS, tag); for (const k in a) e.setAttribute(k, a[k]); if (p) p.appendChild(e); return e; };
const txt = (p, s, a) => { const t = el('text', a, p); t.textContent = s; return t; };
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const sgn = v => (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v).toFixed(1) + '%';

/* progress bar + contents highlight */
(() => {
  const bar = document.getElementById('progress');
  const onScroll = () => { const h = document.documentElement; bar.style.transform = `scaleX(${h.scrollTop / Math.max(1, h.scrollHeight - h.clientHeight)})`; };
  addEventListener('scroll', onScroll, { passive: true }); onScroll();
  const links = [...document.querySelectorAll('.toc a')];
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) links.forEach(l => l.classList.toggle('on', l.getAttribute('href') === '#' + e.target.id)); }), { rootMargin: '-30% 0px -60% 0px' });
    document.querySelectorAll('article > section').forEach(s => io.observe(s));
  }
})();

/* hero smog: slow drifting fog banks carried by the wind, with fine particulate dust */
(() => {
  const c = document.getElementById('haze'), x = c.getContext('2d'); let W, H, P = [], F = [], m = { x: -999, y: -999 }; const dpr = Math.min(devicePixelRatio || 1, 2);
  const size = () => { const r = c.getBoundingClientRect(); W = r.width; H = r.height; c.width = W * dpr; c.height = H * dpr; x.setTransform(dpr, 0, 0, dpr, 0, 0);
    F = Array.from({ length: Math.round(Math.min(26, 8 + W / 70)) }, () => ({ x: Math.random() * W, y: Math.random() * H, r: 90 + Math.random() * 220, vx: .08 + Math.random() * .22, a: .10 + Math.random() * .16, p: Math.random() * 6.28 }));
    P = Array.from({ length: Math.round(Math.min(320, W * H / 3200)) }, () => ({ x: Math.random() * W, y: Math.random() * H, r: .4 + Math.random() * 1.6, vx: .1 + Math.random() * .35, vy: (Math.random() - .5) * .12, a: .12 + Math.random() * .4, p: Math.random() * 6.28 })); };
  const frame = () => { x.clearRect(0, 0, W, H); const fog = css('--fog'), dust = css('--muted');
    for (const f of F) { if (!reduce) { f.p += .004; f.x += f.vx; f.y += Math.sin(f.p) * .12; if (f.x - f.r > W) { f.x = -f.r; f.y = Math.random() * H; } }
      const g = x.createRadialGradient(f.x, f.y, 0, f.x, f.y, f.r); g.addColorStop(0, fog); g.addColorStop(1, 'transparent');
      x.globalAlpha = f.a; x.fillStyle = g; x.fillRect(f.x - f.r, f.y - f.r, f.r * 2, f.r * 2); }
    x.fillStyle = dust;
    for (const p of P) { if (!reduce) { p.p += .01; p.x += p.vx + Math.sin(p.p) * .12; p.y += p.vy + Math.cos(p.p * .8) * .08;
        const dx = p.x - m.x, dy = p.y - m.y, d2 = dx * dx + dy * dy; if (d2 < 16900) { const d = Math.sqrt(d2) || 1, k = (130 - d) / 130 * 2.4; p.x += dx / d * k; p.y += dy / d * k; }
        if (p.x > W + 10) p.x = -10; if (p.x < -10) p.x = W + 10; if (p.y < -10) p.y = H + 10; if (p.y > H + 10) p.y = -10; }
      x.globalAlpha = p.a; x.beginPath(); x.arc(p.x, p.y, p.r, 0, 6.283); x.fill(); }
    x.globalAlpha = 1; if (!reduce) requestAnimationFrame(frame); };
  const h = c.parentElement; h.addEventListener('pointermove', e => { const r = c.getBoundingClientRect(); m.x = e.clientX - r.left; m.y = e.clientY - r.top; });
  h.addEventListener('pointerleave', () => { m.x = m.y = -999; }); addEventListener('resize', () => { size(); if (reduce) frame(); }); size(); requestAnimationFrame(frame);
})();
const C = { up: 'var(--haze)', smoke: 'var(--smoke)', clean: 'var(--clean)', muted: 'var(--muted)', ink: 'var(--ink)', line: 'var(--line)' };
const clear = s => { while (s.firstChild) s.removeChild(s.firstChild); };
const replayFig = f => { f.classList.remove('play', 'armed'); void f.offsetWidth; f.classList.add('play'); };
const grid = (svg, Y, ticks, L, R, fmt = v => v) => ticks.forEach(v => {
  el('line', { x1: L, x2: R, y1: Y(v), y2: Y(v), stroke: v === 0 ? 'var(--ink)' : 'var(--line)' }, svg);
  txt(svg, fmt(v), { x: L - 8, y: Y(v) + 4, 'text-anchor': 'end', 'font-size': 11, fill: 'var(--muted)' }); });
const toggle = (fig, attr, draw) => { const bs = [...fig.querySelectorAll(`.toggle [${attr}]`)];
  bs.forEach(b => b.addEventListener('click', () => { bs.forEach(x => x.setAttribute('aria-pressed', x === b)); draw(b.getAttribute(attr)); replayFig(fig); }));
  draw(bs[0].getAttribute(attr)); };
const drawLine = p => { const len = p.getTotalLength(); p.style.setProperty('--len', len); p.style.strokeDasharray = len; };
const fmtDay = (start, i) => new Date(Date.parse(start + 'T00:00:00Z') + i * 864e5).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', timeZone: 'UTC' });

/* hero CI (percent share) */
(() => {
  const s = document.getElementById('heroci'), L = 20, R = 360, X = v => L + (R - L) * v / 35;
  [0, 10, 20, 30].forEach(v => { el('line', { x1: X(v), x2: X(v), y1: 14, y2: 46, stroke: v === 0 ? 'var(--ink)' : 'var(--line)' }, s); txt(s, v + '%', { x: X(v), y: 64, 'text-anchor': 'middle', 'font-size': 11, fill: 'var(--muted)' }); });
  const w = el('line', { x1: X(HERO.lo), x2: X(HERO.hi), y1: 30, y2: 30, stroke: 'var(--haze)', 'stroke-width': 5, 'stroke-linecap': 'round', class: 'anim gx' }, s); w.style.animationDelay = '.5s';
  const g = el('g', { class: 'anim pop' }, s); g.style.animationDelay = '1.1s';
  el('rect', { x: X(HERO.share) - 8, y: 22, width: 16, height: 16, transform: `rotate(45 ${X(HERO.share)} 30)`, fill: 'var(--haze)', stroke: 'var(--panel)', 'stroke-width': 2 }, g);
  document.getElementById('hero-fig').classList.add('play');
})();

/* season timeline */
(() => {
  const fig = document.getElementById('tl-fig'), svg = document.getElementById('tl');
  toggle(fig, 'data-y', y => {
    clear(svg); const d = D.tl[y], n = d.pm.length, L = 44, R = 884, T = 18, B = 236;
    const max = Math.max(500, Math.ceil(Math.max(...d.pm.filter(v => v != null)) / 100) * 100), umax = Math.max(1, ...d.up.filter(v => v != null));
    const X = i => L + (R - L) * i / (n - 1), Y = v => B - (B - T) * v / max, bw = (R - L) / n;
    grid(svg, Y, [0, 100, 200, 300, 400, 500, 600].filter(v => v <= max), L, R);
    d.up.forEach((u, i) => { if (!u) return; const h = (B - T) * .55 * u / umax; const r = el('rect', { x: X(i) - bw * .4, y: B - h, width: bw * .8, height: h, fill: C.smoke, 'fill-opacity': .35, class: 'anim gy' }, svg); r.style.animationDelay = (i / n * 1.4) + 's'; });
    el('line', { x1: L, x2: R, y1: Y(250), y2: Y(250), stroke: 'var(--muted)', 'stroke-dasharray': '4 4' }, svg);
    txt(svg, '250 severe', { x: L + 6, y: Y(250) - 6, 'font-size': 11, fill: 'var(--muted)' });
    const nov = Math.round((Date.parse(y + '-11-01') - Date.parse(d.start)) / 864e5);
    el('line', { x1: X(nov), x2: X(nov), y1: T, y2: B, stroke: C.clean, 'stroke-dasharray': '2 3' }, svg); txt(svg, '1 Nov', { x: X(nov) + 4, y: T + 26, 'font-size': 11, fill: C.clean });
    d.grap.forEach(i => { el('line', { x1: X(i), x2: X(i), y1: T, y2: B, stroke: C.clean, 'stroke-width': 2 }, svg); txt(svg, 'GRAP III', { x: X(i) + 4, y: T + 42, 'font-size': 11, 'font-weight': 600, fill: C.clean }); });
    let dd = '', pen = false; d.pm.forEach((v, i) => { if (v == null) { pen = false; return; } dd += (pen ? 'L' : 'M') + X(i).toFixed(1) + ' ' + Y(v).toFixed(1); pen = true; });
    const line = el('path', { d: dd, class: 'line', fill: 'none', stroke: 'var(--haze)', 'stroke-width': 2.2, 'stroke-linejoin': 'round' }, svg); drawLine(line);
    [0, 16, 46, 77].forEach(i => txt(svg, fmtDay(d.start, i), { x: X(i), y: B + 20, 'text-anchor': i ? 'middle' : 'start', 'font-size': 11, fill: 'var(--muted)' }));
    txt(svg, fmtDay(d.start, n - 1), { x: R, y: B + 20, 'text-anchor': 'end', 'font-size': 11, fill: 'var(--muted)' });
    txt(svg, 'µg/m³', { x: 8, y: T - 4, 'font-size': 11, fill: 'var(--muted)' });
    const hv = el('line', { y1: T, y2: B, stroke: 'var(--muted)', opacity: 0 }, svg), ht = txt(svg, '', { y: B - 8, 'font-size': 11.5, fill: 'var(--ink)', opacity: 0 });
    svg.onpointermove = e => { const r = svg.getBoundingClientRect(), i = Math.max(0, Math.min(n - 1, Math.round(((e.clientX - r.left) / r.width * 900 - L) / (R - L) * (n - 1))));
      hv.setAttribute('x1', X(i)); hv.setAttribute('x2', X(i)); hv.setAttribute('opacity', .6);
      ht.textContent = `${fmtDay(d.start, i)}: ${d.pm[i] ?? '–'} µg/m³ · upwind index ${d.up[i] ?? 0}`; const rt = X(i) > 560;
      ht.setAttribute('x', X(i) + (rt ? -8 : 8)); ht.setAttribute('text-anchor', rt ? 'end' : 'start'); ht.setAttribute('opacity', 1); };
    svg.onpointerleave = () => { hv.setAttribute('opacity', 0); ht.setAttribute('opacity', 0); };
  });
})();

/* per-period effects */
(() => {
  const svg = document.getElementById('lags'), L = 60, R = 680, T = 22, B = 210, lo = -200, hi = 420;
  const Y = v => B - (B - T) * (v - lo) / (hi - lo), Xc = i => L + (R - L) * (i + .5) / D.eff.length;
  grid(svg, Y, [-100, 0, 100, 200, 300, 400], L, R);
  D.eff.forEach(([per, ue, ul, uh, de, dl, dh], i) => {
    txt(svg, 'Detections ' + per, { x: Xc(i), y: B + 22, 'text-anchor': 'middle', 'font-size': 12, fill: 'var(--ink)' });
    [[ue, ul, uh, -26, 'var(--haze)', 'upwind'], [de, dl, dh, 26, 'var(--muted)', 'downwind']].forEach(([e, a, b, off, c, lab], j) => {
      const x = Xc(i) + off, k = i * 2 + j;
      const w = el('line', { x1: x, x2: x, y1: Y(Math.min(b, hi)), y2: Y(Math.max(a, lo)), stroke: c, 'stroke-width': 3, 'stroke-linecap': 'round', class: 'anim gy' }, svg); w.style.animationDelay = (k * .08) + 's';
      const d = el('circle', { cx: x, cy: Y(e), r: 7, fill: c, stroke: 'var(--panel)', 'stroke-width': 2, class: 'anim pop' }, svg); d.style.animationDelay = (.4 + k * .08) + 's';
      el('title', {}, d).textContent = `${per}, ${lab}: ${e} [${a}, ${b}]`;
      txt(svg, (e > 0 ? '+' : '') + e, { x: x + (j ? 12 : -12), y: Y(e) + 4, 'text-anchor': j ? 'start' : 'end', 'font-size': 11, fill: c });
    });
  });
  el('circle', { cx: L + 10, cy: T - 8, r: 5, fill: 'var(--haze)' }, svg); txt(svg, 'upwind fires', { x: L + 20, y: T - 4, 'font-size': 11, fill: 'var(--ink)' });
  el('circle', { cx: L + 120, cy: T - 8, r: 5, fill: 'var(--muted)' }, svg); txt(svg, 'downwind fires (placebo)', { x: L + 130, y: T - 4, 'font-size': 11, fill: 'var(--ink)' });
})();

/* fire share by year vs detections */
(() => {
  const svg = document.getElementById('byyear'), L = 50, R = 840, T = 24, B = 220, n = D.byyear.length, bw = (R - L) / n;
  const Y = v => B - (B - T) * v / 40, maxd = Math.max(...D.byyear.map(r => r[1])), Yd = v => B - (B - T) * v / (maxd * 1.15);
  grid(svg, Y, [0, 10, 20, 30, 40], L, R, v => v + '%');
  D.byyear.forEach(([y, det, sh, lo, hi], i) => {
    const x = L + i * bw + bw * .22, w = bw * .56, g = el('g', { class: 'anim gy' }, svg); g.style.animationDelay = (i * .07) + 's'; g.style.transformOrigin = `center ${B}px`;
    el('rect', { x, y: Y(sh), width: w, height: B - Y(sh), fill: 'var(--smoke)', rx: 3 }, g);
    el('line', { x1: x + w / 2, x2: x + w / 2, y1: Y(Math.max(lo, 0)), y2: Y(Math.min(hi, 40)), stroke: 'var(--ink)', 'stroke-width': 1.2 }, g);
    txt(svg, y, { x: x + w / 2, y: B + 18, 'text-anchor': 'middle', 'font-size': 11, fill: 'var(--muted)' });
    txt(svg, sh.toFixed(0) + '%', { x: x + w / 2, y: Y(sh) + 14, 'text-anchor': 'middle', 'font-size': 10.5, fill: 'var(--panel)' });
  });
  const line = el('path', { d: D.byyear.map(([y, det], i) => (i ? 'L' : 'M') + (L + i * bw + bw / 2) + ' ' + Yd(det)).join(' '), class: 'line', fill: 'none', stroke: 'var(--haze)', 'stroke-width': 2.4 }, svg); drawLine(line);
  D.byyear.forEach(([y, det], i) => { const c = el('circle', { cx: L + i * bw + bw / 2, cy: Yd(det), r: 4.5, fill: 'var(--haze)', class: 'anim pop' }, svg); c.style.animationDelay = (1 + i * .1) + 's'; el('title', {}, c).textContent = `${y}: ${det.toLocaleString()} detections`; });
  el('rect', { x: L + 6, y: T - 18, width: 12, height: 12, fill: 'var(--smoke)', rx: 2 }, svg); txt(svg, 'crop-fire share of Oct–Nov PM2.5 (95% CI)', { x: L + 24, y: T - 8, 'font-size': 11, fill: 'var(--ink)' });
  el('line', { x1: L + 330, x2: L + 352, y1: T - 12, y2: T - 12, stroke: 'var(--haze)', 'stroke-width': 2.4 }, svg); txt(svg, `satellite detections, Oct–Nov (peak ${(maxd / 1000).toFixed(0)}k in 2021)`, { x: L + 358, y: T - 8, 'font-size': 11, fill: 'var(--ink)' });
})();

/* event study around fire spikes */
(() => {
  const svg = document.getElementById('es'), L = 60, R = 860, T = 20, B = 220, lo = -50, hi = 75;
  const X = o => L + (R - L) * (o + 5) / 10, Y = v => B - (B - T) * (v - lo) / (hi - lo);
  grid(svg, Y, [-40, -20, 0, 20, 40, 60], L, R);
  [-4, -2, 0, 2, 4].forEach(o => txt(svg, o === 0 ? 'spike day' : (o > 0 ? '+' : '') + o, { x: X(o), y: B + 20, 'text-anchor': 'middle', 'font-size': 11, fill: 'var(--muted)' }));
  [['up', 'var(--haze)'], ['dn', 'var(--muted)']].forEach(([k, c]) => {
    const r = D.es[k];
    el('path', { d: 'M' + r.map(p => X(p[0]) + ' ' + Y(p[2])).join('L') + 'L' + r.slice().reverse().map(p => X(p[0]) + ' ' + Y(p[3])).join('L') + 'Z', fill: c, 'fill-opacity': .14 }, svg);
    const p = el('path', { d: r.map((q, i) => (i ? 'L' : 'M') + X(q[0]) + ' ' + Y(q[1])).join(' '), class: 'line', fill: 'none', stroke: c, 'stroke-width': 2.6 }, svg); drawLine(p);
  });
  el('line', { x1: L + 10, x2: L + 32, y1: T - 6, y2: T - 6, stroke: 'var(--haze)', 'stroke-width': 2.6 }, svg); txt(svg, 'around the heaviest upwind-fire days', { x: L + 38, y: T - 2, 'font-size': 11, fill: 'var(--ink)' });
  el('line', { x1: L + 290, x2: L + 312, y1: T - 6, y2: T - 6, stroke: 'var(--muted)', 'stroke-width': 2.6 }, svg); txt(svg, 'around the heaviest downwind-fire days (placebo)', { x: L + 318, y: T - 2, 'font-size': 11, fill: 'var(--ink)' });
  txt(svg, 'µg/m³ vs 21-day mean', { x: 8, y: B + 20, 'font-size': 10.5, fill: 'var(--muted)' });
})();

/* specification ladder + checks */
(() => {
  const svg = document.getElementById('forest'), rows = D.forest, L = 410, R = 880, lo = -5, hi = 30;
  const H = 40 + rows.length * 38 + 34; svg.setAttribute('viewBox', `0 0 900 ${H}`);
  const X = v => L + (R - L) * (v - lo) / (hi - lo);
  [0, 10, 20, 30].forEach(v => { el('line', { x1: X(v), x2: X(v), y1: 20, y2: H - 30, stroke: v === 0 ? 'var(--ink)' : 'var(--line)', 'stroke-width': v === 0 ? 1.3 : 1 }, svg); txt(svg, v + '%', { x: X(v), y: H - 12, 'text-anchor': 'middle', 'font-size': 11, fill: 'var(--muted)' }); });
  txt(svg, 'specification ladder', { x: 8, y: 14, 'font-size': 10.5, fill: 'var(--haze)' });
  rows.forEach(([name, ue, ul, uh, de, dl, dh, kind], i) => {
    const y = 34 + i * 38 + (kind === 'check' ? 14 : 0), prim = name.includes('primary');
    const cl = v => Math.max(lo, Math.min(hi, v));
    if (kind === 'check' && rows[i - 1][7] === 'ladder') { el('line', { x1: 8, x2: R, y1: y - 22, y2: y - 22, stroke: 'var(--line)' }, svg); txt(svg, 'checks on the primary design', { x: 8, y: y - 8 - 20 + 14, 'font-size': 10.5, fill: 'var(--haze)' }); }
    txt(svg, name, { x: L - 14, y: y + 4, 'text-anchor': 'end', 'font-size': 11.5, fill: prim ? 'var(--ink)' : 'var(--muted)', 'font-weight': prim ? 600 : 400 });
    const w = el('line', { x1: X(cl(ul)), x2: X(cl(uh)), y1: y - 4, y2: y - 4, stroke: 'var(--haze)', 'stroke-width': prim ? 4 : 2.6, 'stroke-linecap': 'round', class: 'anim gx' }, svg); w.style.animationDelay = (i * .05) + 's';
    const d = el('circle', { cx: X(ue), cy: y - 4, r: prim ? 6.5 : 5, fill: 'var(--haze)', class: 'anim pop' }, svg); d.style.animationDelay = (.3 + i * .05) + 's';
    el('title', {}, d).textContent = `${name}: fire share ${ue}% [${ul}, ${uh}]`;
    if (de != null) {
      const w2 = el('line', { x1: X(cl(dl)), x2: X(cl(dh)), y1: y + 8, y2: y + 8, stroke: 'var(--muted)', 'stroke-width': 1.6, 'stroke-linecap': 'round', class: 'anim gx' }, svg); w2.style.animationDelay = (.15 + i * .05) + 's';
      const q = el('rect', { x: X(de) - 4, y: y + 4, width: 8, height: 8, fill: 'var(--muted)', class: 'anim pop' }, svg); q.style.animationDelay = (.45 + i * .05) + 's';
      el('title', {}, q).textContent = `${name}: placebo share ${de}% [${dl}, ${dh}]`;
    }
  });
})();

/* dose-response */
(() => {
  const svg = document.getElementById('dose'), L = 60, R = 680, T = 14, B = 200, lo = -30, hi = 80, n = D.dose.length;
  const Y = v => B - (B - T) * (v - lo) / (hi - lo), bw = (R - L) / n;
  grid(svg, Y, [-20, 0, 20, 40, 60, 80], L, R);
  D.dose.forEach(([lab, e, a, b, days], i) => {
    const x = L + i * bw + bw * .2, w = bw * .6, g = el('g', { class: 'anim gy' }, svg); g.style.animationDelay = (i * .1) + 's'; g.style.transformOrigin = `center ${Y(0)}px`;
    el('rect', { x, y: Math.min(Y(e), Y(0)), width: w, height: Math.abs(Y(0) - Y(e)), fill: i === n - 1 ? 'var(--smoke)' : 'var(--haze)', rx: 3 }, g);
    el('line', { x1: x + w / 2, x2: x + w / 2, y1: Y(Math.max(a, lo)), y2: Y(Math.min(b, hi)), stroke: 'var(--ink)', 'stroke-width': 1.4 }, g);
    txt(svg, lab, { x: x + w / 2, y: B + 18, 'text-anchor': 'middle', 'font-size': 11, fill: 'var(--muted)' });
    txt(svg, (e > 0 ? '+' : '') + e, { x: x + w / 2, y: Y(Math.min(b, hi)) - 6, 'text-anchor': 'middle', 'font-size': 11, fill: 'var(--ink)' });
  });
  txt(svg, 'same-day upwind fire exposure, fifths within each year', { x: (L + R) / 2, y: B + 38, 'text-anchor': 'middle', 'font-size': 11, fill: 'var(--muted)' });
})();

/* daily smoke split */
(() => {
  const fig = document.getElementById('ct-fig'), svg = document.getElementById('ct'), cap = document.getElementById('ctcap');
  toggle(fig, 'data-y', y => {
    clear(svg); const d = D.contrib[y], n = d.length, L = 44, R = 884, T = 14, B = 226, max = 700;
    const X = i => L + (R - L) * i / (n - 1), Y = v => B - (B - T) * v / max;
    grid(svg, Y, [0, 200, 400, 600], L, R);
    const rest = d.map(([, pm, f], i) => [X(i), Y(Math.max(pm - f, 0))]), top = d.map(([, pm], i) => [X(i), Y(pm)]);
    const area = (a, b) => 'M' + a.map(p => p.join(' ')).join('L') + 'L' + b.slice().reverse().map(p => p.join(' ')).join('L') + 'Z';
    const base = d.map((_, i) => [X(i), Y(0)]);
    const g = el('g', { class: 'anim gy' }, svg); g.style.transformOrigin = `center ${B}px`;
    el('path', { d: area(rest, base), fill: 'var(--haze)', 'fill-opacity': .3 }, g);
    const g2 = el('g', { class: 'anim gy' }, svg); g2.style.transformOrigin = `center ${B}px`; g2.style.animationDelay = '.5s';
    el('path', { d: area(top, rest), fill: 'var(--smoke)', 'fill-opacity': .85 }, g2);
    [0, 14, 31, 45, n - 1].forEach(i => txt(svg, d[i][0], { x: X(i), y: B + 20, 'text-anchor': i === 0 ? 'start' : i === n - 1 ? 'end' : 'middle', 'font-size': 11, fill: 'var(--muted)' }));
    el('rect', { x: L + 10, y: T, width: 12, height: 12, fill: 'var(--smoke)', rx: 2 }, svg); txt(svg, 'crop-fire smoke', { x: L + 28, y: T + 10, 'font-size': 11, fill: 'var(--ink)' });
    el('rect', { x: L + 150, y: T, width: 12, height: 12, fill: 'var(--haze)', 'fill-opacity': .3, rx: 2 }, svg); txt(svg, 'everything else', { x: L + 168, y: T + 10, 'font-size': 11, fill: 'var(--ink)' });
    const s = d.reduce((a, r) => a + r[2], 0) / d.reduce((a, r) => a + r[1], 0);
    cap.textContent = `Oct–Nov ${y}: smoke averaged ${Math.round(s * 100)}% of PM2.5. Daily splits on the most extreme days are extrapolations; the period average is the reliable quantity. Hover for values.`;
    const hv = el('line', { y1: T, y2: B, stroke: 'var(--muted)', opacity: 0 }, svg), ht = txt(svg, '', { y: T + 34, 'font-size': 11.5, fill: 'var(--ink)', opacity: 0 });
    svg.onpointermove = e => { const r = svg.getBoundingClientRect(), i = Math.max(0, Math.min(n - 1, Math.round(((e.clientX - r.left) / r.width * 900 - L) / (R - L) * (n - 1))));
      hv.setAttribute('x1', X(i)); hv.setAttribute('x2', X(i)); hv.setAttribute('opacity', .6);
      ht.textContent = `${d[i][0]}: ${d[i][1]} µg/m³, smoke ≈ ${d[i][2]}`; const rt = X(i) > 560; ht.setAttribute('x', X(i) + (rt ? -8 : 8)); ht.setAttribute('text-anchor', rt ? 'end' : 'start'); ht.setAttribute('opacity', 1); };
    svg.onpointerleave = () => { hv.setAttribute('opacity', 0); ht.setAttribute('opacity', 0); };
  });
})();

/* composition */
(() => {
  const svg = document.getElementById('comp'), L = 10, R = 890, y = 40, h = 56;
  const rows = [D.comp[0], D.comp[1], D.comp[2]];
  const cols = ['var(--smoke)', 'var(--clean)', 'var(--line)'];
  let x = L;
  rows.forEach(([name, s], i) => {
    const w = Math.max(s, 0) * (R - L), g = el('g', { class: 'anim gx' }, svg); g.style.animationDelay = (i * .25) + 's'; g.style.transformOrigin = `${x}px center`;
    el('rect', { x, y, width: Math.max(w - 2, 1.5), height: h, fill: cols[i], rx: 4 }, g);
    if (w > 40) { txt(g, Math.round(s * 100) + '%', { x: x + w / 2, y: y + h / 2 + 7, 'text-anchor': 'middle', 'font-size': 20, 'font-weight': 600, fill: i === 2 ? 'var(--ink)' : 'var(--panel)' });
      txt(svg, name.split(':')[0], { x: i === 0 ? x : x + w / 2, y: y + h + 22, 'text-anchor': i === 0 ? 'start' : 'middle', 'font-size': 11.5, fill: 'var(--ink)' });
      txt(svg, i === 1 ? 'outside estimate, 26–50%' : i === 0 ? `measured, CI ${Math.round(D.comp[0][2] * 100)}–${Math.round(D.comp[0][3] * 100)}%` : 'NCR, regional, secondary', { x: i === 0 ? x : x + w / 2, y: y + h + 38, 'text-anchor': i === 0 ? 'start' : 'middle', 'font-size': 10.5, fill: 'var(--muted)' }); }
    x += w;
  });
})();

/* October vs November, severe days before 1 Nov */
(() => {
  const svg = document.getElementById('before'), L = 44, R = 884, T = 20, B = 220, max = 320, n = D.before.length, bw = (R - L) / n;
  const Y = v => B - (B - T) * v / max;
  grid(svg, Y, [0, 100, 200, 300], L, R);
  D.before.forEach(([y, o, nv, sb, st], i) => {
    const x = L + i * bw, g = el('g', { class: 'anim gy' }, svg); g.style.animationDelay = (i * .07) + 's'; g.style.transformOrigin = `center ${B}px`;
    el('rect', { x: x + bw * .14, y: Y(o), width: bw * .34, height: B - Y(o), fill: 'var(--haze)', rx: 2 }, g);
    el('rect', { x: x + bw * .52, y: Y(nv), width: bw * .34, height: B - Y(nv), fill: 'var(--smoke)', rx: 2 }, g);
    txt(svg, y, { x: x + bw / 2, y: B + 18, 'text-anchor': 'middle', 'font-size': 11, fill: 'var(--muted)' });
    const t = txt(svg, `${sb}/${st} severe`, { x: x + bw / 2, y: Y(Math.max(o, nv)) - 8, 'text-anchor': 'middle', 'font-size': 10.5, fill: 'var(--ink)', class: 'anim pop' }); t.style.animationDelay = (.5 + i * .07) + 's';
  });
  el('line', { x1: L, x2: R, y1: Y(60), y2: Y(60), stroke: 'var(--clean)', 'stroke-width': 1.5, 'stroke-dasharray': '6 4' }, svg);
  txt(svg, '60', { x: L - 8, y: Y(60) + 4, 'text-anchor': 'end', 'font-size': 11, 'font-weight': 600, fill: 'var(--clean)' });
  el('rect', { x: L + 10, y: T - 12, width: 12, height: 12, fill: 'var(--haze)', rx: 2 }, svg); txt(svg, 'October mean', { x: L + 28, y: T - 2, 'font-size': 11, fill: 'var(--ink)' });
  el('rect', { x: L + 130, y: T - 12, width: 12, height: 12, fill: 'var(--smoke)', rx: 2 }, svg); txt(svg, 'November mean', { x: L + 148, y: T - 2, 'font-size': 11, fill: 'var(--ink)' });
  txt(svg, 'label: severe days before 1 Nov / all severe Oct–Nov days', { x: L + 270, y: T - 2, 'font-size': 10.5, fill: 'var(--muted)' });
})();

/* policy levers, with a slider for Delhi's own emissions */
(() => {
  const svg = document.getElementById('pol'), inp = document.getElementById('cut'), out = document.getElementById('cutv');
  const L = 300, R = 860, max = 26, X = v => L + (R - L) * v / max;
  const fc = D.firecut.find(r => r[0] === 50);
  const draw = (first) => {
    clear(svg); const k = +inp.value, at = s => D.curve[s].find(r => r[0] === k);
    out.textContent = k + '%';
    [0, 5, 10, 15, 20, 25].forEach(v => { el('line', { x1: X(v), x2: X(v), y1: 10, y2: 210, stroke: v === 0 ? 'var(--ink)' : 'var(--line)' }, svg); txt(svg, v + '%', { x: X(v), y: 230, 'text-anchor': 'middle', 'font-size': 11, fill: 'var(--muted)' }); });
    const rows = [
      ...D.grap.map(([s, pct]) => [`GRAP from 1 Sep, ${s}`, pct, null, null, 'var(--muted)', `≤ ${pct}% lower Sep–Jan PM2.5 (best case); no detectable effect at Study 1's estimate`]),
      [`Delhi's own emissions −${k}%`, at('central')[1], at('low')[1], at('high')[1], 'var(--clean)', `−${at('central')[1].toFixed(1)}% October PM2.5 (${at('low')[1].toFixed(1)}–${at('high')[1].toFixed(1)}) · ${at('central')[3].toFixed(1)}% of Oct–Jan`],
      ['Crop fires halved in October', fc[1], fc[2], fc[3], 'var(--smoke)', `−${fc[1]}% October PM2.5 (${fc[2]}–${fc[3]}), measured`]];
    rows.forEach(([name, v, lo, hi, c, note], i) => {
      const y = 30 + i * 46;
      txt(svg, name, { x: L - 14, y: y + 5, 'text-anchor': 'end', 'font-size': 12, fill: 'var(--ink)' });
      const g = el('g', { class: first ? 'anim gx' : '' }, svg); g.style.transformOrigin = `${L}px center`; g.style.animationDelay = (i * .12) + 's';
      el('rect', { x: L, y: y - 9, width: Math.max(X(v) - L, 1), height: 18, fill: c, rx: 3 }, g);
      if (lo != null) el('line', { x1: X(lo), x2: X(hi), y1: y, y2: y, stroke: 'var(--ink)', 'stroke-width': 1.4 }, g);
      txt(svg, note, { x: L + 4, y: y + 24, 'font-size': 10.5, fill: 'var(--muted)' });
    });
  };
  inp.addEventListener('input', () => draw(false)); draw(true);
})();

/* charts come up: arm figures below the fold, play when they scroll in, replay on demand */
(() => {
  const figs = [...document.querySelectorAll('article .figure')];
  figs.forEach(f => {
    f.querySelectorAll('.anim').forEach(a => { const d = parseFloat(a.style.animationDelay) || 0; a.style.animationDelay = (d + .35) + 's'; });
    const b = document.createElement('button'); b.type = 'button'; b.className = 'replay'; b.textContent = '↻ Replay';
    b.setAttribute('aria-label', 'Replay chart animation');
    b.addEventListener('click', () => { f.classList.remove('play', 'armed'); void f.offsetWidth; f.classList.add('play'); f.dispatchEvent(new Event('replay')); });
    if (f.querySelector('.stepper')) return;                  // the bridge has its own step controls
    if (f.querySelector('.toggle')) b.classList.add('bottom'); // keep clear of the view toggle
    f.appendChild(b);
  });
  if (reduce || !('IntersectionObserver' in window)) return;
  figs.forEach(f => { if (f.getBoundingClientRect().top > innerHeight * .9) f.classList.add('armed'); });
  const io = new IntersectionObserver(es => es.forEach(e => { if (!e.isIntersecting) return; e.target.classList.remove('armed'); e.target.classList.add('play'); io.unobserve(e.target); }), { threshold: .18 });
  figs.forEach(f => io.observe(f));
})();

/* reveal + count */
(() => {
  if (reduce || !('IntersectionObserver' in window)) return;
  const count = b => { const end = +b.dataset.count, dec = +(b.dataset.dec || 0), t0 = performance.now();
    const st = t => { const k = Math.min(1, (t - t0) / 1300), e = 1 - Math.pow(1 - k, 3); b.textContent = (end * e).toLocaleString('en-US', { minimumFractionDigits: dec, maximumFractionDigits: dec }); if (k < 1) requestAnimationFrame(st); };
    requestAnimationFrame(st); };
  const io = new IntersectionObserver(es => es.forEach(e => { if (!e.isIntersecting) return; e.target.classList.add('play'); e.target.querySelectorAll('[data-count]').forEach(count); if (e.target.matches('[data-count]')) count(e.target); io.unobserve(e.target); }), { threshold: .15 });
  document.querySelectorAll('.reveal:not(.figure), .numbers, .stat').forEach(n => io.observe(n));
})();