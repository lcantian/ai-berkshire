#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Round 4 - pinpoint missing data."""
import re, os, subprocess, urllib.parse, time, html

BASE = r'D:\AI\ai-berkshire\.tmp_research\catl_research'
OUT = open(BASE + r'\results4.txt', 'w', encoding='utf-8')

PROXY = 'http://127.0.0.1:7897'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'

QUERIES = [
    '宁德时代 2026 中报 动力电池系统 收入 亿元 同比',
    '宁德时代 上半年 储能 532亿 收入',
    '宁德时代 2026H1 研发投入 亿元 占营收',
    '宁德时代 2026 中报 政府补助 其他收益',
    '宁德时代 上半年 境外收入 同比 占比 提升',
    '宁德时代 2026H1 货币资金 交易性金融资产',
    '宁德时代 2026 H1 应付账款 应收账款 存货',
    '宁德时代 中报 2026 H1 短期借款 长期借款',
    '宁德时代 上半年 资本开支 购建固定资产',
    '宁德时代 2026 H1 前五大客户 占比 集中度',
    '宁德时代 产能 1050GWh 利用率 94.86%',
    '宁德时代 业绩会 2026Q2 业绩会速记',
    '宁德时代 26Q2 业绩会 纪要 储能',
    '宁德时代 中报 2026 财务费用 汇兑',
]

def strip_tags(s):
    s = re.sub(r'<[^>]+>', ' ', s)
    s = html.unescape(s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def search_baidu(q, idx):
    enc = urllib.parse.quote(q)
    url = f'https://www.baidu.com/s?wd={enc}&rn=15'
    out_html = f'{BASE}\\html\\bd4_{idx}.html'
    cmd = ['curl','-sL','-m','25','-x',PROXY,'-A',UA,
           '-H','Accept-Language: zh-CN,zh;q=0.9',
           '-H','Referer: https://www.baidu.com/',
           url, '-o', out_html, '-w', '%{http_code}|%{size_download}']
    r = subprocess.run(cmd, capture_output=True, text=True)
    if not os.path.exists(out_html):
        return ''
    data = open(out_html, 'r', encoding='utf-8', errors='ignore').read()
    lines = [f'\n=====Baidu[Q{idx}] {q}=====', f'(size={len(data)})']
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
        if count <= 7:
            lines.append(f'  [{count}] {title[:200]}')
            lines.append(f'      URL: {link[:250]}')
    return '\n'.join(lines)

for i, q in enumerate(QUERIES, 1):
    OUT.write(search_baidu(q, i) + '\n')
    OUT.flush()
    time.sleep(1.5)
OUT.close()
print('Done')
