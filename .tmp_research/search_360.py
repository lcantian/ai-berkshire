#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Search 360 (so.com) for many queries and dump results."""
import re, sys, os, subprocess, urllib.parse, time

BASE = r'D:\AI\ai-berkshire\.tmp_research'
OUT = open(BASE + r'\search360_all.txt', 'w', encoding='utf-8')

PROXY = 'http://127.0.0.1:7897'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'

QUERIES = [
    '藏格矿业 察尔汗 盐湖提锂 单吨 成本',
    '华友钴业 Arcadia 津巴布韦 锂矿 成本 现金',
    '东台吉乃尔 盐湖提锂 成本 青海锂业',
    '西台吉乃尔 盐湖 锂 成本',
    '一里坪 盐湖 五矿 盐湖提锂 成本',
    'Albemarle 雅保 削减产能 减产 2024',
    'Sigma Lithium 锂矿 现金成本 Brazil',
    '紫金矿业 阿根廷 3Q 锂盐湖 成本',
    'Livent Allkem 阿根廷 DLE 成本 USD',
    'Goulamina 马里 锂矿 成本',
    'Arcadium Lithium 现金成本 2025',
    'Pilbara Minerals 现金成本 FOB 2025',
    '非洲 锂矿 现金成本 高成本 边际产能 2025',
    '江西 锂云母 全面停产 2024 2025',
    'Albemarle Greenbushes 减产 2025',
    '直接提锂 DLE 现金成本 美元/吨LCE 吸附法',
    '盐湖股份 蓝科锂业 2025 现金成本',
    '科盐湖 青海 锂 提锂 完全成本 万元',
]

def strip_tags(s):
    s = re.sub(r'<[^>]+>', ' ', s)
    import html
    s = html.unescape(s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def search(q, idx):
    enc = urllib.parse.quote(q)
    url = f'https://www.so.com/s?q={enc}'
    out_html = f'{BASE}\\html\\so_{idx}.html'
    os.makedirs(os.path.dirname(out_html), exist_ok=True)
    cmd = ['curl','-sL','-m','25','-x',PROXY,'-A',UA,
           '-H','Accept-Language: zh-CN,zh;q=0.9',
           '-H','Referer: https://www.so.com/',
           url, '-o', out_html, '-w', '%{http_code}|%{size_download}']
    r = subprocess.run(cmd, capture_output=True, text=True)
    info = r.stdout.strip()
    if not os.path.exists(out_html):
        return f'[Q{idx}] {q} -> NO FILE: {info}'
    data = open(out_html, 'r', encoding='utf-8', errors='ignore').read()
    lines = [f'\n==========[Q{idx}] {q}==========']
    lines.append(f'(curl: {info}, size={len(data)})')
    blocks = re.findall(r'<li[^>]*class="[^"]*res-list[^"]*"[^>]*>(.*?)</li>', data, re.S)
    if not blocks:
        # alt structure
        blocks = re.split(r'(?=<h3)', data)
    count = 0
    for r in blocks:
        title_m = re.search(r'<h3[^>]*>(.*?)</h3>', r, re.S)
        if not title_m:
            continue
        title = strip_tags(title_m.group(1))
        link_m = re.search(r'<a[^>]+href="(https?://[^"]+|/link\?[^"]+)"', title_m.group(1))
        link = link_m.group(1) if link_m else ''
        snip = ''
        after_h3 = r.split('</h3>', 1)[-1]
        # Look for snippet paragraph
        for pat in [r'<p[^>]*class="[^"]*res-desc[^"]*"[^>]*>(.*?)</p>',
                    r'<p[^>]*class="[^"]*[^"]*"[^>]*>(.*?)</p>',
                    r'<span[^>]*>(.*?)</span>']:
            m = re.search(pat, after_h3, re.S)
            if m:
                cand = strip_tags(m.group(1))
                if len(cand) > 40:
                    snip = cand
                    break
        if not snip:
            snip = strip_tags(after_h3)[:300]
        if title and len(title) > 5:
            count += 1
            if count <= 10:
                lines.append(f'  [{count}] {title[:150]}')
                if link: lines.append(f'      URL: {link[:200]}')
                if snip and len(snip)>30: lines.append(f'      SNIP: {snip[:280]}')
        if count >= 10: break
    return '\n'.join(lines)

for i, q in enumerate(QUERIES, 1):
    OUT.write(search(q, i) + '\n')
    OUT.flush()
    time.sleep(1.5)
OUT.close()
print('Done')
