#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Search multiple engines for CATL 2026 H1 report data."""
import re, os, subprocess, urllib.parse, time, html

BASE = r'D:\AI\ai-berkshire\.tmp_research\catl_research'
os.makedirs(BASE, exist_ok=True)
os.makedirs(BASE + r'\html', exist_ok=True)
OUT = open(BASE + r'\results.txt', 'w', encoding='utf-8')

PROXY = 'http://127.0.0.1:7897'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'

QUERIES = [
    # head figure verification
    '宁德时代 2026年 中报 营业收入 2769亿 净利润 432亿',
    '宁德时代 300750 2026 半年报 毛利率 23.93',
    # business segment breakdown
    '宁德时代 2026 中报 储能电池 动力电池 收入 占比 毛利率',
    '宁德时代 2026 上半年 储能 出货量 GWh',
    '宁德时代 2026H1 动力电池 装机量 市占率 全球',
    'CATL 2026 H1 energy storage power battery shipment GWh',
    # regional + customer
    '宁德时代 2026 半年报 境外收入 海外 占比',
    '宁德时代 2026 中报 前五大客户 集中度',
    # cash flow + balance sheet
    '宁德时代 2026 中报 经营现金流 资本开支 capex 自由现金流',
    '宁德时代 2026 半年报 货币资金 短期借款 长期借款 存货',
    # R&D + overseas + notes
    '宁德时代 2026 研发费用 研发投入 半年报',
    '宁德时代 匈牙利工厂 德国工厂 进度 2026 H股 募资',
    '宁德时代 2026 半年报 政府补助 关联交易 或有负债',
    '宁德时代 2026 中期 分红 股权激励',
    # 2026 H1 detail
    '宁德时代 2026年 半年度报告 分业务 收入 拆解',
    '宁德时代 2026 中报 Q2 单季 毛利率',
]

def strip_tags(s):
    s = re.sub(r'<[^>]+>', ' ', s)
    s = html.unescape(s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def search_baidu(q, idx):
    """Baidu search."""
    enc = urllib.parse.quote(q)
    url = f'https://www.baidu.com/s?wd={enc}&rn=20'
    out_html = f'{BASE}\\html\\bd_{idx}.html'
    cmd = ['curl','-sL','-m','25','-x',PROXY,'-A',UA,
           '-H','Accept-Language: zh-CN,zh;q=0.9',
           '-H','Referer: https://www.baidu.com/',
           url, '-o', out_html, '-w', '%{http_code}|%{size_download}']
    r = subprocess.run(cmd, capture_output=True, text=True)
    info = r.stdout.strip()
    if not os.path.exists(out_html):
        return f'[B{idx}] {q} -> NO FILE: {info}'
    data = open(out_html, 'r', encoding='utf-8', errors='ignore').read()
    lines = [f'\n=====Baidu[Q{idx}] {q}=====', f'(curl: {info}, size={len(data)})']
    # Baidu results structure - extract result blocks
    # Find all h3 with links
    h3_blocks = re.findall(r'<h3[^>]*>(.*?)</h3>', data, re.S)
    count = 0
    seen = set()
    for h3 in h3_blocks:
        link_m = re.search(r'<a[^>]+href="(https?://[^"]+|/link\?[^"]+)"', h3)
        if not link_m:
            continue
        link = link_m.group(1)
        title = strip_tags(h3)
        if len(title) < 8 or title in seen:
            continue
        seen.add(title)
        count += 1
        if count <= 8:
            lines.append(f'  [{count}] {title[:200]}')
            lines.append(f'      URL: {link[:250]}')
    # Also try to extract snippets - baidu uses div with class c-abstract or span
    # simpler: just get all text blocks of 60+ chinese chars
    abstracts = re.findall(r'<span[^>]*class="[^"]*"[^>]*>([一-鿿\w\d\s%,.。、（）：-]{50,400})</span>', data)
    seen_abs = set()
    for i, a in enumerate(abstracts[:15]):
        a_clean = strip_tags(a)
        if len(a_clean) > 50 and a_clean not in seen_abs:
            seen_abs.add(a_clean)
            if i < 15:
                lines.append(f'  ABS: {a_clean[:350]}')
    return '\n'.join(lines)

def search_google(q, idx):
    enc = urllib.parse.quote(q)
    url = f'https://www.google.com/search?q={enc}&hl=zh-CN&num=15'
    out_html = f'{BASE}\\html\\g_{idx}.html'
    cmd = ['curl','-sL','-m','25','-x',PROXY,'-A',UA,
           '-H','Accept-Language: zh-CN,zh;q=0.9',
           '-H','Referer: https://www.google.com/',
           url, '-o', out_html, '-w', '%{http_code}|%{size_download}']
    r = subprocess.run(cmd, capture_output=True, text=True)
    info = r.stdout.strip()
    if not os.path.exists(out_html):
        return f'[G{idx}] {q} -> NO FILE: {info}'
    data = open(out_html, 'r', encoding='utf-8', errors='ignore').read()
    lines = [f'\n=====Google[Q{idx}] {q}=====', f'(curl: {info}, size={len(data)})']
    h3_positions = [(m.start(), m.end(), m.group(1)) for m in re.finditer(r'<h3[^>]*>(.*?)</h3>', data, re.S)]
    count = 0
    for s, e, h3_html in h3_positions:
        before = data[max(0, s-400):s]
        link_m = re.search(r'<a[^>]+href="(/url\?q=([^&"]+)[^"]*|https?://[^"]+)"', before)
        if not link_m:
            continue
        link = link_m.group(2) if link_m.group(1).startswith('/url') else link_m.group(1)
        if not link.startswith('http'):
            continue
        if any(d in link for d in ['google.com','youtube.com','gstatic.com','blogger.com','webcache.']):
            continue
        title = strip_tags(h3_html)
        if len(title) < 8:
            continue
        after = data[e:e+2500]
        snip = ''
        for pat in [r'<span[^>]*class="[^"]*"[^>]*>(.{40,500}?)</span>',
                    r'<div[^>]*class="[^"]*"[^>]*>(.{40,500}?)</div>']:
            m = re.search(pat, after, re.S)
            if m:
                cand = strip_tags(m.group(1))
                if len(cand) > 60 and not cand.lower().startswith('http'):
                    snip = cand[:400]
                    break
        count += 1
        if count <= 10:
            lines.append(f'  [{count}] {title[:200]}')
            lines.append(f'      URL: {link[:250]}')
            if snip: lines.append(f'      SNIP: {snip[:400]}')
    return '\n'.join(lines)

for i, q in enumerate(QUERIES, 1):
    OUT.write(search_baidu(q, i) + '\n')
    OUT.flush()
    time.sleep(1.5)
    OUT.write(search_google(q, i) + '\n')
    OUT.flush()
    time.sleep(2)
OUT.close()
print('Done')
