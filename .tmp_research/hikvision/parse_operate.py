#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re, json, sys, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

out = open('segment_data.txt', 'w', encoding='utf-8')

# 10jqka main.json - might have segment data
data = Path('10jqka_main.json').read_text(encoding='utf-8', errors='ignore')
out.write(f"=== 10jqka_main.json size: {len(data)} ===\n")
# Try to parse as JSON
try:
    j = json.loads(data)
    out.write(f"Keys: {list(j.keys()) if isinstance(j, dict) else 'not dict'}\n")
    if isinstance(j, dict):
        for k, v in list(j.items())[:20]:
            if isinstance(v, (str, int, float)):
                out.write(f"  {k}: {str(v)[:200]}\n")
            elif isinstance(v, list):
                out.write(f"  {k}: list({len(v)})\n")
                if v:
                    out.write(f"    first: {str(v[0])[:400]}\n")
            elif isinstance(v, dict):
                out.write(f"  {k}: dict({list(v.keys())[:10]})\n")
except Exception as e:
    out.write(f"JSON parse error: {e}\n")
    # Try decoding unicode escapes first
    BACKSLASH = chr(92)
    def decode_us(s):
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
    decoded = decode_us(data)
    out.write(f"Decoded length: {len(decoded)}\n")
    # Find any PBG/EBG/SMBG
    for kw in ['PBG', 'EBG', 'SMBG', '创新业务', '主业产品', '主营业务', '分产品', '分行业', '分地区']:
        idx = decoded.find(kw)
        if idx >= 0:
            out.write(f"\n[{kw}] @ {idx}: {decoded[max(0,idx-100):idx+500]}\n")

# operate.html
out.write("\n\n=== 10jqka_operate.html ===\n")
data2 = Path('10jqka_operate.html').read_text(encoding='utf-8', errors='ignore')
BACKSLASH = chr(92)
def decode_us(s):
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
decoded2 = decode_us(data2)

for kw in ['PBG', 'EBG', 'SMBG', '创新业务', '主业产品', '主营业务', '分产品', '分行业', '分地区', '海外', '境内', '华东', '华南']:
    idx = 0
    count = 0
    while count < 2:
        idx = decoded2.find(kw, idx)
        if idx < 0: break
        out.write(f"\n[{kw}] @ {idx}: ...{decoded2[max(0,idx-80):idx+400]}...\n")
        idx += len(kw)
        count += 1

out.close()
print("Done")
