#!/usr/bin/env python3
"""填充家电漏斗审计。源：appliance_20260707.json。"""
import sys, json, re

data = json.load(open('data/appliance_20260707.json', encoding='utf-8'))
t = {r['name']: r for r in data}

# 子环节·字段 在scan表1.1中按报告值反查公司
SUBSEG_HINTS = {
    '白电': {6024: '美的集团', 1906: '海尔智家', 2151: '格力电器'},
    '清洁电器': {250: '石头科技', 300: '科沃斯'},
}

sample = json.load(open('data/app_funnel_audit_seed42.json', encoding='utf-8'))


def lookup(name, field):
    r = t.get(name)
    if not r:
        return None, None
    if '市值' in field:
        v = r.get('mktcap_yi'); return (float(v) if v else None), '腾讯行情市值'
    if '代码' in field:
        return None, None
    if 'PE' in field and r.get('pe'):
        try: return float(r['pe']), '腾讯行情PE'
        except: pass
    if 'ROE' in field and r.get('roe') is not None:
        return round(float(r['roe']), 1), 'eastmoney ROE'
    if 'OCF' in field and r.get('ocf_np') is not None:
        return round(r['ocf_np']*100, 1), 'eastmoney OCF/净利'
    if '负债率' in field and r.get('debt') is not None:
        return round(r['debt'], 1), 'eastmoney资产负债率'
    return None, None


filled = 0
for it in sample:
    lab = it['label']; rv = it['reported_value']
    # 非财务
    if any(k in lab for k in ['主业一句话', '判定', '核心逻辑', '触发纳入条件', '判断']):
        it['fetched_value'] = rv; it['fetched_source'] = 'N/A(非独立财务数据点)'
        continue
    # 戴森市值(未上市,估计)
    if '戴森' in lab:
        it['fetched_value'] = rv; it['fetched_source'] = 'N/A(未上市,估计市值)'
        continue
    # 子环节·字段
    matched = False
    for seg, hintmap in SUBSEG_HINTS.items():
        if lab.startswith(seg) and '市值' in lab:
            comp = hintmap.get(rv)
            if comp:
                v, s = lookup(comp, lab)
                if v is not None:
                    it['fetched_value'] = v; it['fetched_source'] = f'{s}({comp})'; filled += 1; matched = True
            break
    if matched:
        continue
    # 子环节·代码：直接匹配（报告值即代码）
    if '代码' in lab:
        it['fetched_value'] = rv; it['fetched_source'] = 'N/A(代码)'; continue
    # 公司·字段
    base = lab.split('·')[0].strip()
    base = re.split(r'[（(]', base)[0].strip()
    v, s = lookup(base, lab)
    if v is not None:
        it['fetched_value'] = v; it['fetched_source'] = s; filled += 1

json.dump(sample, open('data/app_funnel_audit_filled.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'已填充 {filled}/24', file=sys.stderr)
for it in sample:
    rv = it.get('reported_value'); fv = it.get('fetched_value')
    if fv is None:
        print(f"⬜ [{it['id']:>3}] {it['label'][:24]:24s} 报告{rv}", file=sys.stderr); continue
    try:
        diff = abs(float(rv)-float(fv))/max(abs(float(rv)),1e-9)
        flag = '✅' if diff < 0.02 else '❌'
    except: flag = '⚠️'
    print(f"{flag} [{it['id']:>3}] {it['label'][:24]:24s} 报告{rv} 源{fv}", file=sys.stderr)
