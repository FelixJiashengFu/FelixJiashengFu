#!/usr/bin/env python3
"""Refresh the "最近在专注的 · On the bench now" cards on the bookshelf.

Picks the four public, non-fork, non-archived repositories most recently pushed
to (the profile repository itself is skipped), draws one card per repository in
both themes, and rewrites the block between the focus markers in README.md.
Uses only Python's standard library; only public repository data is read.
"""
import argparse
import datetime as dt
import html
import json
import os
from pathlib import Path
import re
import urllib.request
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
COUNT = 4
W, H = 580, 178
THEMES = {
    'light': dict(bg='#f8f5ec', ink='#273d35', muted='#6e7568', line='#dedbcf', green='#386653', gold='#a67a46'),
    'dark': dict(bg='#18241f', ink='#e9e6d8', muted='#a5b0a1', line='#36473d', green='#91b49b', gold='#c6a273'),
}
SANS = "Arial, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'Noto Sans CJK SC', sans-serif"
SERIF = "Georgia, 'Songti SC', 'Noto Serif CJK SC', serif"
START, END = '<!-- focus:start -->', '<!-- focus:end -->'


def fetch(url, token):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'FelixJiashengFu-profile'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=45) as response:
        return json.load(response)


def pick(repos, username):
    keep = [r for r in repos if not r['fork'] and not r['archived'] and not r.get('private')
            and r['name'].lower() != username.lower() and r.get('size', 0) > 0]
    keep.sort(key=lambda r: r['pushed_at'], reverse=True)
    if len(keep) < COUNT:
        raise ValueError(f'Only {len(keep)} public repositories to show; need {COUNT}')
    return keep[:COUNT]


def width(s, size):
    return sum(size if ord(ch) > 0x2e7f else size * (.3 if ch in ' .,:;·|il' else .56) for ch in s)


def wrap(s, size, limit, lines=2):
    s = ' '.join((s or '').split())
    out, cur = [], ''
    for ch in s:
        if width(cur + ch, size) > limit:
            if len(out) == lines - 1:
                while cur and width(cur + '…', size) > limit:
                    cur = cur[:-1]
                out.append(cur.rstrip(' ,，、;；·') + '…')
                return out
            cut = cur.rfind(' ') if ord(ch) < 0x2e80 and ch != ' ' else -1
            if cut > len(cur) * .6:
                out.append(cur[:cut]); cur = cur[cut + 1:] + ch
            else:
                out.append(cur); cur = ch.lstrip()
        else:
            cur += ch
    if cur:
        out.append(cur)
    return out


