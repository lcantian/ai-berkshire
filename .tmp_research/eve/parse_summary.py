# -*- coding: utf-8 -*-
import re, sys, io
def read_html(path):
    with open(path,'rb') as f: raw=f.read()
    for enc in ['gb18030','gbk','utf-8']:
        try: return raw.decode(enc)
        except: continue
    return raw.decode('gb18030',errors='replace')
def parse_statement(path, wanted_labels):
    html=read_html(path)
    tbodies=re.findall(r'<tbody>(.*?)</tbody>', html, re.S)
    rows=[]
    for tb in tbodies: rows.extend(re.findall(r'<tr[^>]*>(.*?)</tr>', tb, re.S))
    dates=[]
    for row in rows:
        cells=re.findall(r'<td[^>]*>(.*?)</td>', row, re.S)
        cells=[re.sub(r'<[^>]+>','',c).strip() for c in cells]
        cells=[c for c in cells if c!='']
        if len(cells)>=2 and re.match(r'^\d{4}-\d{2}-\d{2}$', cells[1]):
            dates=cells[1:]; break
    result={}
    for row in rows:
        cells=re.findall(r'<td[^>]*>(.*?)</td>', row, re.S)
        cells=[re.sub(r'<[^>]+>','',c).strip() for c in cells]
        cells=[c for c in cells if c!='']
        if len(cells)<2: continue
        if cells[0] in wanted_labels:
            vals=cells[1:]
            result[cells[0]]={dates[i]:vals[i] for i in range(min(len(dates),len(vals)))}
    return result
def to_num(s):
    if not s or s in('--','-',''): return None
    s=s.replace(',','').strip()
    try: return float(s)
    except: return None
def yi(v): return v/10000 if v else None
def fmt(v,w=8,p=2): return f'{v:<{w}.{p}f}' if v else f'{"-":<{w}}'
out=io.StringIO()
# CASH FLOW + FCF
cf_labels=['经营活动产生的现金流量净额','购建固定资产、无形资产和其他长期资产所支付的现金','投资活动产生的现金流量净额','筹资活动产生的现金流量净额']
out.write('CASH FLOW & FCF (亿元):\n')
out.write(f'{"年":<6}{"经营CF":<9}{"资本开支":<9}{"FCF":<9}{"FCF/股":<8}{"投资CF":<9}{"筹资CF":<9}\n')
for yr in ['2021','2022','2023','2024','2025']:
    res=parse_statement(f'cf_{yr}.html', cf_labels)
    ocf=yi(to_num(res.get('经营活动产生的现金流量净额',{}).get(f'{yr}-12-31')))
    capex=yi(to_num(res.get('购建固定资产、无形资产和其他长期资产所支付的现金',{}).get(f'{yr}-12-31')))
    icf=yi(to_num(res.get('投资活动产生的现金流量净额',{}).get(f'{yr}-12-31')))
    fcf=yi(to_num(res.get('筹资活动产生的现金流量净额',{}).get(f'{yr}-12-31')))
    fcf_val=(ocf-capex) if ocf and capex else None
    out.write(f'{yr:<6}{fmt(ocf,9)}{fmt(capex,9)}{fmt(fcf_val,9)}{"":<8}{fmt(icf,9)}{fmt(fcf,9)}\n')
# BALANCE SHEET DEBT
bs_labels=['货币资金','交易性金融资产','资产总计','短期借款','一年内到期的非流动负债','长期借款','应付债券','租赁负债','负债合计','归属于母公司股东权益合计','所有者权益（或股东权益）合计']
out.write('\nBALANCE SHEET & NET DEBT (亿元):\n')
out.write(f'{"年":<6}{"货币资金":<9}{"交易FA":<8}{"短期借款":<9}{"1年内非流":<10}{"长期借款":<9}{"应付债券":<9}{"租赁负债":<9}{"有息负债":<9}{"资产负债率%":<10}{"归母净资产":<10}\n')
for yr in ['2021','2022','2023','2024','2025']:
    res=parse_statement(f'bs_{yr}.html', bs_labels)
    cash=yi(to_num(res.get('货币资金',{}).get(f'{yr}-12-31')))
    tfa=yi(to_num(res.get('交易性金融资产',{}).get(f'{yr}-12-31')))
    stb=yi(to_num(res.get('短期借款',{}).get(f'{yr}-12-31')))
    cdn=yi(to_num(res.get('一年内到期的非流动负债',{}).get(f'{yr}-12-31')))
    ltb=yi(to_num(res.get('长期借款',{}).get(f'{yr}-12-31')))
    bond=yi(to_num(res.get('应付债券',{}).get(f'{yr}-12-31')))
    lease=yi(to_num(res.get('租赁负债',{}).get(f'{yr}-12-31')))
    ta=yi(to_num(res.get('资产总计',{}).get(f'{yr}-12-31')))
    tl=yi(to_num(res.get('负债合计',{}).get(f'{yr}-12-31')))
    pe=yi(to_num(res.get('归属于母公司股东权益合计',{}).get(f'{yr}-12-31')))
    ibd=sum(x for x in [stb,cdn,ltb,bond,lease] if x)
    dar=(tl/ta*100) if tl and ta else None
    nc=(cash+tfa-ibd) if all(z is not None for z in [cash,tfa]) else None
    out.write(f'{yr:<6}{fmt(cash,9)}{fmt(tfa,8)}{fmt(stb,9)}{fmt(cdn,10)}{fmt(ltb,9)}{fmt(bond,9)}{fmt(lease,9)}{fmt(ibd,9)}{fmt(dar,10)}{fmt(pe,10)}\n')
    out.write(f'      -> 净现金=(货币+交易FA)-有息负债 = {fmt(nc,10)}\n')
sys.stdout.buffer.write(out.getvalue().encode('utf-8'))
