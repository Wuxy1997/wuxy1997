"""Line-art marks, one per project, drawn in a 120x120 box. Colour comes from currentColor."""
import math


def hatch(x, y, w, h, step=5):
    """Diagonal strokes clipped to a rectangle."""
    d = []
    k = step
    while k < w + h:
        x1, y1 = (x + k, y) if k <= w else (x + w, y + k - w)
        x2, y2 = (x, y + k) if k <= h else (x + k - h, y + h)
        d.append(f'M{x1:.1f} {y1:.1f}L{x2:.1f} {y2:.1f}')
        k += step
    return f'<path d="{"".join(d)}" fill="none" stroke="currentColor" stroke-width=".9"/>'


def line(d, w=1.2, o=None, dash=None):
    op = f' opacity="{o}"' if o else ''
    da = f' stroke-dasharray="{dash}"' if dash else ''
    return f'<path d="{d}" fill="none" stroke="currentColor" stroke-width="{w}"{op}{da}/>'


def box(x, y, w, h, sw=1.2):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="currentColor" stroke-width="{sw}"/>'


def solid(x, y, w, h):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="currentColor"/>'


def dot(x, y, r, fill=True):
    style = 'fill="currentColor"' if fill else 'fill="none" stroke="currentColor" stroke-width="1.2"'
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" {style}/>'


def storyboard():
    out = [box(2, 8, 54, 36), box(64, 8, 54, 36), box(2, 52, 54, 36), box(64, 52, 54, 36)]
    out.append(hatch(64, 8, 54, 36))
    out.append(line('M8 36L22 22L32 31L40 25L50 36'))
    out.append(dot(44, 18, 3))
    out.append(solid(64, 52, 54, 36))
    out.append('<path d="M84 61l16 9-16 9z" fill="var(--pict-bg,#d3cdb8)"/>')
    out.append(line('M8 62H50M8 70H42M8 78H46', 1))
    for x in range(4, 118, 8):
        out.append(solid(x, 96, 4, 4))
        out.append(solid(x, 112, 4, 4))
    out.append(line('M2 106H118', 1, .5))
    out.append(solid(2 + 72, 103, 6, 6))
    return ''.join(out)


def federated():
    out = []
    cx, cy, n, r = 60, 60, 6, 44
    nodes = [(cx + r * math.cos(math.tau * i / n - math.pi / 2), cy + r * math.sin(math.tau * i / n - math.pi / 2)) for i in range(n)]
    out.append(f'<circle cx="60" cy="60" r="56" fill="none" stroke="currentColor" stroke-width=".8" stroke-dasharray="2 5"/>')
    for i, (x, y) in enumerate(nodes):
        out.append(line(f'M60 60L{x:.1f} {y:.1f}', 1, None, '3 3' if i % 2 else None))
        nx, ny = nodes[(i + 1) % n]
        out.append(line(f'M{x:.1f} {y:.1f}L{nx:.1f} {ny:.1f}', .8, .55))
    for i, (x, y) in enumerate(nodes):
        out.append(dot(x, y, 6.5, i % 2 == 0))
        if i % 2:
            out.append(dot(x, y, 2.4))
    out.append(solid(49, 49, 22, 22))
    out.append('<rect x="55" y="55" width="10" height="10" fill="var(--pict-bg,#d3cdb8)"/>')
    return ''.join(out)


def helix():
    a, b, rungs = [], [], []
    for i in range(61):
        t = i / 60
        y = 2 + t * 116
        p = t * math.tau * 1.6
        a.append((60 + math.sin(p) * 38, y))
        b.append((60 - math.sin(p) * 38, y))
    path = lambda pts: 'M' + 'L'.join(f'{x:.1f} {y:.1f}' for x, y in pts)
    for i in range(3, 60, 4):
        (x1, y1), (x2, y2) = a[i], b[i]
        rungs.append(line(f'M{x1:.1f} {y1:.1f}L{x2:.1f} {y2:.1f}', 1, .6))
        if i % 12 == 3:
            rungs.append(solid((x1 + x2) / 2 - 3, y1 - 3, 6, 6))
    return ''.join(rungs) + line(path(a), 2.4) + line(path(b), 1.2, None, '4 3')


def bucket():
    out = []
    for y in (12, 44, 76):
        out.append(f'<ellipse cx="46" cy="{y}" rx="42" ry="10" fill="none" stroke="currentColor" stroke-width="1.2"/>')
        out.append(line(f'M4 {y}V{y + 22}A42 10 0 0 0 88 {y + 22}V{y}', 1.2))
    out.append(f'<ellipse cx="46" cy="76" rx="42" ry="10" fill="currentColor"/>')
    out.append(solid(12, 26, 16, 3))
    out.append(solid(12, 58, 16, 3))
    out.append(line('M100 12V100H92M100 56H92M100 12H92', 1))
    out.append(solid(96, 52, 8, 8))
    out.append(solid(96, 96, 8, 8))
    out.append(solid(96, 8, 8, 8))
    out.append(line('M104 56H118', 1, .6, '2 2'))
    return ''.join(out)


def split_page():
    out = [line('M8 6H52L66 20V82H8Z', 1.2), line('M52 6V20H66', 1.2)]
    out.append(line('M16 30H56M16 38H58M16 46H48M16 54H56M16 62H42', 1))
    out.append(solid(54, 38, 54, 76))
    out.append('<path d="M60 46h42v60H60z" fill="none" stroke="var(--pict-bg,#d3cdb8)" stroke-width="1"/>')
    out.append('<path d="M66 58h30M66 66h26M66 74h30M66 82h18" fill="none" stroke="var(--pict-bg,#d3cdb8)" stroke-width="1"/>')
    out.append(line('M0 100L52 24', 1, None, '4 4'))
    return ''.join(out)


def pulse():
    out = [box(2, 18, 116, 84, 1)]
    for x in range(22, 118, 20):
        out.append(line(f'M{x} 18V102', .7, .4))
    for y in (46, 74):
        out.append(line(f'M2 {y}H118', .7, .4))
    out.append(line('M2 66H30L38 66L44 44L54 92L64 28L72 80L78 66H118', 2))
    out.append(solid(61, 25, 6, 6))
    for i in range(12):
        out.append(solid(4 + i * 10, 108, 7, 8 if i < 8 else 3))
    return ''.join(out)


def report():
    out = [box(2, 4, 116, 112)]
    for i, h in enumerate((22, 40, 30, 58, 46, 70)):
        out.append(solid(12 + i * 13, 74 - h, 9, h))
    out.append(line('M10 76H94', 1))
    out.append(hatch(98, 14, 12, 60, 4))
    out.append(line('M12 88H108M12 96H92M12 104H100', 1))
    return ''.join(out)


def grid_game():
    out = []
    snake = {(0, 1), (1, 1), (2, 1), (3, 1), (3, 2), (3, 3), (2, 3)}
    for r in range(6):
        for c in range(6):
            x, y = 3 + c * 19.5, 3 + r * 19.5
            if (c, r) in snake:
                out.append(solid(x, y, 16, 16))
            else:
                out.append(box(x + 6.5, y + 6.5, 3, 3, .8))
    out.append(solid(84, 84, 16, 16))
    return ''.join(out)


PICTS = {
    'storyboarder': storyboard, 'frl-mec': federated, 'sars-analyzer': helix, 'oss-manager': bucket,
    'pdf-splitter': split_page, 'health-tracker': pulse, 'auto-reports': report, 'mini-games': grid_game,
}


def pictogram(key):
    return PICTS[key]()
