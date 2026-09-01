# -*- coding: utf-8 -*-
"""Extract full content from valid (non-censored) search result files."""
import sys, os, re
from bs4 import BeautifulSoup
sys.stdout.reconfigure(encoding='utf-8')

# Valid files to extract
files = [
    r"D:\AI\ai-berkshire\.tmp_research\eve\bing_bmw_en.html",
    r"D:\AI\ai-berkshire\.tmp_research\eve\so_bmw.html",
    r"D:\AI\ai-berkshire\.tmp_research\eve\sogou_bmw.html",
    r"D:\AI\ai-berkshire\.tmp_research\eve\sogou_news_bmw.html",
    r"D:\AI\ai-berkshire\.tmp_research\sogou_eve_xpeng.html",
]

KEYWORDS = ['亿纬', 'EVE', 'GWh', '300Wh', 'Wh/kg', '固态', '钠离子', '钠电', 'LMFP',
            '46系列', '大圆柱', '消费', '储能', '动力', '三元', '磷酸铁锂', '铁锂',
            '能量密度', '产能', '量产', '客户', '特斯拉', '宝马', '小鹏', '阳光',
            '电子烟', '蓝牙', '锂原', '4680', '4695', '46120', 'NeueKlasse',
            '专利', '研发', 'Mr.Big', 'Mr.battery', '飞行电池', '硅基', 'Tier',
            '定点', '配套', '供货', '中标', '兆瓦', 'MWh', '欧洲', '匈牙利',
            '马来西亚', '方形', '软包', 'hpcm', 'pulse', 'Tesla', 'Megapack',
            'Sungrow', '阳光电源', '储能系统', '亿纬动力', '亿纬储能']

def extract_keyword_sentences(text):
    if not text:
        return []
    sentences = re.split(r'[。.；;！!？?\n\r]+', text)
    hits = []
    seen = set()
    for s in sentences:
        s = re.sub(r'\s+', ' ', s).strip()
        if 10 < len(s) < 500:
            for kw in KEYWORDS:
                if kw in s:
                    if s not in seen:
                        seen.add(s)
                        hits.append(s)
                    break
    return hits

def parse_generic(soup):
    """Try multiple result container selectors."""
    results = []
    # Bing-style
    for li in soup.select('li.b_algo'):
        title_tag = li.select_one('h2 a')
        title = title_tag.get_text(strip=True) if title_tag else ""
        href = title_tag.get('href', '') if title_tag else ""
        snip_parts = []
        for p in li.select('.b_caption p, .b_caption'):
            txt = p.get_text(' ', strip=True)
            if txt and txt not in snip_parts:
                snip_parts.append(txt)
        results.append({'title': title, 'url': href, 'snippet': ' | '.join(snip_parts)[:2500]})

    # Sogou-style
    for item in soup.select('.vrwrap, .results > div, .news-item, li[class*="result"]'):
        title_tag = item.select_one('h3 a, .vr_title a, a.sogou_link, .news-title a, h4 a')
        title = title_tag.get_text(strip=True) if title_tag else ""
        href = title_tag.get('href', '') if title_tag else ''
        # Try multiple snippet selectors
        snip_parts = []
        for sel in ['.str_info', '.str-text-info', '.ftct', '.news-text', '.str_text_info',
                    '.str-time-info', 'p.str_info', 'div.str_info', 'p[class*="text"]',
                    '.summary', '.digest', '.news-txt']:
            for p in item.select(sel):
                txt = p.get_text(' ', strip=True)
                if txt and len(txt) > 15 and txt not in snip_parts:
                    snip_parts.append(txt)
        # fallback: all <p> with long text
        if not snip_parts:
            for p in item.find_all('p'):
                txt = p.get_text(' ', strip=True)
                if 30 < len(txt) < 1500 and txt not in snip_parts:
                    snip_parts.append(txt)
        if title:
            results.append({
                'title': title,
                'url': href,
                'snippet': ' | '.join(snip_parts)[:2500]
            })
    return results

for path in files:
    print("\n" + "="*100)
    print(f"# FILE: {path}")
    print("="*100)
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        html = f.read()
    soup = BeautifulSoup(html, 'html.parser')
    for s in soup(['script', 'style', 'noscript']):
        s.decompose()

    title = soup.title.get_text(strip=True) if soup.title else ""
    print(f"PAGE TITLE: {title}")
    print(f"PAGE URL hint: {soup.find('meta', property='og:url')}")

    results = parse_generic(soup)
    # Dedup by title
    seen_titles = set()
    deduped = []
    for r in results:
        t = r['title'][:50]
        if t not in seen_titles:
            seen_titles.add(t)
            deduped.append(r)
    print(f"\n[Found {len(deduped)} unique results]\n")

    for i, r in enumerate(deduped, 1):
        full = r['title'] + " " + r['snippet']
        if '亿纬' not in full and 'EVE' not in full and '宝马' not in full and '大圆柱' not in full and '小鹏' not in full:
            continue  # skip irrelevant
        print(f"--- #{i} ---")
        print(f"T: {r['title']}")
        print(f"U: {r['url']}")
        if r['snippet']:
            print(f"S: {r['snippet']}")
        hits = extract_keyword_sentences(full)
        if hits:
            print(f"KEY:")
            for h in hits[:10]:
                print(f"  * {h}")
        print()
