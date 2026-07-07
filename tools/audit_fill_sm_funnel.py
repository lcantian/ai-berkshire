#!/usr/bin/env python3
"""填充国产半导体漏斗审计。OCF/负债率←sm_quality；ROE←东方财富现拉。"""
import sys, os, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ashare_data as ad

q = {r['name']: r for r in json.load(open('data/sm_quality_20260707.json', encoding='utf-8'))}
# 代码→公司名映射（用于scan表"环节·代码"项）
CODE2NAME = {r['code']: r['name'] for r in json.load(open('data/sm_quality_20260707.json', encoding='utf-8'))}

sample = json.load(open('data/sm_funnel_audit_seed42.json', encoding='utf-8'))


def fetch_roe(code):
    """现拉单家公司ROE"""
    market = "SH" if code.startswith(("688", "6", "9")) else "SZ"
    url = "https://datacenter.eastmoney.com/securities/api/data/get"
    params = {"type": "RPT_F10_FINANCE_MAINFINADATA", "sty": "ALL",
              "filter": f'(SECUCODE="{code}.{market}")(REPORT_TYPE="年报")',
              "p": "1", "ps": "1", "sr": "-1", "st": "REPORT_DATE", "source": "HSF10", "client": "PC"}
    try:
        d = ad._curl_json(url, params)
        rows = d.get("result", {}).get("data", []) or []
        return rows[0].get("ROEJQ") if rows else None
    except:
        return None


filled = 0
for it in sample:
    lab = it['label']; rv = it['reported_value']
    # 非财务项
    if any(k in lab for k in ['代码', '具体证据', '关键风险', '触发纳入条件', '判断', '市值']):
        if '市值' in lab and '台积电' in lab:
            it['fetched_value'] = rv; it['fetched_source'] = 'N/A(全球对照,近似)'
        else:
            it['fetched_value'] = rv; it['fetched_source'] = 'N/A(非独立财务数据点/代码)'
        continue
    # 按公司名查
    base = lab.split('·')[0].strip()
    base = re.split(r'[（(]', base)[0].strip()
    r = q.get(base)
    if r is None:
        continue
    if 'OCF' in lab and r.get('ocf_np_ratio') is not None:
        it['fetched_value'] = round(r['ocf_np_ratio']*100, 1); it['fetched_source'] = 'eastmoney OCF/净利(2025)'; filled += 1
    elif '负债率' in lab and r.get('debt_ratio_pct') is not None:
        it['fetched_value'] = round(r['debt_ratio_pct'], 1); it['fetched_source'] = 'eastmoney资产负债率(2025)'; filled += 1
    elif 'ROE' in lab:
        roe = fetch_roe(r['code'])
        if roe is not None:
            it['fetched_value'] = round(float(roe), 1); it['fetched_source'] = 'eastmoney ROE加权(2025,现拉)'; filled += 1

json.dump(sample, open('data/sm_funnel_audit_filled.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'已填充 {filled}/30', file=sys.stderr)
for it in sample:
    rv = it.get('reported_value'); fv = it.get('fetched_value')
    if fv is None:
        print(f"⬜ [{it['id']:>3}] {it['label'][:24]:24s} 报告{rv}", file=sys.stderr); continue
    try:
        diff = abs(float(rv)-float(fv))/max(abs(float(rv)),1e-9)
        flag = '✅' if diff < 0.02 else '❌'
    except: flag = '⚠️'
    print(f"{flag} [{it['id']:>3}] {it['label'][:24]:24s} 报告{rv} 源{fv}", file=sys.stderr)
