#!/usr/bin/env python3
"""Path traces a GPU module in green light. NumPy and Pillow only.  usage: FONTS=dir green_module.py out.png [width] [samples]"""
import os; os.environ['OMP_NUM_THREADS'] = os.environ['OPENBLAS_NUM_THREADS'] = '1'
import math, multiprocessing as mp, pathlib, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
FD = os.environ['FONTS']; F = np.float32; R = np.random.default_rng(21); LIME = np.array([.50, 1.0, .06], F)
font = lambda n, s: ImageFont.truetype(f'{FD}/{n}.ttf', s)
BX, TEX = [], []   # x0 y0 z0 x1 y1 z1 | albedo | F0 | rough | emission | texture id
def add(x0, y0, z0, x1, y1, z1, alb=(.03, .03, .03), f0=.05, rough=.22, em=(0, 0, 0), tex=-1): BX.append((x0, y0, z0, x1, y1, z1, *alb, f0, rough, *em, tex))
def lin(a): return (np.asarray(a, F) / 255) ** 2.2

# ---- textures -----------------------------------------------------------------------------------------------------------
def board_tex(w=2600, h=1144):
    im, gl, mt = Image.new('RGB', (w, h), (15, 22, 18)), Image.new('L', (w, h), 0), Image.new('L', (w, h), 0); d, g, m = ImageDraw.Draw(im), ImageDraw.Draw(gl), ImageDraw.Draw(mt)
    for _ in range(620):  # traces: runs with 45-degree turns
        x, y = R.integers(0, w), R.integers(0, h); p = [(x, y)]; dx, dy = [(1, 0), (0, 1), (-1, 0), (0, -1)][R.integers(4)]
        for _ in range(R.integers(2, 5)):
            l = R.integers(20, 150); x, y = x + dx * l, y + dy * l; p.append((x, y)); k = R.integers(10, 40) * (1 if R.random() < .5 else -1); q = (x + dx * abs(k) + dy * k, y + dy * abs(k) + dx * k); p.append(q); x, y = q
        c = (34, 62, 36) if R.random() < .8 else (104, 88, 46); wd = int(R.choice([2, 2, 3, 4])); d.line(p, fill=c, width=wd)
        if R.random() < .085: g.line(p, fill=int(R.integers(60, 200)), width=2)
        d.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(150, 126, 66)); m.ellipse((x - 5, y - 5, x + 5, y + 5), fill=255)
    for _ in range(1500): x, y, r = R.integers(0, w), R.integers(0, h), R.integers(2, 5); d.ellipse((x - r, y - r, x + r, y + r), fill=(146, 122, 66)); m.ellipse((x - r, y - r, x + r, y + r), fill=230)
    return np.flipud(lin(im)), np.flipud(np.asarray(gl, F) / 255), np.flipud(np.asarray(mt, F) / 255), .85
def substrate_tex(s=1500):
    im, gl, mt = Image.new('RGB', (s, s), (12, 30, 14)), Image.new('L', (s, s), 0), Image.new('L', (s, s), 0); d, g, m = ImageDraw.Draw(im), ImageDraw.Draw(gl), ImageDraw.Draw(mt)
    for _ in range(2600):
        x, y = R.integers(0, s, 2); e = max(abs(x - s / 2), abs(y - s / 2)) / (s / 2)
        if e < .60: continue
        a, b = (R.integers(8, 34), R.integers(5, 14)) if R.random() < .5 else (R.integers(5, 14), R.integers(8, 34)); v = int(R.integers(20, 255) * (1.12 - .6 * (e - .6) / .4)); g.rectangle((x, y, x + a, y + b), fill=min(v, 255)); d.rectangle((x, y, x + a, y + b), fill=(60, 110, 20))
    for k in np.linspace(.60, .97, 13): q = s / 2 * k; g.rectangle((s / 2 - q, s / 2 - q, s / 2 + q, s / 2 + q), outline=int(R.integers(70, 220)), width=2)
    for i in range(0, s, 15):
        for q in (.985, .965): r = s / 2 * q; [m.ellipse((x - 3, y - 3, x + 3, y + 3), fill=255) for x, y in ((i, s / 2 - r), (i, s / 2 + r), (s / 2 - r, i), (s / 2 + r, i))]
    return np.flipud(lin(im)), np.flipud(np.asarray(gl, F) / 255), np.flipud(np.asarray(mt, F) / 255), 1.15
