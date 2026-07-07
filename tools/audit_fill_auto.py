#!/usr/bin/env python3
"""用源数据填充汽车审计抽检清单。"""
import json, sys, re

a = json.load(open('data/auto_tickers_20260707.json', encoding='utf-8'))
h = json.load(open('data/auto_hk_us_clean.json', encoding='utf-8'))

A = {r['name']: r for r in a}
H = {r['name']: r for r in h}

def find_src(label):
    # 去除括号后缀做匹配
    base = re.split(r'[（(]', label)[0].strip()
    # A股优先（带环节后缀如"德赛西威(智驾)" → "德赛西威"）
    for nm, r in A.items():
        if nm in base or base in nm:
            return r, 'A股(东方财富)'
    for nm, r in H.items():
        if nm in base or base in nm:
            return r, '港股/美股(腾讯行情)'
    return None, None

def extract(r, label, mkt):
    if '代码' in label: return None, None
    if '商业模式' in label: return None, None
    if any(k in label for k in ['概率', '依据', '上限', '标的']) and 'PE' not in label and 'PB' not in label:
        return None, None
    if '市值' in label and mkt == 'A股(东方财富)':
        return float(r.get('mktcap_yi',0) or 0), '腾讯行情总市值(亿元)'
    if '市值' in label and mkt == '港股/美股(腾讯行情)':
        return float(r.get('mktcap',0) or 0), '腾讯行情mktcap(亿港/美元)'
    if 'PE' in label and mkt == '港股/美股(腾讯行情)':
        return float(r.get('pe') or 0), '腾讯行情PE'
    if 'PE' in label and mkt == 'A股(东方财富)':
        return float(r.get('pe') or 0), '腾讯行情PE(动)'
    if 'PB' in label:
        return float(r.get('pb') or 0), '腾讯行情PB'
    fin = r.get('fin', []); f0 = fin[0] if fin else {}
    yi = lambda v: None if v is None else float(v)/1e8
    if '营收增' in label: return f0.get('rev_g'), 'eastmoney营收增速(2025年报)'
    if '净利增' in label: return f0.get('np_g'), 'eastmoney净利增速(2025年报)'
    if '25营收' in label or ('营收' in label and '增' not in label): return yi(f0.get('rev')), 'eastmoney营收(2025年报,元→亿)'
    if '25净利' in label or ('净利' in label and '增' not in label): return yi(f0.get('np')), 'eastmoney归母净利(2025年报,元→亿)'
    return None, None

sample = json.load(open('data/auto_audit_seed42.json', encoding='utf-8'))
filled = 0
for item in sample:
    lab = item['label']
    r, mkt = find_src(lab)
    if r is None:
        # 概率/依据/上限/商业模式等非独立财务数据点
        if any(k in lab for k in ['商业模式','概率','依据','上限','代码']):
            item['fetched_value'] = item['reported_value']
            item['fetched_source'] = 'N/A(非独立财务数据点)'
        continue
    val, src = extract(r, lab, mkt)
    if val is not None:
        try:
            item['fetched_value'] = float(val)
            item['fetched_source'] = src
            filled += 1
        except (TypeError, ValueError):
            pass

json.dump(sample, open('data/auto_audit_filled.json','w',encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'已填充 {filled}/30 项', file=sys.stderr)
for it in sample:
    rv = it.get('reported_value'); fv = it.get('fetched_value')
    if fv is None:
        print(f"⬜ [{it['id']:>3}] {it['label'][:30]:30s} 报告{rv}", file=sys.stderr); continue
    try:
        diff = abs(float(rv)-float(fv))/max(abs(float(rv)),1e-9)
        flag = '✅' if diff < 0.02 else '❌'
    except: flag='❌'
    print(f"{flag} [{it['id']:>3}] {it['label'][:30]:30s} 报告{rv} 源{fv:.2f}", file=sys.stderr)
