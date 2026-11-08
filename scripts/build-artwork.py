"""Builds the static artwork (bookplate header, bookshelf volumes, desk toolkit) and README.md.

Text is converted to outline paths so the SVGs do not depend on the visitor's fonts.
Needs Python `fonttools` and the macOS fonts Georgia, Georgia Italic, Arial and Songti.
On another machine, copy those four files into one folder and set FONT_DIR to it.
"""
from pathlib import Path
import re
import math
import html
import os
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
FONT_DIR = Path(os.environ.get('FONT_DIR', '/System/Library/Fonts/Supplemental'))
FONTS = {
    'serif': TTFont(FONT_DIR / 'Georgia.ttf'),
    'italic': TTFont(FONT_DIR / 'Georgia Italic.ttf'),
    'sans': TTFont(FONT_DIR / 'Arial.ttf'),
    'zh': TTFont(FONT_DIR / 'Songti.ttc', fontNumber=0),
}
PALETTES = {
    'light': dict(bg='#f8f5ec', panel='#edf0e5', ink='#273d35', muted='#6e7568', line='#dedbcf', green='#386653', gold='#a67a46', pale='#e6e9df'),
    'dark': dict(bg='#18241f', panel='#22362a', ink='#e9e6d8', muted='#a5b0a1', line='#36473d', green='#91b49b', gold='#c6a273', pale='#293b30'),
}


def measure(s, size, font='serif', spacing=0):
    f = FONTS[font]
    glyphs, cmap, scale = f.getGlyphSet(), f.getBestCmap(), size / f['head'].unitsPerEm
    names = [cmap.get(ord(ch), '.notdef') for ch in str(s)]
    return sum(glyphs[g].width * scale for g in names) + spacing * max(0, len(names) - 1)


def text(s, x, y, size=20, fill='#273d35', font='serif', spacing=0, anchor='start', opacity=None):
    f = FONTS[font]
    glyphs, cmap, scale = f.getGlyphSet(), f.getBestCmap(), size / f['head'].unitsPerEm
    names = [cmap.get(ord(ch), '.notdef') for ch in str(s)]
    width = measure(s, size, font, spacing)
    x -= width if anchor == 'end' else width / 2 if anchor == 'middle' else 0
    pen = SVGPathPen(glyphs)
    for name in names:
        glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, x, y)))
        x += glyphs[name].width * scale + spacing
    op = f' opacity="{opacity}"' if opacity is not None else ''
    d = re.sub(r'-?\d+\.\d+', lambda m: f'{float(m.group()):.2f}'.rstrip('0').rstrip('.'), pen.getCommands())
    return f'<path fill="{fill}"{op} d="{d}"/>'


def formula(parts, x, y, size, fill, anchor='middle', font='serif'):
    """parts: [('C', False), ('6', True), ...]; True means subscript."""
    sub = size * .68
    widths = [measure(t, sub if low else size, font) for t, low in parts]
    total = sum(widths)
    x -= total / 2 if anchor == 'middle' else total if anchor == 'end' else 0
    out = ''
    for (t, low), w in zip(parts, widths):
        out += text(t, x, y + (size * .22 if low else 0), sub if low else size, fill, font)
        x += w
    return out


def svg(width, height, title, content, desc=''):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc"><title id="title">{html.escape(title)}</title><desc id="desc">{html.escape(desc or title)}</desc>{content}</svg>'


def hexagon(cx, cy, r, start=-30):
    return [(cx + r * math.cos(math.radians(i * 60 + start)), cy + r * math.sin(math.radians(i * 60 + start))) for i in range(6)]


def poly(pts):
    return ' '.join(f'{x:.2f},{y:.2f}' for x, y in pts)


