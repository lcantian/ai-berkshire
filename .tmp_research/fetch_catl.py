#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Fetch real content of CATL 2026 H1 articles via baidu redirect."""
import re, os, subprocess, time, html

BASE = r'D:\AI\ai-berkshire\.tmp_research\catl_research'
os.makedirs(BASE + r'\articles', exist_ok=True)
SUMMARY = open(BASE + r'\articles_summary.txt', 'w', encoding='utf-8')

PROXY = 'http://127.0.0.1:7897'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'

# Key baidu links from search results (most informative titles)
LINKS = [
    # sina finance - 半年度报告摘要 official summary
    ('sina_summary', 'http://www.baidu.com/link?url=hTzuUbeAGYJDsuUIuHlbdc9f1QwTf4EWC5wzkm88jnDCX8HT8Km4Zb_Z_YqlOStdU3jIum6bYoYjIbL4mszv1v5GqkWCOieOzGG_Vxa7195xOJpqlE25ZwPbAv8r4dII'),
    # sina 半年度报告 03750 HK version
    ('sina_HK', 'http://www.baidu.com/link?url=3GQwut2xeYDXcJ2qwZl4UFjzO9eEhHgILqitTMSGbv3O8wznltX3fZLCNBZjaMcx6WfCgcpGWltQMp2bICJwq0XGfH9oGXchRxPcQle6g18E1FHhLd5LGku7t8DIU9bu'),
    # sina 半年度报告 300750 A version
    ('sina_A', 'http://www.baidu.com/link?url=e0foklF9XBFCJz-FCaHshmMfas53RPnNzhBv6mIV-yG6TgKw6wf2I1vBpLKc0--AHwMdUZdjriOPYJNOS-qvC5vbO7zYPUugZ0hm7juhxHyYlCgfiwK-e9UqhUrPnio9'),
    # 中报 分红 announcement
    ('sina_div', 'http://www.baidu.com/link?url=WUE_zR_gdZ95BpVv-HkOkFvTpXTyeqnT1y5iguZZoQCzWalJANQm59N3Fo1QfsY0fr_hqLcCbhh4UYfL4YC2v8GNMnxH5ivyBi-Pb-3U-y114PWAuafoKiFwSQa5z8zj'),
    # 关联交易 announcement
    ('sina_relate', 'http://www.baidu.com/link?url=xmugOGZxTGDEZYLy-ee9G5VUMyL-y94J-YS8u4eJb_Kh4Wv9JnkZKoOckJbTUHzzqjHKsyegwKyT5Ql3lPjEO2aQdE_F9IH22BIqPEqKoFI70CkZB46PKOaBmZDbhTur'),
    # 雪球深度分析 利润率
    ('xueqiu_analysis', 'http://www.baidu.com/link?url=ZrDxdmVWBp9W7iA550aGTKLR5GvbtFGcZcAr2XpSfEnohrRWcJy1wF41b7NkZ3wGHM_FpWsDeJRVclmUmYnx8q'),
    # eastmoney 高速增长
    ('eastmoney_growth', 'http://www.baidu.com/link?url=FJ9FR6xzlduB5U-3ky1Fwys5pq20x1p1oRamGL-v8jP90gQo7MeHtl_BuvAkN3PHMFovLy786rrW5kU79GVMGt9EH-plnvKgR8aGebfgJqu'),
    # 每小时吸金近千万 含研发投入
    ('hourly_revenue', 'http://www.baidu.com/link?url=zQq2ZHXnUBjl_0JzJEgYx8H_b-KBS1-6RupkxRatwc4V_ruk2sZlV4VE6D-TPELejOajYr0SXI3uKJTO9K1dW3YF7dCEX1uIcS0k97JAeGW'),
    # 宁王 储能大涨 动力电池毛利率下降
    ('ningwang_margin', 'http://www.baidu.com/link?url=05Mzt7o7r4iStNlX-QS5x_8zQFQkZ13QZLbiBtSJ4RZSdNLwW0wSpJwdHj4OjbufU-qkZw4ODUCFBeCifvLP0a'),
    # 图解中报 Q2单季
    ('tujie_Q2', 'http://www.baidu.com/link?url=jRhxMI5SJHMwuj2Fte2D34_O58KIYg4N7qR5cVJArbmslfY3_NQFGpZXCZ4K_EB9BkpXtSs1xNhQV1DnFNh-lJ_Hsvwi3xjU6_RQgTN24E7'),
    # A股史上最大回购
    ('buyback_400yi', 'http://www.baidu.com/link?url=r5O2I_hm8S7Q-8j-XnMo6zMZQHkc41xVWGTrAYHLhpvh04M6bI3ApHf1GIgQtuhRy3sP0aTOOipHapyDFLPM8Nyr6VkhxJhxOkRqbf4Z9Uq'),
    # 日赚2.3亿 还要募资390亿
    ('rima_390', 'http://www.baidu.com/link?url=1ZtzIoD6cjqIhNdj_jLRiGeEl0Ar7KGvfEM19ituy8JWiAFDU8M1jkMEGLqQq62OPRZnKST4VMFSU8WF6R96mc5y0Dshn36ENwSG_2EjC3km'),
    # 花旗 1TWh电池 1000亿利润
    ('citi_1TWh', 'http://www.baidu.com/link?url=nFnvAM7QNykrIrcuNpZeSul2nM6ALbhc2BUVEenNJlqzp6SUMw1a6_kaEpEGq8iIP-UAKD2uYnRY7wXfDdJaLr_XENrLquBsr1LNGePC9-m'),
    # 全球动力电池装车量TOP10
    ('top10_share', 'http://www.baidu.com/link?url=lqLAwkyHKWuQ8-sYtuAhAxSWsHMK_b-8x7a7qnner8FqX16d4FZp0sU1M5QaEQlajsdHfGmoOrT7oj2gQ5DCR7igSRRYUzwvvRvHKp6d2Z_'),
    # 越赚钱越缺钱 负债6520亿
    ('debt_6520', 'http://www.baidu.com/link?url=n_df9fhWRvUbnKIOuZFt2Z9hEjK33clc4F8x9-N5TYBUJuuLlAfB8d0tLx4PlterqH7UJbAd9_T1jLpisHudT7xOkmyVHMFgCLqlhpFkRAW'),
    # 继续给宁德打工 车企半年报
    ('carmakers', 'http://www.baidu.com/link?url=IFpcQ-lPR_YJUjIN4d7njXX-4huXCV5kXODG49kDvA2by_PXAD1TU4Ib89fL27PTZwZa8xwlsdh25Dp3T9EVpIdOCoUBZMSfhqL4E_F1a0aPYwPHbzVH3jWCUR6WWqGQ'),
    # 出口退税调整
    ('export_tax', 'http://www.baidu.com/link?url=Lyc1TvTPd2L7hSkEYXsXOoQLsbZTyjM5_rX2L3EPfnqRze43MxuzlbF6fTzKRfohVcWzpegFeYXGLSzkEDJvL_'),
    # 最大客户曝光
    ('max_customer', 'http://www.baidu.com/link?url=Gw6D9XZ6wq6aZITfScYlxL1nIYuZahffrVrle5wzLsRPECBWSlGnpqKd-taagf1CvXcdP3jLhg-oM53S_gSuIr2YTLiLL0QoffexrdX3bIIjKzGthlrCIGs0UGsOKJzD'),
]

