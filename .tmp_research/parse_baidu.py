#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re, sys, os, glob, io
from html import unescape

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def strip_tags(s):
    s = re.sub(r'<[^>]+>', ' ', s)
    s = unescape(s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

SEARCH_DIR = os.path.dirname(os.path.abspath(__file__))

queries = [
    'DLE 直接提锂 成本 美元 吨 碳酸锂',
    '津巴布韦 锂矿 Bikita 现金成本 中矿资源',
    '盐湖股份 察尔汗 提锂 完全成本',
    'Core Lithium Finniss 停产',
    'Pilbara Minerals 减产 FY2025',
    '江特电机 锂云母 停产 减产',
    '永兴材料 锂云母 成本',
    'Liontown Kathleen Valley 投产 延迟',
]

for i, q in enumerate(queries, 1):
    fp = os.path.join(SEARCH_DIR, 'baidu_search', f'r{i}.html')
    if not os.path.exists(fp):
        # Try the C:\temp path
        fp2 = f'C:/Users/cantianlei/AppData/Local/Temp/baidu_search/r{i}.html'
        if os.path.exists(fp2):
            fp = fp2
    if not os.path.exists(fp):
        print(f'[{i}] MISSING: {fp}')
        continue
    data = open(fp, 'r', encoding='utf-8', errors='ignore').read()
    print(f'\n==========[{i}] {q}==========')
    # Try to find each result block
    # Baidu uses <div class="result c-container ..."> or new <div class="c-container ...">
    blocks = re.findall(r'<div[^>]*class="[^"]*c-container[^"]*"[^>]*>(.*?)(?=<div[^>]*class="[^"]*c-container|<div[^>]*id="rs"|<div[^>]*id="content_right"|$)', data, re.S)
    if not blocks:
        # fallback to splitting by h3
        blocks = re.split(r'(?=<h3)', data)
    count = 0
    for r in blocks:
        title_m = re.search(r'<h3[^>]*>(.*?)</h3>', r, re.S)
        if not title_m:
            continue
        title_html = title_m.group(1)
        title_text = strip_tags(title_html)
        link_m = re.search(r'<a[^>]+href="([^"]+)"', title_html)
        link = link_m.group(1) if link_m else ''
        # get snippet
        snippet = ''
        after_h3 = r.split('</h3>', 1)[-1] if '</h3>' in r else ''
        # Try multiple snippet patterns
        for pat in [
            r'<span[^>]*class="content-right_[^"]*"[^>]*>(.*?)</span>',
            r'<div[^>]*class="c-abstract[^"]*"[^>]*>(.*?)</div>',
            r'<span[^>]*class="[^"]*"[^>]*>(.{50,400}?)</span>',
        ]:
            m = re.search(pat, after_h3, re.S)
            if m:
                snippet = strip_tags(m.group(1))
                if len(snippet) > 30:
                    break
        if not snippet:
            # take any text in the block
            snippet = strip_tags(after_h3)[:250]
        if title_text and link:
            count += 1
            if count <= 10:
                print(f'  [{count}] {title_text[:130]}')
                print(f'      URL: {link[:180]}')
                if snippet and len(snippet) > 30:
                    print(f'      SNIP: {snippet[:200]}')
        if count >= 10: break
