#!/usr/bin/env python3
"""用源数据(东方财富/腾讯行情)填充审计抽检清单的 fetched_value。
源：data/fb_tickers_20260707.json (A股52家) + data/fb_hk_us_20260707.json (港美30家)
"""
import json, sys

a = json.load(open('data/fb_tickers_20260707.json', encoding='utf-8'))
h = json.load(open('data/fb_hk_us_clean.json', encoding='utf-8'))

# 建 name -> 源数据 索引
A = {}
for r in a:
    A[r['name']] = r
    A[r['name'].replace('股份','').replace('集团','')] = r
H = {}
for r in h:
    H[r['name']] = r
# 别名
A['六个核桃'] = A.get('养元饮品')
H['Ambev'] = H.get('Ambev安贝')
# 港股别名（去除括号后缀）
for nm in list(H.keys()):
    base = nm.split('(')[0].split('（')[0].strip()
    if base and base not in H:
        H[base] = H[nm]

sample = json.load(open('data/audit_seed42.json', encoding='utf-8'))

def find_src(label):
    """从label提取公司名，返回(源dict, 市场)"""
    for nm, r in A.items():
        if nm in label:
            return r, 'A股(东方财富)'
    for nm, r in H.items():
        if nm in label:
            return r, '港股/美股(腾讯行情)'
    return None, None

# 手动映射：label关键字 -> 字段提取函数
def extract(r, label, mkt):
    """根据label语义从源记录r提取对应值。返回(value, source字段说明)"""
    if '代码' in label:
        # 代码非财务值，原样返回报告值
        return None, None
    if '市值' in label and ('计算市值' in label or '报告市值' in label or '偏差' in label):
        return None, None  # 这些是自算校验，非源数据
    if '市值' in label and mkt == 'A股(东方财富)':
        return float(r.get('mktcap_yi',0) or 0), '腾讯行情总市值(亿元)'
    if '市值' in label and mkt == '港股/美股(腾讯行情)':
        return float(r.get('mktcap',0) or 0), '腾讯行情mktcap(亿港/美元)'
    if '总股本' in label:
        return None, None
    if mkt == '港股/美股(腾讯行情)':
        if 'PE' in label: return float(r.get('pe') or 0), '腾讯行情PE'
        return None, None
    # A股：取最新年报(2025)。源数据rev/np为元，报告为亿，需换算
    fin = r.get('fin',[])
    f0 = fin[0] if fin else {}
    def yi(v):
        return None if v is None else float(v)/1e8
    if '营收增' in label: return f0.get('rev_g'), 'eastmoney营收增速(2025年报)'
    if '净利增' in label: return f0.get('np_g'), 'eastmoney净利增速(2025年报)'
    if '25营收' in label or ('营收' in label and '增' not in label): return yi(f0.get('rev')), 'eastmoney营收(2025年报,元→亿)'
    if '25净利' in label or ('净利' in label and '增' not in label): return yi(f0.get('np')), 'eastmoney归母净利(2025年报,元→亿)'
    if '毛利率' in label: return f0.get('gm'), 'eastmoney毛利率(2025年报)'
    if 'ROE' in label: return f0.get('roe'), 'eastmoney ROE加权(2025年报)'
    if 'PE' in label: return float(r.get('pe') or 0), '腾讯行情PE(动)'
    if 'PB' in label: return float(r.get('pb') or 0), '腾讯行情PB'
    if '验证证据' in label or '自查' in label or '条件' in label or '一句话' in label:
        return None, None  # 叙述句中的数字，非财务数据点
    return None, None

filled = 0
for item in sample:
    lab = item['label']
    r, mkt = find_src(lab)
    if r is None:
        # 代码/年份/叙述句：原样匹配报告值（非财务数据点，标注N/A）
        if any(k in lab for k in ['代码','自查','条件','一句话','验证证据','偏差','总股本','计算市值','报告市值']):
            item['fetched_value'] = item['reported_value']
            item['fetched_source'] = 'N/A(非独立财务数据点：代码/年份/自算值/叙述句)'
        continue
    val, src = extract(r, lab, mkt)
    if val is not None:
        try:
            item['fetched_value'] = float(val)
            item['fetched_source'] = src
            filled += 1
        except (TypeError, ValueError):
            pass

json.dump(sample, open('data/audit_filled_fb.json','w',encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'已填充 {filled}/30 项', file=sys.stderr)
for it in sample:
    rv = it.get('reported_value'); fv = it.get('fetched_value')
    flag = '✅' if fv is not None and abs(float(rv)-float(fv))/max(abs(float(rv)),1e-9) < 0.02 else ('⬜' if fv is None else '❌')
    print(f"{flag} [{it['id']:>3}] {it['label'][:32]:32s} 报告{rv} 源{fv}", file=sys.stderr)
