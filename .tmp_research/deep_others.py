# -*- coding: utf-8 -*-
"""Deep extraction for sogou_news_bmw.html and sogou_eve_xpeng.html."""
import sys, re
from bs4 import BeautifulSoup
sys.stdout.reconfigure(encoding='utf-8')

paths = [
    r"D:\AI\ai-berkshire\.tmp_research\eve\sogou_news_bmw.html",
    r"D:\AI\ai-berkshire\.tmp_research\sogou_eve_xpeng.html",
]

kws = ['GWh', '亿纬', '大圆柱', '46系', '4680', '4695', '46120', '宝马', '奔驰',
       'Rimac', 'NeueKlasse', '小鹏', '储能', '动力', '消费', '电子烟', '蓝牙',
       '固态', '钠离子', 'LMFP', '磷酸铁锂', '三元', '产能', '量产', '定点',
       '配套', '装机', '亿元', '营收', '净利', '专利', '研发', '能量密度',
       'Wh/kg', '飞行', '低空', '汇天', '高镍', '全极耳', 'LG', '方形', '软包',
       'P7', 'P5', 'G3', 'G6', 'G9', '零跑', '江淮', 'SK', '比亚迪', '宁德',
       'Tier', '客户', '份额', '市占', '装机', '增速', '兆瓦', 'MWh', '欧洲',
       '匈牙利', '马来西亚', '硅基', 'Mr.Big']

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

    results = soup.select('.vrwrap')
    print(f"Found {len(results)} .vrwrap\n")
    for i, r in enumerate(results, 1):
        title_tag = r.select_one('h3 a, .vr_title a, a.sogou_link, h3')
        title = title_tag.get_text(' ', strip=True) if title_tag else ""
        href = ''
        if title_tag and title_tag.name == 'a':
            href = title_tag.get('href', '')
        elif title_tag and title_tag.find('a'):
            href = title_tag.find('a').get('href', '')

        snip_texts = []
        for sel in ['.str_info', '.str-text-info', '.str_text_info', '.str-time-info',
                    '.ftct', '.news-text', '.news-txt', '.summary', '.digest',
                    '.vr-desc', '.vr_desc', '.description']:
            for el in r.select(sel):
                t = el.get_text(' ', strip=True)
                if t and len(t) > 15 and t not in snip_texts:
                    snip_texts.append(t)
        # Fallback: get long text
        if not snip_texts:
            for el in r.find_all(['p', 'div', 'span']):
                t = el.get_text(' ', strip=True)
                if 25 < len(t) < 2000 and t not in snip_texts and t != title:
                    if not any(x in t for x in ['搜狗', '登录', '反馈', '下一页', '上一页']):
                        snip_texts.append(t)

        # Filter relevance
        full = title + " " + " ".join(snip_texts)
        if not any(kw in full for kw in ['亿纬', 'EVE', '宝马', '小鹏', '大圆柱', '动力电池', '储能', 'Mercedes', '奔驰']):
            continue

        print(f"--- #{i} ---")
        print(f"T: {title}")
        print(f"U: {href}")
        for j, t in enumerate(snip_texts[:4], 1):
            print(f"S{j}: {t[:1000]}")
        print()

    # Global text scan
    print("\n=== 关键句全文扫描 ===")
    full_text = soup.get_text(' ', strip=True)
    sentences = re.split(r'[。.；;！!？?\n\r]+', full_text)
    seen = set()
    for s in sentences:
        s = re.sub(r'\s+', ' ', s).strip()
        if 15 < len(s) < 600:
            for kw in kws:
                if kw in s and s not in seen:
                    seen.add(s)
                    print(f"* {s}")
                    break
