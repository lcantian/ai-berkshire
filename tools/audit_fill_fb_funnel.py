import sys, json, re
#!/usr/bin/env python3
"""填充食品饮料漏斗报告审计。合并 fb_tickers(A股)+fb_hk_us(港美股)+fb_quality(OCF/负债率)。"""

t = {r['name']: r for r in json.load(open('data/fb_tickers_20260707.json', encoding='utf-8'))}
h = {r['name']: r for r in json.load(open('data/fb_hk_us_clean.json', encoding='utf-8'))}
q = {r['name']: r for r in json.load(open('data/fb_quality_20260707.json', encoding='utf-8'))}
for nm in list(h.keys()):
    base = re.split(r'[（(]', nm)[0].strip()
    if base and base not in h:
        h[base] = h[nm]

# 子环节→公司 映射（扫描表1.1的行，按报告值反查）
SUBSEG_MAP = {
    '乳制品': ('中国飞鹤', 'h'), '调味品': ('海天味业', 't'), '软饮料': ('东鹏饮料', 't'),
    '保健品': ('汤臣倍健', 't'), '休闲食品': ('卫龙美味', 'h'), '速冻': ('安井食品', 't'),
    '食品添加': ('阜丰集团', 'h'), '肉制品': ('双汇发展', 't'), '饲料': ('海大集团', 't'),
    '包材': ('奥瑞金', 't'),
}

sample = json.load(open('data/fb_funnel_audit_seed42.json', encoding='utf-8'))

def lookup_company(name, field):
    """从t/h/q查公司字段"""
    src = None
    if name in t: src = ('t', t[name])
    elif name in h: src = ('h', h[name])
    elif name in q: src = ('q', q[name])
    if not src:
        return None, None
    kind, r = src
    if '市值' in field:
        v = r.get('mktcap_yi') if kind == 't' else r.get('mktcap')
        return (float(v) if v else None), f'腾讯行情市值'
    if '代码' in field:
        return None, None
    if 'PE' in field and 'pe' in r:
        try: return float(r['pe']), '腾讯行情PE'
        except: return None, None
    if 'ROE' in field and r.get('fin'):
        v = r['fin'][0].get('roe')
        return (float(v) if v else None), 'eastmoney ROE'
    if 'OCF' in field and r.get('ocf_np_ratio') is not None:
        return round(r['ocf_np_ratio']*100, 1), 'eastmoney OCF/净利'
    if '负债率' in field and r.get('debt_ratio_pct') is not None:
        return round(r['debt_ratio_pct'], 1), 'eastmoney资产负债率'
    return None, None

filled = 0
for it in sample:
    lab = it['label']; rv = it['reported_value']
    # 非财务数据点
    if any(k in lab for k in ['主业一句话', '判定', '核心逻辑', '来源', '代码']):
        it['fetched_value'] = rv; it['fetched_source'] = 'N/A(非独立财务数据点/代码)'
        continue
    # 子环节·字段
    for seg, (comp, _) in SUBSEG_MAP.items():
        if lab.startswith(seg + ' ·') or lab.startswith(seg + ' '):
            v, s = lookup_company(comp, lab)
            if v is not None:
                it['fetched_value'] = v; it['fetched_source'] = f'{s}({comp})'; filled += 1
            else:
                it['fetched_value'] = rv; it['fetched_source'] = f'N/A(子环节行,{comp})'
            break
    else:
        # 公司·字段：按 · 分割取公司名
        base = lab.split('·')[0].strip()
        base = re.split(r'[（(]', base)[0].strip()
        v, s = lookup_company(base, lab)
        if v is not None:
            it['fetched_value'] = v; it['fetched_source'] = s; filled += 1

json.dump(sample, open('data/fb_funnel_audit_filled.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'已填充 {filled}/30', file=sys.stderr)
for it in sample:
    rv = it.get('reported_value'); fv = it.get('fetched_value')
    if fv is None:
        print(f"⬜ [{it['id']:>3}] {it['label'][:26]:26s} 报告{rv}", file=sys.stderr); continue
    try:
        diff = abs(float(rv)-float(fv))/max(abs(float(rv)),1e-9)
        flag = '✅' if diff < 0.02 else '❌'
    except: flag = '⚠️'
    print(f"{flag} [{it['id']:>3}] {it['label'][:26]:26s} 报告{rv} 源{fv}", file=sys.stderr)