def kekule(cx, cy, r, color, width=1.6, inner=1.1, start=-30):
    """Benzene drawn the way a textbook draws it: a hexagon with three inner double bonds."""
    outer = hexagon(cx, cy, r, start)
    inside = hexagon(cx, cy, r * .76, start)
    s = f'<polygon points="{poly(outer)}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"/>'
    for i in (0, 2, 4):
        (x1, y1), (x2, y2) = inside[i], inside[(i + 1) % 6]
        t = .16
        s += f'<path d="M{x1 + (x2 - x1) * t:.2f} {y1 + (y2 - y1) * t:.2f}L{x2 - (x2 - x1) * t:.2f} {y2 - (y2 - y1) * t:.2f}" stroke="{color}" stroke-width="{inner}" stroke-linecap="round"/>'
    return s


def sparkle(cx, cy, r, color, opacity=1):
    """Four-pointed star, the same figure as the MolAstria mark."""
    k = r * .22
    return (f'<path d="M{cx} {cy - r}C{cx + k * .4} {cy - k} {cx + k} {cy - k * .4} {cx + r} {cy}'
            f'C{cx + k} {cy + k * .4} {cx + k * .4} {cy + k} {cx} {cy + r}'
            f'C{cx - k * .4} {cy + k} {cx - k} {cy + k * .4} {cx - r} {cy}'
            f'C{cx - k} {cy - k * .4} {cx - k * .4} {cy - k} {cx} {cy - r}Z" fill="{color}" opacity="{opacity}"/>')


def lozenge(cx, cy, r, color, opacity=1):
    return f'<path d="M{cx} {cy - r}L{cx + r} {cy}L{cx} {cy + r}L{cx - r} {cy}Z" fill="{color}" opacity="{opacity}"/>'


def arrowhead(x, y, fx, fy, size, color, width=1.1):
    """Open arrowhead at (x, y), pointing away from (fx, fy)."""
    a = math.atan2(y - fy, x - fx)
    pts = [(x - size * math.cos(a + s), y - size * math.sin(a + s)) for s in (.45, -.45)]
    return f'<path d="M{pts[0][0]:.2f} {pts[0][1]:.2f}L{x:.2f} {y:.2f}L{pts[1][0]:.2f} {pts[1][1]:.2f}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>'


def bookplate_frame(x, y, w, h, r, color, width=1, opacity=1):
    """Rectangle with concave (scooped) corners, as on an old bookplate."""
    return (f'<path d="M{x + r} {y}H{x + w - r}A{r} {r} 0 0 0 {x + w} {y + r}V{y + h - r}A{r} {r} 0 0 0 {x + w - r} {y + h}'
            f'H{x + r}A{r} {r} 0 0 0 {x} {y + h - r}V{y + r}A{r} {r} 0 0 0 {x + r} {y}Z" fill="none" stroke="{color}" stroke-width="{width}" opacity="{opacity}"/>')


def leader(x1, x2, y, color, opacity=.55):
    return f'<path d="M{x1:.1f} {y}H{x2:.1f}" stroke="{color}" stroke-width="1.1" stroke-dasharray=".1 4.2" stroke-linecap="round" opacity="{opacity}"/>'


def turn_arrow(x, y, color):
    return f'<path d="M{x} {y}H{x + 19}M{x + 14} {y - 4.5}L{x + 19} {y}L{x + 14} {y + 4.5}" stroke="{color}" stroke-width="1.1" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'


# ---------------------------------------------------------------- volume emblems

def emblem_nmr(c):
    base, x0, x1 = 66, 424, 550
    peaks = [(438, 21, 1.4), (442.5, 21, 1.4),                     # doublet
             (466, 11, 1.3), (470.5, 22, 1.3), (475, 11, 1.3),     # triplet
             (506, 34, 1.5)]                                       # singlet
    def y_at(x):
        return sum(h * w * w / ((x - cx) ** 2 + w * w) for cx, h, w in peaks)
    xs = [x0 + i * .5 for i in range(int((x1 - x0) / .5) + 1)]
    d = 'M' + 'L'.join(f'{x:.1f} {base - y_at(x):.2f}' for x in xs)
    # running integral, drawn above the spectrum in gold
    total, acc, pts = sum(y_at(x) for x in xs), 0, []
    for x in xs:
        acc += y_at(x)
        pts.append(f'{x:.1f} {32 - 14 * acc / total:.2f}')
    s = f'<path d="M{x0} {base}H{x1}" stroke="{c["line"]}" stroke-width="1"/>'
    s += ''.join(f'<path d="M{x} {base}v3" stroke="{c["line"]}" stroke-width="1"/>' for x in range(430, x1, 12))
    s += f'<path d="{d}" fill="none" stroke="{c["green"]}" stroke-width="1.15" stroke-linejoin="round"/>'
    s += f'<path d="M{"L".join(pts)}" fill="none" stroke="{c["gold"]}" stroke-width="1" opacity=".8"/>'
    s += text('δ / ppm', x1, 82, 8, c['muted'], 'italic', anchor='end', opacity=.8)
    return s


