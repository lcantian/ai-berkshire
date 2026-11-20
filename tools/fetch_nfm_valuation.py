#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""有色金属 — 补抓估值日频序列（PE/PB/PS 分位）与新浪日 K，用于周期与估值分位。

估值日频：东财 RPT_VALUEANALYSIS_DET（PE_TTM / PB_MRQ / PS_TTM / TOTAL_MARKET_CAP / CLOSE_PRICE）
日 K：新浪 quotes.sina.cn（不复权收盘 + 最高价）

用法：
    python tools/fetch_nfm_valuation.py probe
    python tools/fetch_nfm_valuation.py fetch --workers 6
"""
import io
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "data", "nonferrous")
sys.path.insert(0, os.path.join(ROOT, "tools"))
from fetch_nonferrous import UNIVERSE, HK_CODE  # noqa: E402  (导入时已完成 stdout UTF-8 包装)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
DC = "https://datacenter.eastmoney.com/securities/api/data/v1/get?"


def curl(url, tries=4, timeout=45):
    for i in range(tries):
        r = subprocess.run(["curl", "-s", "--noproxy", "*",
                            "-H", "User-Agent: " + UA,
                            "-H", "Referer: https://data.eastmoney.com/", url],
                           capture_output=True, timeout=timeout)
        s = r.stdout.decode("utf-8", errors="ignore")
        if s.strip():
            return s
        time.sleep(1.5)
    return ""


def secucode(code):
    return f"{code}.SH" if code[0] in "6" else f"{code}.SZ"


def fetch_val(code):
    """东财估值分析日频序列。"""
    out = os.path.join(CACHE, f"val_{code}.json")
    if os.path.exists(out):
        return "cached"
    sc = secucode(code)
    url = (DC + "reportName=RPT_VALUEANALYSIS_DET&columns=ALL"
           f"&filter=(SECURITY_CODE%3D%22{code}%22)&pageSize=600"
           "&sortColumns=TRADE_DATE&sortTypes=-1&source=WEB&client=WEB")
    s = curl(url)
    try:
        d = json.loads(s)
        rows = d.get("result", {}).get("data", []) or []
    except Exception:
        rows = []
    if not rows:
        return "EMPTY"
    rows.sort(key=lambda r: r.get("TRADE_DATE", ""), reverse=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, ensure_ascii=False)
    return f"{len(rows)}"


def fetch_kline(code):
    """新浪日 K（不复权）。"""
    out = os.path.join(CACHE, f"kl_{code}.json")
    if os.path.exists(out):
        return "cached"
    sym = ("sh" if code[0] == "6" else "sz") + code
    url = ("https://quotes.sina.cn/cn/api/json_v2.php/CN_MarketDataService.getKLineData"
           f"?symbol={sym}&scale=240&ma=no&datalen=500")
    s = curl(url)
    try:
        rows = json.loads(s)
    except Exception:
        rows = []
    if not rows:
        return "EMPTY"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, ensure_ascii=False)
    return f"{len(rows)}"


def cmd_probe():
    for rn in ["RPT_VALUEANALYSIS_DET", "RPT_VALUEANALYSIS", "RPT_VALUATION_DET"]:
        url = (DC + f"reportName={rn}&columns=ALL&filter=(SECURITY_CODE%3D%22600111%22)"
               "&pageSize=2&sortColumns=TRADE_DATE&sortTypes=-1")
        s = curl(url)
        try:
            d = json.loads(s)
            rows = d.get("result", {}).get("data") if d.get("result") else None
            print(rn, "OK", list(rows[0].keys()) if rows else str(d)[:150])
        except Exception as e:
            print(rn, "FAIL", str(e)[:100], s[:150])


def cmd_fetch(args):
    os.makedirs(CACHE, exist_ok=True)
    codes = [u[0] for u in UNIVERSE]
    for fn, label in ((fetch_val, "val"), (fetch_kline, "kl")):
        todo = [c for c in codes if not os.path.exists(os.path.join(CACHE, f"{label}_{c}.json"))]
        print(f"[{label}] 待抓 {len(todo)}")
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            res = list(ex.map(fn, todo))
        bad = [c for c, r in zip(todo, res) if r in ("EMPTY",)]
        print(f"[{label}] 完成，空结果 {len(bad)}: {bad}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("probe")
    p = sub.add_parser("fetch")
    p.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    if a.cmd == "probe":
        cmd_probe()
    elif a.cmd == "fetch":
        cmd_fetch(a)
    else:
        ap.print_help()
