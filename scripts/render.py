#!/usr/bin/env python3
"""Render README.md and every SVG panel from data/content.json and data/snapshot.json.

The page is a grid of 410px tiles: two side by side on a desktop, one column on a phone,
so text stays at its real size instead of shrinking with one wide image. Only the section
bands span the full width. Each tile exists in a paper and a void version, picked by <picture>.

Every frame of a tile is complete: the block wave only passes over finished content, because
browsers hold off-screen <img> animations at time zero and a cover would stay on there.
"""
import html
import json
import math
import pathlib
import random

from pictograms import pictogram
from textpath import LATIN, LIGHT, MEDIUM, MONO, SANS, SANS_LIGHT, SERIF, UPM, clip, path_data, width, wrap

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / 'assets'
TILE, BAND = 410, 824
CUT = 14

# Same palette as the film; dim is darker on paper so small text stays readable.
THEMES = {
    'light': {'bg': '#d3cdb8', 'ink': '#1a1814', 'dim': '#585345', 'on': '#ece7d6', 'cover': '#1a1814', 'ember': '#c9521f'},
    'dark': {'bg': '#14120f', 'ink': '#ece7d6', 'dim': '#a39d8b', 'on': '#1a1814', 'cover': '#d3cdb8', 'ember': '#e8693a'},
}

CSS = '''
@keyframes wave{from,to{opacity:1}}
@keyframes blink{0%,62%{opacity:1}63%,100%{opacity:.15}}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes unspin{to{transform:rotate(-360deg)}}
@keyframes orbit{to{stroke-dashoffset:-1000}}
@keyframes sweep{0%{transform:translateY(0);opacity:0}5%,95%{opacity:.6}100%{transform:translateY(var(--h));opacity:0}}
.c{opacity:0;animation:wave .34s linear}
.blink{animation:blink 1.6s steps(1) infinite}
.spin{animation:spin 80s linear infinite}
.unspin{animation:unspin 50s linear infinite}
.orbit{animation:orbit 26s linear infinite}
.sweep{animation:sweep 8s linear 1.4s infinite}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
'''


def fract(x):
    return x - math.floor(x)


def hash12(x, y):
    """hash12 from the film's shaders, so these blocks fall the way the film's do."""
    a, b, c = fract(x * .1031), fract(y * .1031), fract(x * .1031)
    d = a * (b + 33.33) + b * (c + 33.33) + c * (a + 33.33)
    a, b, c = a + d, b + d, c + d
    return fract((a + b) * c)


def vnoise(x, y):
    ix, iy, fx, fy = math.floor(x), math.floor(y), fract(x), fract(y)
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    top = hash12(ix, iy) * (1 - fx) + hash12(ix + 1, iy) * fx
    bottom = hash12(ix, iy + 1) * (1 - fx) + hash12(ix + 1, iy + 1) * fx
    return top * (1 - fy) + bottom * fy


def fbm(x, y):
    amp, total = .5, 0
    for _ in range(4):
        total += amp * vnoise(x, y)
        x, y = 1.6 * x + 1.2 * y, -1.2 * x + 1.6 * y
        amp *= .5
    return total


def n(v):
    return f'{v:.2f}'.rstrip('0').rstrip('.')


