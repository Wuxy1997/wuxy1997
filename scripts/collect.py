#!/usr/bin/env python3
"""Pull public GitHub data and the blog index into data/snapshot.json. Needs the gh CLI.

Only public data is read: users/<login>/repos never lists private repositories.
generated_at only moves when the data changes, so an idle week produces no commit.
"""
import base64
import collections
import datetime
import json
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONTENT = json.loads((ROOT / 'data' / 'content.json').read_text('utf-8'))
LOGIN = CONTENT['login']
BLOG = f'{LOGIN}/{LOGIN}.github.io'
SITE = CONTENT['links']['home'].rstrip('/')

# Markup and glue that would drown the real languages: one repo holds 5 MB of generated HTML.
SKIP_LANGS = {'HTML', 'CSS', 'SCSS', 'Dockerfile', 'Batchfile', 'Shell', 'PowerShell'}
SKIP_REPOS = {LOGIN.lower(), f'{LOGIN}.github.io'.lower()}


def api(path):
    out = subprocess.run(['gh', 'api', path], capture_output=True, check=True)
    return json.loads(out.stdout.decode('utf-8'))


def front_matter(text):
    m = re.match(r'---\r?\n(.*?)\r?\n---', text, re.S)
    head = m.group(1) if m else ''
    meta = {'title': '', 'date': '', 'categories': []}
    key = None
    for line in head.splitlines():
        item = re.match(r'\s+-\s+(.*)', line)
        if item and key == 'categories':
            meta['categories'].append(item.group(1).strip().strip('"\''))
            continue
        kv = re.match(r'(\w+):\s*(.*)', line)
        if kv:
            key = kv.group(1)
            if key in ('title', 'date'):
                meta[key] = kv.group(2).strip().strip('"\'')
    return meta


def collect_posts():
    tree = api(f'repos/{BLOG}/git/trees/gh-pages?recursive=1')['tree']
    pages = [n['path'] for n in tree if n['path'].endswith('/index.html')]
    posts = []
    for entry in api(f'repos/{BLOG}/contents/source/_posts'):
        if not entry['name'].endswith('.md'):
            continue
        slug = entry['name'][:-3]
        # Hexo's permalink date is shifted by the timezone, so match the deployed path by slug.
        page = next((p for p in pages if p.endswith(f'/{slug}/index.html')), None)
        if page is None:
            continue
        raw = base64.b64decode(api(entry['url'].split('api.github.com/')[1])['content']).decode('utf-8')
        meta = front_matter(raw)
        posts.append({
            'title': meta['title'],
            'date': meta['date'][:10],
            'time': meta['date'],
            'category': meta['categories'][0] if meta['categories'] else '',
            'url': f'{SITE}/{page[:-len("index.html")]}',
        })
    posts.sort(key=lambda p: (p['time'], p['title']), reverse=True)
    for p in posts:
        del p['time']
    return posts


def collect_repos():
    repos = api(f'users/{LOGIN}/repos?per_page=100&sort=pushed')
    own = [r for r in repos if not r['fork']]
    totals = collections.Counter()
    for r in own:
        if r['name'].lower() in SKIP_REPOS:
            continue
        for lang, size in api(f'repos/{r["full_name"]}/languages').items():
            if lang not in SKIP_LANGS:
                totals[lang] += size
    whole = sum(totals.values()) or 1
    langs = [{'name': k, 'pct': round(v * 100 / whole, 1)} for k, v in totals.most_common(5)]
    work = [r for r in own if r['name'].lower() not in SKIP_REPOS]
    latest = max(work, key=lambda r: r['pushed_at'])
    return {
        'public_repos': len(own),
        'languages': langs,
        'last_push': {'repo': latest['name'], 'date': latest['pushed_at'][:10]},
        'repos': {r['name']: {'language': r['language'], 'pushed': r['pushed_at'][:10]} for r in work},
    }


def main():
    user = api(f'users/{LOGIN}')
    snap = {'since': user['created_at'][:10], **collect_repos(), 'posts': collect_posts()}
    path = ROOT / 'data' / 'snapshot.json'
    old = json.loads(path.read_text('utf-8')) if path.exists() else {}
    stamp = old.pop('generated_at', None)
    if old != snap or not stamp:
        stamp = datetime.date.today().isoformat()
    path.write_text(json.dumps({'generated_at': stamp, **snap}, ensure_ascii=False, indent=2) + '\n', 'utf-8')
    print(f'{stamp}: {snap["public_repos"]} repos, {len(snap["posts"])} posts')


if __name__ == '__main__':
    main()