def emblem_organic(c):
    cx, cy, r = 508, 45, 17
    s = kekule(cx, cy, r, c['green'], 1.4, 1)
    v = hexagon(cx, cy, r)
    ex, ey = v[0][0] + 15 * math.cos(math.radians(-30)), v[0][1] + 15 * math.sin(math.radians(-30))
    s += f'<path d="M{v[0][0]:.2f} {v[0][1]:.2f}L{ex:.2f} {ey:.2f}" stroke="{c["green"]}" stroke-width="1.4" stroke-linecap="round"/>'
    s += f'<circle cx="{ex:.2f}" cy="{ey:.2f}" r="2.4" fill="{c["gold"]}"/>'
    # curly arrow: a pair of electrons leaving the ring
    sx, sy = v[3][0] - 3, (v[3][1] + v[4][1]) / 2
    qx, qy, tx, ty = sx - 22, sy - 4, sx - 8, sy - 22
    s += f'<path d="M{sx:.1f} {sy:.1f}Q{qx:.1f} {qy:.1f} {tx:.1f} {ty:.1f}" fill="none" stroke="{c["gold"]}" stroke-width="1.1" stroke-linecap="round"/>'
    s += arrowhead(tx, ty, qx, qy, 5, c['gold'])
    return s


def emblem_mass(c):
    base = 68
    sticks = [(452, 10), (461, 20), (470, 13), (484, 36), (495, 9), (508, 19), (526, 42), (532, 14), (538, 4)]
    s = f'<path d="M444 {base}H550" stroke="{c["line"]}" stroke-width="1"/>'
    s += ''.join(f'<path d="M{x} {base}v3" stroke="{c["line"]}"/>' for x in range(448, 550, 10))
    s += ''.join(f'<path d="M{x} {base}V{base - h}" stroke="{c["green"]}" stroke-width="1.5"/>' for x, h in sticks)
    s += lozenge(526, base - 48, 2.6, c['gold'])
    s += text('M', 532, base - 45, 8, c['gold'], 'italic')
    s += text('m/z', 550, 84, 8, c['muted'], 'italic', anchor='end', opacity=.8)
    return s


def emblem_symmetry(c):
    cx, cy = 506, 48
    ligands = [(484, 66), (528, 66), (510, 74)]
    s = f'<path d="M{cx} 20V84" stroke="{c["muted"]}" stroke-width=".9" stroke-dasharray="3 3" opacity=".7"/>'
    s += ''.join(f'<path d="M{cx} {cy}L{x} {y}" stroke="{c["green"]}" stroke-width="1.3" stroke-linecap="round"/>' for x, y in ligands)
    s += ''.join(f'<circle cx="{x}" cy="{y}" r="3.2" fill="{c["bg"]}" stroke="{c["green"]}" stroke-width="1.2"/>' for x, y in ligands)
    s += f'<circle cx="{cx}" cy="{cy}" r="4.6" fill="{c["green"]}"/>'
    # rotation about the axis
    s += f'<path d="M{cx - 15} 30A15 4.5 0 1 0 {cx + 12} 27.4" fill="none" stroke="{c["gold"]}" stroke-width="1.1"/>'
    s += arrowhead(cx + 12, 27.4, cx + 2, 25.6, 4.5, c['gold'])
    s += formula([('C', False), ('3', True)], cx + 26, 30, 11, c['gold'], 'start', 'italic')
    return s


