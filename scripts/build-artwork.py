from pathlib import Path
import math
import html
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
FONTS = {
    'serif': TTFont('/System/Library/Fonts/Supplemental/Georgia.ttf'),
    'italic': TTFont('/System/Library/Fonts/Supplemental/Georgia Italic.ttf'),
    'sans': TTFont('/System/Library/Fonts/Supplemental/Arial.ttf'),
    'zh': TTFont('/System/Library/Fonts/Supplemental/Songti.ttc', fontNumber=0),
}
PALETTES = {
    'light': dict(bg='#f8f5ec', panel='#edf0e5', ink='#273d35', muted='#6e7568', line='#dedbcf', green='#386653', gold='#a67a46', pale='#e6e9df'),
    'dark': dict(bg='#18241f', panel='#22362a', ink='#e9e6d8', muted='#a5b0a1', line='#36473d', green='#91b49b', gold='#c6a273', pale='#293b30'),
}


def text(s, x, y, size=20, fill='#273d35', font='serif', spacing=0, anchor='start'):
    f = FONTS[font]
    glyphs, cmap, scale = f.getGlyphSet(), f.getBestCmap(), size / f['head'].unitsPerEm
    names = [cmap.get(ord(ch), '.notdef') for ch in str(s)]
    width = sum(glyphs[g].width * scale for g in names) + spacing * max(0, len(names)-1)
    x -= width if anchor == 'end' else width/2 if anchor == 'middle' else 0
    pen = SVGPathPen(glyphs)
    for name in names:
        glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, x, y)))
        x += glyphs[name].width * scale + spacing
    return f'<path fill="{fill}" d="{pen.getCommands()}"/>'


def svg(width, height, title, content, desc=''):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc"><title id="title">{html.escape(title)}</title><desc id="desc">{html.escape(desc or title)}</desc>{content}</svg>'


def hexagon(cx, cy, r):
    return [(cx + r*math.cos(math.radians(i*60-30)), cy + r*math.sin(math.radians(i*60-30))) for i in range(6)]


def ring(cx, cy, r, color, aromatic=True):
    pts = hexagon(cx, cy, r)
    s = '<polygon points="'+' '.join(f'{x:.2f},{y:.2f}' for x,y in pts)+f'" fill="none" stroke="{color}" stroke-width="2"/>'
    if aromatic:
        s += f'<circle cx="{cx}" cy="{cy}" r="{r*.55}" fill="none" stroke="{color}" stroke-width="1.5"/>'
    return s


for theme, c in PALETTES.items():
    p = f'<rect x=".5" y=".5" width="1199" height="369" rx="10" fill="{c["bg"]}" stroke="{c["line"]}"/>'
    p += f'<path d="M800 1H1189Q1199 1 1199 11V359Q1199 369 1189 369H800Z" fill="{c["panel"]}"/>'
    p += text('FELIX  /  THE CHEMISTRY STUDY', 42, 40, 12, c['muted'], 'sans', 2)
    p += f'<path d="M42 59H755" stroke="{c["line"]}"/>'
    p += text('Jiasheng Fu', 40, 142, 76, c['ink'])
    p += text('化学书房', 45, 204, 38, c['green'], 'zh', 10)
    p += text('Molecules, manuscripts & a little code.', 44, 252, 23, c['muted'], 'italic')
    for label, x, width in [('CHEMISTRY',44,132), ('SCIENTIFIC COMPUTING',188,230), ('VISUAL LEARNING',430,183)]:
        p += f'<rect x="{x}" y="289" width="{width}" height="30" rx="3" fill="none" stroke="{c["line"]}"/>'
        p += text(label,x+width/2,308,10,c['green'],'sans',1,anchor='middle')
    p += f'<path d="M800 22V347" stroke="{c["line"]}"/>'
    p += text('EX LIBRIS', 1000, 43, 11, c['muted'], 'sans', 3, 'middle')
    p += ring(1000, 143, 66, c['green'])
    p += f'<circle cx="1000" cy="143" r="91" fill="none" stroke="{c["line"]}" stroke-width="1" stroke-dasharray="2 7"/>'
    p += text('C₆H₆', 1000, 244, 16, c['muted'], 'serif',0,'middle')
    p += f'<g fill="none" stroke="{c["gold"]}" stroke-width="1.5"><path d="M857 263Q928 241 1000 267Q1072 241 1143 263V315Q1072 296 1000 322Q928 296 857 315Z"/><path d="M1000 267V322M869 273Q929 257 987 276M869 284Q929 268 987 287M869 295Q929 279 987 298M1013 276Q1071 257 1131 273M1013 287Q1071 268 1131 284M1013 298Q1071 279 1131 295"/></g>'
    p += text('READ  ·  QUESTION  ·  MAKE',1000,350,10,c['muted'],'sans',1.5,'middle')
    (ASSETS/f'header-{theme}.svg').write_text(svg(1200,370,'Jiasheng Fu · 化学书房',p,'Molecules, manuscripts & a little code. A bookplate with an aromatic benzene ring above an open book.'))

    cards = [
        ('nmr','I','NMR, read closely','核磁共振 · 从谱峰读出结构','HSQC · HMBC · COSY · TOCSY','SPECTROSCOPY'),
        ('organic','II','The language of reactions','有机化学 · 沿着电子看机理','Mechanisms · synthesis · atom tracking','ORGANIC CHEMISTRY'),
        ('mass','III','Fragments tell stories','质谱 · 从碎片追溯分子','Fragmentation · isotope patterns','MASS SPECTROMETRY'),
        ('symmetry','IV','Order within molecules','分子对称性 · 在三维中理解点群','3D models · symmetry operations','MOLECULAR SYMMETRY'),
    ]
    for slug, number, title, chinese, subtitle, category in cards:
        p = f'<rect x=".5" y=".5" width="579" height="217" rx="8" fill="{c["bg"]}" stroke="{c["line"]}"/>'
        p += f'<path d="M22 25V191" stroke="{c["gold"]}" stroke-width="2"/>'
        p += text(number, 39, 40, 12, c['gold'], 'serif')
        p += text(category, 68, 40, 10, c['muted'], 'sans',1.2)
        p += text(title, 39, 90, 29, c['ink'])
        p += text(chinese, 40, 128, 20, c['green'], 'zh')
        p += text(subtitle, 40, 158, 13, c['muted'], 'sans')
        p += text('OPEN THE VOLUME', 40, 194, 10, c['gold'], 'sans',1.6)
        p += f'<path d="M530 187H549M543 181L549 187L543 193" stroke="{c["gold"]}" stroke-width="1.3" fill="none"/>'
        if slug=='nmr':
            p += f'<path d="M426 57H452L455 42L458 69L461 31L464 69L467 42L470 57H496L500 47L504 57H548" stroke="{c["green"]}" stroke-width="1.3" fill="none" opacity=".5"/>'
        elif slug=='organic':
            p += ring(512,44,18,c['green'])
        elif slug=='mass':
            p += f'<path d="M448 62H548M461 62V50M476 62V39M492 62V27M516 62V48M535 62V35" stroke="{c["green"]}" stroke-width="1.5" opacity=".6"/>'
        else:
            p += f'<g fill="{c["green"]}" opacity=".65"><circle cx="504" cy="42" r="4"/><circle cx="482" cy="56" r="3"/><circle cx="526" cy="56" r="3"/></g><path d="M482 56L504 42L526 56M504 22V68" stroke="{c["green"]}" opacity=".45" fill="none" stroke-dasharray="3 3"/>'
        (ASSETS/f'volume-{slug}-{theme}.svg').write_text(svg(580,218,title,p,chinese+' — '+subtitle))

    p = f'<rect x=".5" y=".5" width="1199" height="119" rx="8" fill="{c["bg"]}" stroke="{c["line"]}"/>'
    tools = [('Py','Python'),('Nb','Jupyter'),('Np','NumPy'),('Mp','Matplotlib'),('TeX','LaTeX'),('</>','HTML / SVG'),('Git','Git & GitHub')]
    for i,(symbol,label) in enumerate(tools):
        x = 25 + i*168
        if i:
            p += f'<path d="M{x-12} 25V96" stroke="{c["line"]}"/>'
        p += text(symbol,x+65,58,25,c['green'],'serif',0,'middle')
        p += text(label,x+65,88,12,c['muted'],'sans',0,'middle')
    (ASSETS/f'toolkit-{theme}.svg').write_text(svg(1200,120,'Tools on my desk',p,'Python, Jupyter, NumPy, Matplotlib, LaTeX, HTML and SVG, Git and GitHub.'))


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
</table>

