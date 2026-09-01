#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Round 2 search - more specific CATL data points."""
import re, os, subprocess, urllib.parse, time, html

BASE = r'D:\AI\ai-berkshire\.tmp_research\catl_research'
OUT = open(BASE + r'\results2.txt', 'w', encoding='utf-8')

PROXY = 'http://127.0.0.1:7897'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'

QUERIES = [
    # business segment - the key one
    '宁德时代 2026 半年报 动力电池系统 储能电池系统 收入 同比',
    '宁德时代 2026 上半年 储能 收入 增长 87.54%',
    '宁德时代 2026 中报 动力电池 毛利率 下降',
    '宁德时代 2026H1 储能 毛利率 提升',
    '宁德时代 2026 半年报 境外收入 海外 30%',
    '宁德时代 2026 上半年 研发投入 亿元',
    '宁德时代 中报 2026 经营活动现金流 净额',
    '宁德时代 2026 半年报 货币资金 期末',
    '宁德时代 2026 中报 短期借款 长期借款 资产负债率',
    '宁德时代 400亿 回购 注销 2026 中报',
    '宁德时代 2026 上半年 储能电池 出货 GWh 全球第一',
    '宁德时代 2026 动力电池 全球 市占率 第一 SNE',
    '宁德时代 2026 匈牙利 投产 进度 海外产能',
    '宁德时代 2026 H股 配售 392亿 绿色债券',
    '宁德时代 政府补助 占利润 比重 2026 中报',
    '宁德时代 2026 上半年 关联交易 预计 135.9亿',
]

def strip_tags(s):
    s = re.sub(r'<[^>]+>', ' ', s)
    s = html.unescape(s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def search_baidu(q, idx):
    enc = urllib.parse.quote(q)
    url = f'https://www.baidu.com/s?wd={enc}&rn=20'
    out_html = f'{BASE}\\html\\bd2_{idx}.html'
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
    return '\n'.join(lines)

for i, q in enumerate(QUERIES, 1):
    OUT.write(search_baidu(q, i) + '\n')
    OUT.flush()
    time.sleep(1.5)
OUT.close()
print('Done')
