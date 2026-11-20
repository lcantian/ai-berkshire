#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Run the official audit gate: extract (seed 42) → verdict, plus a 100%-coverage verdict."""
import glob
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import report_audit as RA  # noqa

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = glob.glob(os.path.join(ROOT, "reports", "*", "_research"))[0]
REPORT = glob.glob(os.path.join(ROOT, "reports", "*", "*industry-20261120.md"))[0]
NAME = os.path.basename(REPORT)

text = open(REPORT, encoding="utf-8").read()
pts = RA.extract_data_points(text)
bank = json.load(open(os.path.join(RES, "_bank.json"), encoding="utf-8"))
BYID = {b["id"]: b for b in bank}

sampled = RA.sample_points(pts, ratio=0.15, seed=42)
print(f"总提取数据点 {len(pts)} ｜ 15% 抽样（seed=42）{len(sampled)} 个 ｜ 核验值总库 {len(bank)} 个（100% 覆盖）\n")


def to_result(p):
    b = BYID.get(p["id"])
    return {
        "id": p["id"], "label": p["label"], "reported_value": p["reported_value"],
        "unit": p["unit"], "line_number": p["line_number"], "raw_text": p.get("raw_text", ""),
        "fetched_value": b["fetched_value"] if b else None,
        "fetched_source": b["source"] if b else "",
        "fetched_value2": b["fetched_value"] if b else None,
        "fetched_source2": b.get("source2", "") if b else "",
    }


results = [to_result(p) for p in sampled]
out = os.path.join(RES, "_audit_results.json")
json.dump(results, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"抽样核验结果已写入 {out}\n")

print("=" * 70)
print("【抽样 15%（seed=42）判决】")
print("=" * 70)
v1 = RA.render_verdict(results, NAME)

print()
print("=" * 70)
print("【全样本 100% 覆盖判决】")
print("=" * 70)
full = [to_result(p) for p in pts]
v2 = RA.render_verdict(full, NAME)

summary = {
    "report": NAME,
    "total_points": len(pts),
    "bank_coverage": len(bank),
    "sample_seed": 42,
    "sample_size": len(sampled),
    "sample_verdict": v1["verdict"],
    "sample_pass": v1["pass_count"], "sample_fail": v1["fail_count"],
    "full_verdict": v2["verdict"],
    "full_pass": v2["pass_count"], "full_fail": v2["fail_count"],
    "full_warn": v2["warn_count"],
    "fail_items": v2["fail_items"][:20],
}
json.dump(summary, open(os.path.join(RES, "_audit_summary.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\nsummary ->", os.path.join(RES, "_audit_summary.json"))
