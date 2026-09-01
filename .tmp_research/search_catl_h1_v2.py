#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Round 2: fill gaps - Q1 commitments detail + H2 guidance."""
import re, os, subprocess, urllib.parse, time, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = r'D:\AI\ai-berkshire\.tmp_research\catl_h1'
PROXY = 'http://127.0.0.1:7897'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'

QUERIES = [
    # Q1电话会承诺细节
    ('bd', '宁德时代 Q1电话会 全年毛利率 相对稳定 二季度排产', 'qp1_bd'),
    ('bd', '宁德时代 FY26 Q1 电话会 产能利用率 85 90', 'qp2_bd'),
    # H1业绩会FY指引
    ('bd', '宁德时代 中报 业绩会 2027 增速 更好 指引', 'qg1_bd'),
    ('bd', '宁德时代 业绩会 全年 毛利率 指引 24 25', 'qg2_bd'),
    # 关键Q&A尖锐问题
    ('bd', '宁德时代 业绩说明会 分析师 提问 比亚迪 固态', 'qq1_bd'),
    ('so', '宁德时代 中报 业绩会 提问 储能 价格战 中东', 'qq1_so'),
    # 详细问答
    ('bd', '宁德时代 半年报 业绩会 纪要 问答 Q&A', 'qq2_bd'),
    # 大摩/麦格理目标价
    ('bd', '宁德时代 大摩 麦格理 目标价 港元 评级', 'qt1_bd'),
    # 蒋理发言
    ('bd', '宁德时代 蒋理 业绩说明会 2026 中报', 'qj1_bd'),
    # 财联社/新浪报道
    ('so', '宁德时代 中报 电话会 财联社 新浪', 'qnr_so'),
]

def strip_tags(s):
    s = re.sub(r'<[^>]+>', ' ', s)
    import html
    s = html.unescape(s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def fetch(url, out_html, lang='zh-CN,zh'):
    cmd = ['curl','-sL','-m','30','-A',UA,'-x',PROXY,
           '-H', f'Accept-Language: {lang},q=0.9',
           '-H','Referer: https://www.baidu.com/',
           url, '-o', out_html, '-w', '%{http_code}|%{size_download}']
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout.strip()

def parse_baidu(data):
    results = []
    blocks = re.findall(r'<div[^>]*class="[^"]*c-container[^"]*"[^>]*>(.*?)(?=<div[^>]*class="[^"]*c-container|<div[^>]*id="rs"|<div[^>]*id="content_right"|$)', data, re.S)
    if not blocks:
        blocks = re.split(r'(?=<h3)', data)
    for r in blocks:
        title_m = re.search(r'<h3[^>]*>(.*?)</h3>', r, re.S)
        if not title_m: continue
        title_html = title_m.group(1)
        title_text = strip_tags(title_html)
        link_m = re.search(r'<a[^>]+href="([^"]+)"', title_html)
        link = link_m.group(1) if link_m else ''
        snippet = ''
        after_h3 = r.split('</h3>', 1)[-1] if '</h3>' in r else ''
        for pat in [r'<span[^>]*class="content-right_[^"]*"[^>]*>(.*?)</span>',
                    r'<div[^>]*class="c-abstract[^"]*"[^>]*>(.*?)</div>',
                    r'<span[^>]*class="[^"]*"[^>]*>(.{50,400}?)</span>']:
            m = re.search(pat, after_h3, re.S)
            if m:
                snippet = strip_tags(m.group(1))
                if len(snippet) > 30: break
        if not snippet:
            snippet = strip_tags(after_h3)[:300]
        if title_text and link:
            results.append((title_text[:200], link[:250], snippet[:400]))
    return results

def parse_360(data):
    results = []
    blocks = re.findall(r'<li[^>]*class="[^"]*res-list[^"]*"[^>]*>(.*?)</li>', data, re.S)
    if not blocks:
        blocks = re.split(r'(?=<h3)', data)
    for r in blocks:
        title_m = re.search(r'<h3[^>]*>(.*?)</h3>', r, re.S)
        if not title_m: continue
        title = strip_tags(title_m.group(1))
        link_m = re.search(r'<a[^>]+href="(https?://[^"]+|/link\?[^"]+)"', title_m.group(1))
        link = link_m.group(1) if link_m else ''
        after_h3 = r.split('</h3>', 1)[-1]
        snip = ''
        for pat in [r'<p[^>]*class="[^"]*res-desc[^"]*"[^>]*>(.*?)</p>',
                    r'<p[^>]*class="[^"]*"[^>]*>(.*?)</p>']:
            m = re.search(pat, after_h3, re.S)
            if m:
                cand = strip_tags(m.group(1))
                if len(cand) > 40: snip = cand; break
        if not snip: snip = strip_tags(after_h3)[:300]
        if title and len(title) > 5:
            results.append((title[:200], link[:250], snip[:400]))
    return results

def run_search(engine, q, tag, idx):
    enc = urllib.parse.quote(q)
    if engine == 'so':
        url = f'https://www.so.com/s?q={enc}'
    else:
        url = f'https://www.baidu.com/s?wd={enc}'
    out_html = f'{BASE}\\html\\r2_{engine}_{tag}_{idx}.html'
    info = fetch(url, out_html)
    if not os.path.exists(out_html):
        return f'\n=====[{engine}/{tag}] {q}=====\nNO FILE: {info}'
    data = open(out_html, 'r', encoding='utf-8', errors='ignore').read()
    results = parse_360(data) if engine == 'so' else parse_baidu(data)
    lines = [f'\n=====[{engine}/{tag}] {q}=====\n(curl: {info}, results: {len(results)})']
    for i, (t, l, s) in enumerate(results[:8], 1):
        lines.append(f'  [{i}] {t}')
        if l: lines.append(f'      URL: {l}')
        if s and len(s) > 25: lines.append(f'      SNIP: {s}')
    return '\n'.join(lines)

OUT = open(BASE + r'\search_results_r2.txt', 'w', encoding='utf-8')
for i, (engine, q, tag) in enumerate(QUERIES, 1):
    try:
        OUT.write(run_search(engine, q, tag, i) + '\n')
        OUT.flush()
    except Exception as e:
        OUT.write(f'\n=====ERROR [{engine}/{tag}] {q}: {e}=====\n')
    time.sleep(1.2)
OUT.close()
print('Done')