def strip_tags(s):
    s = re.sub(r'<script[^>]*>.*?</script>', '', s, flags=re.S)
    s = re.sub(r'<style[^>]*>.*?</style>', '', s, flags=re.S)
    s = re.sub(r'<[^>]+>', ' ', s)
    s = html.unescape(s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def resolve_and_fetch(name, baidu_link):
    """Follow baidu redirect to get real URL, then fetch content."""
    out_html = f'{BASE}\\articles\\{name}.html'
    cmd = ['curl','-sIL','-m','30','-x',PROXY,'-A',UA,
           '-H','Accept-Language: zh-CN,zh;q=0.9',
           baidu_link]
    r = subprocess.run(cmd, capture_output=True, text=True)
    # extract final URL from headers
    final_url = baidu_link
    headers = r.stdout
    loc_m = re.findall(r'Location:\s*(https?://[^\s\r\n]+)', headers, re.I)
    if loc_m:
        final_url = loc_m[-1]
    # Now fetch actual content
    cmd2 = ['curl','-sL','-m','40','-x',PROXY,'-A',UA,
            '-H','Accept-Language: zh-CN,zh;q=0.9',
            '-H','Accept: text/html,application/xhtml+xml',
            final_url, '-o', out_html, '-w', '%{http_code}|%{size_download}|%{url_effective}']
    r2 = subprocess.run(cmd2, capture_output=True, text=True)
    info = r2.stdout.strip()
    if not os.path.exists(out_html):
        SUMMARY.write(f'\n[{name}] FAIL: {info}\n')
        return
    data = open(out_html, 'r', encoding='utf-8', errors='ignore').read()
    # detect encoding
    enc_m = re.search(r'charset=["\']?([\w-]+)', data, re.I)
    enc = enc_m.group(1) if enc_m else 'utf-8'
    if enc.lower() not in ('utf-8','utf8'):
        try:
            data = open(out_html, 'r', encoding=enc, errors='ignore').read()
        except:
            pass
    text = strip_tags(data)
    SUMMARY.write(f'\n===== [{name}] =====\n')
    SUMMARY.write(f'Final URL: {final_url}\n')
    SUMMARY.write(f'Info: {info}\n')
    SUMMARY.write(f'Text size: {len(text)}\n')
    SUMMARY.write(f'Content (truncated 12000):\n{text[:12000]}\n')
    SUMMARY.write('-'*80 + '\n')
    SUMMARY.flush()

for name, link in LINKS:
    print(f'Fetching {name}...')
    try:
        resolve_and_fetch(name, link)
    except Exception as e:
        SUMMARY.write(f'\n[{name}] EXCEPTION: {e}\n')
    time.sleep(1.5)

SUMMARY.close()
print('Done')
