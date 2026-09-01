#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re, sys, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

out = open('segment_data2.txt', 'w', encoding='utf-8')

# Try GBK encoding for 10jqka pages
for fname in ['10jqka_operate.html', '10jqka_sp_operate.html']:
    p = Path(fname)
    if not p.exists():
        continue
    out.write(f"\n========== {fname} ==========\n")
    # Try GBK first
    for enc in ['gbk', 'gb18030', 'utf-8']:
        try:
            data = p.read_text(encoding=enc, errors='ignore')
            if '海康' in data or 'PBG' in data:
                out.write(f"\n--- Decoded with {enc} ---\n")
                # Strip HTML
                text = re.sub(r'<script[^>]*>.*?</script>', ' ', data, flags=re.DOTALL)
                text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL)
                text = re.sub(r'<[^>]+>', ' ', text)
                text = re.sub(r'\s+', ' ', text).strip()

                # Look for PBG/EBG/SMBG with numbers around
                for kw in ['PBG', 'EBG', 'SMBG', '创新业务', '海外', '主业', '分行业', '分产品', '分地区', '公共服务', '企事业', '中小企业']:
                    idx = 0
                    count = 0
                    while count < 3:
                        idx = text.find(kw, idx)
                        if idx < 0: break
                        snippet = text[max(0,idx-50):idx+600]
                        # Only save if contains numbers (financial data)
                        if re.search(r'\d', snippet):
                            out.write(f"\n[{kw} @ {idx}]: ...{snippet}...\n")
                        idx += len(kw)
                        count += 1
                break
        except Exception as e:
            out.write(f"\n{enc} decode error: {e}\n")

out.close()
print("Done")