EMBLEMS = {'nmr': emblem_nmr, 'organic': emblem_organic, 'mass': emblem_mass, 'symmetry': emblem_symmetry}


def volume_card(c, w, h, number, category, title, chinese, subtitle, cta, emblem='', title_size=29):
    p = f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="8" fill="{c["bg"]}" stroke="{c["line"]}"/>'
    p += f'<rect x="7.5" y="7.5" width="{w - 15}" height="{h - 15}" rx="4" fill="none" stroke="{c["line"]}" stroke-width=".8" opacity=".75"/>'
    # spine: a heavy and a hairline gold rule, with small lozenges at the ends
    p += f'<path d="M22 27V{h - 27}" stroke="{c["gold"]}" stroke-width="2"/><path d="M27 31V{h - 31}" stroke="{c["gold"]}" stroke-width=".7" opacity=".7"/>'
    p += lozenge(22, 22, 3, c['gold']) + lozenge(22, h - 22, 3, c['gold'])
    p += text(number, 40, 40, 12, c['gold'], 'serif')
    p += text(category, 40 + measure(number, 12) + 16, 40, 10, c['muted'], 'sans', 1.2)
    p += text(title, 39, 90, title_size, c['ink'])
    p += text(chinese, 40, 128, 20, c['green'], 'zh')
    p += text(subtitle, 40, 158, 13, c['muted'], 'sans')
    y = h - 24
    p += text(cta, 40, y + 3.5, 10, c['gold'], 'sans', 1.6)
    p += leader(40 + measure(cta, 10, 'sans', 1.6) + 12, w - 58, y, c['gold'])
    p += turn_arrow(w - 50, y, c['gold'])
    return p + emblem


def molastria_card(c):
    w, h = 1200, 218
    p = volume_card(c, w, h, 'V', 'THE READING ROOM  ·  A COMPUTATIONAL CHEMISTRY ATLAS', 'MolAstria',
                    '计算化学研究导航 · 检索、读懂、动手算', 'Search · handbook · journals · ML potentials · AI lab · desktop app',
                    'VISIT MOLASTRIA.COM', title_size=34)
    # four figures, set like the reading ledger
    stats = [('2,600+', 'resources, refreshed weekly'), ('20', 'handbook chapters · CN / EN'),
             ('15', 'ML potentials online'), ('28', 'preprint servers')]
    x0, col = 616, 150
    for i, (num, label) in enumerate(stats):
        x = x0 + i * col
        if i:
            p += f'<path d="M{x - 18} 96V156" stroke="{c["line"]}"/>'
        p += text(num, x, 126, 30, c['green'], 'serif')
        p += text(label, x, 150, 9.5, c['muted'], 'sans')
    # the MolAstria mark, drawn as a fine-line seal in the top-right corner
    mx, my = 1130, 50
    p += f'<circle cx="{mx}" cy="{my}" r="27" fill="none" stroke="{c["line"]}"/>'
    p += f'<ellipse cx="{mx}" cy="{my}" rx="25" ry="8.5" transform="rotate(-28 {mx} {my})" fill="none" stroke="{c["gold"]}" stroke-width=".8" opacity=".85"/>'
    p += f'<polygon points="{poly(hexagon(mx, my, 13, -90))}" fill="none" stroke="{c["green"]}" stroke-width="1.4" stroke-linejoin="round"/>'
    p += f'<circle cx="{mx}" cy="{my}" r="6.6" fill="none" stroke="{c["green"]}" stroke-width="1"/>'
    p += sparkle(mx + 21, my - 21, 6.5, c['gold'])
    p += f'<circle cx="{mx - 22}" cy="{my + 9}" r="1.6" fill="{c["gold"]}"/>'
    p += f'<circle cx="{mx + 26}" cy="{my - 2}" r=".9" fill="{c["gold"]}"/>'
    return p


# ---------------------------------------------------------------- header bookplate

