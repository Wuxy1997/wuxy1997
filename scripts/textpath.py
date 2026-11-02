"""Outline text to SVG paths, so a panel looks the same with no fonts on the viewer's machine."""
import pathlib

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

FONTS = pathlib.Path(__file__).resolve().parent.parent / '.fonts'
UPM = 1000
_files = {}


class Face:
    def __init__(self, file, wght=None):
        font = _files.setdefault(file, TTFont(FONTS / file, lazy=True))
        self.cmap = font.getBestCmap()
        self.glyphs = font.getGlyphSet(location={'wght': wght} if wght else None)
        self.cache = {}

    def has(self, ch):
        return ord(ch) in self.cmap

    def advance(self, ch):
        return self.glyphs[self.cmap[ord(ch)]].width

    def outline(self, ch, dx):
        pen = SVGPathPen(self.glyphs, ntos=lambda v: str(round(v)))
        self.glyphs[self.cmap[ord(ch)]].draw(TransformPen(pen, (1, 0, 0, 1, dx, 0)))
        return pen.getCommands()


LIGHT = Face('Barlow-Light.ttf')
LATIN = Face('Barlow-Regular.ttf')
MEDIUM = Face('Barlow-Medium.ttf')
MONO = Face('JetBrainsMono.ttf', 400)
SANS = Face('NotoSansSC.ttf', 400)
SANS_LIGHT = Face('NotoSansSC.ttf', 300)
SANS_MEDIUM = Face('NotoSansSC.ttf', 500)
SERIF = Face('NotoSerifSC.ttf', 500)


def pick(faces, ch):
    return next((f for f in faces if f.has(ch)), None)


def advances(text, faces, size, spacing):
    """Pen position of each character in font units, plus the total width in px."""
    unit = spacing * UPM / size
    pos, x = [], 0
    for ch in text:
        pos.append(x)
        face = pick(faces, ch)
        x += (face.advance(ch) if face else UPM / 2) + unit
    return pos, (x - unit) * size / UPM if text else 0


def width(text, faces, size, spacing=0):
    return advances(text, faces, size, spacing)[1]


def path_data(text, faces, size, spacing=0):
    pos, w = advances(text, faces, size, spacing)
    parts = []
    for ch, x in zip(text, pos):
        face = pick(faces, ch)
        if face and not ch.isspace():
            parts.append(face.outline(ch, round(x)))
    return ''.join(parts), w


def glyph_data(text, faces, size, spacing=0):
    """One (path, offset px) per visible character, for per-character animation."""
    pos, w = advances(text, faces, size, spacing)
    out = []
    for ch, x in zip(text, pos):
        face = pick(faces, ch)
        if face and not ch.isspace():
            out.append((face.outline(ch, 0), x * size / UPM))
    return out, w


def wrap(text, faces, size, max_w, spacing=0, max_lines=2):
    """Greedy wrap for CJK text; closing punctuation never starts a line."""
    lines, line = [], ''
    for ch in text:
        trial = line + ch
        if width(trial, faces, size, spacing) > max_w and ch not in '，。、；：）》':
            lines.append(line)
            line = ch
        else:
            line = trial
    if line:
        lines.append(line)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = clip(lines[-1] + '…', faces, size, max_w, spacing)
    return lines


def clip(text, faces, size, max_w, spacing=0):
    if width(text, faces, size, spacing) <= max_w:
        return text
    body = text.rstrip('…')
    while body and width(body + '…', faces, size, spacing) > max_w:
        body = body[:-1]
    return body.rstrip() + '…'
