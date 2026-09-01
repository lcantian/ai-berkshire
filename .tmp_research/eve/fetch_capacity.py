#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Fetch EVE Energy (300014) capacity data via local Clash proxy 7897."""
import re, os, subprocess, html, time, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = r'D:\AI\ai-berkshire\.tmp_research\eve'
os.makedirs(BASE + r'\cap', exist_ok=True)
SUMMARY = open(BASE + r'\cap_summary.txt', 'w', encoding='utf-8')

PROXY = 'http://127.0.0.1:7897'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'

# Direct URLs (no search engine redirect) -- capacity, annual report, segments
LINKS = [
    # 1. Eastmoney main business by product (按产品) - new API
    ('em_product_2024', 'https://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/MainBusinessAjax?type=2&code=SZ300014'),
    ('em_product_2025', 'https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_F10_MAIN_BUSINESS&columns=ALL&filter=(SECUCODE=%22300014.SZ%22)(REPORT_TYPE=%22按产品%22)&pageNumber=1&pageSize=20&sortTypes=-1&sortFields=REPORT_DATE'),
    # 2. Eastmoney - by region
    ('em_region', 'https://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/MainBusinessAjax?type=3&code=SZ300014'),
    # 3. cninfo (巨潮) fulltext search for 300014 annual reports
    ('cninfo_search', 'https://www.cninfo.com.cn/new/fulltextSearch/full?searchkey=300014&sdate=2024-01-01&edate=2026-12-31&isfulltext=true&sortName=pubdate&sortType=desc&pageNum=1'),
    # 4. sohu/eastmoney article on EVE capacity 2025
    ('eve_capacity_2025', 'https://www.sohu.com/a/800000000_121124376'),
    # 5. EVE investor page
    ('eve_investor', 'https://www.evebattery.com/investor/'),
    # 6. EVE about
    ('eve_about', 'https://www.evebattery.com/about-us/company-profile.html'),
    # 7. 36kr / cls capacity summary
    ('cls_capacity', 'https://www.cls.cn/detail/800000'),
    # 8. 高工锂电 GGII report on EVE
    ('ggli_eve', 'https://www.gg-lb.com/articeinfo.php?article_id=45000'),
    # 9. battery.com.cn
    ('battery_china_eve', 'https://www.battery.com.cn/eve-capacity-2025.html'),
    # 10. xueqiu analysis
    ('xueqiu_eve_capacity', 'https://xueqiu.com/S/SZ300014'),
    # 11. Sina finance EVE report 2025 annual
    ('sina_eve_2025', 'https://finance.sina.com.cn/realstock/company/sz300014/nc.shtml'),
    # 12. EVE 2024 annual report PDF on cninfo
    ('cninfo_pdf_2024', 'http://static.cninfo.com.cn/finalpage/2025-03-28/1219326066.PDF'),  # placeholder may 404
    # 13. baidu article - Mr.Big 628Ah
    ('mr_big_628', 'https://baijiahao.baidu.com/s?id=1800000000000000000'),
    # 14. 储能国际峰会 / CES
    ('ces_eve_storage', 'https://www.ces.cn/eve-storage-2025.html'),
    # 15. eastmoney article - 亿纬锂能2024年产能
    ('em_eve_cap', 'https://finance.eastmoney.com/a/202503283300000000.html'),
]

def strip_tags(s):
    s = re.sub(r'<script[^>]*>.*?</script>', '', s, flags=re.S)
    s = re.sub(r'<style[^>]*>.*?</style>', '', s, flags=re.S)
    s = re.sub(r'<[^>]+>', ' ', s)
    s = html.unescape(s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def fetch(name, url):
    out = f'{BASE}\\cap\\{name}.html'
    cmd = ['curl', '-sL', '-m', '40', '-x', PROXY, '-A', UA,
           '-H', 'Accept-Language: zh-CN,zh;q=0.9',
           '-H', 'Accept: text/html,application/xhtml+xml,application/json,*/*;q=0.8',
           url, '-o', out, '-w', '%{http_code}|%{size_download}|%{url_effective}']
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        info = r.stdout.strip()
    except Exception as e:
        SUMMARY.write(f'\n[{name}] EXCEPTION: {e}\n')
        return
    if not os.path.exists(out):
        SUMMARY.write(f'\n[{name}] FAIL no file: {info}\n')
        return
    raw = open(out, 'rb').read()
    # try utf-8 first, fallback to gb18030
    text = None
    for enc in ['utf-8', 'gb18030', 'gbk']:
        try:
            data = raw.decode(enc)
            text = data
            # check meta charset
            enc_m = re.search(r'charset=["\']?([\w-]+)', data[:2000], re.I)
            if enc_m and enc_m.group(1).lower() not in ('utf-8', 'utf8') and enc_m.group(1).lower() in ('gb2312', 'gbk', 'gb18030'):
                try:
                    data = raw.decode(enc_m.group(1))
                    text = data
                except:
                    pass
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        text = raw.decode('utf-8', errors='ignore')
    is_json = url.endswith(('MainBusinessAjax',)) or 'datacenter.eastmoney.com' in url or 'api/data' in url
    if is_json or text.lstrip().startswith('{'):
        SUMMARY.write(f'\n===== [{name}] JSON =====\nURL: {url}\nInfo: {info}\n')
        try:
            j = json.loads(text)
            SUMMARY.write(json.dumps(j, ensure_ascii=False, indent=2)[:10000])
        except Exception:
            SUMMARY.write(text[:10000])
    else:
        t = strip_tags(text)
        SUMMARY.write(f'\n===== [{name}] HTML txt={len(t)} =====\nURL: {url}\nInfo: {info}\n')
        SUMMARY.write(t[:10000])
    SUMMARY.write('\n' + '-'*80 + '\n')
    SUMMARY.flush()

for name, link in LINKS:
    print(f'Fetching {name}...', flush=True)
    fetch(name, link)
    time.sleep(1.0)

SUMMARY.close()
print('Done')
