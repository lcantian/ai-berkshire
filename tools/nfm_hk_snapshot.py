#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Reconstruct the 2026-11-19 close snapshot for HK/US peers.

Method (validated on 紫金矿业 02899, whose 11-19 row was fetched directly):
  price(11-19) from the daily K-line;
  PE(11-19) = PE(11-20) x price(11-19)/price(11-20)   (EPS unchanged)
  PB(11-19) = PB(11-20) x price(11-19)/price(11-20)   (book value unchanged)
  mcap(11-19) = mcap(11-20) x price(11-19)/price(11-20)
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


def curl(url, timeout=40):
    r = subprocess.run(["curl", "-s", "--noproxy", "*", "-H", "User-Agent: " + UA, url],
                       capture_output=True, timeout=timeout)
    return r.stdout.decode("utf-8", errors="ignore")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = "2026-11-19"


def kline(sym, days=30):
    url = (f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={sym},day,,,{days},qfq")
    try:
        d = json.loads(curl(url))
        node = d["data"][sym]
        rows = node.get("qfqday") or node.get("day") or []
        out = []
        for r in rows:
            if isinstance(r, list) and len(r) >= 3:
                out.append({"d": r[0], "o": float(r[1]), "c": float(r[2])})
        return out
    except Exception as e:
        print("ERR", sym, e)
        return []


GQ2 = json.load(open(os.path.join(ROOT, "data", "nonferrous", "global_quotes2.json"), encoding="utf-8"))
out = []
for d in GQ2:
    sym = d["sym"]
    kl = kline(sym)
    hit = next((r for r in kl if r["d"] == TARGET), None)
    if hit is None and kl:
        hit = kl[-1]
    if not hit:
        print("NO KLINE", sym)
        continue
    p19, p20 = hit["c"], d["price"]
    r = p19 / p20 if p20 else 1.0
    rec = dict(d)
    rec["kline_date"] = hit["d"]
    rec["price_1119"] = p19
    rec["ratio"] = round(r, 6)
    rec["pe_1119"] = round(d["pe"] * r, 4) if d.get("pe") is not None else None
    rec["pb_1119"] = round(d["pb"] * r, 4) if d.get("pb") is not None else None
    rec["float_mcap_1119"] = round(d["float_mcap_yi"] * r, 4) if d.get("float_mcap_yi") is not None else None
    rec["mcap_1119"] = round(d["mcap_yi"] * r, 4) if d.get("mcap_yi") is not None else None
    rec["h_shares_yi"] = (round(d["float_mcap_yi"] / p20, 4)
                          if d.get("float_mcap_yi") and p20 else None)
    out.append(rec)
    print(f"{sym:10s} {hit['d']} px19={p19:<10} px20={p20:<10} ratio={r:.5f} "
          f"pe19={rec['pe_1119']} pb19={rec['pb_1119']} float19={rec['float_mcap_1119']} mcap19={rec['mcap_1119']} "
          f"hshares={rec['h_shares_yi']}")
    time.sleep(0.3)

p = os.path.join(ROOT, "data", "nonferrous", "global_1119.json")
json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("saved", p, len(out))
