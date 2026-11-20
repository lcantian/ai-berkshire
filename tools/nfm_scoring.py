#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""有色金属行业研究 — 三层打分引擎（质量层 / 估值层 / 周期层）。

最终星级 = min(质量层上限 − 估值调整, 周期封顶)
口径唯一来源：skills/four-factor-framework.md 第六章。

护城河★ 与 护城河类别为分析判断（人工赋值，附证据）；
其余三层的判据全部由脚本按统一规则计算，禁止手写星级。
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_nonferrous import UNIVERSE  # noqa

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(ROOT, "reports", "有色金属", "_research")
D = {m["code"]: m for m in json.load(open(os.path.join(BASE, "_analysis.json"), encoding="utf-8"))}

# ------------------------------------------------------------------ 护城河（人工判断，附证据）
MOAT = {
    # code: (护城河★, 最强护城河类别, 证据, 10 年后还在不在)
    "601899": (4, "资源+规模/成本优势",
             "全球前列铜金资源组合；FY2025 归母 517.8 亿元、ROE 31.8%、毛利率 27.7%；逆周期并购与自建矿把量增做进成本曲线",
             "资源会枯竭，但低成本资产组合 + 跨国并购与工程能力属组织能力，可续"),
    "603993": (4, "资源壁垒（世界级钴铜钼矿）",
             "TFM/KFM 钴铜矿 + 钼资源，FY2025 归母 203.4 亿元、ROE 26.5%、毛利率 23.9%、资本开支/收入仅 3.7%",
             "矿权期限与所在国政策是主要变量，资产本身 10 年内不可复制"),
    "000933": (4, "成本优势+牌照（产能置换指标）",
             "煤电铝一体 + 4500 万吨电解铝产能红线；FY2025 ROE 17.3%、毛利率 23.4%、资本开支/收入 2.9%、经济稀释 0.89%",
             "成本优势随煤价波动；产能指标是政策给的不是自己挣的，政策可变"),
    "002532": (3, "成本/规模优势（一体化）",
             "自备电解铝 + 高纯铝 + 铝箔一体化；FY2025 归母 48.2 亿元、净利率 16.3%、资本开支/收入 5.2%",
             "一体化可复制，十年后仍在但不再稀缺"),
    "600988": (3, "资源+成本优势",
             "境内外金矿，FY2025 毛利率 52.5%、净利率 24.4%、ROE 28.9%；但资本开支/收入 25.1% 属扩张期",
             "矿山资源可采，但黄金本身无定价权，成本优势会被追平"),
    "000975": (3, "资源+整合能力",
             "FY2025 毛利率 35.3%、净利率 16.9%、利息覆盖 27.1 倍、经济稀释 0%，账面质量是黄金链最好之一",
             "资源可被同业用钱买到，整合能力是组织能力，可续"),
    "000603": (2, "无（金银资源同质化）",
             "FY2025 毛利率 50.5%、净利率 19.7% 全部来自银价与铅锌价，公司层面无独立定价权",
             "无"),
    "600111": (4, "牌照（开采/冶炼分离总量指标）+ 集团整合",
             "指标制度 + 中国稀土集团整合；FY2025 毛利率 17.1%；但 ROE 12.6%、净利率 6.6%、OCF/NI 81.4% 均偏低",
             "指标制度是政策给的，政策可调；十年后仍在的概率高"),
    "601958": (3, "资源（钼钨矿，主业集中度高）",
             "A 股最纯的钼标的，FY2025 净利率 10.6%、毛利率 25.2%；但 10 年 ROE 均值仅 8.2%",
             "钼矿资源不可复制，但需求端是钢材周期，无定价权"),
    "000408": (3, "资源（盐湖钾肥）",
             "盐湖钾肥资源是护城河（钾），锂只是搭售；FY2025 ROE 83.2% 系权益基数低所致，利息覆盖 216.7 倍",
             "盐湖资源不可复制；锂业务无定价权"),
    "002738": (3, "资源+技术（铯铷全球近乎独占）",
             "铯铷业务全球垄断 + 锂钽资源；FY2025 毛利率 39.0%、净利率 18.6%；经济稀释 26.3%（观察项）",
             "铯铷替代难，锂部分无定价权"),
    "002756": (3, "资源（云母提锂成本优势）",
             "4 万吨碳酸锂 + 萤石资源；FY2025 ROE 18.1%、净利率 14.0%、利息覆盖 103.6 倍",
             "云母提锂成本随锂价承压，优势可被盐湖/锂辉石侵蚀"),
    "002192": (3, "资源（李家头矿）+ 客户绑定",
             "为天齐、比亚迪体系供矿；FY2025 毛利率 37.8%、净利率 9.0%",
             "客户绑定随锂价谈判重谈"),
    "600301": (3, "资源（锡锑）+ 出口管制受益",
             "锡锑资源，FY2025 毛利率 33.9%；但 10 年 ROE 均值仅 9.5%",
             "资源不可复制，但价格由全球供需定"),
}

