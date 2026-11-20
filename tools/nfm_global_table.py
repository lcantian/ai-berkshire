#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build the §3.1 global market-cap map table (A 股 11-19 收盘 / 港美股 11-19 收盘).

港美股口径：价格取腾讯日 K 的 2026-11-19 不复权收盘；PE / PB / 市值由 11-20 收盘快照
按价格比例回算（期间无财报更新，EPS 与每股净资产不变）。
"""
import io
import json
import os
import subprocess
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = "2026-11-19"


def curl(url, timeout=40):
    r = subprocess.run(["curl", "-s", "--noproxy", "*", "-H", "User-Agent: " + UA, url],
                       capture_output=True, timeout=timeout)
    return r.stdout.decode("utf-8", errors="ignore")


def raw_kline(sym, days=20):
    url = f"https://web.ifzq.gtimg.cn/appstock/app/kline/kline?param={sym},day,,,{days}"
    try:
        d = json.loads(curl(url))
        node = d["data"][sym]
        rows = node.get("day") or []
        out = {}
        for r in rows:
            if len(r) >= 3:
                out[r[0]] = float(r[2])
        return out
    except Exception as e:
        print("ERR", sym, e)
        return {}


GQ2 = {d["sym"]: d for d in json.load(
    open(os.path.join(ROOT, "data", "nonferrous", "global_quotes2.json"), encoding="utf-8"))}
AN = {m["code"]: m for m in json.load(
    open(os.path.join(ROOT, "reports", "有色金属", "_research", "_analysis.json"), encoding="utf-8"))}

rows = []
for sym, d in GQ2.items():
    kl = raw_kline(sym)
    p19 = kl.get(TARGET)
    if p19 is None:
        p19 = kl.get("2026-11-20")
    p20 = d["price"]
    ratio = p19 / p20 if p20 else 1.0
    rec = {
        "sym": sym, "cn": d["cn"], "segment": d["segment"], "currency": d["currency"],
        "price": p19, "pe": round(d["pe"] * ratio, 2) if d.get("pe") is not None else None,
        "pb": round(d["pb"] * ratio, 2) if d.get("pb") else None,
        "float_mcap": round(d["float_mcap_yi"] * ratio, 2) if d.get("float_mcap_yi") else None,
        "mcap": round(d["mcap_yi"] * ratio, 2) if d.get("mcap_yi") else None,
        "h_shares": round(d["float_mcap_yi"] / p20, 4) if d.get("float_mcap_yi") and p20 else None,
        "name": d["name"],
    }
    rows.append(rec)
    print(f"{sym:10s} {d['name']:20s} px={p19:<10} pe={rec['pe']} pb={rec['pb']} "
          f"float={rec['float_mcap']} mcap={rec['mcap']} hshares={rec['h_shares']}")
    time.sleep(0.25)

json.dump(rows, open(os.path.join(ROOT, "data", "nonferrous", "global_1119.json"), "w",
                     encoding="utf-8"), ensure_ascii=False, indent=1)

# ---------- markdown ----------
def f(v, n=2):
    return ("%.*f" % (n, v)) if v is not None else "—"


A_ROWS = [("601899", "紫金矿业"), ("603993", "洛阳钼业"), ("601600", "中国铝业"),
          ("600111", "北方稀土"), ("000792", "盐湖股份"), ("600547", "山东黄金"),
          ("603799", "华友钴业")]
out = ["| 市场 | 说明 | 最新价 | PE(TTM) | PB | 市值口径 |",
       "|---|---|---:|---:|---:|---|"]
for code, nm in A_ROWS:
    m = AN[code]
    note = m.get("mcap_note") or ""
    out.append(f"| A 股 | {nm} {code} | {f(m['price'])} 元 | {f(m['pe_ttm'])} | "
               f"{f(m.get('tencent_pb'))} | {f(m['mcap_yi'])} 亿元（{note}） |")
for r in rows:
    if not r["sym"].startswith("hk"):
        continue
    cur = "港元"
    out.append(f"| 港股 | {r['cn']} {r['sym'][2:]} | {f(r['price'])} {cur} | {f(r['pe'])} | "
               f"{f(r['pb'])} | H 股市值 {f(r['float_mcap'])} 亿{cur}；当地股价×全部股本 "
               f"{f(r['mcap'])} 亿{cur} |")
for r in rows:
    if not r["sym"].startswith("us"):
        continue
    out.append(f"| 美股 | {r['name']} {r['sym'][2:]} | {f(r['price'])} 美元 | {f(r['pe'])} | "
               f"{f(r['pb'])} | {f(r['mcap'])} 亿美元 |")
print()
print("\n".join(out))
open(os.path.join(ROOT, "reports", "有色金属", "_research", "_global_map.md"), "w",
     encoding="utf-8").write("\n".join(out) + "\n")
