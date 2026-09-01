# -*- coding: utf-8 -*-
import re, sys, io

def read_html(path):
    with open(path,'rb') as f:
        raw=f.read()
    for enc in ['gb18030','gbk','utf-8']:
        try:
            return raw.decode(enc)
        except: 
            continue
    return raw.decode('gb18030',errors='replace')

def parse_statement(path, wanted_labels):
    html=read_html(path)
    rows=re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.S)
    result={}
    # find header row with dates
    dates=[]
    for row in rows:
        cells=re.findall(r'<td[^>]*>(.*?)</td>', row, re.S)
        cells=[re.sub(r'<[^>]+>','',c).strip() for c in cells]
        cells=[c for c in cells if c]
        if cells and re.match(r'^\d{4}-\d{2}-\d{2}$', cells[0]):
            dates=cells
            break
    # find data rows
    for row in rows:
        cells=re.findall(r'<td[^>]*>(.*?)</td>', row, re.S)
        cells=[re.sub(r'<[^>]+>','',c).strip() for c in cells]
        cells=[c for c in cells if c]
        if not cells: continue
        label=cells[0]
        for wl in wanted_labels:
            if label==wl:
                # values are the remaining cells
                vals=cells[1:]
                result[wl]=dict(zip(dates[1:] if len(dates)>1 else dates, vals)) if len(dates)==len(vals)+1 else dict(zip(dates, vals))
    return dates, result

if __name__=='__main__':
    out=io.StringIO()
    # Balance sheet wanted labels
    bs_labels=['货币资金','交易性金融资产','应收票据','应收账款','存货','流动资产合计','资产总计','短期借款','应付票据及应付账款','应付账款','一年内到期的非流动负债','流动负债合计','长期借款','应付债券','非流动负债合计','负债合计','实收资本（或股本）','未分配利润','归属于母公司股东权益合计','所有者权益（或股东权益）合计','预付款项','合同负债']
    for yr in ['2025','2024','2023','2022','2021']:
        dates,res=parse_statement(f'bs_{yr}.html', bs_labels)
        out.write(f'\n========== Balance Sheet {yr} (dates={dates}) ==========\n')
        for lb in bs_labels:
            if lb in res:
                out.write(f'{lb}: {res[lb]}\n')
    sys.stdout.buffer.write(out.getvalue().encode('utf-8'))
