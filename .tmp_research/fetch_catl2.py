#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Round 2 fetch - the most informative articles."""
import re, os, subprocess, time, html

BASE = r'D:\AI\ai-berkshire\.tmp_research\catl_research'
SUMMARY = open(BASE + r'\articles2_summary.txt', 'w', encoding='utf-8')

PROXY = 'http://127.0.0.1:7897'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'

LINKS = [
    # 宁王回归 深度解读
    ('ningwang_return', 'http://www.baidu.com/link?url=6PJgnaJdKKX-AbX65iJLXPQT_EXEvjiKNQaIK-6kaG9_08g4Z3mm7XhgK2JkbsKlz3FUgZ5lmaD_S2RcA2F4b_'),
    # 2026上半年净利润432.84亿元增41.98% 储能业务增长87.54% (新浪)
    ('sina_8754', 'http://www.baidu.com/link?url=2CANJlB2n-nIutASwOYPCV9usPF09u3__EYXnEw9sRZVQvPs-71jVqaPeTKwKOqG5EL6zmcnQba6Iz8x6kt0SJ0ng60QnggJWKKgIXrgywq'),
    # 储能翻倍 商用车提速 AIDC卡位
    ('aidc_storage', 'http://www.baidu.com/link?url=uckNTDXfOzK1EEpUxnmJCtebp5HfTx3NP0cNf_MhRqr1674FX1BrNeYtvqFRNXwGiqTjGbgdZYC6t7Lnlw01MEfqLgBviPwAJJWpiAt3mLO'),
    # 财报解读 财务费用激增89.17% 汇率
    ('forex_8917', 'http://www.baidu.com/link?url=H42gqX5SfMMwXfGFId6_PiEAKm9xXDe1ztileM88f53E8g5fqz2oqhX0fj0Rc9rFXpe-uxn-kqXM13usUYAsSAUBX5KE3CPs8oZgEtAXTqu'),
    # 毛利率下滑 欠账3千亿 固态电池未见影
    ('maoshang_3000', 'http://www.baidu.com/link?url=q2uy0KtJ0955zMGvuz0SY2BuhROvrrbgSgLiwwwUZTNhBxYesDLGCK9xWeP08dOtdStwXyBxoejxBhOXCucDf1UIvy1cRo3wyfCoKBot9W7'),
    # 逾6000亿负债悬顶
    ('debt_6000', 'http://www.baidu.com/link?url=-56r4dXoUfME89tbV-SLAlo7Z6gsr79NRYiTXqiWNP21lKmKAR_gHcaCQ4p5V6-ek26zclzM_QZGl9wrVdgKSBIUgb4tbPRlkxZsarppCqu'),
    # 半年报 逆势高增
    ('nishigaozeng', 'http://www.baidu.com/link?url=eb-S6BU7jKeJTZpX2dO_2b5jZfVnJo21wVDTldHdnuLZXBSvYVcRbATkUeHlEwkVvksHZgMknDHl-HjH14Jb7xFxk8NufDy6cOViQKv96CS'),
    # 上半年营收2769亿 净利433亿 派息65亿曾毓群3960亿
    ('paixi_65', 'http://www.baidu.com/link?url=eb-S6BU7jKeJTZpX2dO_2b5jZfVnJo21wVDTldHdnuMzgtMD5HrFAkbCXIk_oM-gdlgdocl6nkh68d_jkzQfSCJ7GgyKao4lptMP0zFDZcm'),
    # 财报速递 净利润 432.84
    ('caibao_sudi', 'http://www.baidu.com/link?url=6qO4JdIdzz4PRiNvfAhOJ4BunOEgdF4XwBSaoEm-Ant11dBLjWVim1SWhPTg_opj2bHGzCFdQNZVJJHTgOs0i9db5yD4qYRFYl7TBo8GBgS'),
    # 收款2个月付账大半年
    ('shoukuan_2m', 'http://www.baidu.com/link?url=ewu5D0pcBoA7fcu08rxf_eoTrqUZJZpnRSpHm9Alkxt-CNxWXzGFkh4pD9xFW9Qqi9D2Tr736pBYnL-zNoAQOOSDwokrg6H4m4AUN6k2Z4O'),
    # 上半年净利增42% 拟每10股派14.11元
    ('sina_div_1411', 'http://www.baidu.com/link?url=H42gqX5SfMMwXfGFId6_PpJLTVPCgzfQsng1ZgFknZt6O7WffWhBYlcPDNNNkf3nUMy-iho-i41VinRtikQ2E_'),
    # 每小时吸金近千万 研发投入处在
    ('hourly_rnd', 'http://www.baidu.com/link?url=zQq2ZHXnUBjl_0JzJEgYx8H_b-KBS1-6RupkxRatwc4V_ruk2sZlV4VE6D-TPELejOajYr0SXI3uKJTO9K1dW3YF7dCEX1uIcS0k97JAeGW'),
    # 日均狂赚2.39亿 史上最强中报
    ('shishang_zqiang', 'http://www.baidu.com/link?url=irRgDQlka0NRuFZpKzwPk5l5rOGkDhC760VwORXQ1Gu00lghQtx60DJ92TfSdrs17rs2Ad4ks3fEYtZMHfbsoebb87aHh973emnckK__Oze'),
    # 投300亿重金 海外突围
    ('overseas_300', 'http://www.baidu.com/link?url=8US73or-iJTNTD-uj-cCB2-nW4G27XHpIluaSr7uMZTSKWTK3StJrjalInKjFD123Ti_crwscVdZudRVrvq3Qq'),
    # 手握4123亿现金 海外建厂
    ('cash_4123', 'http://www.baidu.com/link?url=TEdsQNy0M5beZ4MiFKCer6WI0HHoodeMf2uJX1fMPw_I9NhGC3aKfh_1DsqjnDwl2irgqZKCrRxaHW67PBXWUieBjD9qIKYdMKqMkMbu2xG'),
    # 募集资金使用情况
    ('mujizi_use', 'http://www.baidu.com/link?url=dPFFzhKrLhY7zvgOO8cZ9DpK9-7KLaFZyIkQrr1fWjE28NgUmz-__0_AnUc6_JBPOIEqarWEDrd4kJ80gnYk0rgHltDQ468sFTNzOJbJJHO'),
    # 关联交易 135.9亿
    ('relate_1359', 'http://www.baidu.com/link?url=_Yy2NZqOVD8__CDOjb5ztdeU4o3vhV2kxyhyYx8PwjRqQuH-NjHz5l8VEBTW59_X'),
    # 关联交易公告
    ('relate_announce', 'http://www.baidu.com/link?url=xmugOGZxTGDEZYLy-ee9GuVk_4soYjeFqBrRpxXqHlZzqBki-VnLGIs_cIdMNeRB'),
    # 中报摘要 新浪
    ('zhaiyao_em', 'http://www.baidu.com/link?url=qvIsdMU46GJck1Lk3U2Fr4LiIoyiETOhdM6I1pUUd7HpWL8RDJ-9eOGBvI6BAmWwy9YsZlO_zPC7aKyUzErUxcSSrP9hpCzZ2QViGAv4eA4zOqhYonGoBbQowyOTkoQg'),
    # 上半年净利同比增42%至432.8亿
    ('xini_42', 'http://www.baidu.com/link?url=6qO4JdIdzz4PRiNvfAhOJ4lFoI4WvtMaoZYyKMi1E-x2jdYhSvKHOVIRsBugV973qXyq6gienHDEsrGb1U16oFD9QRVi98yxEyFoCrhiYjGUw6jRR2vKtp2DC0EyjGjk'),
]

def strip_tags(s):
    s = re.sub(r'<script[^>]*>.*?</script>', '', s, flags=re.S)
    s = re.sub(r'<style[^>]*>.*?</style>', '', s, flags=re.S)
    s = re.sub(r'<[^>]+>', ' ', s)
    s = html.unescape(s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def resolve_and_fetch(name, baidu_link):
    out_html = f'{BASE}\\articles2\\{name}.html'
    os.makedirs(os.path.dirname(out_html), exist_ok=True)
    cmd = ['curl','-sIL','-m','30','-x',PROXY,'-A',UA,
           '-H','Accept-Language: zh-CN,zh;q=0.9',
           baidu_link]
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
    SUMMARY.write(f'Content (truncated 18000):\n{text[:18000]}\n')
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