# 周期档位：按个股四象限 + 商品价格方向人工判定（附判据），封顶由脚本执行
CYCLE = {
    # code: (档位, 象限, 判据)
    "601899": ("周期下行中段", "Ⅳ 主动补库",
               "存货同比 +28.6%、增速差 +17.1pct、TTM 周转 63.7 天（上年 49.1 天，+14.6 天）；合同负债 +21.6%；铜价 26Q3 均价环比 +3.78% 但已自 1 月 30 日高点回落 17.0%"),
    "603993": ("周期下行中段", "Ⅲ 被动积压",
               "存货同比 +61.1%、单季存货增 88.9 亿元、TTM 周转 84.4 天（+13.8 天）；合同负债 −29.7%；26Q3 单季经营现金流 −28.6 亿元"),
    "000933": ("周期下行中段", "Ⅲ 被动积压",
               "存货同比 +42.7%、增速差 +20.6pct、TTM 周转 50.8 天（+11.9 天）；合同负债 −3.5%；铝价 26Q3 均价环比 −2.77%、自 1 月 30 日高点 −18.5%"),
    "002532": ("周期下行中段", "Ⅱ 订单未至",
               "存货同比 −9.8%、增速差 −32.6pct、TTM 周转 120.2 天（−16.7 天，库存已去化）；合同负债 −5.0%；铝价 26Q3 环比 −2.77%"),
    "600988": ("周期下行中段", "Ⅱ 订单未至",
               "存货同比 +5.9%、增速差 −10.8pct、TTM 周转 167.1 天（−1.1 天）；合同负债 −43.0%；金价 26Q3 均价环比 −6.51%、自 1 月 29 日高点 −36.1%"),
    "000975": ("周期下行中段", "Ⅰ 供不应求",
               "存货同比 −18.3%、增速差 −9.2pct、TTM 周转 42.5 天（+4.9 天）；合同负债 +179.2%；金价 26Q3 环比 −6.51%"),
    "000603": ("周期下行中段", "Ⅳ 主动补库",
               "存货同比 +13.0%、增速差 −9.0pct、TTM 周转 160.7 天（+18.5 天）；合同负债 +13.4%；银价自 1 月 30 日高点 −66.6%、26Q3 环比 −14.72%"),
    "600111": ("周期上行中段", "Ⅱ 订单未至",
               "存货同比 +20.1% 低于收入同比 +36.5%、TTM 周转 136.4 天（较上年同期 −12.7 天）、单季存货减少 10.42 亿元 → 库存已去化；合同负债 −11.5%；2026Q3 单季毛利率 16.9%、归母 15.9 亿元、TTM 扣非同比 +117.73% 均为 8 年新高；氧化镨钕 1-9 月均价 74.2 万元/吨（同比 +57.56%），2026 年开采冶炼分离指标增速放缓至约 5%，1-9 月出口量 −9.6% 而出口额 +40.5%"),
    "601958": ("周期下行中段", "Ⅱ 订单未至",
               "存货同比 +6.7%、增速差 −7.7pct、TTM 周转 22.4 天（+4.0 天）；合同负债 +50.0%"),
    "000408": ("周期下行中段", "Ⅱ 订单未至",
               "存货同比 −27.0%、增速差 −65.2pct、TTM 周转 90.7 天（−18.6 天）；合同负债 −29.6%；碳酸锂自 5 月 13 日高点 −56.4%、26Q3 均价环比 −16.36%"),
    "002738": ("周期下行中段", "Ⅳ 主动补库",
               "存货同比 +14.2%、增速差 −10.6pct、TTM 周转 220.4 天（+66.6 天）；合同负债 +42.2%；碳酸锂 26Q3 均价环比 −16.36%"),
    "002756": ("周期下行中段", "Ⅳ 主动补库",
               "存货同比 +39.7%、增速差 +0.9pct、TTM 周转 51.3 天（+4.6 天）；合同负债 +34.8%；碳酸锂 26Q3 均价环比 −16.36%"),
    "002192": ("周期下行中段", "Ⅳ 主动补库",
               "存货同比 +131.8%、增速差 −246.8pct、TTM 周转 177.8 天（+60.2 天）；合同负债 +152.4%；碳酸锂 26Q3 均价环比 −16.36%"),
    "600301": ("周期下行中段", "Ⅳ 主动补库",
               "存货同比 +43.0%、增速差 +23.1pct、TTM 周转 91.8 天（+14.0 天）；合同负债 +20.5%；沪锡 26Q3 均价环比 +3.06%，是少数未转弱的品种"),
}