<p align="center">
  <a href="https://github.com/FelixJiashengFu/NMR-Graph">NMR</a> ·
  <a href="https://github.com/FelixJiashengFu/Organic-Chemistry-Graph">Organic chemistry</a> ·
  <a href="https://github.com/FelixJiashengFu/mass-spectrometry">Mass spectrometry</a> ·
  <a href="https://github.com/FelixJiashengFu/Molecular-Symmetry-Graph">Molecular symmetry</a>
</p>

### Notes in the margins · 数理札记

<p align="center"><a href="https://github.com/FelixJiashengFu/Complex-Analysis-Graph">Complex analysis</a> &nbsp; / &nbsp; <a href="https://github.com/FelixJiashengFu/pde-visualization">PDE visualizations</a> &nbsp; / &nbsp; <a href="https://github.com/FelixJiashengFu/statistical-mechanics">Statistical mechanics</a> &nbsp; / &nbsp; <a href="https://github.com/FelixJiashengFu/PHYB57-Study-Library">PHYB57 study library</a></p>

### The reading room · 研究导航

<p align="center"><a href="https://molastria.com/"><b>MolAstria</b></a> — 1,465 computational-chemistry resources, 19 guide chapters in Chinese, and a closed-loop AI lab for electrolyte discovery.<br><sub>计算化学研究导航：数据库、教程与论文一处检索；<a href="https://molastria.com/lab/">AI 实验室</a>用 DeepSeek / Muse 提出电解液溶剂分子 · <a href="https://github.com/FelixJiashengFu/chem-research-molastria">源码</a></sub></p>

## On my desk · 案头工具

{picture('toolkit','Python · Jupyter · NumPy · Matplotlib · LaTeX · HTML / SVG · Git and GitHub')}

## A living trail · 贡献游踪

<sub>A copper-coloured snake wanders through a year of real GitHub contributions.</sub>

{picture('snake','Animated snake eating the cells of FelixJiashengFu’s real GitHub contribution calendar.')}

<p align="center">
  <i>Read deeply. Experiment gently. Make things clear.</i><br>
  <sub>读书，求证，让理解慢慢生长。</sub>
</p>

<p align="center"><sub><a href="https://github.com/FelixJiashengFu?tab=repositories">Browse all volumes ↗</a> &nbsp; · &nbsp; Contribution animation by <a href="https://github.com/Platane/snk">Platane/snk</a></sub></p>
'''
(ROOT/'README.md').write_text(readme)
print('Built themed bookplates, four chemistry volumes, toolkit and profile README.')
