#!/usr/bin/env python3
"""AI产业链漏斗筛选：对29家A股+关键港股应用5条硬指标，输出留/弃表。
5条硬指标：PE/PEG · ROE>15% · OCF/净利>70% · 负债率<60% · 护城河★★★+
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

data = json.load(open(os.path.join(os.path.dirname(__file__), '..', 'data', 'ai_industry_20260707.json'), encoding='utf-8'))

# 护城河评级（★1-5，定性判断，基于产业链分析）
MOAT = {
    "300308":4, "300502":4, "300394":5, "002281":3, "688205":2, "300620":2,  # 光模块
    "601138":4, "000977":3, "603019":3, "000938":3, "000034":2,              # 服务器
    "002463":4, "300476":3, "600183":3, "002916":3,                            # PCB
    "002837":3, "300499":2, "301018":2,                                        # 散热
    "002851":3, "300870":2,                                                    # 电源
    "002475":4,                                                                # 连接器
    "688256":3, "688041":4, "688047":2,                                        # AI芯片
    "688111":5, "002230":3, "688561":2, "600570":4, "300496":3,                # 模型/应用
}
# 周期性标记（光模块/服务器当前盈利在周期顶，PEG需打折看）
CYCLICAL_PEAK = {"300308","300502","300394","002281","601138","000977","300476"}

def screen(r):
    f = r["fin"]; q = r["quote"]
    pe = q.get("pe"); roe = f.get("roe_pct"); np_g = f.get("np_growth_pct")
    ocf_np = f.get("ocf_np_ratio"); debt = f.get("debt_ratio_pct")
    np_ = f.get("netprofit_yi")
    moat = MOAT.get(r["code"], 3)
    results = {}
    # 1. PE / PEG
    if np_ is not None and np_ <= 0:
        results["pe"] = ("FAIL", "亏损，PE无意义")
    elif pe is not None and pe <= 0:
        results["pe"] = ("FAIL", "亏损")
    elif np_g is not None and np_g >= 30 and pe and pe > 0:
        peg = pe / np_g
        if peg < 1.5:
            results["pe"] = ("PASS", f"PEG={peg:.2f}(<1.5)" + (" ⚠周期顶" if r["code"] in CYCLICAL_PEAK else ""))
        else:
            results["pe"] = ("FAIL", f"PEG={peg:.2f}(>1.5)")
    elif pe is not None and 0 < pe < 35:
        results["pe"] = ("PASS", f"PE={pe:.0f}(<35合理)")
    else:
        results["pe"] = ("FAIL", f"PE={pe:.0f}偏高")
    # 2. ROE
    if roe is None:
        results["roe"] = ("FAIL", "ROE缺失")
    elif roe > 15:
        results["roe"] = ("PASS", f"ROE={roe:.1f}%")
    else:
        results["roe"] = ("FAIL", f"ROE={roe:.1f}%(<15)")
    # 3. OCF/净利
    if np_ is not None and np_ <= 0:
        results["ocf"] = ("SKIP", "亏损")
    elif ocf_np is None:
        results["ocf"] = ("FAIL", "OCF缺失")
    elif ocf_np >= 0.7:
        results["ocf"] = ("PASS", f"OCF/净利={ocf_np:.2f}")
    else:
        results["ocf"] = ("FAIL", f"OCF/净利={ocf_np:.2f}(<0.7)")
    # 4. 负债率
    if debt is None:
        results["debt"] = ("FAIL", "负债率缺失")
    elif debt < 60:
        results["debt"] = ("PASS", f"{debt:.1f}%")
    elif debt < 66:  # 重资产制造略放宽标黄
        results["debt"] = ("WARN", f"{debt:.1f}%(60-66重资产)")
    else:
        results["debt"] = ("FAIL", f"{debt:.1f}%(>60)")
    # 5. 护城河
    if moat >= 3:
        results["moat"] = ("PASS", "★"*moat)
    else:
        results["moat"] = ("FAIL", "★"*moat)
    # 计分
    passes = sum(1 for v in results.values() if v[0]=="PASS")
    warns = sum(1 for v in results.values() if v[0]=="WARN")
    fails = sum(1 for v in results.values() if v[0]=="FAIL")
    skips = sum(1 for v in results.values() if v[0]=="SKIP")
    # 判定：5全pass→保留；4pass+1warn/pass-adjacent→标黄；含FAIL且pass<4→淘汰
    eff_pass = passes + warns  # warn 视同接近及格
    if fails == 0:
        verdict = "✅保留" if warns == 0 else "🟡标黄"
    elif eff_pass >= 4 and fails <= 1 and skips <= 1:
        verdict = "🟡标黄"
    else:
        verdict = "❌淘汰"
    return results, verdict, (passes, warns, fails, skips)


def main():
    rows = []
    for r in data:
        res, verdict, counts = screen(r)
        rows.append((r, res, verdict, counts))
    # 按判定分组打印
    print("="*120)
    print(f"{'公司':10}{'代码':8}{'PE':>6}{'PEG/PE':>10}{'ROE':>7}{'OCF/NP':>8}{'负债':>7}{'护城河':>7}  {'判定':<8} 理由")
    print("="*120)
    # 保留/标黄优先
    order = {"✅保留":0, "🟡标黄":1, "❌淘汰":2}
    rows.sort(key=lambda x: (order.get(x[2],9), -(x[1]["roe"][1].count or 0) if False else 0))
    for r, res, verdict, counts in rows:
        f=r["fin"]; q=r["quote"]
        pe = q.get("pe"); pe_s = f"{pe:.0f}" if pe else "-"
        pe_detail = res["pe"][1][:16]
        roe_s = res["roe"][1]
        ocf_s = res["ocf"][1]
        debt_s = res["debt"][1]
        moat_s = res["moat"][1]
        print(f"{r['name'][:8]:10}{r['code']:8}{pe_s:>6}{pe_detail:>16}{roe_s:>14}{ocf_s:>14}{debt_s:>9}{moat_s:>6}  {verdict}")
    # 汇总
    keep=[r for r in rows if r[2]=="✅保留"]
    yellow=[r for r in rows if r[2]=="🟡标黄"]
    out=[r for r in rows if r[2]=="❌淘汰"]
    print()
    print(f"保留(5/5): {len(keep)}家  |  标黄: {len(yellow)}家  |  淘汰: {len(out)}家")
    print("\n保留+标黄名单:")
    for r,res,verdict,_ in keep+yellow:
        print(f"  {verdict} {r['name']}({r['code']}) — {r['segment']}  | PE={r['quote'].get('pe','-'):.0f} ROE={r['fin'].get('roe_pct','-')}% 护城河{'★'*MOAT[r['code']]}")

if __name__ == "__main__":
    main()
