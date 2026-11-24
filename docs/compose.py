#!/usr/bin/env python3
"""Sets the titles and draws the result and how-it-works images in the green style.  First run green_module.py docs/drafts/e_render.png 1760 192.  usage: FONTS=dir compose.py"""
import json, math, os, pathlib, statistics as st, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
ROOT = pathlib.Path(__file__).resolve().parent.parent; DR, IMG = ROOT / 'docs' / 'drafts', ROOT / 'docs' / 'img'; FD = os.environ['FONTS']; S = 2
font = lambda n, s: ImageFont.truetype(f'{FD}/{n}.ttf', int(s * S)); WHITE, LIME, SOFT = (244, 248, 240), (164, 232, 42), (176, 190, 168)
runs = [r for r in map(json.loads, open(ROOT / 'data' / 'superposition.jsonl')) if r['seconds'] >= 180]
heaven = [r for r in map(json.loads, open(ROOT / 'data' / 'heaven.jsonl')) if r['finished']]
assert [sum(r['label'] == l for r in x) for x in (runs, heaven) for l in ('boost', 'stock')] == [3, 3, 4, 4]
mean = lambda l, k, x=runs: st.mean(float(r[k]) for r in x if r['label'] == l)
pct = lambda k, x=runs: 100 * (mean('boost', k, x) / mean('stock', k, x) - 1)
aml = (ROOT / 'src' / 'npcf-on.aml').read_bytes(); LIT = aml.index(bytes.fromhex('70015c4e564442')) + 1
def layer(im, fn):
    lay = Image.new('RGBA', (im.width * S, im.height * S), 0); fn(ImageDraw.Draw(lay)); lay = lay.resize(im.size, Image.LANCZOS); im.paste(lay, (0, 0), lay); return im
def txt(d, x, y, s, f, c, a='ls'): d.text((x * S, y * S), s, font=f, fill=(*c, 255), anchor=a); return d.textlength(s, font=f) / S
def arrow(d, x, y, l, c, w=7, h=24): d.line([(x * S, y * S), ((x + l) * S, y * S)], fill=(*c, 255), width=w * S); d.line([((x + l - h) * S, (y - h) * S), ((x + l) * S, y * S), ((x + l - h) * S, (y + h) * S)], fill=(*c, 255), width=w * S, joint='curve')

def hero(src):
    im = Image.open(src).convert('RGB'); W, H = im.size; a = np.asarray(im, np.float32); yy = np.linspace(0, 1, H)[:, None, None]; xx = np.linspace(0, 1, W)[None, :, None]
    a *= 1 - .72 * np.clip((yy - .80) / .20, 0, 1) ** 1.1; a *= 1 - .45 * np.clip(1 - np.hypot(xx / .55, yy / .45), 0, 1); im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    def draw(d):
        big = font('BigShoulders-Bold', 168); txt(d, 82, 82, 'DELL G15 5521 SE  /  RTX 3070 TI LAPTOP  /  LINUX', font('DMMono-Regular', 22), SOFT)
        x = 76 + txt(d, 76, 252, '115', big, WHITE) + 30; arrow(d, x, 192, 80, WHITE); x += 112; x += txt(d, x, 252, '140', big, LIME) + 16; txt(d, x, 252, 'W', font('BigShoulders-Bold', 74), WHITE)
        txt(d, 82, 312, 'Dynamic Boost, switched back on by one byte.', font('BricolageGrotesque-Bold', 31), WHITE)
        for i, (n, l) in enumerate(((f'+{pct("score"):.1f}%', 'Superposition score'), (f'+{pct("fps", heaven):.1f}%', 'Heaven FPS'), ('148 bytes', 'added, nothing flashed'))):
            x = 82 + (0, 350, 600)[i]; txt(d, x, 824, n, font('BigShoulders-Bold', 60), LIME if i < 2 else WHITE); txt(d, x + 2, 856, l, font('BricolageGrotesque-Bold', 22), WHITE)
    layer(im, draw).save(IMG / 'hero.jpg', quality=93, subsampling=0)