class Sheet:
    def __init__(self, name, theme, w, h, label, inverted=False, cut=CUT):
        self.name, self.theme, self.w, self.h, self.label, self.cut = name, theme, w, h, label, cut
        self.t = THEMES[('dark' if theme == 'light' else 'light') if inverted else theme]
        self.parts = []
        self.css = CSS

    def add(self, s):
        self.parts.append(s)

    def color(self, key):
        return self.t.get(key, key)

    def rect(self, x, y, w, h, fill='ink', opacity=None, cls=None):
        o = f' opacity="{opacity}"' if opacity is not None else ''
        c = f' class="{cls}"' if cls else ''
        self.add(f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" fill="{self.color(fill)}"{o}{c}/>')

    def line(self, x1, y1, x2, y2, stroke='ink', w=1, opacity=None, cls=None):
        o = f' opacity="{opacity}"' if opacity is not None else ''
        c = f' class="{cls}"' if cls else ''
        self.add(f'<path d="M{n(x1)} {n(y1)}L{n(x2)} {n(y2)}" fill="none" stroke="{self.color(stroke)}" stroke-width="{w}"{o}{c}/>')

    def text(self, s, x, y, faces, size, spacing=0, fill='ink', anchor='start', opacity=None):
        d, w = path_data(s, faces, size, spacing)
        x0 = x - (w if anchor == 'end' else w / 2 if anchor == 'middle' else 0)
        k = size / UPM
        o = f' opacity="{opacity}"' if opacity is not None else ''
        self.add(f'<path transform="translate({n(x0)} {n(y)}) scale({k:.4f} {-k:.4f})" fill="{self.color(fill)}"{o} d="{d}"/>')
        return x0, w

    def outline(self):
        w, h, c = self.w, self.h, self.cut
        return f'M0 0H{w - c}L{w} {c}V{h}H{c}L0 {h - c}Z'

    def plate(self, grid=20):
        ink = self.t['ink']
        self.add(f'<defs><clipPath id="k"><path d="{self.outline()}"/></clipPath>'
                 f'<pattern id="g" width="{grid}" height="{grid}" patternUnits="userSpaceOnUse"><path d="M{grid} 0H0V{grid}" fill="none" stroke="{ink}" stroke-width=".6" opacity=".1"/></pattern>'
                 f'<pattern id="h" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="1.7" height="5" fill="{ink}"/></pattern>'
                 f'<radialGradient id="v" cx=".5" cy=".5" r=".78"><stop offset=".5" stop-color="{ink}" stop-opacity="0"/><stop offset="1" stop-color="{ink}" stop-opacity=".12"/></radialGradient></defs>'
                 '<g clip-path="url(#k)">')
        self.rect(0, 0, self.w, self.h, 'bg')
        self.add(f'<rect width="{self.w}" height="{self.h}" fill="url(#g)"/><rect width="{self.w}" height="{self.h}" fill="url(#v)"/>')

    def finish(self, start=.1, span=.5, cell=20):
        self.wave(cell, start, span)
        self.add('</g>')
        self.add(f'<path d="{self.outline()}" fill="none" stroke="{self.t["ink"]}" stroke-width="1.5" opacity=".55"/>')

    def wave(self, cell, start, span, levels=10):
        """Port of the block dissolve in POST_FRAG: noise leaning from top to bottom."""
        cols, rows = math.ceil(self.w / cell), math.ceil(self.h / cell)
        buckets = [[] for _ in range(levels)]
        for r in range(rows):
            for c in range(cols):
                v = hash12(c + 3, r + 3) * .65 + (r / rows) * .35
                buckets[min(levels - 1, int((v + .18) / 1.36 * levels))].append(f'M{c * cell} {r * cell}h{cell}v{cell}h-{cell}z')
        for i, cells in enumerate(buckets):
            if cells:
                self.add(f'<path class="c" style="animation-delay:{start + span * i / levels:.2f}s" fill="{self.t["cover"]}" d="{"".join(cells)}"/>')

    def hatch(self, x, y, w, h, opacity=None):
        o = f' opacity="{opacity}"' if opacity is not None else ''
        self.add(f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" fill="url(#h)"{o}/>')

    def barcode(self, x, y, w, h, seed):
        px, i, d = x, 0, []
        while True:
            bar = 1 + int(hash12(i, seed) * 3.4)
            gap = 1 + int(hash12(i + 40, seed) * 3.4)
            if px + bar > x + w:
                break
            d.append(f'M{px} {y}h{bar}v{h}h-{bar}z')
            px += bar + gap
            i += 1
        self.add(f'<path fill="{self.t["ink"]}" d="{"".join(d)}"/>')

    def ruler(self, x, y, w, step=4, major=5, h=4, tall=8, opacity=.6):
        d = ''.join(f'M{n(x + i * step)} {n(y)}v{tall if i % major == 0 else h}' for i in range(int(w / step) + 1))
        self.add(f'<path d="{d}" fill="none" stroke="{self.t["ink"]}" opacity="{opacity}"/>')

    def corner(self, x, y, sx, sy, tick=12):
        self.add(f'<path d="M{n(x + tick * sx)} {n(y)}H{n(x)}V{n(y + tick * sy)}" fill="none" stroke="{self.t["ink"]}" stroke-width="1.6"/>')

    def svg(self):
        title = html.escape(self.label)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}" role="img" aria-label="{title}">'
                f'<title>{title}</title><style>{" ".join(self.css.split())}</style>{"".join(self.parts)}</svg>')

    def save(self):
        (ASSETS / f'{self.name}-{self.theme}.svg').write_text(self.svg(), 'utf-8')


def title_bar(sh, cn, en, right=None):
    x, y, w, h = 10, 10, sh.w - 20, 28
    sh.add(f'<path fill="{sh.t["ink"]}" d="M{x} {y}H{x + w - 9}L{x + w} {y + 9}V{y + h}H{x}Z"/>')
    sh.rect(x + 10, y + 10, 8, 8, 'on')
    x0, wd = sh.text(cn, x + 27, y + 19, [SERIF], 13.5, 2, 'on')
    sh.text(en, x0 + wd + 12, y + 18.5, [LIGHT], 10.5, 2.6, 'on', opacity=.75)
    if right:
        sh.text(right, x + w - 16, y + 18.5, [MONO], 10, .8, 'on', 'end', opacity=.75)


def moon(sh, cx, cy, R, pitch=2.9):
    """Stippled sphere: density follows the light, so ink gathers in the shadow on paper
    and light gathers on the sunlit side on void."""
    r = random.Random(72)
    craters = [(r.uniform(-.8, .8), r.uniform(-.8, .8), r.uniform(.05, .17)) for _ in range(16)]
    lx, ly, lz = -.56, -.5, .66
    paper = sh.t['ink'] == THEMES['light']['ink']
    pts = []
    y = -R
    while y < R:
        x = -R
        while x < R:
            px = x + (r.random() - .5) * pitch * .9
            py = y + (r.random() - .5) * pitch * .9
            x += pitch
            if px * px + py * py > R * R:
                r.random()
                continue
            nx, ny = px / R, py / R
            nz = math.sqrt(max(0, 1 - nx * nx - ny * ny))
            lit = max(0, nx * lx + ny * ly + nz * lz)
            maria = fbm(nx * 2.6 + 7, ny * 2.6 + 3) - .5
            rim = 0
            for cxx, cyy, cr in craters:
                d = math.hypot(nx - cxx, ny - cyy) / cr
                if d < 1:
                    rim += .4 * (cxx * lx + cyy * ly - (nx - cxx) * lx * 5 - (ny - cyy) * ly * 5) * (1 - d)
                if .9 < d < 1.12:
                    rim += .26
            shade = min(1, max(0, lit + maria * .75 - rim))
            tone = .05 + (1 - shade) ** 1.7 * .9 + (1 - nz) ** 4 * .4 if paper else .04 + shade ** 1.5 * 1.02
            if r.random() < tone:
                pts.append((round(px, 1), round(py, 1)))
        y += pitch
    d, ox, oy = [], None, None
    for px, py in pts:
        if ox is None:
            d.append(f'M{n(cx + px)} {n(cy + py)}h.01')
        else:
            d.append(f'm{n(px - ox - .01)} {n(py - oy)}h.01')
        ox, oy = px, py
    sh.add(f'<path d="{"".join(d)}" fill="none" stroke="{sh.t["ink"]}" stroke-width="1.5" stroke-linecap="square"/>')
    sh.add(f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="{sh.t["ink"]}" stroke-width=".8" opacity=".55"/>')


def orbit_system(sh, cx, cy, R):
    ink = sh.t['ink']
    outer = R + 22
    ticks = ''.join(
        f'M{n(math.cos(a) * (outer - (8 if i % 6 == 0 else 3)))} {n(math.sin(a) * (outer - (8 if i % 6 == 0 else 3)))}L{n(math.cos(a) * outer)} {n(math.sin(a) * outer)}'
        for i, a in ((j, math.tau * j / 72) for j in range(72)))
    sh.add(f'<g transform="translate({cx} {cy})"><g class="spin"><path d="{ticks}" fill="none" stroke="{ink}" opacity=".7"/></g>'
           f'<g class="unspin"><circle r="{R + 10}" fill="none" stroke="{ink}" stroke-dasharray="52 16 3 16" opacity=".55"/></g></g>')
    e = f'cx="0" cy="0" rx="{R + 58}" ry="{n((R + 58) * .25)}" pathLength="1000" fill="none"'
    sh.add(f'<g transform="translate({cx} {cy}) rotate(-17)"><ellipse {e} stroke="{ink}" stroke-dasharray="4 7" opacity=".7"/>'
           f'<ellipse class="orbit" {e} stroke="{sh.t["ember"]}" stroke-width="7" stroke-dasharray="11 989"/></g>')


def id_plate(theme, c, s):
    W, H = TILE, 320
    sh = Sheet('hero-id', theme, W, H, f'{c["name"]}（{c["handle"]}）：{c["role"]}。{c["motto"]}', inverted=True)
    sh.plate()
    sh.text('WU', W + 8, H - 6, [LIGHT], 250, 0, 'ink', 'end', opacity=.07)
    sh.hatch(0, 0, 8, H)
    sh.rect(22, 25, 8, 8, 'ink')
    sh.text(f'{c["handle"]} // PERSONAL RECORD', 38, 33, [LATIN], 11.5, 2.4, 'dim')
    sh.rect(W - 80, 25, 8, 8, 'ember', cls='blink')
    sh.text('ONLINE', W - 18, 33, [MONO], 10.5, 1.4, 'dim', 'end')
    sh.text(c['name'], 22, 112, [SERIF, MEDIUM], 66, 4)
    sh.rect(22, 128, 10, 10, 'ink')
    sh.line(22, 133, W - 18, 133, 'ink', 2)
    sh.ruler(40, 140, W - 60, 4, 5, 3, 6, .5)
    sh.text(c['role'], 22, 176, [SERIF], 17, 2.6)
    sh.text(c['role_en'], 22, 196, [LIGHT], 10.5, 1.9, 'dim')
    sh.text(c['motto'], 22, 234, [SERIF], 15, 2.6)
    sh.text(c['motto_en'], 22, 253, [LIGHT], 9.6, 1.5, 'dim')
    sh.barcode(22, 270, 230, 30, 9)
    sh.text(f'SINCE {s["since"][:4]}', W - 18, 283, [MONO], 10, 1, 'dim', 'end')
    sh.text(f'SYNC {s["generated_at"]}', W - 18, 299, [MONO], 10, 1, 'dim', 'end')
    sh.finish(.12, .5)
    return sh


def core_plate(theme, c, s):
    W, H = TILE, 320
    cx, cy, R = 205, 162, 104
    sh = Sheet('hero-core', theme, W, H, f'点描月面与轨道：公开仓库 {s["public_repos"]}，日志 {len(s["posts"])}，起始 {s["since"][:4]}')
    sh.css += f'.sweep{{--h:{H}px}}'
    sh.plate()
    sh.ruler(14, 14, W - 42, 4, 5, 3, 7, .55)
    sh.ruler(14, H - 22, W - 42, 4, 5, 3, 7, .55)
    moon(sh, cx, cy, R)
    orbit_system(sh, cx, cy, R)

    def tag(label, value, x, y, px, py, anchor):
        sh.line(px, py, x + (6 if anchor == 'start' else -6), y - 4, 'ink', 1, .75)
        sh.rect(px - 3, py - 3, 6, 6, 'ink')
        sh.text(label, x + (10 if anchor == 'start' else -10), y - 11, [LIGHT], 9.5, 1.8, 'dim', anchor)
        sh.text(value, x + (10 if anchor == 'start' else -10), y + 4, [MONO], 13, 1, 'ink', anchor)

    tag('PUBLIC REPOS', f'{s["public_repos"]:03d}', 306, 54, cx + 62, cy - 78, 'start')
    tag('LOG ENTRIES', f'{len(s["posts"]):03d}', 104, 280, cx - 66, cy + 72, 'end')
    tag('LAST PUSH', s['last_push']['date'], 262, 282, cx + 76, cy + 62, 'start')
    sh.text('OBSERVATION', 16, 46, [LIGHT], 10, 2.4, 'dim')
    sh.text('RECORD 01', 16, 60, [MONO], 10, 1, 'dim')
    sh.line(0, 0, W, 0, 'ember', 1, cls='sweep')
    sh.finish(.28, .5)
    return sh


def stats_tile(theme, c, s):
    W, H = TILE, 228
    sh = Sheet('stats', theme, W, H, f'状态：公开仓库 {s["public_repos"]} 个，日志 {len(s["posts"])} 篇，最近推送 {s["last_push"]["date"]}')
    sh.plate()
    title_bar(sh, '状态', 'STATUS', f'SYNC {s["generated_at"]}')
    cells = [('公开仓库', 'PUBLIC REPOS', f'{s["public_repos"]:03d}'),
             ('日志条目', 'LOG ENTRIES', f'{len(s["posts"]):03d}'),
             ('记录起始', 'ACTIVE SINCE', s['since'][:4])]
    cw = (W - 20) / 3
    for i, (cn, en, value) in enumerate(cells):
        x = 10 + i * cw
        if i == 1:
            sh.rect(x, 44, cw, 96, 'ink')
        fg = 'on' if i == 1 else 'ink'
        fd = 'on' if i == 1 else 'dim'
        sh.text(cn, x + 12, 64, [SANS], 11.5, 1.2, fg)
        sh.text(en, x + 12, 78, [LIGHT], 9, 1.5, fd, opacity=.8 if i == 1 else None)
        sh.text(value, x + 11, 126, [LIGHT], 42, 1, fg)
    sh.add(f'<path d="M10 44H{W - 10}V140H10Z" fill="none" stroke="{sh.t["ink"]}" opacity=".55"/>')
    latest = s['posts'][0]
    rows = [('最近推送', 'LAST PUSH', s['last_push']['date'], s['last_push']['repo']),
            ('最近日志', 'LATEST LOG', latest['date'], latest['title'])]
    for i, (cn, en, date, what) in enumerate(rows):
        y = 164 + i * 30
        sh.rect(10, y - 9, 4, 12, 'ink')
        sh.text(cn, 22, y + 1, [SANS], 11, 1)
        sh.text(date, 84, y + 1, [MONO], 10.5, .3, 'dim')
        sh.text(clip(what, [SANS_LIGHT, MONO], 11, W - 176, .2), 164, y + 1, [SANS_LIGHT, MONO], 11, .2)
        sh.line(10, y + 11, W - 10, y + 11, 'ink', 1, .22)
    sh.finish(.1, .45)
    return sh


def langs_tile(theme, c, s):
    W, H = TILE, 228
    names = '、'.join(f'{l["name"]} {l["pct"]}%' for l in s['languages'])
    sh = Sheet('langs', theme, W, H, f'语言构成：{names}')
    sh.plate()
    title_bar(sh, '语言', 'LANGUAGES', 'PUBLIC REPOS')
    top = s['languages'][0]['pct'] or 1
    cells, pitch = 34, 6.6
    x0 = 92
    for i, lang in enumerate(s['languages']):
        y = 58 + i * 28
        sh.text(lang['name'], 16, y + 11, [MONO], 11.5, .3, 'ink')
        lit = max(1, round(cells * lang['pct'] / top))
        on = ''.join(f'M{n(x0 + k * pitch)} {y}h5v14h-5z' for k in range(lit))
        off = ''.join(f'M{n(x0 + k * pitch)} {y + 10}h5v4h-5z' for k in range(lit, cells))
        sh.add(f'<path fill="{sh.t["ink"]}" d="{on}"/>')
        if off:
            sh.add(f'<path fill="{sh.t["ink"]}" opacity=".3" d="{off}"/>')
        sh.text(f'{lang["pct"]:.1f}', W - 14, y + 11, [MONO], 11, .3, 'dim', 'end')
    sh.ruler(20, H - 33, W - 46, 4, 5, 3, 6, .5)
    sh.text('BY BYTES / MARKUP EXCLUDED', 20, H - 12, [LIGHT], 9, 1.5, 'dim')
    sh.finish(.2, .45)
    return sh


def chips(sh, items, x, y, right, solid):
    faces, size, pad = ([SANS], 11, 9) if solid else ([MONO, SANS], 10.5, 8)
    cx = x
    for item in items:
        wd = width(item, faces, size, .5) + pad * 2
        if cx + wd > right:
            cx, y = x, y + 25
        if solid:
            sh.rect(cx, y - 14, wd, 20, 'ink')
        else:
            sh.add(f'<rect x="{n(cx)}" y="{y - 14}" width="{n(wd)}" height="20" fill="none" stroke="{sh.t["ink"]}" opacity=".7"/>')
        sh.text(item, cx + pad, y + .5, faces, size, .5, 'on' if solid else 'ink')
        cx += wd + 6
    return y


def loadout_tile(theme, c):
    W, H = TILE, 168
    sh = Sheet('loadout', theme, W, H, f'装备：{"、".join(c["languages"])}；工具：{"、".join(c["tools"])}')
    sh.plate()
    title_bar(sh, '装备', 'LOADOUT')
    sh.text('语言', 16, 72, [SANS], 11.5, 1.2)
    sh.text('LANG', 16, 85, [LIGHT], 8.6, 1.4, 'dim')
    chips(sh, c['languages'], 62, 73, W - 12, False)
    sh.line(16, 96, W - 16, 96, 'ink', 1, .25)
    sh.text('工具', 16, 118, [SANS], 11.5, 1.2)
    sh.text('TOOLS', 16, 131, [LIGHT], 8.6, 1.4, 'dim')
    chips(sh, c['tools'], 62, 119, W - 12, False)
    sh.finish(.15, .4)
    return sh


def fields_tile(theme, c):
    W, H = TILE, 168
    sh = Sheet('fields', theme, W, H, f'方向：{"、".join(f["cn"] for f in c["fields"])}')
    sh.plate()
    title_bar(sh, '方向', 'FIELDS')
    chips(sh, [f['cn'] for f in c['fields']], 16, 72, W - 12, True)
    sh.line(16, 88, W - 16, 88, 'ink', 1, .25)
    for i, item in enumerate(c['interests'][:4]):
        x = 16 + (i % 2) * 190
        y = 110 + (i // 2) * 21
        sh.rect(x, y - 8, 5, 5, 'ink')
        sh.text(item, x + 11, y, [SANS_LIGHT], 11, .3)
    sh.hatch(W - 120, H - 26, 104, 12)
    sh.finish(.25, .4)
    return sh


def band(theme, key, cn, en, right):
    W, H = BAND, 56
    sh = Sheet(f'band-{key}', theme, W, H, f'{cn} {en}：{right}', inverted=True, cut=12)
    sh.plate(14)
    sh.rect(14, 22, 12, 12, 'ink')
    x, w = sh.text(cn, 38, 38, [SERIF], 25, 4)
    x2, w2 = sh.text(en, x + w + 16, 36, [LIGHT], 15, 4, 'dim')
    rx, rw = sh.text(right, W - 38, 34, [MONO], 13, 1, 'ink', 'end')
    sh.add(f'<path d="M{W - 28} 22l9 6-9 6" fill="none" stroke="{sh.t["ink"]}" stroke-width="1.8"/>')
    x3 = x2 + w2 + 18
    sh.hatch(x3, 22, rx - 18 - x3, 12, .8)
    sh.finish(.1, .35, 14)
    return sh


def card(theme, p, i):
    W, H = TILE, 172
    sh = Sheet(f'project-{p["id"]}', theme, W, H, f'{p["title"]}：{p["cn"]}。{p["desc"]}')
    sh.plate()
    sh.rect(0, 0, 6, H - CUT, 'ink')
    sh.rect(18, 17, 8, 8, 'ink')
    sh.text(clip(p['title'], [MEDIUM], 17, 240, 1.2), 34, 27, [MEDIUM], 17, 1.2)
    tag_w = width(p['tag'], [LATIN], 9.5, 1.6) + 14
    sh.text(f'{i + 1:02d}', W - 28, 27, [MONO], 11, .6, 'dim', 'end')
    sh.rect(W - 34 - tag_w - 20, 15, tag_w, 15, 'ink')
    sh.text(p['tag'], W - 34 - tag_w - 13, 26, [LATIN], 9.5, 1.6, 'on')
    sh.line(18, 38, W - 12, 38, 'ink', 1, .5)
    sh.text(p['cn'], 18, 60, [SERIF], 14, 2)
    for j, text in enumerate(wrap(p['desc'], [SANS_LIGHT, SANS], 12, 236, .2, 3)):
        sh.text(text, 18, 83 + j * 19, [SANS_LIGHT, SANS], 12, .2)
    sh.text(clip(' / '.join(p['stack']), [MONO], 10, 240, .3), 18, H - 14, [MONO], 10, .3, 'dim')
    size, px, py = 112, W - 128, 48
    k = size / 120
    sh.add(f'<g transform="translate({px} {py}) scale({k:.3f})" color="{sh.t["ink"]}" style="--pict-bg:{sh.t["bg"]}">{pictogram(p["id"])}</g>')
    sh.finish(.12 + (i // 2) * .1 + (i % 2) * .05, .4)
    return sh


def log_tile(theme, post, i):
    W, H = TILE, 68
    sh = Sheet(f'log-{i}', theme, W, H, f'{post["date"]} {post["category"]}：{post["title"]}', cut=10)
    sh.plate()
    sh.text(f'{i + 1:02d}', W - 28, H - 6, [LIGHT], 64, 0, 'ink', 'end', opacity=.07)
    sh.rect(0, 0, 6, H - 10, 'ink')
    sh.text(post['date'], 18, 24, [MONO], 10.5, .3, 'dim')
    wd = width(post['category'], [SANS], 10, .8) + 12
    sh.rect(96, 13, wd, 15, 'ink')
    sh.text(post['category'], 102, 24.5, [SANS], 10, .8, 'on')
    sh.line(96 + wd + 8, 20.5, W - 12, 20.5, 'ink', 1, .3)
    sh.text(clip(post['title'], [SANS, MEDIUM], 13.5, W - 58, .3), 18, 50, [SANS, MEDIUM], 13.5, .3)
    sh.add(f'<path d="M{W - 24} 40l6 5-6 5" fill="none" stroke="{sh.t["ink"]}" stroke-width="1.5"/>')
    sh.finish(.1 + (i // 2) * .08, .3, 14)
    return sh


def foot_left(theme, c, s):
    W, H = TILE, 76
    sh = Sheet('foot-motto', theme, W, H, c['motto'], inverted=True)
    sh.plate()
    sh.rect(16, 22, 8, 8, 'ink')
    sh.text(c['motto'], 34, 31, [SERIF], 15, 2.4)
    sh.text('END OF RECORD', 34, 53, [LIGHT], 10, 3, 'dim')
    sh.barcode(W - 118, 42, 100, 18, 21)
    sh.finish(.1, .3)
    return sh


def foot_right(theme):
    W, H = TILE, 76
    sh = Sheet('foot-credit', theme, W, H, '界面风格致敬 NieR:Automata，非官方作品')
    sh.plate()
    sh.hatch(0, 0, 8, H)
    sh.text('界面风格致敬 NieR:Automata', 22, 31, [SERIF, MEDIUM], 13, 1.4)
    sh.text('非官方作品，与游戏版权方无关', 22, 52, [SANS_LIGHT], 11, .8, 'dim')
    sh.finish(.15, .3)
    return sh


def picture(name, alt, width_px):
    a = html.escape(alt, quote=True)
    return (f'<picture><source media="(prefers-color-scheme: dark)" srcset="assets/{name}-dark.svg">'
            f'<source media="(prefers-color-scheme: light)" srcset="assets/{name}-light.svg">'
            f'<img src="assets/{name}-light.svg" alt="{a}" width="{width_px}"></picture>')


def linked(url, name, alt, width_px):
    return f'<a href="{url}">{picture(name, alt, width_px)}</a>'


def readme(c, s, projects, posts):
    links = c['links']
    login = c['login']
    langs = '、'.join(l['name'] for l in s['languages'])
    rows = ['<!-- Generated by scripts/render.py from data/. Edit the data, not this file. -->',
            '<div align="center">',
            linked(links['home'], 'hero-id', f'{c["name"]}（{c["handle"]}）：{c["role"]}。{c["motto"]}', TILE),
            linked(links['home'], 'hero-core', f'公开仓库 {s["public_repos"]} 个，日志 {len(s["posts"])} 篇', TILE),
            '<br>',
            linked(links['repos'], 'stats', f'公开仓库 {s["public_repos"]} 个，日志 {len(s["posts"])} 篇', TILE),
            picture('langs', f'语言构成：{langs}', TILE),
            '<br>',
            picture('loadout', '语言：' + '、'.join(c['languages']) + '；工具：' + '、'.join(c['tools']), TILE),
            linked(links['about'], 'fields', '方向：' + '、'.join(f['cn'] for f in c['fields']), TILE),
            '<br><br>',
            linked(links['repos'], 'band-projects', '项目 PROJECTS：全部仓库', BAND),
            '<br>']
    for p in projects:
        rows.append(linked(f'https://github.com/{login}/{p["repo"]}', f'project-{p["id"]}', f'{p["title"]}：{p["cn"]}。{p["desc"]}', TILE))
    rows += ['<br><br>', linked(links['archive'], 'band-log', '日志 LOG：全部归档', BAND), '<br>']
    for i, post in enumerate(posts):
        rows.append(linked(post['url'], f'log-{i}', f'{post["date"]} {post["title"]}', TILE))
    rows += ['<br><br>',
             picture('foot-motto', c['motto'], TILE),
             linked(links['about'], 'foot-credit', '界面风格致敬 NieR:Automata，非官方作品', TILE),
             '</div>']
    return '\n'.join(rows) + '\n'


def main():
    c = json.loads((ROOT / 'data' / 'content.json').read_text('utf-8'))
    s = json.loads((ROOT / 'data' / 'snapshot.json').read_text('utf-8'))
    ASSETS.mkdir(exist_ok=True)
    for old in ASSETS.glob('*.svg'):
        old.unlink()
    projects = [p for p in c['projects'] if p.get('readme')]
    posts = s['posts'][:6]
    for theme in THEMES:
        sheets = [id_plate(theme, c, s), core_plate(theme, c, s), stats_tile(theme, c, s), langs_tile(theme, c, s),
                  loadout_tile(theme, c), fields_tile(theme, c),
                  band(theme, 'projects', '项目', 'PROJECTS', 'ALL REPOSITORIES'),
                  band(theme, 'log', '日志', 'LOG', f'ARCHIVE {len(s["posts"]):03d}'),
                  foot_left(theme, c, s), foot_right(theme)]
        sheets += [card(theme, p, i) for i, p in enumerate(projects)]
        sheets += [log_tile(theme, post, i) for i, post in enumerate(posts)]
        for sheet in sheets:
            sheet.save()
    (ROOT / 'README.md').write_text(readme(c, s, projects, posts), 'utf-8')
    files = list(ASSETS.glob('*.svg'))
    print(f'{len(files)} svg, {sum(f.stat().st_size for f in files) // 1024} KB')


if __name__ == '__main__':
    main()
