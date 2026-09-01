# -*- coding: utf-8 -*-
"""Parse Bing/Sogou search result HTML files for EVE Energy (亿纬锂能) technical route data."""
import sys, os, json, re
from bs4 import BeautifulSoup

io_encoding = 'utf-8'
sys.stdout.reconfigure(encoding=io_encoding)

FILES = [
    (r"D:\AI\ai-berkshire\.tmp_research\bing_eve_consumer.html", "亿纬锂能 消费电池 客户 蓝牙 电子烟"),
    (r"D:\AI\ai-berkshire\.tmp_research\bing_eve_storage2025.html", "亿纬锂能 储能 出货量 2025 客户"),
    (r"D:\AI\ai-berkshire\.tmp_research\bing_eve_sungrow.html", "亿纬锂能 阳光电源 合作"),
    (r"D:\AI\ai-berkshire\.tmp_research\bing_eve_tesla.html", "亿纬锂能 特斯拉 合作"),
    (r"D:\AI\ai-berkshire\.tmp_research\bing_eve_xpeng.html", "亿纬锂能 小鹏 合作"),
    (r"D:\AI\ai-berkshire\.tmp_research\eve\bing_bmw.html", "亿纬锂能 宝马 合作"),
    (r"D:\AI\ai-berkshire\.tmp_research\eve\sogou_bmw.html", "亿纬锂能 宝马 合作 (Sogou)"),
]

def parse_bing(soup):
    """Parse Bing search results page structure."""
    results = []
    # Bing: each result is in <li class="b_algo">
    for li in soup.select('li.b_algo'):
        # title
        title_tag = li.select_one('h2 a')
        title = title_tag.get_text(strip=True) if title_tag else ""
        href = title_tag.get('href', '') if title_tag else ""
        # snippet: often .b_caption p or .b_factrow
        snippet_parts = []
        for p in li.select('.b_caption p, .b_caption .b_searchCaption, .b_dList, .b_caption'):
            txt = p.get_text(' ', strip=True)
            if txt and txt not in snippet_parts:
                snippet_parts.append(txt)
        snippet = ' | '.join(snippet_parts) if snippet_parts else ''
        results.append({'title': title, 'url': href, 'snippet': snippet})
    return results

def parse_sogou(soup):
    """Parse Sogou search results page structure."""
    results = []
    # Sogou: results in .vrwrap or .results .vr_title
    for item in soup.select('.vrwrap, .results > div'):
        title_tag = item.select_one('h3 a, .vr_title a, a.sogou_link')
        title = title_tag.get_text(strip=True) if title_tag else ""
        href = title_tag.get('href', '') if title_tag else ''
        snippet_parts = []
        for sel in ['.str_info', '.str-text-info', 'p.str_time_info', '.ftct', 'div[class*="text"]', 'p']:
            for p in item.select(sel):
                txt = p.get_text(' ', strip=True)
                if txt and txt not in snippet_parts and len(txt) > 20:
                    snippet_parts.append(txt)
        snippet = ' | '.join(snippet_parts[:3]) if snippet_parts else ''
        if title:
            results.append({'title': title, 'url': href, 'snippet': snippet})
    return results

KEYWORDS = ['亿纬', 'EVE', 'GWh', '300Wh', '固态', '钠离子', '钠电', 'LMFP',
            '46系列', '大圆柱', '消费', '储能', '动力', '三元', '磷酸铁锂',
            '能量密度', '产能', '量产', '客户', '特斯拉', '宝马', '小鹏', '阳光',
            '电子烟', '蓝牙', '锂原', '李群', '4680', '4695', '46120',
            '专利', '研发', 'Mr.battery', 'Mr.Big', '飞行电池', '硅基']

def extract_keyword_context(text):
    """Find sentences containing key technical terms."""
    if not text:
        return []
    # Split by Chinese punctuation
    sentences = re.split(r'[。.;；！!？?\n]+', text)
    hits = []
    for s in sentences:
        s = s.strip()
        if 10 < len(s) < 400:
            for kw in KEYWORDS:
                if kw in s:
                    hits.append(s)
                    break
    return hits

for path, query in FILES:
    print("\n" + "="*100)
    print(f"# FILE: {os.path.basename(path)}  | SEARCH QUERY: {query}")
    print(f"# PATH: {path}")
    print("="*100)
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            html = f.read()
    except Exception as e:
        print(f"[ERROR reading file]: {e}")
        continue

    soup = BeautifulSoup(html, 'html.parser')
    # Remove script/style noise
    for s in soup(['script', 'style', 'noscript']):
        s.decompose()

    is_sogou = 'sogou' in path.lower() or '搜狗' in html[:5000]
    results = parse_sogou(soup) if is_sogou else parse_bing(soup)

    print(f"\n[Found {len(results)} results]\n")
    for i, r in enumerate(results, 1):
        print(f"--- Result #{i} ---")
        print(f"TITLE: {r['title']}")
        print(f"URL  : {r['url']}")
        if r['snippet']:
            print(f"SNIP : {r['snippet'][:1500]}")
        # extract keyword-bearing sentences
        full_text = r['title'] + " " + r['snippet']
        hits = extract_keyword_context(full_text)
        if hits:
            print(f"KEY TECH SENTENCES:")
            for h in hits[:8]:
                print(f"  - {h}")
        print()
