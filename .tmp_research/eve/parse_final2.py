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
if __name__=='__main__':
    out=io.StringIO()
    is_labels=['营业总收入','营业收入','营业总成本','营业成本','销售费用','管理费用','研发费用','财务费用','营业利润','投资收益','利润总额','净利润','归属于母公司所有者的净利润','信用减值损失','资产减值损失']
    out.write('INCOME STATEMENT (亿元, 单位转换: 万元->亿):\n')
    hdr=f'{"年":<6}{"营业收入":<9}{"营业成本":<9}{"毛利":<8}{"毛利率":<7}{"销售费":<7}{"管理费":<7}{"研发费":<7}{"研发占收":<8}{"财务费":<7}{"营业利润":<9}{"归母净利":<9}{"净利率":<7}\n'
    out.write(hdr)
    for yr in ['2021','2022','2023','2024','2025']:
        res=parse_statement(f'is_{yr}.html', is_labels)
        rev=yi(to_num(res.get('营业收入',{}).get(f'{yr}-12-31')))
        cost=yi(to_num(res.get('营业成本',{}).get(f'{yr}-12-31')))
        sale=yi(to_num(res.get('销售费用',{}).get(f'{yr}-12-31')))
        mgmt=yi(to_num(res.get('管理费用',{}).get(f'{yr}-12-31')))
        rd=yi(to_num(res.get('研发费用',{}).get(f'{yr}-12-31')))
        fin=yi(to_num(res.get('财务费用',{}).get(f'{yr}-12-31')))
        op=yi(to_num(res.get('营业利润',{}).get(f'{yr}-12-31')))
        np=yi(to_num(res.get('归属于母公司所有者的净利润',{}).get(f'{yr}-12-31')))
        gp=(rev-cost) if rev and cost else None
        gm=(gp/rev*100) if gp and rev else None
        rdr=(rd/rev*100) if rd and rev else None
        nm=(np/rev*100) if np and rev else None
        out.write(f'{yr:<6}{fmt(rev,9)}{fmt(cost,9)}{fmt(gp,8)}{fmt(gm,7)}{fmt(sale,7)}{fmt(mgmt,7)}{fmt(rd,7)}{fmt(rdr,8)}{fmt(fin,7)}{fmt(op,9)}{fmt(np,9)}{fmt(nm,7)}\n')
    sys.stdout.buffer.write(out.getvalue().encode('utf-8'))
