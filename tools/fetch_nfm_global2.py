#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Re-fetch global peer quotes with CORRECTED tickers + full field set.

Verification rule: the Tencent field f[1] (official name) must match the
intended company; a mismatch means the ticker is wrong (e.g. 02618 is 京东物流,
not 中国铝业; 01211 is 比亚迪, not 华友钴业).
"""
import json
import os
import subprocess
import sys
import time
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

HK = [
    ("hk02899", "紫金矿业", "铜金锌综合", "HKD"),
    ("hk02600", "中国铝业", "电解铝", "HKD"),
    ("hk01378", "中国宏桥", "电解铝", "HKD"),
    ("hk03993", "洛阳钼业", "铜钼钴", "HKD"),
    ("hk01818", "招金矿业", "黄金", "HKD"),
    ("hk01208", "五矿资源", "铜锌", "HKD"),
    ("hk03330", "灵宝黄金", "黄金", "HKD"),
    ("hk01258", "中国有色矿业", "铜锌", "HKD"),
    ("hk02245", "力勤资源", "镍", "HKD"),
    ("hk00851", "中国稀土", "稀土", "HKD"),
    ("hk06680", "金力永磁", "永磁", "HKD"),
    ("hk01772", "赣锋锂业", "锂", "HKD"),
    ("hk09696", "天齐锂业", "锂", "HKD"),
    ("hk06181", "老铺黄金", "黄金珠宝零售", "HKD"),
    ("hk01787", "山东黄金", "黄金", "HKD"),
]
US = [
    ("usFCX", "Freeport-McMoRan", "铜", "USD"),
    ("usNEM", "Newmont", "黄金", "USD"),
    ("usB", "Barrick", "黄金", "USD"),
    ("usAEM", "Agnico Eagle", "黄金", "USD"),
    ("usAA", "Alcoa", "铝", "USD"),
    ("usMP", "MP Materials", "稀土", "USD"),
    ("usLAC", "Lithium Americas", "锂", "USD"),
    ("usBHP", "BHP", "铜铁矿", "USD"),
]


def curl(url, tries=4):
    for _ in range(tries):
        r = subprocess.run(["curl", "-s", "--noproxy", "*", "-H", "User-Agent: " + UA, url],
                           capture_output=True, timeout=40)
        s = r.stdout.decode("gbk", errors="ignore")
        if s.strip():
            return s
        time.sleep(1.2)
    return ""


def quote(sym):
    raw = curl(f"https://qt.gtimg.cn/q={sym}")
    if '"' not in raw:
        return None
    f = raw[raw.find('"') + 1:raw.rfind('"')].split("~")
    if len(f) < 50:
        return None

    def n(i):
        try:
            return float(f[i])
        except Exception:
            return None
    return {"name": f[1], "price": n(3), "pe": n(39), "pb": n(43),
            "float_mcap_yi": n(44), "mcap_yi": n(45),
            "time": f[30] if len(f) > 30 else ""}


out = []
for sym, cn, seg, cur in HK + US:
    d = quote(sym)
    if not d:
        print(f"FAIL {sym} ({cn})")
        continue
    ok = cn.replace("McMoRan", "").replace(" ", "")[:2] in d["name"].replace(" ", "") \
        or d["name"].replace(" ", "")[:2] in cn.replace(" ", "")
    d.update({"sym": sym, "cn": cn, "segment": seg, "currency": cur, "name_ok": bool(ok)})
    out.append(d)
    flag = "" if ok else "   <<< 名称不匹配，请核对代码"
    print(f"{sym:10s} name={d['name']:22s} want={cn:18s} px={d['price']} pe={d['pe']} "
          f"pb={d['pb']} float={d['float_mcap_yi']} mcap={d['mcap_yi']}{flag}")
    time.sleep(0.4)

p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "data", "nonferrous", "global_quotes2.json")
json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("saved", p, len(out))