def quality_stars(m):
    """生意质量★（framework §1.3），全部由指标计算。"""
    ex = m["screen_exempt"]
    if not m["screen_pass"]:
        nf = len(m["screen_fails"])
        return 1 if nf >= 4 else (2 if nf >= 2 else 3)
    ex_ok = 3 if ex else 5
    if (m.get("roe_10y_avg") or 0) >= 20 and (m.get("gm_10y_avg") or 0) >= 40 \
            and (m.get("ocf_ni_5y_avg") or 0) >= 100 and (m.get("capex_rev_5y_avg") or 99) <= 5:
        return 5
    good = sum([
        (m.get("roe_10y_avg") or 0) >= 15,
        (m.get("gm_10y_avg") or 0) >= 30,
        (m.get("ocf_ni_5y_avg") or 0) >= 80,
        (m.get("nm_10y_avg") or 0) >= 10,
        (m.get("capex_rev_5y_avg") or 99) <= 10,
    ])
    return 4 if good >= 3 else (3 if good >= 2 else 2)


def quality_layer(q, moat):
    return round((q + moat) / 2.0, 1)


def valuation_state(m):
    """估值状态与调整（framework §5.4）+ PE/PS 分位交叉验证（防利润率周期性扩张）。"""
    pe3 = m.get("pe_pct_3y")
    pea = m.get("pe_pct_all")
    ps3 = m.get("ps_pct_3y")
    div = m.get("pe_ps_div_3y")
    ded = m.get("ded_ratio")
    ded_yoy = m.get("ttm_ded_yoy")
    pq = m.get("pe_q_ann")
    ped = m.get("pe_ttm_ded")
    pn3 = m.get("pe_norm_3y")

    notes = []
    # 明显高估
    if (pe3 is not None and pe3 > 70) or (pea is not None and pea > 70):
        return "明显高估", -2, f"PE 分位 {f(pe3)}% / {f(pea)}% 越 70% 线"
    if pn3 and ped and pn3 > 3 * ped:
        return "明显高估", -2, f"正常化 PE {pn3} > 3× 扣非 PE {ped}"
    if ped and ped > 80 and (ded_yoy is not None and ded_yoy < 30):
        return "明显高估", -2, f"扣非 PE {ped} > 80 且扣非同比 {ded_yoy}% < 30%"
    # 显著低估（四条同时满足）
    c1 = pe3 is not None and pe3 < 20 and pea is not None and pea < 30
    c2 = ded is not None and ded >= 85
    c3 = ded_yoy is not None and ded_yoy > 0
    c4 = pq is not None and ped is not None and pq < ped
    if c1 and c2 and c3 and c4:
        if div is not None and div >= 20:
            notes.append(f"PE 分位 {f(pe3)}% 与 PS 分位 {f(ps3)}% 分歧 {div}pct → 低 PE 由利润率高位造成，PE 分位不可信，降为「合理」")
            return "合理", -1, "；".join(notes)
        return "显著低估", 0, f"PE 分位 {f(pe3)}%/{f(pea)}%、扣非/归母 {f(ded)}%、扣非同比 {f(ded_yoy)}%、单季年化 {pq} < 扣非 PE {ped}，且 PS 分位 {f(ps3)}% 同向"
    # 分项说明
    if div is not None and div >= 20:
        notes.append(f"PE/PS 分位分歧 {div}pct（利润率高位）")
    if div is not None and div <= -20:
        notes.append(f"PE/PS 分位分歧 {div}pct（收入端已见底、利润待释放）")
    return "合理", -1, "；".join(notes) if notes else "未满足显著低估四条判据"


