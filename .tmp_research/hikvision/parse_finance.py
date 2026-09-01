#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import codecs, sys, io, re
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

out = open('finance_history.txt', 'w', encoding='utf-8')

data = Path('10jqka_fin.html').read_text(encoding='utf-8', errors='ignore')

# Manually decode \uXXXX
BACKSLASH = chr(92)  # backslash
def decode_unicode_escapes(s):
    result = []
    i = 0
    n = len(s)
    while i < n:
        if i + 5 < n and s[i] == BACKSLASH and s[i+1] == 'u':
            hex_str = s[i+2:i+6]
            try:
                code = int(hex_str, 16)
                result.append(chr(code))
                i += 6
                continue
            except:
                pass
        result.append(s[i])
        i += 1
    return ''.join(result)

decoded = decode_unicode_escapes(data)
out.write(f"Decoded length: {len(decoded)}\n\n")

out.write("=== Year arrays ===\n")
year_arrays = re.findall(r'\[("20\d{2}-\d{2}-\d{2}"(?:,"20\d{2}-\d{2}-\d{2}")*)\]', decoded)
out.write(f"Year arrays: {len(year_arrays)}\n")
for i, ya in enumerate(year_arrays[:3]):
    years = re.findall(r'"(20\d{2}-\d{2}-\d{2})"', ya)
    out.write(f"  Year array {i+1}: {years[:20]}\n")

out.write("\n=== Yi data arrays ===\n")
yi_arrays = re.findall(r'\[("\d+(?:\.\d+)?亿"(?:,"\d+(?:\.\d+)?亿")*)\]', decoded)
out.write(f"Arrays: {len(yi_arrays)}\n")
for i, ya in enumerate(yi_arrays[:10]):
    dps = re.findall(r'"(\d+(?:\.\d+)?亿)"', ya)
    out.write(f"  Array {i+1} ({len(dps)} pts): {dps[:20]}\n")

out.write("\n=== Percent arrays ===\n")
pct_arrays = re.findall(r'\[("-?\d+(?:\.\d+)?%"(?:,"-?\d+(?:\.\d+)?%")*)\]', decoded)
out.write(f"Arrays: {len(pct_arrays)}\n")
for i, pa in enumerate(pct_arrays[:5]):
    pcts = re.findall(r'"(-?\d+(?:\.\d+)?%)"', pa)
    out.write(f"  Array {i+1}: {pcts[:20]}\n")

out.write("\n=== Labels ===\n")
for lbl in ['营业总收入', '归母净利润', '净利润', '营业收入', '每股收益', '毛利率', '净利率', '净资产收益率', 'ROE', '总股本', '总资产', '经营现金流', '资产负债率', '主营业务收入', '扣除非经常性损益']:
    idx = decoded.find(lbl)
    if idx >= 0:
        out.write(f"\n[{lbl}] @ {idx}: ...{decoded[max(0,idx-100):idx+400]}...\n")

out.close()
print("Done")
