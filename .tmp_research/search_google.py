#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Google search via proxy for English data."""
import re, os, subprocess, urllib.parse, time

BASE = r'D:\AI\ai-berkshire\.tmp_research'
OUT = open(BASE + r'\search_google_en.txt', 'w', encoding='utf-8')

PROXY = 'http://127.0.0.1:7897'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'

QUERIES = [
    'Eramet Centenario Ratones Argentina DLE lithium cash cost per tonne',
    'Eramet Argentina lithium 24000 tonne production cost 2025',
    'Livent Allkem Hombre Muerto DLE production cost USD per tonne',
    'SQM Albemarle Salar de Atacama brine lithium cost per tonne',
    'Core Lithium Finniss suspended January 2024 C1 cost',
    'Liontown Kathleen Valley ramp up delay 2024 2025 production',
    'Pilbara Minerals C1 cash cost FY2025 FOB spodumene',
    'Sigma Lithium cash cost Brazil Grota do Cirilo',
    'Goulamina Mali lithium Firefinch Ganfeng cash cost',
    'Arcadium Lithium Mt Cattlin care maintenance 2025',
    'Albemarle cost reduction 2024 layoffs Kemerton Wodgina',
    'Zimbabwe lithium export ban 2026 Arcadia Bikita',
    'Ganfeng Lithium Mariana Argentina DLE cost',
    'direct lithium extraction DLE cost comparison brine evaporation 2024',
]

def strip_tags(s):
    s = re.sub(r'<[^>]+>', ' ', s)
    import html
    s = html.unescape(s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def search(q, idx):
    enc = urllib.parse.quote(q)
    url = f'https://www.google.com/search?q={enc}&hl=en'
    out_html = f'{BASE}\\html\\g_{idx}.html'
    os.makedirs(os.path.dirname(out_html), exist_ok=True)
    cmd = ['curl','-sL','-m','25','-x',PROXY,'-A',UA,
           '-H','Accept-Language: en-US,en;q=0.9',
           '-H','Referer: https://www.google.com/',
           url, '-o', out_html, '-w', '%{http_code}|%{size_download}']
    r = subprocess.run(cmd, capture_output=True, text=True)
    info = r.stdout.strip()
    if not os.path.exists(out_html):
        return f'[Q{idx}] {q} -> NO FILE: {info}'
    data = open(out_html, 'r', encoding='utf-8', errors='ignore').read()
    lines = [f'\n==========[Q{idx}] {q}==========']
    lines.append(f'(curl: {info}, size={len(data)})')
    # Google results: capture all <a href="/url?q=URL">
    # Then text near each link
    # try to split by result blocks
    # Google structure varies - extract <h3>..</h3> as titles with surrounding text
    # Approach: find all h3s, then the link above and snippet below
    h3_positions = [(m.start(), m.end(), m.group(1)) for m in re.finditer(r'<h3[^>]*>(.*?)</h3>', data, re.S)]
    count = 0
    for i, (s, e, h3_html) in enumerate(h3_positions):
        # find link before this h3 (within 300 chars)
        before = data[max(0, s-400):s]
        link_m = re.search(r'<a[^>]+href="(/url\?q=([^&"]+)[^"]*|https?://[^"]+)"', before)
        if not link_m:
            continue
        link = link_m.group(2) if link_m.group(1).startswith('/url') else link_m.group(1)
        if not link.startswith('http'):
            continue
        # Filter out google domains
        if any(d in link for d in ['google.com','youtube.com','gstatic.com','blogger.com','webcache.']):
            continue
        title = strip_tags(h3_html)
        if len(title) < 8:
            continue
        # find snippet after h3 (next 2000 chars)
        after = data[e:e+2500]
        # Google snippet usually in <span>...</span>
        snip = ''
        for pat in [r'<span[^>]*class="[^"]*"[^>]*>(.{40,500}?)</span>',
                    r'<div[^>]*class="[^"]*"[^>]*>(.{40,500}?)</div>']:
            m = re.search(pat, after, re.S)
            if m:
                cand = strip_tags(m.group(1))
                if len(cand) > 60 and not cand.lower().startswith('http'):
                    snip = cand[:350]
                    break
        count += 1
        if count <= 10:
            lines.append(f'  [{count}] {title[:160]}')
            lines.append(f'      URL: {link[:220]}')
            if snip: lines.append(f'      SNIP: {snip[:350]}')
    return '\n'.join(lines)

for i, q in enumerate(QUERIES, 1):
    OUT.write(search(q, i) + '\n')
    OUT.flush()
    time.sleep(2)
OUT.close()
print('Done')
