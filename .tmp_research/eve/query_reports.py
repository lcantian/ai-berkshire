#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Query cninfo for EVE annual and interim reports, then fetch PDFs."""
import re, os, subprocess, time, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = r'D:\AI\ai-berkshire\.tmp_research\eve'
os.makedirs(BASE + r'\reports', exist_ok=True)
SUMMARY = open(BASE + r'\reports_summary.txt', 'w', encoding='utf-8')

PROXY = 'http://127.0.0.1:7897'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'

# cninfo announcement query API (POST form)
# Categories: category=category_ndbg_szsh (annual), category_bndbg_szsh (interim)
def cninfo_query(category, start_date, end_date, page=1):
    """Returns JSON of announcements."""
    url = 'http://www.cninfo.com.cn/new/hisAnnouncement/query'
    data = (
        f"pageNum={page}&pageSize=30&column=szse&tabName=fulltext"
        f"&plate=&stock=300014%2C9900008311"
        f"&searchkey=&secid=&category={category}"
        f"&trade=&seDate={start_date}~{end_date}"
        f"&sortName=&sortType=&isHLtitle=true"
    )
    out = f'{BASE}\\reports\\query_{category}_{page}.json'
    cmd = ['curl', '-sL', '-m', '40', '-x', PROXY, '-A', UA,
           '-H', 'Content-Type: application/x-www-form-urlencoded',
           '-H', 'Accept: application/json,*/*;q=0.8',
           '-H', 'X-Requested-With: XMLHttpRequest',
           '-H', 'Referer: http://www.cninfo.com.cn/new/commonUrl?url=disclosure/list/notice',
           '-X', 'POST', '-d', data, url, '-o', out,
           '-w', '%{http_code}|%{size_download}']
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    info = r.stdout.strip()
    SUMMARY.write(f'\n[QUERY {category} p{page}] {info}\n')
    if os.path.exists(out):
        try:
            j = json.load(open(out, encoding='utf-8'))
            anns = j.get('announcements') or []
            for a in anns:
                title = a.get('announcementTitle','')
                t = a.get('announcementTime', 0)
                url2 = a.get('adjunctUrl', '')
                from datetime import datetime
                ts = datetime.fromtimestamp(t/1000).strftime('%Y-%m-%d') if t else '?'
                SUMMARY.write(f'  {ts} | {title} | {url2}\n')
            return j
        except Exception as e:
            SUMMARY.write(f'  PARSE ERR: {e}\n')
    return None

# Categories: annual reports
print('Querying annual reports...', flush=True)
cninfo_query('category_ndbg_szsh', '2023-01-01', '2026-12-31')
# Interim reports
print('Querying interim reports...', flush=True)
cninfo_query('category_bndbg_szsh', '2024-01-01', '2026-12-31')
# 季报
print('Querying Q1/Q3 reports...', flush=True)
cninfo_query('category_yjdbg_szsh', '2025-01-01', '2026-12-31')
cninfo_query('category_sjdbg_szsh', '2025-01-01', '2026-12-31')
# 调研纪要 investor research
print('Querying investor research...', flush=True)
cninfo_query('category_yjdbg_szsh', '2024-01-01', '2026-12-31')
# 全部含产能关键字
print('Querying capacity keyword...', flush=True)
cninfo_query('', '2025-01-01', '2026-12-31')  # placeholder

SUMMARY.flush()

# Now look at findings - print summary
print('\n=== SUMMARY ===', flush=True)
with open(f'{BASE}\\reports_summary.txt', encoding='utf-8') as f:
    print(f.read())
