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
    result={}
    for row in rows:
        cells=re.findall(r'<td[^>]*>(.*?)</td>', row, re.S)
        cells=[re.sub(r'<[^>]+>','',c).strip() for c in cells]
        cells=[c for c in cells if c!='']
        if len(cells)>=2 and re.match(r'^\d{4}-\d{2}-\d{2}$', cells[1]):
            dates=cells[1:]; break
    for row in rows:
        cells=re.findall(r'<td[^>]*>(.*?)</td>', row, re.S)
        cells=[re.sub(r'<[^>]+>','',c).strip() for c in cells]
        cells=[c for c in cells if c!='']
        if len(cells)<2: continue
        label=cells[0]
        if label in wanted_labels:
            vals=cells[1:]
            result[label]={dates[i]:vals[i] for i in range(min(len(dates),len(vals)))}
    return dates, result

def to_num(s):
    if not s or s=='--' or s=='-': return None
    s=s.replace(',','').strip()
    try: return float(s)
    except: return None

if __name__=='__main__':
    out=io.StringIO()
    # INCOME STATEMENT
    is_labels=['一、营业总收入','其中：营业收入','四、净利润','归属于母公司股东的净利润','二、营业总成本','其中：营业成本','其中：销售费用','其中：管理费用','其中：研发费用','其中：财务费用','其中：利息费用','三、营业利润','投资收益','信用减值损失','资产减值损失','资产处置收益']
    out.write('################ INCOME STATEMENT ################\n')
    for yr in ['2025','2024','2023','2022','2021']:
        dates,res=parse_statement(f'is_{yr}.html', is_labels)
        out.write(f'\n===== IS {yr} (Dec-31 annual) =====\n')
        for lb in is_labels:
            if lb in res:
                v=to_num(res[lb].get(f'{yr}-12-31'))
                out.write(f'  {lb}: {v/10000:.2f} yi' if v else f'  {lb}: {res[lb].get(f"{yr}-12-31","?")}\n')
                if v: out.write('\n')
    # CASH FLOW
    cf_labels=['销售商品、提供劳务收到的现金','经营活动产生的现金流量净额','购建固定资产、无形资产和其他长期资产支付的现金','投资活动产生的现金流量净额','筹资活动产生的现金流量净额','现金及现金等价物净增加额']
    out.write('\n################ CASH FLOW ################\n')
    for yr in ['2025','2024','2023','2022','2021']:
        dates,res=parse_statement(f'cf_{yr}.html', cf_labels)
        out.write(f'\n===== CF {yr} (Dec-31 annual) =====\n')
        for lb in cf_labels:
            if lb in res:
                v=to_num(res[lb].get(f'{yr}-12-31'))
                out.write(f'  {lb}: {v/10000:.2f} yi\n' if v else f'  {lb}: {res[lb].get(f"{yr}-12-31","?")}\n')
    sys.stdout.buffer.write(out.getvalue().encode('utf-8'))
