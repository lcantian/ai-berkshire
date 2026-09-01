#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Round 3 search - dig into 2026H1 specific numbers."""
import re, os, subprocess, urllib.parse, time, html

BASE = r'D:\AI\ai-berkshire\.tmp_research\catl_research'
OUT = open(BASE + r'\results3.txt', 'w', encoding='utf-8')

PROXY = 'http://127.0.0.1:7897'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'

QUERIES = [
    # storage 87% revenue - which article has it
    '宁德时代 2026 储能系统 收入 增长 87%',
    '宁德时代 2026H1 储能 收入 亿元',
    '宁德时代 上半年 动力电池 营收 同比 增长',
    '宁德时代 上半年 境外收入 30.6%',
    '宁德时代 2026 上半年 电池材料 回收 矿产',
    '宁德时代 中报 2026 研发 费用',
    '宁德时代 2026 中报 研发投入 占比',
    '宁德时代 2026 H1 短期借款 长期借款 资产负债率',
    '宁德时代 6000亿 负债 2026',
    '宁德时代 2026H1 货币资金 期末 余额',
    '宁德时代 政府补助 利润 占比 2026',
    '宁德时代 财务费用 汇率 损失 2026 中报',
    '宁德时代 2026 中报 产能 利用率',
    '宁德时代 匈牙利 工厂 投产 2026 上半年',
    '宁德时代 H股 配售 391亿 628港元',
    '宁德时代 2026 上半年 自由现金流',
]

def strip_tags(s):
    s = re.sub(r'<[^>]+>', ' ', s)
    s = html.unescape(s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def search_baidu(q, idx):
    enc = urllib.parse.quote(q)
    url = f'https://www.baidu.com/s?wd={enc}&rn=15'
    out_html = f'{BASE}\\html\\bd3_{idx}.html'
    cmd = ['curl','-sL','-m','25','-x',PROXY,'-A',UA,
           '-H','Accept-Language: zh-CN,zh;q=0.9',
           '-H','Referer: https://www.baidu.com/',
           url, '-o', out_html, '-w', '%{http_code}|%{size_download}']
    r = subprocess.run(cmd, capture_output=True, text=True)
    info = r.stdout.strip()
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