def backdrop(src, W, H):
    im = Image.open(src).convert('RGB').resize((W, H)).filter(ImageFilter.GaussianBlur(46)); a = np.asarray(im, np.float32) * .30; xx = np.linspace(0, 1, W)[None, :, None]; a = a * (.42 + .75 * xx) + np.array([9, 14, 9]); a += np.random.default_rng(2).normal(0, 1.3, (H, W, 1)); return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def results(src):
    W, H = 1760, 900; im = backdrop(src, W, H)
    def draw(d):
        txt(d, 82, 120, f'{pct("score"):.0f}% faster in two benchmarks', font('BigShoulders-Bold', 88), WHITE); txt(d, 82, 166, 'Mean of every full run at 2560×1440: three per boot entry in Superposition 1.1, four in Heaven 4.0.', font('BricolageGrotesque-Regular', 25), SOFT)
        L, R = 470, 1400
        for i, (lab, sub, k, x, unit, f) in enumerate((('Superposition', 'score', 'score', runs, '', ',.0f'), ('Heaven', 'average FPS', 'fps', heaven, '', '.1f'), ('Core clock', 'in Superposition', 'mhz', runs, ' MHz', ',.0f'), ('Core clock', 'in Heaven', 'mhz', heaven, ' MHz', ',.0f'), ('Power limit', 'GPU', None, None, ' W', '.0f'))):
            y = 222 + i * 120; a, b = (mean('stock', k, x), mean('boost', k, x)) if k else (115, 140); txt(d, 82, y + 42, lab, font('BricolageGrotesque-Bold', 32), WHITE); txt(d, 82, y + 72, sub, font('BricolageGrotesque-Regular', 23), SOFT); sc = (R - L) / b
            for n, (v, c, yy, h) in enumerate(((a, (110, 124, 104), y, 30), (b, LIME, y + 37, 42))):
                d.rounded_rectangle((L * S, yy * S, (L + v * sc) * S, (yy + h) * S), radius=7 * S, fill=(*c, 255), corners=(False, True, True, False)); txt(d, L + v * sc - 18, yy + h / 2, f'{v:{f}}{unit}', font('BricolageGrotesque-Bold', 24 if n else 20), (12, 18, 10) if n else (238, 243, 234), 'rm')
            txt(d, R + 34, y + 70, f'+{100 * (b / a - 1):.1f}%' if k else f'+{b - a:.0f} W', font('BigShoulders-Bold', 72), LIME)
        d.rounded_rectangle((82 * S, 842 * S, 104 * S, 864 * S), radius=5 * S, fill=(110, 124, 104, 255)); txt(d, 118, 862, 'Stock boot entry', font('BricolageGrotesque-Regular', 24), WHITE); d.rounded_rectangle((350 * S, 842 * S, 372 * S, 864 * S), radius=5 * S, fill=(*LIME, 255)); txt(d, 386, 862, 'Unlock boot entry', font('BricolageGrotesque-Regular', 24), WHITE)
    layer(im, draw).save(IMG / 'results.jpg', quality=94, subsampling=0)

