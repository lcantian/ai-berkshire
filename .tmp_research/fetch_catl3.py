#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Round 3 fetch - deep financial details."""
import re, os, subprocess, time, html

BASE = r'D:\AI\ai-berkshire\.tmp_research\catl_research'
SUMMARY = open(BASE + r'\articles3_summary.txt', 'w', encoding='utf-8')

PROXY = 'http://127.0.0.1:7897'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'

LINKS = [
    # 储能业务增长87.54% - 关键分业务文章 (新浪)
    ('sina_8754_v2', 'http://www.baidu.com/link?url=Qu7y2jgiAI9AaoQL62nXDoe0mqa9UC_k_1WayfkRA-OJvLLTIwTc3OBhkv5aWo408XRVvCp_7u1OhWtvhCW5BTmaQEy-HAAYUeHWAPDIgFm'),
    # 半年净赚超432亿 储能营收狂飙87% (eastmoney)
    ('em_storage_87', 'http://www.baidu.com/link?url=6x_QzS4phCsHhEJBbEDdRHPL53flP-K4KUR0urLJ5bYWUss2mrai97PnU5g9AxWJWsWKeh0YQUTDYG-d97uwbCyiQK0hFiAo7zR-IsblpWK'),
    # 上半年业绩亮眼 储能业务成增长新引擎
    ('engine_storage', 'http://www.baidu.com/link?url=UBUPVm1pFqNVCDJ66RWWPHmubdYBfx4ffhuTqX5KH8HZPl80H0iiEKtjofb073woIweR7MRJ5wZXzdvhZYoXp561QbOrxLU5H6rYTBwjwDa'),
    # 半年432亿 中国车企一半利润
    ('half_cheyi', 'http://www.baidu.com/link?url=Jd8_t9hjedFnEpvkIB6XyuRTCO_9_TJer9fsTx_qI_uvykf84FyhkBw0bV21cAYRovQcL77cWRB4Z5i6RRjXKWSY-gU5yknSOTDZfHC7ala'),
    # 谁在逃离宁德时代
    ('who_escape', 'http://www.baidu.com/link?url=8lNbtnsxgf8Sotq4256AeD7Xp6nhqdWsTAKh8hhuTNrh9AKihs-25pUwGq68HJduL4_hmodvOAFdI8sVw5hOb6HgwzB8ErYFjbJchDEjGhK'),
    # 全球储能龙头估值锚20到30倍
    ('anchor_30x', 'http://www.baidu.com/link?url=kJBR4Z0yfXtI__TNTff2wH8RQ_Y0HRTgx6LGfH3k5wAWzEEcrsry7gyo_GDmk1P6ZrZsl-EbgKp7JuQXgGzaDH5I8sWF5-tCPRBB2rVpFG3'),
    # 王者归来还是回光返照 市占率50%
    ('wangzhe_50', 'http://www.baidu.com/link?url=tcl1Ew2ifeo2QwG1y2Dt57NhqP3mdG8kxy8SoZqCkTLNIfEWH0NoDDI8ptyIthCbTHaZReal0xiOh9oI7aV8sK'),
    # 每小时吸金近千万 研发投入
    ('hourly_rnd_v2', 'http://www.baidu.com/link?url=8lNbtnsxgf8Sotq4256AeD7Xp6nhqdWsTAKh8hhuTNsvtk83lROCBr75gHJ_iBetVP-pJKeJ56DNQ9lwmadwFdlboo5riSZausqTM1FWKUG'),
    # 宁王Q2净利创新高 锂矿难题
    ('q2_kuang', 'http://www.baidu.com/link?url=jRhxMI5SJHMwuj2Fte2D34_O58KIYg4N7qR5cVJArboZzwCIhiEs7haVbme-ygITTbR3MSZ3nz99C7s-SOzqYbWR2PmS44umPvgVCikDlny'),
    # 财报解读 财务费用激增89.17% 汇率
    ('forex_v2', 'http://www.baidu.com/link?url=LSLAAlwc_P1JtituIXD55iQC6qzXT31D4IhUGg3eaFiTdcMLV3ltdqTH1mslSzvEgzXSeAmm5axoeJnAOJMdVchvCA62GB6RoPfceaf_xtG'),
    # 资产负债表 前瞻眼
    ('balance_qianzhan', 'http://www.baidu.com/link?url=SreJrpuqHbmD_1PjFII8G8itlVhjJOZvtR0mIr3Ld4n6U8sxaF65feVCaWRq8JzKJayCLHLQHE2p8NwGQdS5OhJL5V1Or_5XtaEp1GADhr7'),
    # 资产负债率上升
    ('debtratio_up', 'http://www.baidu.com/link?url=hTzuUbeAGYJDsuUIuHlbdoqWtQMU3xk1Nn6OzZYI9mOR_A8smf4zftA4SzHsozoDtLfctct3atMETEMvRKamL5xsZiz2lP9cKL-vWcR0Bme'),
    # 越赚钱越缺钱 负债6520亿
    ('more_less', 'http://www.baidu.com/link?url=n_df9fhWRvUbnKIOuZFt2Z9hEjK33clc4F8x9-N5TYBUJuuLlAfB8d0tLx4PlterqH7UJbAd9_T1jLpisHudT7xOkmyVHMFgCLqlhpFkRAW'),
    # 6000亿负债悬顶
    ('debt6000_v2', 'http://www.baidu.com/link?url=-56r4dXoUfME89tbV-SLAlo7Z6gsr79NRYiTXqiWNP21lKmKAR_gHcaCQ4p5V6-ek26zclzM_QZGl9wrVdgKSBIUgb4tbPRlkxZsarppCqu'),
    # 日赚2.4亿 产能再扩1.5倍
    ('capa_15x', 'http://www.baidu.com/link?url=jsHwYxt_8VLhdl7vB7adfTqf6ftheINQl0IX3kJ4SrQbee7f3od4y2kW3mvmGocUwKJfNgfXKpOOfamOjnlbFldLao8C-P7xvULPVdF1bb_'),
    # 上半年营收2769亿 同花顺
    ('THS_2769', 'http://www.baidu.com/link?url=e-5dhN7_2he_oNCmFKvbURHYuXoEuvnkj9qmsEfN_gw4nqg4Vi-T-VfWWGHAys5pyKe7Fu4IdJjibz2qEPcwqASHvGR610uQ6jQyS_WPFyS'),
    # H股配售 628.20港元 391亿
    ('H_391', 'http://www.baidu.com/link?url=e-5dhN7_2he_oNCmFKvbURHYuXoEuvnkj9qmsEfN_gvqTc-SVv89PuubC92vKePM4oLvjJOMsjxP4S_Qi_jPuJX2HG-14lY9uiZpvSYI1tm'),
    # 业绩超预期 龙头份额再提升
    ('beat_share', 'http://www.baidu.com/link?url=-vUj9k9gr8h_O_HmUtHwqFJq60X479H4FeNkZ624_meIBqHY5DjlTgda0JY1Tae8uONyCxkkWGGBoU4HP4xblNrNWGdn8x8hsJs9HbZbh6iR3sqKPnzeJJKMEC2Y4nlc'),
    # 净筹391.23亿港元
    ('net391', 'http://www.baidu.com/link?url=e-5dhN7_2he_oNCmFKvbURHYuXoEuvnkj9qmsEfN_guQOm1jX3ln9Cehk2KehZdLUu1gqkbdcPIYDMF17TuMiCIysaXyQo94-fzobLxmrr7'),
    # 一季报 筹资现金流暴增1149%
    ('q1_financing', 'http://www.baidu.com/link?url=Apjjp9IjUuH10lV_t52JJgumdJmUq9d92pwYXXpPIr4BKgE0O5NJhKq0N15WRs79vZPglf4GY4IVROKvuBj0QhNwexgqXagEbOVly1vO6-i'),
    # 2025年报摘要
    ('AR_2025_summary', 'http://www.baidu.com/link?url=RmBg0PkTotMcQ8YZ-6_Hwc2ADCEfHqSNo6ILV20eG3E1ZsBCMo209FA9AsVhqBpaJH8fTqB-9K4_cgi4bT9yAN97hqkeb1w2EpEoaM-pO2tRFT39swifAJ9esLZJZxPP'),
    # 中报摘要 sina
    ('zhaiyao_sina', 'http://www.baidu.com/link?url=dfNshdqEiXbaRW5CStsemZ_ffoXXojH261aegb5Dd9x72FbjcU0dRTiDIkdtLM83enIWd1E8OUItV-Es8W95KTAtTHSMz7Kbcsz7V3-0UCBShaiH_5xG8w86HXR53XXC'),
    # 全球储能龙头 卡位AIDC
    ('aidc_global', 'http://www.baidu.com/link?url=uckNTDXfOzK1EEpUxnmJCtebp5HfTx3NP0cNf_MhRqr1674FX1BrNeYtvqFRNXwGiqTjGbgdZYC6t7Lnlw01MEfqLgBviPwAJJWpiAt3mLO'),
]

