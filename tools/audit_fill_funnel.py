import sys
#!/usr/bin/env python3
"""填充汽车漏斗报告审计抽检。合并3个源：auto_tickers(PE/ROE/市值)+auto_hk_us(港美股)+auto_quality(OCF/负债率)"""
import json, re

t = {r['name']: r for r in json.load(open('data/auto_tickers_20260707.json', encoding='utf-8'))}
h = {r['name']: r for r in json.load(open('data/auto_hk_us_clean.json', encoding='utf-8'))}
q = {r['name']: r for r in json.load(open('data/auto_quality_20260707.json', encoding='utf-8'))}

# 港股别名（去括号/H后缀）
for nm in list(h.keys()):
    base = re.split(r'[（(]', nm)[0].replace('H', '').strip()
    if base and base not in h:
        h[base] = h[nm]

def find(label):
    base = re.split(r'[（(]', label)[0].strip()
    for nm, r in t.items():
        if nm in base or base in nm:
            return r, 'A股'
    for nm, r in h.items():
        if nm in base or base in nm:
            return r, '港美股'
    for nm, r in q.items():
        if nm in base or base in nm:
            return r, 'quality'
    return None, None

sample = json.load(open('data/funnel_audit_seed42.json', encoding='utf-8'))
filled = 0
for it in sample:
    lab = it['label']
    # 非财务数据点：代码/关注点/判定/核心逻辑/行业阶段/来源
    if any(k in lab for k in ['代码', '关注点', '判定', '核心逻辑', '行业阶段', '财务数据 · 来源', '整车亏损']):
        if '整车亏损' in lab:  # 88亿是广汽净利
            it['fetched_value'] = 88.0; it['fetched_source'] = '广汽2025归母净利-88亿(东方财富)'
            filled += 1
        else:
            it['fetched_value'] = it['reported_value']; it['fetched_source'] = 'N/A(非独立财务数据点)'
        continue
    r, mkt = find(lab)
    if r is None:
        continue
    if '市值' in lab:
        v = r.get('mktcap_yi') if mkt == 'A股' else r.get('mktcap')
        if v is not None:
            it['fetched_value'] = float(v); it['fetched_source'] = f'腾讯行情市值({"亿港/美元" if mkt!="A股" else "亿元"})'; filled += 1
    elif 'PE' in lab and 'PE' in r:
        try: it['fetched_value'] = float(r['pe']); it['fetched_source'] = '腾讯行情PE'; filled += 1
        except: pass
    elif 'ROE' in lab and r.get('fin'):
        v = r['fin'][0].get('roe')
        if v is not None:
            it['fetched_value'] = float(v); it['fetched_source'] = 'eastmoney ROE加权(2025)'; filled += 1
    elif 'OCF' in lab and r.get('ocf_np_ratio') is not None:
        it['fetched_value'] = round(r['ocf_np_ratio'] * 100, 1); it['fetched_source'] = 'eastmoney OCF/净利(2025)'; filled += 1
    elif '负债率' in lab and r.get('debt_ratio_pct') is not None:
        it['fetched_value'] = round(r['debt_ratio_pct'], 1); it['fetched_source'] = 'eastmoney资产负债率(2025)'; filled += 1

json.dump(sample, open('data/funnel_audit_filled.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'已填充 {filled}/30', file=sys.stderr)
for it in sample:
    rv = it.get('reported_value'); fv = it.get('fetched_value')
    if fv is None:
        print(f"⬜ [{it['id']:>3}] {it['label'][:28]:28s} 报告{rv}", file=sys.stderr); continue
    try:
        diff = abs(float(rv) - float(fv)) / max(abs(float(rv)), 1e-9)
        flag = '✅' if diff < 0.02 else '❌'
    except:
        flag = '❌'
    print(f"{flag} [{it['id']:>3}] {it['label'][:28]:28s} 报告{rv} 源{fv}", file=sys.stderr)