def how():
    W, H, bg, ln = 1760, 900, '#0b110b', '#0b110b'; o = []; cx, cy, u = 610, 372, 27
    P = lambda x, y, z: (cx + (x - y) * u * .866, cy + (x + y) * u * .5 - z * u); pts = lambda *p: ' '.join(f'{a:.1f},{b:.1f}' for a, b in (P(*q) for q in p))
    poly = lambda fill, *p, sw=2: o.append(f'<polygon points="{pts(*p)}" fill="{fill}" stroke="{ln}" stroke-width="{sw}" stroke-linejoin="round"/>')
    def slab(x, y, z, a, b, t, c, sw=2): poly(c[1], (x, y + b, z), (x + a, y + b, z), (x + a, y + b, z - t), (x, y + b, z - t), sw=sw); poly(c[2], (x + a, y, z), (x + a, y + b, z), (x + a, y + b, z - t), (x + a, y, z - t), sw=sw); poly(c[0], (x, y, z), (x + a, y, z), (x + a, y + b, z), (x, y + b, z), sw=sw)
    def t(x, y, s, size, fam='DM Mono', fill='#f4f8f0', w=400, extra=''): o.append(f'<text x="{x}" y="{y}" font-family="{fam}" font-size="{size}" font-weight="{w}" fill="{fill}" {extra}>{s}</text>')
    PCB, GREY, LIGHT, CHIP, HOT = ('#24401c', '#182d13', '#12230e'), ('#39463a', '#283329', '#1e281f'), ('#b9c7b2', '#8e9c88', '#75836f'), ('#1d241d', '#141a14', '#0f140f'), ('#b4f02e', '#7fb41b', '#5f8a12')
    o.append('<defs><radialGradient id="g"><stop offset="0" stop-color="#9be01f" stop-opacity=".55"/><stop offset=".45" stop-color="#76b900" stop-opacity=".16"/><stop offset="1" stop-color="#76b900" stop-opacity="0"/></radialGradient></defs>')
    glow = lambda x, y, r: o.append(f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="{r}" ry="{r*.62:.0f}" fill="url(#g)"/>'); L = 10; X0 = Y0 = -5; lv = (-10.6, -4.6, .9, 6.2); g = P(0, 0, lv[0]); glow(g[0], g[1] + 10, 470); g = P(0, 2, lv[2]); glow(g[0], g[1], 400)
    for z0, z1 in zip(lv, lv[1:]):
        for (x, y) in ((X0, Y0 + L), (X0 + L, Y0)): a, b = P(x, y, z0), P(x, y, z1 - .8); o.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="#76b900" stroke-width="1.6" stroke-dasharray="2 7" stroke-linecap="round"/>')
    z = lv[0]; slab(X0, Y0, z, L, L, .7, PCB)
    for i in range(4): slab(-4.5, -4.3 + i * 2.3, z + .4, 1.2, 1.8, .4, CHIP, 1.5); slab(-2.6 + i * 1.9, -4.5, z + .4, 1.5, 1.2, .4, CHIP, 1.5)
    slab(-1.1, -1.1, z + .5, 5.2, 5.2, .5, GREY); slab(0, 0, z + .95, 3, 3, .45, HOT)
    z = lv[1]; slab(X0, Y0, z, L, L, .55, GREY)
    for i in range(6):
        for j in range(6): x, y = X0 + .75 + i * 1.45, Y0 + .75 + j * 1.45; poly('#445345' if (i + j) % 2 else '#313d32', (x, y, z), (x + 1.25, y, z), (x + 1.25, y + 1.25, z), (x, y + 1.25, z), sw=1.2)
    z = lv[2]; slab(X0, Y0, z, L, L, .45, PCB); n, q = 13, 8.8 / 13
    for k in sorted(range(148), key=lambda k: k // n + k % n): r, c = k // n, k % n; lit = k == LIT; hh = 1.9 if lit else .12 + 1.15 * aml[k] / 255; slab(X0 + .6 + c * q, Y0 + .6 + r * q, z + hh, q * .74, q * .74, hh, HOT if lit else LIGHT, 1)
    z, m = lv[3], 2.0
    for i in range(7): y = Y0 + m + .35 + i * .83; slab(X0 + m - .75, y, z - .35, .75, .42, .2, LIGHT, 1); slab(X0 + L - m, y, z - .35, .75, .42, .2, LIGHT, 1)
    slab(X0 + m, Y0 + m, z, L - 2 * m, L - 2 * m, 1.0, CHIP); a = P(X0 + m + .8, Y0 + m + .8, z); o.append(f'<ellipse cx="{a[0]}" cy="{a[1]}" rx="11" ry="6.4" fill="#39463a"/>')
    for z, n, a, b in ((lv[3], '1', 'Firmware', 'leaves the flag NVDB at 0'), (lv[2], '2', 'Added table', '148 bytes set NVDB to 1'), (lv[1], '3', 'NVIDIA driver', 'asks for Dynamic Boost, is told yes'), (lv[0], '4', 'GPU', 'limit rises from 115 W to 140 W')):
        k = 2.0 if n == '1' else 0; p = P(X0 + L - k, Y0 + k, z); x2 = 1010; c = '#b4f02e' if n in '24' else '#f4f8f0'; o.append(f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="4.5" fill="#b4f02e"/><path d="M{p[0]:.1f} {p[1]:.1f}H{x2}" stroke="#76b900" stroke-width="1.6"/>'); t(x2 + 20, p[1] + 14, n, 74, 'Big Shoulders', c, 700); t(x2 + 78, p[1] - 8, a, 38, 'Bricolage Grotesque', w=700); t(x2 + 78, p[1] + 28, b, 24, fill='#b0bea8')
    t(78, 116, 'How it', 84, 'Big Shoulders', w=700); t(78, 198, 'works', 84, 'Big Shoulders', w=700)
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d); (d / 'i.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="{bg}"/>{"".join(o)}</svg>'); (d / 'f.conf').write_text(f'<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig><include ignore_missing="yes">/etc/fonts/fonts.conf</include><dir>{FD}</dir><cachedir>{d}/c</cachedir></fontconfig>')
        subprocess.run(['inkscape', str(d / 'i.svg'), '--export-type=png', f'--export-filename={IMG / "how.png"}', '-w', str(W)], check=True, timeout=120, env=dict(os.environ, FONTCONFIG_FILE=str(d / 'f.conf')), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
src = sys.argv[1] if len(sys.argv) > 1 else DR / 'e_render.png'; hero(src); results(src); how(); print('ok')