def header(c):
    p = f'<rect x=".5" y=".5" width="1199" height="369" rx="10" fill="{c["bg"]}" stroke="{c["line"]}"/>'
    p += f'<path d="M800 1H1189Q1199 1 1199 11V359Q1199 369 1189 369H800Z" fill="{c["panel"]}"/>'
    p += text('FELIX  /  THE CHEMISTRY STUDY', 42, 40, 12, c['muted'], 'sans', 2)
    p += f'<path d="M42 59H748" stroke="{c["line"]}"/>' + lozenge(755, 59, 3.2, c['gold'])
    p += text('Jiasheng Fu', 40, 142, 76, c['ink'])
    p += text('化学书房', 45, 204, 38, c['green'], 'zh', 10)
    p += text('Molecules, manuscripts & a little code.', 44, 252, 23, c['muted'], 'italic')
    x = 44
    for i, label in enumerate(['CHEMISTRY', 'SCIENTIFIC COMPUTING', 'VISUAL LEARNING']):
        width = measure(label, 10, 'sans', 1.4) + 44
        p += f'<rect x="{x + .5}" y="289.5" width="{width:.1f}" height="29" rx="2" fill="none" stroke="{c["line"]}"/>'
        p += lozenge(x + 15, 304, 2.2, c['gold'], .9)
        p += text(label, x + 27, 307.6, 10, c['green'], 'sans', 1.4)
        x += width + 12
    p += f'<path d="M42 340H755" stroke="{c["line"]}" stroke-width=".8" opacity=".7"/>'

    # Ex libris plate
    cx = 1000
    p += bookplate_frame(822.5, 20.5, 355, 329, 14, c['gold'], 1.2, .8)
    p += bookplate_frame(828.5, 26.5, 343, 317, 10, c['line'], 1)
    p += text('EX LIBRIS', cx, 48, 11, c['muted'], 'sans', 3.2, 'middle')
    p += f'<path d="M918 44H938M1062 44H1082" stroke="{c["gold"]}" stroke-width=".8" opacity=".8"/>'
    ry = 140
    # astrolabe ring: two hairlines with a graduated scale, cardinal lozenges
    p += f'<circle cx="{cx}" cy="{ry}" r="82" fill="none" stroke="{c["gold"]}" stroke-width="1.1" opacity=".75"/>'
    p += f'<circle cx="{cx}" cy="{ry}" r="73" fill="none" stroke="{c["line"]}" stroke-width="1"/>'
    ticks = ''
    for k in range(72):
        a = math.radians(k * 5 - 90)
        r1, r2 = (73, 82) if k % 6 == 0 else (73, 77)
        ticks += f'M{cx + r1 * math.cos(a):.2f} {ry + r1 * math.sin(a):.2f}L{cx + r2 * math.cos(a):.2f} {ry + r2 * math.sin(a):.2f}'
    p += f'<path d="{ticks}" stroke="{c["gold"]}" stroke-width=".8" opacity=".75"/>'
    for a in (0, 90, 180, 270):
        p += lozenge(cx + 82 * math.cos(math.radians(a)), ry + 82 * math.sin(math.radians(a)), 3.4, c['gold'])
    # a pi molecular orbital of benzene: six p lobes with alternating phase (three nodal planes)
    rr, lobe, wide = 30, 34, 9.5
    for i, (x, y) in enumerate(hexagon(cx, ry, rr, -90)):
        ang = i * 60 - 90
        lx, ly = cx + (rr + lobe / 2) * math.cos(math.radians(ang)), ry + (rr + lobe / 2) * math.sin(math.radians(ang))
        if i % 2 == 0:
            style = f'fill="{c["green"]}" fill-opacity=".38" stroke="{c["green"]}" stroke-width="1.3"'
        else:
            style = f'fill="{c["gold"]}" fill-opacity=".14" stroke="{c["gold"]}" stroke-width="1.3"'
        p += f'<ellipse cx="{lx:.2f}" cy="{ly:.2f}" rx="{lobe / 2}" ry="{wide}" transform="rotate({ang} {lx:.2f} {ly:.2f})" {style}/>'
    # delocalised pi density as contour lines inside the ring
    for r, op in ((21, .9), (15, .65), (9, .45)):
        p += f'<circle cx="{cx}" cy="{ry}" r="{r}" fill="none" stroke="{c["green"]}" stroke-width=".9" opacity="{op}"/>'
    p += f'<polygon points="{poly(hexagon(cx, ry, rr, -90))}" fill="none" stroke="{c["ink"]}" stroke-width="2" stroke-linejoin="round" opacity=".85"/>'
    p += ''.join(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="2.6" fill="{c["panel"]}" stroke="{c["gold"]}" stroke-width="1.2"/>' for x, y in hexagon(cx, ry, rr, -90))
    p += f'<circle cx="{cx}" cy="{ry}" r="1.6" fill="{c["gold"]}"/>'
    p += formula([('C', False), ('6', True), ('H', False), ('6', True), ('  ·  π', False)], cx, 245, 14, c['muted'])
    # open book with page edges and a ribbon
    p += f'<g fill="none" stroke="{c["gold"]}" stroke-linejoin="round" stroke-linecap="round">'
    p += '<path stroke-width="1.4" d="M872 262Q936 244 1000 268Q1064 244 1128 262V306Q1064 290 1000 313Q936 290 872 306Z"/>'
    p += '<path stroke-width=".8" opacity=".75" d="M872 306V310Q936 294 1000 317Q1064 294 1128 310V306M1000 268V313"/>'
    for i in range(4):
        dy = i * 9
        p += f'<path stroke-width=".7" opacity=".7" d="M884 {273 + dy}Q938 {260 + dy} 988 {278 + dy}M1012 {278 + dy}Q1062 {260 + dy} 1116 {273 + dy}"/>'
    p += '</g>'
    p += f'<path d="M995.5 268V324L1000 319L1004.5 324V268" fill="{c["green"]}" opacity=".75"/>'
    p += text('READ  ·  QUESTION  ·  MAKE', cx, 336, 10, c['muted'], 'sans', 1.6, 'middle')
    return p


# ---------------------------------------------------------------- desk toolkit

BENCH = [
    ('Py', 'Python', 'scripts & servers'), ('Nb', 'Jupyter', 'notebooks'), ('Np', 'NumPy', 'arrays'),
    ('Mp', 'Matplotlib', 'figures'), ('Rd', 'RDKit', 'cheminformatics'), ('Ps', 'PySCF', 'reference QC'),
    ('Ml', 'UMA · MACE', 'ML potentials'), ('Tx', 'LaTeX', 'manuscripts'),
]
WORKSHOP = [
    ('Js', 'JavaScript', 'no framework'), ('Dn', 'Deno', 'tooling & tests'), ('Cf', 'Cloudflare', 'Workers · D1'),
    ('Ta', 'Tauri · Rust', 'desktop app'), ('Pw', 'Playwright', 'browser tests'), ('Ga', 'GitHub Actions', 'CI & data'),
    ('Ds', 'DeepSeek', 'LLM API'), ('Ff', 'ffmpeg', 'video'),
]


def toolkit(c):
    w, h = 1200, 318
    p = f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="8" fill="{c["bg"]}" stroke="{c["line"]}"/>'
    p += f'<rect x="7.5" y="7.5" width="{w - 15}" height="{h - 15}" rx="4" fill="none" stroke="{c["line"]}" stroke-width=".8" opacity=".75"/>'
    rows = [('I', 'THE BENCH', '计算与笔记', BENCH, 30), ('II', 'THE WORKSHOP', '建站与发布', WORKSHOP, 168)]
    n = 0
    for numeral, name, zh, tools, top in rows:
        p += text(numeral, 40, top + 30, 13, c['gold'], 'serif')
        p += text(name, 40, top + 52, 10, c['muted'], 'sans', 1.6)
        p += text(zh, 40, top + 78, 16, c['green'], 'zh', 2)
        p += f'<path d="M40 {top + 92}H150" stroke="{c["line"]}"/>' + lozenge(156, top + 92, 2.4, c['gold'])
        x0, pitch, size = 196, 122, 88
        for i, (sym, label, note) in enumerate(tools):
            n += 1
            x, y = x0 + i * pitch, top
            p += f'<rect x="{x + .5}" y="{y + .5}" width="{size}" height="{size}" rx="3" fill="{c["pale"]}" fill-opacity=".45" stroke="{c["line"]}"/>'
            p += f'<path d="M{x + 5} {y + 5}H{x + size - 4}V{y + size - 4}H{x + 5}Z" fill="none" stroke="{c["line"]}" stroke-width=".6" opacity=".7"/>'
            p += text(str(n), x + 11, y + 19, 8.5, c['gold'], 'sans')
            p += text(sym, x + size / 2 + .5, y + 55, 28, c['green'], 'serif', 0, 'middle')
            p += text(label, x + size / 2 + .5, y + 76, 9, c['muted'], 'sans', .2, 'middle')
            p += text(note, x + size / 2 + .5, y + size + 19, 10.5, c['muted'], 'italic', 0, 'middle', .9)
    return w, h, p


# ---------------------------------------------------------------- write files

CARDS = [
    ('nmr', 'I', 'NMR, read closely', '核磁共振 · 从谱峰读出结构', 'HSQC · HMBC · COSY · TOCSY', 'SPECTROSCOPY'),
    ('organic', 'II', 'The language of reactions', '有机化学 · 沿着电子看机理', 'Mechanisms · synthesis · atom tracking', 'ORGANIC CHEMISTRY'),
    ('mass', 'III', 'Fragments tell stories', '质谱 · 从碎片追溯分子', 'Fragmentation · isotope patterns', 'MASS SPECTROMETRY'),
    ('symmetry', 'IV', 'Order within molecules', '分子对称性 · 在三维中理解点群', '3D models · symmetry operations', 'MOLECULAR SYMMETRY'),
]
TOOL_LIST = ', '.join(label for _, label, _ in BENCH + WORKSHOP)

for theme, c in PALETTES.items():
    (ASSETS / f'header-{theme}.svg').write_text(svg(1200, 370, 'Jiasheng Fu · 化学书房', header(c),
        'Molecules, manuscripts & a little code. An ex libris plate: a pi molecular orbital of benzene inside a graduated ring, above an open book with a ribbon.'))
    for slug, number, title, chinese, subtitle, category in CARDS:
        p = volume_card(c, 580, 218, number, category, title, chinese, subtitle, 'OPEN THE VOLUME', EMBLEMS[slug](c))
        (ASSETS / f'volume-{slug}-{theme}.svg').write_text(svg(580, 218, title, p, chinese + ' — ' + subtitle))
    (ASSETS / f'volume-molastria-{theme}.svg').write_text(svg(1200, 218, 'MolAstria', molastria_card(c),
        'MolAstria — a computational chemistry atlas: 2,600+ resources, a 20-chapter Chinese and English handbook, 15 machine-learning potentials online, 28 preprint servers.'))
    w, h, p = toolkit(c)
    (ASSETS / f'toolkit-{theme}.svg').write_text(svg(w, h, 'Tools on my desk', p, 'Two rows of tiles set like a periodic table: ' + TOOL_LIST + '.'))


def picture(slug, alt, width='100%'):
    return f'''<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/{slug}-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="./assets/{slug}-light.svg">
  <img alt="{alt}" src="./assets/{slug}-light.svg" width="{width}">
</picture>'''


readme = f'''<!-- Static artwork is kept in this repository. Daily contribution artwork is refreshed by GitHub Actions. -->
<p align="center">{picture('header','Jiasheng Fu · 化学书房 — Molecules, manuscripts and a little code.')}</p>

<p align="center">
  <b>Chemistry, explained with care.</b><br>
  I turn chemistry, mathematics and physics into visual explanations,<br>
  interactive experiments and carefully written notes.<br>
  <sub>以书为径，以化学为趣，把抽象的科学讲得清楚一点。</sub>
</p>

{picture('ledger','GitHub reading ledger: contributions over the past year, public repositories, and monthly activity. Updated daily.')}

## The bookshelf · 化学书架

<sub>Open a volume. Follow a spectrum, a mechanism, or a question.</sub>

<table>
<tr>
<td width="50%"><a href="https://github.com/FelixJiashengFu/NMR-Graph">{picture('volume-nmr','NMR Graph — 核磁共振：HSQC、HMBC、COSY、TOCSY 与结构解析')}</a></td>
<td width="50%"><a href="https://github.com/FelixJiashengFu/Organic-Chemistry-Graph">{picture('volume-organic','Organic Chemistry Graph — 有机反应机理、合成与原子追踪')}</a></td>
</tr>
<tr>
<td width="50%"><a href="https://github.com/FelixJiashengFu/mass-spectrometry">{picture('volume-mass','Mass Spectrometry — 分子碎裂与同位素峰图解')}</a></td>
<td width="50%"><a href="https://github.com/FelixJiashengFu/Molecular-Symmetry-Graph">{picture('volume-symmetry','Molecular Symmetry Graph — 三维分子模型、对称操作与点群')}</a></td>
</tr>
<tr>
<td colspan="2"><a href="https://molastria.com/">{picture('volume-molastria','MolAstria — 计算化学研究导航：2,600 多条资源、20 章中英双语讲解手册、15 个在线机器学习势、28 个预印本平台')}</a></td>
</tr>
</table>

<p align="center">
  <a href="https://github.com/FelixJiashengFu/NMR-Graph">NMR</a> ·
  <a href="https://github.com/FelixJiashengFu/Organic-Chemistry-Graph">Organic chemistry</a> ·
  <a href="https://github.com/FelixJiashengFu/mass-spectrometry">Mass spectrometry</a> ·
  <a href="https://github.com/FelixJiashengFu/Molecular-Symmetry-Graph">Molecular symmetry</a> ·
  <a href="https://molastria.com/">MolAstria</a>
</p>

### Notes in the margins · 数理札记

<p align="center"><a href="https://github.com/FelixJiashengFu/Complex-Analysis-Graph">Complex analysis</a> &nbsp; / &nbsp; <a href="https://github.com/FelixJiashengFu/pde-visualization">PDE visualizations</a> &nbsp; / &nbsp; <a href="https://github.com/FelixJiashengFu/statistical-mechanics">Statistical mechanics</a></p>

### The reading room · 研究导航

<p align="center"><a href="https://molastria.com/"><b>MolAstria</b></a> — 2,600+ computational-chemistry resources from 24 sources, refreshed every Thursday; a 20-chapter handbook in Chinese and English; 15 machine-learning potentials you can run online; a closed-loop AI lab for electrolyte discovery; and a Windows / macOS desktop app.<br><sub>计算化学研究导航：数据库、教程、期刊与论文一处检索，27 个科学大模型对比，28 个平台的预印本雷达，量子化学游乐场；<a href="https://molastria.com/lab/">AI 实验室</a>用 DeepSeek / Muse 提出电解液溶剂分子 · <a href="https://github.com/FelixJiashengFu/chem-research-molastria/releases/latest">桌面版</a> · <a href="https://github.com/FelixJiashengFu/chem-research-molastria">源码</a></sub></p>

## On my desk · 案头工具

<sub>The bench is for thinking and calculating; the workshop is where MolAstria gets built and shipped.</sub>

{picture('toolkit', TOOL_LIST)}

## A living trail · 贡献游踪

<sub>A copper-coloured snake wanders through a year of real GitHub contributions.</sub>

{picture('snake','Animated snake eating the cells of FelixJiashengFu’s real GitHub contribution calendar.')}

<p align="center">
  <i>Read deeply. Experiment gently. Make things clear.</i><br>
  <sub>读书，求证，让理解慢慢生长。</sub>
</p>

<p align="center"><sub><a href="https://github.com/FelixJiashengFu?tab=repositories">Browse all volumes ↗</a> &nbsp; · &nbsp; Contribution animation by <a href="https://github.com/Platane/snk">Platane/snk</a></sub></p>
'''
(ROOT / 'README.md').write_text(readme)
print('Built the bookplate, five volumes, the desk toolkit and the profile README.')