def cap_stars(cycle, layer, adj):
    cap = {"周期底部": 5, "周期上行中段": 5, "周期顶部": 3, "周期下行中段": 3}[cycle]
    if cycle == "周期下行中段" and layer < 4.5:
        cap = min(cap, 3)
    return cap


def tier(layer):
    if layer >= 4.5:
        return "A1"
    if layer >= 4.0:
        return "A1"
    if layer >= 3.5:
        return "A2"
    return "A3"


def f(v, n=2):
    return ('%.*f' % (n, v)) if v is not None else '—'


rows = []
for code, (moat, cat, evid, ten) in MOAT.items():
    m = D[code]
    q = quality_stars(m)
    layer = quality_layer(q, moat)
    vstate, adj, vnote = valuation_state(m)
    cycle, quad, cnote = CYCLE[code]
    cap = cap_stars(cycle, layer, adj)
    upper = 5 if layer >= 4.5 else (4 if layer >= 4.0 else (3 if layer >= 3.0 else (2 if layer >= 2.0 else 1)))
    # 估值调整已是带符号的档位下调量（0 / -1 / -2），故为「上限 + 调整」
    final = max(1, min(upper + adj, cap))
    # 护城河五类全部 < ★★★ → B 通道：不做估值、不进组合
    channel = "B" if moat < 3 else "A"
    if channel == "B":
        final = 0
    rows.append({
        "code": code, "name": m["name"], "segment": m["segment"],
        "q": q, "moat": moat, "moat_cat": cat, "evid": evid, "ten": ten,
        "layer": layer, "tier": tier(layer), "upper": upper,
        "vstate": vstate, "adj": adj, "vnote": vnote,
        "cycle": cycle, "quad": quad, "cnote": cnote, "cap": cap,
        "final": final, "channel": channel,
        "mcap": m.get("mcap_yi"), "pe": m.get("pe_ttm"), "ped": m.get("pe_ttm_ded"),
        "pn3": m.get("pe_norm_3y"), "pe3": m.get("pe_pct_3y"), "pea": m.get("pe_pct_all"),
        "ps3": m.get("ps_pct_3y"), "div": m.get("pe_ps_div_3y"),
    })


# ---------------------------------------------------------------- 仓位映射（含周期硬约束）
def destocked(m):
    """库存是否已去化：期末增速 vs 收入增速 + 周转天数 vs 上年同期 + 单季存货增量 三口径互证。"""
    c = m.get("cycle", {})
    iy, ry = c.get("inv_yoy"), c.get("rev_yoy")
    dd, dly = c.get("ttm_days_delta"), None
    q = c.get("inv_qoq_yi")
    if iy is None:
        return None
    if iy <= 0:
        return True
    if iy is None or ry is None or iy >= ry:
        return False
    return (dd is not None and dd <= 0) or (q is not None and q <= 0)


def position(r, m):
    if r["channel"] == "B":
        return "0%", "B 通道：护城河五类全部 <★★★，不做估值、不进组合（含期权）"
    cyc = r["cycle"]
    ds = destocked(m)
    hard = (cyc in ("周期下行中段", "周期顶部")) and (ds is False)
    if r["final"] >= 5:
        return "核心 50-60%", "质量层 ≥4.5 + 估值调整 0 + 周期不在顶部"
    if r["final"] == 4:
        return "卫星 25-35%", "质量层 ≥4.5 合理 或 4.0-4.4 显著低估"
    if r["final"] == 3:
        if r["tier"] == "A1":
            base = "小仓 10-15%（A1 4.0-4.4 合理）"
        elif r["tier"] == "A2":
            base = "试探仓 ≤10%（A2 3.5-3.9 显著低估）"
        else:
            base = "期权 ≤5%（A3 显著低估 + 明确催化剂）"
        if hard:
            return "0%", base + "，但" + cyc + "且库存未去化 → 硬约束一律不新建仓"
        return base, base
    return "0%", "质量或安全边际不足"


