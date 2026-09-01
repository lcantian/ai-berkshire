# -*- coding: utf-8 -*-
"""Deep extraction for 360 search and Bing English BMW file."""
import sys, re
from bs4 import BeautifulSoup
sys.stdout.reconfigure(encoding='utf-8')

paths = [
    r"D:\AI\ai-berkshire\.tmp_research\eve\so_bmw.html",
    r"D:\AI\ai-berkshire\.tmp_research\eve\bing_bmw_en.html",
]

kws = ['GWh', '亿纬', 'EVE', '大圆柱', '46系', '4680', '4695', '46120', 'BMW', '宝马',
       'Rimac', 'NeueKlasse', 'Mercedes', '奔驰', '储能', '动力', '消费', '电子烟',
       '固态', '钠离子', 'LMFP', '磷酸铁锂', '三元', '产能', '量产', '定点',
       '配套', '装机', 'Wh/kg', '能量密度', '高镍', '全极耳', 'LG', '专利',
       ' Hungary', '匈牙利', 'malaysia', '马来西亚', 'cell', 'cylindrical']

for path in paths:
    print("\n" + "#"*100)
    print(f"# FILE: {path}")
    print("#"*100)
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        html = f.read()
    soup = BeautifulSoup(html, 'html.parser')
    for s in soup(['script', 'style', 'noscript']):
        s.decompose()
    print(f"PAGE TITLE: {soup.title.get_text(strip=True) if soup.title else ''}")

    # 360 uses different structure - try .result, .res-list, li
    results = soup.select('.result, .res-list, .res_item, li.res, .news-item, .vrwrap, li.b_algo')
    print(f"Found {len(results)} result items\n")
    for i, r in enumerate(results, 1):
        title_tag = r.select_one('h3 a, h2 a, .title a, a.title, .vr_title a')
        title = title_tag.get_text(' ', strip=True) if title_tag else ""
        href = title_tag.get('href', '') if title_tag else ''
        snip = []
        for sel in ['.res-desc, .desc, .summary, .digest, .text, p, .str_info, .ftct, .b_caption p']:
            for el in r.select(sel):
                t = el.get_text(' ', strip=True)
                if t and 20 < len(t) < 2000 and t not in snip:
                    snip.append(t)
        full = title + " " + " ".join(snip)
        if not any(kw in full for kw in ['亿纬', 'EVE', 'BMW', '宝马', '大圆柱', '46']):
            continue
        print(f"--- #{i} ---")
        print(f"T: {title[:200]}")
        print(f"U: {href}")
        for j, t in enumerate(snip[:3], 1):
            print(f"S{j}: {t[:800]}")
        print()

    # Global scan
    print("\n=== 关键句全文扫描 ===")
    full_text = soup.get_text(' ', strip=True)
    sentences = re.split(r'[。.；;！!？?\n\r]+', full_text)
    seen = set()
    for s in sentences:
        s = re.sub(r'\s+', ' ', s).strip()
        if 15 < len(s) < 500:
            for kw in kws:
                if kw in s and s not in seen:
                    seen.add(s)
                    print(f"* {s}")
                    break
