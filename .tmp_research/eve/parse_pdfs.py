#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Extract capacity-related text from EVE PDFs."""
import sys, io, re, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pdfplumber

BASE = r'D:\AI\ai-berkshire\.tmp_research\eve\reports'

PDFS = ['2025annual.PDF','2025interim.PDF','2026Q1.PDF','2026H1pre.PDF','2024annual.PDF']

KW = re.compile(r'(产能|GWh|GW\b|动力电池|储能电池|消费电池|锂原电池|小型锂离子|三元圆柱|大圆柱|方形|软包|产能利用率|在建产能|规划产能|惠州|荆门|成都|沈阳|云南|玉溪|曲靖|盐城|青海|匈牙利|马来|泰国|628Ah?|625Ah?|Mr\.?\s*Big|麒麟|产能建设|投产|项目达产|生产基地|工厂|产能规划|扩建|产业化项目)')

OUT = open(r'D:\AI\ai-berkshire\.tmp_research\eve\pdf_extract.txt','w',encoding='utf-8')

for fn in PDFS:
    path = f'{BASE}\\{fn}'
    if not os.path.exists(path):
        continue
    OUT.write(f'\n{"#"*80}\n# {fn}\n{"#"*80}\n')
    print(f'Parsing {fn}...', flush=True)
    try:
        with pdfplumber.open(path) as pdf:
            print(f'  pages: {len(pdf.pages)}', flush=True)
            for i, page in enumerate(pdf.pages):
                try:
                    txt = page.extract_text() or ''
                except Exception as e:
                    txt = ''
                    OUT.write(f'\n[p{i+1} ERR {e}]\n')
                if KW.search(txt):
                    OUT.write(f'\n=== {fn} p{i+1} ===\n')
                    OUT.write(txt)
                    OUT.write('\n----\n')
    except Exception as e:
        OUT.write(f'\n[{fn} OPEN ERR {e}]\n')
        print(f'  ERR: {e}', flush=True)
    OUT.flush()
OUT.close()
print('Done')
