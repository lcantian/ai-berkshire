#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Recompute the full-sample and per-group medians used in §3.5.2 and compare
with the values written in the report."""
import glob
import io
import json
import os
import statistics
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = glob.glob(os.path.join(ROOT, "reports", "*", "_research"))[0]
AN = json.load(open(os.path.join(RES, "_analysis.json"), encoding="utf-8"))


def med(vals):
    vals = [v for v in vals if v is not None]
    return round(statistics.median(vals), 2) if vals else None


def cyc(m, k):
    return (m.get("cycle") or {}).get(k)


allm = AN
print("=== 全样本 68 家 ===")
for k, lbl in [("inv_yoy", "存货同比"), ("inv_rev_spread", "存货−收入增速差"),
               ("ttm_days", "TTM周转天数"), ("ttm_days_ly", "上年同期"),
               ("contract_yoy", "合同负债同比"), ("rev_yoy", "收入同比")]:
    print(f"  {lbl}: {med([cyc(m, k) for m in allm])}")
print("  ttm_days_delta:", med([cyc(m, "ttm_days_delta") for m in allm]))

# --- groups per §3.5.2 table ---
BY = {}
for m in AN:
    BY.setdefault(m["name"], []).append(m)


def grp(names):
    out = []
    for n in names:
        out.extend(BY.get(n, []))
    return out


GROUPS = {
    "铜金锌综合（紫金）": ["紫金矿业"],
    "铜钼钴（洛钼）": ["洛阳钼业"],
    "铜（江西/云南）": ["江西铜业", "云南铜业"],
    "铜冶炼（铜陵）": ["铜陵有色"],
    "电解铝（云铝/神火/中铝）": ["中国铝业", "云铝股份", "神火股份"],
    "电解铝一体化（天山）": ["天山铝业"],
    "黄金（中金/赤峰/山金/西部/湖南）": ["中金黄金", "赤峰黄金", "山金国际", "西部黄金", "湖南黄金"],
    "稀土（北方/中国稀土/盛和/广晟）": ["北方稀土", "中国稀土", "盛和资源", "广晟有色"],
    "永磁（金力/正海/中科/韵升/大地熊）": ["金力永磁", "正海磁材", "中科三环", "宁波韵升", "大地熊"],
    "钨（中钨/章源）": ["中钨高新", "章源钨业"],
    "锂（6 家）": ["赣锋锂业", "天齐锂业", "永兴材料", "雅化集团", "盛新锂能", "融捷股份"],
    "锂钾（盐湖/藏格）": ["盐湖股份", "藏格矿业"],
    "钴镍锂（华友）": ["华友钴业"],
    "珠宝零售（4 家）": ["周大生", "潮宏基", "菜百股份", "豫园股份"],
}
print("\n=== 分组中位数 ===")
for g, names in GROUPS.items():
    ms = grp(names)
    print(f"  {g} (n={len(ms)}): 家数={len(ms)} 存货同比={med([cyc(m,'inv_yoy') for m in ms])} "
          f"差={med([cyc(m,'inv_rev_spread') for m in ms])} 周转={med([cyc(m,'ttm_days') for m in ms])} "
          f"上年={med([cyc(m,'ttm_days_ly') for m in ms])} 差值={med([cyc(m,'ttm_days_delta') for m in ms])} "
          f"合同={med([cyc(m,'contract_yoy') for m in ms])}")

print("\n=== 象限统计（全样本 68 家，按存货/合同负债符号）===")
q = {"Ⅰ": 0, "Ⅱ": 0, "Ⅲ": 0, "Ⅳ": 0}
for m in AN:
    i = cyc(m, "inv_yoy")
    c = cyc(m, "contract_yoy")
    if i is None or c is None:
        continue
    if i <= 0 and c > 0:
        q["Ⅰ"] += 1
    elif i <= 0 and c <= 0:
        q["Ⅱ"] += 1
    elif i > 0 and c <= 0:
        q["Ⅲ"] += 1
    else:
        q["Ⅳ"] += 1
print(" ", q, "有效样本", sum(q.values()))
