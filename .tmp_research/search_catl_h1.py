#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Search multiple engines for CATL 2026 H1 earnings call / Q2 gross margin."""
import re, os, subprocess, urllib.parse, time, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = r'D:\AI\ai-berkshire\.tmp_research\catl_h1'
os.makedirs(BASE, exist_ok=True)
os.makedirs(BASE + r'\html', exist_ok=True)

PROXY = 'http://127.0.0.1:7897'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'

# Queries: (engine, query, tag)
# engines: so=360, gg=google, bd=baidu
QUERIES = [
    # 业绩说明会/电话会纪要 (中文，最关键)
    ('so', '宁德时代 2026年 中报 业绩说明会 纪要', 'qmeeting_so1'),
    ('so', '宁德时代 2026 半年报 电话会 管理层', 'qmeeting_so2'),
    ('so', '宁德时代 300750 2026 业绩会 曾毓群 周佳', 'qmeeting_so3'),
    ('bd', '宁德时代 2026 中报 业绩说明会 纪要', 'qmeeting_bd1'),
    ('bd', '宁德时代 2026 二季度 业绩会 毛利率', 'qmeeting_bd2'),
    ('bd', '宁德时代 2026H1 电话会议 分析师', 'qmeeting_bd3'),
    # Q2 毛利率下行解释
    ('so', '宁德时代 Q2 毛利率 下滑 原因 储能', 'qmargin_so1'),
    ('so', '宁德时代 2026 二季度 毛利率 23%', 'qmargin_so2'),
    ('bd', '宁德时代 2026 半年报 毛利率 下滑', 'qmargin_bd1'),
    ('bd', '宁德时代 储能 毛利率 拖累 2026', 'qmargin_bd2'),
    # 英文
    ('gg', 'CATL 2026 H1 earnings call transcript gross margin Q2', 'qen_gg1'),
    ('gg', 'CATL Ningde 300750 2026 interim results analyst call', 'qen_gg2'),
    ('gg', 'CATL 2026 H1 gross margin decline energy storage lithium', 'qen_gg3'),
    # 曾毓群近期表态
    ('so', '曾毓群 2026 固态电池 凝聚态 最新表态', 'qzeng_so1'),
    ('so', '曾毓群 LRS 技术授权 福特 海外', 'qzeng_so2'),
    ('so', '曾毓群 2026 中报 财报 解读', 'qzeng_so3'),
    ('bd', '曾毓群 巧克力换电 2026 进展', 'qzeng_bd1'),
    ('bd', '曾毓群 2026 中报 发言 指引', 'qzeng_bd2'),
    # 海外业务 / 市占率
    ('so', '宁德时代 2026 全球 市占率 海外 业务', 'qshare_so1'),
    ('bd', '宁德时代 匈牙利 工厂 2026 进展', 'qshare_bd1'),
    # 承诺追踪：Q1业绩会承诺
    ('so', '宁德时代 2026 一季度 业绩会 全年 指引', 'qpromise_so1'),
    ('bd', '宁德时代 2026 Q1 电话会 25-30% 增速', 'qpromise_bd1'),
]

def strip_tags(s):
    s = re.sub(r'<[^>]+>', ' ', s)
    import html
    s = html.unescape(s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def fetch(url, out_html, use_proxy=True, lang='zh-CN'):
    cmd = ['curl','-sL','-m','30','-A',UA,
           '-H', f'Accept-Language: {lang},q=0.9']
    if use_proxy:
        cmd += ['-x', PROXY]
    if 'so.com' in url:
        cmd += ['-H','Referer: https://www.so.com/']
    elif 'google' in url:
        cmd += ['-H','Referer: https://www.google.com/']
    elif 'baidu' in url:
        cmd += ['-H','Referer: https://www.baidu.com/']
    cmd += [url, '-o', out_html, '-w', '%{http_code}|%{size_download}']
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout.strip()

def parse_360(data):
    """360 so.com result parser."""
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
                    r'<p[^>]*class="[^"]*"[^>]*>(.*?)</p>',
                    r'<span[^>]*>(.*?)</span>']:
            m = re.search(pat, after_h3, re.S)
            if m:
                cand = strip_tags(m.group(1))
                if len(cand) > 40:
                    snip = cand; break
        if not snip:
            snip = strip_tags(after_h3)[:300]
        if title and len(title) > 5:
            results.append((title[:200], link[:250], snip[:350]))
    return results

def parse_google(data):
    """Google result parser."""
    results = []
    h3_positions = [(m.start(), m.end(), m.group(1)) for m in re.finditer(r'<h3[^>]*>(.*?)</h3>', data, re.S)]
    for s, e, h3_html in h3_positions:
        before = data[max(0, s-400):s]
        link_m = re.search(r'<a[^>]+href="(/url\?q=([^&"]+)[^"]*|https?://[^"]+)"', before)
        if not link_m: continue
        link = link_m.group(2) if link_m.group(1).startswith('/url') else link_m.group(1)
        if not link.startswith('http'): continue
        if any(d in link for d in ['google.com','youtube.com','gstatic.com','blogger.com','webcache.']):
            continue
        title = strip_tags(h3_html)
        if len(title) < 8: continue
        after = data[e:e+2500]
        snip = ''
        for pat in [r'<span[^>]*class="[^"]*"[^>]*>(.{40,500}?)</span>',
                    r'<div[^>]*class="[^"]*"[^>]*>(.{40,500}?)</div>']:
            m = re.search(pat, after, re.S)
            if m:
                cand = strip_tags(m.group(1))
                if len(cand) > 60 and not cand.lower().startswith('http'):
                    snip = cand[:400]; break
        results.append((title[:200], link[:250], snip[:400]))
    return results

def parse_baidu(data):
    """Baidu result parser."""
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
            results.append((title_text[:200], link[:250], snippet[:350]))
    return results

def run_search(engine, q, tag, idx):
    enc = urllib.parse.quote(q)
    if engine == 'so':
        url = f'https://www.so.com/s?q={enc}'
        lang = 'zh-CN,zh'
    elif engine == 'gg':
        url = f'https://www.google.com/search?q={enc}&hl=en'
        lang = 'en-US,en'
    else:  # bd
        url = f'https://www.baidu.com/s?wd={enc}'
        lang = 'zh-CN,zh'
    out_html = f'{BASE}\\html\\{engine}_{tag}_{idx}.html'
    info = fetch(url, out_html, use_proxy=True, lang=lang)
    if not os.path.exists(out_html):
        return f'\n=====[{engine}/{tag}] {q}=====\nNO FILE: {info}'
    data = open(out_html, 'r', encoding='utf-8', errors='ignore').read()
    if engine == 'so':
        results = parse_360(data)
    elif engine == 'gg':
        results = parse_google(data)
    else:
        results = parse_baidu(data)
    lines = [f'\n=====[{engine}/{tag}] {q}=====\n(curl: {info}, results: {len(results)})']
    for i, (t, l, s) in enumerate(results[:10], 1):
        lines.append(f'  [{i}] {t}')
        if l: lines.append(f'      URL: {l}')
        if s and len(s) > 25: lines.append(f'      SNIP: {s}')
    return '\n'.join(lines)

OUT = open(BASE + r'\search_results.txt', 'w', encoding='utf-8')
for i, (engine, q, tag) in enumerate(QUERIES, 1):
    try:
        OUT.write(run_search(engine, q, tag, i) + '\n')
        OUT.flush()
    except Exception as e:
        OUT.write(f'\n=====ERROR [{engine}/{tag}] {q}: {e}=====\n')
        OUT.flush()
    time.sleep(1.5)
OUT.close()
print('Done')