def die_tex(s=1400):
    im, mt = Image.new('RGB', (s, s), (27, 29, 28)), Image.new('L', (s, s), 0); d, m = ImageDraw.Draw(im), ImageDraw.Draw(mt)
    for i in range(0, s, 70): c = 24 + int(R.integers(0, 8)); d.rectangle((i, 0, i + 70, s), fill=(c, c + 2, c + 1))
    n = np.asarray(im, np.int16) + R.integers(-3, 4, (s, s, 1)); im = Image.fromarray(np.clip(n, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    for dd, c in ((d, (214, 220, 208)), (m, 255)):
        dd.text((s * .5, s * .57), '140', font=font('BigShoulders-Bold', int(s * .60)), fill=c, anchor='ms'); dd.text((s * .5, s * .74), 'WATTS', font=font('BigShoulders-Bold', int(s * .155)), fill=c, anchor='ms'); dd.rectangle((s * .07, s * .07, s * .10, s * .10), fill=c)
    return np.flipud(lin(im)), np.zeros((s, s), F), np.flipud(np.asarray(mt, F) / 255), 0
TEX += [board_tex(), substrate_tex(), die_tex()]

# ---- geometry -----------------------------------------------------------------------------------------------------------
W2, H2 = 5.0, 2.2; GROUND = -.62
add(-W2, -H2, -.26, W2, H2, 0, (.02, .03, .022), .05, .28, tex=0)
for a in ((-W2 - .09, H2, -.28, W2 + .09, H2 + .09, .07), (-W2 - .09, -H2 - .09, -.28, W2 + .09, -H2, .07), (-W2 - .09, -H2, -.28, -W2, H2, .07), (W2, -H2, -.28, W2 + .09, H2, .07)): add(*a, (.82, .84, .80), .80, .13)
glow = lambda p: tuple(LIME * p)
for x0, x1, s in ((-4.4, -3.5, -1), (-1.1, .1, -1), (2.3, 3.0, -1), (-3.2, -2.4, 1), (.4, 1.5, 1), (3.6, 4.5, 1)): y = H2 * s; add(x0, min(y, y + .09 * s) - .004, .065, x1, max(y, y + .09 * s) + .004, .082, em=glow(4.6))
for y0, y1, s in ((-1.6, -.7, -1), (.5, 1.5, 1)): x = W2 * s; add(min(x, x + .09 * s) - .004, y0, .065, max(x, x + .09 * s) + .004, y1, .082, em=glow(4.6))
add(-1.55, -1.55, 0, 1.55, 1.55, .10, (.02, .05, .02), .05, .25, tex=1); add(-.92, -.92, .10, .92, .92, .30, (.03, .03, .03), .16, .20, tex=2)
for q in (-.98, .94): add(-.98, q, .10, .98, q + .04, .13, em=glow(3.4)); add(q, -.98, .10, q + .04, .98, .13, em=glow(3.4))
for s in (-1, 1):
    for i in range(2):
        for j in range(4): cx, cy = s * (2.16 + i * .62), -1.44 + j * .96; add(cx - .28, cy - .44, 0, cx + .28, cy + .44, .17, (.036, .038, .038), .055, .24); add(cx - .23, cy - .39, .17, cx + .23, cy + .39, .172, (.05, .052, .052), .06, .30)
    for j in range(9): cy = -1.72 + j * .43; add(s * 1.73 - .05, cy - .17, 0, s * 1.73 + .05, cy + .17, .05, em=glow(.35 + 2.4 * R.random() ** 2)); add(s * 3.18 - .035, cy - .16, 0, s * 3.18 + .035, cy + .16, .04, em=glow(.15 + 2.6 * R.random() ** 3))
used = []
for s in (-1, 1):
    n = 0
    for _ in range(900):
        if n == 19: break
        a, b = R.uniform(.15, .27, 2); cx, cy = s * R.uniform(3.5, 4.62), R.uniform(-1.85, 1.85)
        if any(abs(cx - u[0]) < a + u[2] + .05 and abs(cy - u[1]) < b + u[3] + .05 for u in used): continue
        used.append((cx, cy, a, b)); n += 1; t = R.random(); hgt = R.uniform(.10, .30)
        if t < .56: add(cx - a, cy - b, 0, cx + a, cy + b, hgt, (.032, .034, .035), .05, .22)
        elif t < .84: add(cx - a, cy - b, 0, cx + a, cy + b, hgt, (.56, .56, .53), .55, .22)
        else: add(cx - a, cy - b, 0, cx + a, cy + b, hgt, (.50, .42, .26), .50, .25)
def smd(x, y, horiz):
    a, b = (.055, .03) if horiz else (.03, .055); c = [(.62, .52, .34), (.68, .66, .60), (.10, .08, .06)][R.integers(3)]; add(x - a, y - b, 0, x + a, y + b, R.uniform(.035, .06), c, .20, .3)
for i in range(58):
    x = -4.8 + i * .168
    if R.random() < .80: smd(x, 2.06, True)
    if R.random() < .80: smd(x, -2.06, True)
for s in (-1, 1):
    for i in range(26):
        y = -1.95 + i * .156
        if R.random() < .75: smd(s * 4.86, y, False)
        if abs(y) > 1.62 and R.random() < .7: smd(s * R.uniform(.1, 1.4), math.copysign(R.uniform(1.66, 1.95), y), True)
A = np.array(BX, F); LO, HI, ALB, F0, RGH, EM, TID = A[:, :3], A[:, 3:6], A[:, 6:9], A[:, 9], A[:, 10], A[:, 11:14], A[:, 14].astype(int)
order = np.lexsort(((LO[:, 1] + HI[:, 1] > 0), np.floor((LO[:, 0] + HI[:, 0]) / 2 / 1.05))); order = order[order != 0]; GR = [np.array([0])] + [g for g in np.array_split(order, max(1, len(order) // 11))]
GLO, GHI = np.array([LO[g].min(0) for g in GR]), np.array([HI[g].max(0) for g in GR]); EMI = np.flatnonzero(EM.max(1) > 0); EP = EM[EMI].max(1) * (HI[EMI, 0] - LO[EMI, 0]) * (HI[EMI, 1] - LO[EMI, 1]); EP /= EP.sum()
ALL = (LO.min(0), HI.max(0))

EYE, AT = np.array([-6.4, -11.6, 8.3], F), np.array([-1.50, .62, -.15], F); fw = AT - EYE; fw /= np.linalg.norm(fw); rt = np.cross(fw, [0, 0, 1]); rt /= np.linalg.norm(rt); up = np.cross(rt, fw)
FOV = math.tan(math.radians(48) / 2); APER = .16; FOC = float(np.dot(np.array([0, -.2, .25]) - EYE, fw)); SUND = np.array([-.62, .62, .55], F); SUND /= np.linalg.norm(SUND)
def env(d):
    a = np.clip(d @ np.array([-.55, .72, .42], F), 0, 1)[:, None]; b = np.clip(d @ np.array([.75, -.25, .60], F), 0, 1)[:, None]; z = np.clip(d[:, 2:3], 0, 1)
    c = np.clip(d @ np.array([.26, .78, .57], F), 0, 1)[:, None]; e = np.clip(d @ np.array([-.10, .62, .78], F), 0, 1)[:, None]
    return c ** 7 * np.array([.17, .22, .13], F) + e ** 40 * np.array([1.0, 1.15, .85], F) + np.array([.004, .010, .004], F) + z * np.array([.010, .022, .010], F) + a ** 9 * np.array([.55, .80, .26], F) + a ** 60 * np.array([6.5, 8.0, 4.8], F) + b ** 24 * np.array([1.5, 1.7, 1.4], F)
def hsh(x, y): v = np.sin(x * 127.1 + y * 311.7) * 43758.5453; return v - np.floor(v)

def hit(o, d, tmax=None):
    n = len(o); T = np.full(n, np.inf, F) if tmax is None else tmax.astype(F).copy(); I = np.full(n, -1); inv = 1 / np.where(np.abs(d) < 1e-7, 1e-7, d)
    a, b = (ALL[0] - o) * inv, (ALL[1] - o) * inv; cand = np.flatnonzero((np.maximum(a, b).min(1) > 1e-4) & (np.minimum(a, b).max(1) < np.maximum(a, b).min(1)))
    if not len(cand): return T, I
    oc, ic = o[cand], inv[cand]
    for gi, g in enumerate(GR):
        a, b = (GLO[gi] - oc) * ic, (GHI[gi] - oc) * ic; nr, fr = np.minimum(a, b).max(1), np.maximum(a, b).min(1); s = np.flatnonzero((fr > 1e-4) & (nr < fr) & (nr < T[cand]))
        if not len(s): continue
        r = cand[s]; a, b = (LO[g][None] - o[r, None]) * inv[r, None], (HI[g][None] - o[r, None]) * inv[r, None]; tn, tf = np.minimum(a, b).max(2), np.maximum(a, b).min(2); tn = np.where((tn < tf) & (tn > 1e-4), tn, np.inf)
        k = tn.argmin(1); v = tn[np.arange(len(r)), k]; m = v < T[r]; T[r[m]] = v[m]; I[r[m]] = g[k[m]]
    return T, I

def surface(p, N, I, fl):
    n = len(p); alb, f0, rg, em = np.zeros((n, 3), F), np.zeros(n, F), np.zeros(n, F), np.zeros((n, 3), F); b = np.flatnonzero(~fl); ib = I[b]; alb[b], f0[b], rg[b], em[b] = ALB[ib], F0[ib], RGH[ib], EM[ib]
    for t, (tx, gl, mt, pw) in enumerate(TEX):
        s = b[(TID[ib] == t) & (N[b, 2] > .5)]
        if not len(s): continue
        k = I[s]; u, v = (p[s, 0] - LO[k, 0]) / (HI[k, 0] - LO[k, 0]), (p[s, 1] - LO[k, 1]) / (HI[k, 1] - LO[k, 1]); h, w = gl.shape; yi, xi = np.clip((v * h).astype(int), 0, h - 1), np.clip((u * w).astype(int), 0, w - 1)
        alb[s] = tx[yi, xi]; m = mt[yi, xi]; f0[s] = f0[s] * (1 - m) + .60 * m; rg[s] = rg[s] * (1 - m) + .26 * m; em[s] = (gl[yi, xi] ** 1.5 * pw)[:, None] * LIME if t != 2 else m[:, None] * np.array([.62, .80, .50], F)
    g = np.flatnonzero(fl)
    if len(g):
        x, y = p[g, 0], p[g, 1]; gr = hsh(np.floor(x * 46), np.floor(y * 46)); alb[g] = (np.array([.010, .019, .009], F) * (.35 + 1.5 * gr[:, None])); f0[g] = .05; rg[g] = .45
        far = np.exp(-(((x - 15.0) / 7.0) ** 2 + ((y - 9.0) / 6.5) ** 2))[:, None]; rim = np.exp(-(((x - 7.5) / 5.5) ** 2 + ((y + 1.0) / 5.0) ** 2))[:, None]
        em[g] = far * np.array([.46, .95, .06], F) * .62 + rim * np.array([.012, .036, .002], F) + (gr ** 26)[:, None] * LIME * (.03 + .42 * rim + .16 * far)
    return alb, f0, rg, em

def shade(o, d, rng):
    n = len(o); L, W = np.zeros((n, 3), F), np.ones((n, 3), F); live = np.arange(n); spec = np.ones(n, bool); dull = np.zeros(n, bool)
    for depth in range(4):
        T, I = hit(o, d); tf = np.where(d[:, 2] < -1e-5, (GROUND - o[:, 2]) / np.minimum(d[:, 2], -1e-5), np.inf); fl = tf < T; t = np.minimum(T, tf); miss = ~np.isfinite(t); L[live[miss]] += np.minimum(W[live[miss]] * env(d[miss]), np.where(dull[live[miss]], .07, 30)[:, None]); k = ~miss
        if not k.any(): break
        live, o, d, t, I, fl = live[k], o[k], d[k], t[k], I[k], fl[k]; p = o + d * t[:, None]; N = np.zeros_like(p); N[fl, 2] = 1; bi = np.flatnonzero(~fl)
        c = np.abs((p[bi] - (LO[I[bi]] + HI[I[bi]]) / 2) / ((HI[I[bi]] - LO[I[bi]]) / 2)).argmax(1); N[bi, c] = -np.sign(d[bi, c]); alb, f0, rg, em = surface(p, N, I, fl)
        s = spec[live]; lamp = (~fl) & (EM[np.maximum(I, 0)].max(1) > 0); L[live] += W[live] * np.where((s | ~lamp)[:, None], np.minimum(em, np.where(s, 60, 1.2)[:, None]), 0)
        k = ~lamp; live, p, d, N, fl, alb, f0, rg = live[k], p[k], d[k], N[k], fl[k], alb[k], f0[k], rg[k]
        if not len(live): break
        Ns = N.copy(); g = np.flatnonzero(fl)
        if len(g): j = rng.normal(0, .30, (len(g), 2)); Ns[g, 0] += j[:, 0]; Ns[g, 1] += j[:, 1]; Ns /= np.linalg.norm(Ns, axis=1, keepdims=True)
        ci = np.clip(-(d * Ns).sum(1), 0, 1); Fr = f0 + (1 - f0) * (1 - ci) ** 5 * np.where(f0 > .3, 1, .75); pr = np.clip(Fr + .08, .1, .95); mir = rng.random(len(p)) < pr; metal = f0 > .3
        W[live] *= np.where(mir, Fr / pr, (1 - Fr) / (1 - pr))[:, None] * np.where(mir[:, None], np.where(metal[:, None], np.minimum(alb * 1.35, 1), 1), alb * np.where(metal, .25, 1)[:, None]); q = p + N * 1.5e-3; spec[live] = mir; dull[live] |= (rg > .4) | ~mir; df = np.flatnonzero(~mir)
        if len(df):
            sd = SUND + rng.normal(0, .16, (len(df), 3)).astype(F); sd /= np.linalg.norm(sd, axis=1, keepdims=True); ct = (N[df] * sd).sum(1); m = np.flatnonzero(ct > 0)
            if len(m): vis = ~np.isfinite(hit(q[df[m]], sd[m])[0]); L[live[df[m]]] += W[live[df[m]]] * np.array([.50, .60, .40], F) * (ct[m] * vis)[:, None]
            e = rng.choice(len(EMI), len(df), p=EP); bx = EMI[e]; u = rng.random((len(df), 2)); tgt = np.column_stack([LO[bx, 0] + u[:, 0] * (HI[bx, 0] - LO[bx, 0]), LO[bx, 1] + u[:, 1] * (HI[bx, 1] - LO[bx, 1]), HI[bx, 2] + 1e-3]).astype(F); v = tgt - q[df]; r = np.linalg.norm(v, axis=1); v /= r[:, None]
            g = np.clip((N[df] * v).sum(1), 0, 1) * np.abs(v[:, 2]) ** .5; m = np.flatnonzero((g > 1e-4) & (v[:, 2] < .0))
            if len(m): vis = hit(q[df[m]], v[m], r[m] - 4e-3)[1] < 0; ar = (HI[bx[m], 0] - LO[bx[m], 0]) * (HI[bx[m], 1] - LO[bx[m], 1]); L[live[df[m]]] += W[live[df[m]]] * EM[bx[m]] * np.minimum(vis * g[m] * ar / EP[e[m]] / (math.pi * np.maximum(r[m] ** 2, .004)), 5)[:, None]
        a, b = rng.random(len(p)).astype(F), rng.random(len(p)).astype(F) * 2 * math.pi; hv = np.where(np.abs(N[:, :1]) > .9, np.array([[0, 1, 0]], F), np.array([[1, 0, 0]], F)); tx = np.cross(hv, N); tx /= np.linalg.norm(tx, axis=1, keepdims=True); ty = np.cross(N, tx)
        nd = tx * (np.sqrt(a) * np.cos(b))[:, None] + ty * (np.sqrt(a) * np.sin(b))[:, None] + N * np.sqrt(1 - a)[:, None]; rd = d - 2 * (d * Ns).sum(1)[:, None] * Ns + rng.normal(0, 1, p.shape).astype(F) * (rg ** 1.7)[:, None]; below = (rd * N).sum(1) < 1e-3; rd[below] = nd[below]; rd /= np.linalg.norm(rd, axis=1, keepdims=True)
        o, d = q, np.where(mir[:, None], rd, nd).astype(F)
    return L

def job(a):
    W, H, spp, seed = a; rng = np.random.default_rng(seed); acc = np.zeros((H * W, 3), F); yy, xx = np.mgrid[0:H, 0:W]; xx, yy = xx.ravel(), yy.ravel()
    for _ in range(spp):
        for s in np.array_split(np.arange(H * W), max(1, H * W // 50000)):
            sx, sy = ((xx[s] + rng.random(len(s))) / W * 2 - 1) * FOV, (1 - (yy[s] + rng.random(len(s))) / H * 2) * FOV * H / W; d = fw + sx[:, None] * rt + sy[:, None] * up; tgt = EYE + d * FOC; an, ra = rng.random(len(s)) * 2 * math.pi, APER * np.sqrt(rng.random(len(s)))
            o = EYE + rt * (ra * np.cos(an))[:, None] + up * (ra * np.sin(an))[:, None]; d = tgt - o; d /= np.linalg.norm(d, axis=1, keepdims=True); acc[s] += np.minimum(shade(o.astype(F), d.astype(F), rng), 24)
    return acc

def bokeh(W, H):
    """Glowing dust, drawn as lens discs. Particles behind the module are hidden."""
    n = 5200; r = np.random.default_rng(9); side = r.random(n); x = np.where(side < .62, r.normal(5.6, 3.6, n), r.uniform(-13, 9, n)); y = np.where(side < .62, r.normal(-1.0, 4.2, n), r.uniform(-7, 15, n)); z = GROUND + r.exponential(.10, n) + (r.random(n) < .07) * r.uniform(0, 2.6, n)
    p = np.column_stack([x, y, z]).astype(F); v = p - EYE; dep = v @ fw; u, w = (v @ rt) / dep / FOV, (v @ up) / dep / FOV * W / H; px, py = (u + 1) / 2 * W, (1 - w) / 2 * H; ok = (dep > 2) & (px > -90) & (px < W + 90) & (py > -90) & (py < H + 90)
    inside = (np.abs(x) < W2 + .25) & (np.abs(y) < H2 + .25) & (z < .5); ok &= ~inside; ok &= r.random(n) < np.clip((px / W - .38) / .34, .10, 1) ** 1.4 + np.clip((py / H - .55) / .45, 0, 1) * np.clip(px / W - .08, 0, .5); dist = np.linalg.norm(v, axis=1); hd = v / dist[:, None]; vis = hit(np.broadcast_to(EYE, v.shape).astype(F).copy(), hd.astype(F), dist.astype(F) - .02)[1] < 0; ok &= vis
    out = np.zeros((H, W, 3), F); coc = APER * np.abs(dep - FOC) / (dep * FOC) * FOC / (FOC * FOV) * W / 2 * 1.25; b = r.pareto(1.55, n) * .55 + .12
    for i in np.flatnonzero(ok):
        rad = max(.8 * W / 1760, coc[i]); k = int(rad + 2); X, Y = int(px[i]), int(py[i]); x0, x1, y0, y1 = max(X - k, 0), min(X + k + 1, W), max(Y - k, 0), min(Y + k + 1, H)
        if x0 >= x1 or y0 >= y1: continue
        gy, gx = np.mgrid[y0:y1, x0:x1]; rr = np.hypot(gx - px[i], gy - py[i]); disc = np.clip(rad - rr + .5, 0, 1) * (.72 + .28 * np.clip(rr / max(rad, 1), 0, 1) ** 3); col = LIME * (1 - .35 * r.random()) + np.array([.22, .12, .05], F) * r.random()
        out[y0:y1, x0:x1] += (disc * min(b[i], 5) * 1.35 / max(rad, .9) ** 1.18 * (W / 1760) ** .35)[..., None] * col
    return out

def grade(img, dust):
    H, W = img.shape[:2]; img = img + dust; fy, fx = np.fft.fftfreq(2 * H)[:, None], np.fft.rfftfreq(2 * W)[None]; blur = lambda a, r: np.fft.irfft2(np.fft.rfft2(a, (2 * H, 2 * W)) * np.exp(-2 * (math.pi * r) ** 2 * (fx ** 2 + fy ** 2)), (2 * H, 2 * W))[:H, :W]
    hot = np.clip(img - .5, 0, 8); img = img + sum(np.stack([blur(hot[..., c], W * r) for c in range(3)], -1) * k for r, k in ((.0016, .24), (.006, .17), (.022, .13), (.07, .07)))
    yy, xx = np.mgrid[0:H, 0:W]; img = img * (1 - .42 * np.clip(np.hypot((xx / W - .46) * 1.15, (yy / H - .48)) - .28, 0, 1))[..., None]; x = np.maximum(img * 1.95 - .022, 0); x = (x * (2.51 * x + .03)) / (x * (2.43 * x + .59) + .14)
    return Image.fromarray(np.clip(np.clip(x, 0, 1) ** (1 / 2.2) * 255 + np.random.default_rng(1).normal(0, 1.2, x.shape), 0, 255).astype(np.uint8))

if __name__ == '__main__':
    out, W, spp = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 880, int(sys.argv[3]) if len(sys.argv) > 3 else 16; H, n = W // 2, min(spp, max(1, (os.cpu_count() or 2) - 4)); parts = [spp // n + (i < spp % n) for i in range(n)]; print(len(BX), 'boxes', len(GR), 'groups', len(EMI), 'lamps', flush=True)
    with mp.Pool(n) as p: img = sum(p.map(job, [(W, H, s, 5 + i) for i, s in enumerate(parts)])) / spp
    grade(img.reshape(H, W, 3), bokeh(W, H)).save(out)