for r in rows:
    m = D[r["code"]]
    r["destocked"] = destocked(m)
    r["pos"], r["pos_note"] = position(r, m)
    r["inv_to_mcap"] = (round(m.get("cycle", {}).get("inv_yi") / m.get("mcap_yi") * 100.0, 2)
                        if m.get("cycle", {}).get("inv_yi") and m.get("mcap_yi") else None)
    r["inv_to_rev"] = m.get("cycle", {}).get("inv_to_ttm_rev")
    r["inv_yoy"] = m.get("cycle", {}).get("inv_yoy")
    r["rev_yoy"] = m.get("cycle", {}).get("rev_yoy")
    r["ttm_days_delta"] = m.get("cycle", {}).get("ttm_days_delta")

rows.sort(key=lambda r: (-r["final"], -r["layer"], r["code"]))
rows_a = [r for r in rows if r["channel"] == "A"]
rows_b = [r for r in rows if r["channel"] == "B"]
print("| 公司 | 代码 | 环节 | 生意质量★ | 护城河★ | 最强护城河 | 质量层 | 层级 | 质量层上限 | 估值状态 | 估值调整 | 周期档位 | 象限 | 周期封顶 | **最终星级** |")
print("|---|---|---|---:|---:|---|---:|:---:|:---:|---|---:|---|---:|---:|:---:|")
for r in rows_a:
    print(f"| {r['name']} | {r['code']} | {r['segment']} | {'★'*r['q']} | {'★'*r['moat']} | {r['moat_cat']} "
          f"| {r['layer']} | {r['tier']} | {'★'*r['upper']} | {r['vstate']} | {r['adj']} | {r['cycle']} | {r['quad']} "
          f"| {'★'*r['cap']} | **{'★'*r['final']}** |")
print()
print("| 公司 | 代码 | 最终星级 | 仓位 | 依据 | 存货同比 | 收入同比 | 周转天数变化 | 库存是否去化 | 存货/市值 | 存货/TTM收入 |")
print("|---|---|:---:|---|---|---:|---:|---:|:---:|---:|---:|")
for r in rows:
    print(f"| {r['name']} | {r['code']} | {'★'*r['final'] if r['final'] else '—'} | {r['pos']} | {r['pos_note']} "
          f"| {f(r['inv_yoy'],1)}% | {f(r['rev_yoy'],1)}% | {f(r['ttm_days_delta'],1)} 天 "
          f"| {'已去化' if r['destocked'] else ('未去化' if r['destocked'] is False else '数据不足')} "
          f"| {f(r['inv_to_mcap'],1)}% | {f(r['inv_to_rev'],1)}% |")
print()
for r in rows_b:
    print(f"### [B 通道] {r['name']} {r['code']} ｜ 护城河仅 {'★'*r['moat']}（<★★★）→ B 通道，不做估值、不进组合")
    print(f"- 排除理由：{r['evid']}")
    print(f"- 十年后：{r['ten']}")
    print()
for r in rows_a:
    print(f"### {r['name']} {r['code']} ｜ 质量层 {r['layer']}（{r['tier']}）｜ {r['vstate']}（{r['adj']}）｜ {r['cycle']} ｜ 最终 {'★'*r['final']}")
    print(f"- 生意质量 {'★'*r['q']}：ROE10y {f(D[r['code']].get('roe_10y_avg'),1)}%、毛利10y {f(D[r['code']].get('gm_10y_avg'),1)}%、"
          f"净利10y {f(D[r['code']].get('nm_10y_avg'),1)}%、OCF/NI5y {f(D[r['code']].get('ocf_ni_5y_avg'),1)}、"
          f"FCF5y {f(D[r['code']].get('fcf_5y_yi'),1)}亿、资本开支/收入 {f(D[r['code']].get('capex_rev_5y_avg'),1)}%")
    print(f"- 护城河 {'★'*r['moat']}（{r['moat_cat']}）：{r['evid']}")
    print(f"- 十年后：{r['ten']}")
    print(f"- 估值：PE(TTM) {f(r['pe'])}、扣非PE {f(r['ped'])}、正常化3y PE {f(r['pn3'])}、PE分位3y/全历史 {f(r['pe3'],1)}%/{f(r['pea'],1)}%、"
          f"PS分位3y {f(r['ps3'],1)}%、分歧 {f(r['div'],1)}pct → {r['vnote']}")
    print(f"- 周期：{r['quad']}，{r['cnote']}")
    print(f"- 推导：min(上限{'★'*r['upper']} − {r['adj']}, 封顶{'★'*r['cap']}) = {'★'*r['final']}")
    print()

json.dump(rows, open(os.path.join(BASE, "_scoring.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("saved _scoring.json")
