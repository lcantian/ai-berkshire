#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Three-scenario valuation for the A-channel names, using tools/financial_rigor.py.

Base EPS = TTM (last four single quarters, differenced from cumulative).
Scenarios describe what happens to the commodity price -> earnings path.
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_nonferrous import UNIVERSE  # noqa
from financial_rigor import three_scenario_valuation  # noqa

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(ROOT, "reports", "有色金属", "_research")
D = {m["code"]: m for m in json.load(open(os.path.join(BASE, "_analysis.json"), encoding="utf-8"))}

# code: (bull_g, base_g, bear_g, bull_pe, base_pe, bear_pe, note)
SCEN = {
    "601899": (0.10, -0.08, -0.20, 12, 10, 8,
               "Bull: copper >110k/t and gold back above 1000 CNY/g, output keeps growing. "
               "Base: copper 95k/t and gold 800 CNY/g, profit mean-reverts to FY2025 level. "
               "Bear: copper 80k/t and gold 700 CNY/g."),
    "000933": (0.12, -0.06, -0.18, 10, 8, 6,
               "Bull: aluminium >24k/t, coal cost advantage persists. "
               "Base: aluminium 21k/t, profit reverts to FY2025. "
               "Bear: aluminium 19k/t and coal price up."),
    "002738": (0.15, -0.05, -0.22, 22, 16, 12,
               "Bull: caesium-rubidium monopoly pricing plus lithium above 100k/t. "
               "Base: lithium 90k/t, cesium steady. "
               "Bear: lithium 70k/t below the cost line of outside-fed converters."),
    "600111": (0.12, -0.10, -0.22, 30, 25, 20,
               "Bull: NdPr stays above 800k/t, quota growth capped at 5%. "
               "Base: NdPr back to 600k/t, profit reverts to FY2025. "
               "Bear: NdPr back to the 2024 trough, profit back to 1.0bn."),
}

out = []
for code, (bg, ng, pg, bpe, npe, ppe, note) in SCEN.items():
    m = D[code]
    price = m["price"]
    shares = m["total_shares_yi"]
    eps_ttm = m["ttm_np_yi"] / shares
    eps_norm = (m.get("norm_np_3y_yi") or 0) / shares
    print("=" * 78)
    print(f"{m['name']} {code}  price={price}  shares={shares:.4f} yi  "
          f"EPS(TTM)={eps_ttm:.4f}  EPS(3y-avg)={eps_norm:.4f}")
    print(f"  TTM NP={m['ttm_np_yi']} yi   3y avg NP={m.get('norm_np_3y_yi')} yi   "
          f"PE(TTM)={m.get('pe_ttm')}  PE(norm3y)={m.get('pe_norm_3y')}")
    print("=" * 78)
    three_scenario_valuation(price, eps_ttm, shares, bg, ng, pg, bpe, npe, ppe, years=3,
                             currency="CNY")
    print(note)
    print()
    out.append({"code": code, "name": m["name"], "price": price, "shares": shares,
                "eps_ttm": round(eps_ttm, 4), "eps_norm3y": round(eps_norm, 4),
                "pe_ttm": m.get("pe_ttm"), "pe_norm3y": m.get("pe_norm_3y"),
                "bull": (bg, bpe), "base": (ng, npe), "bear": (pg, ppe), "note": note})

json.dump(out, open(os.path.join(BASE, "_scenarios.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
