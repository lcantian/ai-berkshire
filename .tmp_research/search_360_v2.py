#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""More 360 searches to fill gaps."""
import re, os, subprocess, urllib.parse, time

BASE = r'D:\AI\ai-berkshire\.tmp_research'
OUT = open(BASE + r'\search360_more.txt', 'w', encoding='utf-8')

PROXY = 'http://127.0.0.1:7897'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'

QUERIES = [
    'Eramet 阿根廷 Centenario 现金成本 5000 美元',
    '赣锋锂业 阿根廷 Mariana 盐湖 成本',
    '蓝晓科技 吸附剂 阿根廷 Salta 盐湖',
    '雅化集团 Kamativv 津巴布韦 锂矿 成本',
    '盛新锂能 津巴布韦 锂矿萨比星 成本',
    '中矿资源 Bikita Tanco 成本 2025',
    '天齐锂业 Greenbushes 锂精矿 现金成本',
    '藏格矿业 老卤 吸附法 膜法 成本',
    '西藏矿业 扎布耶 2024年 年报 锂盐',
    '澳洲 Wodgina Mineral Resources 减产 2024',
    '马里 Goulamina 一期 投产 现金成本 2024',
    'Patriot Battery Metals Corvette 锂矿 成本',
    '非洲 锂矿 运输成本 海运 中国',
    '纳米比亚 锂矿 Xuxenbergs Usakos 成本',
    '加纳 Atlantic Lithium Ewoyaa 成本',
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
    out_html = f'{BASE}\\html\\so2_{idx}.html'
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
            if count <= 8:
                lines.append(f'  [{count}] {title[:150]}')
                if link: lines.append(f'      URL: {link[:200]}')
                if snip and len(snip)>30: lines.append(f'      SNIP: {snip[:280]}')
        if count >= 8: break
    return '\n'.join(lines)

for i, q in enumerate(QUERIES, 1):
    OUT.write(search(q, i) + '\n')
    OUT.flush()
    time.sleep(1.5)
OUT.close()
print('Done')
