#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Search multiple engines for EVE Energy (300014) tech roadmap data."""
import re, os, subprocess, urllib.parse, html, time

BASE = r'D:\AI\ai-berkshire\.tmp_research\eve_research'
os.makedirs(BASE, exist_ok=True)
SUMMARY = open(BASE + r'\summary.txt', 'w', encoding='utf-8')

PROXY = 'http://127.0.0.1:7897'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'

QUERIES = [
    # LFP / NCM mix
    '亿纬锂能 磷酸铁锂 LFP 产能 GWh 2025',
    '亿纬锂能 三元 NCM 产能 惠州 荆门',
    '亿纬锂能 LMFP 磷酸锰铁锂 量产 时间',
    '亿纬锂能 大圆柱 46系列 46800 量产 宝马',
    # Solid state
    '亿纬锂能 龙泉二号 全固态 10Ah 300Wh',
    '亿纬锂能 半固态电池 量产 2026',
    '亿纬锂能 固态电池 中试线 荆门',
    # Sodium
    '亿纬锂能 钠离子电池 量产 客户',
    '亿纬锂能 钠离子 层状氧化物 聚阴离子',
    # Storage
    '亿纬锂能 Mr旗舰 储能 628Ah 5MWh',
    '亿纬锂能 储能 LMFP 量产 2025',
    '亿纬锂能 阳光电源 储能 合作',
    # Customers
    '亿纬锂能 宝马 46大圆柱 供货 2025',
    '亿纬锂能 特拉 供货 LFP',
    '亿纬锂能 小鹏 蔚来 动力电池',
    # R&D / patents
    '亿纬锂能 研发投入 占比 研发人员 2024',
    '亿纬锂能 发明专利 数量 技术',
    # Capacity expansion
    '亿纬锂能 全球产能 2025 2026 出货',
    '亿纬锂能 海外工厂 匈牙利 美国 马来西亚',
]

def strip_tags(s):
    s = re.sub(r'<script[^>]*>.*?</script>', '', s, flags=re.S)
    s = re.sub(r'<style[^>]*>.*?</style>', '', s, flags=re.S)
    s = re.sub(r'<[^>]+>', ' ', s)
    s = html.unescape(s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def fetch(url, label, idx, engine):
    out = f'{BASE}\\{engine}_{idx}_{label}.html'
    headers = [
        '-A', UA,
        '-H', 'Accept-Language: zh-CN,zh;q=0.9',
        '-H', f'Referer: https://www.{engine}.com/',
    ]
    cmd = ['curl','-sL','-m','25','-x',PROXY] + headers + [url,'-o',out,'-w','%{http_code}|%{size_download}']
    r = subprocess.run(cmd, capture_output=True, text=True)
    info = r.stdout.strip()
    try:
        with open(out, 'r', encoding='utf-8', errors='replace') as f:
            raw = f.read()
        # Extract results depending on engine
        if engine == 'bing':
            items = re.findall(r'<li class="b_algo"[^>]*>(.*?)</li>', raw, flags=re.S)
            for j, it in enumerate(items[:8]):
                title = re.search(r'<h2>(.*?)</h2>', it, flags=re.S)
                link = re.search(r'<a[^>]+href="([^"]+)"', it)
                abst = re.search(r'<p[^>]*>(.*?)</p>', it, flags=re.S)
                t = strip_tags(title.group(1)) if title else ''
                l = link.group(1) if link else ''
                a = strip_tags(abst.group(1)) if abst else ''
                SUMMARY.write(f'\n[BING {idx}.{j}] {label}\nTITLE: {t}\nURL: {l}\nABST: {a[:500]}\n')
        elif engine == 'sogou':
            items = re.findall(r'<div class="vrwrap[^"]*"[^>]*>(.*?)</div>\s*</div>', raw, flags=re.S)
            for j, it in enumerate(items[:8]):
                title = re.search(r'<h3[^>]*>(.*?)</h3>', it, flags=re.S)
                link = re.search(r'<a[^>]+href="([^"]+)"[^>]*target', it) or re.search(r'<a[^>]+href="([^"]+)"', it)
                abst = re.search(r'<div class="fz_ms[^"]*"[^>]*>(.*?)</div>', it, flags=re.S) or re.search(r'<p[^>]*>(.*?)</p>', it, flags=re.S)
                t = strip_tags(title.group(1)) if title else ''
                l = link.group(1) if link else ''
                a = strip_tags(abst.group(1)) if abst else ''
                SUMMARY.write(f'\n[SOGOU {idx}.{j}] {label}\nTITLE: {t}\nURL: {l}\nABST: {a[:500]}\n')
        elif engine == '360':
            items = re.findall(r'<li class="res-list[^"]*"[^>]*>(.*?)</li>', raw, flags=re.S)
            for j, it in enumerate(items[:8]):
                title = re.search(r'<h3[^>]*>(.*?)</h3>', it, flags=re.S)
                link = re.search(r'<a[^>]+href="([^"]+)"', it)
                abst = re.search(r'<p[^>]*class="res-desc[^"]*"[^>]*>(.*?)</p>', it, flags=re.S) or re.search(r'<p[^>]*>(.*?)</p>', it, flags=re.S)
                t = strip_tags(title.group(1)) if title else ''
                l = link.group(1) if link else ''
                a = strip_tags(abst.group(1)) if abst else ''
                SUMMARY.write(f'\n[360 {idx}.{j}] {label}\nTITLE: {t}\nURL: {l}\nABST: {a[:500]}\n')
        SUMMARY.write(f'[{engine.upper()} {idx}] {label} | {info} | {url[:100]}\n')
        return info
    except Exception as e:
        SUMMARY.write(f'[ERR {engine} {idx}] {label}: {e}\n')
        return 'ERR'

# Run Bing first - most reliable
for i, q in enumerate(QUERIES):
    enc = urllib.parse.quote(q)
    url = f'https://cn.bing.com/search?q={enc}&setlang=zh-CN'
    fetch(url, f'q{i}', i, 'bing')
    time.sleep(1.5)

SUMMARY.write('\n\n========== SOGOU ==========\n')
for i, q in enumerate(QUERIES):
    enc = urllib.parse.quote(q)
    url = f'https://www.sogou.com/web?query={enc}'
    fetch(url, f'q{i}', i, 'sogou')
    time.sleep(1.5)

SUMMARY.write('\n\n========== 360 ==========\n')
for i, q in enumerate(QUERIES):
    enc = urllib.parse.quote(q)
    url = f'https://www.so.com/s?q={enc}'
    fetch(url, f'q{i}', i, '360')
    time.sleep(1.5)

SUMMARY.close()
print('Done. See summary.txt')
