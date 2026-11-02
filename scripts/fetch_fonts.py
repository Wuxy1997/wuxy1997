#!/usr/bin/env python3
"""Download the open fonts the panels are outlined from. Pinned so a re-render never shifts."""
import pathlib
import urllib.parse
import urllib.request

COMMIT = '6c1dbe27dcf7d817d4b62cec033ba77fa8e2a5ec'
BASE = f'https://raw.githubusercontent.com/google/fonts/{COMMIT}/ofl'
OUT = pathlib.Path(__file__).resolve().parent.parent / '.fonts'

FILES = {
    'NotoSansSC.ttf': 'notosanssc/NotoSansSC[wght].ttf',
    'NotoSerifSC.ttf': 'notoserifsc/NotoSerifSC[wght].ttf',
    'JetBrainsMono.ttf': 'jetbrainsmono/JetBrainsMono[wght].ttf',
    'Barlow-Light.ttf': 'barlow/Barlow-Light.ttf',
    'Barlow-Regular.ttf': 'barlow/Barlow-Regular.ttf',
    'Barlow-Medium.ttf': 'barlow/Barlow-Medium.ttf',
    'OFL-Barlow.txt': 'barlow/OFL.txt',
    'OFL-JetBrainsMono.txt': 'jetbrainsmono/OFL.txt',
    'OFL-NotoSansSC.txt': 'notosanssc/OFL.txt',
    'OFL-NotoSerifSC.txt': 'notoserifsc/OFL.txt',
}


def main():
    OUT.mkdir(exist_ok=True)
    for name, src in FILES.items():
        dst = OUT / name
        if dst.exists():
            continue
        url = f'{BASE}/{urllib.parse.quote(src)}'
        print('fetch', name)
        with urllib.request.urlopen(url, timeout=300) as r:
            dst.write_bytes(r.read())


if __name__ == '__main__':
    main()