def strip_tags(s):
    s = re.sub(r'<script[^>]*>.*?</script>', '', s, flags=re.S)
    s = re.sub(r'<style[^>]*>.*?</style>', '', s, flags=re.S)
    s = re.sub(r'<[^>]+>', ' ', s)
    s = html.unescape(s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def resolve_and_fetch(name, baidu_link):
    out_html = f'{BASE}\\articles3\\{name}.html'
    os.makedirs(os.path.dirname(out_html), exist_ok=True)
    cmd = ['curl','-sIL','-m','30','-x',PROXY,'-A',UA,
           '-H','Accept-Language: zh-CN,zh;q=0.9', baidu_link]
    r = subprocess.run(cmd, capture_output=True, text=True)
    final_url = baidu_link
    loc_m = re.findall(r'Location:\s*(https?://[^\s\r\n]+)', r.stdout, re.I)
    if loc_m:
        final_url = loc_m[-1]
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
    SUMMARY.write(f'Content (truncated 20000):\n{text[:20000]}\n')
    SUMMARY.write('-'*80 + '\n')
    SUMMARY.flush()

for name, link in LINKS:
    print(f'Fetching {name}...')
    try:
        resolve_and_fetch(name, link)
    except Exception as e:
        SUMMARY.write(f'\n[{name}] EXCEPTION: {e}\n')
    time.sleep(1.2)

SUMMARY.close()
print('Done')
