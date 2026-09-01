# -*- coding: utf-8 -*-
"""Deep extraction for sogou_bmw.html - find all text snippets including hidden ones."""
import sys, re
from bs4 import BeautifulSoup
sys.stdout.reconfigure(encoding='utf-8')

path = r"D:\AI\ai-berkshire\.tmp_research\eve\sogou_bmw.html"
with open(path, 'r', encoding='utf-8', errors='ignore') as f:
    html = f.read()
soup = BeautifulSoup(html, 'html.parser')
for s in soup(['script', 'style', 'noscript']):
    s.decompose()

# Find all result-like structures - vrwrap is Sogou's main result wrapper
results = soup.select('.vrwrap')
print(f"Found {len(results)} .vrwrap result wrappers\n")

for i, r in enumerate(results, 1):
    print(f"=== Result #{i} ===")
    # Title - try multiple
    title_tag = r.select_one('h3 a, .vr_title a, a.sogou_link, h3')
    title = title_tag.get_text(' ', strip=True) if title_tag else ""
    href = ''
    if title_tag and title_tag.name == 'a':
        href = title_tag.get('href', '')
    elif title_tag and title_tag.find('a'):
        href = title_tag.find('a').get('href', '')
    print(f"TITLE: {title}")
    print(f"HREF  : {href}")

    # Snippet - try MANY selectors
    snip_texts = []
    for sel in ['.str_info', '.str-text-info', '.str_text_info', '.str-time-info',
                '.ftct', '.news-text', '.news-txt', '.summary', '.digest',
                '.vr-desc', '.vr_desc', '.description', '.text', '.txt',
                'p.str_info', 'div[class*="info"]', 'p[class*="desc"]',
                'span[class*="desc"]', '.vr_bottom', '.vrbot']:
        for el in r.select(sel):
            t = el.get_text(' ', strip=True)
            if t and len(t) > 15 and t not in snip_texts:
                snip_texts.append(t)

    # If still nothing, get ALL long text from result
    if not snip_texts:
        for el in r.find_all(['p', 'div', 'span']):
            t = el.get_text(' ', strip=True)
            if 25 < len(t) < 2000 and t not in snip_texts and t != title:
                # Filter out navigational junk
                if not any(x in t for x in ['搜狗', '登录', '反馈', '相关搜索', '下一页', '上一页']):
                    snip_texts.append(t)

    # Source/time info
    time_tag = r.select_one('.str_time_info, .str-time-info, .news-source, .source, .time')
    if time_tag:
        print(f"TIME/SRC: {time_tag.get_text(' ', strip=True)}")

    for j, t in enumerate(snip_texts[:5], 1):
        print(f"SNIP{j}: {t[:800]}")
    print()

# Also extract "related searches" if any
print("\n=== Related searches / 全文搜 ===")
full = soup.get_text(' ', strip=True)
# Find sentences with EVE keywords
kws = ['GWh', '亿纬', '大圆柱', '46系', '4680', '4695', '46120', '宝马', '奔驰',
       'Rimac', 'NeueKlasse', '小鹏', '储能', '动力', '消费', '电子烟', '蓝牙',
       '固态', '钠离子', 'LMFP', '磷酸铁锂', '三元', '产能', '量产', '定点',
       '配套', '装机', '亿元', '营收', '净利', '专利', '研发', '能量密度',
       'Wh/kg', '飞行', '低空', '汇天']
sentences = re.split(r'[。.；;！!？?\n\r]+', full)
seen = set()
for s in sentences:
    s = re.sub(r'\s+', ' ', s).strip()
    if 15 < len(s) < 600:
        for kw in kws:
            if kw in s and s not in seen:
                seen.add(s)
                print(f"* {s}")
                break
