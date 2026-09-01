# -*- coding: utf-8 -*-
"""Inspect all candidate Bing/Baidu files to find ones with real EVE content."""
import sys, os
from bs4 import BeautifulSoup
sys.stdout.reconfigure(encoding='utf-8')

# All candidate files
files = [
    r"D:\AI\ai-berkshire\.tmp_research\bing_eve_consumer.html",
    r"D:\AI\ai-berkshire\.tmp_research\bing_eve_storage2025.html",
    r"D:\AI\ai-berkshire\.tmp_research\bing_eve_sungrow.html",
    r"D:\AI\ai-berkshire\.tmp_research\bing_eve_tesla.html",
    r"D:\AI\ai-berkshire\.tmp_research\bing_eve_xpeng.html",
    r"D:\AI\ai-berkshire\.tmp_research\bing2_eve_xpeng.html",
    r"D:\AI\ai-berkshire\.tmp_research\bing3_eve_gac.html",
    r"D:\AI\ai-berkshire\.tmp_research\eve\bing_bmw.html",
    r"D:\AI\ai-berkshire\.tmp_research\eve\bing_bmw2.html",
    r"D:\AI\ai-berkshire\.tmp_research\eve\bing_bmw_en.html",
    r"D:\AI\ai-berkshire\.tmp_research\eve\baidu_bmw.html",
    r"D:\AI\ai-berkshire\.tmp_research\eve\so_bmw.html",
    r"D:\AI\ai-berkshire\.tmp_research\eve\sogou_bmw.html",
    r"D:\AI\ai-berkshire\.tmp_research\eve\sogou_news_bmw.html",
    r"D:\AI\ai-berkshire\.tmp_research\sogou_eve_xpeng.html",
    r"D:\AI\ai-berkshire\.tmp_research\baidu_eve_xpeng.html",
]

for path in files:
    if not os.path.exists(path):
        print(f"[NOT FOUND] {path}")
        continue
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        html = f.read()
    soup = BeautifulSoup(html, 'html.parser')
    for s in soup(['script', 'style', 'noscript']):
        s.decompose()
    title = soup.title.get_text(strip=True) if soup.title else ""
    # Count "亿纬" mentions in body
    body_text = soup.get_text(' ', strip=True)
    eve_count = body_text.count('亿纬')
    # Detect censorship notice
    censored = ('部分搜索结果未予显示' in body_text or
                '本地法律要求' in body_text)
    # count links
    cite_count = len(soup.find_all('cite'))
    print(f"\n=== {os.path.basename(path)} ===")
    print(f"  TITLE: {title[:120]}")
    print(f"  EVE mentions: {eve_count} | Censored: {censored} | cite tags: {cite_count}")
