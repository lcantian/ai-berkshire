#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Round 4 fetch - final details."""
import re, os, subprocess, time, html

BASE = r'D:\AI\ai-berkshire\.tmp_research\catl_research'
SUMMARY = open(BASE + r'\articles4_summary.txt', 'w', encoding='utf-8')

PROXY = 'http://127.0.0.1:7897'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'

LINKS = [
    # 中报深度复盘及2026-2027业绩前瞻
    ('deep_replay', 'http://www.baidu.com/link?url=G-XigyVhiw6LYW9nSf6XhuL4FPcBRIfDdKNHpJfFsv9HMAsipX4G-QEV1kLRmv0UKhCW0nUCySvoryTYeLm4nmt5jRRxs1-GmHVgXgX5d0C'),
    # 高增长结构切换与现金转换压力
    ('structure_shift', 'http://www.baidu.com/link?url=ZoihgnNposZBM7r0dYF3h64wgc2J6PhNukMl7oL1Z_E-5ZW3NbbwXUKGqA5VHeGuAAfWlIZrt7Ok3IrY7MN74a'),
    # 26年中报业绩自问自答 财务费用
    ('self_qa', 'http://www.baidu.com/link?url=ZoihgnNposZBM7r0dYF3h64wgc2J6PhNukMl7oL1Z_CkSN2Se9AmfNgkN5ta5Vy88sbdAVkbCKllKleFwi7kxq'),
    # Q2业绩符合预期 盈利能力稳定
    ('q2_stable', 'http://www.baidu.com/link?url=owxpEPNoAHTx2w1oL96q1yvjfImGZdV6DYI7oU6GLor8m9qpZ9nYUA0wQwU4oeT6Wnh5gfUUiTqZafMdqrPYJNTmZjFijOYura5ARGin8f'),
    # 上半年储能业务为何增长近九成
    ('storage_90', 'http://www.baidu.com/link?url=owxpEPNoAHTx2w1oL96q1v76p1DjJwIAxDsqKz49MWZ55uH51q8RjlVGGKz1KeBMsr4rUrH1mWfd8IBM5nk3anJHvTSNP0vPPY8LCKExogq'),
    # 宁王半年报绝地反攻 锂电鬼故事
    ('ghost_story', 'http://www.baidu.com/link?url=x-bIBcqai0O1BOhDLMLmONRZ0AvLRD9PdsQp0nSaXLh7IvPaxcuQVdQs86vOEy9qhhPwcEl9BQg4N7Hf7TMVJthRMLUPXq-JnUMxu0eX-rk8nXYVSNAJ66MXIQKeDQ4oPG3mrOKVtBJztKgZZK6UEK'),
    # 连续募资超470亿背后 利息投资收益占四成利润
    ('470_interest', 'http://www.baidu.com/link?url=_OyA5o8rqpoU_cw6Ho2U06Y_Nt605SfD5t_9JDiJ6e-2Vu7v3_KfIxjEyEU3MPb7mGglIZeAVMiczl_3vgwe-a'),
    # 宁王半年报出炉 10派10.07元 (旧文)
    ('ning10_07', 'http://www.baidu.com/link?url=EPQMIa4_KIKKZUyf3VHKtRE-8prUVgK8yNPS_tznOrHAOj9ysoFThb98RBfH44gzT9pIiA8xak4-WJDCUyNjnq'),
    # 价格战下挤出利润 进入保守期
    ('conservative', 'http://www.baidu.com/link?url=oM7aeSaaDLRud5Vn_qRnx2QbeFliP7qe3jx0JMer9lBYm6eygnSEKUdMi3yuYkVN37WbckURo0UhvMX8JCo9AEI4LwpQXj-fln51JgJSu0W'),
    # 这份半年报真的低预期了吗
    ('low_expect', 'http://www.baidu.com/link?url=qvBdcJxApK4x6XXGgyGu8NVo5nNY6vuVrMZilaSyPOPpWjtLy2juvbcPOrsZDocEoTv5oJ8vFX1Hq1hSCquYyfnUyPRMudmCCqv3ga1nKne'),
    # 一季度三元锂份额81.6% 同比增10.7个百分点
    ('ternary_816', 'http://www.baidu.com/link?url=aYIMonEsYA0p1l52KmVZnaEU1mP5826vEuWXZ7QJWZdrvU8enghIcy2XICaBqzuy_YUlrgy_RAs97S2vZQhzWhhOgUMqbPOBjLkOoQqHC31FPX4OdDhnpC5s8qmRoVUD'),
    # 中东订单变化
    ('middle_east', 'http://www.baidu.com/link?url=g5n66jBNUivF5JWFbDV6Sd93SLdtMtro-dOYpcJ2sCePRXqlzgWkX5Gu2cxCheQrbP0YVZd7nMeXac0HcaanjtRBbrARYzg1XrqEJqEoWOa'),
    # 央广网 业绩持续超预期增长 市场份额稳步提升
    ('cctv_share', 'http://www.baidu.com/link?url=Jj6gxZORWIwD_TZ90IxYZOCnGV0SprwJ9Cxb2gDvFDbxozu_CGdk-xMpw_2nqvPlU-X41DKBOSm8N-_2bViALM35dJZirHLd9cEylV77IIK'),
    # 上半年与子公司非经营性资金往来132.38亿
    ('zijin_132', 'http://www.baidu.com/link?url=lFgnZmTkCJvCVxr65QUHDtm2c59DIAW0tlfhF-sIt-9V9_edpain8dKe2kuosGa7pG-8ElZ631Tb9RjCjuESKtlQGNKeIfxepnTO3aoD3Ta'),
    # 济宁140亿电池基地投入119亿
    ('jining_119', 'http://www.baidu.com/link?url=oM7aeSaaDLRud5Vn_qRnx2QbeFliP7qe3jx0JMer9l4_kWwBy0Ixffalt5d_pifRVFJgMnL5JfAOJs0bWqonTVoCe0CvVciPnUlo9bRCHOS'),
    # 工信部 电池货款账期不超60天
    ('zhangqi_60', 'http://www.baidu.com/link?url=DaArqEzl0_4QEx_Q9FYkUJ656h_g2xUMb4PF2qewt092671FtG6NdB1R8fwGGUaFt5zmTPJWtKqUS7YwRyIy7q'),
    # 收款2个月付账大半年
    ('shoukuan_2m_v2', 'http://www.baidu.com/link?url=yetZ3XBJfv5Rfmjn01lair_8J-SHLQFLrlNp7VxGDSGP8EhI86VXpuF78Pkm05Up3CvgZ2ksp41d4aOS04e1-x8ICPddurmX3W69ziTIxwu'),
    # 花旗预估2026Q2宁德净利润243亿元 电池出货
    ('citi_q2_243', 'http://www.baidu.com/link?url=s39IfTaiJfaX0_I-ZGvKknDz9WJ_HOONL9m_M-NnTV1-5DfmtzTyfiT_lAs3EmDG_6Fh2G2iAZBlxOxHMcAm7a'),
]

def strip_tags(s):
    s = re.sub(r'<script[^>]*>.*?</script>', '', s, flags=re.S)
    s = re.sub(r'<style[^>]*>.*?</style>', '', s, flags=re.S)
    s = re.sub(r'<[^>]+>', ' ', s)
    s = html.unescape(s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def resolve_and_fetch(name, baidu_link):
    out_html = f'{BASE}\\articles4\\{name}.html'
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
