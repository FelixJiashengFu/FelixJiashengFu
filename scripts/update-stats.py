#!/usr/bin/env python3
"""Refresh profile cards from GitHub's public profile and contribution calendar.

Uses only Python's standard library. GITHUB_TOKEN is read from the environment;
no credentials or private repository metadata are saved to the repository.
"""
import argparse
import collections
import datetime as dt
import html
import json
import os
from pathlib import Path
import urllib.request
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
THEMES = {
    'light': dict(bg='#f8f5ec', ink='#273d35', muted='#6e7568', line='#dedbcf', green='#386653', gold='#a67a46', pale='#e6e9df'),
    'dark': dict(bg='#18241f', ink='#e9e6d8', muted='#a5b0a1', line='#36473d', green='#91b49b', gold='#c6a273', pale='#293b30'),
}


def fetch(url, token, payload=None):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'FelixJiashengFu-profile'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    if payload is not None:
        headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(url, headers=headers, data=json.dumps(payload).encode() if payload else None)
    with urllib.request.urlopen(req, timeout=45) as response:
        return json.load(response)


def render(profile, calendar, asof):
    days = [day for week in calendar['weeks'] for day in week['contributionDays']]
    monthly = collections.OrderedDict()
    for day in days:
        key = day['date'][:7]
        monthly[key] = monthly.get(key, 0) + day['contributionCount']
    total = calendar['totalContributions']
    if total != sum(d['contributionCount'] for d in days):
        raise ValueError('Contribution total does not match daily counts')
    peak = max(monthly.values(), default=1) or 1
    for theme, c in THEMES.items():
        p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="258" viewBox="0 0 1200 258" role="img" aria-labelledby="title desc">',
             f'<title id="title">Jiasheng Fu — GitHub reading ledger</title>',
             f'<desc id="desc">{total} contributions in the past year, {profile["public_repos"]} public repositories, joined {profile["created_at"][:4]}. Monthly contributions from {next(iter(monthly))} to {next(reversed(monthly))}. Refreshed {asof}.</desc>',
             f'<rect x=".5" y=".5" width="1199" height="257" rx="10" fill="{c["bg"]}" stroke="{c["line"]}"/>']
        def text(x, y, s, size=16, color=None, font='Arial, sans-serif', extra=''):
            p.append(f'<text x="{x}" y="{y}" fill="{color or c["ink"]}" font-family="{font}" font-size="{size}" {extra}>{html.escape(str(s))}</text>')
        text(36, 34, 'A READING LEDGER', 12, c['muted'], extra='letter-spacing="2"')
        text(36, 94, f'{total:,}', 47, c['green'], 'Georgia, serif')
        text(36, 120, 'contributions · past year', 14, c['muted'])
        text(325, 94, profile['public_repos'], 47, c['green'], 'Georgia, serif')
        text(325, 120, 'public repositories', 14, c['muted'])
        text(36, 170, 'Member since ' + profile['created_at'][:4], 15)
        text(36, 206, 'Small entries. A growing body of work.', 16, c['muted'], 'Georgia, serif', 'font-style="italic"')
        p.append(f'<path d="M557 37V220" stroke="{c["line"]}"/>')
        text(598, 37, 'CONTRIBUTIONS BY MONTH', 12, c['muted'], extra='letter-spacing="1.4"')
        text(1164, 37, f'peak {peak}', 11, c['muted'], extra='text-anchor="end"')
        for i, (month, value) in enumerate(monthly.items()):
            x = 600 + i * 44
            height = max(2, value / peak * 108)
            fill = c['gold'] if i == len(monthly) - 1 else c['green']
            p.append(f'<rect x="{x}" y="{173-height:.2f}" width="28" height="{height:.2f}" rx="2" fill="{fill}"><title>{month}: {value}</title></rect>')
            if value:
                text(x+14, 164-height, value, 10, c['muted'], extra='text-anchor="middle"')
            text(x+14, 192, dt.date.fromisoformat(month+'-01').strftime('%b'), 10, c['muted'], extra='text-anchor="middle"')
        text(598, 226, f'{days[0]["date"]} → {days[-1]["date"]}  ·  refreshed {asof}', 11, c['muted'])
        p.append('</svg>')
        (ROOT / 'assets' / f'ledger-{theme}.svg').write_text('\n'.join(p))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--username', default=os.environ.get('GITHUB_REPOSITORY_OWNER', 'FelixJiashengFu'))
    ap.add_argument('--snapshot-dir', type=Path, help='Use local API response fixtures for an offline refresh')
    args = ap.parse_args()
    if args.snapshot_dir:
        profile = json.loads((args.snapshot_dir / 'profile.json').read_text())
        response = json.loads((args.snapshot_dir / 'contributions.json').read_text())
        owner = response['data'].get('user') or response['data'].get('viewer')
    else:
        token = os.environ['GITHUB_TOKEN']
        profile = fetch('https://api.github.com/users/' + args.username, token)
        query = 'query($login:String!){user(login:$login){login contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}'
        response = fetch('https://api.github.com/graphql', token, {'query': query, 'variables': {'login': args.username}})
        if response.get('errors'):
            raise RuntimeError('GitHub could not return the contribution calendar')
        owner = response['data']['user']
    if profile['login'].lower() != args.username.lower() or owner['login'].lower() != args.username.lower():
        raise ValueError('GitHub identity does not match the requested profile')
    (ROOT / 'assets').mkdir(exist_ok=True)
    render(profile, owner['contributionsCollection']['contributionCalendar'], dt.datetime.now(ZoneInfo('America/Toronto')).strftime('%d %b %Y'))
    print('Updated both ledger themes from verified GitHub data.')


if __name__ == '__main__':
    main()