def card(c, i, repo, pushed):
    def text(x, y, s, size, color, font=SANS, extra=''):
        return f'<text x="{x}" y="{y}" fill="{color}" font-family="{font}" font-size="{size}" {extra}>{html.escape(str(s))}</text>'
    def lozenge(cx, cy, r=3):
        return f'<path d="M{cx} {cy - r}L{cx + r} {cy}L{cx} {cy + r}L{cx - r} {cy}Z" fill="{c["gold"]}"/>'
    p = [f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="8" fill="{c["bg"]}" stroke="{c["line"]}"/>',
         f'<rect x="7.5" y="7.5" width="{W - 15}" height="{H - 15}" rx="4" fill="none" stroke="{c["line"]}" stroke-width=".8" opacity=".75"/>',
         f'<path d="M22 27V{H - 27}" stroke="{c["gold"]}" stroke-width="2"/><path d="M27 31V{H - 31}" stroke="{c["gold"]}" stroke-width=".7" opacity=".7"/>',
         lozenge(22, 22), lozenge(22, H - 22)]
    p.append(text(40, 40, f'0{i}', 12, c['gold'], SERIF))
    p.append(text(64, 40, 'ON THE BENCH  ·  LAST PUSHED ' + pushed.upper(), 10, c['muted'], extra='letter-spacing="1.2"'))
    meta = ' · '.join(x for x in [repo.get('language'), f'★ {repo["stargazers_count"]}' if repo['stargazers_count'] else ''] if x)
    if meta:
        p.append(text(W - 40, 40, meta, 11, c['green'], extra='text-anchor="end"'))
    p.append(text(39, 80, repo['name'], 26, c['ink'], SERIF))
    for n, line in enumerate(wrap(repo.get('description') or 'A work in progress.', 13, W - 80)):
        p.append(text(40, 108 + n * 19, line, 13, c['muted']))
    y = H - 24
    p.append(text(40, y + 3.5, 'OPEN THE REPOSITORY', 10, c['gold'], extra='letter-spacing="1.6"'))
    p.append(f'<path d="M202 {y}H{W - 58}" stroke="{c["gold"]}" stroke-width="1.1" stroke-dasharray=".1 4.2" stroke-linecap="round" opacity=".55"/>')
    x = W - 50
    p.append(f'<path d="M{x} {y}H{x + 19}M{x + 14} {y - 4.5}L{x + 19} {y}L{x + 14} {y + 4.5}" stroke="{c["gold"]}" stroke-width="1.1" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
    desc = html.escape(f'{repo["name"]} — {repo.get("description") or ""} Last pushed {pushed}.')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">'
            f'<title id="title">{html.escape(repo["name"])}</title><desc id="desc">{desc}</desc>' + ''.join(p) + '</svg>\n')


def picture(i, alt):
    return f'''<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/focus-{i}-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="./assets/focus-{i}-light.svg">
  <img alt="{html.escape(alt, quote=True)}" src="./assets/focus-{i}-light.svg" width="100%">
</picture>'''


def readme_block(chosen):
    cells = [f'<td width="50%"><a href="{r["html_url"]}">{picture(i, r["name"] + " — " + (r.get("description") or ""))}</a></td>'
             for i, r in enumerate(chosen, 1)]
    rows = ['<tr>\n<td colspan="2" align="center"><b>On the bench now · 最近在专注的</b><br><sub>The four repositories I pushed to most recently — refreshed daily.</sub></td>\n</tr>']
    rows += ['<tr>\n' + '\n'.join(cells[k:k + 2]) + '\n</tr>' for k in range(0, COUNT, 2)]
    return START + '\n' + '\n'.join(rows) + '\n' + END


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--username', default=os.environ.get('GITHUB_REPOSITORY_OWNER', 'FelixJiashengFu'))
    ap.add_argument('--snapshot', type=Path, help='Use a saved /users/<name>/repos response instead of the API')
    args = ap.parse_args()
    if args.snapshot:
        repos = json.loads(args.snapshot.read_text())
    else:
        repos = fetch(f'https://api.github.com/users/{args.username}/repos?type=owner&sort=pushed&per_page=50',
                      os.environ.get('GITHUB_TOKEN'))
    if any(r['owner']['login'].lower() != args.username.lower() for r in repos):
        raise ValueError('GitHub returned repositories for a different owner')
    chosen = pick(repos, args.username)
    toronto = ZoneInfo('America/Toronto')
    for i, repo in enumerate(chosen, 1):
        pushed = dt.datetime.fromisoformat(repo['pushed_at'].replace('Z', '+00:00')).astimezone(toronto).strftime('%-d %b %Y')
        for theme, c in THEMES.items():
            (ROOT / 'assets' / f'focus-{i}-{theme}.svg').write_text(card(c, i, repo, pushed))
    readme = (ROOT / 'README.md').read_text()
    pattern = re.compile(re.escape(START) + '.*?' + re.escape(END), re.S)
    if not pattern.search(readme):
        raise ValueError('README.md has no focus markers')
    (ROOT / 'README.md').write_text(pattern.sub(lambda _: readme_block(chosen), readme))
    print('On the bench:', ', '.join(r['name'] for r in chosen))


if __name__ == '__main__':
    main()
